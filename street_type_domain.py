import arcpy
import logging

ARCGIS_WORKSPACE = (
    "O:/GISUserProjects/Users/ErikRose/address_site_points/address_site_points.gdb"
)
ARCGIS_PROJECT = (
    "O:/GISUserProjects/Users/ErikRose/address_site_points/address_site_points.aprx"
)

LOG_FILE = "P:/street_type_domain.log"

logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename=LOG_FILE,
    level=logging.INFO,
)

arcpy.env.parallelProcessingFactor = "1000%"
arcpy.env.workspace = ARCGIS_WORKSPACE
logging.info("Workspace loaded.")
aprx = arcpy.mp.ArcGISProject(ARCGIS_PROJECT)
logging.info("Project loaded.")

# copy street name domain from county service
domain_table = "p:/StreetTypeDomain.dbf"
code_field = "Street_Typ"
desc_field = "Street_Typ"
domain_workspace = ARCGIS_WORKSPACE
domain_name = "StreetTypes"
domain_desc = "Authorized street types for Josephine County."
logging.info("Local parameters loaded.")

# arcpy.management.TableToDomain(
#     domain_table,
#     code_field,
#     desc_field,
#     domain_workspace,
#     domain_name,
#     domain_desc,
#     "REPLACE",
# )
# logging.info("%s domain created.", domain_name)

arcpy.management.AddCodedValueToDomain(
    ARCGIS_WORKSPACE, "StreetTypes", "CUTOFF", "CUTOFF"
)
arcpy.management.AddCodedValueToDomain(
    ARCGIS_WORKSPACE, "StreetTypes", "DRIVE CUTOFF", "DRIVE CUTOFF"
)
