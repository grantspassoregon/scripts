import arcpy
import logging

ARCGIS_WORKSPACE = (
    "O:/GISUserProjects/Users/ErikRose/address_site_points/address_site_points.gdb"
)
ARCGIS_PROJECT = (
    "O:/GISUserProjects/Users/ErikRose/address_site_points/address_site_points.aprx"
)
# this project imports the authorized street names domain from Josephine County's
# ECSO 911 service maintained Chad Murders
# https://gis.ecso911.com/server/rest/services/Hosted/AuthorizedStreetNameTable/FeatureServer/0

LOG_FILE = "P:/street_name_domain.log"

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
# domain_table = "AuthorizedStreetNameTable"
# code_field = "NAME"
# desc_field = "DESCRIPT"
# domain_workspace = ARCGIS_WORKSPACE
# domain_name = "StreetNames"
# domain_desc = "Authorized street names for Josephine County."
# logging.info("Local parameters loaded.")
#
# arcpy.TableToDomain_management(
#     domain_table, code_field, desc_field, domain_workspace, domain_name, domain_desc
# )
# logging.info("%s domain created.", domain_name)

# add proposed street names to domain
# arcpy.management.AddCodedValueToDomain(
#     ARCGIS_WORKSPACE, "StreetNames", "CARA MIA", "CARA MIA"
# )
# arcpy.management.AddCodedValueToDomain(
#     ARCGIS_WORKSPACE, "StreetNames", "KATRINA", "KATRINA"
# )
# arcpy.management.AddCodedValueToDomain(
#     ARCGIS_WORKSPACE, "StreetNames", "GRAYLING", "GRAYLING"
# )
# arcpy.management.AddCodedValueToDomain(
#     ARCGIS_WORKSPACE, "StreetNames", "FAMILY", "FAMILY"
# )
# arcpy.management.AddCodedValueToDomain(
#     ARCGIS_WORKSPACE, "StreetNames", "DIETZ", "DIETZ"
# )
# arcpy.management.AddCodedValueToDomain(
#     ARCGIS_WORKSPACE, "StreetNames", "SILVERBROOK", "SILVERBROOK"
# )
# arcpy.management.AddCodedValueToDomain(
#     ARCGIS_WORKSPACE, "StreetNames", "BRIANNA'S", "BRIANNA'S"
# )
# arcpy.management.AddCodedValueToDomain(
#     ARCGIS_WORKSPACE, "StreetNames", "ALBERTA ROSE", "ALBERTA ROSE"
# )
# arcpy.management.AddCodedValueToDomain(
#     ARCGIS_WORKSPACE, "StreetNames", "COOPERS LANDING", "COOPERS LANDING"
# )
# arcpy.management.AddCodedValueToDomain(
#     ARCGIS_WORKSPACE, "StreetNames", "TAYBERRY GLEN", "TAYBERRY GLEN"
# )
# arcpy.management.AddCodedValueToDomain(
#     ARCGIS_WORKSPACE, "StreetNames", "BEAKER", "BEAKER"
# )
# arcpy.management.AddCodedValueToDomain(
#     ARCGIS_WORKSPACE, "StreetNames", "JUNE BUG", "JUNE BUG"
# )
arcpy.management.AddCodedValueToDomain(
    ARCGIS_WORKSPACE, "StreetNames", "FORMOSA", "FORMOSA"
)
arcpy.management.AddCodedValueToDomain(
    ARCGIS_WORKSPACE, "StreetNames", "BEAVILLA", "BEAVILLA"
)
logging.info("Proposed roads added to domain.")
