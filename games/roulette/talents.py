# -*- coding: utf-8 -*-
import random
from typing import List, Optional
from .models import Talent

TALENT_POOL: List[Talent] = [
    Talent(
        id="ultra_dodge",
        name="极意·闪避拉满",
        description="身法如电！本局闪避率直接提升至 40%，残影绝活哥！",
        tag="神技",
        rarity="SSR",
        dodge_bonus=0.40
    ),
    Talent(
        id="sugar_daddy",
        name="义父救我 (替死)",
        description="中弹瞬间扑通跪地！有 60% 几率抓取上一位开枪者或对手代为替死禁言！",
        tag="神技",
        rarity="SSR",
        transfer_chance=0.60
    ),
    Talent(
        id="parry_master",
        name="弹反大师 (Parry)",
        description="平底锅护体！中弹瞬间有 30% 几率触发完美弹反，子弹原路射回击中装弹者！",
        tag="神技",
        rarity="SSR",
        parry_chance=0.30
    ),
    Talent(
        id="hp_lock",
        name="锁血挂壁",
        description="开局自带名刀·司命！本局受到第一次致命实弹时强制免疫中弹！",
        tag="神技",
        rarity="SR",
        hp_lock=True
    ),
    Talent(
        id="mambo_reversal",
        name="曼波·因果逆转",
        description="曼波魔法！遭遇实弹判定时有 45% 几率直接将实弹逆转为哑弹，化险为夷！",
        tag="神技",
        rarity="SR",
        reverse_bullet_chance=0.45
    ),
    Talent(
        id="fifty_fifty_kill",
        name="五五开·强行一换一",
        description="因果律武器！若自己中弹倒地，有 50% 几率强行拉上对手一同被禁言一换一！",
        tag="搞怪",
        rarity="SR",
        fifty_fifty_kill=True
    ),
    Talent(
        id="devil_gambler",
        name="恶魔赌徒·致命双响",
        description="心狠手辣！命中对手时实弹禁言时长额外提升 50%，并掠夺对方 50 金币！",
        tag="策略",
        rarity="SR",
        opponent_extra_ban=0.50
    ),
    Talent(
        id="nuclear_boom",
        name="原地核爆 (自爆)",
        description="大伙一起走！如果中弹倒地，引爆全身手雷，拉上随机 1 位路人一起进小黑屋！",
        tag="搞怪",
        rarity="SR",
        suicide_aoe=True
    ),
    Talent(
        id="stubborn_mouth",
        name="嘴硬王者",
        description="只要我不承认我就没输！中弹禁言时间直接减少 50%，且触发最硬遗言！",
        tag="搞怪",
        rarity="SR",
        ban_reduction=0.50
    ),
    Talent(
        id="crazy_thursday",
        name="疯狂星期四",
        description="活着就是赚到！每次扣动空枪获得双倍金币，并触发 V 我 50 庆祝！",
        tag="经济",
        rarity="R",
        coin_multiplier=2.0
    ),
    Talent(
        id="extortionist",
        name="专业碰瓷",
        description="倒地就抱大腿！若中弹，强行从装弹者身上碰瓷讹走 100 金币！",
        tag="经济",
        rarity="R",
        extortion=True
    ),
    Talent(
        id="jittery_hands",
        name="手抖症候群",
        description="手抖得像帕金森！开枪时有 25% 几率一不小心连续扣动两枪！",
        tag="负面",
        rarity="N",
        double_shot_chance=0.25
    ),
    Talent(
        id="pure_curse",
        name="纯真体质 (非酋)",
        description="霉运附体！闪避率直接归零，枪口似乎总是自动对准你的天灵盖！",
        tag="负面",
        rarity="N",
        dodge_bonus=-1.0
    )
]


def draw_random_talent() -> Talent:
    """抽取随机命格异能"""
    weights = []
    for t in TALENT_POOL:
        if t.rarity == "SSR":
            weights.append(10)
        elif t.rarity == "SR":
            weights.append(25)
        elif t.rarity == "R":
            weights.append(35)
        else:
            weights.append(30)
    return random.choices(TALENT_POOL, weights=weights, k=1)[0]

