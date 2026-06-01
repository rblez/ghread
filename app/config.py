import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    API_KEY: str = os.getenv("API_KEY", "")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
