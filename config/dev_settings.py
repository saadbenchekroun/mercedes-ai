"""
Development-specific settings that override the main settings.
"""
from .settings import *

# Debug mode
DEBUG = True
TEST_MODE = True

# Use mock services in development
USE_MOCK_SERVICES = True

# Development API endpoints
DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"
OPENAI_API_URL = "https://api.openai.com/v1"
AZURE_SPEECH_ENDPOINT = "https://westeurope.stt.speech.microsoft.com/speech/universal/v2"

# Development credentials (should be loaded from environment in production)
DEEPGRAM_API_KEY = "dev_key"
OPENAI_API_KEY = "dev_key"
AZURE_SPEECH_KEY = "dev_key"

# Reduced performance settings for development
MAX_CONCURRENT_REQUESTS = 5
COMPUTE_ALLOCATION_TIMEOUT = 2.0

# Development logging
LOG_LEVEL = "DEBUG"
LOG_FILE = LOGS_DIR / "mercedes_ai_dev.log"

# Development testing
SIMULATION_MODE = True
HIL_TEST_ENABLED = False

# Development deployment
OTA_UPDATE_CHECK_INTERVAL = 60  # Check more frequently in development
TELEMETRY_INTERVAL = 60
AB_TESTING_ENABLED = False

# Development security
SECURE_BOOT_ENABLED = False
PRIVACY_MODE_ENABLED = False 