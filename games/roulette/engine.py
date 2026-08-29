# -*- coding: utf-8 -*-
import random
import time
from typing import List, Dict, Optional, Tuple, Set

from .models import (
    WeaponType,
    GameMode,
    ShootTarget,
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

    def _get_group_settings(self):
        return Database.get_instance().get_group_settings(self.group_id)

    def _calculate_ban_duration(self, talent: Optional[Talent]) -> int:
        g_cfg = self._get_group_settings()
        base_ban = random.randint(g_cfg.min_ban, g_cfg.max_ban)
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
        is_admin: bool = False,
        target_type: ShootTarget = ShootTarget.OPPONENT,
        target_user_id: Optional[str] = None,
        target_user_name: Optional[str] = None
    ) -> ShootResult:
        """执行开枪扣动扳机流程（支持向自己开枪自瞄再动 / 向对面决斗）"""
        uid = str(user_id)
        self.register_player(uid, user_name)
        shooter_talent = self.user_talents.get(uid)

        # 确定目标受害者
        if target_type == ShootTarget.SELF:
            victim_id = uid
            victim_name = user_name
            victim_is_admin = is_admin
        else:
            if target_user_id and target_user_name:
                victim_id = str(target_user_id)
                victim_name = target_user_name
                self.register_player(victim_id, victim_name)
            else:
                other = self._get_random_other_player([uid]) or self.last_shooter or (uid, user_name)
                victim_id, victim_name = other
            victim_is_admin = False  # 外部传入或在hit时判定

        result = ShootResult(
            user_id=uid,
            user_name=user_name,
            weapon_type=self.weapon_spec.type,
            shots_fired=0,
            live_hits=0,
            blanks_fired=0,
            game_over=False,
            remaining_bullets=0,
            remaining_chambers=0,
            extra_turn=False
        )

        burst = self.weapon_spec.burst_count
        if shooter_talent and shooter_talent.double_shot_chance > 0 and random.random() < shooter_talent.double_shot_chance:
            burst += 1
            result.narratives.append(f"🔫 【{user_name}】触发【手抖症候群】，手指颤抖，不小心多扣了一枪！")

        if self.weapon_spec.type == WeaponType.GATLING:
            result.narratives.append(RouletteTexts.get_gatling_burst_text(user_name))

        for _ in range(burst):
            if self.current_chamber_idx >= len(self.chambers):
                break

            is_live = self.chambers[self.current_chamber_idx]
            self.current_chamber_idx += 1
            result.shots_fired += 1

            if not is_live:
                # ====== 空弹判定 ======
                result.blanks_fired += 1
                if target_type == ShootTarget.SELF:
                    # 恶魔轮盘核心：朝自己开枪空弹，获得额外一回合再动开火权！
                    result.extra_turn = True
                    self.user_extra_turn = uid
                    self_text = RouletteTexts.get_self_blank_text(user_name)
                    result.narratives.append(self_text)
                else:
                    if victim_id == uid:
                        blank_text = RouletteTexts.get_blank_text(user_name)
                        result.narratives.append(blank_text)
                    else:
                        blank_text = f"🎲 咔哒！【{user_name}】瞄准【{victim_name}】扣动扳机——击发击空！未能击中目标！"
                        result.narratives.append(blank_text)

                        # 决斗规则：射击他人未命中，开枪者必须立即接受一发自罚子弹！
                        if self.current_chamber_idx < len(self.chambers):
                            penalty_is_live = self.chambers[self.current_chamber_idx]
                            self.current_chamber_idx += 1
                            result.shots_fired += 1
                            if penalty_is_live:
                                penalty_ban = self._calculate_ban_duration(shooter_talent)
                                penalty_hit_text = RouletteTexts.get_counter_penalty_hit_text(user_name, victim_name, penalty_ban)
                                result.narratives.append(penalty_hit_text)
                                result.effects.append(ShootEffectResult(
                                    target_id=uid,
                                    target_name=user_name,
                                    is_admin=is_admin,
                                    ban_seconds=0 if is_admin else penalty_ban,
                                    is_dead=True,
                                    reason="决斗反噬自罚中弹"
                                ))
                                Database.get_instance().record_user_action(uid, death=True, score_delta=-10)
                            else:
                                result.blanks_fired += 1
                                penalty_blank_text = RouletteTexts.get_counter_penalty_blank_text(user_name, victim_name)
                                result.narratives.append(penalty_blank_text)

                # 经济加成
                if shooter_talent and shooter_talent.coin_multiplier > 1.0:
                    Database.get_instance().record_user_action(uid, survive=True, coins_delta=50, score_delta=10)
                    trig = RouletteTexts.get_talent_trigger_text("crazy_thursday", user_name)
                    if trig:
                        result.narratives.append(trig)
                else:
                    Database.get_instance().record_user_action(uid, survive=True, coins_delta=20, score_delta=5)


            else:
                # ====== 实弹命中判定 ======
                # 检查曼波·因果逆转
                victim_talent = self.user_talents.get(victim_id)
                active_talent = shooter_talent if target_type == ShootTarget.SELF else victim_talent
                if active_talent and active_talent.reverse_bullet_chance > 0 and random.random() < active_talent.reverse_bullet_chance:
                    result.blanks_fired += 1
                    if target_type == ShootTarget.SELF:
                        result.extra_turn = True
                    trig = RouletteTexts.get_talent_trigger_text("mambo_reversal", victim_name)
                    result.narratives.append(trig)
                    Database.get_instance().record_user_action(victim_id, dodge=True, score_delta=20)
                    continue

                self._handle_live_hit(
                    shooter_id=uid,
                    shooter_name=user_name,
                    victim_id=victim_id,
                    victim_name=victim_name,
                    shooter_talent=shooter_talent,
                    victim_talent=victim_talent,
                    is_admin=victim_is_admin,
                    target_type=target_type,
                    result=result
                )

        Database.get_instance().record_user_action(uid, shot=True)

        # 粘性炸弹传递与引爆
        if self.sticky_bomb:
            self._handle_sticky_bomb(uid, user_name, is_admin, result)

        # 随机突发战场道具空投
        g_cfg = self._get_group_settings()
        if self.sticky_bomb is None and g_cfg.items_enabled:
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
        shooter_id: str,
        shooter_name: str,
        victim_id: str,
        victim_name: str,
        shooter_talent: Optional[Talent],
        victim_talent: Optional[Talent],
        is_admin: bool,
        target_type: ShootTarget,
        result: ShootResult
    ):
        result.live_hits += 1

        # 1. 锁血挂壁
        if victim_talent and victim_talent.hp_lock and victim_id not in self.user_hp_lock_used:
            self.user_hp_lock_used.add(victim_id)
            trig = RouletteTexts.get_talent_trigger_text("hp_lock", victim_name)
            result.narratives.append(trig)
            Database.get_instance().record_user_action(victim_id, dodge=True, score_delta=15)
            return

        # 2. 弹反 (Parry)
        if victim_talent and victim_talent.parry_chance > 0 and random.random() < victim_talent.parry_chance:
            target_id = shooter_id if shooter_id != victim_id else self.loader_id
            target_name = shooter_name if shooter_id != victim_id else self.loader_name
            ban_dur = self._calculate_ban_duration(None)
            trig = RouletteTexts.get_talent_trigger_text("parry_master", victim_name, target_name)
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
            Database.get_instance().record_user_action(victim_id, dodge=True, score_delta=25)
            return

        # 3. 替死 (义父救我)
        if victim_talent and victim_talent.transfer_chance > 0 and random.random() < victim_talent.transfer_chance:
            sub = self._get_random_other_player([victim_id, shooter_id]) or (shooter_id, shooter_name)
            target_id, target_name = sub
            ban_dur = self._calculate_ban_duration(None)
            trig = RouletteTexts.get_talent_trigger_text("sugar_daddy", victim_name, target_name)
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
            Database.get_instance().record_user_action(victim_id, dodge=True, score_delta=20)
            return

        # 4. 闪避率判定
        g_cfg = self._get_group_settings()
        dodge_rate = g_cfg.dodge_rate
        if victim_id in self.blinded_users:
            dodge_rate = 0.0
        elif victim_talent:
            dodge_rate += victim_talent.dodge_bonus

        if dodge_rate > 0 and random.random() < dodge_rate:
            dodge_text = RouletteTexts.get_dodge_text(victim_name)
            result.narratives.append(dodge_text)
            Database.get_instance().record_user_action(victim_id, dodge=True, score_delta=20)
            return

        self._apply_hit_consequences(
            shooter_id=shooter_id,
            shooter_name=shooter_name,
            victim_id=victim_id,
            victim_name=victim_name,
            shooter_talent=shooter_talent,
            victim_talent=victim_talent,
            is_admin=is_admin,
            target_type=target_type,
            result=result
        )


    def _apply_hit_consequences(
        self,
        shooter_id: str,
        shooter_name: str,
        victim_id: str,
        victim_name: str,
        shooter_talent: Optional[Talent],
        victim_talent: Optional[Talent],
        is_admin: bool,
        target_type: ShootTarget,
        result: ShootResult
    ):
        ban_dur = self._calculate_ban_duration(victim_talent)

        # 恶魔赌徒加成
        if shooter_talent and shooter_talent.opponent_extra_ban > 0 and shooter_id != victim_id:
            ban_dur = int(ban_dur * (1.0 + shooter_talent.opponent_extra_ban))
            Database.get_instance().record_user_action(shooter_id, coins_delta=50)
            Database.get_instance().record_user_action(victim_id, coins_delta=-50)
            trig = RouletteTexts.get_talent_trigger_text("devil_gambler", shooter_name, victim_name)
            if trig:
                result.narratives.append(trig)

        if is_admin:
            imm_text = RouletteTexts.get_admin_immunity_text(victim_name)
            result.narratives.append(imm_text)
            result.effects.append(ShootEffectResult(
                target_id=victim_id,
                target_name=victim_name,
                is_admin=True,
                ban_seconds=0,
                is_dead=False,
                reason="管理员特权护体"
            ))
        else:
            if target_type == ShootTarget.OPPONENT and shooter_id != victim_id:
                hit_text = RouletteTexts.get_opponent_hit_text(shooter_name, victim_name, ban_dur)
            else:
                hit_text = RouletteTexts.get_hit_text(victim_name, ban_dur)
            result.narratives.append(hit_text)

            result.effects.append(ShootEffectResult(
                target_id=victim_id,
                target_name=victim_name,
                is_admin=False,
                ban_seconds=ban_dur,
                is_dead=True,
                reason="中弹击倒"
            ))
            Database.get_instance().record_user_action(victim_id, death=True, score_delta=-10)

            # 五五开·强行一换一
            if victim_talent and victim_talent.fifty_fifty_kill and random.random() < 0.50:
                co_victim_id = shooter_id if shooter_id != victim_id else self.loader_id
                co_victim_name = shooter_name if shooter_id != victim_id else self.loader_name
                if co_victim_id != victim_id:
                    co_ban = self._calculate_ban_duration(None)
                    trig = RouletteTexts.get_talent_trigger_text("fifty_fifty_kill", victim_name, co_victim_name)
                    if trig:
                        result.narratives.append(trig)
                    result.effects.append(ShootEffectResult(
                        target_id=co_victim_id,
                        target_name=co_victim_name,
                        is_admin=False,
                        ban_seconds=co_ban,
                        is_dead=True,
                        reason="五五开一换一"
                    ))


            if victim_talent:
                if victim_talent.extortion:
                    Database.get_instance().record_user_action(victim_id, coins_delta=100)
                    Database.get_instance().record_user_action(self.loader_id, coins_delta=-100)
                    trig = RouletteTexts.get_talent_trigger_text("extortionist", victim_name, self.loader_name)
                    if trig:
                        result.narratives.append(trig)
                if victim_talent.ban_reduction > 0:
                    trig = RouletteTexts.get_talent_trigger_text("stubborn_mouth", victim_name)
                    if trig:
                        result.narratives.append(trig)
                if victim_talent.suicide_aoe:
                    sub = self._get_random_other_player([victim_id])
                    if sub:
                        s_id, s_name = sub
                        extra_ban = self._calculate_ban_duration(None)
                        trig = RouletteTexts.get_talent_trigger_text("nuclear_boom", victim_name, s_name)
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
            sub = self._get_random_other_player([victim_id, shooter_id]) or self._get_random_other_player([victim_id])
            if sub:
                s_id, s_name = sub
                pierce_ban = self._calculate_ban_duration(None)
                pierce_text = RouletteTexts.get_sniper_pierce_text(victim_name, s_name)
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
            sub = self._get_random_other_player([victim_id, shooter_id]) or self._get_random_other_player([victim_id])
            if sub:
                s_id, s_name = sub
                rpg_ban = self._calculate_ban_duration(None)
                rpg_text = RouletteTexts.get_rpg_aoe_text(victim_name, s_name)
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



