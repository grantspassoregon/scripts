import arcpy
import pandas as pd
import logging

ARCGIS_WORKSPACE = (
    "O:/GISUserProjects/Users/ErikRose/address_site_points/address_site_points.gdb"
)
ARCGIS_PROJECT = (
    "O:/GISUserProjects/Users/ErikRose/address_site_points/address_site_points.aprx"
)
LOG_FILE = "P:/address_fields.log"
CSV_FILE = "P:/address_fields.csv"

logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename=LOG_FILE,
    level=logging.INFO,
)

arcpy.env.workspace = ARCGIS_WORKSPACE
aprx = arcpy.mp.ArcGISProject(ARCGIS_PROJECT)
arcpy.env.parallelProcessingFactor = "1000%"


cursor = arcpy.UpdateCursor("addresses")
# address number
# for row in cursor:
#     num = row.getValue("ADDRNUM")
#     if num is not None:
#         if num.isnumeric():
#             row.setValue("AddressNumber", int(num))
#             cursor.updateRow(row)
#         else:
#             logging.info("Error processing %s.", num)
#     else:
#         logging.info("Field is none.")
# logging.info("All records processed.")

# complete address number
# for row in cursor:
#     num = row.getValue("AddressNumber")
#     suffix = row.getValue("AddressNumberSuffix")
#     addr = None
#     if num is not None:
#         if suffix is not None:
#             addr = str(num) + " " + suffix
#         else:
#             addr = str(num)
#         row.setValue("CompleteAddressNumber", addr)
#         cursor.updateRow(row)
#     else:
#         logging.info("Field is none.")
# logging.info("All records processed.")

# street name pre-directional
# for row in cursor:
#     predir = row.getValue("ROADPREDIR")
#     result = None
#     if predir is not None:
#         if predir == "NE":
#             result = "NORTHEAST"
#         if predir == "NW":
#             result = "NORTHWEST"
#         if predir == "SE":
#             result = "SOUTHEAST"
#         if predir == "SW":
#             result = "SOUTHWEST"
#         if predir == "N":
#             result = "NORTH"
#         if predir == "E":
#             result = "EAST"
#         if predir == "S":
#             result = "SOUTH"
#         if predir == "W":
#             result = "WEST"
#         row.setValue("StreetNamePreDirectional", result)
#         cursor.updateRow(row)
#         logging.debug("Field is %s.", result)
#     else:
#         logging.debug("Field is none.")
# logging.info("All records processed.")

# street names

# read street names from county registry into list
# street_names = []
#
# cursor = arcpy.SearchCursor("AuthorizedStreetNameTable")
# for row in cursor:
#     street = row.getValue("name")
#     street_names.append(street)

# update field row if street name is valid
# cursor = arcpy.UpdateCursor("addresses")
# for row in cursor:
#     result = row.getValue("ROADNAME")
#     if result is not None and result in street_names:
#         row.setValue("StreetName", result)
#         cursor.updateRow(row)
#         logging.debug('Field is %s.", result')
#     else:
#         logging.debug("Field is None.")
# logging.info("All records processed.")

# street type
# street_types = {}
#
# cursor = arcpy.SearchCursor("StreetTypeDomain")
# for row in cursor:
#     abbr = row.getValue("Street_abb")
#     name = row.getValue("Street_Typ")
#     street_types.update({abbr: name})
# logging.info("Street types loaded.")

# update field row if street type is valid
# cursor = arcpy.UpdateCursor("addresses")
# for row in cursor:
#     result = row.getValue("ROADTYPE")
#     logging.info("Result is %s.", result)
#     if result != None:
#         upr = result.upper()
#         if upr in street_types:
#             row.setValue("St_PosTyp", street_types[upr])
#             cursor.updateRow(row)
#             logging.info("Field is %s.", street_types[upr])
#     else:
#         logging.debug("Field is None.")
# logging.info("All records processed.")

# complete street name
for row in cursor:
    predir = row.getValue("St_PreDir")
    name = row.getValue("St_Name")
    postyp = row.getValue("St_PosTyp")
    result = None
    if predir is not None:
        result = predir + " " + name + " " + postyp
    else:
        result = name + " " + postyp
    row.setValue("CompleteStreetName", result)
    cursor.updateRow(row)
    logging.debug("Field is %s.", result)
logging.info("All records processed.")

del cursor, row
