# -*- coding: utf-8 -*-
import random
import time
from typing import List, Dict, Optional, Tuple, Set

from .models import (
    WeaponType,
    GameMode,
    TacticalItemType,
    Talent,
    StickyBombState,
    ShootResult,
    ShootEffectResult,
)
from .weapons import WeaponSpec, get_weapon_spec
from .talents import draw_random_talent
from .items import TacticalItemManager
from .texts import RouletteTexts

try:
    from ...core.config import PluginConfig
    from ...core.database import Database
except (ImportError, ValueError):
    from core.config import PluginConfig
    from core.database import Database



class RouletteSession:
    """单个群聊的轮盘赌游戏会话"""

    def __init__(
        self,
        group_id: str,
        loader_id: str,
        loader_name: str,
        weapon_spec: WeaponSpec,
        bullet_count: int,
        mode: GameMode,
        config: PluginConfig
    ):
        self.group_id = str(group_id)
        self.loader_id = str(loader_id)
        self.loader_name = loader_name
        self.weapon_spec = weapon_spec
        self.mode = mode
        self.config = config

        # 初始化弹仓
        chambers_list = [True] * bullet_count + [False] * (weapon_spec.max_chambers - bullet_count)
        random.shuffle(chambers_list)
        self.chambers: List[bool] = chambers_list
        self.current_chamber_idx: int = 0

        # 玩家状态
        self.user_talents: Dict[str, Talent] = {}
        self.user_hp_lock_used: Set[str] = set()
        self.recent_players: List[Tuple[str, str]] = [(loader_id, loader_name)]
        self.last_shooter: Optional[Tuple[str, str]] = None

        # 战场突发道具状态
        self.sticky_bomb: Optional[StickyBombState] = None
        self.smoke_rounds_left: int = 0
        self.blinded_users: Set[str] = set()

        self.created_at: float = time.time()
        self.game_over: bool = False

    @property
    def remaining_bullets(self) -> int:
        return self.chambers[self.current_chamber_idx:].count(True)

    @property
    def remaining_chambers(self) -> int:
        return len(self.chambers) - self.current_chamber_idx

    def register_player(self, user_id: str, user_name: str):
        uid = str(user_id)
        if not any(p[0] == uid for p in self.recent_players):
            self.recent_players.append((uid, user_name))

    def draw_talent(self, user_id: str, user_name: str) -> Tuple[bool, str]:
        """抽取命格异能（能力模式下可用，每人每局限抽一次）"""
        uid = str(user_id)
        if self.mode != GameMode.TALENT:
            return False, "⚠️ 当前为【普通轮盘模式】，命格抽取未开启！请管理员使用指令切换至【能力模式】！"

        if uid in self.user_talents:
            existing = self.user_talents[uid]
            return False, f"⚠️ @{user_name} 你本局已经觉醒了命格 【{existing.rarity}·{existing.name}】（{existing.tag}），不可重复抽取！"

        talent = draw_random_talent()
        self.user_talents[uid] = talent
        self.register_player(uid, user_name)

        text = RouletteTexts.get_talent_draw_text(
            user=user_name,
            rarity=talent.rarity,
            name=talent.name,
            tag=talent.tag,
            desc=talent.description
        )
        return True, text

    def peek_next_bullet(self, user_id: str) -> Optional[bool]:
        """曼波透视眼能力"""
        uid = str(user_id)
        talent = self.user_talents.get(uid)
        if talent and talent.xray and self.current_chamber_idx < len(self.chambers):
            return self.chambers[self.current_chamber_idx]
        return None

    def _calculate_ban_duration(self, talent: Optional[Talent]) -> int:
        base_ban = random.randint(self.config.min_ban_seconds, self.config.max_ban_seconds)
        ban = int(base_ban * self.weapon_spec.ban_multiplier)
        if talent and talent.ban_reduction > 0:
            ban = int(ban * (1.0 - talent.ban_reduction))
        return max(10, ban)

    def _get_random_other_player(self, exclude_ids: List[str]) -> Optional[Tuple[str, str]]:
        candidates = [p for p in self.recent_players if p[0] not in exclude_ids]
        if candidates:
            return random.choice(candidates)
        return None

    def execute_shoot(
        self,
        user_id: str,
        user_name: str,
        is_admin: bool = False
    ) -> ShootResult:
        """执行开枪扣动扳机流程"""
        uid = str(user_id)
        self.register_player(uid, user_name)
        talent = self.user_talents.get(uid)

        result = ShootResult(
            user_id=uid,
            user_name=user_name,
            weapon_type=self.weapon_spec.type,
            shots_fired=0,
            live_hits=0,
            blanks_fired=0,
            game_over=False,
            remaining_bullets=0,
            remaining_chambers=0
        )

        burst = self.weapon_spec.burst_count
        if talent and talent.double_shot_chance > 0 and random.random() < talent.double_shot_chance:
            burst += 1
            result.narratives.append(f"🔫 @{user_name} 触发【手抖症候群】，手指颤抖，不小心多扣了一枪！")

        if self.weapon_spec.type == WeaponType.GATLING:
            result.narratives.append(RouletteTexts.get_gatling_burst_text(user_name))

        for _ in range(burst):
            if self.current_chamber_idx >= len(self.chambers):
                break

            is_live = self.chambers[self.current_chamber_idx]
            self.current_chamber_idx += 1
            result.shots_fired += 1

            if not is_live:
                result.blanks_fired += 1
                blank_text = RouletteTexts.get_blank_text(user_name)
                result.narratives.append(blank_text)

                if talent:
                    if talent.coin_multiplier > 1.0:
                        Database.get_instance().record_user_action(uid, survive=True, coins_delta=50, score_delta=10)
                        trig = RouletteTexts.get_talent_trigger_text("crazy_thursday", user_name)
                        if trig:
                            result.narratives.append(trig)
                    elif talent.bluff and random.random() < 0.40:
                        trig = RouletteTexts.get_talent_trigger_text("bluff_king", user_name)
                        if trig:
                            result.narratives.append(trig)
                    else:
                        Database.get_instance().record_user_action(uid, survive=True, coins_delta=20, score_delta=5)
                else:
                    Database.get_instance().record_user_action(uid, survive=True, coins_delta=20, score_delta=5)
            else:
                self._handle_live_hit(uid, user_name, talent, is_admin, result)
        Database.get_instance().record_user_action(uid, shot=True)

        # 粘性炸弹传递与引爆
        if self.sticky_bomb:
            self._handle_sticky_bomb(uid, user_name, is_admin, result)

        # 随机突发战场道具空投
        if self.sticky_bomb is None:
            dropped_item = TacticalItemManager.roll_airdrop(self.config.item_trigger_rate)
            if dropped_item == TacticalItemType.STICKY_BOMB:
                self.sticky_bomb = TacticalItemManager.init_sticky_bomb(uid, user_name)
                drop_text = RouletteTexts.get_tactical_drop_text(TacticalItemType.STICKY_BOMB, user_name)
                result.narratives.append(drop_text)
            elif dropped_item == TacticalItemType.SMOKE_GRENADE:
                self.smoke_rounds_left = 2
                drop_text = RouletteTexts.get_tactical_drop_text(TacticalItemType.SMOKE_GRENADE, user_name)
                result.narratives.append(drop_text)
            elif dropped_item == TacticalItemType.FLASHBANG:
                self.blinded_users.add(uid)
                drop_text = RouletteTexts.get_tactical_drop_text(TacticalItemType.FLASHBANG, user_name)
                result.narratives.append(drop_text)

        result.next_bullet_peek = self.peek_next_bullet(uid)
        self.last_shooter = (uid, user_name)
        result.remaining_bullets = self.remaining_bullets
        result.remaining_chambers = self.remaining_chambers

        if result.remaining_bullets == 0 or result.remaining_chambers == 0:
            result.game_over = True
            self.game_over = True
            result.narratives.append(RouletteTexts.get_empty_magazine_text())

        return result

    def _handle_sticky_bomb(self, uid: str, user_name: str, is_admin: bool, result: ShootResult):
        if self.sticky_bomb.holder_id != uid:
            old_user = self.sticky_bomb.holder_name
            self.sticky_bomb.holder_id = uid
            self.sticky_bomb.holder_name = user_name
            self.sticky_bomb.fuse_remaining -= 1

            if self.sticky_bomb.fuse_remaining <= 0:
                bomb_ban = random.randint(90, 240)
                exp_text = RouletteTexts.get_sticky_explode_text(user_name, bomb_ban)
                result.narratives.append(exp_text)
                result.effects.append(ShootEffectResult(
                    target_id=uid,
                    target_name=user_name,
                    is_admin=is_admin,
                    ban_seconds=0 if is_admin else bomb_ban,
                    is_dead=True,
                    is_blown_up=True,
                    reason="粘性炸弹引爆"
                ))
                self.sticky_bomb = None
            else:
                pass_text = RouletteTexts.get_sticky_pass_text(
                    old_user=old_user,
                    new_user=user_name,
                    remaining=self.sticky_bomb.fuse_remaining
                )
                result.narratives.append(pass_text)

    def _handle_live_hit(
        self,
        uid: str,
        user_name: str,
        talent: Optional[Talent],
        is_admin: bool,
        result: ShootResult
    ):
        result.live_hits += 1

        # 1. 锁血挂壁
        if talent and talent.hp_lock and uid not in self.user_hp_lock_used:
            self.user_hp_lock_used.add(uid)
            trig = RouletteTexts.get_talent_trigger_text("hp_lock", user_name)
            result.narratives.append(trig)
            Database.get_instance().record_user_action(uid, dodge=True, score_delta=15)
            return

        # 2. 弹反 (Parry)
        if talent and talent.parry_chance > 0 and random.random() < talent.parry_chance:
            target_id = self.loader_id
            target_name = self.loader_name
            ban_dur = self._calculate_ban_duration(None)
            trig = RouletteTexts.get_talent_trigger_text("parry_master", user_name, target_name)
            result.narratives.append(trig)
            result.effects.append(ShootEffectResult(
                target_id=target_id,
                target_name=target_name,
                is_admin=False,
                ban_seconds=ban_dur,
                is_dead=True,
                is_parried=True,
                reason="弹反反噬"
            ))
            Database.get_instance().record_user_action(uid, dodge=True, score_delta=25)
            return

        # 3. 替死 (义父救我)
        if talent and talent.transfer_chance > 0 and random.random() < talent.transfer_chance:
            sub = self._get_random_other_player([uid]) or self.last_shooter or (self.loader_id, self.loader_name)
            target_id, target_name = sub
            ban_dur = self._calculate_ban_duration(None)
            trig = RouletteTexts.get_talent_trigger_text("sugar_daddy", user_name, target_name)
            result.narratives.append(trig)
            result.effects.append(ShootEffectResult(
                target_id=target_id,
                target_name=target_name,
                is_admin=False,
                ban_seconds=ban_dur,
                is_dead=True,
                is_transferred=True,
                reason="义父替死"
            ))
            Database.get_instance().record_user_action(uid, dodge=True, score_delta=20)
            return

        # 4. 闪避率判定
        dodge_rate = self.config.default_dodge_rate
        if uid in self.blinded_users:
            dodge_rate = 0.0
        elif talent:
            dodge_rate += talent.dodge_bonus

        if dodge_rate > 0 and random.random() < dodge_rate:
            dodge_text = RouletteTexts.get_dodge_text(user_name)
            result.narratives.append(dodge_text)
            Database.get_instance().record_user_action(uid, dodge=True, score_delta=20)
            return

        self._apply_hit_consequences(uid, user_name, talent, is_admin, result)

    def _apply_hit_consequences(
        self,
        uid: str,
        user_name: str,
        talent: Optional[Talent],
        is_admin: bool,
        result: ShootResult
    ):
        ban_dur = self._calculate_ban_duration(talent)

        if is_admin:
            imm_text = RouletteTexts.get_admin_immunity_text(user_name)
            result.narratives.append(imm_text)
            result.effects.append(ShootEffectResult(
                target_id=uid,
                target_name=user_name,
                is_admin=True,
                ban_seconds=0,
                is_dead=False,
                reason="管理员特权护体"
            ))
        else:
            hit_text = RouletteTexts.get_hit_text(user_name, ban_dur)
            result.narratives.append(hit_text)
            result.effects.append(ShootEffectResult(
                target_id=uid,
                target_name=user_name,
                is_admin=False,
                ban_seconds=ban_dur,
                is_dead=True,
                reason="中弹击倒"
            ))
            Database.get_instance().record_user_action(uid, death=True, score_delta=-10)

            if talent:
                if talent.extortion:
                    Database.get_instance().record_user_action(uid, coins_delta=100)
                    Database.get_instance().record_user_action(self.loader_id, coins_delta=-100)
                    trig = RouletteTexts.get_talent_trigger_text("extortionist", user_name, self.loader_name)
                    if trig:
                        result.narratives.append(trig)
                if talent.ban_reduction > 0:
                    trig = RouletteTexts.get_talent_trigger_text("stubborn_mouth", user_name)
                    if trig:
                        result.narratives.append(trig)
                if talent.suicide_aoe:
                    sub = self._get_random_other_player([uid])
                    if sub:
                        s_id, s_name = sub
                        extra_ban = self._calculate_ban_duration(None)
                        trig = RouletteTexts.get_talent_trigger_text("nuclear_boom", user_name, s_name)
                        if trig:
                            result.narratives.append(trig)
                        result.effects.append(ShootEffectResult(
                            target_id=s_id,
                            target_name=s_name,
                            is_admin=False,
                            ban_seconds=extra_ban,
                            is_dead=True,
                            is_blown_up=True,
                            reason="自爆炸伤"
                        ))

        # 武器特效：大狙穿透 / RPG AOE
        if self.weapon_spec.type == WeaponType.SNIPER and random.random() < self.weapon_spec.pierce_chance:
            sub = self._get_random_other_player([uid])
            if sub:
                s_id, s_name = sub
                pierce_ban = self._calculate_ban_duration(None)
                pierce_text = RouletteTexts.get_sniper_pierce_text(user_name, s_name)
                result.narratives.append(pierce_text)
                result.effects.append(ShootEffectResult(
                    target_id=s_id,
                    target_name=s_name,
                    is_admin=False,
                    ban_seconds=pierce_ban,
                    is_dead=True,
                    reason="大狙穿透伤害"
                ))

        elif self.weapon_spec.type == WeaponType.RPG and random.random() < self.weapon_spec.aoe_splash_chance:
            sub = self._get_random_other_player([uid])
            if sub:
                s_id, s_name = sub
                rpg_ban = self._calculate_ban_duration(None)
                rpg_text = RouletteTexts.get_rpg_aoe_text(user_name, s_name)
                result.narratives.append(rpg_text)
                result.effects.append(ShootEffectResult(
                    target_id=s_id,
                    target_name=s_name,
                    is_admin=False,
                    ban_seconds=rpg_ban,
                    is_dead=True,
                    is_blown_up=True,
                    reason="RPG冲击波波及"
                ))


