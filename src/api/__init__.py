from __future__ import annotations

from fastapi import FastAPI

from src.api.main import create_app

__all__ = ["create_app", "FastAPI"]
