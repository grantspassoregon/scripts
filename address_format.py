"""
Script documentation

- Tool parameters are accessed using arcpy.GetParameter() or 
                                     arcpy.GetParameterAsText()
- Update derived parameter values using arcpy.SetParameter() or
                                        arcpy.SetParameterAsText()
"""

import arcpy
import os
import pandas


def add_coordinates(in_table, out_table, out_gdb):
    """
    Creates a local copy of `in_table`.
    Adds long/lat and geographic coordinates to the local copy.
    """
    arcpy.env.workspace = out_gdb
    arcpy.AddMessage("Copying address layer.")
    arcpy.management.CopyFeatures(in_table, out_table)
    arcpy.env.outputCoordinateSystem = arcpy.Describe(out_table).spatialReference
    arcpy.AddMessage("Calculating latitude and longitude.")
    arcpy.management.CalculateGeometryAttributes(
        out_table,
        [["long", "POINT_X"], ["lat", "POINT_Y"]],
        coordinate_format="DMS_PACKED",
    )
    arcpy.AddMessage("Calculating geographic coordinates.")
    arcpy.management.CalculateGeometryAttributes(
        out_table,
        [["x", "POINT_X"], ["y", "POINT_Y"]],
    )


def address_export(in_table, out_table, cwd):
    """
    Reads columns from `in_table` into a dataframe and exports it to .csv at `out_table`.

    """

    cur = arcpy.SearchCursor(in_table)
    arcpy.AddMessage("Cursor opened.")
    add_num = []
    add_num_suf = []
    predir = []
    premod = []
    pretype = []
    separator = []
    name = []
    posttype = []
    subtype = []
    subid = []
    flr = []
    bldg = []
    city = []
    st = []
    stats = []
    zip = []
    long = []
    lat = []
    x = []
    y = []

    for row in cur:
        add_num.append(row.getValue(address_number))
        add_num_suf.append(row.getValue(address_number_suffix))
        predir.append(row.getValue(street_name_predirectional))
        premod.append(row.getValue(street_name_premodifier))
        pretype.append(row.getValue(street_name_pretype))
        separator.append(row.getValue(street_name_separator))
        name.append(row.getValue(street_name))
        posttype.append(row.getValue(street_name_posttype))
        subtype.append(row.getValue(subaddress_type))
        subid.append(row.getValue(subaddress_id))
        flr.append(row.getValue(floor))
        bldg.append(row.getValue(building))
        zip.append(row.getValue(postal_code))
        city.append(row.getValue(postal_community))
        st.append(row.getValue(state))
        stats.append(row.getValue(status))
        long.append(row.getValue("long"))
        lat.append(row.getValue("lat"))
        x.append(row.getValue("x"))
        y.append(row.getValue("y"))

    arcpy.AddMessage("Table read.")
    df = pandas.DataFrame()
    df["number"] = add_num
    df["number_suffix"] = add_num_suf
    df["directional"] = predir
    df["pre_modifier"] = premod
    df["pre_type"] = pretype
    df["separator"] = separator
    df["street_name"] = name
    df["street_type"] = posttype
    df["subaddress_type"] = subtype
    df["subaddress_id"] = subid
    df["floor"] = flr
    df["building"] = bldg
    df["zip"] = zip
    df["postal_community"] = city
    df["state"] = st
    df["status"] = stats
    df["longitude"] = x
    df["latitude"] = y
    # df["longitude"] = long
    # df["latitude"] = lat
    df["x"] = x
    df["y"] = y

    df["number"] = df["number"].round().astype("Int64")
    arcpy.AddMessage("type of address number is {}".format(df["number"].dtype))
    match df["zip"].dtype:
        case "float64":
            df["zip"] = df["zip"].round().astype("Int64")
            arcpy.AddMessage("Type of zip code is {}".format(df["zip"].dtype))
        case _:
            arcpy.AddMessage("Unexpected type {}".format(df["zip"].dtype))

    out_table = out_table + ".csv"
    out_table = os.path.join(cwd, out_table)
    df.to_csv(out_table, sep=",", index=False)
    arcpy.AddMessage("Exported to {}".format(out_table))


if __name__ == "__main__":

    in_feature = arcpy.GetParameterAsText(0)
    address_number = arcpy.GetParameterAsText(1)
    address_number_suffix = arcpy.GetParameterAsText(2)
    street_name_predirectional = arcpy.GetParameterAsText(3)
    street_name_premodifier = arcpy.GetParameterAsText(4)
    street_name_pretype = arcpy.GetParameterAsText(5)
    street_name_separator = arcpy.GetParameterAsText(6)
    street_name = arcpy.GetParameterAsText(7)
    street_name_posttype = arcpy.GetParameterAsText(8)
    subaddress_type = arcpy.GetParameterAsText(9)
    subaddress_id = arcpy.GetParameterAsText(10)
    floor = arcpy.GetParameterAsText(11)
    building = arcpy.GetParameterAsText(12)
    postal_code = arcpy.GetParameterAsText(13)
    postal_community = arcpy.GetParameterAsText(14)
    state = arcpy.GetParameterAsText(15)
    status = arcpy.GetParameterAsText(16)
    out_feature = arcpy.GetParameterAsText(17)
    out_gdb = arcpy.GetParameterAsText(18)
    cwd = arcpy.GetParameterAsText(19)

    arcpy.AddMessage("Parameters read {}".format(address_number))

    add_coordinates(in_feature, out_feature, out_gdb)
    address_export(out_feature, out_feature, cwd)
