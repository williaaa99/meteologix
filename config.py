import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
EVOLUTION_API_URL: str = os.environ.get("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY: str = os.environ["EVOLUTION_API_KEY"]
EVOLUTION_INSTANCE: str = os.environ.get("EVOLUTION_INSTANCE", "meteologix-bot")
WHATSAPP_GROUP_ID: str = os.environ["WHATSAPP_GROUP_ID"]
STORAGE_DIR: str = os.environ.get("STORAGE_DIR", "storage")
