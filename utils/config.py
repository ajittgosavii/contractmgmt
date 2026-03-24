"""Centralized configuration for Smart Contracts Management."""

import os
from openai import OpenAI

OPENAI_MODEL = "gpt-4o"
OPENAI_MODEL_FAST = "gpt-4o-mini"

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "contracts.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

RISK_THRESHOLDS = {"critical": 80, "high": 60, "medium": 40, "low": 20}

CONTRACT_TYPES = [
    "NDA (Non-Disclosure Agreement)",
    "MSA (Master Service Agreement)",
    "SOW (Statement of Work)",
    "Employment Agreement",
    "Vendor Agreement",
    "Lease Agreement",
    "Custom",
]

CONTRACT_STATUSES = ["Draft", "Under Review", "Active", "Expired", "Terminated"]


def get_openai_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)
