#!/usr/bin/env python
"""Run the AI Gateway server with cloud providers always healthy."""

import os
import sys

# Suppress TF warnings
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Patch the health monitor before importing the app
from src.registry.schemas import ModelProvider, ModelStatus
from src import registry as registry_module
from src.health.health_monitor import health_monitor

# Pre-seed cloud providers as healthy
for model in registry_module.registry.all_models():
    if model.provider == ModelProvider.GROQ:
        health_monitor._health[model.id] = ModelStatus.HEALTHY

# Now import and run the app
from src.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
    )