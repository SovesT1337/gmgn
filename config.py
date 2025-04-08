import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("API_KEY", "1")
PROXY_SOURCE_URL = os.environ.get("PROXY_SOURCE_URL", "")