# -*- coding: utf-8 -*-
import os
import json
import asyncio
from typing import Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_FILE = os.path.join(DATA_DIR, "storage.json")


class Database:
    """持久化数据存储管理器（群模式、金币、战绩等）"""
    _instance: Optional["Database"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._data: Dict[str, Any] = {
            "group_modes": {},       # group_id -> "classic" | "talent"
            "group_misfire": {},     # group_id -> bool
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

    def get_group_mode(self, group_id: str, default: str = "classic") -> str:
        """获取群轮盘模式（classic/talent）"""
        return self._data.get("group_modes", {}).get(str(group_id), default)

    def set_group_mode(self, group_id: str, mode: str):
        """设置并持久化群轮盘模式"""
        if "group_modes" not in self._data:
            self._data["group_modes"] = {}
        self._data["group_modes"][str(group_id)] = mode
        self._save()

    def get_group_misfire(self, group_id: str, default: bool = False) -> bool:
        return self._data.get("group_misfire", {}).get(str(group_id), default)

    def set_group_misfire(self, group_id: str, enabled: bool):
        if "group_misfire" not in self._data:
            self._data["group_misfire"] = {}
        self._data["group_misfire"][str(group_id)] = enabled
        self._save()

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
