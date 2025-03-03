import arcpy
import os, sys
from arcgis.gis import GIS
import logging

# PS> Get-content p:/service_update.log -Tail 0 -Wait
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename="p:/service_update.log",
    level=logging.INFO,
)

# path to base directory for draft projects
base_path = "O:/gisuserprojects/users/erikrose/service_drafts"
# path to template arpx projects for services
agreements_path = "O:/gisuserprojects/users/erikrose/agreements/agreements.aprx"
as_builts_path = "O:/gisuserprojects/users/erikrose/as_builts/as_builts.aprx"
cell_towers_path = "O:/gisuserprojects/users/erikrose/cell_towers/cell_towers.aprx"
environmental_features_path = "O:/gisuserprojects/users/erikrose/environmental_features/environmental_features.aprx"
hazards_path = "O:/gisuserprojects/users/erikrose/hazards/hazards.aprx"
historic_cultural_areas_path = "O:/gisuserprojects/users/erikrose/historic_areas.aprx"
impervious_surface_path = "O:/gisuserprojects/users/erikrose/stormwater/stormwater.aprx"
land_use_path = "O:/gisuserprojects/users/erikrose/land_use/land_use.aprx"
merlin_landfill_path = (
    "O:/gisuserprojects/users/erikrose/merlin_landfill/merlin_landfill.aprx"
)
parking_path = "O:/gisuserprojects/users/erikrose/parking/parking.aprx"
parks_path = "O:/gisuserprojects/users/erikrose/parks/parks.aprx"
planning_path = "O:/gisuserprojects/users/erikrose/planning/planning.aprx"
regulatory_boundaries_path = (
    "O:/gisuserprojects/users/erikrose/regulatory_boundaries/regulatory_boundaries.aprx"
)
schools_path = "O:/gisuserprojects/users/erikrose/schools/schools.aprx"
sewer_utilities_path = (
    "O:/gisuserprojects/users/erikrose/sewer_utilities/sewer_utilities.aprx"
)
stormwater_path = "O:/gisuserprojects/users/erikrose/stormwater/stormwater.aprx"
tax_parcels_path = "O:/gisuserprojects/users/erikrose/tax_parcels/tax_parcels.aprx"
traffic_path = "O:/gisuserprojects/users/erikrose/traffic/traffic.aprx"
transportation_path = (
    "O:/gisuserprojects/users/erikrose/transportation/transportation.aprx"
)
water_utilities_path = "O:/gisuserprojects/users/erikrose/water_utilities.aprx"
zoning_path = "O:/gisuserprojects/users/erikrose/zoning.aprx"


class Draft:
    """
    The `Draft` class holds the required data to publish a service draft.
    """

    def __init__(self, name, summary, tags, description, credits, limitations, project):
        self.name = name
        self.summary = summary
        self.tags = tags
        self.description = description
        self.credits = credits
        self.limitations = limitations
        self.project = project

    def draft_service(self, path):
        draft_dir = os.path.join(path, self.name)
        if not os.path.isdir(draft_dir):
            os.mkdir(draft_dir)
        files = os.listdir(draft_dir)
        for file in files:
            file_path = os.path.join(draft_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        sddraft_name = "temp_" + self.name + ".sddraft"
        sd_name = "temp_" + self.name + ".sd"
        sddraft = os.path.join(draft_dir, sddraft_name)
        sd = os.path.join(draft_dir, sd_name)

        logging.info("Loading project %s.", self.name)
        arcpy.AddMessage("Loading project {}.".format(self.name))
        project = arcpy.mp.ArcGISProject(self.project)
        project_maps = project.listMaps()
        i = 0
        while project_maps[i].name != self.name:
            i += 1
        project_map = project_maps[i]
        logging.info("Preparing sharing draft for %s.", self.name)
        arcpy.AddMessage("Preparing sharing draft for {}.".format(self.name))
        sharing_draft = project_map.getWebLayerSharingDraft(
            "HOSTING_SERVER", "FEATURE", self.name
        )
        sharing_draft.summary = self.summary
        sharing_draft.tags = self.tags
        sharing_draft.description = self.description
        sharing_draft.credits = self.credits
        sharing_draft.useLimitations = self.limitations
        logging.info("Exporting service draft for %s.", self.name)
        arcpy.AddMessage("Exporting service draft for {}.".format(self.name))
        sharing_draft.exportToSDDraft(sddraft)
        logging.info("Staging service draft for %s.", self.name)
        arcpy.AddMessage("Staging service draft for {}.".format(self.name))
        arcpy.StageService_server(sddraft, sd)
        logging.info("Draft staged for %s.", self.name)
        arcpy.AddMessage("Draft staged for {}.".format(self.name))


class Drafts:
    """
    The `Drafts` class is a thin wrapper around a vector of type `Draft`.
    """

    def __init__(self, records):
        self.records = records

    def draft_service(self, path=base_path, sel="all"):
        dropped = 0
        drop_names = []
        if sel == "all":
            for draft in self.records.values():
                try:
                    draft.draft_service(path)
                except Exception as e:
                    logging.info("Exception %s.", e)
                    arcpy.AddMessage("Exception {}.".format(e))
                    logging.info("Dropping %s.", draft.name)
                    arcpy.AddMessage("Dropping {}.".format(draft.name))
                    dropped += 1
                    drop_names.append(draft.name)
        else:
            for item in sel:
                draft = self.records[item]
                try:
                    draft.draft_service(path)
                except Exception as e:
                    logging.info("Exception %s.", e)
                    arcpy.AddMessage("Exception {}.".format(e))
                    logging.info("Dropping %s.", draft.name)
                    arcpy.AddMessage("Dropping {}.".format(draft.name))
                    dropped += 1
                    drop_names.append(draft.name)
        logging.info("Service drafts complete, {} dropped.", dropped)
        arcpy.AddMessage("Service drafts complete, {} dropped.".format(dropped))
        arcpy.AddMessage("Dropped layers: {}".format(drop_names))


credits = "City of Grants Pass"
limitations = """
DISCLAIMER

Basic data for pre-planning purposes, not to be relied upon for professional services. The geographic information systems (GIS) data made available are developed and maintained by the City of Grants Pass and Josephine County. The City of Grants Pass makes no warranties, claims, or representations (express or implied) as to the use of the maps and data made available by City personnel or at City websites. There are no implied warranties of merchantability or fitness for a particular purpose. The user acknowledges and accepts all inherent limitations of the maps and data, including the fact that the maps and data are dynamic and in a constant state of maintenance, correction and revision. Any maps and associated data for access do not represent a survey. No liability is assumed for the accuracy of the data delineated on any map, or data disseminated in any other form, either expressed or implied. Data includes but is not limited to the following: hard copy maps, web maps/applications, auto-CAD (.DWG/.DXF), shapefiles, geodatabases, and/or all image file formats. Please consult appropriate professionals when planning any variety of jobs (RPLs, licensed engineers, 811, title company, etc.)
"""

name = "agreements"
summary = "Agreements service for the City of Grants Pass, Oregon."
tags = "planning"
description = "Fee-in-Lieu, Service and Annexation, and Deferred Development agreements for the City of Grants Pass, Oregon."
project = agreements_path
agreements = Draft(name, summary, tags, description, credits, limitations, project)

name = "as_builts"
summary = "As-builts service for the City of Grants Pass, Oregon."
tags = "planning"
description = "Service for as-builts in the City of Grants Pass, Oregon."
project = as_builts_path
as_builts = Draft(name, summary, tags, description, credits, limitations, project)

name = "cell_towers"
summary = "Cell towers service for the City of Grants Pass, Oregon."
tags = "planning"
description = "Service for cell tower locations in the City of Grants Pass, Oregon."
project = cell_towers_path
cell_towers = Draft(name, summary, tags, description, credits, limitations, project)

name = "environmental_features"
summary = "Environmental features service for the City of Grants Pass, Oregon."
tags = "planning"
description = "Service for environmental features in the City of Grants Pass, Oregon."
project = environmental_features_path
environmental_features = Draft(
    name, summary, tags, description, credits, limitations, project
)

name = "hazards"
summary = "Environmental hazards service for the City of Grants Pass, Oregon."
tags = "planning"
description = (
    "Service for environmental hazards layers in the City of Grants Pass, Oregon."
)
project = hazards_path
hazards = Draft(name, summary, tags, description, credits, limitations, project)

name = "historic_cultural_areas"
summary = "Historic and cultural areas service for the City of Grants Pass, Oregon."
tags = "planning"
description = (
    "Service for historic and cultural areas in the City of Grants Pass, Oregon."
)
project = historic_cultural_areas_path
historic_cultural_areas = Draft(
    name, summary, tags, description, credits, limitations, project
)

name = "impervious_surface"
summary = "Impervious surface service for the City of Grants Pass, Oregon."
tags = "planning"
description = "Service for impervious surface layer in the City of Grants Pass, Oregon."
project = impervious_surface_path
impervious_surface = Draft(
    name, summary, tags, description, credits, limitations, project
)

name = "land_use"
summary = "Land use service for the City of Grants Pass, Oregon."
tags = "planning"
description = "Service for addresses, subdivision boundaries, building footprints and other land use layers for the City of Grants Pass, Oregon."
project = land_use_path
land_use = Draft(name, summary, tags, description, credits, limitations, project)

name = "merlin_landfill"
summary = "Merlin landfill service for the City of Grants Pass, Oregon."
tags = "planning, public works"
description = "Service for Merlin landfill layers for the City of Grants Pass, Oregon."
project = merlin_landfill_path
merlin_landfill = Draft(name, summary, tags, description, credits, limitations, project)

name = "parking"
summary = "Parking service for the City of Grants Pass, Oregon."
tags = "planning, public works"
description = "Service for parking spaces and lots in the City of Grants Pass, Oregon."
project = parking_path
parking = Draft(name, summary, tags, description, credits, limitations, project)

name = "parks"
summary = "Parks service for the City of Grants Pass, Oregon."
tags = "planning"
description = "Service for public parks in the City of Grants Pass, Oregon."
project = parks_path
parks = Draft(name, summary, tags, description, credits, limitations, project)

name = "planning"
summary = "Planning service for the City of Grants Pass, Oregon."
tags = "planning"
description = "Service for planning layers in the City of Grants Pass, Oregon."
project = planning_path
planning = Draft(name, summary, tags, description, credits, limitations, project)

name = "regulatory_boundaries"
summary = "Regulatory boundaries service for the City of Grants Pass, Oregon."
tags = "planning"
description = "Service for City Limits, UGB, Council Wards and other regulatory boundaries of the City of Grants Pass, Oregon."
project = regulatory_boundaries_path
boundaries = Draft(name, summary, tags, description, credits, limitations, project)

name = "schools"
summary = "School districts service for the City of Grants Pass, Oregon."
tags = "planning"
description = "Service for school district layers in the City of Grants Pass, Oregon."
project = schools_path
schools = Draft(name, summary, tags, description, credits, limitations, project)

name = "sewer_utilities"
summary = "Sewer utilities service for the City of Grants Pass, Oregon."
tags = "utilities"
description = "Service for sewer utilities layers in the City of Grants Pass, Oregon."
project = sewer_utilities_path
sewer_utilities = Draft(name, summary, tags, description, credits, limitations, project)

name = "stormwater"
summary = "Stormwater utilities service for the City of Grants Pass, Oregon."
tags = "utilities"
description = (
    "Service for stormwater utilities layers in the City of Grants Pass, Oregon."
)
project = stormwater_path
stormwater = Draft(name, summary, tags, description, credits, limitations, project)

name = "tax_parcels"
summary = "Tax parcels service for the City of Grants Pass, Oregon."
tags = "planning"
description = "Service for tax parcels in the City of Grants Pass, Oregon."
project = tax_parcels_path
tax_parcels = Draft(name, summary, tags, description, credits, limitations, project)

name = "traffic"
summary = "Traffic studies service for the City of Grants Pass, Oregon."
tags = "transportation, public works"
description = "Service for traffic studies in the City of Grants Pass, Oregon."
project = traffic_path
traffic = Draft(name, summary, tags, description, credits, limitations, project)

name = "transportation"
summary = "Transportation service for the City of Grants Pass, Oregon."
tags = "public works"
description = "Service for transporation layers in the City of Grants Pass, Oregon."
project = transportation_path
transportation = Draft(name, summary, tags, description, credits, limitations, project)

name = "water_utilities"
summary = "Water utilities service for the City of Grants Pass, Oregon."
tags = "public works"
description = "Service for water utilities in the City of Grants Pass, Oregon."
project = water_utilities_path
water_utilities = Draft(name, summary, tags, description, credits, limitations, project)

name = "zoning"
summary = "Zoning service for the City of Grants Pass, Oregon."
tags = "public works"
description = "Service for the Zoning Map, Comprehensive Plan map and related layers in the City of Grants Pass, Oregon."
project = zoning_path
zoning = Draft(name, summary, tags, description, credits, limitations, project)

records = {}
records.update({"agreements": agreements})
records.update({"as_builts": as_builts})
records.update({"boundaries": boundaries})
records.update({"cell_towers": cell_towers})
records.update({"environmental_features": environmental_features})
records.update({"hazards": hazards})
records.update({"historic_cultural_areas": historic_cultural_areas})
records.update({"impervious_surface": impervious_surface})
records.update({"land_use": land_use})
records.update({"merlin_landfill": merlin_landfill})
records.update({"parking": parking})
records.update({"parks": parks})
records.update({"planning": planning})
records.update({"schools": schools})
records.update({"sewer_utilities": sewer_utilities})
records.update({"stormwater": stormwater})
records.update({"tax_parcels": tax_parcels})
records.update({"traffic": traffic})
records.update({"transportation": transportation})
records.update({"water_utilities": water_utilities})
records.update({"zoning": zoning})

drafts = Drafts(records)
short = [
    "agreements",
    "as_builts",
    "boundaries",
    "cell_towers",
    "environmental_features",
    "hazards",
    "historic_cultural_areas",
    "impervious_surface",
    "land_use",
    "merlin_landfill",
    "parking",
    "parks",
    "planning",
    "schools",
    "sewer_utilities",
    "stormwater",
    "tax_parcels",
    "traffic",
    "transportation",
    "water_utilities",
    "zoning",
]

# logging.info("Run")
# arcpy.AddMessage("Run the command:")
# logging.info("drafts.draft_service(sel=short)")
# arcpy.AddMessage("drafts.draft_service(sel=short)")
# added for ArcPro tool
drafts.draft_service()
