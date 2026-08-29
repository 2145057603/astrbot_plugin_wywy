# -*- coding: utf-8 -*-
import os
import json
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_FILE = os.path.join(DATA_DIR, "storage.json")


@dataclass
class GroupSettings:
    """单个群聊的专属独立配置"""
    enabled: bool = True               # 本群娱乐插件总开关
    mode: str = "classic"             # 本群模式 (classic / talent)
    misfire_enabled: bool = False      # 本群是否开启被动走火
    min_ban: int = 60                  # 本群实弹最小禁言秒数
    max_ban: int = 180                 # 本群实弹最大禁言秒数
    items_enabled: bool = True         # 本群是否启用随机战术空投道具
    dodge_rate: float = 0.05           # 本群默认闪避率


class Database:
    """持久化数据存储管理器（群独立配置、金币、战绩等）"""
    _instance: Optional["Database"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._data: Dict[str, Any] = {
            "group_configs": {},     # group_id -> dict of GroupSettings
            "user_stats": {},        # user_id -> { shots, deaths, dodges, survives, coins, score }
        }
        self._ensure_dir()
        self._load()

    @classmethod
    def get_instance(cls) -> "Database":
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance

    def _ensure_dir(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)

    def _load(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    self._data.update(content)
            except Exception as e:
                print(f"[无欲物语] 读取数据文件失败: {e}")

    def _save(self):
        try:
            self._ensure_dir()
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[无欲物语] 保存数据文件失败: {e}")

    def get_group_settings(self, group_id: str, default_mode: str = "classic") -> GroupSettings:
        """获取群专属配置（若无则根据默认值生成）"""
        gid = str(group_id)
        if "group_configs" not in self._data:
            self._data["group_configs"] = {}
        
        cfg_dict = self._data["group_configs"].get(gid)
        if not cfg_dict:
            # 兼容旧字段
            old_mode = self._data.get("group_modes", {}).get(gid, default_mode)
            old_misfire = self._data.get("group_misfire", {}).get(gid, False)
            settings = GroupSettings(mode=old_mode, misfire_enabled=old_misfire)
            self._data["group_configs"][gid] = asdict(settings)
            self._save()
            return settings
        
        return GroupSettings(
            enabled=cfg_dict.get("enabled", True),
            mode=cfg_dict.get("mode", default_mode),
            misfire_enabled=cfg_dict.get("misfire_enabled", False),
            min_ban=int(cfg_dict.get("min_ban", 60)),
            max_ban=int(cfg_dict.get("max_ban", 180)),
            items_enabled=cfg_dict.get("items_enabled", True),
            dodge_rate=float(cfg_dict.get("dodge_rate", 0.05)),
        )

    def update_group_settings(self, group_id: str, **kwargs):
        """更新并保存群专属配置"""
        gid = str(group_id)
        current = self.get_group_settings(gid)
        d = asdict(current)
        for k, v in kwargs.items():
            if k in d and v is not None:
                d[k] = v
        
        if "group_configs" not in self._data:
            self._data["group_configs"] = {}
        self._data["group_configs"][gid] = d
        self._save()

    def get_group_mode(self, group_id: str, default: str = "classic") -> str:
        return self.get_group_settings(group_id, default).mode

    def set_group_mode(self, group_id: str, mode: str):
        self.update_group_settings(group_id, mode=mode)

    def get_group_misfire(self, group_id: str, default: bool = False) -> bool:
        return self.get_group_settings(group_id).misfire_enabled

    def set_group_misfire(self, group_id: str, enabled: bool):
        self.update_group_settings(group_id, misfire_enabled=enabled)

    def record_user_action(
        self,
        user_id: str,
        shot: bool = False,
        death: bool = False,
        dodge: bool = False,
        survive: bool = False,
        coins_delta: int = 0,
        score_delta: int = 0
    ):
        """记录用户轮盘战绩与经济"""
        uid = str(user_id)
        if "user_stats" not in self._data:
            self._data["user_stats"] = {}
        if uid not in self._data["user_stats"]:
            self._data["user_stats"][uid] = {
                "shots": 0,
                "deaths": 0,
                "dodges": 0,
                "survives": 0,
                "coins": 100,
                "score": 0
            }
        stat = self._data["user_stats"][uid]
        if shot:
            stat["shots"] += 1
        if death:
            stat["deaths"] += 1
        if dodge:
            stat["dodges"] += 1
        if survive:
            stat["survives"] += 1
        stat["coins"] = max(0, stat.get("coins", 0) + coins_delta)
        stat["score"] = stat.get("score", 0) + score_delta
        self._save()

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        uid = str(user_id)
        return self._data.get("user_stats", {}).get(uid, {
            "shots": 0,
            "deaths": 0,
            "dodges": 0,
            "survives": 0,
            "coins": 100,
            "score": 0
        })

