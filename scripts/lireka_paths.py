"""Chemins du repo Lireka — override entrepôt via LIREKA_DWH."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def datawarehouse_root() -> Path:
    return Path(os.environ.get("LIREKA_DWH", REPO_ROOT / "Power_BI_Datawarehouse"))


def backend_root() -> Path:
    return datawarehouse_root() / "Données_Backend"


def transport_dashboards_root() -> Path:
    return datawarehouse_root() / "Dashboards_transporteurs"
