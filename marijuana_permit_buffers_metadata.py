import arcgis
from arcgis.gis import GIS
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)

load_dotenv()
ARCGIS_USERNAME = os.getenv("ARCGIS_USERNAME")
ARCGIS_PASSWORD = os.getenv("ARCGIS_PASSWORD")
API_KEY = os.getenv("API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
PORTAL = "https://grantspassoregon.maps.arcgis.com/"
INTERNAL = os.getenv("INTERNAL")
INTERNAL_ID = os.getenv("INTERNAL_ID")
logging.info("environmental variables loaded")

gis = GIS(PORTAL, client_id=CLIENT_ID)
marijuana_permit_service = gis.content.get("b585dd65eb4544c190cf5a0e2b3e8beb")

# for lyr in marijuana_permit_service.layers:
#     lyr.download_metadata(save_folder="./metadata")
# retail_permissible = marijuana_permit_service.copy_feature_layer_collection(
#     "marijuana_permitting", layers=0
# )
# retail_permissible.download_metadata(save_folder="./metadata")
