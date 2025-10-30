import arcpy
import logging
import os
import sys
import traceback

sys.path.append(r"c:\users\erose\repos\scripts")
from helpers import field_map

os.environ["NUMEXPR_MAX_THREADS"] = "32"


def is_arcgis_pro():
    """Detect if running inside ArcGIS Pro."""
    return "ArcGISPro.exe" in sys.executable


class ArcGISProFallbackHandler(logging.StreamHandler):
    """Custom handler that prints to console if inside ArcGIS Pro."""

    def emit(self, record):
        super().emit(record)  # normal logging
        if is_arcgis_pro():
            try:
                msg = self.format(record)
                # print(msg)  # fallback for ArcGIS Pro Python window
            except Exception:
                self.handleError(record)


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # Create handler with fallback
    handler = ArcGISProFallbackHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def log_field_types(layer, label):
    for f in arcpy.ListFields(layer):
        logging.info(f"{label} field: {f.name} ({f.type})")


def main():
    logger = setup_logger()
    try:
        logger.info("Starting address site points append process...")

        # Set environment
        arcpy.env.parallelProcessingFactor = "100%"
        arcpy.env.overwriteOutput = True

        # Paths
        egdb = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic_gpgis.sde"
        path = "O:/GISUserProjects/Users/ErikRose/address_site_points/"
        legacy_path = os.path.join(egdb, "SDEPublic.GPGIS.land_ADDRESSES")
        modern_path = os.path.join(
            egdb, "SDEPublic.GPGIS.Land", "SDEPublic.GPGIS.ADDRESSES"
        )

        # Load project and map
        aprx = arcpy.mp.ArcGISProject(os.path.join(path, "address_site_points.aprx"))
        mp = aprx.listMaps("legacy_addresses")[0]
        logger.info("ArcGIS project and map loaded.")

        # Copy features
        legacy = arcpy.management.CopyFeatures(legacy_path, "legacy_addresses")
        modern = arcpy.management.CopyFeatures(modern_path, "modern_addresses")
        logger.info("Feature classes copied locally.")

        # The predirection field on the legacy data has a length too short for 'Northwest' or 'Southwest'
        predir = """
        var dir = $feature.St_PreDir
        When(
        dir == 'NORTHWEST', 'NW',
        dir == 'SOUTHWEST', 'SW',
        dir == 'NORTHEAST', 'NE',
        dir == 'SOUTHEAST', 'SE',
        dir == 'NORTH', 'N',
        dir == 'SOUTH', 'S',
        dir == 'WEST', 'W',
        dir == 'EAST', 'E',
        Null)
        """

        apt = """
        var unit = $feature.SubaddressType
        var unit = When(
        unit == 'APARTMENT', 'APT',
        unit == 'SUITE', 'STE',
        unit == 'COUNCIL CHAMBERS', 'COUNCIL',
        // unit == 'BUILDING', 'BLDG',
        unit == 'BUILDING', '',
        unit == 'SPACE', 'SP',
        unit)
        unit + ' ' + $feature.SubaddressIdentifier
            """

        # Calculate fields
        field_calcs = {
            "addrnum": "$feature.CompleteAddressNumber",
            "apartment": apt,
            "flr": "$feature.Floor",
            "roadpredir": predir,
            "roadname": "$feature.St_Name",
            "roadtype": "$feature.St_PosTyp",
            "fulladdr": "$feature.FULLADDRESS",
            "stat": "$feature.Status",
            "city": "$feature.CITY",
            "state": "$feature.STATE",
            "zip": "$feature.Post_Code",
            "roadpostdir": "Null",
        }

        for field, expr in field_calcs.items():
            arcpy.management.CalculateField(
                modern, field, expr, "ARCADE", field_type="TEXT"
            )
            logger.info(f"Calculated field: {field}")

        log_field_types(modern, "Modern")
        log_field_types(legacy, "Legacy")

        # Build field mappings
        fms = arcpy.FieldMappings()
        fields = [
            ("addrnum", "ADDRNUM", "Full Address Number"),
            ("apartment", "APARTMENT", "Apartment"),
            ("flr", "FLOOR", "Floor Number"),
            ("roadpredir", "ROADPREDIR", "Road Prefix"),
            ("roadname", "ROADNAME", "Road Name"),
            ("roadtype", "ROADTYPE", "Road Type"),
            ("fulladdr", "FULLADDR", "Full Address"),
            ("stat", "STATUS", "Status"),
            ("created_user", "created_user", "created_user"),
            ("created_date", "created_date", "created_date"),
            ("last_edited_user", "last_edited_user", "last_edited_user"),
            ("last_edited_date", "last_edited_date", "last_edited_date"),
            ("Post_Comm", "CITY", "CITY"),
            ("StateName", "STATE", "STATE"),
            ("zip", "ZIP", "ZIP"),
            ("NOTES", "NOTES", "NOTES"),
            ("NOTIFICATION", "NOTIFICATION", "NOTIFICATION"),
        ]

        for source, target, alias in fields:
            field_map(fms, modern, source, target, alias)
            logger.info(f"Mapped field: {source} → {target}, {alias}")

        for i in range(fms.fieldCount):
            fm = fms.getFieldMap(i)
            out_field = fm.outputField
            logging.info(f"FieldMap {i}: {out_field.name} ({out_field.type})")

        # Delete existing features in legacy
        arcpy.management.DeleteFeatures(legacy)
        logger.info("Deleted existing features in legacy layer.")

        # Append data
        arcpy.management.Append("modern_addresses", legacy, "NO_TEST", fms)
        logger.info("Append operation completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the append process: {e}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
