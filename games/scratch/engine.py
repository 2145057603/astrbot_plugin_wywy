# -*- coding: utf-8 -*-
import random
from collections import Counter
from typing import Tuple, List, Optional
from dataclasses import dataclass

from .config import SCRATCH_SYMBOLS, SCRATCH_TIERS, ScratchTier, ScratchSymbol

try:
    from ...core.database import Database
except (ImportError, ValueError):
    from core.database import Database


@dataclass
class ScratchResult:
    user_id: str
    user_name: str
    tier: ScratchTier
    symbols: List[ScratchSymbol]
    reward: int
    profit: int
    is_win: bool
    win_desc: str
    is_gift: bool = False
    gifter_name: Optional[str] = None


class ScratchEngine:
    """刮刮乐核心业务引擎"""

    @classmethod
    def roll_symbols(cls) -> List[ScratchSymbol]:
        weights = [s.weight for s in SCRATCH_SYMBOLS]
        return random.choices(SCRATCH_SYMBOLS, weights=weights, k=3)

    @classmethod
    def calculate_reward(cls, symbols: List[ScratchSymbol], cost: int) -> Tuple[int, str]:
        chars = [s.char for s in symbols]
        counts = Counter(chars)

        for s in SCRATCH_SYMBOLS:
            c = counts.get(s.char, 0)
            if c == 3:
                reward = int(cost * s.match_3_mult)
                return reward, f"🎉 哇塞！【3连{s.name}】大爆发！获得 {s.match_3_mult:g} 倍超级巨奖！"
            elif c == 2:
                reward = int(cost * s.match_2_mult)
                return reward, f"✨ 恭喜！开出【双连{s.name}】！获得 {s.match_2_mult:g} 倍奖金！"

        return 0, "💔 差一点就中奖了！谢谢惠顾，下一次大奖就是你！"

    @classmethod
    def play(
        cls,
        user_id: str,
        user_name: str,
        cost: int = 50,
        is_gift: bool = False,
        gifter_name: Optional[str] = None
    ) -> Tuple[bool, Optional[ScratchResult], str]:
        uid = str(user_id)
        tier = SCRATCH_TIERS.get(cost, SCRATCH_TIERS[50])

        db = Database.get_instance()
        stats = db.get_user_stats(uid)
        user_coins = stats.get("coins", 0)

        if not is_gift and user_coins < tier.cost:
            return False, None, f"⚠️ 金币不足！购买一张【{tier.name}】需要 {tier.cost} 金币，你当前随身只有 {user_coins} 金币！"

        symbols = cls.roll_symbols()
        reward, desc = cls.calculate_reward(symbols, tier.cost)
        profit = reward if is_gift else (reward - tier.cost)

        db.record_user_action(uid, nickname=user_name, coins_delta=profit, score_delta=max(0, profit // 5))

        res = ScratchResult(
            user_id=uid,
            user_name=user_name,
            tier=tier,
            symbols=symbols,
            reward=reward,
            profit=profit,
            is_win=(reward > 0),
            win_desc=desc,
            is_gift=is_gift,
            gifter_name=gifter_name
        )

        card_text = cls.render_card_text(res)
        return True, res, card_text

    @classmethod
    def render_card_text(cls, res: ScratchResult) -> str:
        s0, s1, s2 = res.symbols[0].char, res.symbols[1].char, res.symbols[2].char

        gift_header = f"🎁 管理员【{res.gifter_name}】赠予专属福利！\n" if res.is_gift else ""
        cost_str = "【免费赠送】" if res.is_gift else f"{res.tier.cost} 金币"

        profit_str = f"+{res.profit} 金币" if res.profit >= 0 else f"{res.profit} 金币"

        text = (
            f"🎟️ 〓 无欲物语 · {res.tier.name} 〓\n"
            f"{gift_header}"
            f"━━━━━━━━━━━━━━━━━\n"
            f"👤 刮奖人：【{res.user_name}】\n"
            f"💰 彩票面额：{cost_str}\n"
            f"─────────────────\n"
            f"【刮开涂层】\n"
            f"  ┏━━━━━┳━━━━━┳━━━━━┓\n"
            f"  ┃  {s0}  ┃  {s1}  ┃  {s2}  ┃\n"
            f"  ┗━━━━━┻━━━━━┻━━━━━┛\n"
            f"─────────────────\n"
            f"{res.win_desc}\n"
            f"💰 获得奖金：{res.reward} 金币\n"
            f"✨ 净收益：{profit_str}\n"
            f"━━━━━━━━━━━━━━━━━"
        )
        return text
