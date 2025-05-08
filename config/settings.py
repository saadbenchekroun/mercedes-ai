"""
Global configuration settings for the Mercedes AI system.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# API Keys and Credentials
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "westeurope")

# Speech Recognition Settings
ASR_SAMPLE_RATE = 16000
ASR_CHANNELS = 4  # 4-mic array
ASR_CHUNK_SIZE = 1024
ASR_LANGUAGE = "en-US"

# NLU Settings
NLU_MODEL_PATH = MODELS_DIR / "nlu" / "model"
SPACY_MODEL = "en_core_web_lg"
INTENT_CONFIDENCE_THRESHOLD = 0.7

# Dialogue Settings
GPT_MODEL = "gpt-4"
MAX_CONVERSATION_TURNS = 10
CONTEXT_WINDOW_SIZE = 5

# TTS Settings
TTS_VOICE_NAME = "en-US-MercedesNeural"
TTS_SPEAKING_RATE = 1.0
TTS_PITCH = 0.0

# Vehicle Integration
CAN_BUS_INTERFACE = "can0"
MBUX_API_VERSION = "v1"
VEHICLE_UPDATE_INTERVAL = 0.1  # seconds

# Context Fusion
FLINK_JOB_NAME = "mercedes_context_fusion"
FLINK_PARALLELISM = 4
CONTEXT_UPDATE_INTERVAL = 0.5  # seconds

# Security
ENCRYPTION_KEY_SIZE = 32
SECURE_BOOT_ENABLED = True
PRIVACY_MODE_ENABLED = True

# Performance
TENSORRT_PRECISION = "FP16"
MAX_CONCURRENT_REQUESTS = 10
COMPUTE_ALLOCATION_TIMEOUT = 5.0  # seconds

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / "mercedes_ai.log"

# Testing
TEST_MODE = False
SIMULATION_MODE = False
HIL_TEST_ENABLED = False

# Deployment
OTA_UPDATE_CHECK_INTERVAL = 3600  # seconds
TELEMETRY_INTERVAL = 300  # seconds
AB_TESTING_ENABLED = True 