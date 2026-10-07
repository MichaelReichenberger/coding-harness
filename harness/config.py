"""Vertrauenswürdige Einstellungen; das Modell kann sie nicht verändern.

Pydantic prüft Datentypen und Wertebereiche beim Laden. Tippfehler werden durch
extra='forbid' abgelehnt, statt unbemerkt die gewünschte Grenze zu ignorieren.
"""

from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

ROOT = Path(__file__).resolve().parents[1]


class StrictModel(BaseModel):
    """Gemeinsame Regeln: keine Zusatzfelder, keine stillen Typumwandlungen."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Limits(StrictModel):
    """Budgets eines Laufs, getrennt nach Aktionen, Zeit und Speicherverbrauch."""

    actions: int = Field(default=40, ge=1, le=200)
    rounds: int = Field(default=50, ge=1, le=200)
    retries: int = Field(default=2, ge=0, le=5)
    check_seconds: int = Field(default=120, ge=1, le=600)
    model_seconds: int = Field(default=180, ge=1, le=600)
    output_bytes: int = Field(default=65536, ge=1024, le=262144)
    file_bytes: int = Field(default=262144, ge=1024, le=1048576)
    context_bytes: int = Field(default=196608, ge=4096, le=1048576)
    artifact_bytes: int = Field(default=8388608, ge=1048576, le=33554432)


class Settings(StrictModel):
    """Lokaler Modellzugang, vorbereitetes Docker-Image und Laufgrenzen."""

    ollama_base_url: str = "http://127.0.0.1:11434"
    model: str = Field(default="qwen2.5-coder:7b", min_length=1, max_length=200)
    image: str = Field(
        default="docker.io/library/supermarket-harness:stage1",
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_./:@-]{0,200}$",
    )
    limits: Limits = Field(default_factory=Limits)

    @field_validator("ollama_base_url")
    @classmethod
    def valid_url(cls, value: str) -> str:
        parts = urlsplit(value)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError("Ollama benötigt eine HTTP(S)-Adresse")
        if parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError("Keine Zugangsdaten oder Query-Parameter in der Modelladresse")
        return value.rstrip("/")


class Target(StrictModel):
    """Fixierter öffentlicher Quellstand und erlaubte Dateien; enthält keine Lösung."""

    name: Literal["Supermarket Receipt"]
    url: Literal["https://github.com/emilybache/SupermarketReceipt-Refactoring-Kata"]
    subdirectory: Literal["python"]
    commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    editable: list[
        Literal[
            "shopping_cart.py",
            "teller.py",
            "receipt.py",
            "receipt_printer.py",
            "model_objects.py",
            "catalog.py",
        ]
    ] = Field(min_length=1)


def load_settings(path: Path | None = None) -> Settings:
    """Priorität: Umgebungsvariable > lokale TOML-Datei > Klassenstandard."""
    path = path or ROOT / "config.local.toml"
    data = tomllib.loads(path.read_text("utf-8")) if path.exists() else {}
    for env, key in [("HARNESS_OLLAMA_BASE_URL", "ollama_base_url"), ("HARNESS_MODEL", "model")]:
        if env in os.environ:
            data[key] = os.environ[env]
    return Settings.model_validate(data)


def load_target() -> Target:
    return Target.model_validate(json.loads((ROOT / "config/target.json").read_text("utf-8")))
