import arcpy
import logging
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
import sys

sys.path.append(r"d:\repos")
from un_update import Cleanout

sys.path.append(r"c:\users\erose\repos\scripts")
from helpers import created, get_created, field_map, select_within

# configure environment in arcpy
arcpy.env.parallelProcessingFactor = "100%"  # try to be parallel
arcpy.env.overwriteOutput = True  # overwrite GDB

LOG_FILE = "P:/un_update.log"

# format log messages to include time before message
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename=LOG_FILE,
    level=logging.INFO,
)


# enterprise database
egdb = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic_gpgis.sde"
branch = "O:/Connection (Admin)/branch/wastewater@branch.sde"
fs = "https://gisserver.grantspassoregon.gov/server/rest/services/UtilityNetwork/wastewater/FeatureServer"
path = "O:/GISUserProjects/Users/ErikRose/un_update"

# source layer paths
sewer = os.path.join(egdb, "SDEPublic.GPGIS.SewerStormwater")
clean_outs = os.path.join(sewer, "SDEPublic.GPGIS.ssCleanOut")
fittings = os.path.join(sewer, "SDEPublic.GPGIS.ssFitting")
force = os.path.join(sewer, "SDEPublic.GPGIS.ssPressurizedMain")
laterals = os.path.join(sewer, "SDEPublic.GPGIS.ssLateralLine")
mains = os.path.join(sewer, "SDEPublic.GPGIS.ssGravityMain")
manholes = os.path.join(sewer, "SDEPublic.GPGIS.ssManhole")
outlets = os.path.join(sewer, "SDEPublic.GPGIS.ssDischargePoint")
valves = os.path.join(sewer, "SDEPublic.GPGIS.ssSystemValve")

# un_sewer = os.path.join(branch, "WASTEWATER.wastewater")
# devices = os.path.join(un_sewer, "WASTEWATER.SewerDevice")
# lines = os.path.join(un_sewer, "WASTEWATER.SewerLine")
# junctions = os.path.join(un_sewer, "WASTEWATER.SewerJunction")

devices = os.path.join(fs, "1")
lines = os.path.join(fs, "6")
junctions = os.path.join(fs, "2")

# open arcpro project
aprx = os.path.join(path, "un_update.aprx")
aprx = arcpy.mp.ArcGISProject(aprx)
mp = aprx.listMaps("workspace")[0]


# 1. Check if layer exists and has features
count = int(arcpy.management.GetCount("Sewer Device")[0])
print(f"Feature count: {count}")

now = datetime.now()
ago = now - relativedelta(months=6)


new_clean_outs = "new_clean_outs"
new_ids = created(clean_outs, "Sewer Device", "AssetID", "assetid")
get_created(clean_outs, "Sewer Device", new_clean_outs)


def clean_out_fms():
    fms = arcpy.FieldMappings()
    field_map(fms, new_clean_outs, "ACCESSDIAM", "diameter")
    field_map(fms, new_clean_outs, "FACILITYID", "assetid")
    field_map(fms, new_clean_outs, "NOTES", "notes")
    field_map(fms, new_clean_outs, "HistoricID", "historic_id")
    field_map(fms, new_clean_outs, "RIM", "rim")
    field_map(fms, new_clean_outs, "OUT", "out")
    field_map(fms, new_clean_outs, "AssetID", "facility_id")
    return fms


def update_cleanout_fields(new, old, new_id, old_id, ids, workspace):
    new_clause = select_within(new_id, ids)
    old_clause = select_within(old_id, ids)
    with arcpy.da.SearchCursor(
        new,
        [
            new_id,
            "piCleanoutTypes",
            "AssetStatus_2019",
            "INSTALLDATE",
            "AssetOwner_2019",
            "piPipeMaterial",
            "DataSource",
            "SurveyPtNum",
            "SurveyDate",
        ],
        new_clause,
    ) as cursor:
        for row in cursor:
            print(row[0])
            with arcpy.da.Editor(workspace):
                with arcpy.da.UpdateCursor(
                    old,
                    [
                        old_id,
                        "assettype",
                        "lifecyclestatus",
                        "installdate",
                        "ownedby",
                        "material",
                        "spatialsource",
                        "constructionstatus",
                        "survey_pt",
                        "survey_date",
                    ],
                    old_clause,
                ) as update_cursor:
                    for j in update_cursor:
                        print(j[0])


fc = arcpy.Describe(branch).catalogPath
print("arcpy.Describe(branch).catalogPath = " + fc)
# Get just the .sde file (before the backslash)
workspace = fc.split("\\")[0]

cleanout = Cleanout(new_clean_outs)  # type: ignore

arcpy.management.Append(
    new_clean_outs, "Sewer Device", "NO_TEST", cleanout.field_mappings(), "Cleanout"
)
arcpy.management.AddJoin("Sewer Device", "assetid", new_clean_outs, "AssetID")
clause = select_within("L1Sewer_Device.assetid", new_ids)
arcpy.management.SelectLayerByAttribute("Sewer Device", "NEW_SELECTION", clause)
cleanout.update(workspace)


# 2. Check if there's a selection
desc = arcpy.Describe("Sewer Device")
if hasattr(desc, "FIDSet") and desc.FIDSet:
    print(f"Selected features: {len(desc.FIDSet.split(';'))}")
else:
    print("No selection - will affect all features")


# 3. Check the field properties
fields = arcpy.ListFields("Sewer Device", "L1Sewer_Device.ASSETTYPE")
if fields:
    field = fields[0]
    print(f"Field name: {field.name}")
    print(f"Field type: {field.type}")
    print(f"Field editable: {field.editable}")
    print(f"Field nullable: {field.isNullable}")
else:
    print("ASSETTYPE field not found!")

print(len(created(clean_outs, devices, "FACILITYID", "assetid")))
print(len(created(manholes, devices, "FACILITYID", "assetid")))
print(len(created(fittings, junctions, "FACILITYID", "assetid")))
