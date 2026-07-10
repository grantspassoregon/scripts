import arcpy
import os
import logging

# PS> Get-content p:/service_update.log -Tail 0 -Wait
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename="p:/service_update.log",
    level=logging.INFO,
)

# Services directory
service_dir = "O:/GISUserProjects/Departments/GIS_General/Services/"
# Drafts directory
drafts_dir = service_dir + "service_drafts"

# project paths
agreements_path = service_dir + "agreements/agreements.aprx"
as_builts_path = service_dir + "as_builts/as_builts.aprx"
boundaries_path = service_dir + "boundaries/boundaries.aprx"
# businesses_path = service_dir + "businesses/businesses.aprx"
environment_path = service_dir + "environment/environment.aprx"
historic_cultural_areas_path = (
    service_dir + "historic_cultural_areas/historic_cultural_areas.aprx"
)
impervious_surface_path = service_dir + "impervious_surface/impervious_surface.aprx"
marijuana_adult_use_path = service_dir + "marijuana_adult_use/marijuana_adult_use.aprx"
parking_path = service_dir + "parking/parking.aprx"
parks_path = service_dir + "parks/parks.aprx"
parks_irrigation_path = service_dir + "parks_irrigation/parks_irrigation.aprx"
planning_path = service_dir + "planning/planning.aprx"
project_tracker_path = service_dir + "project_tracker/project_tracker.aprx"
property_path = service_dir + "property/property.aprx"
stormwater_gn_path = service_dir + "stormwater_gn/stormwater_gn.aprx"
traffic_path = service_dir + "traffic/traffic.aprx"
transportation_path = service_dir + "transportation/transportation.aprx"
wastewater_gn_path = service_dir + "wastewater_gn/wastewater_gn.aprx"
water_gn_path = service_dir + "water_gn/water_gn.aprx"
zoning_path = service_dir + "zoning/zoning.aprx"


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
        # each project file is in an eponymous folder in the drafts directory
        draft_dir = os.path.join(path, self.name)
        # create the drafts directory if it does not exist
        if not os.path.isdir(draft_dir):
            os.mkdir(draft_dir)
        # the folder may contain an older draft, delete if it does
        files = os.listdir(draft_dir)
        for file in files:
            file_path = os.path.join(draft_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        # service draft name
        sddraft_name = "temp_" + self.name + ".sddraft"
        # service definition name
        sd_name = "temp_" + self.name + ".sd"
        # full service draft path
        sddraft = os.path.join(draft_dir, sddraft_name)
        # full service definition path
        sd = os.path.join(draft_dir, sd_name)

        logging.info("Loading project %s.", self.name)
        arcpy.AddMessage("Loading project {}.".format(self.name))
        project = arcpy.mp.ArcGISProject(self.project)
        project_maps = project.listMaps()
        # map name used for project map and service name
        map_name = self.name + "_service"
        # fails with an out-of-index error if the map is not present
        # add error handling to report this condition to the user
        i = 0
        while project_maps[i].name != map_name:
            i += 1
        project_map = project_maps[i]
        logging.info("Preparing sharing draft for %s.", self.name)
        arcpy.AddMessage("Preparing sharing draft for {}.".format(self.name))
        sharing_draft = project_map.getWebLayerSharingDraft(
            "HOSTING_SERVER", "FEATURE", self.name
        )
        # needed to overwrite existing services
        sharing_draft.overwriteExistingService = True
        # set metadata for layer
        sharing_draft.summary = self.summary
        sharing_draft.tags = self.tags
        sharing_draft.description = self.description
        sharing_draft.credits = self.credits
        sharing_draft.useLimitations = self.limitations
        # configure map
        sharing_draft.allowExporting = True
        # default sharing is Individual
        sharing_draft.sharing.sharingLevel = "EVERYONE"
        logging.info("Exporting service draft for %s.", self.name)
        arcpy.AddMessage("Exporting service draft for {}.".format(self.name))
        sharing_draft.exportToSDDraft(sddraft)
        logging.info("Staging service draft for %s.", self.name)
        arcpy.AddMessage("Staging service draft for {}.".format(self.name))
        arcpy.StageService_server(sddraft, sd)
        logging.info("Draft staged for %s.", self.name)
        arcpy.AddMessage("Draft staged for {}.".format(self.name))

        logging.info("Publishing draft for %s.", self.name)
        arcpy.AddMessage("Publishing draft for {}.".format(self.name))
        arcpy.server.UploadServiceDefinition(sd, "HOSTING_SERVER")
        logging.info("Service published for %s.", self.name)
        arcpy.AddMessage("Service published for {}.".format(self.name))


class Drafts:
    """
    The `Drafts` class is a thin wrapper around a vector of type `Draft`.
    """

    def __init__(self, records):
        self.records = records

    def draft_service(self, path=drafts_dir, sel="all"):
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
        if drop_names:
            logging.info("Dropped layers: {}".format(drop_names))
            arcpy.AddMessage("Dropped layers: {}".format(drop_names))
        else:
            logging.info("All services published.")
            arcpy.AddMessage("All services published.")


### Metadata for each layer

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

name = "boundaries"
summary = "Regulatory boundaries service for the City of Grants Pass, Oregon."
tags = "planning, grants pass, oregon"
description = "Service for City Limits, UGB, Council Wards and other regulatory boundaries of the City of Grants Pass, Oregon."
project = boundaries_path
boundaries = Draft(name, summary, tags, description, credits, limitations, project)

# name = "businesses"
# summary = "Licensed businesses in the City of Grants Pass, Oregon."
# tags = "planning, grants pass, oregon"
# description = "Service for licensed businesses in the City of Grants Pass, Oregon."
# project = businesses_path
# businesses = Draft(name, summary, tags, description, credits, limitations, project)

name = "environment"
summary = (
    "Environmental features and hazards service for the City of Grants Pass, Oregon."
)
tags = "planning, grants pass, oregon"
description = (
    "Service for environmental features and hazards in the City of Grants Pass, Oregon."
)
project = environment_path
environment = Draft(name, summary, tags, description, credits, limitations, project)

name = "historic_cultural_areas"
summary = "Historic and cultural areas service for the City of Grants Pass, Oregon."
tags = "planning, grants pass, oregon"
description = (
    "Service for historic and cultural areas in the City of Grants Pass, Oregon."
)
project = historic_cultural_areas_path
historic_cultural_areas = Draft(
    name, summary, tags, description, credits, limitations, project
)

name = "impervious_surface"
summary = "Impervious surface service for the City of Grants Pass, Oregon."
tags = "public works, stormwater, grants pass, oregon"
description = "Service for impervious surface layer in the City of Grants Pass, Oregon."
project = impervious_surface_path
impervious_surface = Draft(
    name, summary, tags, description, credits, limitations, project
)

name = "marijuana_permitting"
summary = "Marijuana permitting layers for the Planning Department at the City of Grants Pass, Oregon."
tags = "planning, permitting, cannabis, grants pass, oregon"
description = "Marijuana permitting service for the Planning Department at the City of Grants Pass, Oregon."
project = marijuana_adult_use_path
marijuana_permitting = Draft(
    name, summary, tags, description, credits, limitations, project
)

# name = "merlin_landfill"
# summary = "Merlin landfill service for the City of Grants Pass, Oregon."
# tags = "planning, public works"
# description = "Service for Merlin landfill layers for the City of Grants Pass, Oregon."
# project = merlin_landfill_path
# merlin_landfill = Draft(name, summary, tags, description, credits, limitations, project)

name = "parking"
summary = "Parking service for the City of Grants Pass, Oregon."
tags = "planning, public works, grants pass, oregon"
description = "Service for parking spaces and lots in the City of Grants Pass, Oregon."
project = parking_path
parking = Draft(name, summary, tags, description, credits, limitations, project)

name = "parks"
summary = "Parks service for the City of Grants Pass, Oregon."
tags = "parks, grants pass, oregon"
description = "Service for public parks in the City of Grants Pass, Oregon."
project = parks_path
parks = Draft(name, summary, tags, description, credits, limitations, project)

name = "parks_irrigation"
summary = "Parks irrigation service for the City of Grants Pass, Oregon."
tags = "parks, grants pass, oregon"
description = "Service for irrigation infrastructure of public parks in the City of Grants Pass, Oregon."
project = parks_irrigation_path
parks_irrigation = Draft(
    name, summary, tags, description, credits, limitations, project
)

name = "planning"
summary = "Planning service for the City of Grants Pass, Oregon."
tags = "planning"
description = "Service for planning layers in the City of Grants Pass, Oregon."
project = planning_path
planning = Draft(name, summary, tags, description, credits, limitations, project)

name = "project_tracker"
summary = (
    "Tracking layers for Public Works projects at the City of Grants Pass, Oregon."
)
tags = "planning"
description = "Surveying and work footprints for Public Works projects at the City of Grants Pass, Oregon."
project = project_tracker_path
project_tracker = Draft(name, summary, tags, description, credits, limitations, project)

name = "property"
summary = "Property and land use layers for the City of Grants Pass, Oregon."
tags = "planning, addresses, parcels, subdivisions, grants pass, oregon"
description = (
    "Addresses, tax parcels and subdivisions for the City of Grants Pass, Oregon."
)
project = project_tracker_path
property = Draft(name, summary, tags, description, credits, limitations, project)

# name = "schools"
# summary = "School districts service for the City of Grants Pass, Oregon."
# tags = "planning"
# description = "Service for school district layers in the City of Grants Pass, Oregon."
# project = schools_path
# schools = Draft(name, summary, tags, description, credits, limitations, project)

name = "stormwater"
summary = "Stormwater utilities service for the City of Grants Pass, Oregon."
tags = "utilities, public works, grants pass, oregon"
description = (
    "Service for stormwater utilities layers in the City of Grants Pass, Oregon."
)
project = stormwater_gn_path
stormwater_gn = Draft(name, summary, tags, description, credits, limitations, project)

name = "traffic"
summary = "Traffic studies service for the City of Grants Pass, Oregon."
tags = "transportation, public works, grants pass, oregon"
description = "Service for traffic studies in the City of Grants Pass, Oregon."
project = traffic_path
traffic = Draft(name, summary, tags, description, credits, limitations, project)

name = "transportation"
summary = "Transportation service for the City of Grants Pass, Oregon."
tags = "public works, transportation, grants pass, oregon"
description = "Service for transporation layers in the City of Grants Pass, Oregon."
project = transportation_path
transportation = Draft(name, summary, tags, description, credits, limitations, project)

name = "sewer_utilities"
summary = "Sewer utilities service for the City of Grants Pass, Oregon."
tags = "utilities, public works, grants pass, oregon"
description = "Service for sewer utilities layers in the City of Grants Pass, Oregon."
project = wastewater_gn_path
wastewater_gn = Draft(name, summary, tags, description, credits, limitations, project)

name = "water_utilities"
summary = "Water utilities service for the City of Grants Pass, Oregon."
tags = "public works, utilities, grants pass, oregon"
description = "Service for water utilities in the City of Grants Pass, Oregon."
project = water_gn_path
water_gn = Draft(name, summary, tags, description, credits, limitations, project)

name = "zoning"
summary = "Zoning service for the City of Grants Pass, Oregon."
tags = "planning, grants pass, oregon"
description = "Service for the Zoning Map, Comprehensive Plan map and related layers in the City of Grants Pass, Oregon."
project = zoning_path
zoning = Draft(name, summary, tags, description, credits, limitations, project)

records = {}
records.update({"agreements": agreements})
records.update({"as_builts": as_builts})
records.update({"boundaries": boundaries})
# records.update({"cell_towers": cell_towers})
records.update({"environment": environment})
records.update({"historic_cultural_areas": historic_cultural_areas})
records.update({"impervious_surface": impervious_surface})
records.update({"marijuana_permitting": marijuana_permitting})
# records.update({"merlin_landfill": merlin_landfill})
records.update({"parking": parking})
records.update({"parks": parks})
records.update({"planning": planning})
records.update({"property": property})
# records.update({"schools": schools})
records.update({"stormwater_gn": stormwater_gn})
records.update({"traffic": traffic})
records.update({"transportation": transportation})
records.update({"wastewater_gn": wastewater_gn})
records.update({"water_gn": water_gn})
records.update({"zoning": zoning})

drafts = Drafts(records)
short = [
    "agreements",
    "as_builts",
    "boundaries",
    "environment",
    "historic_cultural_areas",
    "impervious_surface",
    "marijuana_permitting" "parking",
    "parks",
    "planning",
    "property",
    "stormwater_gn",
    "traffic",
    "transportation",
    "wastewater_gn",
    "water_gn",
    "zoning",
]

# logging.info("Run")
# arcpy.AddMessage("Run the command:")
# logging.info("drafts.draft_service(sel=short)")
# arcpy.AddMessage("drafts.draft_service(sel=short)")
# added for ArcPro tool
drafts.draft_service()
