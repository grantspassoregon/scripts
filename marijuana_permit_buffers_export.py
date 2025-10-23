#! Exports marijuana permitting buffer layers from the local GDB to the Enterprise GDB.
import arcpy
import os
import logging

# format log messages to include time before message
LOG_FILE = "P:/marijuana_permit_buffers.log"
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename=LOG_FILE,
    level=logging.INFO,
)
logging.info("environmental variables loaded")

# set environmental variables
# try to parallel process
arcpy.env.parallelProcessingFactor = "100%"
# overwrite existing files/gdb
arcpy.env.overwriteOutput = True

# Customize these variables to paths on your system
# path to workspace
path = "O:/GISUserProjects/Departments/GIS_General/Services/marijuana_permit_buffers"
# path to project
aprx = os.path.join(path, "marijuana_permit_buffers.aprx")
# path to project GDB
gdb = os.path.join(path, "marijuana_permit_buffers.gdb")
# path to enterprise database
egdb = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic_gpgis.sde"
# path to marijuana permitting feature set
permitting_gdb = os.path.join(egdb, "SDEPublic.GPGIS.MarijuanaPermitting")

# open arcpro project
# aprx = arcpy.mp.ArcGISProject(aprx)


def export_over(name, source_gdb, target_gdb):
    source = os.path.join(source_gdb, name)
    target = os.path.join(target_gdb, name)
    if arcpy.Exists(target):
        arcpy.management.Delete(target)
    arcpy.conversion.ExportFeatures(source, target)


export_over("permissible_area_retailers", gdb, permitting_gdb)
export_over("permissible_area_wholesalers", gdb, permitting_gdb)
export_over("permissible_area_producers", gdb, permitting_gdb)
export_over("marijuana_businesses", gdb, permitting_gdb)
export_over("marijuana_retailers_buffer", gdb, permitting_gdb)
export_over("licensed_daycares", gdb, permitting_gdb)
export_over("licensed_daycares_buffer", gdb, permitting_gdb)
export_over("schools_nonindustrial", gdb, permitting_gdb)
export_over("schools_nonindustrial_buffer", gdb, permitting_gdb)
export_over("schools_industrial", gdb, permitting_gdb)
export_over("schools_industrial_buffer_500", gdb, permitting_gdb)
export_over("schools_industrial_buffer_1000", gdb, permitting_gdb)
export_over("libraries", gdb, permitting_gdb)
export_over("libraries_buffer", gdb, permitting_gdb)
export_over("developed_parks", gdb, permitting_gdb)
export_over("developed_parks_buffer", gdb, permitting_gdb)
export_over("recreational_facilities", gdb, permitting_gdb)
export_over("recreational_facilities_buffer", gdb, permitting_gdb)
export_over("residential_zones", gdb, permitting_gdb)
export_over("residential_zones_buffer", gdb, permitting_gdb)
