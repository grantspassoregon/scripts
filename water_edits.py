# patch_meters_fieldwise_guid.py
from __future__ import annotations
import arcpy
import argparse, os, sys, json, math, datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Sequence, Literal, Iterator, TypeVar
from arcpy_logging import gp_info, gp_warn, gp_error  # your helpers

from guid import Guid, GuidError  # <-- Our type-safe GUID

# ============================================================
# Utilities
# ============================================================


def nowstamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


T = TypeVar("T")


def chunker(seq: Sequence[T], size: int) -> Iterator[Sequence[T]]:
    """
    Yield slices of `seq` of length `size`. Requires a sliceable sequence.

    Example:
        list(chunker([1,2,3,4,5], 2)) == [[1,2], [3,4], [5]]
    """
    if size <= 0:
        raise ValueError("chunk size must be > 0")
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def where_globalid_in(ids: Sequence[Guid]) -> str:
    if not ids:
        return "1=0"
    in_list = ",".join(g.sql_literal() for g in ids)
    return f"GlobalID IN ({in_list})"


# ============================================================
# Data models
# ============================================================


@dataclass(frozen=True)
class EditEvent:
    """One edit event for an asset, with timestamp and the fields touched."""

    parent_guid: Guid
    when: Optional[datetime.datetime]  # may be None if no date field
    values: Dict[str, Any]  # SOURCE (table) fields -> raw values


@dataclass(frozen=True)
class EditRow:
    """Final folded result used for patching (source fields -> final values)."""

    parent_guid: Guid
    values: Dict[str, Any]


@dataclass(frozen=True)
class PatchChange:
    field: str
    old: Any
    new: Any


@dataclass
class PatchResult:
    updated_count: int = 0
    failures: List[Dict[str, Any]] = field(default_factory=list)
    missing_in_prod: List[Guid] = field(default_factory=list)
    preview_changes: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self.failures = self.failures or []
        self.missing_in_prod = self.missing_in_prod or []
        self.preview_changes = self.preview_changes or []


# ============================================================
# TABLE loader → event streams
# ============================================================


class TableEditsSource:
    """
    Reads edits from a GDB table and produces ordered EditEvents keyed by Guid.
    Sorting: chronological asc by date_field, tie-break by OBJECTID asc (if present).
    """

    def __init__(
        self,
        workspace: str,
        table: str,
        parent_field: str,
        date_field: Optional[str],
        include_fields: List[str],
        tie_break_field: Optional[str] = "OBJECTID",
    ):
        self.workspace = workspace
        self.table = table
        self.parent_field = parent_field
        self.date_field = date_field
        self.include_fields = include_fields or []
        self.tie_break_field = tie_break_field

    def _fields(self, table_path: str) -> List[str]:
        return [f.name for f in arcpy.ListFields(table_path)]

    def load_event_streams(self) -> Dict[Guid, List[EditEvent]]:
        arcpy.env.workspace = self.workspace
        table_path = os.path.join(self.workspace, self.table)
        if not arcpy.Exists(table_path):
            raise RuntimeError(f"Edits table not found: {table_path}")

        fields = self._fields(table_path)
        if self.parent_field not in fields:
            raise RuntimeError(f"'{self.parent_field}' not found in edits table.")

        read_fields = [self.parent_field]
        if self.date_field:
            if self.date_field not in fields:
                raise RuntimeError(f"date_field '{self.date_field}' not found.")
            read_fields.append(self.date_field)

        tb = self.tie_break_field if self.tie_break_field in fields else None
        if tb and tb not in read_fields:
            read_fields.append(tb)

        for f in self.include_fields:
            if f in fields and f not in read_fields:
                read_fields.append(f)

        streams: Dict[Guid, List[EditEvent]] = {}
        with arcpy.da.SearchCursor(table_path, read_fields) as scur:
            # Indices for quick access
            parent_idx = read_fields.index(self.parent_field)
            date_idx = read_fields.index(self.date_field) if self.date_field else None
            tb_idx = read_fields.index(tb) if tb else None

            for row in scur:
                try:
                    parent_guid = Guid.from_db(row[parent_idx])
                except GuidError as e:
                    # Log/skip bad GUIDs (could collect to a side channel if desired)
                    print(f"[WARN] Skipping row: {e}")
                    continue

                dt = row[date_idx] if date_idx is not None else None

                vals: Dict[str, Any] = {}
                for i, fld in enumerate(read_fields):
                    if i in (parent_idx, date_idx, tb_idx):
                        continue
                    vals[fld] = row[i]
                event = EditEvent(parent_guid=parent_guid, when=dt, values=vals)
                streams.setdefault(parent_guid, []).append(event)

        # Sort per guid: by date asc, tie-break OBJECTID asc (if present)
        for guid, events in streams.items():
            if self.date_field:
                if tb:
                    events.sort(
                        key=lambda e: (
                            e.when or datetime.datetime.min,
                            e.values.get(tb) or 0,
                        )
                    )
                    # Remove tie-break field from values before folding
                    for e in events:
                        e.values.pop(tb, None)
                else:
                    events.sort(key=lambda e: (e.when or datetime.datetime.min))

        return streams


# ============================================================
# Fieldwise chronological folding
# ============================================================


class FieldwiseChronologicalAggregator:
    """
    Folds a list of EditEvents (chronologically) into a single EditRow
    where newer non-empty values overwrite older ones, per field.
    """

    def __init__(self, treat_empty_as_clear: bool = False):
        self.treat_empty_as_clear = treat_empty_as_clear

    def _is_touched(self, val: Any) -> bool:
        if val is None:
            return self.treat_empty_as_clear
        if isinstance(val, float) and math.isnan(val):
            return False
        if isinstance(val, str):
            return (val.strip() != "") or self.treat_empty_as_clear
        return True

    def fold(self, guid: Guid, events: List[EditEvent], fields: List[str]) -> EditRow:
        final: Dict[str, Any] = {}
        for e in events:  # chronological; newer overwrites older per field
            for f in fields:
                if f in e.values and self._is_touched(e.values[f]):
                    final[f] = e.values[f]
        return EditRow(parent_guid=guid, values=final)


# ============================================================
# Field mapping & domain translation
# ============================================================


class FieldMap:
    """
    Edits-table -> production field mapping, numeric conversion, domain translation.
    mapping: SOURCE_FIELD_IN_TABLE -> PROD_FIELD_IN_FC
    """

    def __init__(self, mapping: Dict[str, str], numeric_fields: Set[str]):
        self.mapping = mapping
        self.numeric_fields = numeric_fields

    def validate_against(self, prod_field_names: List[str]):
        missing = [
            dest for dest in self.mapping.values() if dest not in prod_field_names
        ]
        if missing:
            raise RuntimeError(f"Production layer missing mapped fields: {missing}")

    def translate_row(
        self, edit: EditRow, domain_maps: Dict[str, Dict[str, Dict[Any, Any]]]
    ) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for src_field, prod_field in self.mapping.items():
            if src_field not in edit.values:
                continue  # field not touched; skip
            val = edit.values.get(src_field)

            if isinstance(val, float) and math.isnan(val):
                val = None

            if prod_field in self.numeric_fields and val is not None:
                try:
                    val = float(val)
                except Exception:
                    pass

            dm = domain_maps.get(prod_field)
            if dm and val is not None:
                sval = str(val)
                if sval in dm["label_to_code"]:
                    val = dm["label_to_code"][sval]
                elif sval in dm["code_to_label"]:
                    pass
                else:
                    out[f"{prod_field}__domain_warning"] = (
                        f"Unrecognized domain value '{sval}'"
                    )

            out[prod_field] = val
        return out


class DomainMapsResolver:
    """Build code↔label maps for coded-value domains from SDE workspace."""

    @staticmethod
    def build(workspace: str, fc_path: str) -> Dict[str, Dict[str, Dict[Any, Any]]]:
        maps: Dict[str, Dict[str, Dict[Any, Any]]] = {}
        domains = {d.name: d for d in arcpy.da.ListDomains(workspace)}
        for f in arcpy.ListFields(fc_path):
            if f.domain and f.domain in domains:
                dom = domains[f.domain]
                try:
                    cv = dom.codedValues  # {code: label}
                except Exception:
                    cv = None
                if cv:
                    code_to_label = dict(cv)
                    label_to_code = {str(v): k for (k, v) in cv.items()}
                    maps[f.name] = {
                        "code_to_label": code_to_label,
                        "label_to_code": label_to_code,
                    }
        return maps


# ============================================================
# Version management (traditional)
# ============================================================


# version_manager.py

# Strongly-typed literals (prevent bad strings like "SPECIFIED"/"FAVOR_EDIT")
ReconcileMode = Literal["ALL_VERSIONS", "BLOCKING_VERSIONS"]
AcquireLocks = Literal["LOCK_ACQUIRED", "NO_LOCK_ACQUIRED"]
AbortConflicts = Literal["ABORT_CONFLICTS", "NO_ABORT"]
ConflictDef = Literal["BY_OBJECT", "BY_ATTRIBUTE"]
ConflictRes = Literal["FAVOR_TARGET_VERSION", "FAVOR_EDIT_VERSION"]
WithPost = Literal["POST", "NO_POST"]
WithDelete = Literal["DELETE_VERSION", "KEEP_VERSION"]


class VersionManager:
    """
    Traditional versioning helper:
      - Ensures a child version exists
      - Points a layer to the child
      - Reconcile/Post child -> parent (optionally delete child)

    Observability:
      - Emits structured logs via `logger`
      - Mirrors key events to ArcPy messages (Geoprocessing pane/history)
      - Captures GP tool messages and optional out_log
    """

    def __init__(
        self,
        sde: str,
        parent_version: str,
        child_version: Optional[str] = None,
        logger=None,
    ):
        self.sde = sde
        self.logger = logger  # <-- injected logger (can be None)
        self._owner = self._connection_owner()
        self.parent_version = self._ensure_qualified(parent_version)
        self.child_version = (
            self._ensure_qualified(child_version) if child_version else None
        )

    # -------------------- Internal helpers --------------------

    def _log_info(self, payload):
        if self.logger:
            self.logger.info(payload)
        gp_info(
            payload if isinstance(payload, str) else str(payload)
        )  # [1](https://desktop.arcgis.com/en/arcmap/latest/analyze/arcpy-functions/setprogressor.htm)

    def _log_warn(self, payload):
        if self.logger:
            self.logger.warning(payload)
        gp_warn(
            payload if isinstance(payload, str) else str(payload)
        )  # [5](https://www.sig.cmquebec.qc.ca/gspvega/help/en/notebook/latest/python/windows/setprogressorposition.htm)

    def _log_error(self, payload):
        if self.logger:
            self.logger.error(payload)
        gp_error(
            payload if isinstance(payload, str) else str(payload)
        )  # [6](https://chjch.github.io/gisautomation/modules/9-3.additional_features.html)

    def _connection_owner(self) -> str:
        desc = arcpy.Describe(self.sde)
        cp = getattr(desc, "connectionProperties", None)
        owner = getattr(cp, "user", None) if cp else None
        return owner or "sde"

    def _ensure_qualified(self, ver_name: Optional[str]) -> str:
        if not ver_name:
            return ""
        return ver_name if "." in ver_name else f"{self._owner}.{ver_name}"

    @staticmethod
    def _short_name(qualified_name: str) -> str:
        return qualified_name.split(".", 1)[-1]

    def _existing_version_names(self) -> set[str]:
        # ListVersions returns Version objects; use .name (not [0])
        names = {v.name for v in arcpy.da.ListVersions(self.sde)}
        return names  # [7](https://pro.arcgis.com/en/pro-app/latest/help/data/geodatabases/overview/using-python-scripting-to-batch-reconcile-and-post-versions.htm)

    def _assert_parent_exists(self) -> None:
        if self.parent_version not in self._existing_version_names():
            raise RuntimeError(f"Parent version not found: {self.parent_version}")

    # -------------------- Public API --------------------

    def ensure_child_exists(self) -> str:
        """
        Create the child version if missing; return fully-qualified child name.
        Logs creation and selection.
        """
        if not self.child_version:
            auto_short = (
                f"BACKPATCH_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.child_version = self._ensure_qualified(auto_short)

        self._assert_parent_exists()

        if self.child_version not in self._existing_version_names():
            # CreateVersion(workspace, parent_version, short_child_name, access)
            arcpy.management.CreateVersion(
                self.sde,
                self.parent_version,
                self._short_name(self.child_version),
                "PUBLIC",
            )
            self._log_info(
                {
                    "event": "create_version",
                    "child": self.child_version,
                    "parent": self.parent_version,
                }
            )
        else:
            self._log_info({"event": "reuse_version", "child": self.child_version})

        return self.child_version

    def point_layer_to_child(self, layer_name: str) -> None:
        """
        Switch a feature layer to the child version (TRANSACTIONAL).
        """
        if not self.child_version:
            raise RuntimeError("Child version must be set before ChangeVersion.")
        arcpy.management.ChangeVersion(
            layer_name, "TRANSACTIONAL", self.child_version, "PUBLIC"
        )
        self._log_info(
            {"event": "change_version", "layer": layer_name, "to": self.child_version}
        )

    def reconcile_post_delete(
        self,
        mode: ReconcileMode = "ALL_VERSIONS",
        locks: AcquireLocks = "LOCK_ACQUIRED",
        abort: AbortConflicts = "NO_ABORT",
        definition: ConflictDef = "BY_ATTRIBUTE",
        resolution: ConflictRes = "FAVOR_EDIT_VERSION",
        post: WithPost = "POST",
        delete: WithDelete = "DELETE_VERSION",
        edit_versions: Sequence[str] | None = None,
        out_log: Optional[str] = None,
    ) -> None:
        """
        Reconcile/Post the child version into the parent; optionally delete the child.

        Valid values are exactly those documented by Esri for Reconcile Versions.  [7](https://pro.arcgis.com/en/pro-app/latest/help/data/geodatabases/overview/using-python-scripting-to-batch-reconcile-and-post-versions.htm)[4](https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/addwarning.htm)
        """
        if not self.child_version:
            raise RuntimeError(
                "Child version must be set before reconcile_post_delete()."
            )

        edits = list(edit_versions) if edit_versions else [self.child_version]

        # Pre-log the intent
        self._log_info(
            {
                "event": "reconcile_start",
                "mode": mode,
                "locks": locks,
                "abort": abort,
                "definition": definition,
                "resolution": resolution,
                "post": post,
                "delete": delete,
                "target": self.parent_version,
                "edits": edits,
                "out_log": out_log,
            }
        )

        try:
            # Use positional args per Pro/ArcMap Python syntax
            arcpy.management.ReconcileVersions(
                self.sde,
                mode,
                self.parent_version,
                edits,
                locks,
                abort,
                definition,
                resolution,
                post,
                delete,
                out_log,  # optional reconcile text log file
            )
            self._log_info({"event": "reconcile_done", "post": post, "delete": delete})

            # Append GP tool messages into the logger
            try:
                gp_messages = arcpy.GetMessages(
                    0
                )  # all severities 0/1/2  [3](https://community.esri.com/t5/arcgis-enterprise-questions/automated-reconciliation-with-arcpy-re-identifies/td-p/700564)
                if self.logger:
                    self.logger.info({"event": "gp_messages", "text": gp_messages})
                gp_info(
                    "Captured geoprocessing messages for ReconcileVersions."
                )  # [2](https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/getmessages.htm)
            except Exception:
                pass

            # If out_log provided, append into our structured log too
            if out_log and self.logger:
                try:
                    with open(out_log, "r", encoding="utf-8", errors="ignore") as rec:
                        for line in rec:
                            self.logger.info(
                                {
                                    "event": "reconcile_out_log",
                                    "line": line.rstrip("\n"),
                                }
                            )
                    gp_info(
                        f"ReconcileVersions out_log appended: {out_log}"
                    )  # [4](https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/addwarning.htm)
                except Exception as ex:
                    self._log_warn(
                        {
                            "event": "reconcile_out_log_append_failed",
                            "path": out_log,
                            "error": str(ex),
                        }
                    )

        except arcpy.ExecuteError as ex:
            # Mirror ArcPy failure to both log streams
            self._log_error(
                {"event": "reconcile_failed", "error": "ArcPy ExecuteError"}
            )
            # Also include GP messages if available
            try:
                gp_messages = arcpy.GetMessages(
                    2
                )  # errors only  [3](https://community.esri.com/t5/arcgis-enterprise-questions/automated-reconciliation-with-arcpy-re-identifies/td-p/700564)
                if self.logger:
                    self.logger.error(
                        {"event": "gp_messages_error", "text": gp_messages}
                    )
            except Exception:
                pass
            raise
        except Exception as ex:
            self._log_error({"event": "reconcile_failed", "error": str(ex)})
            raise


# ============================================================
# Feature layer wrapper
# ============================================================


class MetersLayer:
    def __init__(self, sde: str, fc: str, logger=None):
        """
        sde: path to SDE connection
        fc:  feature class (e.g., WATER.WaterMeters)
        logger: injected structured logger from arcpy_logging.make_logger()
        """
        self.sde = sde
        self.fc = fc
        self.logger = logger
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.layer_name = f"meters_layer_obsv_{ts}"

        # Resolve FC path and make layer
        fc_path = (f"{sde}\\{fc}") if "\\" not in fc else fc
        self.fc_path = fc_path
        if arcpy.Exists(self.layer_name):
            arcpy.management.Delete(self.layer_name)

        arcpy.management.MakeFeatureLayer(fc_path, self.layer_name)
        self._log_info(
            {
                "event": "make_feature_layer",
                "layer": self.layer_name,
                "fc_path": self.fc_path,
            }
        )

    # ---------- internal logging helpers ----------

    def _log_info(self, payload):
        if self.logger:
            self.logger.info(payload)
        # Also show in Pro’s Geoprocessing pane/history
        gp_info(payload if isinstance(payload, str) else str(payload))

    def _log_warn(self, payload):
        if self.logger:
            self.logger.warning(payload)
        gp_warn(payload if isinstance(payload, str) else str(payload))

    def _log_error(self, payload):
        if self.logger:
            self.logger.error(payload)
        gp_error(payload if isinstance(payload, str) else str(payload))

    # ---------- public API ----------

    def prod_field_names(self) -> List[str]:
        names = [f.name for f in arcpy.ListFields(self.layer_name)]
        self._log_info({"event": "list_fields", "count": len(names)})
        return names

    def select_globalids(
        self,
        guid_chunk: Sequence,  # Sequence[Guid] (stringify internally)
        chunk_index: Optional[int] = None,
        total_chunks: Optional[int] = None,
    ) -> int:
        """
        Select features by GlobalID for a chunk, with logs.
        If progress_label is provided, use SetProgressorLabel outside before/after this call.
        """
        where = "GlobalID IN ({})".format(",".join([f"'{str(g)}'" for g in guid_chunk]))
        chunk_tag = (
            {"chunk_index": chunk_index, "total_chunks": total_chunks}
            if chunk_index is not None
            else {}
        )

        self._log_info({"event": "select_start", "where": where, **chunk_tag})

        # Execute selection
        arcpy.management.SelectLayerByAttribute(self.layer_name, "NEW_SELECTION", where)
        count = int(arcpy.management.GetCount(self.layer_name).getOutput(0))

        # Capture tool messages (last GP tool run)
        try:
            gp_messages = arcpy.GetMessages(0)  # all severities
            if self.logger:
                self.logger.info(
                    {"event": "gp_messages_select", "text": gp_messages, **chunk_tag}
                )
        except Exception:
            pass

        self._log_info({"event": "select_done", "selected_count": count, **chunk_tag})
        return count

    def update_selected(
        self,
        field_map,  # FieldMap instance
        edits_by_guid: Dict,  # Dict[Guid, EditRow]
        domain_maps: Dict[str, Dict[str, Dict[Any, Any]]],
        dry_run: bool,
        chunk_index: Optional[int] = None,
        total_chunks: Optional[int] = None,
        preview_limit: int = 5,
    ) -> PatchResult:
        """
        Apply translated attribute updates on the current selection and log summary.
        """
        result = PatchResult()
        cursor_fields = ["GlobalID"] + list(field_map.mapping.values())
        chunk_tag = (
            {"chunk_index": chunk_index, "total_chunks": total_chunks}
            if chunk_index is not None
            else {}
        )

        self._log_info(
            {
                "event": "update_start",
                "dry_run": dry_run,
                "cursor_fields": cursor_fields,
                **chunk_tag,
            }
        )

        updated = 0
        failures = 0
        preview_sample: List[Dict[str, Any]] = []

        with arcpy.da.UpdateCursor(self.layer_name, cursor_fields) as ucur:
            for row in ucur:
                # Convert feature GUID; if invalid skip and log
                try:
                    raw_gid = row[0]
                    guid_str = str(raw_gid).strip("{}").upper()
                except Exception as e:
                    failures += 1
                    result.failures.append(
                        {"GlobalID": str(row[0]), "error": f"Guid parse: {e}"}
                    )
                    continue

                edit = edits_by_guid.get(guid_str) or edits_by_guid.get(
                    getattr(guid_str, "_value", guid_str)
                )
                if not edit:
                    # Not a failure—just not in edits set
                    continue

                translated = field_map.translate_row(edit, domain_maps)
                delta = 0
                changes: List[PatchChange] = []

                for idx, prod_field in enumerate(cursor_fields[1:], start=1):
                    if prod_field not in translated:
                        continue
                    new_val = translated.get(prod_field)
                    old_val = row[idx]
                    if old_val != new_val:
                        if not dry_run:
                            row[idx] = new_val
                        delta += 1
                        changes.append(
                            PatchChange(field=prod_field, old=old_val, new=new_val)
                        )

                if delta > 0:
                    if dry_run:
                        if len(preview_sample) < preview_limit:
                            preview_sample.append(
                                {
                                    "GlobalID": guid_str,
                                    "changes": [
                                        {"field": c.field, "from": c.old, "to": c.new}
                                        for c in changes
                                    ],
                                }
                            )
                    else:
                        try:
                            ucur.updateRow(row)
                            updated += 1
                        except Exception as ex:
                            failures += 1
                            result.failures.append(
                                {"GlobalID": guid_str, "error": str(ex)}
                            )

        # Summarize & log
        result.updated_count = updated
        if dry_run:
            result.preview_changes = preview_sample[:preview_limit]

        summary_payload = {
            "event": "update_done",
            "dry_run": dry_run,
            "updated_count": updated,
            "failures_count": failures,
            "preview_count": len(result.preview_changes),
            **chunk_tag,
        }
        self._log_info(summary_payload)

        if result.preview_changes and self.logger:
            # write a compact preview sample in structured log
            self.logger.info(
                {
                    "event": "update_preview_sample",
                    "sample": result.preview_changes[:preview_limit],
                    **chunk_tag,
                }
            )

        # Capture any GP messages produced during cursor work (selection already captured)
        try:
            gp_messages = arcpy.GetMessages(0)
            if self.logger:
                self.logger.info(
                    {"event": "gp_messages_update", "text": gp_messages, **chunk_tag}
                )
        except Exception:
            pass

        return result


# ============================================================
# Reporting
# ============================================================


@dataclass
class PatchReport:
    sde: str
    feature_class: str
    edits_table: str
    parent_version: str
    child_version: str
    dry_run: bool
    unique_parent_guids: int
    updated_rows: int
    missing_in_prod_count: int
    missing_in_prod_sample: List[str]  # stringified Guids for readability
    failures_count: int
    preview_changes_sample: List[Dict[str, Any]]

    def to_json(self) -> str:
        return json.dumps(
            {
                "sde": self.sde,
                "feature_class": self.feature_class,
                "edits_table": self.edits_table,
                "parent_version": self.parent_version,
                "child_version": self.child_version,
                "dry_run": self.dry_run,
                "unique_parent_guids": self.unique_parent_guids,
                "updated_rows": self.updated_rows,
                "missing_in_prod_count": self.missing_in_prod_count,
                "missing_in_prod_sample": self.missing_in_prod_sample,
                "failures_count": self.failures_count,
                "preview_changes_sample": self.preview_changes_sample,
            },
            indent=2,
        )


# ============================================================
# Orchestrator
# ============================================================


class PatcherRunner:
    def __init__(
        self,
        sde: str,
        fc: str,
        edits_table: str,
        parent_field: str,
        date_field: Optional[str],
        include_fields: List[str],
        field_map: FieldMap,
        fold_aggregator: FieldwiseChronologicalAggregator,
        chunk_size: int,
        dry_run: bool,
        parent_version: str,
        child_version: Optional[str],
        reconcile: bool,
        compress_after: bool,
        tie_break_field: Optional[str] = "OBJECTID",
    ):
        self.sde = sde
        self.fc = fc
        self.edits_table = edits_table
        self.parent_field = parent_field
        self.date_field = date_field
        self.include_fields = include_fields
        self.field_map = field_map
        self.fold_aggregator = fold_aggregator
        self.chunk_size = chunk_size
        self.dry_run = dry_run
        self.parent_version = parent_version
        self.child_version = child_version
        self.reconcile = reconcile
        self.compress_after = compress_after
        self.tie_break_field = tie_break_field

        arcpy.env.workspace = sde
        arcpy.env.overwriteOutput = True
        self.vm = VersionManager(sde, parent_version, child_version)
        self.layer = MetersLayer(sde, fc)

    def run(self) -> PatchReport:
        child_ver = self.vm.ensure_child_exists()
        self.vm.point_layer_to_child(self.layer.layer_name)

        self.field_map.validate_against(self.layer.prod_field_names())
        domain_maps = DomainMapsResolver.build(self.sde, self.layer.fc_path)

        source = TableEditsSource(
            workspace=self.sde,
            table=self.edits_table,
            parent_field=self.parent_field,
            date_field=self.date_field,
            include_fields=self.include_fields,
            tie_break_field=self.tie_break_field,
        )
        streams = source.load_event_streams()

        folded: Dict[Guid, EditRow] = {}
        for guid, events in streams.items():
            folded[guid] = self.fold_aggregator.fold(guid, events, self.include_fields)

        target_guids = sorted(
            folded.keys(), key=lambda g: str(g)
        )  # deterministic order
        missing_in_prod: List[Guid] = []
        total_updated = 0
        failures: List[Dict[str, Any]] = []
        previews: List[Dict[str, Any]] = []

        for guid_chunk in chunker(target_guids, self.chunk_size):
            sel_count = self.layer.select_globalids(guid_chunk)
            if sel_count == 0:
                missing_in_prod.extend(guid_chunk)
                continue

            res = self.layer.update_selected(
                self.field_map, folded, domain_maps, self.dry_run
            )
            total_updated += res.updated_count
            failures.extend(res.failures)
            previews.extend(res.preview_changes)
        if self.reconcile and not self.dry_run:
            self.vm.reconcile_post_delete(
                mode="ALL_VERSIONS",  # or "BLOCKING_VERSIONS"
                locks="LOCK_ACQUIRED",  # traditional versioning
                abort="NO_ABORT",  # or "ABORT_CONFLICTS"
                definition="BY_ATTRIBUTE",  # or "BY_OBJECT"
                resolution="FAVOR_EDIT_VERSION",  # or "FAVOR_TARGET_VERSION"
                post="POST",  # <- replaces do_post=True
                delete="DELETE_VERSION",  # <- replaces delete_child=True
                # edit_versions=None            # defaults to [child_version]
            )

        report = PatchReport(
            sde=self.sde,
            feature_class=self.fc,
            edits_table=self.edits_table,
            parent_version=self.parent_version,
            child_version=child_ver,
            dry_run=self.dry_run,
            unique_parent_guids=len(target_guids),
            updated_rows=total_updated,
            missing_in_prod_count=len(missing_in_prod),
            missing_in_prod_sample=[str(g) for g in missing_in_prod][:25],
            failures_count=len(failures),
            preview_changes_sample=previews[:5],
        )
        return report


# ============================================================
# CLI
# ============================================================


def build_field_map(include_fields: List[str]) -> FieldMap:
    """
    Build SOURCE (edits table) -> DEST (feature class) mapping.
    Adjust to YOUR schema.
    """
    mapping = {
        "owner": "OWNER",
        "status": "STATUS",
        "address": "ADDRESS",
        "account": "ACCOUNT",
        "number": "METER_NUMBER",
        "size": "SIZE",
        "material": "MATERIAL",
        "source": "SOURCE",
        "notes": "NOTES",
    }
    mapping = {k: v for k, v in mapping.items() if k in include_fields}
    numeric_fields = {"SIZE"}
    return FieldMap(mapping, numeric_fields)


def main():
    parser = argparse.ArgumentParser(
        description="Patch meters from a GDB edits table (fieldwise chronological, Guid-safe)."
    )
    parser.add_argument("--sde", required=True, help="Path to SDE connection (.sde)")
    parser.add_argument(
        "--fc", required=True, help="Feature class (e.g., WATER.WaterMeters)"
    )
    parser.add_argument(
        "--table", required=True, help="Edits table (e.g., WATER.MeterEdits)"
    )
    parser.add_argument(
        "--parent-field",
        required=True,
        help="Field in edits table that stores parent GlobalID",
    )
    parser.add_argument(
        "--date-field",
        default=None,
        help="Date/time field used to order events chronologically",
    )
    parser.add_argument(
        "--include-fields",
        nargs="*",
        required=True,
        help="Source fields to fold & patch (e.g., owner status size material ...)",
    )
    parser.add_argument(
        "--treat-empty-as-clear",
        default="false",
        help="true/false: if true, empty strings/None clear target fields",
    )
    parser.add_argument("--chunk", type=int, default=500, help="IN-clause chunk size")
    parser.add_argument(
        "--dry-run", default="true", help="true/false; preview changes without commit"
    )
    parser.add_argument(
        "--parent-version", default="sde.DEFAULT", help="Parent traditional version"
    )
    parser.add_argument(
        "--child-version", default=None, help="Child version (auto-created if missing)"
    )
    parser.add_argument(
        "--reconcile",
        default="false",
        help="true/false; reconcile/post/delete child after updates",
    )
    parser.add_argument(
        "--compress", default="false", help="true/false; compress after reconcile/post"
    )
    args = parser.parse_args()

    dry = str(args.dry_run).lower() in ("true", "1", "yes")
    rec = str(args.reconcile).lower() in ("true", "1", "yes")
    cmp = str(args.compress).lower() in ("true", "1", "yes")
    clear = str(args.treat_empty_as_clear).lower() in ("true", "1", "yes")

    field_map = build_field_map(args.include_fields)
    aggregator = FieldwiseChronologicalAggregator(treat_empty_as_clear=clear)

    runner = PatcherRunner(
        sde=args.sde,
        fc=args.fc,
        edits_table=args.table,
        parent_field=args.parent_field,
        date_field=args.date_field,
        include_fields=args.include_fields,
        field_map=field_map,
        fold_aggregator=aggregator,
        chunk_size=args.chunk,
        dry_run=dry,
        parent_version=args.parent_version,
        child_version=args.child_version,
        reconcile=rec,
        compress_after=cmp,
        tie_break_field="OBJECTID",
    )
    report = runner.run()
    print(report.to_json())

    # Save logs next to SDE connection
    base = f"patch_report_{nowstamp()}"
    out_dir = os.path.dirname(args.sde) or os.getcwd()
    with open(os.path.join(out_dir, f"{base}.json"), "w") as f:
        f.write(report.to_json())


if __name__ == "__main__":
    sys.exit(main() or 0)
