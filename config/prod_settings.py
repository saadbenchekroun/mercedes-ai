"""
Production-specific settings that override the main settings.
"""
from .settings import *

# Production mode
DEBUG = False
TEST_MODE = False

# Production API endpoints
DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"
OPENAI_API_URL = "https://api.openai.com/v1"
AZURE_SPEECH_ENDPOINT = "https://westeurope.stt.speech.microsoft.com/speech/universal/v2"

# Production credentials must be set via environment variables
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")

if not all([DEEPGRAM_API_KEY, OPENAI_API_KEY, AZURE_SPEECH_KEY]):
    raise ValueError("Production API keys must be set via environment variables")

# Production performance settings
MAX_CONCURRENT_REQUESTS = 20
COMPUTE_ALLOCATION_TIMEOUT = 10.0

# Production logging
LOG_LEVEL = "INFO"
LOG_FILE = LOGS_DIR / "mercedes_ai_prod.log"

# Production testing
SIMULATION_MODE = False
HIL_TEST_ENABLED = True

# Production deployment
OTA_UPDATE_CHECK_INTERVAL = 3600  # Check less frequently in production
TELEMETRY_INTERVAL = 300
AB_TESTING_ENABLED = True

# Production security
SECURE_BOOT_ENABLED = True
PRIVACY_MODE_ENABLED = True

# Production error handling
RAISE_ON_ERROR = True
ERROR_NOTIFICATION_EMAIL = "ai-systems-alerts@mercedes-benz.com"

# Production monitoring
ENABLE_METRICS = True
METRICS_INTERVAL = 60  # seconds
ENABLE_ALERTING = True
ALERT_THRESHOLD = 0.95  # 95% error rate threshold 