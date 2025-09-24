import arcpy
from arcpy import metadata as md
import logging
import os

# configure environment in arcpy
arcpy.env.parallelProcessingFactor = "100%"  # try to be parallel
arcpy.env.overwriteOutput = True  # overwrite GDB

LOG_FILE = "P:/housing_inventory.log"

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
egdb = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde"
path = "O:/GISUserProjects/Users/ErikRose/housing_inventory"

# source layer paths
addresses = os.path.join(egdb, "SDEPublic.GPGIS.Land/SDEPublic.GPGIS.ADDRESSES")
parcels = "https://gis.co.josephine.or.us/arcgis/rest/services/Assessor/Assessor_Taxlots/FeatureServer/0"
ugb = os.path.join(egdb, "SDEPublic.GPGIS.reg_UGB2014")
# open arcpro project
aprx = os.path.join(path, "housing_inventory.aprx")
aprx = arcpy.mp.ArcGISProject(aprx)

arcpy.management.Project(
    parcels,
    "parcels_ocrs",
    arcpy.SpatialReference("OCRS_Grants_Pass-Ashland_NAD_1983_2011_TM_Meters"),
)
arcpy.management.Project(
    addresses,
    "addresses_ocrs",
    arcpy.SpatialReference("OCRS_Grants_Pass-Ashland_NAD_1983_2011_TM_Meters"),
)
arcpy.management.Project(
    ugb,
    "ugb_ocrs",
    arcpy.SpatialReference("OCRS_Grants_Pass-Ashland_NAD_1983_2011_TM_Meters"),
)

# arcpy.management.CopyFeatures(addresses, "addresses")
# arcpy.management.CopyFeatures(parcels, "parcels")
# arcpy.management.CopyFeatures(ugb, "ugb")

# remove addresses of type "Parent" or status "Retired"
select_address = (
    "AddressType <> 'PARENT' Or AddressType IS NULL And STATUS <> 'Retired'"
)
logging.info("Selecting service addresses.")
arcpy.management.SelectLayerByAttribute(
    "addresses_ocrs", "NEW_SELECTION", select_address
)
arcpy.management.CopyFeatures("addresses_ocrs", "addresses_service")

# clip parcels to ugb
arcpy.analysis.PairwiseClip("parcels_ocrs", "ugb_ocrs", "parcels_ugb")


# add field for housing type
arcpy.management.AddField(
    "parcels_ugb",
    "housing_type",
    "SHORT",
    field_alias="Housing Type",
    field_domain="HousingType",
)

# if a field matches a clause, it will not fall through to the next clause, choosing the first match
# put building codes above property codes to preempt them
housing_expr = """
When(
    $feature.BLDG_CLASS >= 171 && $feature.BLDG_CLASS < 200, 0,
    $feature.BLDG_CLASS >= 222 && $feature.BLDG_CLASS < 300, 1,
    $feature.BLDG_CLASS >= 400 && $feature.BLDG_CLASS < 401, 2,
    $feature.BLDG_CLASS >= 411 && $feature.BLDG_CLASS < 414, 4,
    $feature.BLDG_CLASS >= 421 && $feature.BLDG_CLASS < 429, 2,
    $feature.BLDG_CLASS >= 429 && $feature.BLDG_CLASS < 430, 3,
    $feature.BLDG_CLASS >= 502 && $feature.BLDG_CLASS < 504, 3,
    $feature.BLDG_CLASS >= 900 && $feature.BLDG_CLASS < 1000, 3,
    $feature.PROP_CLASS >= 100 && $feature.PROP_CLASS < 102, 0,
    $feature.PROP_CLASS >= 121 && $feature.PROP_CLASS < 122, 0,
    $feature.PROP_CLASS >= 131 && $feature.PROP_CLASS < 132, 0,
    $feature.PROP_CLASS >= 191 && $feature.PROP_CLASS < 192, 0,
    $feature.PROP_CLASS >= 202 && $feature.PROP_CLASS < 203, 2,
    $feature.PROP_CLASS >= 207 && $feature.PROP_CLASS < 208, 3,
    $feature.PROP_CLASS >= 211 && $feature.PROP_CLASS < 212, 0,
    $feature.PROP_CLASS >= 401 && $feature.PROP_CLASS < 402, 0,
    $feature.PROP_CLASS >= 700 && $feature.PROP_CLASS < 702, 1,
    $feature.PROP_CLASS >= 711 && $feature.PROP_CLASS < 712, 1,
    $feature.PROP_CLASS >= 721 && $feature.PROP_CLASS < 722, 2,
    $feature.PROP_CLASS >= 731 && $feature.PROP_CLASS < 732, 1,
    $feature.PROP_CLASS >= 991 && $feature.PROP_CLASS < 992, 2,
    $feature.PROP_CLASS >= 1061 && $feature.PROP_CLASS < 1062, 0,
    $feature.PROP_CLASS >= 1961 && $feature.PROP_CLASS < 1962, 0,
    $feature.PROP_CLASS >= 4061 && $feature.PROP_CLASS < 4062, 0,
    $feature.BLDG_CLASS >= 111 && $feature.BLDG_CLASS < 162, 0,
        Null)
"""

arcpy.management.CalculateField("parcels_ugb", "housing_type", housing_expr, "ARCADE")

# subset residential property classes
# select_parcels = "(BLDG_CLASS >= '111' And BLDG_CLASS < '162') Or (BLDG_CLASS >= '171' And BLDG_CLASS < '200') Or (BLDG_CLASS >= '222' And BLDG_CLASS < '300') Or (BLDG_CLASS >= '400' And BLDG_CLASS < '431') Or (BLDG_CLASS >= '502' And BLDG_CLASS <= '503') Or PROP_CLASS IN ('100', '101', '102', '1061', '1961', '121', '131', '191', '202', '207', '211', '401', '4061', '700', '701', '711', '721', '731')"
# var = "PROP_CLASS IN ('100', '101', '102', '1061', '1961', '121', '131', '191', '202', '207', '211', '401', '4061', '700', '701', '711', '721', '731')"
select_parcels = "housing_type IS NOT NULL"
logging.info("Selecting residential property classes.")
arcpy.management.SelectLayerByAttribute("parcels_ugb", "NEW_SELECTION", select_parcels)
arcpy.management.CopyFeatures("parcels_ugb", "parcels_residential")

# two proxies for owner occupied
#
# * Does the situs address match the mailing address?
# * Does any unit address within the parcel match the mailing address of the owner?
#
# Situs vs. Mailing

owner_expr = """
When($feature.housing_type == 3, 2,
     $feature.housing_type == 4, 2,
    $feature.ADDRESS == $feature.SITUS, 1,
     0)
"""

arcpy.management.AddField(
    "parcels_residential",
    "owner_occupied",
    "SHORT",
    field_alias="Owner Occupied",
    field_domain="OwnerOccupied",
)

arcpy.management.CalculateField(
    "parcels_residential",
    "owner_occupied",
    owner_expr,
    "ARCADE",
)

# subset addresses within residential parcels
# arcpy.analysis.PairwiseClip("addresses_service", "parcels_residential", "addresses_residential")
# remove addresses of type "Parent" or status "Retired"
# select_address = (
#     "AddressType <> 'PARENT' Or AddressType IS NULL And STATUS <> 'Retired'"
# )
# logging.info("Selecting service addresses.")
# arcpy.management.SelectLayerByAttribute(
#     "addresses_residential", "NEW_SELECTION", select_address
# )
# arcpy.management.CopyFeatures("addresses_residential", "addresses_service")

fms = arcpy.FieldMappings()
field_map(fms, "parcels_residential", "ACCOUNT", "account", "Account", "First")
field_map(fms, "parcels_residential", "MapNum", "map_number", "Map Number", "First")
field_map(fms, "parcels_residential", "SITUS", "address", "Situs Address", "First")
field_map(
    fms, "parcels_residential", "housing_type", "housing_type", "Housing Type", "First"
)
field_map(
    fms,
    "parcels_residential",
    "owner_occupied",
    "owner_occupied",
    "Owner Occupied",
    "First",
)

logging.info("Counting service addresses in parcels.")
arcpy.analysis.SpatialJoin(
    "parcels_residential",
    "addresses_service",
    "housing_inventory",
    "JOIN_ONE_TO_ONE",
    "KEEP_ALL",
    fms,
    match_option="INTERSECT",
)

# assign Owner Occupied domain to field
arcpy.management.AssignDomainToField(
    "housing_inventory", "owner_occupied", "OwnerOccupied"
)

# assing Housing Type domain to field
arcpy.management.AssignDomainToField("housing_inventory", "housing_type", "HousingType")

# Create field for household counts
arcpy.management.AddField(
    "housing_inventory", "housing_units", "SHORT", field_alias="Housing Units"
)

# Copy join_count field to housing unit count
arcpy.management.CalculateField(
    "housing_inventory", "housing_units", "$feature.join_count", "ARCADE"
)

# Remove unused fields
arcpy.management.DeleteField(
    "housing_inventory", ["Join_Count", "TARGET_FID"], "DELETE_FIELDS"
)

# set metadata

disclaimer = """
DISCLAIMER

Basic data for pre-planning purposes, not to be relied upon for professional services. The geographic information systems (GIS) data made available are developed and maintained by the City of Grants Pass and Josephine County. The City of Grants Pass makes no warranties, claims, or representations (express or implied) as to the use of the maps and data made available by City personnel or at City websites. There are no implied warranties of merchantability or fitness for a particular purpose. The user acknowledges and accepts all inherent limitations of the maps and data, including the fact that the maps and data are dynamic and in a constant state of maintenance, correction and revision. Any maps and associated data for access do not represent a survey. No liability is assumed for the accuracy of the data delineated on any map, or data disseminated in any other form, either expressed or implied. Data includes but is not limited to the following: hard copy maps, web maps/applications, auto-CAD (.DWG/.DXF), shapefiles, geodatabases, and/or all image file formats. Please consult appropriate professionals when planning any variety of jobs (RPLs, licensed engineers, 811, title company, etc.)
"""
contact_info = "City of Grants Pass"

housing_inventory_path = os.path.join(path, "housing_inventory.gdb/housing_inventory")
lyr_md = md.Metadata()
lyr_md.title = "Housing Inventory"
lyr_md.tags = "community development, planning, grants pass, oregon"
lyr_md.summary = "Estimated Housing Stock for the City of Grants Pass, Oregon."
lyr_md.description = """
The type of housing is estimated from the property and building class codes in the County taxlot layer.  The number of housing units is estimated from the number of active service addresses in the City records. 
These estimates are intended for planning purposes, and do not guarantee a specific use at any given parcel.
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(housing_inventory_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()
