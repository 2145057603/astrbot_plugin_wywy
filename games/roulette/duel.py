# -*- coding: utf-8 -*-
import time
import random
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List

from .models import ShootTarget, GameMode, ShootResult, WeaponType
from .weapons import WeaponSpec, WEAPON_SPECS, get_weapon_spec
from .engine import RouletteSession
from .texts import RouletteTexts

try:
    from ...core.config import PluginConfig
    from ...core.database import Database
except (ImportError, ValueError):
    from core.config import PluginConfig
    from core.database import Database


@dataclass
class DuelInvitation:
    group_id: str
    challenger_id: str
    challenger_name: str
    target_id: str
    target_name: str
    weapon_spec: WeaponSpec
    expire_at: float


class DuelSession:
    """1v1 专属定向生死决斗会话"""

    def __init__(
        self,
        group_id: str,
        challenger_id: str,
        challenger_name: str,
        target_id: str,
        target_name: str,
        weapon_spec: WeaponSpec,
        config: PluginConfig
    ):
        self.group_id = str(group_id)
        self.p1 = (str(challenger_id), challenger_name)
        self.p2 = (str(target_id), target_name)
        self.current_turn = str(challenger_id)
        self.weapon_spec = weapon_spec
        self.config = config

        bullet_count = random.randint(weapon_spec.default_min_bullets, weapon_spec.default_max_bullets)
        g_cfg = Database.get_instance().get_group_settings(group_id, config.default_mode)
        mode = GameMode.TALENT if g_cfg.mode == "talent" else GameMode.CLASSIC

        self.roulette = RouletteSession(
            group_id=group_id,
            loader_id=challenger_id,
            loader_name=challenger_name,
            weapon_spec=weapon_spec,
            bullet_count=bullet_count,
            mode=mode,
            config=config
        )
        self.roulette.register_player(target_id, target_name)
        self.winner: Optional[Tuple[str, str]] = None
        self.loser: Optional[Tuple[str, str]] = None
        self.game_over = False

    def is_participant(self, user_id: str) -> bool:
        uid = str(user_id)
        return uid in [self.p1[0], self.p2[0]]

    def get_opponent(self, user_id: str) -> Tuple[str, str]:
        uid = str(user_id)
        return self.p2 if uid == self.p1[0] else self.p1

    def execute_turn(
        self,
        user_id: str,
        user_name: str,
        is_admin: bool,
        target_type: ShootTarget
    ) -> Tuple[bool, Optional[ShootResult], str]:
        uid = str(user_id)
        if not self.is_participant(uid):
            return False, None, "⚠️ 本场为 1v1 专属生死决斗，闲杂人等请勿插手！"

        if self.current_turn != uid:
            curr_name = self.p1[1] if self.current_turn == self.p1[0] else self.p2[1]
            return False, None, f"⚠️ 还没轮到你！当前是【{curr_name}】的行动回合！"

        opp_id, opp_name = self.get_opponent(uid)

        result = self.roulette.execute_shoot(
            user_id=uid,
            user_name=user_name,
            is_admin=is_admin,
            target_type=target_type,
            target_user_id=opp_id,
            target_user_name=opp_name
        )

        dead_effects = [e for e in result.effects if e.is_dead]
        if dead_effects:
            self.game_over = True
            dead_user_id = dead_effects[0].target_id
            if dead_user_id == uid:
                self.loser = (uid, user_name)
                self.winner = (opp_id, opp_name)
            else:
                self.loser = (opp_id, opp_name)
                self.winner = (uid, user_name)

            Database.get_instance().record_user_action(
                self.winner[0], nickname=self.winner[1], duel_win=True, coins_delta=100, score_delta=30
            )
            Database.get_instance().record_user_action(
                self.loser[0], nickname=self.loser[1], duel_loss=True, coins_delta=-50, score_delta=-10
            )

            win_text = (
                f"\n\n👑 〓 决斗落幕 · 胜负已分 〓\n"
                f"🏆 胜者：【{self.winner[1]}】（+100 金币 / +30 积分 / 战神榜+1胜）\n"
                f"💀 败者：【{self.loser[1]}】（倒地送入ICU小黑屋）"
            )
            result.narratives.append(win_text)

        elif result.extra_turn:
            pass
        else:
            self.current_turn = opp_id

        if result.game_over:
            self.game_over = True

        return True, result, ""


class DuelManager:
    """1v1 决斗管理器（邀请池与会话管理）"""
    _instance: Optional["DuelManager"] = None

    def __init__(self):
        self.invitations: Dict[str, DuelInvitation] = {}
        self.active_duels: Dict[str, DuelSession] = {}

    @classmethod
    def get_instance(cls) -> "DuelManager":
        if cls._instance is None:
            cls._instance = DuelManager()
        return cls._instance

    def create_invitation(
        self,
        group_id: str,
        challenger_id: str,
        challenger_name: str,
        target_id: str,
        target_name: str,
        weapon_spec: WeaponSpec
    ) -> DuelInvitation:
        inv = DuelInvitation(
            group_id=str(group_id),
            challenger_id=str(challenger_id),
            challenger_name=challenger_name,
            target_id=str(target_id),
            target_name=target_name,
            weapon_spec=weapon_spec,
            expire_at=time.time() + 60
        )
        self.invitations[str(group_id)] = inv
        return inv

    def get_invitation(self, group_id: str) -> Optional[DuelInvitation]:
        inv = self.invitations.get(str(group_id))
        if inv and time.time() > inv.expire_at:
            del self.invitations[str(group_id)]
            return None
        return inv

    def remove_invitation(self, group_id: str):
        self.invitations.pop(str(group_id), None)

    def start_duel(self, inv: DuelInvitation, config: PluginConfig) -> DuelSession:
        session = DuelSession(
            group_id=inv.group_id,
            challenger_id=inv.challenger_id,
            challenger_name=inv.challenger_name,
            target_id=inv.target_id,
            target_name=inv.target_name,
            weapon_spec=inv.weapon_spec,
            config=config
        )
        self.active_duels[inv.group_id] = session
        self.remove_invitation(inv.group_id)
        return session

    def get_duel(self, group_id: str) -> Optional[DuelSession]:
        return self.active_duels.get(str(group_id))

    def remove_duel(self, group_id: str):
        self.active_duels.pop(str(group_id), None)

