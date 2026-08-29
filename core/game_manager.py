# -*- coding: utf-8 -*-
import asyncio
from typing import Any, Dict, Optional, Callable, Awaitable



class GameManager:
    """管理所有群正在进行的对局实例与超时回收"""
    _instance: Optional["GameManager"] = None

    def __init__(self):
        self._active_games: Dict[str, Any] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._timeout_tasks: Dict[str, asyncio.Task] = {}

    @classmethod
    def get_instance(cls) -> "GameManager":
        if cls._instance is None:
            cls._instance = GameManager()
        return cls._instance

    def get_lock(self, group_id: str) -> asyncio.Lock:
        gid = str(group_id)
        if gid not in self._locks:
            self._locks[gid] = asyncio.Lock()
        return self._locks[gid]

    def get_game(self, group_id: str) -> Optional[Any]:
        return self._active_games.get(str(group_id))

    def set_game(self, group_id: str, game_instance: Any):
        self._active_games[str(group_id)] = game_instance

    def remove_game(self, group_id: str):
        gid = str(group_id)
        if gid in self._active_games:
            del self._active_games[gid]
        self.cancel_timeout(gid)

    def schedule_timeout(
        self,
        group_id: str,
        timeout_seconds: int,
        callback: Callable[[str], Awaitable[None]]
    ):
        """设定超时自动清理任务"""
        gid = str(group_id)
        self.cancel_timeout(gid)

        async def _timeout_coro():
            try:
                await asyncio.sleep(timeout_seconds)
                await callback(gid)
            except asyncio.CancelledError:
                pass

        self._timeout_tasks[gid] = asyncio.create_task(_timeout_coro())

    def cancel_timeout(self, group_id: str):
        gid = str(group_id)
        if gid in self._timeout_tasks:
            task = self._timeout_tasks.pop(gid)
            if not task.done():
                task.cancel()
