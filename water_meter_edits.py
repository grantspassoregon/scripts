import arcpy
from arcpy import metadata as md
import logging
import os

# configure environment in arcpy
arcpy.env.parallelProcessingFactor = "100%"  # try to be parallel
arcpy.env.overwriteOutput = True  # overwrite GDB

LOG_FILE = "P:/water_meter_edits.log"

# format log messages to include time before message
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename=LOG_FILE,
    level=logging.INFO,
)


def field_map(fms, lyr, from_name, to_name, alias, rule):
    """
    Populates field map `fms` with a mapping of `from_name` in `lyr` into `to_name` using `rule`.

    Use this function to cherry-pick fields from a source layer (e.g. in a spatial join) for inclusion in the output layer.
    """
    fm = arcpy.FieldMap()
    fm.addInputField(lyr, from_name)
    fm.mergeRule = rule
    fm_name = fm.outputField
    fm_name.name = to_name
    fm_name.aliasName = alias
    fm.outputField = fm_name
    fms.addFieldMap(fm)


# enterprise database
egdb = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic_gpgis.sde"
path = "O:/GISUserProjects/Users/ErikRose/water_meter_editor"

# source layer paths
meters = os.path.join(
    egdb, "SDEPublic.GPGIS.WaterDistribution/SDEPublic.GPGIS.wServiceConnection"
)
edits = os.path.join(egdb, "SDEPublic.GPGIS.water_meter_edits")

# open arcpro project
aprx = os.path.join(path, "water_meter_editor.aprx")
aprx = arcpy.mp.ArcGISProject(aprx)
mp = aprx.listMaps("workspace")[0]

# mp.addDataFromPath(
#     "https://gisserver.grantspassoregon.gov/server/rest/services/Editing/water_meter_editor/FeatureServer/1"
# )
# arcpy.management.CopyFeatures(meters, "meters")
tab = mp.listTables("Water Meter Edits")[0]

meter_fields = [
    "GlobalID",
    "AssetOwner_2019",
    "AssetStatus_2019",
    "AssociatedAddress",
    "ACCOUNTID",
    "MeterNumber",
    "NOTES",
    "DataSource",
]

meters_fc = arcpy.Describe(meters).catalogPath
print("arcpy.Describe(meters).catalogPath = " + meters_fc)

meters_fc = arcpy.Describe(meters).catalogPath
# Get just the .sde file (before the backslash)
workspace = meters_fc.split("\\")[0]

edited = {}
with arcpy.da.SearchCursor(tab, ["OBJECTID", "parentid"]) as cursor:
    for row in cursor:
        objectid = row[0]
        parent = row[1]
        if parent not in edited or objectid > edited[parent]:
            edited[parent] = objectid


with arcpy.da.Editor(workspace) as edit:
    with arcpy.da.SearchCursor(tab, "*") as cursor:
        for row in cursor:
            parent = row[1]
            where_clause = f"GlobalID = '{parent}'"

            if row[0] != edited.get(parent):
                continue

            with arcpy.da.UpdateCursor(
                meters, meter_fields, where_clause
            ) as update_cursor:
                for feature in update_cursor:
                    feature = list(feature)
                    feature[1] = row[2]  # owner
                    feature[2] = row[3]  # status
                    feature[3] = row[4]  # address
                    feature[4] = row[5]  # account
                    feature[5] = row[6]  # number
                    feature[6] = row[7]  # notes
                    feature[7] = row[8]  # Data source
                    update_cursor.updateRow(feature)


print("Edits complete.")
