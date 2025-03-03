import os
from arcgis.gis import GIS
import arcpy

gis = GIS()

# path to base directory for draft projects
base_path = "O:/gisuserprojects/users/erikrose/service_drafts"

# id of service definition on AGOL
agreements_id = "a54de43b273d42d6b821864fea7e516b"
cell_towers_id = "0d856642e8a747f08553b0f6584c2045"
historic_cultural_areas_id = "b8812a2306634693b3915edb7ca433d9"
impervious_surface_id = "3142e253f84a468fb917ac14ea1ae1d7"
land_use_id = "bee544cbd3d44b0dbded3cd67329b9bf"
merlin_landfill_id = "508c15ced3a54ac0aa70ac8f5f1c8d2e"
parking_id = "79b1a3ca773d41789b099422e78002f5"
parks_id = "918581aeaaf643d49ef52161b96b44d4"
planning_id = "4f78fb469b1f47758ff144d5a2714ba2"
regulatory_boundaries_id = "d7e5d2ca2769414fa0114ae411ad7b46"
schools_id = "7c7196fc6231414e93c24e858eefdc52"
sewer_utilities_id = "7eb19a97deaf4cc68e73de9082f79804"
stormwater_id = "33ece6450b5f43c3a61a462d03a45a8b"
tax_parcels_id = "f6922c750dfb417b85792d0eb5bf14c2"
transportation_id = "867fce923516477c88aec85ae2c90474"
water_utilities_id = "ff95504c06494f90863dc496f33d5481"
zoning_id = "b94fd0b63ab046569bd6419d70d59250"

short = [
    "agreements",
    "historic_cultural_areas",
    "land_use",
    "impervious_surface",
    "merlin_landfill",
    "parking",
    "parks",
    "planning",
    "regulatory_boundaries",
    "sewer_utilities",
    "stormwater",
    "transportation",
    "water_utilities",
    "zoning",
]


class Service:
    def __init__(self, name, id):
        self.name = name
        self.id = id

    def publish(self, gis, path):
        sd_name = "temp_" + self.name + ".sd"
        draft_dir = os.path.join(path, self.name)
        sd = os.path.join(draft_dir, sd_name)
        arcpy.AddMessage(
            "Searching for {} service on {}".format(self.name, gis.properties.name)
        )
        item = gis.content.get(self.id)
        arcpy.AddMessage("Updating service for {}".format(self.name))
        item.update(data=sd)
        arcpy.AddMessage("Overwriting service for {}".format(self.name))
        fs = item.publish(overwrite=True, file_type="serviceDefinition")
        arcpy.AddMessage("Service updated for {}".format(fs.title))


class Services:
    def __init__(self, records):
        self.records = records

    def publish(self, gis, path, sel=short):
        failed = 0
        fail_names = []
        if sel == "all":
            for service in self.records.values():
                try:
                    service.publish(gis, path)
                except Exception as e:
                    arcpy.AddMessage("Exception {}".format(e))
                    arcpy.AddMessage("Failed to publish {}".format(service.name))
                    failed += 1
                    fail_names.append(service.name)
        else:
            for item in sel:
                service = self.records[item]
                try:
                    service.publish(gis, path)
                except Exception as e:
                    arcpy.AddMessage("Exception {}".format(e))
                    arcpy.AddMessage("Failed to publish {}".format(service.name))
                    failed += 1
                    fail_names.append(service.name)
        arcpy.AddMessage("Services published, {} failed".format(failed))
        arcpy.AddMessage("Failed services: {}.".format(fail_names))


agreements = Service("agreements", agreements_id)
cell_towers = Service("cell_towers", cell_towers_id)
historic_cultural_areas = Service("historic_cultural_areas", historic_cultural_areas_id)
impervious_surface = Service("impervious_surface", impervious_surface_id)
land_use = Service("land_use", land_use_id)
merlin_landfill = Service("merlin_landfill", merlin_landfill_id)
parking = Service("parking", parking_id)
parks = Service("parks", parks_id)
planning = Service("planning", planning_id)
regulatory_boundaries = Service("regulatory_boundaries", regulatory_boundaries_id)
schools = Service("schools", schools_id)
sewer_utilities = Service("sewer_utilities", sewer_utilities_id)
stormwater = Service("stormwater", stormwater_id)
tax_parcels = Service("tax_parcels", tax_parcels_id)
transportation = Service("transportation", transportation_id)
water_utilities = Service("water_utilities", water_utilities_id)
zoning = Service("zoning", zoning_id)

records = {}
records["agreements"] = agreements
records["cell_towers"] = cell_towers
records["historic_cultural_areas"] = historic_cultural_areas
records["impervious_surface"] = impervious_surface
records["land_use"] = land_use
records["merlin_landfill"] = merlin_landfill
records["parking"] = parking
records["parks"] = parks
records["planning"] = planning
records["regulatory_boundaries"] = regulatory_boundaries
records["schools"] = schools
records["sewer_utilities"] = sewer_utilities
records["stormwater"] = stormwater
records["tax_parcels"] = tax_parcels
records["transportation"] = transportation
records["water_utilities"] = water_utilities
records["zoning"] = zoning

services = Services(records)
services.publish(gis, base_path, short)
