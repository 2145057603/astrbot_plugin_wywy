# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PluginConfig:
    default_mode: str = "classic"  # classic or talent
    default_dodge_rate: float = 0.05
    timeout_seconds: int = 300
    item_trigger_rate: float = 0.15
    min_ban_seconds: int = 60
    max_ban_seconds: int = 180
    enable_misfire: bool = False
    misfire_probability: float = 0.003

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginConfig":
        return cls(
            default_mode=data.get("default_mode", "classic"),
            default_dodge_rate=float(data.get("default_dodge_rate", 0.05)),
            timeout_seconds=int(data.get("timeout_seconds", 300)),
            item_trigger_rate=float(data.get("item_trigger_rate", 0.15)),
            min_ban_seconds=int(data.get("min_ban_seconds", 60)),
            max_ban_seconds=int(data.get("max_ban_seconds", 180)),
            enable_misfire=bool(data.get("enable_misfire", False)),
            misfire_probability=float(data.get("misfire_probability", 0.003)),
        )
