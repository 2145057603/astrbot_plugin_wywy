# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class ScratchSymbol:
    char: str
    name: str
    weight: int
    match_3_mult: float
    match_2_mult: float


SCRATCH_SYMBOLS: List[ScratchSymbol] = [
    ScratchSymbol(char="💎", name="璀璨钻石", weight=10, match_3_mult=25.0, match_2_mult=2.0),
    ScratchSymbol(char="👑", name="黄金皇冠", weight=15, match_3_mult=15.0, match_2_mult=1.8),
    ScratchSymbol(char="💰", name="鼓鼓钱袋", weight=25, match_3_mult=8.0, match_2_mult=1.5),
    ScratchSymbol(char="7️⃣", name="幸运之七", weight=30, match_3_mult=5.0, match_2_mult=1.2),
    ScratchSymbol(char="🔔", name="黄金铃铛", weight=40, match_3_mult=3.5, match_2_mult=1.0),
    ScratchSymbol(char="🍒", name="新鲜樱桃", weight=55, match_3_mult=2.5, match_2_mult=0.8),
]


@dataclass
class ScratchTier:
    cost: int
    name: str
    desc: str
    max_reward: int


SCRATCH_TIERS: Dict[int, ScratchTier] = {
    20: ScratchTier(cost=20, name="新手刮刮乐", desc="低门槛保底体验，最高大奖 500 金币！", max_reward=500),
    50: ScratchTier(cost=50, name="暴富刮刮乐", desc="倍率均衡刺激推荐，最高大奖 1,250 金币！", max_reward=1250),
    200: ScratchTier(cost=200, name="至尊刮刮乐", desc="高风险巨额回报，最高大奖 5,000 金币！", max_reward=5000),
}
