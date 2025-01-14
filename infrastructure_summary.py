import arcpy
from arcpy import env
from sympy import symbols
import sympy.physics.units as u
from sympy.physics.units.systems import SI
from sympy.physics.units import length, meter, foot, mile, kilometer, convert_to
from sympy.physics.units.systems.si import dimsys_SI
import os
import pandas
import logging


arcpy.env.parallelProcessingFactor = "100%"

# Customize these variables to paths on your system
PROJECT_DIR = "C:/Users/erose/projects"
GDB_NAME = "infrastructure_summary.gdb"
WORKSPACE = "C:/Users/erose/projects/infrastructure_summary.gdb"
ARCGIS_PROJECT = (
    "C:/Users/erose/Documents/ArcGIS/Projects/water_utilities/water_utilities.aprx"
)
LOG_FILE = "P:/infrastructure_summary.log"
CSV_FILE = "P:/infrastructure_summary.csv"

# format log messages to include time before message
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename=LOG_FILE,
    level=logging.INFO,
)
logging.info("environmental variables loaded")

# create gbd to host project layers
arcpy.management.CreateFileGDB(PROJECT_DIR, GDB_NAME)
# set new gdb as workspace
env.workspace = WORKSPACE

# copy layers from city database to local gdb
# defensive copies for editing and publishing
logging.info("Importing layers from SDE database.")
og_water_mains = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.wMain"
og_water_laterals = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.wLateralLine"
og_ugb = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.reg_UGB2014"
og_sewer_pressurized = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.ssPressurizedMain"
og_sewer_gravity = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.ssGravityMain"
og_sewer_lateral = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.ssLateralLine"
og_storm_gravity = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.swGravityMain"
og_storm_drain = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.swOpenDrain"
og_storm_culvert = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.swCulvert"
# og_streets = "https://gis.ecso911.com/server/rest/services/Hosted/Centerline_View/FeatureServer"
og_streets = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.tran_StreetPavementCL"
og_sidewalks = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.tran_SIDEWALK"
arcpy.CopyFeatures_management(og_water_mains, "water_mains")
arcpy.CopyFeatures_management(og_water_laterals, "water_laterals")
arcpy.CopyFeatures_management(og_sewer_pressurized, "sewer_pressurized")
arcpy.CopyFeatures_management(og_sewer_gravity, "sewer_gravity")
arcpy.CopyFeatures_management(og_sewer_lateral, "sewer_lateral")
arcpy.CopyFeatures_management(og_storm_gravity, "storm_gravity")
arcpy.CopyFeatures_management(og_storm_drain, "storm_drain")
arcpy.CopyFeatures_management(og_storm_culvert, "storm_culvert")
arcpy.CopyFeatures_management(og_streets, "streets")
arcpy.CopyFeatures_management(og_sidewalks, "sidewalks")
arcpy.CopyFeatures_management(og_ugb, "ugb")

# open arcpro project
aprx = arcpy.mp.ArcGISProject(ARCGIS_PROJECT)


def field_map(fms, lyr, from_name, to_name, rule):
    fm = arcpy.FieldMap()
    fm.addInputField(lyr, from_name)
    fm.mergeRule = rule
    fm_name = fm.outputField
    fm_name.name = to_name
    fm_name.aliasName = to_name
    fm.outputField = fm_name
    fms.addFieldMap(fm)


def report_count(vals):
    vals_set = set(vals)
    vals_uniq = list(vals_set)
    vals_ct = len(vals_uniq)
    return vals_ct


def list_field(fc, field_val, field_type=None, select_type=None):
    rows = arcpy.SearchCursor(fc)
    vals = []
    for row in rows:
        val = row.getValue(field_val)
        if field_val == "STLength()":
            dist = u.Quantity("d")
            SI.set_quantity_dimension(dist, u.length)
            SI.set_quantity_scale_factor(dist, val * u.foot)
            val = dist
            print(val)
        if field_type is None:
            vals.append(val)
        else:
            val_type = row.getValue(field_type)
            if val_type == select_type:
                vals.append(val)
    return vals


def list_pipe_length(pipe, value, status, owner, ugb, in_ugb=True):
    rows = arcpy.SearchCursor(pipe)
    vals = []
    for row in rows:
        val = row.getValue(value)
        pipe_status = row.getValue(status)
        logging.debug(pipe_status == "Active")
        pipe_owner = row.getValue(owner)
        logging.debug(pipe_owner == "City of Grants Pass")
        pipe_ugb = row.getValue(ugb)
        ugb_test = 1
        if in_ugb is False:
            ugb_test = 0
        if (
            pipe_status == "Active"
            and pipe_owner == "City of Grants Pass"
            and pipe_ugb == ugb_test
        ):
            vals.append(val)
    return vals


def list_street_length(street, value, owner, ugb, in_ugb=True):
    rows = arcpy.SearchCursor(street)
    vals = []
    for row in rows:
        val = row.getValue(value)
        pipe_owner = row.getValue(owner)
        logging.debug(pipe_owner == "City of Grants Pass")
        pipe_ugb = row.getValue(ugb)
        ugb_test = 1
        if in_ugb is False:
            ugb_test = 0
        if pipe_owner == "City of Grants Pass" and pipe_ugb == ugb_test:
            vals.append(val)
    return vals


def report_length(vals, unit="km"):
    vals_sum = sum(vals)
    dist = u.Quantity("d")
    SI.set_quantity_dimension(dist, u.length)
    SI.set_quantity_scale_factor(dist, vals_sum * u.foot)
    if unit == "km":
        km = convert_to(dist, kilometer).evalf(7)
        if km == 0:
            report = 0
        else:
            report = km.args[0]
    if unit == "miles":
        ml = convert_to(dist, mile).evalf(7)
        if ml == 0:
            report = 0
        else:
            report = ml.args[0]
    return report


# field map for water_mains
fms = arcpy.FieldMappings()
field_map(fms, "water_mains", "AssetStatus_2019", "status", "First")
field_map(fms, "water_mains", "AssetOwner_2019", "owner", "First")
field_map(fms, "water_mains", "FACILITYID", "id", "First")

# pipes within ugb
logging.info("Counting water mains within UGB.")
arcpy.analysis.SpatialJoin(
    "water_mains",
    "ugb",
    "water_mains_ugb",
    "#",
    "#",
    fms,
    "INTERSECT",
)

# field map for water_laterals
fms = arcpy.FieldMappings()
field_map(fms, "water_laterals", "AssetStatus_2019", "status", "First")
field_map(fms, "water_laterals", "AssetOwner_2019", "owner", "First")
field_map(fms, "water_laterals", "FACILITYID", "id", "First")

logging.info("Counting water laterals within UGB.")
arcpy.analysis.SpatialJoin(
    "water_laterals",
    "ugb",
    "water_laterals_ugb",
    "#",
    "#",
    fms,
    "INTERSECT",
)

# field map for sewer_pressurized
fms = arcpy.FieldMappings()
field_map(fms, "sewer_pressurized", "AssetStatus_2019", "status", "First")
field_map(fms, "sewer_pressurized", "AssetOwner_2019", "owner", "First")
field_map(fms, "sewer_pressurized", "FACILITYID", "id", "First")

logging.info("Counting pressurized sewer within UGB.")
arcpy.analysis.SpatialJoin(
    "sewer_pressurized",
    "ugb",
    "sewer_pressurized_ugb",
    "#",
    "#",
    fms,
    "INTERSECT",
)

# field map for sewer_gravity
fms = arcpy.FieldMappings()
field_map(fms, "sewer_gravity", "AssetStatus_2019", "status", "First")
field_map(fms, "sewer_gravity", "AssetOwner_2019", "owner", "First")
field_map(fms, "sewer_gravity", "FACILITYID", "id", "First")

logging.info("Counting gravity fed sewer within UGB.")
arcpy.analysis.SpatialJoin(
    "sewer_gravity",
    "ugb",
    "sewer_gravity_ugb",
    "#",
    "#",
    fms,
    "INTERSECT",
)

# field map for sewer_lateral
fms = arcpy.FieldMappings()
field_map(fms, "sewer_lateral", "AssetStatus_2019", "status", "First")
field_map(fms, "sewer_lateral", "AssetOwner_2019", "owner", "First")
field_map(fms, "sewer_lateral", "FACILITYID", "id", "First")

logging.info("Counting lateral sewer within UGB.")
arcpy.analysis.SpatialJoin(
    "sewer_lateral",
    "ugb",
    "sewer_lateral_ugb",
    "#",
    "#",
    fms,
    "INTERSECT",
)

# field map for storm_gravity
fms = arcpy.FieldMappings()
field_map(fms, "storm_gravity", "AssetStatus_2019", "status", "First")
field_map(fms, "storm_gravity", "AssetOwner_2019", "owner", "First")
field_map(fms, "storm_gravity", "FACILITYID", "id", "First")

logging.info("Counting gravity fed stormwater mains within UGB.")
arcpy.analysis.SpatialJoin(
    "storm_gravity",
    "ugb",
    "storm_gravity_ugb",
    "#",
    "#",
    fms,
    "INTERSECT",
)

# field map for storm_drain
fms = arcpy.FieldMappings()
field_map(fms, "storm_drain", "AssetStatus_2019", "status", "First")
field_map(fms, "storm_drain", "AssetOwner_2019", "owner", "First")
field_map(fms, "storm_drain", "FACILITYID", "id", "First")

logging.info("Counting stormwater drains within UGB.")
arcpy.analysis.SpatialJoin(
    "storm_drain",
    "ugb",
    "storm_drain_ugb",
    "#",
    "#",
    fms,
    "INTERSECT",
)

# field map for storm_culvert
fms = arcpy.FieldMappings()
field_map(fms, "storm_culvert", "AssetStatus_2019", "status", "First")
field_map(fms, "storm_culvert", "AssetOwner_2019", "owner", "First")
field_map(fms, "storm_culvert", "FACILITYID", "id", "First")

logging.info("Counting stormwater culverts within UGB.")
arcpy.analysis.SpatialJoin(
    "storm_culvert",
    "ugb",
    "storm_culvert_ugb",
    "#",
    "#",
    fms,
    "INTERSECT",
)

street_type = [
    "local_street",
    "local_collector",
    "collector",
    "arterial",
]

# sql select statements for SelectLayerByAttribute
local_street_select = "ROADCLASS = 'Local Street' Or ROADCLASS = 'LOCAL STREET'"
local_collector_select = "ROADCLASS = 'Local Collector'"
collector_select = "ROADCLASS = 'Collector' Or ROADCLASS = 'COLLECTOR'"
arterial_select = "ROADCLASS = 'Arterial' Or ROADCLASS = 'ARTERIAL'"

# dictionary key=street type, value=select statement
street_dict = {}
street_dict[street_type[0]] = local_street_select
street_dict[street_type[1]] = local_collector_select
street_dict[street_type[2]] = collector_select
street_dict[street_type[3]] = arterial_select


def streets_ugb(street_type, streets="streets"):
    # subset street layer by type
    logging.info("Subsetting street type %s.", street_type)
    arcpy.management.SelectLayerByAttribute(
        streets, "NEW_SELECTION", street_dict.get(street_type)
    )
    arcpy.management.CopyFeatures("streets", street_type)
    arcpy.management.SelectLayerByAttribute(streets, "CLEAR_SELECTION")

    # field map for street_type
    fms = arcpy.FieldMappings()
    field_map(fms, street_type, "AssetOwner", "owner", "First")
    field_map(fms, street_type, "FULLNAME", "id", "First")

    logging.info("Counting %s within UGB.", street_type)
    arcpy.analysis.SpatialJoin(
        street_type,
        "ugb",
        street_type + "_ugb",
        "#",
        "#",
        fms,
        "INTERSECT",
    )


for street in street_type:
    streets_ugb(street)


# field map for sidewalks
fms = arcpy.FieldMappings()
field_map(fms, "sidewalks", "FACILITYID", "id", "First")

logging.info("Counting sidewalks within UGB.")
arcpy.analysis.SpatialJoin(
    "sidewalks",
    "ugb",
    "sidewalks_ugb",
    "#",
    "#",
    fms,
    "INTERSECT",
)


def infrastructure_report():
    report_names = [
        "Water Mains",
        "Water Laterals",
        "Water Subtotal",
        "Sewer Pressurized",
        "Sewer Gravity",
        "Sewer Laterals",
        "Sewer Subtotal",
        "Stormwater Gravity",
        "Stormwater Drains",
        "Stormwater Culverts",
        "Stormwater Subtotal",
        "Local Streets",
        "Local Collector",
        "Collector",
        "Arterial",
        "Streets Subtotal",
        "Sidewalks",
        "Total",
    ]
    df = pandas.DataFrame(data={"name": report_names})

    ugb_ct = []
    ugb_km = []
    ugb_ml = []
    out_ct = []
    out_km = []
    out_ml = []

    main_ct = list_pipe_length("water_mains_ugb", "id", "status", "owner", "Join_Count")
    main_ct_out = list_pipe_length(
        "water_mains_ugb", "id", "status", "owner", "Join_Count", False
    )
    ugb_ct.append(report_count(main_ct))
    out_ct.append(report_count(main_ct_out))

    main_lengths = list_pipe_length(
        "water_mains_ugb", "Shape_Length", "status", "owner", "Join_Count"
    )
    ugb_km.append(report_length(main_lengths))
    ugb_ml.append(report_length(main_lengths, "miles"))

    main_lengths_nonugb = list_pipe_length(
        "water_mains_ugb", "Shape_Length", "status", "owner", "Join_Count", in_ugb=False
    )
    out_km.append(report_length(main_lengths_nonugb))
    out_ml.append(report_length(main_lengths_nonugb, "miles"))

    lateral_ct = list_pipe_length(
        "water_laterals_ugb", "id", "status", "owner", "Join_Count"
    )
    lateral_ct_out = list_pipe_length(
        "water_laterals_ugb", "id", "status", "owner", "Join_Count", False
    )
    ugb_ct.append(report_count(lateral_ct))
    out_ct.append(report_count(lateral_ct_out))

    lateral_lengths = list_pipe_length(
        "water_laterals_ugb", "Shape_Length", "status", "owner", "Join_Count"
    )
    ugb_km.append(report_length(lateral_lengths))
    ugb_ml.append(report_length(lateral_lengths, "miles"))

    lateral_lengths_nonugb = list_pipe_length(
        "water_laterals_ugb",
        "Shape_Length",
        "status",
        "owner",
        "Join_Count",
        in_ugb=False,
    )
    out_km.append(report_length(lateral_lengths_nonugb))
    out_ml.append(report_length(lateral_lengths_nonugb, "miles"))

    # water subtotal
    ugb_ct.append(ugb_ct[0] + ugb_ct[1])
    out_ct.append(out_ct[0] + out_ct[1])
    ugb_km.append(ugb_km[0] + ugb_km[1])
    ugb_ml.append(ugb_ml[0] + ugb_ml[1])
    out_km.append(out_km[0] + out_km[1])
    out_ml.append(out_ml[0] + out_ml[1])

    # sewer
    pressurized_ct = list_pipe_length(
        "sewer_pressurized_ugb", "id", "status", "owner", "Join_Count"
    )
    pressurized_ct_out = list_pipe_length(
        "sewer_pressurized_ugb", "id", "status", "owner", "Join_Count", False
    )
    ugb_ct.append(report_count(pressurized_ct))
    out_ct.append(report_count(pressurized_ct_out))

    pressurized_lengths = list_pipe_length(
        "sewer_pressurized_ugb", "Shape_Length", "status", "owner", "Join_Count"
    )
    ugb_km.append(report_length(pressurized_lengths))
    ugb_ml.append(report_length(pressurized_lengths, "miles"))

    pressurized_lengths_nonugb = list_pipe_length(
        "sewer_pressurized_ugb",
        "Shape_Length",
        "status",
        "owner",
        "Join_Count",
        in_ugb=False,
    )
    out_km.append(report_length(pressurized_lengths_nonugb))
    out_ml.append(report_length(pressurized_lengths_nonugb, "miles"))

    gravity_ct = list_pipe_length(
        "sewer_gravity_ugb", "id", "status", "owner", "Join_Count"
    )
    gravity_ct_out = list_pipe_length(
        "sewer_gravity_ugb", "id", "status", "owner", "Join_Count", False
    )
    ugb_ct.append(report_count(gravity_ct))
    out_ct.append(report_count(gravity_ct_out))

    gravity_lengths = list_pipe_length(
        "sewer_gravity_ugb", "Shape_Length", "status", "owner", "Join_Count"
    )
    ugb_km.append(report_length(gravity_lengths))
    ugb_ml.append(report_length(gravity_lengths, "miles"))

    gravity_lengths_nonugb = list_pipe_length(
        "sewer_gravity_ugb",
        "Shape_Length",
        "status",
        "owner",
        "Join_Count",
        in_ugb=False,
    )
    out_km.append(report_length(gravity_lengths_nonugb))
    out_ml.append(report_length(gravity_lengths_nonugb, "miles"))

    laterals_ct = list_pipe_length(
        "sewer_lateral_ugb", "id", "status", "owner", "Join_Count"
    )
    laterals_ct_out = list_pipe_length(
        "sewer_lateral_ugb", "id", "status", "owner", "Join_Count", False
    )
    ugb_ct.append(report_count(laterals_ct))
    out_ct.append(report_count(laterals_ct_out))

    laterals_lengths = list_pipe_length(
        "sewer_lateral_ugb", "Shape_Length", "status", "owner", "Join_Count"
    )
    ugb_km.append(report_length(laterals_lengths))
    ugb_ml.append(report_length(laterals_lengths, "miles"))

    laterals_lengths_nonugb = list_pipe_length(
        "sewer_lateral_ugb",
        "Shape_Length",
        "status",
        "owner",
        "Join_Count",
        False,
    )
    out_km.append(report_length(laterals_lengths_nonugb))
    out_ml.append(report_length(laterals_lengths_nonugb, "miles"))

    # sewer subtotal
    ugb_ct.append(ugb_ct[3] + ugb_ct[4] + ugb_ct[5])
    ugb_km.append(ugb_km[3] + ugb_km[4] + ugb_km[5])
    ugb_ml.append(ugb_ml[3] + ugb_ml[4] + ugb_ml[5])
    out_ct.append(out_ct[3] + out_ct[4] + out_ct[5])
    out_km.append(out_km[3] + out_km[4] + out_km[5])
    out_ml.append(out_ml[3] + out_ml[4] + out_ml[5])

    gravity_ct = list_pipe_length(
        "storm_gravity_ugb", "id", "status", "owner", "Join_Count"
    )
    gravity_ct_out = list_pipe_length(
        "storm_gravity_ugb", "id", "status", "owner", "Join_Count", False
    )
    ugb_ct.append(report_count(gravity_ct))
    out_ct.append(report_count(gravity_ct_out))

    gravity_lengths = list_pipe_length(
        "storm_gravity_ugb", "Shape_Length", "status", "owner", "Join_Count"
    )
    ugb_km.append(report_length(gravity_lengths))
    ugb_ml.append(report_length(gravity_lengths, "miles"))

    gravity_lengths_nonugb = list_pipe_length(
        "storm_gravity_ugb",
        "Shape_Length",
        "status",
        "owner",
        "Join_Count",
        in_ugb=False,
    )
    out_km.append(report_length(gravity_lengths_nonugb))
    out_ml.append(report_length(gravity_lengths_nonugb, "miles"))

    drain_ct = list_pipe_length(
        "storm_drain_ugb", "id", "status", "owner", "Join_Count"
    )
    drain_ct_out = list_pipe_length(
        "storm_drain_ugb", "id", "status", "owner", "Join_Count", False
    )
    ugb_ct.append(report_count(drain_ct))
    out_ct.append(report_count(drain_ct_out))

    drain_lengths = list_pipe_length(
        "storm_drain_ugb", "Shape_Length", "status", "owner", "Join_Count"
    )
    ugb_km.append(report_length(drain_lengths))
    ugb_ml.append(report_length(drain_lengths, "miles"))

    drain_lengths_nonugb = list_pipe_length(
        "storm_drain_ugb",
        "Shape_Length",
        "status",
        "owner",
        "Join_Count",
        in_ugb=False,
    )
    out_km.append(report_length(drain_lengths_nonugb))
    out_ml.append(report_length(drain_lengths_nonugb, "miles"))

    culvert_ct = list_pipe_length(
        "storm_culvert_ugb", "id", "status", "owner", "Join_Count", 1
    )
    culvert_ct_out = list_pipe_length(
        "storm_culvert_ugb", "id", "status", "owner", "Join_Count", 0
    )
    ugb_ct.append(report_count(culvert_ct))
    out_ct.append(report_count(culvert_ct_out))

    culvert_lengths = list_pipe_length(
        "storm_culvert_ugb", "Shape_Length", "status", "owner", "Join_Count"
    )
    ugb_km.append(report_length(culvert_lengths))
    ugb_ml.append(report_length(culvert_lengths, "miles"))

    culvert_lengths_nonugb = list_pipe_length(
        "storm_culvert_ugb",
        "Shape_Length",
        "status",
        "owner",
        "Join_Count",
        in_ugb=False,
    )
    out_km.append(report_length(culvert_lengths_nonugb))
    out_ml.append(report_length(culvert_lengths_nonugb, "miles"))

    # stormwater subtotal
    ugb_ct.append(ugb_ct[7] + ugb_ct[8] + ugb_ct[9])
    ugb_km.append(ugb_km[7] + ugb_km[8] + ugb_km[9])
    ugb_ml.append(ugb_ml[7] + ugb_ml[8] + ugb_ml[9])
    out_ct.append(out_ct[7] + out_ct[8] + out_ct[9])
    out_km.append(out_km[7] + out_km[8] + out_km[9])
    out_ml.append(out_ml[7] + out_ml[8] + out_ml[9])

    local_street_ct = list_street_length(
        "local_street_ugb", "id", "owner", "Join_Count", 1
    )
    local_street_ct_out = list_street_length(
        "local_street_ugb", "id", "owner", "Join_Count", 0
    )
    ugb_ct.append(report_count(local_street_ct))
    out_ct.append(report_count(local_street_ct_out))

    local_street_lengths = list_street_length(
        "local_street_ugb", "Shape_Length", "owner", "Join_Count"
    )
    ugb_km.append(report_length(local_street_lengths))
    ugb_ml.append(report_length(local_street_lengths, "miles"))

    local_street_lengths_nonugb = list_street_length(
        "local_street_ugb",
        "Shape_Length",
        "owner",
        "Join_Count",
        in_ugb=False,
    )
    out_km.append(report_length(local_street_lengths_nonugb))
    out_ml.append(report_length(local_street_lengths_nonugb, "miles"))

    local_collector_ct = list_street_length(
        "local_collector_ugb", "id", "owner", "Join_Count", 1
    )
    local_collector_ct_out = list_street_length(
        "local_collector_ugb", "id", "owner", "Join_Count", 0
    )
    ugb_ct.append(report_count(local_collector_ct))
    out_ct.append(report_count(local_collector_ct_out))

    local_collector_lengths = list_street_length(
        "local_collector_ugb", "Shape_Length", "owner", "Join_Count"
    )
    ugb_km.append(report_length(local_collector_lengths))
    ugb_ml.append(report_length(local_collector_lengths, "miles"))

    local_collector_lengths_nonugb = list_street_length(
        "local_collector_ugb",
        "Shape_Length",
        "owner",
        "Join_Count",
        in_ugb=False,
    )
    out_km.append(report_length(local_collector_lengths_nonugb))
    out_ml.append(report_length(local_collector_lengths_nonugb, "miles"))

    collector_ct = list_street_length("collector_ugb", "id", "owner", "Join_Count", 1)
    collector_ct_out = list_street_length(
        "collector_ugb", "id", "owner", "Join_Count", 0
    )
    ugb_ct.append(report_count(collector_ct))
    out_ct.append(report_count(collector_ct_out))

    collector_lengths = list_street_length(
        "collector_ugb", "Shape_Length", "owner", "Join_Count"
    )
    ugb_km.append(report_length(collector_lengths))
    ugb_ml.append(report_length(collector_lengths, "miles"))

    collector_lengths_nonugb = list_street_length(
        "collector_ugb",
        "Shape_Length",
        "owner",
        "Join_Count",
        in_ugb=False,
    )
    out_km.append(report_length(collector_lengths_nonugb))
    out_ml.append(report_length(collector_lengths_nonugb, "miles"))

    arterial_ct = list_street_length("arterial_ugb", "id", "owner", "Join_Count", 1)
    arterial_ct_out = list_street_length("arterial_ugb", "id", "owner", "Join_Count", 0)
    ugb_ct.append(report_count(arterial_ct))
    out_ct.append(report_count(arterial_ct_out))

    arterial_lengths = list_street_length(
        "arterial_ugb", "Shape_Length", "owner", "Join_Count"
    )
    ugb_km.append(report_length(arterial_lengths))
    ugb_ml.append(report_length(arterial_lengths, "miles"))

    arterial_lengths_nonugb = list_street_length(
        "arterial_ugb",
        "Shape_Length",
        "owner",
        "Join_Count",
        in_ugb=False,
    )
    out_km.append(report_length(arterial_lengths_nonugb))
    out_ml.append(report_length(arterial_lengths_nonugb, "miles"))

    # streets subtotal
    ugb_ct.append(ugb_ct[11] + ugb_ct[12] + ugb_ct[13] + ugb_ct[14])
    ugb_km.append(ugb_km[11] + ugb_km[12] + ugb_km[13] + ugb_km[14])
    ugb_ml.append(ugb_ml[11] + ugb_ml[12] + ugb_ml[13] + ugb_ml[14])
    out_ct.append(out_ct[11] + out_ct[12] + out_ct[13] + out_ct[14])
    out_km.append(out_km[11] + out_km[12] + out_km[13] + out_km[14])
    out_ml.append(out_ml[11] + out_ml[12] + out_ml[13] + out_ml[14])

    sidewalks_ct = list_field("sidewalks_ugb", "id", "Join_Count", 1)
    sidewalks_ct_out = list_field("sidewalks_ugb", "id", "Join_Count", 0)
    ugb_ct.append(report_count(sidewalks_ct))
    out_ct.append(report_count(sidewalks_ct_out))

    sidewalks_lengths = list_field("sidewalks_ugb", "Shape_Length", "Join_Count", 1)
    ugb_km.append(report_length(sidewalks_lengths))
    ugb_ml.append(report_length(sidewalks_lengths, "miles"))

    sidewalks_lengths_nonugb = list_field(
        "sidewalks_ugb",
        "Shape_Length",
        "Join_Count",
        0,
    )
    out_km.append(report_length(sidewalks_lengths_nonugb))
    out_ml.append(report_length(sidewalks_lengths_nonugb, "miles"))

    # total
    ugb_ct.append(ugb_ct[2] + ugb_ct[6] + ugb_ct[10] + ugb_ct[15] + ugb_ct[16])
    ugb_km.append(ugb_km[2] + ugb_km[6] + ugb_km[10] + ugb_km[15] + ugb_km[16])
    ugb_ml.append(ugb_ml[2] + ugb_ml[6] + ugb_ml[10] + ugb_ml[15] + ugb_ml[16])
    out_ct.append(out_ct[2] + out_ct[6] + out_ct[10] + out_ct[15] + out_ct[16])
    out_km.append(out_km[2] + out_km[6] + out_km[10] + out_km[15] + out_km[16])
    out_ml.append(out_ml[2] + out_ml[6] + out_ml[10] + out_ml[15] + out_ml[16])

    df["ugb_ct"] = ugb_ct
    df["ugb_km"] = ugb_km
    df["ugb_ml"] = ugb_ml
    df["out_ct"] = out_ct
    df["out_km"] = out_km
    df["out_ml"] = out_ml

    df.to_csv(CSV_FILE, sep=",", index=False)


infrastructure_report()
