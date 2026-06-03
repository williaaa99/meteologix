import os

# Set required env vars at module level so they're available during test collection,
# before any production modules (config.py) are imported.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("EVOLUTION_API_KEY", "test-evo-key")
os.environ.setdefault("WHATSAPP_GROUP_ID", "test-group@g.us")
