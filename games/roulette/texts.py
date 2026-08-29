# -*- coding: utf-8 -*-
import random
from typing import List, Dict
from .models import WeaponType, TacticalItemType


class RouletteTexts:
    """轮盘赌海量带梗台词库（每种情景/武器均包含 ≥5 种随机台词，正文无冗余@）"""

    # 1. 装填武器台词池（按武器区分，每种 5+ 种）
    LOAD_TEXTS: Dict[WeaponType, List[str]] = {
        WeaponType.REVOLVER: [
            "🔫 【{user}】优雅地把左轮手枪拍在桌上，冷笑一声：“今天在座的各位，谁赞成，谁反对？”装填了 {bullets}/{chambers} 发实弹！",
            "🔫 【{user}】帅气地转动左轮弹巢，咔哒入膛：“命运的齿轮开始转动，今天谁是那个倒霉蛋？”装填了 {bullets}/{chambers} 发实弹！",
            "🔫 【{user}】掏出祖传左轮吹了吹枪口：“生死看淡，不服就干！只要我不尴尬，阎王爷也拿我没辙！”装填了 {bullets}/{chambers} 发实弹！",
            "🔫 【{user}】眼神冷酷，缓缓压上子弹：“听说群里个个都是绝活哥？来，尝尝这 {bullets} 颗花生米的威力！”",
            "🔫 【{user}】邪魅一笑扣上击锤：“左轮转一转，亲人泪两行！今天不是你进小黑屋就是我进ICU！”装填了 {bullets}/{chambers} 发实弹！",
            "🔫 【{user}】点了支华子，把左轮递出：“哥们赌的不是命，是纯粹的刺激！谁敢接第一枪？”装填了 {bullets}/{chambers} 发实弹！"
        ],
        WeaponType.SNIPER: [
            "🎯 【{user}】扛出一柄两米长的大狙重重架在桌上：“时代变了大人！这一枪下去，你可能会直接化作天上的星星！”装填了 {bullets}/{chambers} 发重型穿甲弹！",
            "🎯 【{user}】咔哒一声拉动巴雷特枪栓：“八百里开外，一枪干掉鬼子的机枪手！谁先来试靶？”装填了 {bullets}/{chambers} 发！",
            "🎯 【{user}】扶了扶墨镜：“一枪一个小朋友，超强穿透力拉满，小心把身后的人一并带走！”装填了 {bullets}/{chambers} 发重弹！",
            "🎯 【{user}】扛起大狙深吸一口气：“众所周知，大狙也是能拿来打轮盘的！阎王点名，命中注定！”装填了 {bullets}/{chambers} 发！",
            "🎯 【{user}】拍了拍硕大的狙击镜：“这枪要是响了，禁言时长直接翻倍起步！谁敢来赌这波大的？”装填了 {bullets}/{chambers} 发！",
            "🎯 【{user}】咧嘴一笑：“巴雷特已就位！建议各位开枪前先写好遗书！”装填了 {bullets}/{chambers} 发穿甲弹！"
        ],
        WeaponType.GATLING: [
            "🔥 【{user}】单手提起了冒蓝火的重型加特林：“南无加特林菩萨，六根清净贫铀弹，一息三千六百转！”装填了 {bullets}/{chambers} 发密集弹药！",
            "🔥 【{user}】疯狂拉动加特林供弹链：“什么叫火力覆盖啊？连扣三发，大伙排好队一个个来受死！”装填了 {bullets}/{chambers} 发！",
            "🔥 【{user}】狂笑不止：“大人，时代不仅变了，而且下暴雨了！接招吧，疯狂扫射模式！”装填了 {bullets}/{chambers} 发弹药！",
            "🔥 【{user}】扛起转管机枪咆哮：“今天就让你们见识一下什么叫人体描边大师的终极形态！”装填了 {bullets}/{chambers} 发！",
            "🔥 【{user}】预热枪管发出嗡嗡轰鸣：“今晚全场的消费由中弹的公子买单！三连发开胃菜准备！”装填了 {bullets}/{chambers} 发！",
            "🔥 【{user}】狞笑一声：“15发大弹鼓已就绪！连吃三枪的勇士究竟是谁？”装填了 {bullets}/{chambers} 发密集弹药！"
        ],
        WeaponType.RPG: [
            "🚀 【{user}】扛起绿皮火箭筒对准天花板：“吃我一记正义的RPG！要么相安无事，要么全场开席！”装填了 {bullets}/{chambers} 发高爆火箭弹！",
            "🚀 【{user}】眼神极其核善：“我不吃牛肉，我只吃火箭弹！AOE范围轰炸预警，前后邻居小心了！”装填了 {bullets}/{chambers} 发！",
            "🚀 【{user}】扣上引信大喊：“全体起立！艺术就是爆炸，喝！谁来当那个爆破鬼才？”装填了 {bullets}/{chambers} 发高能弹头！",
            "🚀 【{user}】拍了拍火箭弹头：“这一炮下去，不仅扣扳机的要走，隔壁看戏的也得被冲击波抬走！”装填了 {bullets}/{chambers} 发！",
            "🚀 【{user}】扛着筒子狂笑：“虽然弹药少，但每一发都是核平使者！敢不敢来一炮？”装填了 {bullets}/{chambers} 发火箭弹！",
            "🚀 【{user}】傲视全场：“真男人从不回头看爆炸！火箭筒已上膛，谁来试爆？”装填了 {bullets}/{chambers} 发！"
        ]
    }

    # 2. 开枪·空弹生还台词（8 种）
    BLANK_TEXTS: List[str] = [
        "🎲 咔哒！【{user}】擦了擦额头冷汗：“就这？阎王爷看了我的生死簿都得当场撕两页！”",
        "🎲 咔哒！【{user}】仰天长笑：“赌上职业生涯的空枪！今天我就是天选之子，耶稣也留不住我！”",
        "🎲 咔哒！枪口冒出一缕青烟，【{user}】战术后仰：“吓死爹了，差点当场给各位表演一个大变活人！”",
        "🎲 咔哒！【{user}】邪魅一笑：“我预判了你的预判，这发绝对是哑弹！下一个受害者请就位！”",
        "🎲 咔哒！【{user}】拍了拍胸口长舒一口气：“生死时速！哥们的阳寿果然还能再续五百年！”",
        "🎲 咔哒！【{user}】摆出极度嚣张的姿势：“这就是神明的庇护吗？感觉整个人都升华了，下一个！”",
        "🎲 咔哒！击锤击空！【{user}】嘲讽道：“枪法不行就去练练，连根毛都没伤到哥！”",
        "🎲 咔哒！【{user}】摊手表示无奈：“无敌是多么寂寞，空弹已经无法满足我追求刺激的心了！”"
    ]

    # 2.1 【向自己开枪·空弹·再动一回合】高能台词（5 种）
    SELF_BLANK_TEXTS: List[str] = [
        "🎲 ✨ 咔哒！【{user}】竟然把枪口对准了自己，果断扣下扳机——是空弹！\n🔥 恶魔轮盘判定成功！【{user}】触发【命运再动】，获得额外连开一枪机会！",
        "🎲 💥 咔哒！【{user}】艺高人胆大朝自己脑袋开枪！击锤击空！\n⚡ 极致心理博弈！【{user}】赌命成功，本回合不换人，继续拥有开火权！",
        "🎲 🃏 咔哒！枪口安全！【{user}】嘴角微微上扬：“恶魔也站在我这边！”\n🎯 触发再动回合！【{user}】可继续选择向自己或对手射击！",
        "🎲 🔥 咔哒！【{user}】自瞄扣动扳机，毫发无伤！全场倒吸一口凉气！\n✨ 狂暴节奏！【{user}】获得额外开火回合，连续出击！",
        "🎲 👑 咔哒！【{user}】面不改色自崩一枪！空弹！\n🌟 赌神降临！【{user}】逆天改命获得连击开火权！"
    ]

    # 2.2 【向对面开枪·命中击倒】台词（5 种）
    OPPONENT_HIT_TEXTS: List[str] = [
        "💥 砰！枪焰喷涌！【{user}】果断将枪口指向【{target}】扣动扳机！实弹命中！【{target} 倒地送入小黑屋禁言 {duration} 秒】",
        "💥 轰！【{user}】冷笑一声一枪轰出，【{target}】猝不及防当场中弹升天！【禁言 {duration} 秒】",
        "💥 砰！子弹呼啸而出！【{user}】精准命中【{target}】天灵盖！【{target} 喜提闭麦套餐 {duration} 秒】",
        "💥 砰！【{user}】瞄准【{target}】扣下击锤，火光四射！【{target} 饮恨西北，被禁言 {duration} 秒】",
        "💥 🎯 绝杀！【{user}】这一枪直接送走了【{target}】！【小黑屋一日游 {duration} 秒】"
    ]
    # 2.3 【向对面开枪·未命中·反噬自罚一枪】台词
    COUNTER_PENALTY_HIT_TEXTS: List[str] = [
        "⚠️ 决斗反噬！【{user}】射击【{target}】击发击空，触发决斗自罚规则！\n💥 砰！枪声炸响！【{user}】自罚吃下实弹，偷鸡不成蚀把米！【小黑屋禁言 {duration} 秒】",
        "⚠️ 决斗反弹！【{user}】未能命中【{target}】，自罚一枪——💥 轰！当场玩火自焚！【禁言 {duration} 秒】",
        "⚠️ 猎人成了猎物！【{user}】空枪失误，被迫向自己扣动扳机——💥 砰！花生米下肚，直接抬走！【禁言 {duration} 秒】",
        "⚠️ 偷鸡失败！【{user}】枪口没能击中【{target}】，自罚一发——💥 砰！自己给自己表演了大变活人！【禁言 {duration} 秒】",
        "⚠️ 杀敌未成身先死！【{user}】未中目标自罚一枪，不幸命中自己！【送入ICU禁言 {duration} 秒】"
    ]

    COUNTER_PENALTY_BLANK_TEXTS: List[str] = [
        "⚠️ 决斗反噬！【{user}】未能命中【{target}】，必须向自己自罚一枪——🎲 咔哒！自罚也是空弹！【{user}】惊出一身冷汗！",
        "⚠️ 虚惊一场！【{user}】空枪后自罚一击——🎲 咔哒！枪口冒青烟，再次死里逃生！",
        "⚠️ 自罚判定！【{user}】被迫朝自己扣动扳机——🎲 咔哒！阳寿拉满，侥幸生还！",
        "⚠️ 决斗自罚！【{user}】自扣一枪，击锤击空！心脏差点跳出嗓子眼！",
        "⚠️ 命运眷顾！【{user}】自罚一发也是空枪，阎王爷直呼好家伙！"
    ]



    # 3. 开枪·中弹倒地台词（8 种通用）
    HIT_TEXTS: List[str] = [
        "💥 砰！枪声炸响！【{user}】眼前一黑，临终遗言：“等...等等，我花呗还没还呢...”【被送进ICU禁言 {duration} 秒】",
        "💥 轰！【{user}】当场去世，死因：过于自信！黑人抬棺BGM已响起，大伙开席咯！【小黑屋一日游 {duration} 秒】",
        "💥 砰！【{user}】应声倒地，颤抖着伸出手指：“刀，怒斩雪翼雕...山，豪迈冲云霄...兄弟们先走一步！”【禁言 {duration} 秒】",
        "💥 砰！【{user}】头顶冒烟直挺挺倒下：“我命由我不由...算了，下辈子投胎注意点。”【物理闭麦 {duration} 秒】",
        "💥 砰！【{user}】惨叫一声：“焯！有挂！这把绝对有透视！”【强制静音 {duration} 秒】",
        "💥 砰！【{user}】倒地前发出凄厉呐喊：“兄弟们，快帮我把我电脑浏览器历史记录删了啊啊啊！”【禁言 {duration} 秒】",
        "💥 砰！【{user}】满脸写着不可思议：“为什么受伤的总是我？难道这就是传说中的非酋体质？”【禁言 {duration} 秒】",
        "💥 砰！致命一击！【{user}】饮恨西北，化作一缕幽魂飘向天际...【小黑屋禁言 {duration} 秒】"
    ]

    # 4. 命运闪避成功台词（6 种）
    DODGE_TEXTS: List[str] = [
        "💨 唰——！子弹擦着发梢掠过，【{user}】一个滑铲：“不会吧不会吧？就这枪法也想抓我？残影闪避！”",
        "💨 叮！【{user}】战术歪头，触发被动【火云邪神】：“天下武功，唯快不破！子弹我躲过去了，你气不气？”",
        "💨 💨 【{user}】突然鬼畜抖动，完美卡进无敌帧：“只要我卡得够快，子弹就追不上我！毫发无伤！”",
        "💨 啪！【{user}】凭空掏出一枚硬币弹开了致命子弹：“不好意思，今天幸运女神在对我微笑！”",
        "💨 嗖！【{user}】身形如鬼魅：“我一个左正蹬，一个右鞭腿，大意没有闪——不对，我真闪了！”",
        "💨 ✨ 闪避奇迹！【{user}】触发绝对命运闪避，子弹擦肩而过，带走一撮空气！"
    ]

    # 5. 武器专属特效台词
    SNIPER_PIERCE_TEXTS: List[str] = [
        "🎯 💥 穿透轰鸣！巴雷特威力过于恐怖，重弹贯穿了【{user}】后，竟然直直飞向了后排围观的【{target}】！【双人连带禁言！】",
        "🎯 ⚡ 贯穿全场！【{user}】倒地的瞬间，穿甲弹撕裂空间把无辜路人【{target}】一并送上了救护车！",
        "🎯 🌪️ 一石二鸟！巴雷特大狙触发【八百里穿透】，【{user}】和【{target}】携手步入小黑屋！",
        "🎯 💥 恐怖穿透力！大狙子弹带起狂暴气流，不仅击倒了【{user}】，连身旁的【{target}】也被震晕禁言！",
        "🎯 🚀 子弹不长眼！巴雷特贯穿伤害触发，【{user}】倒地，【{target}】躺枪双双被抬走！"
    ]

    GATLING_BURST_TEXTS: List[str] = [
        "🔥 哒哒哒！加特林疯狂扫射三连发！【{user}】身陷枪林弹雨之中...",
        "🔥 狂暴倾泻！加特林冒着蓝火连续喷射三发！硝烟弥漫...",
        "🔥 一息三千六百转！加特林三连射咆哮开火，这波火力太凶猛了！",
        "🔥 扫射风暴！【{user}】连续扣动三下扳机，火花在弹膛中疯狂闪烁！",
        "🔥 哒哒哒哒！加特林三发暴风骤雨般射出，全场心跳骤停！"
    ]

    RPG_AOE_TEXTS: List[str] = [
        "🚀 💥 轰隆隆隆！RPG火箭弹当场殉爆！不仅【{user}】被炸飞，剧烈的冲击波还把路过的【{target}】炸了个底朝天！【双人爆炸禁言！】",
        "🚀 🌋 艺术就是爆炸！核能RPG引爆全场，【{user}】升天的同时，拉上了吃瓜群众【{target}】一起看烟花！",
        "🚀 💥 范围溅射！火箭弹在人群中炸开巨大的蘑菇云，【{user}】与【{target}】携手喜提禁言套餐！",
        "🚀 🌪️ 轰——！RPG威力太大掀翻了整个群聊，【{user}】倒地，而倒霉蛋【{target}】被弹片命中连带退场！",
        "🚀 💣 核爆现场！【{user}】一炮轰出，产生的余波直接把【{target}】送进了隔壁病房！"
    ]

    # 6. 管理员/群主中弹免疫台词（5 种）
    ADMIN_IMMUNITY_TEXTS: List[str] = [
        "🛡️ 铛——！子弹打在【{user}】身上火花四溅：“可恶，这就是传说中的【群管金刚不坏之躯】吗？物理禁言免疫！”",
        "🛡️ 【{user}】拍了拍三级防弹头盔冷笑一声：“想禁言本管理？回去多练练权限再来吧！”【特权免禁】",
        "🛡️ 砰！子弹被管理员威严当场震碎！【{user}】毫发无损，甚至想反手给枪来个禁言！",
        "🛡️ 【{user}】掏出管理员令牌挡住子弹：“雕虫小技，竟敢班门弄斧！权限护体，万毒不侵！”",
        "🛡️ 💥 枪响了，但【{user}】头顶浮现四个大字【免疫伤害】：“在群里，我就是规则本身！”"
    ]

    # 7. 被动走火台词（5 种）
    MISFIRE_TEXTS: List[str] = [
        "💥 砰！桌上的枪突然走火！【{user}】发消息时不小心踢到了扳机，不幸中弹倒地！【禁言 {duration} 秒】",
        "💥 砰！手枪发生诡异走火！正欢快水群的【{user}】飞来横祸，当场中弹躺枪！【禁言 {duration} 秒】",
        "💥 砰！枪管过热走火！子弹精准找到了正在发言的【{user}】，瞬间物理闭麦！【禁言 {duration} 秒】",
        "💥 轰！走火事故发生！【{user}】甚至不知道发生了什么，就已被抬上了救护车！【禁言 {duration} 秒】",
        "💥 砰！走火警报！【{user}】被飞出的流弹击中天灵盖，含泪领了小黑屋门票！【禁言 {duration} 秒】"
    ]


    # 8. 突发战术道具空投台词（每种 5 种）
    TACTICAL_ITEM_DROPS: Dict[TacticalItemType, List[str]] = {
        TacticalItemType.STICKY_BOMB: [
            "💣 哔哔哔！机器人恶作剧扔出一枚【粘性炸弹】，“啪”地死死粘在了【{user}】的脑门上！‘击鼓传花开始，下一个开枪的人接盘！’",
            "💣 突发事件！机器人向人群扔了一颗滴答倒计时的【粘性炸弹】，黏在了【{user}】背后！‘快传出去，马上要炸了！’",
            "💣 警告！【{user}】身上被挂上了一枚【粘性炸弹】，引信正在疯狂燃烧！‘谁来当接盘侠？’",
            "💣 机器人空投了一枚【粘性炸弹】精准吸附在【{user}】身上！‘倒计时启动，下一个开枪者继承炸弹！’",
            "💣 啪嗒！一枚冒着红光的【粘性炸弹】黏住了【{user}】！‘击鼓传花，谁开枪传给谁！’"
        ],
        TacticalItemType.SMOKE_GRENADE: [
            "💨 嗤——！机器人直接掀翻桌子扔出【战术烟雾弹】：‘全场白茫茫，瞎子打盲盒模式开启！下一枪看谁运气好！’",
            "💨 浓烟滚滚！机器人打翻了【烟雾罐】：‘咳咳咳...谁放的毒烟？现在谁也看不清剩余弹药了！’",
            "💨 💨 战术掩护！机器人扔出高浓度烟雾：‘烟中恶鬼降临！浓烟掩护，战场进入迷雾状态！’",
            "💨 嗤嗤！一枚【战术烟雾弹】在人群中炸开，满屏白烟让所有人视野受阻！",
            "💨 烟雾弥漫！机器人大喊：‘战术撤退！’下一位开枪者将在烟雾迷障中摸黑开火！"
        ],
        TacticalItemType.FLASHBANG: [
            "⚡ 嗡——！机器人反手扔出一枚【强光闪光弹】：‘看我白给一击！’全场瞬间白屏，【{user}】被闪瞎了双眼，闪避率归零！",
            "⚡ 闪光突袭！‘啊！我的眼睛！是谁在眼前遮住了帘！’【{user}】眼前一片雪白，手抖得拿不住枪！",
            "⚡ ⚡ 机器人扔出了亮瞎全场的【闪光弹】：‘大白天放闪光是吧！’下一位受害者命中判定大幅恶化！",
            "⚡ 强光暴击！全场被闪光弹致盲，【{user}】捂着双眼惨叫：‘我什么都看不见了！’",
            "⚡ 闪光降临！致盲强光让现场陷入混乱，所有防御身法暂时失效！"
        ]
    }

    # 8.1 粘性炸弹传递台词（5 种）
    STICKY_BOMB_PASS_TEXTS: List[str] = [
        "💣 啪！【{old_user}】趁开枪的瞬间，眼疾手快把【粘性炸弹】一把拍到了【{new_user}】身上！引信还剩 {remaining} 次！",
        "💣 战术转移！【{old_user}】甩锅成功，把背上的【粘性炸弹】顺手挂在了【{new_user}】头顶！剩余倒计时：{remaining}！",
        "💣 击鼓传花！【{old_user}】像扔烫手山芋一样把炸弹抛给了【{new_user}】！‘兄弟，该你接盘了！’【剩余 {remaining} 次】",
        "💣 移花接木！【{new_user}】刚准备开枪，身上就被【{old_user}】塞了一枚倒计时的炸弹！【剩余 {remaining} 次】",
        "💣 炸弹交接！【{old_user}】嘿嘿一笑把炸弹贴在【{new_user}】背后：‘好兄弟有难同当！’【剩余 {remaining} 次】"
    ]

    # 8.2 粘性炸弹引爆台词（5 种）
    STICKY_BOMB_EXPLODE_TEXTS: List[str] = [
        "💣 💥 轰隆！【粘性炸弹】引信燃尽，在【{user}】怀里轰然爆炸！当场炸成小黑人！【被炸进ICU禁言 {duration} 秒】",
        "💣 💥 滴滴滴——砰！粘性炸弹爆裂！【{user}】终究没能传出去，被炸上了天花板！【禁言 {duration} 秒】",
        "💣 💥 倒计时归零！‘完了芭比Q了！’【{user}】在火光中化作焦炭！【小黑屋禁言 {duration} 秒】",
        "💣 💥 艺术就是派大星！粘性炸弹在【{user}】头顶炸开一朵美丽的烟花！【禁言 {duration} 秒】",
        "💣 💥 轰！接盘侠诞生！【{user}】怀抱炸弹光荣退场，吃席大军已就位！【禁言 {duration} 秒】"
    ]

    # 9. 异能命格抽取台词（5 种）
    TALENT_DRAW_TEXTS: List[str] = [
        "✨ 【{user}】沐浴更衣洗了洗手，逆天改命抽中了 【{rarity}·{name}】（{tag}）！\n📜 命格效果：{desc}",
        "🔮 命运轮盘转动！【{user}】获得了神秘命格 【{rarity}·{name}】（{tag}）！\n📜 命格效果：{desc}",
        "🌟 天地异象！【{user}】觉醒了专属异能 【{rarity}·{name}】（{tag}）！\n📜 命格效果：{desc}",
        "🎲 抽奖完成！【{user}】本局获得了命格 【{rarity}·{name}】（{tag}）！\n📜 命格效果：{desc}",
        "🃏 命格觉醒！【{user}】翻开了命运底牌：【{rarity}·{name}】（{tag}）！\n📜 命格效果：{desc}"
    ]

    # 9.1 异能具体触发梗台词
    TALENT_TRIGGER_TEXTS: Dict[str, List[str]] = {
        "sugar_daddy": [
            "🛡️ 扑通！中弹瞬间，【{user}】毫无尊严地跪倒在地大喊：“义父救我！” 站在一旁的【{target}】还没反应过来，就被拉去挡了致命一枪！【{target} 替死中弹禁言！】",
            "🛡️ 替罪羊触发！【{user}】大喊：“有请下一位大冤种！” 顺手把【{target}】推到了枪口前！【{target} 替死禁言！】",
            "🛡️ 移花接木！【{user}】发动【义父救我】，将致命伤害强行转移给了【{target}】！"
        ],
        "parry_master": [
            "⚔️ 铛——！金铁交鸣之声响彻全场！【{user}】掏出平底锅完成了一记完美弹反（Parry）：“你的子弹很不错，现在原路奉还！” 子弹反弹击中了装弹者【{target}】！【反伤中弹禁言！】",
            "⚔️ 弹反成功！【{user}】眼神一凛，反手将子弹打回，装弹者【{target}】当场自食其果！",
            "⚔️ 铛！完美弹刀！【{user}】触发神级弹反，子弹原路逆流轰碎了【{target}】的防线！"
        ],
        "hp_lock": [
            "🛡️ ✨ 名刀·司命触发！致命子弹击中【{user}】的瞬间亮起一道金光，强制锁血 1 点，免疫了本次中弹！“只要我不死，我就能翻盘！”",
            "🛡️ 挂壁现身！【{user}】触发【锁血挂壁】，硬生生抗下了实弹，子弹被护盾弹飞！",
            "🛡️ 金身不灭！【{user}】触发保命神技，本次致命中弹被系统强制判定无效！"
        ],
        "mambo_reversal": [
            "🔮 ✨ 曼波因果逆转触发！遭遇实弹瞬间，【{user}】发动神秘魔法，膛室内的真子弹瞬间化为青烟哑火！“曼波曼波，化险为夷！”",
            "🔮 🌀 奇迹逆转！【{user}】触发【曼波·因果逆转】，致命实弹被强行扭转为哑弹！毫发无伤！",
            "🔮 ✨ 因果篡改！【{user}】念动咒语，实弹当场变成哑弹！逃过一劫！"
        ],
        "fifty_fifty_kill": [
            "💀 💥 五五开强行一换一触发！【{user}】倒地瞬间狞笑一声：“五五开，我走了你也别想活！” 因果律反噬，【{target}】一同被实弹击中升天！【双双禁言！】",
            "💀 ⚖️ 强行一换一！【{user}】中弹倒地，同时拉上【{target}】同归于尽！",
            "💀 💥 绝对五五开！【{user}】倒地触发因果律武器，【{target}】连带被抬走！"
        ],
        "devil_gambler": [
            "😈 🔥 恶魔赌徒·致命双响触发！【{user}】这一枪附带恶魔诅咒，【{target}】禁言时间额外延长 50%，并被顺走 50 金币！",
            "😈 💰 致命双响！【{user}】痛击【{target}】，追加 50% 禁言惩罚并当场掠夺 50 金币！",
            "😈 💥 恶魔收割！【{target}】遭受双倍痛苦，禁言延长且金币被讹！"
        ],
        "nuclear_boom": [
            "💥 💣 原地核爆启动！【{user}】倒地前狞笑着按下了起爆电门：“既然我活不了，那大家就都别想活！” 轰！拉上了路人【{target}】一同升天！",
            "💥 💥 疯狂自爆！【{user}】触发【原地核爆】，恐怖的殉爆冲击波把【{target}】一并炸进了小黑屋！",
            "💥 🌋 同归于尽！【{user}】倒地引爆核手雷，与【{target}】双双殉情化作灰烬！"
        ],
        "stubborn_mouth": [
            "💀 【{user}】虽倒在血泊中，但依然咬紧牙关高声呐喊：“其实我一点都不痛，哥们还能再抗十发！”【禁言时间减半！】",
            "💀 嘴硬至死！【{user}】中弹倒地前留下遗言：“刀怒斩雪翼雕，哥们只是在闭目养神！”【禁言时长减半！】",
            "💀 骨头断了嘴还硬！【{user}】倒地发出狂笑：“这就完了？不过如此！”【禁言减免 50%！】"
        ],
        "crazy_thursday": [
            "🍗 咔哒！开出空枪！【{user}】狂喜大喊：“活着就是赚到！今天是疯狂星期四，V 我 50 庆祝一下！金币翻倍到账！”",
            "🍗 疯狂星期四狂欢！【{user}】逃过一劫，不仅毫发无损，还赚取了双倍金币！",
            "🍗 财运亨通！【{user}】避开实弹，触发疯狂星期四特权，金币狂飙！"
        ],
        "extortionist": [
            "💰 啪叽！【{user}】倒地后立刻以八十迈速度抱住装弹者【{target}】的大腿哭嚎：“哎哟喂！杀人啦！没有 100 金币今天这事没完！”【成功碰瓷讹走 100 金币！】",
            "💰 专业碰瓷触发！【{user}】虽被禁言，但强行从【{target}】兜里掏走了 100 金币作为医药费！",
            "💰 倒地讹钱！【{user}】临倒地前精准碰瓷，从【{target}】身上划扣了 100 赔偿金！"
        ]
    }


    # 10. 弹药耗尽 / 游戏平局 / 结算台词（5 种）
    EMPTY_MAGAZINE_TEXTS: List[str] = [
        "🏁 咔哒！弹巢所有膛室已全部击发！所有生还者举杯狂欢，本次对决圆满落幕！",
        "🏁 弹药耗尽！枪管发烫冒烟，本轮所有勇士成功存活，阎王爷今天空手而归！",
        "🏁 轮盘旋转停止！弹膛已空，存活的勇士们瓜分了战局荣耀！",
        "🏁 战火平息！子弹全部打完，感谢各位绝活哥的精彩表演！",
        "🏁 鸣金收兵！弹药告罄，恭喜所有活下来的兄弟，大难不死必有后福！"
    ]

    @classmethod
    def get_load_text(cls, weapon_type: WeaponType, user: str, bullets: int, chambers: int) -> str:
        templates = cls.LOAD_TEXTS.get(weapon_type, cls.LOAD_TEXTS[WeaponType.REVOLVER])
        return random.choice(templates).format(
            user=user,
            bullets=bullets,
            chambers=chambers,
            weapon=weapon_type.value
        )

    @classmethod
    def get_blank_text(cls, user: str) -> str:
        return random.choice(cls.BLANK_TEXTS).format(user=user)

    @classmethod
    def get_self_blank_text(cls, user: str) -> str:
        return random.choice(cls.SELF_BLANK_TEXTS).format(user=user)

    @classmethod
    def get_opponent_hit_text(cls, user: str, target: str, duration: int) -> str:
        return random.choice(cls.OPPONENT_HIT_TEXTS).format(user=user, target=target, duration=duration)
    @classmethod
    def get_counter_penalty_hit_text(cls, user: str, target: str, duration: int) -> str:
        return random.choice(cls.COUNTER_PENALTY_HIT_TEXTS).format(user=user, target=target, duration=duration)

    @classmethod
    def get_counter_penalty_blank_text(cls, user: str, target: str) -> str:
        return random.choice(cls.COUNTER_PENALTY_BLANK_TEXTS).format(user=user, target=target)


    @classmethod
    def get_hit_text(cls, user: str, duration: int) -> str:
        return random.choice(cls.HIT_TEXTS).format(user=user, duration=duration)

    @classmethod
    def get_dodge_text(cls, user: str) -> str:
        return random.choice(cls.DODGE_TEXTS).format(user=user)

    @classmethod
    def get_sniper_pierce_text(cls, user: str, target: str) -> str:
        return random.choice(cls.SNIPER_PIERCE_TEXTS).format(user=user, target=target)

    @classmethod
    def get_gatling_burst_text(cls, user: str) -> str:
        return random.choice(cls.GATLING_BURST_TEXTS).format(user=user)

    @classmethod
    def get_rpg_aoe_text(cls, user: str, target: str) -> str:
        return random.choice(cls.RPG_AOE_TEXTS).format(user=user, target=target)

    @classmethod
    def get_admin_immunity_text(cls, user: str) -> str:
        return random.choice(cls.ADMIN_IMMUNITY_TEXTS).format(user=user)

    @classmethod
    def get_misfire_text(cls, user: str, duration: int) -> str:
        return random.choice(cls.MISFIRE_TEXTS).format(user=user, duration=duration)

    @classmethod
    def get_tactical_drop_text(cls, item_type: TacticalItemType, user: str) -> str:
        templates = cls.TACTICAL_ITEM_DROPS.get(item_type, cls.TACTICAL_ITEM_DROPS[TacticalItemType.STICKY_BOMB])
        return random.choice(templates).format(user=user)

    @classmethod
    def get_sticky_pass_text(cls, old_user: str, new_user: str, remaining: int) -> str:
        return random.choice(cls.STICKY_BOMB_PASS_TEXTS).format(
            old_user=old_user,
            new_user=new_user,
            remaining=remaining
        )

    @classmethod
    def get_sticky_explode_text(cls, user: str, duration: int) -> str:
        return random.choice(cls.STICKY_BOMB_EXPLODE_TEXTS).format(user=user, duration=duration)

    @classmethod
    def get_talent_draw_text(cls, user: str, rarity: str, name: str, tag: str, desc: str) -> str:
        return random.choice(cls.TALENT_DRAW_TEXTS).format(
            user=user,
            rarity=rarity,
            name=name,
            tag=tag,
            desc=desc
        )

    @classmethod
    def get_talent_trigger_text(cls, talent_id: str, user: str, target: str = "") -> str:
        templates = cls.TALENT_TRIGGER_TEXTS.get(talent_id)
        if not templates:
            return ""
        return random.choice(templates).format(user=user, target=target)

    @classmethod
    def get_empty_magazine_text(cls) -> str:
        return random.choice(cls.EMPTY_MAGAZINE_TEXTS)



