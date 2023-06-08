import arcpy
from arcpy import metadata as md
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
PROJECT_DIR = "C:/Users/erose/projects/marijuana_permit_buffers"
GDB_NAME = "marijuana_permit_buffers.gdb"
# WORKSPACE = os.path.join(PROJECT_DIR, GDB_NAME)
WORKSPACE = (
    "C:/Users/erose/projects/marijuana_permit_buffers/marijuana_permit_buffers.gdb"
)
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
arcpy.env.workspace = WORKSPACE

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


# copy layers from city database to local gdb
# defensive copies for editing and publishing
logging.info("Importing layers from SDE database.")
# og_marijuana_businesses = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.MarijuanaBusinesses/SDEPublic.GPGIS.MarijuanaBusinesses"
og_marijuana_businesses = "O:/GISUserProjects/Users/ErikRose/marijuana_adult_use/marijuana_adult_use.gdb/marijuana_businesses"
# og_daycare_facilities = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.MarijuanaBusinesses/SDEPublic.GPGIS.DaycareFacilities"
# og_licensed_daycares = "O:/GISUserProjects/Users/ErikRose/marijuana_adult_use/marijuana_adult_use.gdb/licensed_daycares_confirmed"
# og_industrial_zone_schools = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.MarijuanaBusinesses/SDEPublic.GPGIS.IndustrialZoneSchools"
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
og_taxlots = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.JoCo_FS_Export_1"
og_city_limits = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.reg_CITYLIMITS2023"

arcpy.CopyFeatures_management(og_residential_zones, "residential_zones")
arcpy.CopyFeatures_management(og_recreational_facilities, "recreational_facilities")
arcpy.CopyFeatures_management(og_developed_parks, "developed_parks")
arcpy.CopyFeatures_management(og_schools, "schools")
# arcpy.CopyFeatures_management(og_industrial_zone_schools, "industrial_zone_schools")
# arcpy.CopyFeatures_management(og_daycare_facilities, "daycare_facilities")
# arcpy.CopyFeatures_management(og_licensed_daycares, "licensed_daycares")
arcpy.CopyFeatures_management(og_library, "library")
arcpy.CopyFeatures_management(og_marijuana_businesses, "marijuana_businesses")
arcpy.CopyFeatures_management(og_ugb, "ugb")
arcpy.CopyFeatures_management(og_zoning, "zoning")
arcpy.CopyFeatures_management(og_taxlots, "taxlots")
arcpy.CopyFeatures_management(og_city_limits, "city_limits")

# read csv of daycares from OCC
intable = "c:/users/erose/projects/marijuana_permit_buffers/licensed_daycares.csv"
# arcpy.management.MakeTableView(intable, "licensed_daycares_tbl")
arcpy.conversion.ExportTable(
    intable,
    "c:/users/erose/projects/marijuana_permit_buffers/marijuana_permit_buffers.gdb/daycares_tbl",
)
# match OCC address to parcel situs address
codeblock = """
def parse_address(address):
    addr = address.upper()
    if addr == "3345 1/2 REDWOOD HWY":
        addr = "3345 REDWOOD HWY"
    if addr == "1701 SW NEBRASKA AVE":
        addr = "1701 NEBRASKA AVE"
    if addr == "1867 WILLIAMS HWY STE 106A":
        addr = "1867 WILLIAMS HWY"
    if addr == "222 GRANGE RD":
        addr = "220 WILLIAMSON LOOP"
    if addr == "408 SE G ST STE B & C":
        addr = "410 SE G ST"
    if addr == "1252 E VIEW PL": 
        addr = "1252 EAST VIEW PL"
    if addr == "1281 E VIEW PL": 
        addr = "1281 EAST VIEW PL"
    if addr == "1324 NE BEA VILLA VW":
        addr = "1324 NE BEAVILLA VIEW"
    if addr == "241 MARION LN":
        addr = "241 SW MARION LN"
    return(addr)
"""
logging.info("Converting daycare addresses to tax parcel situs addresses.")
arcpy.management.CalculateField(
    "daycares_tbl", "address", "parse_address(!Facility_Address!)", "PYTHON3", codeblock
)
# join tbl to taxlot parcels by address
logging.info("Joining daycares with tax parcels by situs addresses.")
arcpy.management.AddJoin("daycares_tbl", "address", "taxlots", "SITUS")

fc = "daycares_tbl"
fields = [
    "daycares_tbl.License_No",
    "daycares_tbl.Facility_Type",
    "daycares_tbl.Facility_Name",
    "daycares_tbl.Facility_Address",
    "taxlots.MAPNUM",
]

# southern oregon head start redwood center located on 360627D000010100
# remove other map numbers associated with Rogue community college
rogue_lots = ["360627A0001000", "360627AD001400", "360627AD001600", "360627A0001001"]
# list map numbers associated with situs address for each facility
daycare_taxlots = []
with arcpy.da.SearchCursor("daycares_tbl", "taxlots.MAPNUM") as cursor:
    for row in cursor:
        if row[0] is not None and row[0] not in rogue_lots:
            daycare_taxlots.append(row[0])

select_daycares = "MAPNUM IN " + str(daycare_taxlots)
select_daycares = select_daycares.replace("[", "(")
select_daycares = select_daycares.replace("]", ")")
logging.info("Selecting taxlots matching daycare situs addresses.")
arcpy.management.SelectLayerByAttribute("taxlots", "NEW_SELECTION", select_daycares)
arcpy.management.CopyFeatures("taxlots", "daycare_taxlots")
logging.info("Joining daycare attributes to taxlot parcels.")
arcpy.management.AddJoin(
    "daycare_taxlots", "SITUS", "daycares_tbl", "daycares_tbl.address"
)

logging.info("Building field map for licensed daycares layer.")
fms = arcpy.FieldMappings()
field_map(fms, "daycare_taxlots", "daycares_tbl.License_No", "License")
field_map(fms, "daycare_taxlots", "daycares_tbl.Facility_Name", "Name")
field_map(fms, "daycare_taxlots", "daycares_tbl.Facility_Type", "Type")
field_map(fms, "daycare_taxlots", "daycares_tbl.Facility_Address", "Address")

logging.info("Exporting parcels with daycare attributes as licensed daycares layer.")
arcpy.conversion.ExportFeatures(
    "daycare_taxlots", "licensed_daycares", field_mapping=fms
)


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
arcpy.analysis.SymDiff(
    "ugb", "exclusion_area_retailers", "permissible_area_retailers_ugb"
)
arcpy.analysis.Clip(
    "permissible_area_retailers_ugb", "city_limits", "permissible_area_retailers"
)
arcpy.analysis.SymDiff(
    "ugb", "exclusion_area_producers", "permissible_area_producers_ugb"
)
arcpy.analysis.Clip(
    "permissible_area_producers_ugb", "city_limits", "permissible_area_producers"
)
arcpy.analysis.SymDiff(
    "ugb", "exclusion_area_wholesalers", "permissible_area_wholesalers_ugb"
)
arcpy.analysis.Clip(
    "permissible_area_wholesalers_ugb", "city_limits", "permissible_area_wholesalers"
)

# set metadata

disclaimer = """
DISCLAIMER

Basic data for pre-planning purposes, not to be relied upon for professional services. The geographic information systems (GIS) data made available are developed and maintained by the City of Grants Pass and Josephine County. The City of Grants Pass makes no warranties, claims, or representations (express or implied) as to the use of the maps and data made available by City personnel or at City websites. There are no implied warranties of merchantability or fitness for a particular purpose. The user acknowledges and accepts all inherent limitations of the maps and data, including the fact that the maps and data are dynamic and in a constant state of maintenance, correction and revision. Any maps and associated data for access do not represent a survey. No liability is assumed for the accuracy of the data delineated on any map, or data disseminated in any other form, either expressed or implied. Data includes but is not limited to the following: hard copy maps, web maps/applications, auto-CAD (.DWG/.DXF), shapefiles, geodatabases, and/or all image file formats. Please consult appropriate professionals when planning any variety of jobs (RPLs, licensed engineers, 811, title company, etc.)
"""
contact_info = "City of Grants Pass"

permissible_retailers_path = WORKSPACE + "/permissible_area_retailers"
lyr_md = md.Metadata()
lyr_md.title = "Potentially Permissible Area Marijuana Retail Business"
lyr_md.tags = "marijuana business permitting, planning"
lyr_md.summary = "Area showing where permits for new marijuana retail businesses are not prohibited by the language on buffers (11.01.500) or colocation (11.01.600) in the Grants Pass Municipal Code."
lyr_md.description = """
    <p>According to the <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.500 (Buffers) and 11.01.600 (Colocation), the City may not issue new marijuana retail business permits in the following areas:</p>
<ul>
    <li>Within 200 feet of a residential zone.</li>
    <li>Within 1000 feet of a residential or commercial recreational facility.</li>
    <li>Within 1000 feet of a public library.</li>
    <li>Within 1000 feet of a public park that exceeds 20,000 square feet in size and has developed facilities such as a playground or sports field.</li>
    <li>Within 1000 feet of a public school that exceeds an average weekly attendance of 50 children.</li>
    <li>Within 1000 feet of a daycare facility licensed by the State of Oregon.</li>
    <li>On the same property, parcel, address or tax lot as another marijuana business.</li>
    <li>Within 1000 feet of another licensed marijuana retail business.</li>
</ul>
<p>The potentially permissible areas polygon shows portions within the City Limits where new marijuana retail business permits are not prohibited by any of the restrictions listed above.</p>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(permissible_retailers_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()


permissible_wholesalers_path = WORKSPACE + "/permissible_area_wholesalers"
lyr_md = md.Metadata()
lyr_md.title = "Potentially Permissible Area Marijuana Wholesalers Processing Sites and Medical Dispensaries"
lyr_md.tags = "marijuana business permitting, planning"
lyr_md.summary = "Area showing where permits for new marijuana wholesalers, processing sites and medical dispensary businesses are not prohibited by the language on buffers (11.01.500) or colocation (11.01.600) in the Grants Pass Municipal Code."
lyr_md.description = """
    <p>According to the <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.500 (Buffers) and 11.01.600 (Colocation), the City may not issue new marijuana wholesaler, processing site or medical dispensary business permits in the following areas:</p>
<ul>
    <li>Within 200 feet of a residential zone.</li>
    <li>Within 1000 feet of a residential or commercial recreational facility.</li>
    <li>Within 1000 feet of a public library.</li>
    <li>Within 1000 feet of a public park that exceeds 20,000 square feet in size and has developed facilities such as a playground or sports field.</li>
    <li>Within 1000 feet of a public school that exceeds an average weekly attendance of 50 children.</li>
    <li>Within 1000 feet of a daycare facility licensed by the State of Oregon.</li>
    <li>On the same property, parcel, address or tax lot as another marijuana business.</li>
</ul>
<p>The potentially permissible areas polygon shows portions within the City Limits where new marijuana wholesaler, processing site or medical dispensary business permits are not prohibited by any of the restrictions listed above.</p>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(permissible_wholesalers_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

permissible_producers_path = WORKSPACE + "/permissible_area_producers"
lyr_md = md.Metadata()
lyr_md.title = "Potentially Permissible Area Marijuana Producers & Processors"
lyr_md.tags = "marijuana business permitting, planning"
lyr_md.summary = "Area showing where permits for new marijuana producers and processors are not prohibited by the language on buffers (11.01.500) or colocation (11.01.600) in the Grants Pass Municipal Code."
lyr_md.description = """
    <p>According to the <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.500 (Buffers) and 11.01.600 (Colocation), the City may not issue new marijuana producer or processor business permits in the following areas:</p>
<ul>
    <li>Within 200 feet of a residential zone.</li>
    <li>Within 1000 feet of a residential or commercial recreational facility.</li>
    <li>Within 1000 feet of a public library.</li>
    <li>Within 1000 feet of a public park that exceeds 20,000 square feet in size and has developed facilities such as a playground or sports field.</li>
    <li>Within 1000 feet of a public school that exceeds an average weekly attendance of 50 children that is not in an Industrial Zone.</li>
    <li>Within 500 feet of a public school that exceeds an average weekly attendance of 50 children that is in an Industrial Zone.</li>
    <li>Within 1000 feet of a daycare facility licensed by the State of Oregon.</li>
    <li>On the same property, parcel, address or tax lot as another marijuana business.</li>
</ul>
<p>The potentially permissible areas polygon shows portions within the City Limits where new marijuana producer or processor business permits are not prohibited by any of the restrictions listed above.</p>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(permissible_producers_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

marijuana_businesses_path = WORKSPACE + "/marijuana_businesses"
lyr_md = md.Metadata()
lyr_md.title = "Marijuana Businesses"
lyr_md.tags = "marijuana business permitting, planning"
lyr_md.summary = "Property boundaries of marijuana business sites in the City of Grants Pass, Oregon, for use in marijuana business permitting."
lyr_md.description = """
<p>Application for Marijuana Business Permitting:</p>

<p>From the <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.600:</p>
<ul>
    <li><b>No more than one Marijuana Business may be located on the same property, parcel, address or tax lot.</b></li>
</ul>

<p>This layer is also the source for the marijuana retailers 1000' buffer.</p>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(marijuana_businesses_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

marijuana_retailers_path = WORKSPACE + "/marijuana_retailers"
lyr_md = md.Metadata()
lyr_md.title = "Marijuana Retailers"
lyr_md.tags = "marijuana business permitting, planning"
lyr_md.summary = "Property boundaries of marijuana retail business sites in the City of Grants Pass, Oregon, for use in marijuana business permitting."
lyr_md.description = """
<p>Application for Marijuana Business Permitting:</p>

<p>From the <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.600:</p>
<ul>
    <li><b>No more than one Marijuana Business may be located on the same property, parcel, address or tax lot.</b></li>
</ul>

<p>This layer is also the source for the marijuana retailers 1000' buffer.</p>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(marijuana_retailers_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

marijuana_retailers_buffer_path = WORKSPACE + "/marijuana_retailers_buffer"
lyr_md = md.Metadata()
lyr_md.title = "Marijuana Retailers Buffer 1000'"
lyr_md.tags = "marijuana business permitting, planning"
lyr_md.summary = "A 1000' buffer around marijuana retailers in the City of Grants Pass, Oregon, for use in marijuana business permitting."
lyr_md.description = """
<p>Application for Marijuana Business Permitting:</p>

<p>From the <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.500:</p>
<ul>
    <li><b>Marijuana retailers may not be located within 1000 feet of other Marijuana relailers.</b></li>
</ul>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(marijuana_retailers_buffer_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

licensed_daycares_path = WORKSPACE + "/licensed_daycares"
lyr_md = md.Metadata()
lyr_md.title = "Licensed Daycare Facilities"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = (
    "Property boundaries for daycare facilities licensed by the State of Oregon."
)
lyr_md.description = "Source layer for generating the 1000' daycare buffers for marijuana business and adult use permitting."
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(licensed_daycares_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/licensed_daycares_buffer"
lyr_md = md.Metadata()
lyr_md.title = "Licensed Daycare Facilities Buffer 1000'"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = """
<p>Application for Marijuana Business Permitting:</p>

<p>The licensed daycares buffer is based upon <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.500:</p>
<blockquote> Marijuana Businesses may not be located within 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the Adult Business is located to the closest edge of the property line on which the facility is located): </blockquote>
<ul>
    <li> 1) A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3 month period during the preceding 12 months) of not less than 50 children who are under 18 years of age;
    <ul>
        <li> a) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone. </li>
    </ul> </li>
    <li> 2) A public library; or</li>
    <li> 3) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court; or</li>
    <li> 4) A commercial or residential recreational facility, as defined in Article 30, which serves children under 18 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet; or</li>
    <li> 5) <b>A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business.</b></li>
</ul>

<p>Application for Adult Use Permitting:</p>

<p>The licensed daycares buffer is based upon paragraph 2(c)(ii) of <a href='https://www.grantspassoregon.gov/221/Development-Code'>Grants Pass Development Code</a> 14.630:</p>
<blockquote>Additional Criteria for Permit Approval.  A development permit for an adult business shall also comply with all of the following criteria: </blockquote>
<ul>
    <li> 1) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business is located more than 200 feet from any R-1, R-2, R-3, or R-4 residential zones (measured in a straight line from the closest edge of the property line on which the business is located to the closest edge of property in the residential zone); and </li>
        </ul> </li>
    <li> 2) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business has 10,000 or more square feet of covered and enclosed building space open to the public, and contains restaurant accommodations that are not restricted at any time by age and which restaurant accommodations have a floor area equal to or greater in size than the portion of the premises where any persons younger than 21 years of age are prohibited; or</li>
        <li> c) The adult business has less than 10,000 square feet of covered and enclosed building space open to the public, and the adult business is located more than 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the adult business is located to the closest edge of the property line on which the facility is located):
        <ul>
            <li> i) A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3-month period during the preceding 12 months) of not less than 50 children who are under 21 years of age.
            <ul>
                <li> A) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</li>
            </ul> </li>
            <li> ii) A public library.</li>
            <li> iii) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court.</li>
            <li> iv) A commercial or residential recreational facility, as defined in Article 30, which serves children under 21 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet.</li>
            <li> v) <b>A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business. </b></li>
        </ul> </li>
    </ul> </li>
</ul>

<p>The extent of the buffer is limited to within the Urban Growth Boundary of the City of Grants Pass, Oregon. </p>
"""
lyr_md.description = "Source layer for generating the 1000' daycare buffers for marijuana business and adult use permitting."
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/schools_nonindustrial"
lyr_md = md.Metadata()
lyr_md.title = "Schools - Nonindustrial Zoning"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = "Property boundaries of public schools exceeding an average daily attendance of 50 students that are not in an industrial zone."
lyr_md.description = "The source layer for the 1000' buffer around nonindustrial public schools exceeding an average daily attendance of 50 students, for use in marijuana business and adult use permitting."
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/schools_nonindustrial_buffer"
lyr_md = md.Metadata()
lyr_md.title = "Schools Buffer 1000' - Nonindustrial Zoning"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = "A 1000' buffer around schools not in Industrial Zoning within the City of Grants Pass, for use in marijuana business and adult use permitting."
lyr_md.description = """
<p>Application for Marijuana Business Permitting:</p>

<p>The buffer for schools not in an industrial zone is based upon <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.500:</p>
<blockquote> Marijuana Businesses may not be located within 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the Adult Business is located to the closest edge of the property line on which the facility is located): </blockquote>
<ul>
    <li> 1) <b>A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3 month period during the preceding 12 months) of not less than 50 children who are under 18 years of age;</b>
    <ul>
        <li> a) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone. </li>
    </ul> </li>
    <li> 2) A public library; or</li>
    <li> 3) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court; or</li>
    <li> 4) A commercial or residential recreational facility, as defined in Article 30, which serves children under 18 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet; or</li>
    <li> 5) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business.</li>
</ul>

<p>Application for Adult Use Permitting:</p>

<p>The buffer for schools not in an industrial zone is based upon paragraph 2(c)(ii) of <a href='https://www.grantspassoregon.gov/221/Development-Code'>Grants Pass Development Code</a> 14.630:</p>
<blockquote>Additional Criteria for Permit Approval.  A development permit for an adult business shall also comply with all of the following criteria: </blockquote>
<ul>
    <li> 1) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business is located more than 200 feet from any R-1, R-2, R-3, or R-4 residential zones (measured in a straight line from the closest edge of the property line on which the business is located to the closest edge of property in the residential zone); and </li>
        </ul> </li>
    <li> 2) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business has 10,000 or more square feet of covered and enclosed building space open to the public, and contains restaurant accommodations that are not restricted at any time by age and which restaurant accommodations have a floor area equal to or greater in size than the portion of the premises where any persons younger than 21 years of age are prohibited; or</li>
        <li> c) The adult business has less than 10,000 square feet of covered and enclosed building space open to the public, and the adult business is located more than 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the adult business is located to the closest edge of the property line on which the facility is located):
        <ul>
            <li> i) <b>A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3-month period during the preceding 12 months) of not less than 50 children who are under 21 years of age.</b>
            <ul>
                <li> A) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</li>
            </ul> </li>
            <li> ii) A public library.</li>
            <li> iii) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court.</li>
            <li> iv) A commercial or residential recreational facility, as defined in Article 30, which serves children under 21 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet.</li>
            <li> v) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business. </li>
        </ul> </li>
    </ul> </li>
</ul>

<p>The extent of the buffer is limited to within the Urban Growth Boundary of the City of Grants Pass, Oregon. </p>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/schools_industrial"
lyr_md = md.Metadata()
lyr_md.title = "Schools - Industrial Zoning"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = "Property boundaries of public schools exceeding an average daily attendance of 50 students that are in an industrial zone."
lyr_md.description = "The source layer for the 500' and 1000' buffer around public schools in an industrial zone exceeding an average daily attendance of 50 students, for use in marijuana business and adult use permitting."
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/schools_industrial_buffer_1000"
lyr_md = md.Metadata()
lyr_md.title = "Schools Buffer 1000' - Industrial Zoning"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = "A 1000' buffer around schools not in Industrial Zoning within the City of Grants Pass, for use in marijuana business and adult use permitting."
lyr_md.description = """
<p>Application for Marijuana Business Permitting:</p>

<p>The 1000 foot buffer for schools in an industrial zone is based upon <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.500:</p>
<blockquote> Marijuana Businesses may not be located within 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the Adult Business is located to the closest edge of the property line on which the facility is located): </blockquote>
<ul>
    <li> 1) <b>A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3 month period during the preceding 12 months) of not less than 50 children who are under 18 years of age;</b>
    <ul>
        <li> a) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</li>
    </ul> </li>
    <li> 2) A public library; or</li>
    <li> 3) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court; or</li>
    <li> 4) A commercial or residential recreational facility, as defined in Article 30, which serves children under 18 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet; or</li>
    <li> 5) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business.</li>
</ul>

<p>Application for Adult Use Permitting:</p>

<p>The 1000 foot buffer for schools in an industrial zone is based upon paragraph 2(c)(ii) of <a href='https://www.grantspassoregon.gov/221/Development-Code'>Grants Pass Development Code</a> 14.630:</p>
<blockquote>Additional Criteria for Permit Approval.  A development permit for an adult business shall also comply with all of the following criteria: </blockquote>
<ul>
    <li> 1) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business is located more than 200 feet from any R-1, R-2, R-3, or R-4 residential zones (measured in a straight line from the closest edge of the property line on which the business is located to the closest edge of property in the residential zone); and </li>
        </ul> </li>
    <li> 2) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business has 10,000 or more square feet of covered and enclosed building space open to the public, and contains restaurant accommodations that are not restricted at any time by age and which restaurant accommodations have a floor area equal to or greater in size than the portion of the premises where any persons younger than 21 years of age are prohibited; or</li>
        <li> c) The adult business has less than 10,000 square feet of covered and enclosed building space open to the public, and the adult business is located more than 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the adult business is located to the closest edge of the property line on which the facility is located):
        <ul>
            <li> i) <b>A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3-month period during the preceding 12 months) of not less than 50 children who are under 21 years of age.</b>
            <ul>
                <li> A) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</li>
            </ul> </li>
            <li> ii) A public library.</li>
            <li> iii) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court.</li>
            <li> iv) A commercial or residential recreational facility, as defined in Article 30, which serves children under 21 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet.</li>
            <li> v) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business. </li>
        </ul> </li>
    </ul> </li>
</ul>

<p>The extent of the buffer is limited to within the Urban Growth Boundary of the City of Grants Pass, Oregon. </p>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/schools_industrial_buffer_500"
lyr_md = md.Metadata()
lyr_md.title = "Schools Buffer 500' - Industrial Zoning"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = "A 500' buffer around schools not in Industrial Zoning within the City of Grants Pass, for use in marijuana business and adult use permitting."
lyr_md.description = """
<p>Application for Marijuana Business Permitting:</p>

<p>The 500 foot buffer for schools in an industrial zone is based upon <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.500:</p>
<blockquote> Marijuana Businesses may not be located within 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the Adult Business is located to the closest edge of the property line on which the facility is located): </blockquote>
<ul>
    <li> 1) <b>A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3 month period during the preceding 12 months) of not less than 50 children who are under 18 years of age;</b>
    <ul>
        <li> a) <b>Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</b></li>
    </ul> </li>
    <li> 2) A public library; or</li>
    <li> 3) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court; or</li>
    <li> 4) A commercial or residential recreational facility, as defined in Article 30, which serves children under 18 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet; or</li>
    <li> 5) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business.</li>
</ul>

<p>Application for Adult Use Permitting:</p>

<p>The 500 foot buffer for schools in an industrial zone is based upon paragraph 2(c)(ii) of <a href='https://www.grantspassoregon.gov/221/Development-Code'>Grants Pass Development Code</a> 14.630:</p>
<blockquote>Additional Criteria for Permit Approval.  A development permit for an adult business shall also comply with all of the following criteria: </blockquote>
<ul>
    <li> 1) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business is located more than 200 feet from any R-1, R-2, R-3, or R-4 residential zones (measured in a straight line from the closest edge of the property line on which the business is located to the closest edge of property in the residential zone); and </li>
        </ul> </li>
    <li> 2) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business has 10,000 or more square feet of covered and enclosed building space open to the public, and contains restaurant accommodations that are not restricted at any time by age and which restaurant accommodations have a floor area equal to or greater in size than the portion of the premises where any persons younger than 21 years of age are prohibited; or</li>
        <li> c) The adult business has less than 10,000 square feet of covered and enclosed building space open to the public, and the adult business is located more than 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the adult business is located to the closest edge of the property line on which the facility is located):
        <ul>
            <li> i) <b>A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3-month period during the preceding 12 months) of not less than 50 children who are under 21 years of age.</b>
            <ul>
                <li> A) Exception: <b>Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</b></li>
            </ul> </li>
            <li> ii) A public library.</li>
            <li> iii) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court.</li>
            <li> iv) A commercial or residential recreational facility, as defined in Article 30, which serves children under 21 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet.</li>
            <li> v) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business. </li>
        </ul> </li>
    </ul> </li>
</ul>

<p>The extent of the buffer is limited to within the Urban Growth Boundary of the City of Grants Pass, Oregon. </p>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/residential_zones"
lyr_md = md.Metadata()
lyr_md.title = "Residential Zones"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = "Residential zoning in the City of Grants Pass, Oregon."
lyr_md.description = "Source layer for generating the 200 foot residential buffer for marijuana permitting and adult use."
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/residential_zones_buffer"
lyr_md = md.Metadata()
lyr_md.title = "Residential Zones Buffer 200'"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = "A 200' buffer around residential zoning in the City of Grants Pass, Oregon, for use in marijuana and adult use permitting."
lyr_md.description = """
<p>Application for Marijuana Business Permitting:</p>

<p>The 200 foot buffer for residential zoning is based upon <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.500, first paragraph:</p>
<blockquote> Marijuana Businesses may not be located within 200 feet of any R-1, R-2, R-3, R-4 or other residential zone (measured in a straight line from the closest edge of the property line on which the Marijuana Business is located to the closest edge of property in the residential zone).</blockquote>

<p>Application for Adult Use Permitting:</p>

<p>The 200 foot buffer for residential zoning is based upon paragraph 2(c)(ii) of <a href='https://www.grantspassoregon.gov/221/Development-Code'>Grants Pass Development Code</a> 14.630:</p>
<blockquote>Additional Criteria for Permit Approval.  A development permit for an adult business shall also comply with all of the following criteria: </blockquote>
<ul>
    <li> 1) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) <b>The adult business is located more than 200 feet from any R-1, R-2, R-3, or R-4 residential zones (measured in a straight line from the closest edge of the property line on which the business is located to the closest edge of property in the residential zone)</b>; and </li>
        </ul> </li>
    <li> 2) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business has 10,000 or more square feet of covered and enclosed building space open to the public, and contains restaurant accommodations that are not restricted at any time by age and which restaurant accommodations have a floor area equal to or greater in size than the portion of the premises where any persons younger than 21 years of age are prohibited; or</li>
        <li> c) The adult business has less than 10,000 square feet of covered and enclosed building space open to the public, and the adult business is located more than 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the adult business is located to the closest edge of the property line on which the facility is located):
        <ul>
            <li> i) A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3-month period during the preceding 12 months) of not less than 50 children who are under 21 years of age.
            <ul>
                <li> A) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</li>
            </ul> </li>
            <li> ii) A public library.</li>
            <li> iii) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court.</li>
            <li> iv) A commercial or residential recreational facility, as defined in Article 30, which serves children under 21 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet.</li>
            <li> v) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business. </li>
        </ul> </li>
    </ul> </li>
</ul>

<p>The extent of the buffer is limited to within the Urban Growth Boundary of the City of Grants Pass, Oregon. </p>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/recreational_facilities"
lyr_md = md.Metadata()
lyr_md.title = "Recreational Facilities"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = "Property boundaries for commercial and residential recreational facilities exceeding a total area (indoors and outdoors) of 20,000 square feet."
lyr_md.description = "The source layer for the 1000' foot buffer around commercial and residential recreational facilities, for use in marijuana business and adult use permitting."
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/recreational_facilities_buffer"
lyr_md = md.Metadata()
lyr_md.title = "Recreational Facilities Buffer 1000'"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = "A 1000' foot buffer around commercial and residential recreational facilities, for use in marijuana business and adult use permitting."
lyr_md.description = """
<p>Application for Marijuana Business Permitting:</p>

<p>The 1000 foot buffer for recreational facilities is based upon <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.500:</p>
<blockquote> Marijuana Businesses may not be located within 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the Adult Business is located to the closest edge of the property line on which the facility is located): </blockquote>
<ul>
    <li> 1) A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3 month period during the preceding 12 months) of not less than 50 children who are under 18 years of age;
    <ul>
        <li> a) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</li>
    </ul> </li>
    <li> 2) A public library; or</li>
    <li> 3) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court; or</li>
    <li> 4) <b>A commercial or residential recreational facility, as defined in Article 30, which serves children under 18 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet</b>; or</li>
    <li> 5) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business.</li>
</ul>

<p>Application for Adult Use Permitting:</p>

<p>The 1000 foot buffer for recreaational facilities is based upon paragraph 2(c)(ii) of <a href='https://www.grantspassoregon.gov/221/Development-Code'>Grants Pass Development Code</a> 14.630:</p>
<blockquote>Additional Criteria for Permit Approval.  A development permit for an adult business shall also comply with all of the following criteria: </blockquote>
<ul>
    <li> 1) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business is located more than 200 feet from any R-1, R-2, R-3, or R-4 residential zones (measured in a straight line from the closest edge of the property line on which the business is located to the closest edge of property in the residential zone); and </li>
        </ul> </li>
    <li> 2) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business has 10,000 or more square feet of covered and enclosed building space open to the public, and contains restaurant accommodations that are not restricted at any time by age and which restaurant accommodations have a floor area equal to or greater in size than the portion of the premises where any persons younger than 21 years of age are prohibited; or</li>
        <li> c) The adult business has less than 10,000 square feet of covered and enclosed building space open to the public, and the adult business is located more than 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the adult business is located to the closest edge of the property line on which the facility is located):
        <ul>
            <li> i) A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3-month period during the preceding 12 months) of not less than 50 children who are under 21 years of age.
            <ul>
                <li> A) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</li>
            </ul> </li>
            <li> ii) A public library.</li>
            <li> iii) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court.</li>
            <li> iv) <b>A commercial or residential recreational facility, as defined in Article 30, which serves children under 21 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet.</b></li>
            <li> v) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business. </li>
        </ul> </li>
    </ul> </li>
</ul>

<p>The extent of the buffer is limited to within the Urban Growth Boundary of the City of Grants Pass, Oregon. </p>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/library"
lyr_md = md.Metadata()
lyr_md.title = "Library"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = (
    "Property boundary of the public library for the City of Grants Pass, Oregon."
)
lyr_md.description = "The source layer for the 1000' foot buffer around the public library, for use in marijuana business and adult use permitting."
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/library_buffer"
lyr_md = md.Metadata()
lyr_md.title = "Library Buffer 1000'"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = "A 1000' foot buffer around the property line for the public library, used for marijuana business and adult use permitting."
lyr_md.description = """
<p>Application for Marijuana Business Permitting:</p>

<p>The 1000 foot library buffer is based upon <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.500:</p>
<blockquote> Marijuana Businesses may not be located within 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the Adult Business is located to the closest edge of the property line on which the facility is located): </blockquote>
<ul>
    <li> 1) A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3 month period during the preceding 12 months) of not less than 50 children who are under 18 years of age;
    <ul>
        <li> a) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</li>
    </ul> </li>
    <li> 2) <b>A public library</b>; or</li>
    <li> 3) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court; or</li>
    <li> 4) A commercial or residential recreational facility, as defined in Article 30, which serves children under 18 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet; or</li>
    <li> 5) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business.</li>
</ul>

<p>Application for Adult Use Permitting:</p>

<p>The 1000 foot library buffer is based upon paragraph 2(c)(ii) of <a href='https://www.grantspassoregon.gov/221/Development-Code'>Grants Pass Development Code</a> 14.630:</p>
<blockquote>Additional Criteria for Permit Approval.  A development permit for an adult business shall also comply with all of the following criteria: </blockquote>
<ul>
    <li> 1) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business is located more than 200 feet from any R-1, R-2, R-3, or R-4 residential zones (measured in a straight line from the closest edge of the property line on which the business is located to the closest edge of property in the residential zone); and </li>
        </ul> </li>
    <li> 2) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business has 10,000 or more square feet of covered and enclosed building space open to the public, and contains restaurant accommodations that are not restricted at any time by age and which restaurant accommodations have a floor area equal to or greater in size than the portion of the premises where any persons younger than 21 years of age are prohibited; or</li>
        <li> c) The adult business has less than 10,000 square feet of covered and enclosed building space open to the public, and the adult business is located more than 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the adult business is located to the closest edge of the property line on which the facility is located):
        <ul>
            <li> i) A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3-month period during the preceding 12 months) of not less than 50 children who are under 21 years of age.
            <ul>
                <li> A) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</li>
            </ul> </li>
            <li> ii) <b>A public library.</b></li>
            <li> iii) A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court.</li>
            <li> iv) A commercial or residential recreational facility, as defined in Article 30, which serves children under 21 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet.</li>
            <li> v) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business. </li>
        </ul> </li>
    </ul> </li>
</ul>

<p>The extent of the buffer is limited to within the Urban Growth Boundary of the City of Grants Pass, Oregon. </p>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/developed_parks"
lyr_md = md.Metadata()
lyr_md.title = "Developed Parks"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = "Parks greater than 20,000 sq. ft. with facilities such as a playground or sports field in the City of Grants Pass, Oregon."
lyr_md.description = "Source layer for generating the 1000 foot parks buffer for marijuana business or adult use permitting."
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()

lyr_path = WORKSPACE + "/developed_parks_buffer"
lyr_md = md.Metadata()
lyr_md.title = "Developed Parks Buffer 1000'"
lyr_md.tags = "marijuana business permitting, adult use permitting, planning"
lyr_md.summary = "A 1000' foot buffer around parks greater than 20,000 square feet in area with facilities such as a playground or sports field, for use in marijuana business or adult use permitting in the City of Grants Pass, Oregon."
lyr_md.description = """
<p>Application for Marijuana Business Permitting:</p>

<p>The 1000 foot developed parks buffer is based upon <a href='https://www.grantspassoregon.gov/316/Municipal-Code'>Grants Pass Municipal Code</a> 11.01.500:</p>
<blockquote> Marijuana Businesses may not be located within 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the Adult Business is located to the closest edge of the property line on which the facility is located): </blockquote>
<ul>
    <li> 1) A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3 month period during the preceding 12 months) of not less than 50 children who are under 18 years of age;
    <ul>
        <li> a) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</li>
    </ul> </li>
    <li> 2) A public library; or</li>
    <li> 3) <b>A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court</b>; or</li>
    <li> 4) A commercial or residential recreational facility, as defined in Article 30, which serves children under 18 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet; or</li>
    <li> 5) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business.</li>
</ul>

<p>Application for Adult Use Permitting:</p>

<p>The 1000 foot developed parks buffer is based upon paragraph 2(c)(ii) of <a href='https://www.grantspassoregon.gov/221/Development-Code'>Grants Pass Development Code</a> 14.630:</p>
<blockquote>Additional Criteria for Permit Approval.  A development permit for an adult business shall also comply with all of the following criteria: </blockquote>
<ul>
    <li> 1) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business is located more than 200 feet from any R-1, R-2, R-3, or R-4 residential zones (measured in a straight line from the closest edge of the property line on which the business is located to the closest edge of property in the residential zone); and </li>
        </ul> </li>
    <li> 2) <ul>
        <li> a) The adult business is located in a Riverfront Tourist Commercial Zone and has 10,000 or more square feet of covered and enclosed building space open to the public; or</li>
        <li> b) The adult business has 10,000 or more square feet of covered and enclosed building space open to the public, and contains restaurant accommodations that are not restricted at any time by age and which restaurant accommodations have a floor area equal to or greater in size than the portion of the premises where any persons younger than 21 years of age are prohibited; or</li>
        <li> c) The adult business has less than 10,000 square feet of covered and enclosed building space open to the public, and the adult business is located more than 1000 feet from all of the following facilities (measured in a straight line from the closest property line on which the adult business is located to the closest edge of the property line on which the facility is located):
        <ul>
            <li> i) A “school, public” as defined by Article 30, with an average weekday attendance (during any continuous 3-month period during the preceding 12 months) of not less than 50 children who are under 21 years of age.
            <ul>
                <li> A) Exception: Marijuana producers or processors may not be located within 500 feet from a school located in an Industrial Zone.</li>
            </ul> </li>
            <li> ii) A public library.</li>
            <li> iii) <b>A public park which covers an area of not less than 20,000 square feet and has facilities such as a playground, baseball field, football field, soccer field, tennis court, basketball court, or volleyball court.</b></li>
            <li> iv) A commercial or residential recreational facility, as defined in Article 30, which serves children under 21 years of age, and has a total area for indoor and outdoor recreation (not including parking) of not less than 20,000 square feet.</li>
            <li> v) A daycare facility licensed by the State of Oregon, unless such daycare facility is established after the Marijuana Business has received all regulatory licensing and approvals, in which case the Marijuana Business shall be permitted to remain in that location, unless the State of Oregon revokes the license for the Marijuana Business. </li>
        </ul> </li>
    </ul> </li>
</ul>

<p>The extent of the buffer is limited to within the Urban Growth Boundary of the City of Grants Pass, Oregon. </p>
"""
lyr_md.credits = contact_info
lyr_md.accessConstraints = disclaimer
tgt_item_md = md.Metadata(lyr_path)
if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(lyr_md)
    tgt_item_md.save()
