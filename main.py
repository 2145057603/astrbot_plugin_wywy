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
    from .games.roulette.models import GameMode, WeaponType
    from .games.roulette.weapons import get_weapon_spec, WEAPON_SPECS
    from .games.roulette.engine import RouletteSession
    from .games.roulette.texts import RouletteTexts
except (ImportError, ValueError):
    from core.config import PluginConfig
    from core.database import Database
    from core.game_manager import GameManager
    from games.roulette.models import GameMode, WeaponType
    from games.roulette.weapons import get_weapon_spec, WEAPON_SPECS
    from games.roulette.engine import RouletteSession
    from games.roulette.texts import RouletteTexts



@register("astrbot_plugin_wywy", "无欲物语", "多功能群聊小型娱乐综合插件，集成魔改高能军火轮盘赌、命格异能抽奖与突发战场战术道具", "1.0.0")
class Main(Star):
    def __init__(self, context: Context, config: Dict[str, Any] = None):
        super().__init__(context)
        self.config_data = config or {}
        self.plugin_config = PluginConfig.from_dict(self.config_data)
        self.db = Database.get_instance()
        self.game_mgr = GameManager.get_instance()

    def _get_group_id(self, event: AstrMessageEvent) -> Optional[str]:
        """安全获取群ID，私聊则返回 None"""
        try:
            gid = event.get_group_id()
            return str(gid) if gid else None
        except Exception:
            return None

    def _get_user_info(self, event: AstrMessageEvent) -> tuple[str, str, bool]:
        """安全获取用户 ID、昵称、是否为管理员（全协议容错兼容）"""
        try:
            uid = str(event.get_sender_id() or "")
        except Exception:
            uid = "unknown"

        try:
            uname = str(event.get_sender_name() or uid)
        except Exception:
            uname = uid

        is_admin = False
        try:
            sender_obj = getattr(getattr(event, "message_obj", None), "sender", None)
            role = str(getattr(sender_obj, "role", "") or "").lower()
            is_admin = role in ["admin", "owner", "administrator"]
        except Exception:
            pass

        try:
            admin_id = str(getattr(self.context, "admin_id", "") or "")
            if admin_id and uid == admin_id:
                is_admin = True
        except Exception:
            pass

        return uid, uname, is_admin

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

        uid, uname, is_admin = self._get_user_info(event)
        async with self.game_mgr.get_lock(group_id):
            if self.game_mgr.get_game(group_id):
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

            current_mode_str = self.db.get_group_mode(group_id, self.plugin_config.default_mode)
            game_mode = GameMode.TALENT if current_mode_str == "talent" else GameMode.CLASSIC

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

    async def _do_shoot(self, event: AstrMessageEvent):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 轮盘赌仅支持在群聊中进行！")
            return

        uid, uname, is_admin = self._get_user_info(event)
        async with self.game_mgr.get_lock(group_id):
            session: Optional[RouletteSession] = self.game_mgr.get_game(group_id)
            if not session:
                yield event.plain_result("⚠️ 当前群内没有正在进行的对局！发送【/装填】装上子弹开始一场生死对决吧！")
                return

            self.game_mgr.schedule_timeout(group_id, self.plugin_config.timeout_seconds, self._handle_timeout_callback)
            result = session.execute_shoot(uid, uname, is_admin)

            for effect in result.effects:
                if effect.is_dead and effect.ban_seconds > 0 and not effect.is_admin:
                    await self._try_ban_user(event, group_id, effect.target_id, effect.ban_seconds)

            extra_notes = []
            if result.next_bullet_peek is not None:
                peek_desc = "💀【极度危险·实弹在膛】" if result.next_bullet_peek else "🍀【虚惊一场·下发是空弹】"
                extra_notes.append(f"👁️ 曼波透视眼暗号：{peek_desc}")

            narrative_block = "\n\n".join(result.narratives)
            status_line = f"📊 膛室剩余: {result.remaining_bullets}/{result.remaining_chambers}"

            final_msg = f"{narrative_block}\n\n{status_line}"
            if extra_notes:
                final_msg += "\n" + "\n".join(extra_notes)

            if result.game_over:
                self.game_mgr.remove_game(group_id)

            yield event.plain_result(final_msg)

    async def _do_talent(self, event: AstrMessageEvent):
        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("⚠️ 仅支持在群聊中使用！")
            return

        uid, uname, _ = self._get_user_info(event)
        async with self.game_mgr.get_lock(group_id):
            session: Optional[RouletteSession] = self.game_mgr.get_game(group_id)
            if not session:
                current_mode_str = self.db.get_group_mode(group_id, self.plugin_config.default_mode)
                if current_mode_str != "talent":
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

        uid, uname, is_admin = self._get_user_info(event)
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
            "• /装填 [武器] [实弹数] —— 装填开局（支持：左轮/大狙/加特林/火箭筒）\n"
            "• /开枪 (或: 碰/扣动扳机/开火) —— 扣动当前武器扳机参与对决\n"
            "• /轮盘状态 (或: 看枪) —— 查看当前弹仓实弹、剩余膛室与炸弹状态\n"
            "• /轮盘帮助 (或: 无欲物语) —— 查看轮盘武器特效与机制详解\n"
            "\n"
            "【🌟 异能命格指令】\n"
            "• /抽能力 (或: 逆天改命/觉醒) —— 在能力模式下抽取专属神技命格\n"
            "\n"
            "【⚙️ 管理员配置指令】\n"
            "• /轮盘模式 [普通/能力] —— 持久切换或查询当前群生效的轮盘模式\n"
            "• /走火开 —— 开启群聊消息随机被动走火功能\n"
            "• /走火关 —— 关闭群聊消息随机被动走火功能\n"
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
    async def cmd_shoot(self, event: AstrMessageEvent):
        async for r in self._do_shoot(event):
            yield r

    @filter.command("扣动扳机")
    async def cmd_shoot_alias1(self, event: AstrMessageEvent):
        async for r in self._do_shoot(event):
            yield r

    @filter.command("碰")
    async def cmd_shoot_alias2(self, event: AstrMessageEvent):
        async for r in self._do_shoot(event):
            yield r

    @filter.command("开火")
    async def cmd_shoot_alias3(self, event: AstrMessageEvent):
        async for r in self._do_shoot(event):
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
        _, _, is_admin = self._get_user_info(event)
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
        _, _, is_admin = self._get_user_info(event)
        if not is_admin:
            yield event.plain_result("⚠️ 只有管理员才能关闭随机走火功能！")
            return
        self.db.set_group_misfire(group_id, False)
        yield event.plain_result("🛡️ 随机走火功能已【关闭】。")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_group_message(self, event: AstrMessageEvent):
        """被动监听群聊消息（支持被动走火与自然语言兜底）"""
        group_id = self._get_group_id(event)
        if not group_id:
            return

        is_misfire_on = self.db.get_group_misfire(group_id, self.plugin_config.enable_misfire)
        if is_misfire_on and random.random() < self.plugin_config.misfire_probability:
            uid, uname, is_admin = self._get_user_info(event)
            ban_dur = random.randint(self.plugin_config.min_ban_seconds, self.plugin_config.max_ban_seconds)
            misfire_text = RouletteTexts.get_misfire_text(uname, ban_dur)
            if not is_admin:
                await self._try_ban_user(event, group_id, uid, ban_dur)
            else:
                misfire_text += "\n" + RouletteTexts.get_admin_immunity_text(uname)
            yield event.plain_result(misfire_text)


