from arcgis.gis import GIS
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)

# Load .env
load_dotenv()
# Read portal and client id from .env
PORTAL = os.getenv("INTERNAL_PORTAL")
CLIENT_ID = os.getenv("INTERNAL_PORTAL_ID")
logging.info("Environmental variables loaded.")
GIS_CONN = GIS(PORTAL, client_id=CLIENT_ID)
logging.info("Login successful.")
