import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL


load_dotenv(Path(__file__).with_name(".env"))


def _required_environment_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name}. "
            "Set it in backend/.env or in the process environment."
        )
    return value


class Config:
    SECRET_KEY = _required_environment_value("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or SECRET_KEY
    if len(SECRET_KEY.encode("utf-8")) < 32:
        raise RuntimeError("SECRET_KEY must contain at least 32 bytes.")
    if len(JWT_SECRET_KEY.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 bytes.")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "900"))
    )
    JWT_ALGORITHM = "HS256"
    JWT_DECODE_ALGORITHMS = ["HS256"]
    JWT_TOKEN_LOCATION = ["headers"]
    SQLALCHEMY_DATABASE_URI = URL.create(
        drivername="mysql+pymysql",
        username=_required_environment_value("DB_USER"),
        password=os.getenv("DB_PASSWORD", ""),
        host=_required_environment_value("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=_required_environment_value("DB_NAME"),
        query={"charset": "utf8mb4"},
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]
    APP_ENV = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "development")).lower()
    if APP_ENV == "production" and "*" in CORS_ORIGINS:
        raise RuntimeError("Wildcard CORS origins are not allowed in production.")
