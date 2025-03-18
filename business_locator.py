"""
Script documentation

- Tool parameters are accessed using arcpy.GetParameter() or
                                     arcpy.GetParameterAsText()
- Update derived parameter values using arcpy.SetParameter() or
                                        arcpy.SetParameterAsText()
"""

import arcpy
import os
import subprocess


if __name__ == "__main__":
    business = arcpy.GetParameterAsText(0)
    addresses = arcpy.GetParameterAsText(1)
    out_table = arcpy.GetParameterAsText(2)
    cwd = arcpy.GetParameterAsText(3)
    exe = arcpy.GetParameterAsText(4)

    out = out_table + ".csv"
    out = os.path.join(cwd, out)
    # map business licenses to addresses
    subprocess.run(
        [
            exe,
            "-c",
            "business",
            "-s",
            business,
            "-t",
            addresses,
            "-z",
            "common",
            "-o",
            out,
        ]
    )

    # filter missing licenses
    missing = out_table + "_missing.csv"
    missing = os.path.join(cwd, missing)
    subprocess.run(
        [
            exe,
            "-c",
            "filter",
            "-f",
            "missing",
            "-s",
            out,
            "-k",
            "business",
            "-o",
            missing,
        ]
    )

    # filter divergent licenses
    divergent = out_table + "_divergent.csv"
    divergent = os.path.join(cwd, divergent)
    subprocess.run(
        [
            exe,
            "-c",
            "filter",
            "-f",
            "divergent",
            "-s",
            out,
            "-k",
            "business",
            "-o",
            divergent,
        ]
    )
