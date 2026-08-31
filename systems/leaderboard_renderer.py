# -*- coding: utf-8 -*-
import html
import time
from typing import List, Dict, Any, Optional


class LeaderboardRenderer:
    """基于 HTML5 + CSS3 + AstrBot 原生 html_render 的多维度排行榜渲染器"""

    TITLES_MAP = {
        "ban_time": ("🩸 惩罚时间排行榜 (受害者榜)", "谁是进小黑屋最久的ICU终身VIP？", ["ICU终身VIP", "小黑屋常客", "闭麦艺术家", "天选受害者", "沉睡魔咒", "静音达人"]),
        "lucky": ("🍀 幸运之星排行榜 (阳寿榜)", "闪避拉满，阎王爷也抓不到的身法仙人！", ["阳寿透支仙人", "身法大宗师", "极意绝活哥", "幸运女神干儿子", "滑铲大师", "天选之子"]),
        "deaths": ("💀 枪下亡魂排行榜 (中弹榜)", "倒地次数最多，吃席大军总指挥！", ["吃席总指挥", "人体描边标靶", "爆头体验官", "阎王老熟人", "和平使者", "先走一步"]),
        "duel": ("👑 决斗战神排行榜 (胜场榜)", "1v1 生死对决全胜，统治战局的死神！", ["战局真死神", "左轮暴徒", "决斗大宗师", "冷酷杀手", "百步穿杨", "枪斗术传人"]),
        "coins": ("💰 财富总值排行榜 (首富榜)", "全场消费由这位买单！富可敌国的大亨！", ["群聊大首富", "疯狂大亨", "行走的印钞机", "财运滔天", "金币狂魔", "富甲一方"]),
    }

    @classmethod
    def generate_leaderboard_html(cls, rank_type: str, items: List[Dict[str, Any]], group_id: str = "") -> str:
        type_key = rank_type if rank_type in cls.TITLES_MAP else "ban_time"
        main_title, sub_title, titles_pool = cls.TITLES_MAP[type_key]

        accent_color = "#FF3D00" if type_key == "ban_time" else ("#00E676" if type_key == "lucky" else ("#FF5252" if type_key == "deaths" else ("#FFD700" if type_key == "duel" else "#FFC400")))

        rows_html = []
        if not items:
            rows_html.append('<div class="empty-tip">💤 暂无任何战绩数据，快去群里开一局吧！</div>')
        else:
            for idx, user in enumerate(items):
                rank = idx + 1
                name = html.escape(str(user.get("nickname") or user.get("user_id") or "神秘玩家"))
                honor_title = titles_pool[min(idx, len(titles_pool) - 1)]

                if rank == 1:
                    rank_badge = '<span class="rank-badge rank-1">🥇 1</span>'
                    row_class = "row-top row-1"
                elif rank == 2:
                    rank_badge = '<span class="rank-badge rank-2">🥈 2</span>'
                    row_class = "row-top row-2"
                elif rank == 3:
                    rank_badge = '<span class="rank-badge rank-3">🥉 3</span>'
                    row_class = "row-top row-3"
                else:
                    rank_badge = f'<span class="rank-badge rank-normal">{rank}</span>'
                    row_class = "row-normal"

                if type_key == "ban_time":
                    secs = user.get("ban_seconds", 0)
                    if secs >= 3600:
                        val_str = f"{secs} 秒 ({secs // 3600}小时{(secs % 3600) // 60}分)"
                    elif secs >= 60:
                        val_str = f"{secs} 秒 ({secs // 60}分{secs % 60}秒)"
                    else:
                        val_str = f"{secs} 秒"
                    val_class = "val-red"
                elif type_key == "lucky":
                    dodges = user.get("dodges", 0)
                    survives = user.get("survives", 0)
                    val_str = f"{dodges} 次闪避 / {survives} 次生还"
                    val_class = "val-green"
                elif type_key == "deaths":
                    deaths = user.get("deaths", 0)
                    shots = user.get("shots", 0)
                    val_str = f"中弹 {deaths} 次 (总开枪 {shots})"
                    val_class = "val-coral"
                elif type_key == "duel":
                    wins = user.get("duel_wins", 0)
                    losses = user.get("duel_losses", 0)
                    total = wins + losses
                    rate = f"{int(wins / total * 100)}%" if total > 0 else "0%"
                    val_str = f"{wins} 胜 {losses} 负 (胜率 {rate})"
                    val_class = "val-gold"
                else:
                    coins = user.get("coins", 0)
                    val_str = f"{coins:,} 金币"
                    val_class = "val-yellow"

                rows_html.append(f"""
                <div class="leaderboard-row {row_class}">
                    <div class="row-left">
                        {rank_badge}
                        <div class="user-name">{name}</div>
                        <div class="honor-tag">🏷️ {honor_title}</div>
                    </div>
                    <div class="row-right">
                        <div class="stat-pill {val_class}">{val_str}</div>
                    </div>
                </div>
                """)

        rows_joined = "".join(rows_html)
        time_str = time.strftime("%Y-%m-%d %H:%M")

        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}
body {{
    width: 800px;
    background: #0B0C10;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;
    color: #E0E6ED;
    padding: 30px;
    display: flex;
    justify-content: center;
}}
.container {{
    width: 100%;
    background: #141620;
    border-radius: 18px;
    border: 1px solid #232738;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
    overflow: hidden;
}}
.header {{
    background: linear-gradient(135deg, #1C1F2E 0%, #171926 100%);
    padding: 30px;
    border-bottom: 2px solid {accent_color};
    position: relative;
}}
.header::after {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: {accent_color};
    box-shadow: 0 0 15px {accent_color};
}}
.title {{
    font-size: 26px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}}
.subtitle {{
    font-size: 15px;
    color: #8C9BAE;
    margin-bottom: 14px;
}}
.meta-badges {{
    display: flex;
    gap: 12px;
}}
.meta-badge {{
    font-size: 12px;
    background: #232738;
    color: #7986CB;
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid #2E344A;
}}
.content {{
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}}
.leaderboard-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 18px;
    border-radius: 12px;
    background: #191B28;
    border: 1px solid #232738;
}}
.row-1 {{
    background: linear-gradient(90deg, rgba(255, 215, 0, 0.1) 0%, #191B28 100%);
    border: 1px solid rgba(255, 215, 0, 0.35);
}}
.row-2 {{
    background: linear-gradient(90deg, rgba(192, 192, 192, 0.1) 0%, #191B28 100%);
    border: 1px solid rgba(192, 192, 192, 0.35);
}}
.row-3 {{
    background: linear-gradient(90deg, rgba(205, 127, 50, 0.1) 0%, #191B28 100%);
    border: 1px solid rgba(205, 127, 50, 0.35);
}}
.row-left {{
    display: flex;
    align-items: center;
    gap: 14px;
}}
.rank-badge {{
    font-size: 18px;
    font-weight: 700;
    width: 50px;
    text-align: center;
}}
.rank-1 {{ color: #FFD700; text-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }}
.rank-2 {{ color: #E0E0E0; text-shadow: 0 0 10px rgba(224, 224, 224, 0.5); }}
.rank-3 {{ color: #FF8A65; text-shadow: 0 0 10px rgba(255, 138, 101, 0.5); }}
.rank-normal {{ color: #64748B; }}
.user-name {{
    font-size: 16px;
    font-weight: 600;
    color: #F8FAFC;
    max-width: 170px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}
.honor-tag {{
    font-size: 12px;
    background: #232738;
    color: #FFD54F;
    padding: 3px 8px;
    border-radius: 6px;
    border: 1px solid rgba(255, 213, 79, 0.2);
}}
.stat-pill {{
    font-size: 15px;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 8px;
    background: #11121A;
    border: 1px solid #232738;
}}
.val-red {{ color: #FF5252; }}
.val-green {{ color: #00E676; }}
.val-coral {{ color: #FF7043; }}
.val-gold {{ color: #FFD700; }}
.val-yellow {{ color: #FFEE58; }}
.empty-tip {{
    text-align: center;
    padding: 40px;
    color: #64748B;
    font-size: 16px;
}}
.footer {{
    padding: 16px;
    text-align: center;
    background: #11121A;
    border-top: 1px solid #1E2230;
    font-size: 13px;
    color: #5C6BC0;
}}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="title">{main_title}</div>
        <div class="subtitle">{sub_title}</div>
        <div class="meta-badges">
            <div class="meta-badge">群号: {group_id or '全服统计'}</div>
            <div class="meta-badge">生成时间: {time_str}</div>
        </div>
    </div>
    <div class="content">
        {rows_joined}
    </div>
    <div class="footer">
        ⚡ 无欲物语 · 娱乐决斗系统
    </div>
</div>
</body>
</html>"""
        return html_template

    @classmethod
    async def render_leaderboard_image(cls, context, rank_type: str, items: List[Dict[str, Any]], group_id: str = "") -> Optional[str]:
        """通过 AstrBot 原生 html_render 渲染生成超清排行榜图片"""
        html_code = cls.generate_leaderboard_html(rank_type, items, group_id)
        try:
            if hasattr(context, "html_render") and callable(context.html_render):
                img_path = await context.html_render(html_code, width=800)
                if img_path:
                    return str(img_path)

            if hasattr(context, "html_to_image") and callable(context.html_to_image):
                img_path = await context.html_to_image(html_code)
                if img_path:
                    return str(img_path)
        except Exception as e:
            print(f"[无欲物语] html_render 渲染异常: {e}")

        return None
