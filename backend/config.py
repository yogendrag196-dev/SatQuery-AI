import os

def load_env_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()

# Load backend/.env if present
base_dir = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(base_dir, '.env')
load_env_file(env_file)

class Config:
    PORT = int(os.environ.get("PORT", 5000))
    HOST = os.environ.get("HOST", "0.0.0.0")
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    
    # Gemini API Key
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    
    # Base directories
    BASE_DIR = base_dir
    DATA_DIR = os.path.join(BASE_DIR, "data")
    SAMPLE_IMAGERY_DIR = os.path.join(DATA_DIR, "sample_imagery")
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    
    # Model Cache
    MODEL_CACHE_DIR = os.path.join(BASE_DIR, "model_cache")

os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.MODEL_CACHE_DIR, exist_ok=True)
