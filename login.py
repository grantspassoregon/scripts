from arcgis.gis import GIS
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)

load_dotenv()
PORTAL = "https://grantspassoregon.maps.arcgis.com/"
CLIENT_ID = os.getenv("CLIENT_ID")
ARCGIS_USERNAME = os.getenv("ARCGIS_USERNAME")
ARCGIS_PASSWORD = os.getenv("ARCGIS_PASSWORD")
logging.info("Environmental variables loaded.")
