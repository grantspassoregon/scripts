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
GDB_NAME = "missing_sidewalks.gdb"
WORKSPACE = "C:/Users/erose/projects/missing_sidewalks.gdb"
ARCGIS_PROJECT = "P:/projects/sidewalks/sidewalks3.aprx"
LOG_FILE = "P:/missing_sidewalks.log"
CSV_FILE = "P:/missing_sidewalks_report.csv"

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
og_streets = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.tran_StreetPavementCL"
og_sidewalks = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.tran_SIDEWALK"
og_hillslope = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.env_SLOPEHAZARD"
og_addresses = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.land_SITEADDRESSPOINT"
og_taxlots = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.JoCo_FS_Export_1"
arcpy.CopyFeatures_management(og_streets, "streets")
arcpy.CopyFeatures_management(og_sidewalks, "sidewalks")
arcpy.CopyFeatures_management(og_hillslope, "hillslope")
arcpy.CopyFeatures_management(og_addresses, "addresses")
arcpy.CopyFeatures_management(og_taxlots, "taxlots")


# open arcpro project
aprx = arcpy.mp.ArcGISProject(ARCGIS_PROJECT)


# for use in CalculateField calls
# caps number of sidewalks per side to one
# some joins return 2 sidewalks on a single side for some reason
block = """
def ceiling(sidewalks):
    if sidewalks > 1:
        return 1
    else:
        return sidewalks
"""

# loop through street classifications
# use list to store street types
# and dict to store sql select statements for each type
street_type = [
    "local_street",
    "local_collector",
    "collector",
    "arterial",
    "state_street",
    "private_street",
    "park_street",
]

# Row labels for csv report
street_class_names = [
    "Local Street",
    "Local Collector",
    "Collector",
    "Arterial",
    "State Street",
    "Private Street",
    "Park Street",
]

# sql select statements for SelectLayerByAttribute
local_street_select = "ROADCLASS = 'Local Street' Or ROADCLASS = 'LOCAL STREET'"
local_collector_select = "ROADCLASS = 'Local Collector'"
collector_select = "ROADCLASS = 'Collector' Or ROADCLASS = 'COLLECTOR'"
arterial_select = "ROADCLASS = 'Arterial' Or ROADCLASS = 'ARTERIAL'"
state_street_select = "ROADCLASS = 'State of Oregon' Or ROADCLASS = 'STATE HIGHWAY'"
private_street_select = "ROADCLASS = 'Private' Or ROADCLASS = 'PRIVATE' Or ROADCLASS = 'Private Street' Or ROADCLASS = 'PRIVATE STREET'"
park_street_select = "ROADCLASS = 'Park'"

# dictionary key=street type, value=select statement
street_dict = {}
street_dict[street_type[0]] = local_street_select
street_dict[street_type[1]] = local_collector_select
street_dict[street_type[2]] = collector_select
street_dict[street_type[3]] = arterial_select
street_dict[street_type[4]] = state_street_select
street_dict[street_type[5]] = private_street_select
street_dict[street_type[6]] = park_street_select


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


def list_sub_field(fc, field_val, field_type=None, select_type=None, sub=None):
    rows = arcpy.SearchCursor(fc)
    vals = []
    for row in rows:
        val = row.getValue(field_val)
        val_sub = row.getValue(sub)
        val_sub = int(val_sub)
        if field_val == "STLength()":
            dist = u.Quantity("d")
            SI.set_quantity_dimension(dist, u.length)
            SI.set_quantity_scale_factor(dist, val * u.foot)
            val = dist
            logging.debug("val is %s.", val)
        if field_type == None:
            if val_sub == 1:
                vals.append(val)
        else:
            val_type = row.getValue(field_type)
            if val_type == select_type and val_sub == 1:
                vals.append(val)
    return vals


def report_length(vals, unit="km"):
    vals_sum = sum(vals)
    dist = u.Quantity("d")
    SI.set_quantity_dimension(dist, u.length)
    SI.set_quantity_scale_factor(dist, vals_sum * u.foot)
    if unit == "km":
        km = convert_to(dist, kilometer).evalf(4)
        # report = "Total length of " + type + ": " + str(km)
        report = km.args[0]
    if unit == "miles":
        ml = convert_to(dist, mile).evalf(4)
        # report = "Total length of " + type + ": " + str(ml)
        report = ml.args[0]
    return report


def report_count(vals):
    vals_set = set(vals)
    vals_uniq = list(vals_set)
    vals_ct = len(vals_uniq)
    # report = "Total count of " + type + ": " + str(vals_ct) + "."
    return vals_ct


def report(street_type=street_type, street_class_names=street_class_names):
    df = pandas.DataFrame(data={"name": street_class_names})

    total_km = []
    total_ml = []
    total_ct = []
    has_sidewalks_km = []
    has_sidewalks_ml = []
    needs_one_km = []
    needs_one_ml = []
    needs_two_km = []
    needs_two_ml = []

    undev_total_km = []
    undev_total_ml = []
    undev_total_ct = []
    undev_has_sidewalks_km = []
    undev_has_sidewalks_ml = []
    undev_needs_one_km = []
    undev_needs_one_ml = []
    undev_needs_two_km = []
    undev_needs_two_ml = []

    for street in street_type:
        street_class = street + "_sidewalks_export"
        needed_sidewalks = street + "_sidewalks_join_needed_sidewalks"
        undeveloped = street + "_undeveloped_undeveloped"

        names = list_field(street_class, street + "_sidewalk_class_" + "FULLNAME")
        undev_names = list_sub_field(
            street_class,
            street + "_sidewalk_class_" + "FULLNAME",
            sub=undeveloped,
        )
        logging.info("undev names is %s.", undev_names)
        vals = list_field(street_class, "Shape_Length")
        undev_vals = list_sub_field(street_class, "Shape_Length", sub=undeveloped)
        logging.info("undev vals is %s.", undev_vals)

        total_ct.append(report_count(names))
        total_km.append(report_length(vals))
        total_ml.append(report_length(vals, "miles"))
        undev_total_ct.append(report_count(undev_names))
        undev_total_km.append(report_length(undev_vals))
        undev_total_ml.append(report_length(undev_vals, "miles"))

        has_sidewalks_vals = list_field(
            street_class, "Shape_Length", needed_sidewalks, "0"
        )
        undev_has_sidewalks_vals = list_sub_field(
            street_class, "Shape_Length", needed_sidewalks, "0", undeveloped
        )
        has_sidewalks_km.append(report_length(has_sidewalks_vals))
        has_sidewalks_ml.append(report_length(has_sidewalks_vals, "miles"))
        undev_has_sidewalks_km.append(report_length(undev_has_sidewalks_vals))
        undev_has_sidewalks_ml.append(report_length(undev_has_sidewalks_vals, "miles"))

        needs_one_vals = list_field(street_class, "Shape_Length", needed_sidewalks, "1")
        undev_needs_one_vals = list_sub_field(
            street_class, "Shape_Length", needed_sidewalks, "1", undeveloped
        )
        needs_one_km.append(report_length(needs_one_vals))
        needs_one_ml.append(report_length(needs_one_vals, "miles"))
        undev_needs_one_km.append(report_length(undev_needs_one_vals))
        undev_needs_one_ml.append(report_length(undev_needs_one_vals, "miles"))

        needs_two_vals = list_field(street_class, "Shape_Length", needed_sidewalks, "2")
        undev_needs_two_vals = list_sub_field(
            street_class, "Shape_Length", needed_sidewalks, "2", undeveloped
        )
        needs_two_km.append(report_length(needs_two_vals))
        needs_two_ml.append(report_length(needs_two_vals, "miles"))
        undev_needs_two_km.append(report_length(undev_needs_two_vals))
        undev_needs_two_ml.append(report_length(undev_needs_two_vals, "miles"))

    df["total_count"] = total_ct
    df["total_kilometers"] = total_km
    df["total_miles"] = total_ml
    df["has_sidewalks_kilometers"] = has_sidewalks_km
    df["has_sidewalks_miles"] = has_sidewalks_ml
    df["needs_one_kilometers"] = needs_one_km
    df["needs_one_miles"] = needs_one_ml
    df["needs_two_kilometers"] = needs_two_km
    df["needs_two_miles"] = needs_two_ml

    df["undev_total_count"] = undev_total_ct
    df["undev_total_kilometers"] = undev_total_km
    df["undev_total_miles"] = undev_total_ml
    df["undev_has_sidewalks_kilometers"] = undev_has_sidewalks_km
    df["undev_has_sidewalks_miles"] = undev_has_sidewalks_ml
    df["undev_needs_one_kilometers"] = undev_needs_one_km
    df["undev_needs_one_miles"] = undev_needs_one_ml
    df["undev_needs_two_kilometers"] = undev_needs_two_km
    df["undev_needs_two_miles"] = undev_needs_two_ml

    df.to_csv(CSV_FILE, sep=",", index=False)


def street_buffers(
    street_type,
    buffer_dist="70 Feet",
    streets_split="streets_split",
    sidewalks="sidewalks",
):
    """
    Subset the streets layer by classification and build a buffer on both sides
    of the street for the subset.

    :param street_type: The street classification to subset.
    :type street_type: String
    :param buffer_dist: Linear distance to draw the buffer.
    :type buffer_dist: String
    :param streets_split: Streets layer split into small segments, defaults to 'streets_split'.
    :type streets_split: String
    :param sidewalks: Sidewalks layer to capture with buffer.
    :type sidewalks: String
    :return: Produces a subset streets layer, right and left buffers, and buffers with sidewalk count.
    :rtype: None
    """
    # subset street layer by type
    logging.info("Subsetting street type %s.", street_type)
    arcpy.management.SelectLayerByAttribute(
        streets_split, "NEW_SELECTION", street_dict.get(street_type)
    )
    arcpy.management.CopyFeatures("streets_split", street_type)
    arcpy.management.SelectLayerByAttribute(streets_split, "CLEAR_SELECTION")

    # buffer street layer to overlay sidewalks on either side
    logging.info("Buffering left and right sides of %s.", street_type)
    buff_left = street_type + "_buff_left"
    arcpy.analysis.Buffer(street_type, buff_left, buffer_dist, "LEFT", "FLAT", "NONE")
    buff_right = street_type + "_buff_right"
    arcpy.analysis.Buffer(
        street_type,
        buff_right,
        buffer_dist,
        "RIGHT",
        "FLAT",
        "NONE",
    )

    # counts sidewalks overlain by street buffer
    logging.info("Counting sidewalks within buffers for %s.", street_type)
    buff_left_sidewalks = buff_left + "_sidewalks"
    arcpy.analysis.SpatialJoin(
        buff_left,
        sidewalks,
        buff_left_sidewalks,
        "#",
        "#",
        "Count",
        "INTERSECT",
    )

    buff_right_sidewalks = buff_right + "_sidewalks"
    arcpy.analysis.SpatialJoin(
        buff_right,
        sidewalks,
        buff_right_sidewalks,
        "#",
        "#",
        "Count",
        "INTERSECT",
    )

    logging.info("Counting undeveloped lots within buffers for %s.", street_type)
    buff_left_undeveloped = buff_left + "_undeveloped"
    arcpy.analysis.SpatialJoin(
        buff_left,
        "undeveloped_lots",
        buff_left_undeveloped,
        "#",
        "#",
        "Count",
        "INTERSECT",
    )

    buff_right_undeveloped = buff_right + "_undeveloped"
    arcpy.analysis.SpatialJoin(
        buff_right,
        "undeveloped_lots",
        buff_right_undeveloped,
        "#",
        "#",
        "Count",
        "INTERSECT",
    )


def count_sidewalks(street_type):
    """
    Add sidewalk count from street buffers to street line and sum.
    Uses output from street_buffers().

    :param street_type: The street classification of interest from the streets layer.
    :type street_type: String
    :return: Produces a copy of the streets layer with sidewalks fields added.
    :rtype: None
    """
    # map spatial join count to field name "sidewalks_left"
    buff_left_sidewalks = street_type + "_buff_left_sidewalks"
    fm_left = arcpy.FieldMap()
    fm_left.addInputField(buff_left_sidewalks, "Join_Count")
    fm_left.mergeRule = "First"
    fm_name = fm_left.outputField
    fm_name.name = "sidewalks_left"
    fm_name.aliasName = "sidewalks_left"
    fm_left.outputField = fm_name
    fms = arcpy.FieldMappings()
    fms.addFieldMap(fm_left)

    # join sidewalks counted by buffer to street line
    logging.info("Adding sidewalk count to line layer for %s.", street_type)
    sidewalks_left = street_type + "_sidewalks_left"
    arcpy.analysis.SpatialJoin(
        street_type,
        buff_left_sidewalks,
        sidewalks_left,
        "#",
        "#",
        fms,
        "INTERSECT",
    )

    # if two sidewalks counted on one side, adjust to one
    # only one sidewalk max on each side of the street
    arcpy.management.CalculateField(
        sidewalks_left,
        "sidewalks_left",
        "ceiling(!sidewalks_left!)",
        "PYTHON3",
        block,
    )

    # map spatial join count to field name "sidewalks_right"
    buff_right_sidewalks = street_type + "_buff_right_sidewalks"
    fm_right = arcpy.FieldMap()
    fm_right.addInputField(buff_right_sidewalks, "Join_Count")
    fm_right.mergeRule = "First"
    fm_name = fm_right.outputField
    fm_name.name = "sidewalks_right"
    fm_name.aliasName = "sidewalks_right"
    fm_right.outputField = fm_name
    fms = arcpy.FieldMappings()
    fms.addFieldMap(fm_right)

    # join sidewalks counted by buffer to street line
    sidewalks_right = street_type + "_sidewalks_right"
    arcpy.analysis.SpatialJoin(
        street_type,
        buff_right_sidewalks,
        sidewalks_right,
        "#",
        "#",
        fms,
        "INTERSECT",
    )

    # if two sidewalks counted on one side, adjust to one
    # only one sidewalk max on each side of the street
    arcpy.management.CalculateField(
        sidewalks_right,
        "sidewalks_right",
        "ceiling(!sidewalks_right!)",
        "PYTHON3",
        block,
    )

    # defensive copy of layer to join
    logging.info("Creating sidewalks join layer for %s.", street_type)
    sidewalks_join = street_type + "_sidewalks"
    arcpy.CopyFeatures_management(sidewalks_left, sidewalks_join)

    # join right and left street sides to count sidewalks on both sides
    arcpy.management.AddJoin(
        sidewalks_join,
        "OBJECTID",
        sidewalks_right,
        "OBJECTID",
        "KEEP_COMMON",
    )

    # add field for total sidewalks (right and left)
    expr = (
        "!"
        + sidewalks_join
        + ".sidewalks_left! + !"
        + sidewalks_right
        + ".sidewalks_right!"
    )
    logging.info("Summing sidewalk count for %s.", street_type)
    arcpy.management.CalculateField(
        sidewalks_join,
        "sidewalks",
        expr,
    )


def count_undeveloped(street_type):
    """
    Add undeveloped lot count from street buffers to street line and sum.
    Uses output from street_buffers().

    :param street_type: The street classification of interest from the streets layer.
    :type street_type: String
    :return: Produces a copy of the streets layer with undeveloped lot fields added.
    :rtype: None
    """
    # map spatial join count to field name "undeveloped_left"
    buff_left_undeveloped = street_type + "_buff_left_undeveloped"
    fm_left = arcpy.FieldMap()
    fm_left.addInputField(buff_left_undeveloped, "Join_Count")
    fm_left.mergeRule = "First"
    fm_name = fm_left.outputField
    fm_name.name = "undeveloped_left"
    fm_name.aliasName = "undeveloped_left"
    fm_left.outputField = fm_name
    fms = arcpy.FieldMappings()
    fms.addFieldMap(fm_left)

    # join sidewalks counted by buffer to street line
    logging.info("Adding undeveloped lot count to line layer for %s.", street_type)
    undeveloped_left = street_type + "_undeveloped_left"
    arcpy.analysis.SpatialJoin(
        street_type,
        buff_left_undeveloped,
        undeveloped_left,
        "#",
        "#",
        fms,
        "INTERSECT",
    )

    # streets segments are only adjacent to one undeveloped lot max
    arcpy.management.CalculateField(
        undeveloped_left,
        "undeveloped_left",
        "ceiling(!undeveloped_left!)",
        "PYTHON3",
        block,
    )

    # map spatial join count to field name "undeveloped_right"
    buff_right_undeveloped = street_type + "_buff_right_undeveloped"
    fm_right = arcpy.FieldMap()
    fm_right.addInputField(buff_right_undeveloped, "Join_Count")
    fm_right.mergeRule = "First"
    fm_name = fm_right.outputField
    fm_name.name = "undeveloped_right"
    fm_name.aliasName = "undeveloped_right"
    fm_right.outputField = fm_name
    fms = arcpy.FieldMappings()
    fms.addFieldMap(fm_right)

    # join undeveloped lots counted by buffer to street line
    undeveloped_right = street_type + "_undeveloped_right"
    arcpy.analysis.SpatialJoin(
        street_type,
        buff_right_undeveloped,
        undeveloped_right,
        "#",
        "#",
        fms,
        "INTERSECT",
    )

    # streets segments are only adjacent to one undeveloped lot max
    arcpy.management.CalculateField(
        undeveloped_right,
        "undeveloped_right",
        "ceiling(!undeveloped_right!)",
        "PYTHON3",
        block,
    )

    # defensive copy of layer to join
    logging.info("Creating undeveloped lots join layer for %s.", street_type)
    undeveloped_join = street_type + "_undeveloped"
    arcpy.management.CopyFeatures(undeveloped_left, undeveloped_join)

    # join right and left street sides to count undeveloped lots on both sides
    arcpy.management.AddJoin(
        undeveloped_join,
        "OBJECTID",
        undeveloped_right,
        "OBJECTID",
        "KEEP_COMMON",
    )

    # add field for total (right and left)
    expr = (
        "!"
        + undeveloped_join
        + ".undeveloped_left! + !"
        + undeveloped_right
        + ".undeveloped_right!"
    )
    logging.info("Summing undeveloped lots count for %s.", street_type)
    arcpy.management.CalculateField(
        undeveloped_join,
        "undeveloped",
        expr,
    )

    # field "undeveloped" capped at one (boolean indicating whether next to undeveloped lot or not)
    arcpy.management.CalculateField(
        undeveloped_join,
        "undeveloped",
        "ceiling(int(!" + undeveloped_join + ".undeveloped!))",
        "PYTHON3",
        block,
    )


def sidewalks_needed(street_type, few_units="few_units_served", expr=block):
    """
    Number of units served by each street is based on the number of
    addresses registered at each tax lot served by the street.  The few_units layer
    is based on buffers around each street to capture nearby taxlots for a spatial
    join, so the length of the street line (how the street line is segmented in
    the streets feature class) determines which lots the street serves.

    Uses a spatial join to determine which streets are on steep slopes.  If on a steep
    slope, or serving less than four units, only one sidewalk is required.  Subtracts
    current sidewalks from required sidewalks to determine sidewalks needed.

    :param street_type: The street classification of interest from the streets layer.
    :type street_type: String
    :param few_units: Layer indicating streets that serve four units or less.
    :type few_units: String
    :return: Produces "sidewalk_units", "sidewalk_hills" and "sidewalk_join" layers,
    indicating the number of sidewalks needed.
    :rtype: None
    """
    logging.info("Adding field indicating few units served to %s layer.", street_type)
    sidewalks = street_type + "_sidewalks"
    sidewalk_units = street_type + "_sidewalk_units"
    arcpy.analysis.SpatialJoin(
        sidewalks,
        few_units,
        sidewalk_units,
        "#",
        "KEEP_ALL",
        "Count",
        "INTERSECT",
    )

    arcpy.management.CalculateField(
        sidewalk_units,
        "few_units",
        "ceiling(!Join_Count!)",
        "PYTHON3",
        expr,
    )

    arcpy.management.DeleteField(sidewalk_units, ["Join_Count", "TARGET_FID", "Count"])

    logging.info("Adding field indicated steep slope to %s layer.", street_type)
    sidewalk_hills = street_type + "_sidewalk_hills"
    arcpy.analysis.SpatialJoin(
        sidewalk_units,
        "hillslope",
        sidewalk_hills,
        "#",
        "KEEP_ALL",
        "Count",
        "INTERSECT",
    )

    arcpy.management.CalculateField(
        sidewalk_hills,
        "hills",
        "ceiling(!Join_Count!)",
        "PYTHON3",
        expr,
    )

    arcpy.management.DeleteField(sidewalk_hills, ["Join_Count", "TARGET_FID", "Count"])

    logging.info(
        "Joining sidewalks count with units served and steep slope for %s.", street_type
    )
    sidewalks_join = street_type + "_sidewalks_join"
    arcpy.CopyFeatures_management(
        sidewalks,
        sidewalks_join,
    )

    arcpy.management.AddJoin(
        sidewalks_join,
        "OBJECTID",
        sidewalk_units,
        "OBJECTID",
    )
    arcpy.management.AddJoin(
        sidewalks_join,
        "OBJECTID",
        sidewalk_hills,
        "OBJECTID",
    )

    logging.info("Calculating sidewalks needed for %s.", street_type)
    arcpy.management.CalculateField(
        sidewalks_join,
        "required_sidewalks",
        "2 - int(max(!few_units!, !hills!))",
    )

    sidewalks_name = "!" + sidewalks_join + "." + sidewalks + "_sidewalks!"
    arcpy.management.CalculateField(
        sidewalks_join,
        "needed_sidewalks",
        "max(0, int(!required_sidewalks!) - int(" + sidewalks_name + "))",
    )

    logging.info(
        "Joining undeveloped lots field to sidewalks needed layer for %s.", street_type
    )
    undeveloped_join = street_type + "_undeveloped"
    arcpy.management.AddJoin(
        sidewalks_join,
        sidewalks_join + ".OBJECTID",
        undeveloped_join,
        undeveloped_join + ".OBJECTID",
    )


def unsplit_streets(street_type):
    """
    Merges the segmented street layer back into a continuous line, preserving
    fields for street name, the number of sidewalks needed and whether the lot
    is undeveloped.  Exports the layer as a feature class to eliminate in-memory
    joins, required to publish the feature class to a web map.

    :param street_type: The street classification of interest from the streets layer.
    :type street_type: String
    :return: Produces "sidewalks_unsplit" and "sidewalks_export" layers for each street type.
    :rtype: None
    """
    sidewalks_join = street_type + "_sidewalks_join"
    sidewalk_class = street_type + "_sidewalk_class"
    logging.info("Subsetting street layer to capture street names for %s.", street_type)
    arcpy.management.CopyFeatures(
        street_type,
        sidewalk_class,
    )

    arcpy.management.DeleteField(sidewalk_class, "FULLNAME", "KEEP_FIELDS")

    logging.info("Adding street name to sidewalks join layer for %s.", street_type)
    arcpy.management.AddJoin(
        sidewalks_join,
        "OBJECTID",
        sidewalk_class,
        "OBJECTID",
    )

    sidewalks_unsplit = street_type + "_sidewalks_unsplit"
    undeveloped = street_type + "_undeveloped"
    road_name = sidewalk_class + ".FULLNAME"
    needed_sidewalks_name = sidewalks_join + ".needed_sidewalks"
    undeveloped_name = undeveloped + ".undeveloped"
    logging.info("Unsplitting streets lines for %s.", street_type)
    arcpy.management.UnsplitLine(
        sidewalks_join,
        sidewalks_unsplit,
        [road_name, needed_sidewalks_name, undeveloped_name],
    )

    # export in-memory joins to publish on web
    sidewalks_export = street_type + "_sidewalks_export"
    logging.info("Exporting %s layer for web map publishing.", street_type)
    arcpy.conversion.FeatureClassToFeatureClass(
        sidewalks_unsplit, env.workspace, sidewalks_export
    )


# streets that serve four units or less require only one sidewalk
# determine how many units a street serves by addresses
# number of addresses at each tax lot
logging.info("Calculating units served at each tax lot.")
arcpy.analysis.SpatialJoin(
    "taxlots",
    "addresses",
    "lot_address_count",
    "JOIN_ONE_TO_ONE",
    "KEEP_ALL",
    "COUNT",
    "Intersects",
)

logging.info("Creating undeveloped taxlots layer.")
arcpy.management.SelectLayerByAttribute(
    "lot_address_count", "NEW_SELECTION", "Join_Count = 0"
)
arcpy.management.CopyFeatures("lot_address_count", "undeveloped_lots")
arcpy.management.SelectLayerByAttribute("lot_address_count", "CLEAR_SELECTION")

# buffer streets layer to estimate how many tax lots they serve
# false positives from corner lots, primary access from only one street
logging.info("Buffering street layer for address count.")
arcpy.analysis.Buffer("streets", "streets_buff", "60 Feet", "FULL", "ROUND", "NONE")

# set field map rules for spatial join
# addresses per lot set to "Units_Served" field
fm_lot_count = arcpy.FieldMap()
fm_lot_count.addInputField("lot_address_count", "Join_Count")
fm_street = arcpy.FieldMap()
fm_street.addInputField("streets_buff", "ROADCLASS")
fm_lot_count.mergeRule = "Sum"
fm_name = fm_lot_count.outputField
fm_name.name = "Units_Served"
fm_name.aliasName = "Units_Served"
fm_lot_count.outputField = fm_name

fms = arcpy.FieldMappings()
fms.addFieldMap(fm_lot_count)
fms.addFieldMap(fm_street)

# units served per street by buffer overlap
logging.info("Counting units served per street using buffer layer.")
arcpy.analysis.SpatialJoin(
    "streets_buff", "lot_address_count", "streets_units_served", "#", "KEEP_ALL", fms
)

# street buffer for lots serving four units or less
units_select = "Units_Served <= 4 And ROADCLASS <> 'STATE_HIGHWAY' And ROADCLASS <> 'State of Oregon'"
arcpy.management.SelectLayerByAttribute(
    "streets_units_served", "NEW_SELECTION", units_select
)
arcpy.management.CopyFeatures("streets_units_served", "few_units_served")

# split streets layer into 1 foot segments
logging.info("Splitting street layer into segments.")
arcpy.edit.Densify("streets", "DISTANCE", "1 Feet")
arcpy.management.SplitLine("streets", "streets_split")

# if joined before Densify, throws an error
# join units served back to original streets layer
# arcpy.management.AddJoin("streets_split", "ORIG_FID", "streets_units_served", "OBJECTID")

for street in street_type:
    street_buffers(street)
    count_sidewalks(street)
    count_undeveloped(street)
    sidewalks_needed(street)
    unsplit_streets(street)

logging.info("Calculating summary statistics.")
report()
