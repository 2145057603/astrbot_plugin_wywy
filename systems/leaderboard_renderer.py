# -*- coding: utf-8 -*-
import os
import time
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """获取跨平台可用的中文字体"""
    font_candidates = [
        "msyh.ttc",
        "simhei.ttf",
        "simsun.ttc",
        "C:\\Windows\\Fonts\\msyh.ttc",
        "C:\\Windows\\Fonts\\simhei.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    ]
    for candidate in font_candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


class LeaderboardRenderer:
    """排行榜高清图片渲染器"""

    TITLES_MAP = {
        "ban_time": ("🩸 惩罚时间排行榜 (受害者榜)", "谁是进小黑屋最久的ICU终身VIP？", ["ICU终身VIP", "小黑屋常客", "闭麦艺术家", "天选受害者", "沉睡魔咒", "静音达人"]),
        "lucky": ("🍀 幸运之星排行榜 (阳寿榜)", "闪避拉满，阎王爷也抓不到的身法仙人！", ["阳寿透支仙人", "身法大宗师", "极意绝活哥", "幸运女神干儿子", "滑铲大师", "天选之子"]),
        "deaths": ("💀 枪下亡魂排行榜 (中弹榜)", "倒地次数最多，吃席大军总指挥！", ["吃席总指挥", "人体描边标靶", "爆头体验官", "阎王老熟人", "和平使者", "先走一步"]),
        "duel": ("👑 决斗战神排行榜 (胜场榜)", "1v1 生死对决全胜，统治战局的死神！", ["战局真死神", "左轮暴徒", "决斗大宗师", "冷酷杀手", "百步穿杨", "枪斗术传人"]),
        "coins": ("💰 财富总值排行榜 (首富榜)", "全场消费由这位买单！富可敌国的大亨！", ["群聊大首富", "疯狂大亨", "行走的印钞机", "财运滔天", "金币狂魔", "富甲一方"]),
    }
    @classmethod
    def render_leaderboard_image(cls, rank_type: str, items: List[Dict[str, Any]], group_id: str = "") -> str:
        """渲染生成排行榜图片，并返回图片文件路径"""
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR, exist_ok=True)

        type_key = rank_type if rank_type in cls.TITLES_MAP else "ban_time"
        main_title, sub_title, titles_pool = cls.TITLES_MAP[type_key]

        width = 860
        header_height = 150
        row_height = 60
        footer_height = 60
        item_count = max(1, len(items))
        height = header_height + item_count * row_height + footer_height

        img = Image.new("RGB", (width, height), color="#12131C")
        draw = ImageDraw.Draw(img)

        draw.rectangle([0, 0, width, header_height - 10], fill="#1A1C28")
        draw.rectangle([0, header_height - 14, width, header_height - 10], fill="#E65100" if type_key == "ban_time" else "#2979FF")

        font_title = _get_font(28)
        font_sub = _get_font(16)
        font_rank = _get_font(20)
        font_name = _get_font(18)
        font_val = _get_font(18)
        font_badge = _get_font(14)
        font_footer = _get_font(14)

        draw.text((35, 25), main_title, font=font_title, fill="#FFFFFF")
        draw.text((37, 70), sub_title, font=font_sub, fill="#9FA8DA")
        draw.text((37, 100), f"数据范围: {group_id or '全服统计'} | 生成时间: {time.strftime('%Y-%m-%d %H:%M')}", font=font_footer, fill="#5C6BC0")

        y = header_height
        if not items:
            draw.text((width // 2 - 100, y + 20), "💤 暂无战绩数据，快去玩一把吧！", font=font_name, fill="#7986CB")
        else:
            for idx, user in enumerate(items):
                rank = idx + 1
                row_bg = "#181A26" if idx % 2 == 0 else "#141520"
                draw.rectangle([20, y, width - 20, y + row_height - 8], fill=row_bg, outline="#282A3A", width=1)

                if rank == 1:
                    badge_color = "#FFD700"
                    rank_str = "🥇 1"
                elif rank == 2:
                    badge_color = "#C0C0C0"
                    rank_str = "🥈 2"
                elif rank == 3:
                    badge_color = "#CD7F32"
                    rank_str = "🥉 3"
                else:
                    badge_color = "#7986CB"
                    rank_str = f" {rank} "

                draw.text((35, y + 14), rank_str, font=font_rank, fill=badge_color)

                name = str(user.get("nickname") or user.get("user_id") or "神秘玩家")
                if len(name) > 10:
                    name = name[:9] + "..."
                draw.text((120, y + 15), name, font=font_name, fill="#ECEFF1")

                honor_title = titles_pool[min(idx, len(titles_pool) - 1)]
                draw.rounded_rectangle([300, y + 12, 430, y + 38], radius=4, fill="#262A40")
                draw.text((310, y + 15), f"🏷️ {honor_title}", font=font_badge, fill="#FFD54F")

                if type_key == "ban_time":
                    secs = user.get("ban_seconds", 0)
                    if secs >= 3600:
                        val_str = f"{secs} 秒 ({secs // 3600}小时{(secs % 3600) // 60}分)"
                    elif secs >= 60:
                        val_str = f"{secs} 秒 ({secs // 60}分{secs % 60}秒)"
                    else:
                        val_str = f"{secs} 秒"
                    val_color = "#FF5252"
                elif type_key == "lucky":
                    dodges = user.get("dodges", 0)
                    survives = user.get("survives", 0)
                    val_str = f"{dodges} 次闪避 / {survives} 空枪"
                    val_color = "#69F0AE"
                elif type_key == "deaths":
                    deaths = user.get("deaths", 0)
                    shots = user.get("shots", 0)
                    val_str = f"中弹 {deaths} 次 (总开枪 {shots})"
                    val_color = "#FF8A80"
                elif type_key == "duel":
                    wins = user.get("duel_wins", 0)
                    losses = user.get("duel_losses", 0)
                    total = wins + losses
                    rate = f"{int(wins / total * 100)}%" if total > 0 else "0%"
                    val_str = f"{wins} 胜 {losses} 负 (胜率 {rate})"
                    val_color = "#FFD700"
                else:
                    coins = user.get("coins", 0)
                    val_str = f"{coins:,} 金币"
                    val_color = "#FFEB3B"

                draw.text((500, y + 15), val_str, font=font_val, fill=val_color)
                y += row_height

        draw.text((width // 2 - 110, height - 35), "⚡ 无欲物语 · 娱乐决斗系统", font=font_footer, fill="#3F51B5")

        output_path = os.path.join(CACHE_DIR, f"leaderboard_{type_key}_{int(time.time() * 1000)}.png")
        img.save(output_path, "PNG")
        return output_path

