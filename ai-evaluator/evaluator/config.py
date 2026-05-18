from __future__ import annotations

import os


class Config:
    MODEL_DIR: str = os.getenv("MODEL_DIR", "/models")
    DATASET_DIR: str = os.getenv("DATASET_DIR", "/datasets")
    MIMO_API_URL: str = os.getenv("MIMO_API_URL", "http://localhost:8100/api/v1")
    DEVICE: str = os.getenv("DEVICE", "cpu")  # cpu / cuda / mps
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PORT: int = int(os.getenv("PORT", "8200"))


config = Config()
