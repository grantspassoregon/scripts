import arcpy

# path to connection doc set manually in system environmental variables
connection = arcpy.GetSystemEnvironment("ARCGIS_CONNECTION")
arcpy.management.Compress(connection)
arcpy.management.RebuildIndexes(connection, "SYSTEM")
arcpy.management.AnalyzeDatasets(
    connection, "SYSTEM", [], "ANALYZE_BASE", "ANALYZE_DELTA", "ANALYZE_ARCHIVE"
)
