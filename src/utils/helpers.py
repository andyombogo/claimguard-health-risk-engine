"""Common path and data loading helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config.settings import get_settings


def repo_root() -> Path:
    """Return the repository root path."""

    return get_settings().repo_root


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV file from disk."""

    resolved_path = Path(path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"CSV file was not found: {resolved_path}")
    return pd.read_csv(resolved_path)


def load_synthetic_claims() -> pd.DataFrame:
    """Load the synthetic health claims dataset used across the prototype."""

    try:
        return load_csv(get_settings().synthetic_claims_path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "Synthetic claims data is missing. Generate it from the repository root with "
            "`py -B src\\data_processing\\generate_synthetic_claims.py`."
        ) from exc


def load_processed_claims() -> pd.DataFrame:
    """Load the illustrative processed claims sample."""

    return load_csv(get_settings().processed_claims_path)
