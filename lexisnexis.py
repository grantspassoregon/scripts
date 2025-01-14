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


def script_tool(param0, param1):
    """Script code goes below"""

    return


if __name__ == "__main__":

    inclusion = arcpy.GetParameterAsText(0)
    exclusion = arcpy.GetParameterAsText(1)
    out = arcpy.GetParameterAsText(2)
    exe = arcpy.GetParameterAsText(3)

    cwd = os.getcwd()
    out = out + ".csv"
    out = os.path.join(cwd, out)

    subprocess.run(
        [
            exe,
            "-c",
            "lexisnexis",
            "-s",
            inclusion,
            "-k",
            "common",
            "-t",
            exclusion,
            "-z",
            "common",
            "-o",
            out,
        ]
    )
