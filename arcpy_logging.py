# observability.py
from __future__ import annotations
import json
import logging
import logging.handlers
import time
import arcpy


def _json_formatter(record: logging.LogRecord) -> str:
    payload = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(record.created)),
        "level": record.levelname,
        "msg": record.getMessage(),
        "logger": record.name,
        "module": record.module,
        "func": record.funcName,
        "line": record.lineno,
    }
    if record.exc_info:
        payload["exc"] = logging.Formatter().formatException(record.exc_info)
    return json.dumps(payload)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return _json_formatter(record)


def make_logger(name: str, log_path: str, console: bool = True) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Rotating file
    fh = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=5_000_000, backupCount=5
    )
    fh.setFormatter(JsonFormatter())
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    # Minimal console (for dev/test)
    if console:
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)

    return logger


def gp_info(msg: str) -> None:
    """Mirror logs to ArcPy messaging so they show in Geoprocessing history/pane."""
    try:
        arcpy.AddMessage(msg)  # info/severity=0
    except Exception:
        pass


def gp_warn(msg: str) -> None:
    try:
        arcpy.AddWarning(msg)  # warning/severity=1
    except Exception:
        pass


def gp_error(msg: str) -> None:
    try:
        arcpy.AddError(msg)  # error/severity=2
    except Exception:
        pass


def start_progress(total_steps: int, label: str = "Processing…") -> None:
    arcpy.SetProgressor(
        "step", label, 0, total_steps, 1
    )  # step progressor [3](https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/setprogressor.htm)


def step_progress(sub_label: str | None = None) -> None:
    if sub_label:
        arcpy.SetProgressorLabel(sub_label)
    arcpy.SetProgressorPosition()


def end_progress() -> None:
    arcpy.ResetProgressor()  # reset to initial state [4](https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/resetprogressor.htm)


def log_last_gp_messages(logger):
    try:
        gpmsg = arcpy.GetMessages(
            0
        )  # 0=all severities [5](https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/getmessages.htm)
        logger.info({"gp_messages": gpmsg})
        gp_info("Last GP messages captured.")
    except Exception:
        pass
