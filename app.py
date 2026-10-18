from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def convert_value(key, value):
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        return str(value).lower() in ("true", "1", "yes", "on")

    return str(value)


def apply_layer(config, layer):
    for key, value in layer.items():
        if value is None:
            continue

        key = str(key).lower()

        if key == "num_workers":
            key = "workers"
        elif key.startswith("app_"):
            key = key[4:]

        config[key] = convert_value(key, value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    # Layer 2: environment-specific YAML
    environment = os.getenv("APP_ENV", "development")
    yaml_file = Path(f"config.{environment}.yaml")

    if yaml_file.exists():
        with yaml_file.open() as file:
            yaml_config = yaml.safe_load(file) or {}
        apply_layer(config, yaml_config)

    # Layer 3: .env file
    apply_layer(config, dotenv_values(".env"))

    # Layer 4: operating-system environment variables
    os_config = {
        key: value
        for key, value in os.environ.items()
        if key.startswith("APP_")
    }
    apply_layer(config, os_config)

    # Layer 5: query-string overrides
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        key = key.lower()

        if key == "num_workers":
            key = "workers"
        elif key.startswith("app_"):
            key = key[4:]

        config[key] = convert_value(key, value)

    # Never expose the actual secret
    config["api_key"] = "****"

    return config
