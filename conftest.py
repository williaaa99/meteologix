import os

# Set required env vars before any module is imported during test collection.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("EVOLUTION_API_KEY", "test-evo-key")
os.environ.setdefault("WHATSAPP_GROUP_ID", "test-group@g.us")
