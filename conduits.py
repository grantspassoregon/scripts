import arcpy
import csv
import logging
import os

# PS> Get-content p:/service_update.log -Tail 0 -Wait
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename="p:/service_update.log",
    level=logging.INFO,
)

arcpy.env.overwriteOutput = True


def field_map(fms, lyr, from_name, to_name, rule):
    fm = arcpy.FieldMap()
    fm.addInputField(lyr, from_name)
    fm.mergeRule = rule
    fm_name = fm.outputField
    fm_name.name = to_name
    fm_name.aliasName = to_name
    fm.outputField = fm_name
    fms.addFieldMap(fm)


def convert_csv_to_tsv(input_file, output_file):
    """
    Convert CSV file to TSV file with headers removed.

    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output TSV file
    """
    try:
        with open(input_file, "r", newline="", encoding="utf-8") as infile:
            # Create CSV reader
            reader = csv.reader(infile)

            # Skip the header row
            next(reader, None)

            with open(output_file, "w", newline="", encoding="utf-8") as outfile:
                # Create CSV writer with tab delimiter
                writer = csv.writer(outfile, delimiter="\t")

                # Write all remaining rows (excluding header)
                for row in reader:
                    writer.writerow(row)

        print(f"Successfully converted {input_file} to {output_file}")
        print("Headers removed and converted to tab-separated values.")

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
    except Exception as e:
        print(f"Error: {e}")


# Finance projects directory
fin_dir = "O:/GISUserProjects/Departments/GIS_General/Finance_Projects"

project_path = os.path.join(fin_dir, "conduits/conduits.aprx")
logging.info("Loading project conduits.")
arcpy.AddMessage("Loading project conduits.")
project = arcpy.mp.ArcGISProject(project_path)
project_maps = project.listMaps()
# map name used for project map and service name
map_name = "conduits"
# fails with an out-of-index error if the map is not present
# add error handling to report this condition to the user
i = 0
while project_maps[i].name != map_name:
    i += 1
project_map = project_maps[i]
logging.info("conduits map found.")

taxlots = project_map.listLayers("taxlots")[0]
logging.info("Taxlot layer found.")
arcpy.AddMessage("Taxlot layer found.")

fms = arcpy.FieldMappings()
field_map(fms, taxlots, "ACCOUNT", "account", "First")
field_map(fms, taxlots, "MapNum", "map_number", "First")
field_map(fms, taxlots, "SITUS", "address", "First")

target_dir = os.path.join(fin_dir, "Conduits_Output")
csv_path = os.path.join(target_dir, "conduits_property.csv")
txt_path = "C:/Users/erose/City of Grants Pass, Oregon/COGP Home - Conduits/conduits_property.txt"

logging.info("Exporting parcel table.")
arcpy.AddMessage("Exporting parcel table.")
arcpy.conversion.ExportTable(
    taxlots,
    csv_path,
    None,
    "NOT_USE_ALIAS",
    fms,
)
logging.info("Parcel table exported.")
arcpy.AddMessage("Parcel table exported.")

logging.info("Converting to tab-separated values.")
arcpy.AddMessage("Converting to tab-separated values.")
convert_csv_to_tsv(csv_path, txt_path)
logging.info("Table ready at %s.", txt_path)
arcpy.AddMessage("Table ready at {}".format(txt_path))
