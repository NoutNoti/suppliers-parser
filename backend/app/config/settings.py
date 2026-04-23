import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/supply_parser",
    )
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/supply_parser",
    )

    # Supplier credentials
    SUPPLIER_EMAIL: str = os.getenv("SUPPLIER_EMAIL", "")
    SUPPLIER_PASSWORD: str = os.getenv("SUPPLIER_PASSWORD", "")
    SUPPLIER_MELAD_PASSWORD: str = os.getenv("SUPPLIER_MELAD_PASSWORD", "")
    SUPPLIER_JUMPEX_PASSWORD: str = os.getenv("SUPPLIER_JUMPEX_PASSWORD", "")
    SUPPLIER_SPARTAK_LOGIN: str = os.getenv("SUPPLIER_SPARTAK_LOGIN", "")

    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


settings = Settings()
