# -*- coding: utf-8 -*-
import random
import asyncio
from typing import Dict, Any, Optional

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

try:
    from .core.config import PluginConfig
    from .core.database import Database
    from .core.game_manager import GameManager
    from .games.roulette.models import GameMode, WeaponType, ShootTarget
    from .games.roulette.weapons import get_weapon_spec, WEAPON_SPECS
    from .games.roulette.engine import RouletteSession
    from .games.roulette.duel import DuelManager, DuelInvitation, DuelSession
    from .games.roulette.texts import RouletteTexts
    from .games.scratch import ScratchEngine, SCRATCH_TIERS
    from .systems.leaderboard_renderer import LeaderboardRenderer
except (ImportError, ValueError):
    from games.scratch import ScratchEngine, SCRATCH_TIERS
    from core.config import PluginConfig
    from core.database import Database
    from core.game_manager import GameManager
    from games.roulette.models import GameMode, WeaponType, ShootTarget
    from games.roulette.weapons import get_weapon_spec, WEAPON_SPECS
    from games.roulette.engine import RouletteSession
    from games.roulette.duel import DuelManager, DuelInvitation, DuelSession
    from games.roulette.texts import RouletteTexts
    from systems.leaderboard_renderer import LeaderboardRenderer





@register("astrbot_plugin_wywy", "无欲物语", "多功能群聊小型娱乐综合插件，集成魔改高能军火轮盘赌、命格异能抽奖与突发战场战术道具", "1.2.0")
class Main(Star):
    def __init__(self, context: Context, config: Dict[str, Any] = None):
        super().__init__(context)
        self.config_data = config or {}
        self.plugin_config = PluginConfig.from_dict(self.config_data)
        self.db = Database.get_instance()
        self.game_mgr = GameManager.get_instance()
        self.duel_mgr = DuelManager.get_instance()


    def _get_group_id(self, event: AstrMessageEvent) -> Optional[str]:
        """安全获取群ID，私聊则返回 None"""
        try:
            gid = event.get_group_id()
            return str(gid) if gid else None
        except Exception:
            return None

    def _get_user_info(self, event: AstrMessageEvent) -> tuple[str, str]:
        """安全获取用户 ID、昵称"""
        try:
            uid = str(event.get_sender_id() or "")
        except Exception:
            uid = "unknown"

        try:
            uname = str(event.get_sender_name() or uid)
        except Exception:
            uname = uid

        return uid, uname

    async def _check_is_admin(self, event: AstrMessageEvent, group_id: str, user_id: str) -> bool:
        """全平台、多维度管理员与群主权限鉴定"""
        # 1. 优先调用 AstrBot 原生角色提取方法
        try:
            if hasattr(event, "get_sender_role"):
                r = str(event.get_sender_role() or "").lower()
                if r in ["admin", "owner", "administrator"]:
                    return True
            if hasattr(event, "get_role"):
                r = str(event.get_role() or "").lower()
                if r in ["admin", "owner", "administrator"]:
                    return True
            if hasattr(event, "is_admin"):
                val = event.is_admin
                if callable(val):
                    val = val()
                if asyncio.iscoroutine(val):
                    val = await val
                if val:
                    return True
        except Exception:
            pass

        # 2. 检查 message_obj.sender 属性
        try:
            sender_obj = getattr(getattr(event, "message_obj", None), "sender", None)
            if sender_obj:
                role = str(getattr(sender_obj, "role", "") or "").lower()
                if role in ["admin", "owner", "administrator"]:
                    return True
        except Exception:
            pass

        # 3. 检查 raw_event 原始消息体
        try:
            raw = getattr(event, "raw_message", None) or getattr(event, "message_obj", None)
            if hasattr(event, "get_raw_event"):
                raw_evt = event.get_raw_event()
                if isinstance(raw_evt, dict):
                    sender_dict = raw_evt.get("sender", {})
                    r = str(sender_dict.get("role", "")).lower()
                    if r in ["admin", "owner", "administrator"]:
                        return True
        except Exception:
            pass

        # 4. 检查 AstrBot 全局超管配置
        try:
            admin_id = str(getattr(self.context, "admin_id", "") or "")
            if admin_id and str(user_id) == admin_id:
                return True
            if hasattr(self.context, "is_admin") and callable(self.context.is_admin):
                if self.context.is_admin(user_id):
                    return True
        except Exception:
            pass

        # 5. 主动向 Bot 查询群成员真实身份（权威兜底）
        try:
            bot = getattr(event, "bot", None)
            if bot and hasattr(bot, "get_group_member_info"):
                g_val = int(group_id) if group_id.isdigit() else group_id
                u_val = int(user_id) if user_id.isdigit() else user_id
                info = await bot.get_group_member_info(group_id=g_val, user_id=u_val, no_cache=False)
                if isinstance(info, dict):
                    r = str(info.get("role", "")).lower()
                    if r in ["admin", "owner", "administrator"]:
                        return True
        except Exception:
            pass

        return False


    async def _try_ban_user(self, event: AstrMessageEvent, group_id: str, user_id: str, duration: int):
        """尝试禁言用户（全平台多协议适配：OneBot v11、NapCat、Lagrange、QQ官方等）"""
        if duration <= 0:
            return

        # 尝试转数字类型（若为纯数字QQ号）
        try:
            g_val = int(group_id) if group_id.isdigit() else group_id
            u_val = int(user_id) if user_id.isdigit() else user_id
        except Exception:
            g_val, u_val = group_id, user_id

        # 1. 尝试 bot client 的直接调用
        bot = getattr(event, "bot", None)
        if bot:
            for method_name in ["set_group_ban", "group_ban", "mute_member"]:
                if hasattr(bot, method_name):
                    try:
                        func = getattr(bot, method_name)
                        await func(group_id=g_val, user_id=u_val, duration=duration)
                        return
                    except Exception:
                        pass

            # 2. 尝试 bot.api
            bot_api = getattr(bot, "api", None)
            if bot_api:
                for method_name in ["set_group_ban", "group_ban", "mute_member"]:
                    if hasattr(bot_api, method_name):
                        try:
                            func = getattr(bot_api, method_name)
                            await func(group_id=g_val, user_id=u_val, duration=duration)
                            return
                        except Exception:
                            pass

        # 3. 尝试 event.call_api
        if hasattr(event, "call_api"):
            try:
                await event.call_api("set_group_ban", group_id=g_val, user_id=u_val, duration=duration)
                return
            except Exception as e:
                logger.warning(f"[无欲物语] call_api 禁言用户 {user_id} 提示: {e}")


    async def _handle_timeout_callback(self, group_id: str):
        """轮盘超时清理回调"""
        self.game_mgr.remove_game(group_id)
        logger.info(f"[无欲物语] 群 {group_id} 轮盘赌超时已自动解散。")

    # ========== 核心业务处理方法 ==========

    async def _do_load(self, event: AstrMessageEvent, weapon_or_count: str = "", count_str: str = ""):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 轮盘赌仅支持在群聊中进行！")
            return

        g_cfg = self.db.get_group_settings(group_id, self.plugin_config.default_mode)
        if not g_cfg.enabled:
            yield event.plain_result("⛔ 本群娱乐小游戏已被管理员关闭。发送【/群开关 开启】可重新启用。")
            return

        uid, uname = self._get_user_info(event)
        is_admin = await self._check_is_admin(event, group_id, uid)

        async with self.game_mgr.get_lock(group_id):
            if self.game_mgr.get_game(group_id) or self.duel_mgr.get_duel(group_id):
                yield event.plain_result("⚠️ 当前群内已经有一场激烈的对决正在进行中了！请发送【/开枪】扣动扳机，或发送【/轮盘状态】查看对局！")
                return

            weapon_input = weapon_or_count
            custom_count = None

            if weapon_or_count.isdigit():
                custom_count = int(weapon_or_count)
                weapon_input = "左轮"
            elif count_str.isdigit():
                custom_count = int(count_str)

            weapon_spec = get_weapon_spec(weapon_input)

            if custom_count is not None:
                if not is_admin:
                    yield event.plain_result("⚠️ 只有群管理员才能指定自定义实弹数量哦！普通玩家随机装填！")
                    return
                bullet_count = max(1, min(custom_count, weapon_spec.max_chambers))
            else:
                bullet_count = random.randint(weapon_spec.default_min_bullets, weapon_spec.default_max_bullets)

            game_mode = GameMode.TALENT if g_cfg.mode == "talent" else GameMode.CLASSIC

            session = RouletteSession(
                group_id=group_id,
                loader_id=uid,
                loader_name=uname,
                weapon_spec=weapon_spec,
                bullet_count=bullet_count,
                mode=game_mode,
                config=self.plugin_config
            )
            self.game_mgr.set_game(group_id, session)
            self.game_mgr.schedule_timeout(group_id, self.plugin_config.timeout_seconds, self._handle_timeout_callback)

            load_text = RouletteTexts.get_load_text(weapon_spec.type, uname, bullet_count, weapon_spec.max_chambers)
            mode_desc = "🌟【能力大乱斗模式】（发送 /抽能力 觉醒本局神技）" if game_mode == GameMode.TALENT else "🎲【普通经典模式】（自带5%命运闪避）"

            reply_msg = (
                f"{load_text}\n\n"
                f"📊 武器规格：{weapon_spec.icon} {weapon_spec.name}\n"
                f"⚙️ 当前模式：{mode_desc}\n"
                f"💡 操作指引：发送【/开枪】扣动扳机 | 发送【/抽能力】觉醒命格"
            )
            yield event.plain_result(reply_msg)

    async def _do_shoot(self, event: AstrMessageEvent, target_param: str = "", force_target_type: Optional[ShootTarget] = None):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 轮盘赌仅支持在群聊中进行！")
            return

        g_cfg = self.db.get_group_settings(group_id, self.plugin_config.default_mode)
        if not g_cfg.enabled:
            yield event.plain_result("⛔ 本群娱乐小游戏已被管理员关闭。发送【/群开关 开启】可重新启用。")
            return

        uid, uname = self._get_user_info(event)
        is_admin = await self._check_is_admin(event, group_id, uid)

        # 解析开枪目标
        target_uid = None
        target_uname = None
        param = target_param.strip()
        is_devil = False

        for comp in getattr(getattr(event, "message_obj", None), "message", []):
            if getattr(comp, "type", "") == "At" or comp.__class__.__name__ == "At":
                target_uid = str(getattr(comp, "qq", "") or getattr(comp, "target", "") or "")
        if not target_uid and param.isdigit():
            target_uid = param
        if target_uid:
            target_uname = param.replace("@", "").strip() or f"玩家{target_uid}"

        if force_target_type == ShootTarget.SELF or any(k in param for k in ["自己", "self", "me", "自瞄"]):
            target_type = ShootTarget.SELF
            is_devil = True
        elif force_target_type == ShootTarget.OPPONENT or target_uid:
            target_type = ShootTarget.OPPONENT
        else:
            if self.duel_mgr.get_duel(group_id):
                target_type = ShootTarget.OPPONENT
            else:
                target_type = ShootTarget.SELF
                is_devil = False

        # 1. 优先检查 1v1 决斗会话
        duel = self.duel_mgr.get_duel(group_id)
        if duel:
            success, result, err_msg = duel.execute_turn(uid, uname, is_admin, target_type)
            if not success:
                yield event.plain_result(err_msg)
                return

            for effect in result.effects:
                if effect.is_dead and effect.ban_seconds > 0 and not effect.is_admin:
                    await self._try_ban_user(event, group_id, effect.target_id, effect.ban_seconds)

            narrative_block = "\n\n".join(result.narratives)
            status_line = f"📊 膛室剩余: {result.remaining_bullets}/{result.remaining_chambers}"
            turn_tip = f"\n👉 下一行动回合：【{duel.p1[1] if duel.current_turn == duel.p1[0] else duel.p2[1]}】（请发送 /向对面开枪 或 /向自己开枪）" if not duel.game_over else ""

            final_msg = f"{narrative_block}\n\n{status_line}{turn_tip}"
            if duel.game_over:
                self.duel_mgr.remove_duel(group_id)

            yield event.plain_result(final_msg)
            return

        async with self.game_mgr.get_lock(group_id):
            session: Optional[RouletteSession] = self.game_mgr.get_game(group_id)
            if not session:
                yield event.plain_result("⚠️ 当前群内没有正在进行的对局！发送【/装填】装上子弹开始一场生死对决吧！")
                return

            self.game_mgr.schedule_timeout(group_id, self.plugin_config.timeout_seconds, self._handle_timeout_callback)
            result = session.execute_shoot(
                user_id=uid,
                user_name=uname,
                is_admin=is_admin,
                target_type=target_type,
                target_user_id=target_uid,
                target_user_name=target_uname,
                is_devil_self=is_devil
            )



            for effect in result.effects:
                if effect.is_dead and effect.ban_seconds > 0 and not effect.is_admin:
                    await self._try_ban_user(event, group_id, effect.target_id, effect.ban_seconds)

            narrative_block = "\n\n".join(result.narratives)
            status_line = f"📊 膛室剩余: {result.remaining_bullets}/{result.remaining_chambers}"

            final_msg = f"{narrative_block}\n\n{status_line}"
            if result.extra_turn and not result.game_over:
                final_msg += "\n🔥【命运再动】你获得了一次额外行动机会，请继续选择【/向自己开枪】或【/向对面开枪】！"

            if result.game_over:
                self.game_mgr.remove_game(group_id)

            yield event.plain_result(final_msg)


    async def _do_talent(self, event: AstrMessageEvent):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 仅支持在群聊中使用！")
            return

        g_cfg = self.db.get_group_settings(group_id, self.plugin_config.default_mode)
        if not g_cfg.enabled:
            yield event.plain_result("⛔ 本群娱乐小游戏已被管理员关闭。")
            return

        uid, uname = self._get_user_info(event)

        # ???? 1v1 ??????????
        duel = self.duel_mgr.get_duel(group_id)
        if duel:
            if not duel.is_participant(uid):
                yield event.plain_result("?? ??????? 1v1 ????????????????????")
                return
            success, msg = duel.roulette.draw_talent(uid, uname)
            yield event.plain_result(msg)
            return

        async with self.game_mgr.get_lock(group_id):
            session: Optional[RouletteSession] = self.game_mgr.get_game(group_id)
            if not session:
                if g_cfg.mode != "talent":
                    yield event.plain_result("⚠️ 当前群为【普通模式】，发送【/轮盘模式 能力】可切换为能力大乱斗模式！")
                else:
                    yield event.plain_result("⚠️ 当前还没有装填开局！发送【/装填】开始游戏后即可抽取命格！")
                return

            success, msg = session.draw_talent(uid, uname)
            yield event.plain_result(msg)


    async def _do_mode(self, event: AstrMessageEvent, target_mode: str = ""):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 仅支持在群聊中使用！")
            return

        uid, uname = self._get_user_info(event)
        is_admin = await self._check_is_admin(event, group_id, uid)
        target = target_mode.strip()

        if not target:
            curr = self.db.get_group_mode(group_id, self.plugin_config.default_mode)
            curr_name = "🌟【能力大乱斗模式】" if curr == "talent" else "🎲【普通经典模式】"
            yield event.plain_result(
                f"⚙️ 当前群轮盘模式为：{curr_name}\n"
                f"💡 切换指令：【/轮盘模式 普通】或【/轮盘模式 能力】（持久生效）"
            )
            return

        if not is_admin:
            yield event.plain_result("⚠️ 只有群管理员才能切换群轮盘模式哦！")

            return

        if any(k in target for k in ["能力", "异能", "talent"]):
            self.db.set_group_mode(group_id, "talent")
            yield event.plain_result("✅ 群轮盘模式已切换为：🌟【能力大乱斗模式】！\n后续每局开局后，所有玩家均可通过【/抽能力】觉醒专属神技！设置已持久保存。")
        elif any(k in target for k in ["普通", "经典", "classic"]):
            self.db.set_group_mode(group_id, "classic")
            yield event.plain_result("✅ 群轮盘模式已切换为：🎲【普通经典模式】！\n回归经典原汁原味对决，默认附带 5% 命运闪避。设置已持久保存。")
        else:
            yield event.plain_result("⚠️ 模式参数不正确！请使用：【/轮盘模式 普通】 或 【/轮盘模式 能力】")

    async def _do_status(self, event: AstrMessageEvent):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 仅支持在群聊中使用！")
            return

        session: Optional[RouletteSession] = self.game_mgr.get_game(group_id)
        if not session:
            curr_mode = self.db.get_group_mode(group_id, self.plugin_config.default_mode)
            mode_name = "🌟【能力大乱斗】" if curr_mode == "talent" else "🎲【普通经典】"
            yield event.plain_result(f"💤 当前群内暂无进行中的轮盘对局。\n⚙️ 群默认模式：{mode_name}\n🔫 发送【/装填】立即开始！")
            return

        bomb_info = f"💣 粘性炸弹：正在 @{session.sticky_bomb.holder_name} 身上滴答倒计时（剩余{session.sticky_bomb.fuse_remaining}次）" if session.sticky_bomb else "💣 战场无炸弹"
        players_str = "、".join([p[1] for p in session.recent_players]) or "暂无"

        msg = (
            f"🔫 军火轮盘 · 当前战况\n"
            f"━━━━━━━━━━━━━━\n"
            f"🎯 武器类型：{session.weapon_spec.icon} {session.weapon_spec.name}\n"
            f"📊 弹仓情况：剩余 {session.remaining_bullets} 发实弹 / 共剩 {session.remaining_chambers} 个膛室\n"
            f"👤 装弹勇士：@{session.loader_name}\n"
            f"👥 参战玩家：{players_str}\n"
            f"⚠️ 战场状态：{bomb_info}\n"
            f"━━━━━━━━━━━━━━\n"
            f"👉 发送【/开枪】扣动扳机！"
        )
        yield event.plain_result(msg)

    async def _do_entertainment(self, event: AstrMessageEvent):
        msg = (
            "🎮 〓 无欲物语 · 小型娱乐中心 〓\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✨ 当前开放小游戏：\n"
            "【1】🔫 魔改军火轮盘赌\n"
            "   ▸ 玩法：左轮/大狙/加特林/火箭筒 四大武器心跳博弈\n"
            "   ▸ 机制：开局异能抽奖、5%极意闪避、战场突发战术道具\n"
            "   ▸ 快速开局：发送【/装填】或【/开枪】\n"
            "\n"
            "⏳ 即将上线玩法：\n"
            "【2】🎫 刮刮乐彩票（高倍返奖，一夜暴富）\n"
            "【3】💰 银行与抢劫（随身金币存取、高风险抢劫博弈）\n"
            "【4】📅 每日签到（连签加成、金币补给）\n"
            "【5】🏆 综合排行榜（首富榜、神枪手榜、枪下亡魂榜）\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 发送【/帮助中心】可查看本插件全部详细指令清单！"
        )
        yield event.plain_result(msg)

    async def _do_help_center(self, event: AstrMessageEvent):
        msg = (
            "📖 〓 无欲物语 · 帮助中心 〓\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "【🎮 轮盘对决指令】\n"
            "• /向自己开枪 (或: /自瞄) —— 朝自己开枪（空弹获得额外连开机会，实弹自爆）\n"
            "• /向对面开枪 (或: /打对面/射击) —— 瞄准对手/下家扣动扳机\n"
            "• /开枪 —— 快捷扣动扳机（支持: /开枪 自己、/开枪 @某人）\n"
            "• /装填 [武器] [实弹数] —— 装填开局（支持：左轮/大狙/加特林/火箭筒）\n"
            "• /轮盘状态 (或: 看枪) —— 查看当前弹仓实弹、剩余膛室与炸弹状态\n"
            "• /轮盘帮助 (或: 无欲物语) —— 查看轮盘武器特效与机制详解\n"
            "\n"
            "【🌟 异能命格指令】\n"
            "• /抽能力 (或: 逆天改命/觉醒) —— 抽取【曼波因果逆转】、【五五开一换一】、【恶魔双响】、【锁血】等神技\n"
            "\n"
            "【⚙️ 群独立管理员指令】\n"
            "• /群管理 (或: /群配置) —— 查看本群当前生效的全部独立参数\n"
            "• /群开关 开启/关闭 —— 控制本群全部娱乐功能启停\n"
            "• /轮盘模式 普通/能力 —— 持久切换本群轮盘玩法模式\n"
            "• /群禁言 60 300 —— 自定义本群实弹中弹禁言区间\n"
            "• /群道具 开启/关闭 —— 控制本群战场突发空投道具\n"
            "• /强制结束 (或: /重置轮盘) —— 强制清空本群卡住的对局\n"
            "• /走火开 或 /走火关 —— 控制本群被动随机走火功能\n"
            "\n"
            "【🎪 综合娱乐指令】\n"
            "• /娱乐 —— 打开小型娱乐中心游戏菜单\n"
            "• /帮助中心 —— 查看此指令清单\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        yield event.plain_result(msg)



    async def _do_help(self, event: AstrMessageEvent):
        msg = (
            "🔫 〓 无欲物语 · 军火轮盘决斗说明书 〓\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "【🎯 武器库一览】\n"
            "• /装填 [左轮] —— 标准6孔左轮，1~3发实弹，经典心跳博弈\n"
            "• /装填 大狙   —— 巴雷特重狙，禁言翻倍，35%穿透连带后排！\n"
            "• /装填 加特林 —— 15发大弹鼓，疯狂3连扫射，火力覆盖！\n"
            "• /装填 火箭筒 —— 高爆RPG，80%几率AOE爆炸拉路人同归于尽！\n"
            "\n"
            "【🌟 核心机制】\n"
            "• /开枪 —— 扣动扳机参与对决，被击中将接受小黑屋禁言洗礼！\n"
            "• 5% 命运闪避 —— 极意残影！触发时免除禁言惩罚！\n"
            "• 战术空投 —— 开枪后随机空投【粘性炸弹(击鼓传花)】、【战术烟雾】、【强光闪光】！\n"
            "• /抽能力 —— (能力模式下) 抽取【义父救我】、【弹反Parry】、【原地自爆】、【锁血】等10+热梗神技！\n"
            "• /轮盘模式 [普通/能力] —— 管理员可一键持久切换群玩法模式！\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ 提示：同一时间每个群只允许开启一场对决，300秒无操作自动解散。"
        )
        yield event.plain_result(msg)


    async def _do_group_admin(self, event: AstrMessageEvent):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 仅支持在群聊中使用！")
            return
        g_cfg = self.db.get_group_settings(group_id, self.plugin_config.default_mode)
        status_switch = "🟢 开启中" if g_cfg.enabled else "🔴 已关闭"
        mode_str = "🌟 能力大乱斗模式" if g_cfg.mode == "talent" else "🎲 普通经典模式"
        misfire_str = "🟢 开启" if g_cfg.misfire_enabled else "🔴 关闭"
        items_str = "🟢 启用" if g_cfg.items_enabled else "🔴 禁用"
        msg = (
            f"⚙️ 〓 本群专属娱乐管理看板 〓\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"【群 号】: {group_id}\n"
            f"【娱乐开关】: {status_switch}\n"
            f"【轮盘模式】: {mode_str}\n"
            f"【禁言区间】: {g_cfg.min_ban}秒 ~ {g_cfg.max_ban}秒\n"
            f"【战术空投】: {items_str}\n"
            f"【被动走火】: {misfire_str}\n"
            f"【基础闪避】: {int(g_cfg.dodge_rate * 100)}%\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 管理员专属配置指令：\n"
            f"• /群开关 开启/关闭 —— 控制本群功能启停\n"
            f"• /轮盘模式 普通/能力 —— 切换本群玩法模式\n"
            f"• /群禁言 60 300 —— 自定义本群禁言区间\n"
            f"• /群道具 开启/关闭 —— 控制空投战术道具\n"
            f"• /走火开 或 /走火关 —— 控制群聊被动走火\n"
            f"• /强制结束 —— 强制解散当前卡住的对局"
        )
        yield event.plain_result(msg)

    async def _do_group_switch(self, event: AstrMessageEvent, status_str: str = ""):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 仅支持在群聊中使用！")
            return
        uid, uname = self._get_user_info(event)
        if not await self._check_is_admin(event, group_id, uid):
            yield event.plain_result("⚠️ 只有群管理员才能调整本群娱乐功能开关哦！")
            return
        target = status_str.strip()
        if any(k in target for k in ["开", "开启", "on", "enable", "true"]):
            self.db.update_group_settings(group_id, enabled=True)
            yield event.plain_result("✅ 本群娱乐小游戏功能已【开启】！")
        elif any(k in target for k in ["关", "关闭", "off", "disable", "false"]):
            self.db.update_group_settings(group_id, enabled=False)
            self.game_mgr.remove_game(group_id)
            self.duel_mgr.remove_duel(group_id)
            self.duel_mgr.remove_invitation(group_id)
            yield event.plain_result("⛔ 本群娱乐小游戏功能已【关闭】。正在进行的对局已自动清空。")
        else:
            yield event.plain_result("⚠️ 请使用：【/群开关 开启】或【/群开关 关闭】")

    async def _do_group_ban_config(self, event: AstrMessageEvent, min_str: str = "", max_str: str = ""):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 仅支持在群聊中使用！")
            return
        uid, uname = self._get_user_info(event)
        if not await self._check_is_admin(event, group_id, uid):
            yield event.plain_result("⚠️ 只有群管理员才能配置本群禁言时长！")
            return
        if not min_str.isdigit():
            yield event.plain_result("⚠️ 请提供有效的禁言秒数！格式：【/群禁言 60 300】（最小秒 最大秒）")
            return
        min_sec = int(min_str)
        max_sec = int(max_str) if max_str.isdigit() else min_sec
        if min_sec > max_sec:
            min_sec, max_sec = max_sec, min_sec
        min_sec = max(10, min_sec)
        max_sec = max(min_sec, max_sec)
        self.db.update_group_settings(group_id, min_ban=min_sec, max_ban=max_sec)
        yield event.plain_result(f"✅ 本群轮盘实弹中弹基础禁言时长已设置为：{min_sec}秒 ~ {max_sec}秒！设置已持久保存。")

    async def _do_group_items_switch(self, event: AstrMessageEvent, status_str: str = ""):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 仅支持在群聊中使用！")
            return
        uid, uname = self._get_user_info(event)
        if not await self._check_is_admin(event, group_id, uid):
            yield event.plain_result("⚠️ 只有群管理员才能调整战场战术道具开关！")
            return
        target = status_str.strip()
        if any(k in target for k in ["开", "开启", "on", "enable", "true"]):
            self.db.update_group_settings(group_id, items_enabled=True)
            yield event.plain_result("✅ 本群【战场突发道具（粘弹/烟雾/闪光）】已【启用】！")
        elif any(k in target for k in ["关", "关闭", "off", "disable", "false"]):
            self.db.update_group_settings(group_id, items_enabled=False)
            yield event.plain_result("🛡️ 本群【战场突发道具】已【禁用】。")
        else:
            yield event.plain_result("⚠️ 请使用：【/群道具 开启】或【/群道具 关闭】")

    async def _do_force_reset(self, event: AstrMessageEvent):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 仅支持在群聊中使用！")
            return
        uid, uname = self._get_user_info(event)
        if not await self._check_is_admin(event, group_id, uid):
            yield event.plain_result("⚠️ 只有群管理员才能强制结束对局！")
            return
        self.game_mgr.remove_game(group_id)
        yield event.plain_result("🧹 本群轮盘对局已强制解散并重置！")

    async def _do_duel_challenge(self, event: AstrMessageEvent, target_str: str = "", weapon_str: str = ""):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 决斗仅支持在群聊中发起！")
            return

        g_cfg = self.db.get_group_settings(group_id, self.plugin_config.default_mode)
        if not g_cfg.enabled:
            yield event.plain_result("⛔ 本群娱乐小游戏已被管理员关闭。")
            return

        uid, uname = self._get_user_info(event)

        if self.duel_mgr.get_duel(group_id) or self.game_mgr.get_game(group_id):
            yield event.plain_result("⚠️ 当前群内已有对决正在进行中，请等待本局结束！")
            return

        target_uid = None
        for comp in getattr(getattr(event, "message_obj", None), "message", []):
            if getattr(comp, "type", "") == "At" or comp.__class__.__name__ == "At":
                target_uid = str(getattr(comp, "qq", "") or getattr(comp, "target", "") or "")
        if not target_uid and target_str.isdigit():
            target_uid = target_str

        if not target_uid or target_uid == uid:
            yield event.plain_result("⚠️ 请使用【/决斗 @某人 [武器]】指定你想挑战的对手！不能挑战自己哦！")
            return

        target_name = target_str.replace("@", "").strip() or f"玩家{target_uid}"
        weapon_spec = get_weapon_spec(weapon_str or "左轮")

        inv = self.duel_mgr.create_invitation(
            group_id=group_id,
            challenger_id=uid,
            challenger_name=uname,
            target_id=target_uid,
            target_name=target_name,
            weapon_spec=weapon_spec
        )

        msg = (
            f"⚔️ 〓 生死决斗发起通知 〓\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 发起人：【{uname}】\n"
            f"🎯 被挑战人：【{target_name}】\n"
            f"🔫 决斗武器：{weapon_spec.icon} {weapon_spec.name}\n"
            f"⏳ 响应时限：60 秒\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👉 请【{target_name}】发送【/接受决斗】应战，或发送【/拒绝决斗】弃权！"
        )
        yield event.plain_result(msg)

    async def _do_duel_accept(self, event: AstrMessageEvent):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 仅支持在群聊中使用！")
            return

        uid, uname = self._get_user_info(event)
        inv = self.duel_mgr.get_invitation(group_id)
        if not inv:
            yield event.plain_result("⚠️ 当前群内没有待接受的决斗邀请或邀请已过期！")
            return

        if inv.target_id != uid:
            yield event.plain_result(f"⚠️ 这场决斗是向【{inv.target_name}】发起的，你不能代为接受哦！")
            return

        inv.target_name = uname
        duel = self.duel_mgr.start_duel(inv, self.plugin_config)
        msg = (
            f"🔥 〓 决斗正式开启 · 生死看淡 〓\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚔️ 决斗双方：【{duel.p1[1]}】 VS 【{duel.p2[1]}】\n"
            f"🎯 选定武器：{duel.weapon_spec.icon} {duel.weapon_spec.name}\n"
            f"🎲 先手行动：【{duel.p1[1]}】\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 规则提示：\n"
            f"1. 发送【/向自己开枪】—— 空弹获得【再动】连击，实弹自爆！\n"
            f"2. 发送【/向对面开枪】—— 实弹淘汰对手，空弹触发【反噬自罚一枪】！\n"
            f"👉 请【{duel.p1[1]}】开始你的回合！"
        )
        yield event.plain_result(msg)

    async def _do_duel_reject(self, event: AstrMessageEvent):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 仅支持在群聊中使用！")
            return

        uid, uname = self._get_user_info(event)
        inv = self.duel_mgr.get_invitation(group_id)
        if not inv:
            yield event.plain_result("⚠️ 当前群内没有待处理的决斗邀请！")
            return

        if inv.target_id != uid and inv.challenger_id != uid:
            yield event.plain_result("⚠️ 你不是本场决斗的参与者！")
            return

        self.duel_mgr.remove_invitation(group_id)
        yield event.plain_result(f"🏳️ 【{uname}】取消/拒绝了本次决斗邀请，硝烟散去。")

    async def _do_leaderboard(self, event: AstrMessageEvent, rank_type_str: str = ""):
        group_id = self._get_group_id(event)
        r_type = (rank_type_str or "ban_time").strip().lower()
        if any(k in r_type for k in ["幸运", "阳寿", "lucky", "dodge"]):
            key = "lucky"
        elif any(k in r_type for k in ["中弹", "亡魂", "death", "dead"]):
            key = "deaths"
        elif any(k in r_type for k in ["胜场", "战神", "duel", "win"]):
            key = "duel"
        elif any(k in r_type for k in ["财富", "首富", "coin", "wealth", "钱"]):
            key = "coins"
        else:
            key = "ban_time"

        items = self.db.get_leaderboard(rank_type=key, limit=10)
        img_path = await LeaderboardRenderer.render_leaderboard_image(self.context, key, items, group_id or "")
        if img_path:
            yield event.image_result(img_path)
        else:
            yield event.plain_result("?? ??????????")

    # ========== 独立指令注册（符合官方规范） ==========

    @filter.command("装填")
    async def cmd_load(self, event: AstrMessageEvent, weapon_or_count: str = "", count_str: str = ""):
        async for r in self._do_load(event, weapon_or_count, count_str):
            yield r

    @filter.command("装弹")
    async def cmd_load_alias(self, event: AstrMessageEvent, weapon_or_count: str = "", count_str: str = ""):
        async for r in self._do_load(event, weapon_or_count, count_str):
            yield r

    @filter.command("开枪")
    async def cmd_shoot(self, event: AstrMessageEvent, target_param: str = ""):
        async for r in self._do_shoot(event, target_param):
            yield r

    @filter.command("扣动扳机")
    async def cmd_shoot_alias1(self, event: AstrMessageEvent, target_param: str = ""):
        async for r in self._do_shoot(event, target_param):
            yield r

    @filter.command("碰")
    async def cmd_shoot_alias2(self, event: AstrMessageEvent, target_param: str = ""):
        async for r in self._do_shoot(event, target_param):
            yield r

    @filter.command("开火")
    async def cmd_shoot_alias3(self, event: AstrMessageEvent, target_param: str = ""):
        async for r in self._do_shoot(event, target_param):
            yield r

    @filter.command("向自己开枪")
    async def cmd_shoot_self(self, event: AstrMessageEvent):
        async for r in self._do_shoot(event, force_target_type=ShootTarget.SELF):
            yield r

    @filter.command("自瞄")
    async def cmd_shoot_self_alias1(self, event: AstrMessageEvent):
        async for r in self._do_shoot(event, force_target_type=ShootTarget.SELF):
            yield r

    @filter.command("打自己")
    async def cmd_shoot_self_alias2(self, event: AstrMessageEvent):
        async for r in self._do_shoot(event, force_target_type=ShootTarget.SELF):
            yield r

    @filter.command("自开枪")
    async def cmd_shoot_self_alias3(self, event: AstrMessageEvent):
        async for r in self._do_shoot(event, force_target_type=ShootTarget.SELF):
            yield r

    @filter.command("向对面开枪")
    async def cmd_shoot_opponent(self, event: AstrMessageEvent, target_param: str = ""):
        async for r in self._do_shoot(event, target_param, force_target_type=ShootTarget.OPPONENT):
            yield r

    @filter.command("打对面")
    async def cmd_shoot_opponent_alias1(self, event: AstrMessageEvent, target_param: str = ""):
        async for r in self._do_shoot(event, target_param, force_target_type=ShootTarget.OPPONENT):
            yield r

    @filter.command("射击")
    async def cmd_shoot_opponent_alias2(self, event: AstrMessageEvent, target_param: str = ""):
        async for r in self._do_shoot(event, target_param, force_target_type=ShootTarget.OPPONENT):
            yield r


    @filter.command("抽能力")
    async def cmd_talent(self, event: AstrMessageEvent):
        async for r in self._do_talent(event):
            yield r

    @filter.command("逆天改命")
    async def cmd_talent_alias1(self, event: AstrMessageEvent):
        async for r in self._do_talent(event):
            yield r

    @filter.command("觉醒")
    async def cmd_talent_alias2(self, event: AstrMessageEvent):
        async for r in self._do_talent(event):
            yield r

    @filter.command("轮盘模式")
    async def cmd_mode(self, event: AstrMessageEvent, target_mode: str = ""):
        async for r in self._do_mode(event, target_mode):
            yield r

    @filter.command("轮盘状态")
    async def cmd_status(self, event: AstrMessageEvent):
        async for r in self._do_status(event):
            yield r

    @filter.command("看枪")
    async def cmd_status_alias(self, event: AstrMessageEvent):
        async for r in self._do_status(event):
            yield r

    @filter.command("娱乐")
    async def cmd_entertainment(self, event: AstrMessageEvent):
        async for r in self._do_entertainment(event):
            yield r

    @filter.command("小型娱乐")
    async def cmd_entertainment_alias(self, event: AstrMessageEvent):
        async for r in self._do_entertainment(event):
            yield r

    @filter.command("帮助中心")
    async def cmd_help_center(self, event: AstrMessageEvent):
        async for r in self._do_help_center(event):
            yield r

    @filter.command("娱乐帮助")
    async def cmd_help_center_alias1(self, event: AstrMessageEvent):
        async for r in self._do_help_center(event):
            yield r

    @filter.command("所有指令")
    async def cmd_help_center_alias2(self, event: AstrMessageEvent):
        async for r in self._do_help_center(event):
            yield r

    @filter.command("轮盘帮助")
    async def cmd_help(self, event: AstrMessageEvent):
        async for r in self._do_help(event):
            yield r

    @filter.command("无欲物语")
    async def cmd_help_alias(self, event: AstrMessageEvent):
        async for r in self._do_help(event):
            yield r

    @filter.command("走火开")
    async def cmd_misfire_on(self, event: AstrMessageEvent):
        group_id = self._get_group_id(event)
        if not group_id:
            return
        uid, uname = self._get_user_info(event)
        is_admin = await self._check_is_admin(event, group_id, uid)
        if not is_admin:
            yield event.plain_result("⚠️ 只有管理员才能开启随机走火功能！")
            return
        self.db.set_group_misfire(group_id, True)
        yield event.plain_result("🔥 随机走火功能已【开启】！群聊闲聊时将有微小几率走火中弹！")

    @filter.command("走火关")
    async def cmd_misfire_off(self, event: AstrMessageEvent):
        group_id = self._get_group_id(event)
        if not group_id:
            return
        uid, uname = self._get_user_info(event)
        is_admin = await self._check_is_admin(event, group_id, uid)
        if not is_admin:
            yield event.plain_result("⚠️ 只有管理员才能关闭随机走火功能！")
            return
        self.db.set_group_misfire(group_id, False)
        yield event.plain_result("🛡️ 随机走火功能已【关闭】。")

    @filter.command("群管理")
    async def cmd_group_admin(self, event: AstrMessageEvent):
        async for r in self._do_group_admin(event):
            yield r

    @filter.command("群配置")
    async def cmd_group_admin_alias1(self, event: AstrMessageEvent):
        async for r in self._do_group_admin(event):
            yield r

    @filter.command("娱乐设置")
    async def cmd_group_admin_alias2(self, event: AstrMessageEvent):
        async for r in self._do_group_admin(event):
            yield r

    @filter.command("群开关")
    async def cmd_group_switch(self, event: AstrMessageEvent, status: str = ""):
        async for r in self._do_group_switch(event, status):
            yield r

    @filter.command("娱乐开关")
    async def cmd_group_switch_alias(self, event: AstrMessageEvent, status: str = ""):
        async for r in self._do_group_switch(event, status):
            yield r

    @filter.command("群禁言")
    async def cmd_group_ban(self, event: AstrMessageEvent, min_sec: str = "", max_sec: str = ""):
        async for r in self._do_group_ban_config(event, min_sec, max_sec):
            yield r

    @filter.command("轮盘禁言")
    async def cmd_group_ban_alias(self, event: AstrMessageEvent, min_sec: str = "", max_sec: str = ""):
        async for r in self._do_group_ban_config(event, min_sec, max_sec):
            yield r

    @filter.command("群道具")
    async def cmd_group_items(self, event: AstrMessageEvent, status: str = ""):
        async for r in self._do_group_items_switch(event, status):
            yield r

    @filter.command("道具开关")
    async def cmd_group_items_alias(self, event: AstrMessageEvent, status: str = ""):
        async for r in self._do_group_items_switch(event, status):
            yield r

    @filter.command("强制结束")
    async def cmd_force_reset(self, event: AstrMessageEvent):
        async for r in self._do_force_reset(event):
            yield r

    @filter.command("重置轮盘")
    async def cmd_force_reset_alias1(self, event: AstrMessageEvent):
        async for r in self._do_force_reset(event):
            yield r

    @filter.command("清空轮盘")
    async def cmd_force_reset_alias2(self, event: AstrMessageEvent):
        async for r in self._do_force_reset(event):
            yield r

    # ========== 决斗指令注册 ==========

    @filter.command("决斗")
    async def cmd_duel(self, event: AstrMessageEvent, target: str = "", weapon: str = ""):
        async for r in self._do_duel_challenge(event, target, weapon):
            yield r

    @filter.command("发起决斗")
    async def cmd_duel_alias1(self, event: AstrMessageEvent, target: str = "", weapon: str = ""):
        async for r in self._do_duel_challenge(event, target, weapon):
            yield r

    @filter.command("挑战")
    async def cmd_duel_alias2(self, event: AstrMessageEvent, target: str = "", weapon: str = ""):
        async for r in self._do_duel_challenge(event, target, weapon):
            yield r

    @filter.command("接受决斗")
    async def cmd_duel_accept(self, event: AstrMessageEvent):
        async for r in self._do_duel_accept(event):
            yield r

    @filter.command("应战")
    async def cmd_duel_accept_alias1(self, event: AstrMessageEvent):
        async for r in self._do_duel_accept(event):
            yield r

    @filter.command("接战")
    async def cmd_duel_accept_alias2(self, event: AstrMessageEvent):
        async for r in self._do_duel_accept(event):
            yield r

    @filter.command("拒绝决斗")
    async def cmd_duel_reject(self, event: AstrMessageEvent):
        async for r in self._do_duel_reject(event):
            yield r

    @filter.command("拒战")
    async def cmd_duel_reject_alias(self, event: AstrMessageEvent):
        async for r in self._do_duel_reject(event):
            yield r

    # ========== 排行榜指令注册（输出高清渲染图片） ==========

    @filter.command("轮盘排行")
    async def cmd_rank(self, event: AstrMessageEvent, rank_type: str = ""):
        async for r in self._do_leaderboard(event, rank_type):
            yield r

    @filter.command("排行榜")
    async def cmd_rank_alias1(self, event: AstrMessageEvent, rank_type: str = ""):
        async for r in self._do_leaderboard(event, rank_type):
            yield r

    @filter.command("娱乐排行")
    async def cmd_rank_alias2(self, event: AstrMessageEvent, rank_type: str = ""):
        async for r in self._do_leaderboard(event, rank_type):
            yield r

    @filter.command("受害者榜")
    async def cmd_rank_ban(self, event: AstrMessageEvent):
        async for r in self._do_leaderboard(event, "ban_time"):
            yield r

    @filter.command("惩罚排行")
    async def cmd_rank_ban_alias(self, event: AstrMessageEvent):
        async for r in self._do_leaderboard(event, "ban_time"):
            yield r

    @filter.command("幸运榜")
    async def cmd_rank_lucky(self, event: AstrMessageEvent):
        async for r in self._do_leaderboard(event, "lucky"):
            yield r

    @filter.command("阳寿排行")
    async def cmd_rank_lucky_alias(self, event: AstrMessageEvent):
        async for r in self._do_leaderboard(event, "lucky"):
            yield r

    @filter.command("中弹榜")
    async def cmd_rank_death(self, event: AstrMessageEvent):
        async for r in self._do_leaderboard(event, "deaths"):
            yield r

    @filter.command("亡魂排行")
    async def cmd_rank_death_alias(self, event: AstrMessageEvent):
        async for r in self._do_leaderboard(event, "deaths"):
            yield r

    @filter.command("胜场榜")
    async def cmd_rank_duel(self, event: AstrMessageEvent):
        async for r in self._do_leaderboard(event, "duel"):
            yield r

    @filter.command("战神榜")
    async def cmd_rank_duel_alias(self, event: AstrMessageEvent):
        async for r in self._do_leaderboard(event, "duel"):
            yield r

    @filter.command("首富榜")
    async def cmd_rank_coins(self, event: AstrMessageEvent):
        async for r in self._do_leaderboard(event, "coins"):
            yield r

    @filter.command("财富榜")
    async def cmd_rank_coins_alias(self, event: AstrMessageEvent):
        async for r in self._do_leaderboard(event, "coins"):
            yield r

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_group_message(self, event: AstrMessageEvent):
        """被动监听群聊消息（支持被动走火与自然语言兜底）"""
        group_id = self._get_group_id(event)
        if not group_id:
            return

        is_misfire_on = self.db.get_group_misfire(group_id, self.plugin_config.enable_misfire)
        if is_misfire_on and random.random() < self.plugin_config.misfire_probability:
            uid, uname = self._get_user_info(event)
            is_admin = await self._check_is_admin(event, group_id, uid)
            ban_dur = random.randint(self.plugin_config.min_ban_seconds, self.plugin_config.max_ban_seconds)
            misfire_text = RouletteTexts.get_misfire_text(uname, ban_dur)
            if not is_admin:
                await self._try_ban_user(event, group_id, uid, ban_dur)
            else:
                misfire_text += "\n" + RouletteTexts.get_admin_immunity_text(uname)
            yield event.plain_result(misfire_text)



