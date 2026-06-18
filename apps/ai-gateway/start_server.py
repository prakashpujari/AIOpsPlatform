#!/usr/bin/env python
"""Simple script to start the AI Gateway server for local testing."""

import os
import sys

# Ensure the src directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
    )