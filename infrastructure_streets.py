import arcpy
from arcpy import env
from sympy import symbols
import sympy.physics.units as u
from sympy.physics.units.systems import SI
from sympy.physics.units import length, meter, foot, mile, kilometer, convert_to
from sympy.physics.units.systems.si import dimsys_SI
import pandas
import logging

arcpy.env.parallelProcessingFactor = "100%"

# Customize these variables to paths on your system
PROJECT_DIR = "C:/Users/erose/projects"
GDB_NAME = "infrastructure_streets.gdb"
WORKSPACE = "C:/Users/erose/projects/infrastructure_streets.gdb"
ARCGIS_PROJECT = "C:/Users/erose/projects/infrastructure/infrastructure.aprx"
LOG_FILE = "P:/infrastructure_streets.log"
CSV_FILE = "P:/infrastructure_streets.csv"

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
logging.info("Importing layers from local database.")
og_streets = "c:/users/erose/projects/infrastructure/infrastructure.gdb/streets"
og_ugb = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.reg_UGB2014"
og_city = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.reg_CITYLIMITS2023"
arcpy.CopyFeatures_management(og_streets, "streets")
arcpy.CopyFeatures_management(og_ugb, "ugb")
arcpy.CopyFeatures_management(og_ugb, "city_limits")

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
        if field_type == None:
            vals.append(val)
        else:
            val_type = row.getValue(field_type)
            if val_type == select_type:
                vals.append(val)
    return vals


def list_street_length_city(street, value, city, in_city=True):
    rows = arcpy.SearchCursor(street)
    vals = []
    for row in rows:
        val = row.getValue(value)
        street_city = row.getValue(city)
        city_test = 1
        if in_city == False:
            city_test = 0
        if street_city == city_test:
            vals.append(val)
    return vals


def list_street_length_city_city_owned(street, value, owner, city, in_city=True):
    rows = arcpy.SearchCursor(street)
    vals = []
    for row in rows:
        val = row.getValue(value)
        street_owner = row.getValue(owner)
        logging.debug(street_owner == "GRANTS PASS")
        street_city = row.getValue(city)
        city_test = 1
        if in_city == False:
            city_test = 0
        if street_owner == "GRANTS PASS" and street_city == city_test:
            vals.append(val)
    return vals


def list_street_length_ugb(street, value, ugb, in_ugb=True):
    rows = arcpy.SearchCursor(street)
    vals = []
    for row in rows:
        val = row.getValue(value)
        street_ugb = row.getValue(ugb)
        ugb_test = 1
        if in_ugb == False:
            ugb_test = 0
        if street_ugb == ugb_test:
            vals.append(val)
    return vals


def list_street_length_ugb_city_owned(street, value, owner, ugb, in_ugb=True):
    rows = arcpy.SearchCursor(street)
    vals = []
    for row in rows:
        val = row.getValue(value)
        street_owner = row.getValue(owner)
        logging.debug(street_owner == "GRANTS PASS")
        street_ugb = row.getValue(ugb)
        ugb_test = 1
        if in_ugb == False:
            ugb_test = 0
        if street_owner == "GRANTS PASS" and street_ugb == ugb_test:
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


street_type = [
    "local_street",
    "local_collector",
    "collector",
    "arterial",
    "highway",
    "blm",
]

# sql select statements for SelectLayerByAttribute
local_street_select = "localtype IN ('7', '8', '9', '14', '0', '99')"
local_collector_select = "localtype IN ('6')"
collector_select = "localtype IN ('5')"
arterial_select = "localtype IN ('3', '4', '10')"
highway_select = "localtype IN ('1', '2')"
blm_select = "localtype IN ('11', '12')"

# dictionary key=street type, value=select statement
street_dict = {}
street_dict[street_type[0]] = local_street_select
street_dict[street_type[1]] = local_collector_select
street_dict[street_type[2]] = collector_select
street_dict[street_type[3]] = arterial_select
street_dict[street_type[4]] = highway_select
street_dict[street_type[5]] = blm_select


def streets_city(street_type, streets="streets"):
    # subset street layer by type
    logging.info("Subsetting street type %s.", street_type)
    arcpy.management.SelectLayerByAttribute(
        streets, "NEW_SELECTION", street_dict.get(street_type)
    )
    arcpy.management.CopyFeatures("streets", street_type)
    arcpy.management.SelectLayerByAttribute(streets, "CLEAR_SELECTION")

    # field map for street_type
    fms = arcpy.FieldMappings()
    field_map(fms, street_type, "st_owner", "owner", "First")
    field_map(fms, street_type, "name", "id", "First")

    logging.info("Counting %s within city.", street_type)
    arcpy.analysis.SpatialJoin(
        street_type,
        "city_limits",
        street_type + "_city",
        "#",
        "#",
        fms,
        "INTERSECT",
    )


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
    field_map(fms, street_type, "st_owner", "owner", "First")
    field_map(fms, street_type, "name", "id", "First")

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
    streets_city(street)
    streets_ugb(street)


def infrastructure_report():
    report_names = [
        "Local Streets",
        "Local Collector",
        "Collector",
        "Arterial",
        "Highway",
        "BLM",
        "Total",
    ]
    df = pandas.DataFrame(data={"name": report_names})

    city_all_ct = []
    city_own_ct = []
    city_all_km = []
    city_own_km = []
    city_all_ml = []
    city_own_ml = []
    ugb_all_ct = []
    ugb_own_ct = []
    ugb_all_km = []
    ugb_own_km = []
    ugb_all_ml = []
    ugb_own_ml = []

    # index 0
    local_street_city_all_ct = list_street_length_city(
        "local_street_city", "id", "Join_Count", True
    )
    local_street_city_own_ct = list_street_length_city_city_owned(
        "local_street_city", "id", "owner", "Join_Count", True
    )
    local_street_ugb_all_ct = list_street_length_ugb(
        "local_street_ugb", "id", "Join_Count", True
    )
    local_street_ugb_own_ct = list_street_length_ugb_city_owned(
        "local_street_ugb", "id", "owner", "Join_Count", True
    )

    city_all_ct.append(report_count(local_street_city_all_ct))
    city_own_ct.append(report_count(local_street_city_own_ct))
    ugb_all_ct.append(report_count(local_street_ugb_all_ct) - city_all_ct[0])
    ugb_own_ct.append(report_count(local_street_ugb_own_ct) - city_own_ct[0])

    local_street_city_all_km = list_street_length_city(
        "local_street_city", "Shape_Length", "Join_Count"
    )
    local_street_city_own_km = list_street_length_city_city_owned(
        "local_street_city", "Shape_Length", "owner", "Join_Count"
    )
    local_street_ugb_all_km = list_street_length_city(
        "local_street_ugb", "Shape_Length", "Join_Count"
    )
    local_street_ugb_own_km = list_street_length_city_city_owned(
        "local_street_ugb", "Shape_Length", "owner", "Join_Count"
    )

    city_all_km.append(report_length(local_street_city_all_km))
    city_own_km.append(report_length(local_street_city_own_km))
    ugb_all_km.append(report_length(local_street_ugb_all_km) - city_all_km[0])
    ugb_own_km.append(report_length(local_street_ugb_own_km) - city_own_km[0])

    city_all_ml.append(report_length(local_street_city_all_km, "miles"))
    city_own_ml.append(report_length(local_street_city_own_km, "miles"))
    ugb_all_ml.append(report_length(local_street_ugb_all_km, "miles") - city_all_ml[0])
    ugb_own_ml.append(report_length(local_street_ugb_own_km, "miles") - city_own_ml[0])

    # index 1
    local_collector_city_all_ct = list_street_length_city(
        "local_collector_city", "id", "Join_Count", True
    )
    local_collector_city_own_ct = list_street_length_city_city_owned(
        "local_collector_city", "id", "owner", "Join_Count", True
    )
    local_collector_ugb_all_ct = list_street_length_ugb(
        "local_collector_ugb", "id", "Join_Count", True
    )
    local_collector_ugb_own_ct = list_street_length_ugb_city_owned(
        "local_collector_ugb", "id", "owner", "Join_Count", True
    )

    city_all_ct.append(report_count(local_collector_city_all_ct))
    city_own_ct.append(report_count(local_collector_city_own_ct))
    ugb_all_ct.append(report_count(local_collector_ugb_all_ct) - city_all_ct[1])
    ugb_own_ct.append(report_count(local_collector_ugb_own_ct) - city_own_ct[1])

    local_collector_city_all_km = list_street_length_city(
        "local_collector_city", "Shape_Length", "Join_Count"
    )
    local_collector_city_own_km = list_street_length_city_city_owned(
        "local_collector_city", "Shape_Length", "owner", "Join_Count"
    )
    local_collector_ugb_all_km = list_street_length_city(
        "local_collector_ugb", "Shape_Length", "Join_Count"
    )
    local_collector_ugb_own_km = list_street_length_city_city_owned(
        "local_collector_ugb", "Shape_Length", "owner", "Join_Count"
    )

    city_all_km.append(report_length(local_collector_city_all_km))
    city_own_km.append(report_length(local_collector_city_own_km))
    ugb_all_km.append(report_length(local_collector_ugb_all_km) - city_all_km[1])
    ugb_own_km.append(report_length(local_collector_ugb_own_km) - city_own_km[1])

    city_all_ml.append(report_length(local_collector_city_all_km, "miles"))
    city_own_ml.append(report_length(local_collector_city_own_km, "miles"))
    ugb_all_ml.append(
        report_length(local_collector_ugb_all_km, "miles") - city_all_ml[1]
    )
    ugb_own_ml.append(
        report_length(local_collector_ugb_own_km, "miles") - city_own_ml[1]
    )

    # index 2
    collector_city_all_ct = list_street_length_city(
        "collector_city", "id", "Join_Count", True
    )
    collector_city_own_ct = list_street_length_city_city_owned(
        "collector_city", "id", "owner", "Join_Count", True
    )
    collector_ugb_all_ct = list_street_length_ugb(
        "collector_ugb", "id", "Join_Count", True
    )
    collector_ugb_own_ct = list_street_length_ugb_city_owned(
        "collector_ugb", "id", "owner", "Join_Count", True
    )

    city_all_ct.append(report_count(collector_city_all_ct))
    city_own_ct.append(report_count(collector_city_own_ct))
    ugb_all_ct.append(report_count(collector_ugb_all_ct) - city_all_ct[2])
    ugb_own_ct.append(report_count(collector_ugb_own_ct) - city_own_ct[2])

    collector_city_all_km = list_street_length_city(
        "collector_city", "Shape_Length", "Join_Count"
    )
    collector_city_own_km = list_street_length_city_city_owned(
        "collector_city", "Shape_Length", "owner", "Join_Count"
    )
    collector_ugb_all_km = list_street_length_city(
        "collector_ugb", "Shape_Length", "Join_Count"
    )
    collector_ugb_own_km = list_street_length_city_city_owned(
        "collector_ugb", "Shape_Length", "owner", "Join_Count"
    )

    city_all_km.append(report_length(collector_city_all_km))
    city_own_km.append(report_length(collector_city_own_km))
    ugb_all_km.append(report_length(collector_ugb_all_km) - city_all_km[2])
    ugb_own_km.append(report_length(collector_ugb_own_km) - city_own_km[2])

    city_all_ml.append(report_length(collector_city_all_km, "miles"))
    city_own_ml.append(report_length(collector_city_own_km, "miles"))
    ugb_all_ml.append(report_length(collector_ugb_all_km, "miles") - city_all_ml[2])
    ugb_own_ml.append(report_length(collector_ugb_own_km, "miles") - city_own_ml[2])

    # index 3
    arterial_city_all_ct = list_street_length_city(
        "arterial_city", "id", "Join_Count", True
    )
    arterial_city_own_ct = list_street_length_city_city_owned(
        "arterial_city", "id", "owner", "Join_Count", True
    )
    arterial_ugb_all_ct = list_street_length_ugb(
        "arterial_ugb", "id", "Join_Count", True
    )
    arterial_ugb_own_ct = list_street_length_ugb_city_owned(
        "arterial_ugb", "id", "owner", "Join_Count", True
    )

    city_all_ct.append(report_count(arterial_city_all_ct))
    city_own_ct.append(report_count(arterial_city_own_ct))
    ugb_all_ct.append(report_count(arterial_ugb_all_ct) - city_all_ct[3])
    ugb_own_ct.append(report_count(arterial_ugb_own_ct) - city_own_ct[3])

    arterial_city_all_km = list_street_length_city(
        "arterial_city", "Shape_Length", "Join_Count"
    )
    arterial_city_own_km = list_street_length_city_city_owned(
        "arterial_city", "Shape_Length", "owner", "Join_Count"
    )
    arterial_ugb_all_km = list_street_length_city(
        "arterial_ugb", "Shape_Length", "Join_Count"
    )
    arterial_ugb_own_km = list_street_length_city_city_owned(
        "arterial_ugb", "Shape_Length", "owner", "Join_Count"
    )

    city_all_km.append(report_length(arterial_city_all_km))
    city_own_km.append(report_length(arterial_city_own_km))
    ugb_all_km.append(report_length(arterial_ugb_all_km) - city_all_km[3])
    ugb_own_km.append(report_length(arterial_ugb_own_km) - city_own_km[3])

    city_all_ml.append(report_length(arterial_city_all_km, "miles"))
    city_own_ml.append(report_length(arterial_city_own_km, "miles"))
    ugb_all_ml.append(report_length(arterial_ugb_all_km, "miles") - city_all_ml[3])
    ugb_own_ml.append(report_length(arterial_ugb_own_km, "miles") - city_own_ml[3])

    # index 4
    highway_city_all_ct = list_street_length_city(
        "highway_city", "id", "Join_Count", True
    )
    highway_city_own_ct = list_street_length_city_city_owned(
        "highway_city", "id", "owner", "Join_Count", True
    )
    highway_ugb_all_ct = list_street_length_ugb("highway_ugb", "id", "Join_Count", True)
    highway_ugb_own_ct = list_street_length_ugb_city_owned(
        "highway_ugb", "id", "owner", "Join_Count", True
    )

    city_all_ct.append(report_count(highway_city_all_ct))
    city_own_ct.append(report_count(highway_city_own_ct))
    ugb_all_ct.append(report_count(highway_ugb_all_ct) - city_all_ct[4])
    ugb_own_ct.append(report_count(highway_ugb_own_ct) - city_own_ct[4])

    highway_city_all_km = list_street_length_city(
        "highway_city", "Shape_Length", "Join_Count"
    )
    highway_city_own_km = list_street_length_city_city_owned(
        "highway_city", "Shape_Length", "owner", "Join_Count"
    )
    highway_ugb_all_km = list_street_length_city(
        "highway_ugb", "Shape_Length", "Join_Count"
    )
    highway_ugb_own_km = list_street_length_city_city_owned(
        "highway_ugb", "Shape_Length", "owner", "Join_Count"
    )

    city_all_km.append(report_length(highway_city_all_km))
    city_own_km.append(report_length(highway_city_own_km))
    ugb_all_km.append(report_length(highway_ugb_all_km) - city_all_km[4])
    ugb_own_km.append(report_length(highway_ugb_own_km) - city_own_km[4])

    city_all_ml.append(report_length(highway_city_all_km, "miles"))
    city_own_ml.append(report_length(highway_city_own_km, "miles"))
    ugb_all_ml.append(report_length(highway_ugb_all_km, "miles") - city_all_ml[4])
    ugb_own_ml.append(report_length(highway_ugb_own_km, "miles") - city_own_ml[4])

    # index 5
    blm_city_all_ct = list_street_length_city("blm_city", "id", "Join_Count", True)
    blm_city_own_ct = list_street_length_city_city_owned(
        "blm_city", "id", "owner", "Join_Count", True
    )
    blm_ugb_all_ct = list_street_length_ugb("blm_ugb", "id", "Join_Count", True)
    blm_ugb_own_ct = list_street_length_ugb_city_owned(
        "blm_ugb", "id", "owner", "Join_Count", True
    )

    city_all_ct.append(report_count(blm_city_all_ct))
    city_own_ct.append(report_count(blm_city_own_ct))
    ugb_all_ct.append(report_count(blm_ugb_all_ct) - city_all_ct[5])
    ugb_own_ct.append(report_count(blm_ugb_own_ct) - city_own_ct[5])

    blm_city_all_km = list_street_length_city("blm_city", "Shape_Length", "Join_Count")
    blm_city_own_km = list_street_length_city_city_owned(
        "blm_city", "Shape_Length", "owner", "Join_Count"
    )
    blm_ugb_all_km = list_street_length_city("blm_ugb", "Shape_Length", "Join_Count")
    blm_ugb_own_km = list_street_length_city_city_owned(
        "blm_ugb", "Shape_Length", "owner", "Join_Count"
    )

    city_all_km.append(report_length(blm_city_all_km))
    city_own_km.append(report_length(blm_city_own_km))
    ugb_all_km.append(report_length(blm_ugb_all_km) - city_all_km[5])
    ugb_own_km.append(report_length(blm_ugb_own_km) - city_own_km[5])

    city_all_ml.append(report_length(blm_city_all_km, "miles"))
    city_own_ml.append(report_length(blm_city_own_km, "miles"))
    ugb_all_ml.append(report_length(blm_ugb_all_km, "miles") - city_all_ml[5])
    ugb_own_ml.append(report_length(blm_ugb_own_km, "miles") - city_own_ml[5])

    # total
    city_all_ct.append(
        city_all_ct[0]
        + city_all_ct[1]
        + city_all_ct[2]
        + city_all_ct[3]
        + city_all_ct[4]
        + city_all_ct[5]
    )
    city_own_ct.append(
        city_own_ct[0]
        + city_own_ct[1]
        + city_own_ct[2]
        + city_own_ct[3]
        + city_own_ct[4]
        + city_own_ct[5]
    )
    city_all_km.append(
        city_all_km[0]
        + city_all_km[1]
        + city_all_km[2]
        + city_all_km[3]
        + city_all_km[4]
        + city_all_km[5]
    )
    city_own_km.append(
        city_own_km[0]
        + city_own_km[1]
        + city_own_km[2]
        + city_own_km[3]
        + city_own_km[4]
        + city_own_km[5]
    )
    city_all_ml.append(
        city_all_ml[0]
        + city_all_ml[1]
        + city_all_ml[2]
        + city_all_ml[3]
        + city_all_ml[4]
        + city_all_ml[5]
    )
    city_own_ml.append(
        city_own_ml[0]
        + city_own_ml[1]
        + city_own_ml[2]
        + city_own_ml[3]
        + city_own_ml[4]
        + city_own_ml[5]
    )

    ugb_all_ct.append(
        ugb_all_ct[0]
        + ugb_all_ct[1]
        + ugb_all_ct[2]
        + ugb_all_ct[3]
        + ugb_all_ct[4]
        + ugb_all_ct[5]
    )
    ugb_own_ct.append(
        ugb_own_ct[0]
        + ugb_own_ct[1]
        + ugb_own_ct[2]
        + ugb_own_ct[3]
        + ugb_own_ct[4]
        + ugb_own_ct[5]
    )
    ugb_all_km.append(
        ugb_all_km[0]
        + ugb_all_km[1]
        + ugb_all_km[2]
        + ugb_all_km[3]
        + ugb_all_km[4]
        + ugb_all_km[5]
    )
    ugb_own_km.append(
        ugb_own_km[0]
        + ugb_own_km[1]
        + ugb_own_km[2]
        + ugb_own_km[3]
        + ugb_own_km[4]
        + ugb_own_km[5]
    )
    ugb_all_ml.append(
        ugb_all_ml[0]
        + ugb_all_ml[1]
        + ugb_all_ml[2]
        + ugb_all_ml[3]
        + ugb_all_ml[4]
        + ugb_all_ml[5]
    )
    ugb_own_ml.append(
        ugb_own_ml[0]
        + ugb_own_ml[1]
        + ugb_own_ml[2]
        + ugb_own_ml[3]
        + ugb_own_ml[4]
        + ugb_own_ml[5]
    )

    df["City Limits Count"] = city_all_ct
    df["City Limits Kilometers"] = city_all_km
    df["City Limits Miles"] = city_all_ml
    df["City Limits Count - City Owned"] = city_own_ct
    df["City Limits Kilometers - City Owned"] = city_own_km
    df["City Limits Miles - City Owned"] = city_own_ml
    df["UGB Count"] = ugb_all_ct
    df["UGB Kilometers"] = ugb_all_km
    df["UGB Miles"] = ugb_all_ml
    df["UGB Count - City Owned"] = ugb_own_ct
    df["UGB Kilometers - City Owned"] = ugb_own_km
    df["UGB Miles - City Owned"] = ugb_own_ml

    df.to_csv(CSV_FILE, sep=",", index=False)


infrastructure_report()
