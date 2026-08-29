# -*- coding: utf-8 -*-
import random
from typing import Optional, Tuple
from .models import TacticalItemType, StickyBombState


class TacticalItemManager:
    """突发战场道具空投管理器"""

    @staticmethod
    def roll_airdrop(trigger_rate: float = 0.15) -> Optional[TacticalItemType]:
        """判定本次开火后是否触发机器人空投突发道具"""
        if random.random() < trigger_rate:
            return random.choice([
                TacticalItemType.STICKY_BOMB,
                TacticalItemType.SMOKE_GRENADE,
                TacticalItemType.FLASHBANG
            ])
        return None

    @staticmethod
    def init_sticky_bomb(holder_id: str, holder_name: str) -> StickyBombState:
        """初始化一枚粘性炸弹（可传递 2~4 次后爆炸）"""
        fuse = random.randint(2, 4)
        return StickyBombState(
            holder_id=str(holder_id),
            holder_name=holder_name,
            fuse_remaining=fuse
        )
