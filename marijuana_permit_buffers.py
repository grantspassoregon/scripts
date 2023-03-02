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
arcpy.env.overwriteOutput = True

# Customize these variables to paths on your system
PROJECT_DIR = "C:/Users/erose/projects"
GDB_NAME = "marijuana_permit_buffers.gdb"
WORKSPACE = "C:/Users/erose/projects/marijuana_permit_buffers.gdb"
ARCGIS_PROJECT = (
    "C:/Users/erose/projects/marijuana_permit_buffers/marijuana_permit_buffers.aprx"
)
LOG_FILE = "P:/marijuana_permit_buffers.log"

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
# og_marijuana_businesses = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.MarijuanaBusinesses/SDEPublic.GPGIS.MarijuanaBusinesses"
og_marijuana_businesses = "O:/GISUserProjects/Users/ErikRose/marijuana_adult_use/marijuana_adult_use.gdb/marijuana_businesses"
# og_daycare_facilities = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.MarijuanaBusinesses/SDEPublic.GPGIS.DaycareFacilities"
og_licensed_daycares = "O:/GISUserProjects/Users/ErikRose/marijuana_adult_use/marijuana_adult_use.gdb/licensed_daycares_confirmed"
og_industrial_zone_schools = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.MarijuanaBusinesses/SDEPublic.GPGIS.IndustrialZoneSchools"
# og_recreational_facilities = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.AdultUse/SDEPublic.GPGIS.CommRecFacilities"
og_recreational_facilities = "O:/GISUserProjects/Users/ErikRose/marijuana_adult_use/marijuana_adult_use.gdb/recreational_facilities"
og_library = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.AdultUse/SDEPublic.GPGIS.Library"
og_parks = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.AdultUse/SDEPublic.GPGIS.Parks"
og_developed_parks = "O:/GISUserProjects/Users/ErikRose/marijuana_adult_use/marijuana_adult_use.gdb/developed_parks"
og_residential_zones = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.AdultUse/SDEPublic.GPGIS.ResidentialZones"
# og_schools = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.AdultUse/SDEPublic.GPGIS.Schools"
og_schools = "O:/GISUserProjects/Users/ErikRose/marijuana_adult_use/marijuana_adult_use.gdb/schools"
og_ugb = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.reg_UGB2014"
og_zoning = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.plan_ZONINGDISTRICT"

arcpy.CopyFeatures_management(og_residential_zones, "residential_zones")
arcpy.CopyFeatures_management(og_recreational_facilities, "recreational_facilities")
arcpy.CopyFeatures_management(og_developed_parks, "developed_parks")
arcpy.CopyFeatures_management(og_schools, "schools")
arcpy.CopyFeatures_management(og_industrial_zone_schools, "industrial_zone_schools")
# arcpy.CopyFeatures_management(og_daycare_facilities, "daycare_facilities")
arcpy.CopyFeatures_management(og_licensed_daycares, "licensed_daycares")
arcpy.CopyFeatures_management(og_library, "library")
arcpy.CopyFeatures_management(og_marijuana_businesses, "marijuana_businesses")
arcpy.CopyFeatures_management(og_ugb, "ugb")
arcpy.CopyFeatures_management(og_zoning, "zoning")

# open arcpro project
aprx = arcpy.mp.ArcGISProject(ARCGIS_PROJECT)


# helper functions
def field_map(fms, lyr, from_name, to_name, rule="First"):
    fm = arcpy.FieldMap()
    fm.addInputField(lyr, from_name)
    fm.mergeRule = rule
    fm_name = fm.outputField
    fm_name.name = to_name
    fm_name.aliasName = to_name
    fm.outputField = fm_name
    fms.addFieldMap(fm)


# field map for spatial join of schools to zoning
logging.info("Building field map for spatial join of schools to zoning.")
fms = arcpy.FieldMappings()
field_map(fms, "schools", "SCHOOL_NAM", "Name")
field_map(fms, "schools", "SCHOOL_DIS", "District")
field_map(fms, "schools", "ADDRESS", "Address")
field_map(fms, "schools", "GRADE", "Grade")
field_map(fms, "zoning", "ZONECLASS", "ZoneClass")
field_map(fms, "zoning", "ZONEDESC", "ZoneDescription")

# spatial join of schools to zoning
logging.info("Joining zoning fields to schools layer.")
arcpy.analysis.SpatialJoin(
    "schools",
    "zoning",
    "schools_zoned",
    "#",
    "#",
    fms,
    "HAVE_THEIR_CENTER_IN",
)

# school in industrial zoning
logging.info("Subsetting schools in industrial zoning.")
arcpy.management.SelectLayerByAttribute(
    "schools_zoned", "NEW_SELECTION", "ZoneClass IN ('I', 'IP', 'BP')"
)
arcpy.management.CopyFeatures("schools_zoned", "schools_industrial")

# schools not in industrial zoning
logging.info("Subsetting schools not in industrial zoning.")
arcpy.management.SelectLayerByAttribute(
    "schools_zoned", "NEW_SELECTION", "ZoneClass NOT IN ('I', 'IP', 'BP')"
)
arcpy.management.CopyFeatures("schools_zoned", "schools_nonindustrial")

# exclusion buffers
logging.info("Building permit exclusion area from buffers.")
# residential zone buffer (200 ft)
logging.info("Buffering 200 ft from residential zones.")
arcpy.analysis.Buffer(
    "residential_zones",
    "residential_zones_buffer_full",
    "200 Feet",
    "FULL",
    "ROUND",
    "ALL",
)
arcpy.analysis.Clip("residential_zones_buffer_full", "ugb", "residential_zones_buffer")
# commercial and recreational facilities (1000 ft)
logging.info(
    "Buffering 1000 ft from commercial and residential recreational facilities."
)
arcpy.analysis.Buffer(
    "recreational_facilities",
    "recreational_facilities_buffer_full",
    "1000 Feet",
    "FULL",
    "ROUND",
    "ALL",
)
arcpy.analysis.Clip(
    "recreational_facilities_buffer_full", "ugb", "recreational_facilities_buffer"
)
# developed parks buffer (1000 ft)
logging.info("Buffering 1000 ft from developed parks.")
arcpy.analysis.Buffer(
    "developed_parks",
    "developed_parks_buffer_full",
    "1000 Feet",
    "FULL",
    "ROUND",
    "ALL",
)
arcpy.analysis.Clip("developed_parks_buffer_full", "ugb", "developed_parks_buffer")

# schools buffer (1000 ft)
logging.info("Buffering 1000 ft from schools not in industrial zoning.")
arcpy.analysis.Buffer(
    "schools_nonindustrial",
    "schools_nonindustrial_buffer_full",
    "1000 Feet",
    "FULL",
    "ROUND",
    "ALL",
)
arcpy.analysis.Clip(
    "schools_nonindustrial_buffer_full", "ugb", "schools_nonindustrial_buffer"
)
# industrial schools (1000 ft, 500 ft for producers and processors)
logging.info("Buffering 1000 ft from schools in industrial zoning.")
arcpy.analysis.Buffer(
    "schools_industrial",
    "schools_industrial_buffer_1000_full",
    "1000 Feet",
    "FULL",
    "ROUND",
    "ALL",
)
arcpy.analysis.Clip(
    "schools_industrial_buffer_1000_full", "ugb", "schools_industrial_buffer_1000"
)
logging.info("Buffering 500 ft from schools in industrial zoning.")
arcpy.analysis.Buffer(
    "schools_industrial",
    "schools_industrial_buffer_500_full",
    "500 Feet",
    "FULL",
    "ROUND",
    "ALL",
)
arcpy.analysis.Clip(
    "schools_industrial_buffer_500_full", "ugb", "schools_industrial_buffer_500"
)
# licensed daycares buffer (1000 ft)
logging.info("Buffering 1000 ft from licensed daycare centers.")
arcpy.analysis.Buffer(
    "licensed_daycares",
    "licensed_daycares_buffer_full",
    "1000 Feet",
    "FULL",
    "ROUND",
    "ALL",
)
arcpy.analysis.Clip("licensed_daycares_buffer_full", "ugb", "licensed_daycares_buffer")
# library buffer (1000 ft)
logging.info("Buffering 1000 ft from libraries.")
arcpy.analysis.Buffer(
    "library", "library_buffer_full", "1000 Feet", "FULL", "ROUND", "ALL"
)
arcpy.analysis.Clip("library_buffer_full", "ugb", "library_buffer")
# marijuana retailer buffer (1000 ft)
logging.info("Subsetting marijuana retailers from marijuana businesses.")
arcpy.management.SelectLayerByAttribute(
    "marijuana_businesses", "NEW_SELECTION", "BusinessType IN ('Retailer')"
)
arcpy.management.CopyFeatures("marijuana_businesses", "marijuana_retailers")
arcpy.management.SelectLayerByAttribute("marijuana_businesses", "CLEAR_SELECTION")
logging.info("Buffering 1000 ft from marijuana retailers.")
arcpy.analysis.Buffer(
    "marijuana_retailers",
    "marijuana_retailers_buffer_full",
    "1000 Feet",
    "FULL",
    "ROUND",
    "ALL",
)
arcpy.analysis.Clip(
    "marijuana_retailers_buffer_full", "ugb", "marijuana_retailers_buffer"
)


# exclusion area union
logging.info("Building exclusion area from union of component buffers.")
# marijuana retailers
logging.info("Building exclusion area for marijuana retailers.")
arcpy.analysis.Union(
    [
        "residential_zones_buffer",
        "recreational_facilities_buffer",
        "developed_parks_buffer",
        "schools_nonindustrial_buffer",
        "schools_industrial_buffer_1000",
        "licensed_daycares_buffer",
        "library_buffer",
        "marijuana_retailers_buffer",
    ],
    "exclusion_area_retailers_union",
    "NO_FID",
)

arcpy.management.Dissolve("exclusion_area_retailers_union", "exclusion_area_retailers")

# marijuana producers and processors
logging.info("Building exclusion area for marijuana producers and processors.")
arcpy.analysis.Union(
    [
        "residential_zones_buffer",
        "recreational_facilities_buffer",
        "developed_parks_buffer",
        "schools_nonindustrial_buffer",
        "schools_industrial_buffer_500",
        "licensed_daycares_buffer",
        "library_buffer",
        "marijuana_businesses",
    ],
    "exclusion_area_producers_union",
    "NO_FID",
)

arcpy.management.Dissolve("exclusion_area_producers_union", "exclusion_area_producers")

# marijuana processing sites, wholesalers and medical dispensaries
logging.info(
    "Building exclusion area for marijuana wholesalers, processing sites and medical dispensaries."
)
arcpy.analysis.Union(
    [
        "residential_zones_buffer",
        "recreational_facilities_buffer",
        "developed_parks_buffer",
        "schools_nonindustrial_buffer",
        "schools_industrial_buffer_1000",
        "licensed_daycares_buffer",
        "library_buffer",
        "marijuana_businesses",
    ],
    "exclusion_area_wholesalers_union",
    "NO_FID",
)

arcpy.management.Dissolve(
    "exclusion_area_wholesalers_union", "exclusion_area_wholesalers"
)

logging.info("Permissible areas for marijuana permitting by business type.")
arcpy.analysis.SymDiff("ugb", "exclusion_area_retailers", "permissible_area_retailers")
arcpy.analysis.SymDiff("ugb", "exclusion_area_producers", "permissible_area_producers")
arcpy.analysis.SymDiff(
    "ugb", "exclusion_area_wholesalers", "permissible_area_wholesalers"
)
