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

    source = arcpy.GetParameterAsText(0)
    target = arcpy.GetParameterAsText(1)
    out_table = arcpy.GetParameterAsText(2)
    cwd = arcpy.GetParameterAsText(3)
    exe = arcpy.GetParameterAsText(4)

    out = out_table + ".csv"
    out = os.path.join(cwd, out_table)
    # compare addresses
    subprocess.run(
        [
            exe,
            "-c",
            "compare",
            "-s",
            source,
            "-k",
            "common",
            "-t",
            target,
            "-z",
            "common",
            "-o",
            out,
        ]
    )

    # filter missing addresses
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
            "full",
            "-o",
            missing,
        ]
    )

    # filter missing addresses
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
            "full",
            "-o",
            divergent,
        ]
    )
