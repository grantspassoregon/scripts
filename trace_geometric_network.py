import arcpy

arcpy.env.workspace = "in_memory"
arcpy.env.overwriteOutput = True
mxd = arcpy.mapping.MapDocument("CURRENT")
df = arcpy.mapping.ListDataFrames(mxd)[0]

og_water_net = "O:/Connection (Admin)/Connection docs/OUTRIGGER_COGP_GIS_SDEPublic.sde/SDEPublic.GPGIS.WaterDistribution_Net5"

# Define Parameters
inflags = arcpy.GetParameterAsText(0)  # type: layer
geoNetwork = arcpy.GetParameterAsText(1)  # type: geometric network
barriers = arcpy.GetParameterAsText(2)  # type: layer (optional)
outGDB = arcpy.GetParameterAsText(3)  # type: data element
outName = arcpy.GetParameterAsText(4)  # type: string


def makeFullPath(path, name):
    return path + "\\" + name


def TraceCapture(inflags, geoNetwork, barriers, outPath, outName):
    flagList = list(arcpy.da.SearchCursor(inflags, ["OBJECTID", "UNITID"]))
    segmentCapture = []
    for (
        flag
    ) in (
        flagList
    ):  # using list instead of counter combats errors with non-sequential OBJECTID's
        try:
            trace = flag[0]
            outputLayer = "Trace"
            expression = '"OBJECTID" =' + str(trace)
            arcpy.SelectLayerByAttribute_management(
                inflags, "NEW_SELECTION", expression
            )
            arcpy.TraceGeometricNetwork_management(
                geoNetwork, outputLayer, inflags, "TRACE_DOWNSTREAM", barriers
            )
            arcpy.AddMessage("Trace_" + str(trace) + " complete")

            # access trace from "in_memory"
            for lyr in arcpy.mapping.Layer(outputLayer):
                for x in arcpy.mapping.ListLayers(lyr):
                    if x.name == "Sewers":
                        pipesCursor = arcpy.da.SearchCursor(x, "ASSETID")
                        for i in pipesCursor:
                            segmentCapture.append(
                                (flag[1], i[0])
                            )  # main event: append tuples relating manhole UnitID to pipe AssetID
        except RuntimeError:
            arcpy.AddMessage("Flag " + str(trace) + " was invalid and skipped.")
            continue
    arcpy.SelectLayerByAttribute_management(inflags, "CLEAR_SELECTION")

    # write segmentCapture to a GBD table
    arcpy.CreateTable_management(outPath, outName)
    outTable = makeFullPath(outPath, outName)
    arcpy.AddField_management(outTable, "manholeID", "TEXT", "", "", 10)
    arcpy.AddField_management(outTable, "pipeID", "TEXT", "", "", 10)

    with arcpy.da.InsertCursor(outTable, ["manholeID", "pipeID"]) as cursor:
        for row in segmentCapture:
            cursor.insertRow(row)

    # add new table to the map
    tView = arcpy.mapping.TableView(outTable)
    arcpy.mapping.AddTableView(df, tView)


# execute TraceCapture Tool
TraceCapture(inflags, geoNetwork, barriers, outGDB, outName)

# For display, execute trace for all flags
arcpy.TraceGeometricNetwork_management(
    geoNetwork, "Trace", inflags, "TRACE_DOWNSTREAM", barriers
)

# add final trace to map, from "in_memory location"
addLayer = arcpy.mapping.Layer("Trace")
arcpy.mapping.AddLayer(df, addLayer)
