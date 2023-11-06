import arcpy
import logging

arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.overwriteOutput = True

log_file = arcpy.GetSystemEnvironment("LINKS_LOG")
logging.info("Log file: %s.", log_file)
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename=log_file,
    level=logging.INFO,
)

project_dir = arcpy.GetSystemEnvironment("LINKS_DIR")
workspace = arcpy.GetSystemEnvironment("LINKS_WORKSPACE")
arcpy.env.workspace = workspace
arcgis_project = arcpy.GetSystemEnvironment("LINKS_PROJECT")
aprx = arcpy.mp.ArcGISProject(arcgis_project)

logging.info("Importing layers from SDE database.")
afds = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.plan_AFD_RD"
ddas = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.plan_DEFERREDDEVELOPMENTAGREEMENTS"
filas = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.plan_FILAGREEMENT"
sas = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.plan_SERVICEANNEXATIONAGREEMENTS"
urps = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.plan_UNRECORDEDPARCELDOCUMENTS"
logging.info("Fee in Lieu Agreements loaded.")
# arcpy.management.CopyFeatures(og_filas, "filas")
# arcpy.management.AddField("filas", "web_link", "TEXT", "", "", "100", "Web Link")

web_link_dir = "o:/gisuserprojects/departments/gis_general/processes/web_links"
in_table = web_link_dir + "/" + "fila_links.csv"
arcpy.conversion.ExportTable(in_table, "fila_links")
in_table = web_link_dir + "/" + "advance_finance_links.csv"
arcpy.conversion.ExportTable(in_table, "afd_links")
in_table = web_link_dir + "/" + "deferred_development_links.csv"
arcpy.conversion.ExportTable(in_table, "dda_links")
in_table = web_link_dir + "/" + "service_annexation_links.csv"
arcpy.conversion.ExportTable(in_table, "sa_links")
in_table = web_link_dir + "/" + "unrecorded_parcels_links.csv"
arcpy.conversion.ExportTable(in_table, "urp_links")

arcpy.management.AddJoin("filas", "INSTRUMENT", "fila_links", "field")
arcpy.management.CalculateField(
    "filas", "web_link", "$feature['fila_links.web_link']", "ARCADE"
)
arcpy.management.RemoveJoin("filas", "fila_links")
arcpy.management.Delete("fila_links")
