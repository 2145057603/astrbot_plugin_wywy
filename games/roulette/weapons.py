# -*- coding: utf-8 -*-
from dataclasses import dataclass
from .models import WeaponType


@dataclass
class WeaponSpec:
    type: WeaponType
    name: str
    icon: str
    max_chambers: int
    default_min_bullets: int
    default_max_bullets: int
    burst_count: int  # 每次开枪扣动几发
    ban_multiplier: float
    pierce_chance: float  # 穿透下一位概率（大狙）
    aoe_splash_chance: float  # AOE波及概率（火箭筒）
    description: str


WEAPON_SPECS = {
    WeaponType.REVOLVER: WeaponSpec(
        type=WeaponType.REVOLVER,
        name="经典左轮",
        icon="🔫",
        max_chambers=6,
        default_min_bullets=1,
        default_max_bullets=3,
        burst_count=1,
        ban_multiplier=1.0,
        pierce_chance=0.0,
        aoe_splash_chance=0.0,
        description="标准6孔弹巢决斗，单发判定，经典心跳博弈。"
    ),
    WeaponType.SNIPER: WeaponSpec(
        type=WeaponType.SNIPER,
        name="巴雷特大狙",
        icon="🎯",
        max_chambers=4,
        default_min_bullets=1,
        default_max_bullets=2,
        burst_count=1,
        ban_multiplier=2.0,
        pierce_chance=0.35,
        aoe_splash_chance=0.0,
        description="威力极大！禁言时间翻倍，命中时有35%几率触发【穿透】，连带下一位倒霉蛋一起升天！"
    ),
    WeaponType.GATLING: WeaponSpec(
        type=WeaponType.GATLING,
        name="加特林机枪",
        icon="🔥",
        max_chambers=15,
        default_min_bullets=3,
        default_max_bullets=6,
        burst_count=3,
        ban_multiplier=0.8,
        pierce_chance=0.0,
        aoe_splash_chance=0.0,
        description="一息三千六百转！每次开火直接【疯狂3连射】，实弹中弹禁言时间可叠加，极致疯狂！"
    ),
    WeaponType.RPG: WeaponSpec(
        type=WeaponType.RPG,
        name="RPG火箭筒",
        icon="🚀",
        max_chambers=3,
        default_min_bullets=1,
        default_max_bullets=1,
        burst_count=1,
        ban_multiplier=1.5,
        pierce_chance=0.0,
        aoe_splash_chance=0.80,
        description="艺术就是爆炸！命中时本人倒地，并有80%几率产生【AOE冲击波】，拉上群内幸运儿同归于尽！"
    )
}


def get_weapon_spec(weapon_input: str) -> WeaponSpec:
    """根据用户输入识别武器，默认返回左轮"""
    text = (weapon_input or "").strip().lower()
    if any(k in text for k in ["狙", "巴雷特", "sniper"]):
        return WEAPON_SPECS[WeaponType.SNIPER]
    if any(k in text for k in ["加特林", "机枪", "gatling"]):
        return WEAPON_SPECS[WeaponType.GATLING]
    if any(k in text for k in ["火箭筒", "rpg", "筒子"]):
        return WEAPON_SPECS[WeaponType.RPG]
    return WEAPON_SPECS[WeaponType.REVOLVER]
