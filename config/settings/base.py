from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATABASE_URL: str = config("DATABASE_URL")

GROQ_API_KEY: str = config("GROQ_API_KEY", default="")
TAVILY_API_KEY: str = config("TAVILY_API_KEY", default="")

SECRET_KEY: str = config("SECRET_KEY", default="change-me")
DEBUG: bool = config("DEBUG", default=False, cast=bool)

UPLOAD_DIR: Path = BASE_DIR / config("UPLOAD_DIR", default="uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS: int = 384
CHUNK_SIZE: int = 500
CHUNK_OVERLAP: int = 50
MEMORY_TOP_K: int = 3
CRITIC_MAX_REVISIONS: int = 3
