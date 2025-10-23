#! helper functions
import arcpy
import datetime
import itertools


def field_map(
    fms, lyr, from_name: str, to_name: str, alias: str | None = None, rule=None
):
    """
    Populates field map `fms` with a mapping of `from_name` in `lyr` into `to_name` using `rule`.

    Use this function to cherry-pick fields from a source layer (e.g. in a spatial join) for inclusion in the output layer.
    :param fms: Field mappings object to contain the mapping.
    :param lyr: Subject layer of the mapping.
    :param from_name: Name of attribute in subject layer.
    :type from_name: str
    :param to_name: Name of attribute in target layer.
    :type to_name: str
    :param alias: Target attribute alias (optional).
    :param rule: Merge rule (default = "First")
    :return: Adds mapping to provided *fms* as a side effect.
    :rtype: None
    """
    fm = arcpy.FieldMap()
    fm.addInputField(lyr, from_name)
    if rule:
        fm.mergeRule = rule
    else:
        fm.mergeRule = "First"
    fm_name = fm.outputField
    fm_name.name = to_name
    if alias:
        fm_name.aliasName = alias
    else:
        fm_name.aliasName = to_name
    fm.outputField = fm_name
    fms.addFieldMap(fm)


def since(lyr, cutoff, id="GlobalID", edit_date="last_edited_date"):
    """
    Subset global ids of items in layer last updated since the user-provided date.
    Used to generate where clauses for selections in updates.

    :param lyr: The layer data to subset.
    :return: Lists global ids edited since the cutoff date.
    :rtype: List(str)
    """
    edited = []
    with arcpy.da.SearchCursor(lyr, [id, edit_date]) as cursor:
        for row in cursor:
            id = row[0]
            edit_date = row[1]
            if id not in edited and edit_date > cutoff:
                edited.append(id)
    return edited


def ids(lyr, id="GlobalID"):
    """
    Collects user-defined ids *id* in layer *lyr* and returns the values in a list.

    :param lyr: The layer data to search for ids.
    :param id: Attribute name of id in layer.
    :type id: str
    :return: List of ids in the target layer.
    :rtype: List(str)
    """
    ids = []
    with arcpy.da.SearchCursor(lyr, [id]) as cursor:
        for row in cursor:
            ids.append(row[0])
    return ids


def created(new, old, new_id="AssetID", old_id="assetid"):
    """
    Returns ids in *new* that are not in *old*.

    :param new: Layer with latest additions.
    :param old: Outdated layer in need of update.
    :param new_id: Identifying attribute in *new*.
    :type new_id: str
    :param old_id: Identifying attribute in *old*.
    :type old_id: str
    """
    old_ids = ids(old, old_id)
    new_ids = ids(new, new_id)
    return list(set(new_ids) - set(old_ids))


def select_within(attribute: str, ids: list[str]):
    """
    Formats strings in a python list into an SQL where clause for use in SelectLayerByAttribute.

    :param attribute: Name of the target attribute to select by id.
    :type attribute: str
    :param ids: List of ids to select in layer.
    :type ids: list[str]
    :return: A string formatted as an SQL where clause.
    :rtype: str
    """
    fmt = "', '".join(ids)
    return f"{attribute} IN ('{fmt}')"


def get_created(new, old, out, new_id="AssetID", old_id="assetid"):
    """
    Create subset of *new* where ids in *new* are not in *old*.

    :param new: Layer with latest additions.
    :param old: Outdated layer in need of update.
    :param new_id: Identifying attribute in *new*.
    :type new_id: str
    :param old_id: Identifying attribute in *old*.
    :type old_id: str
    """
    temp = arcpy.management.MakeFeatureLayer(new, "temp")
    new_ids = created(temp, old, new_id, old_id)
    where_clause = select_within(new_id, new_ids)
    arcpy.management.SelectLayerByAttribute(temp, "NEW_SELECTION", where_clause)
    arcpy.management.CopyFeatures(temp, out)
    arcpy.management.Delete(temp)


def date_to_datetime(date: datetime.date | None) -> datetime.datetime | None:
    """Converts date only to date time format with arbitrary time data."""
    if not date:
        return None
    return datetime.datetime(date.year, date.month, date.day, 1, 0, 0, 0, None)


def extract_leading_number(text: str | None) -> int | None:
    """Extract the first contiguous sequence of digits from the start of a string."""
    if not text:
        return None

    digits = "".join(itertools.takewhile(str.isdigit, text))
    return int(digits) if digits else None
