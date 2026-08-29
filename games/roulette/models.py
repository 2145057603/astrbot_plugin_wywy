# -*- coding: utf-8 -*-
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


class WeaponType(str, Enum):
    REVOLVER = "左轮"
    SNIPER = "大狙"
    GATLING = "加特林"
    RPG = "火箭筒"


class GameMode(str, Enum):
    CLASSIC = "classic"  # 经典/普通模式（默认5%命运闪避）
    TALENT = "talent"    # 能力大乱斗模式（命格抽取）


class TacticalItemType(str, Enum):
    STICKY_BOMB = "粘性炸弹"
    SMOKE_GRENADE = "战术烟雾弹"
    FLASHBANG = "强光闪光弹"


@dataclass
class Talent:
    id: str
    name: str
    description: str
    tag: str  # 神技 / 搞怪 / 恶搞 / 经济 / 负面
    rarity: str  # SSR / SR / R / N
    dodge_bonus: float = 0.0
    ban_reduction: float = 0.0
    parry_chance: float = 0.0
    transfer_chance: float = 0.0
    suicide_aoe: bool = False
    xray: bool = False
    bluff: bool = False
    double_shot_chance: float = 0.0
    coin_multiplier: float = 1.0
    extortion: bool = False
    hp_lock: bool = False


@dataclass
class StickyBombState:
    """粘性炸弹状态"""
    holder_id: str
    holder_name: str
    fuse_remaining: int  # 剩余可传递次数，到达0引爆


@dataclass
class ShootEffectResult:
    """开枪判定产生的影响"""
    target_id: str
    target_name: str
    is_admin: bool = False
    ban_seconds: int = 0
    is_dead: bool = False
    is_dodged: bool = False
    is_parried: bool = False
    is_transferred: bool = False
    is_blown_up: bool = False
    reason: str = ""


@dataclass
class ShootResult:
    """整轮开枪的总结果"""
    user_id: str
    user_name: str
    weapon_type: WeaponType
    shots_fired: int
    live_hits: int
    blanks_fired: int
    game_over: bool
    remaining_bullets: int
    remaining_chambers: int
    effects: List[ShootEffectResult] = field(default_factory=list)
    narratives: List[str] = field(default_factory=list)
    tactical_item_event: Optional[str] = None
    next_bullet_peek: Optional[bool] = None  # 透视能力返回
