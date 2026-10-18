import os
from pathlib import Path
from typing import Optional
import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
DEFAULTS = {"port": 8000, "workers": 1, "debug": False, "log_level": "info", "api_key": "default-secret-000"}

app = FastAPI(title="12-Factor Config Precedence API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

def coerce(key, value):
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "on"}
    return str(value)

def normalize_key(key) -> Optional[str]:
    key = key.strip().lower()
    aliases = {"app_port":"port", "app_workers":"workers", "num_workers":"workers",
               "app_debug":"debug", "app_log_level":"log_level", "app_api_key":"api_key"}
    return key if key in DEFAULTS else aliases.get(key)

def effective_config(overrides):
    config = dict(DEFAULTS)

    app_env = os.getenv("APP_ENV", "development").strip() or "development"
    yaml_path = BASE_DIR / f"config.{app_env}.yaml"
    if yaml_path.exists():
        with yaml_path.open(encoding="utf-8") as f:
            values = yaml.safe_load(f) or {}
        for key, value in values.items():
            normalized = normalize_key(key)
            if normalized:
                config[normalized] = coerce(normalized, value)

    env_path = BASE_DIR / ".env"
    file_values = dotenv_values(env_path) if env_path.exists() else {}
    for key, value in file_values.items():
        normalized = normalize_key(key)
        if normalized and value is not None:
            config[normalized] = coerce(normalized, value)

    os_names = {"APP_PORT":"port", "APP_WORKERS":"workers", "APP_DEBUG":"debug",
                "APP_LOG_LEVEL":"log_level", "APP_API_KEY":"api_key"}
    for env_name, normalized in os_names.items():
        if env_name in os.environ:
            config[normalized] = coerce(normalized, os.environ[env_name])

    for item in overrides:
        if "=" not in item:
            continue
        raw_key, raw_value = item.split("=", 1)
        normalized = normalize_key(raw_key)
        if normalized:
            config[normalized] = coerce(normalized, raw_value)

    config["api_key"] = "****"
    return {"port": int(config["port"]), "workers": int(config["workers"]),
            "debug": bool(config["debug"]), "log_level": str(config["log_level"]),
            "api_key": "****"}

@app.get("/")
def health():
    return {"status":"ok", "service":"config-precedence-api"}

@app.get("/effective-config")
def get_effective_config(set: list[str] = Query(default=[])):
    return effective_config(set)
