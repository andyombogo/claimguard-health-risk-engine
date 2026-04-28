"""Project settings and rule configuration models."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, model_validator

load_dotenv()


class ProjectMetadata(BaseModel):
    """Basic metadata for the current prototype configuration."""

    name: str = Field(min_length=3)
    version: str = Field(min_length=1)
    description: str = Field(min_length=10)


class ScoringConfig(BaseModel):
    """Score boundaries for the additive rule engine."""

    min_score: int = Field(default=0, ge=0, le=100)
    max_score: int = Field(default=100, ge=0, le=100)

    @model_validator(mode="after")
    def validate_range(self) -> "ScoringConfig":
        if self.min_score > self.max_score:
            raise ValueError("min_score cannot be greater than max_score")
        return self


class RiskBand(BaseModel):
    """Human-readable score bucket."""

    min_score: int = Field(ge=0, le=100)
    max_score: int = Field(ge=0, le=100)
    description: str = Field(min_length=5)

    @model_validator(mode="after")
    def validate_range(self) -> "RiskBand":
        if self.min_score > self.max_score:
            raise ValueError("Risk band minimum cannot exceed the maximum")
        return self


class RiskRule(BaseModel):
    """Single explainable rule definition."""

    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = True
    weight: int = Field(alias="points", ge=0, le=100)
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    description: str = Field(alias="short_description", min_length=10)
    parameters: dict[str, Any] = Field(default_factory=dict)

    @property
    def points(self) -> int:
        """Expose the configured rule points using the task-friendly name."""

        return self.weight

    @property
    def short_description(self) -> str:
        """Expose the configured description using the task-friendly name."""

        return self.description


class RiskRulesConfig(BaseModel):
    """Root configuration model for the YAML rule pack."""

    model_config = ConfigDict(extra="forbid")

    metadata: ProjectMetadata
    scoring: ScoringConfig
    risk_bands: dict[str, RiskBand]
    rules: dict[str, RiskRule]


class AppSettings(BaseModel):
    """Resolved repository paths and lightweight runtime settings."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    project_name: str = "ClaimGuard Health Risk Engine"
    repo_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "data"
    )
    docs_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "docs"
    )
    synthetic_claims_path: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
        / "data"
        / "synthetic"
        / "synthetic_health_claims.csv"
    )
    processed_claims_path: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
        / "data"
        / "processed"
        / "sample_scored_claims.csv"
    )
    risk_rules_path: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
        / "src"
        / "config"
        / "risk_rules.yaml"
    )
    default_maker: str = Field(
        default_factory=lambda: os.getenv("CLAIMGUARD_DEFAULT_MAKER", "claims_officer")
    )
    default_checker: str = Field(
        default_factory=lambda: os.getenv(
            "CLAIMGUARD_DEFAULT_CHECKER",
            "senior_reviewer",
        )
    )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached application settings."""

    return AppSettings()


@lru_cache(maxsize=4)
def load_risk_rules_config(path: str | Path | None = None) -> RiskRulesConfig:
    """Load and validate the risk rule configuration."""

    target_path = Path(path) if path else get_settings().risk_rules_path
    with target_path.open("r", encoding="utf-8") as file_handle:
        raw_config = yaml.safe_load(file_handle) or {}

    return RiskRulesConfig.model_validate(raw_config)
