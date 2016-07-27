from __future__ import print_function
from __future__ import unicode_literals
import os
import re
import json

class emoji():

    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'

    def __init__(self):

        self.dingbats = {} # 雜錦符號
        self.dingbats_keynames = ["雜錦", "十字架", "星號與雪花", "紋飾", "標點符號", "括號", "數字", "箭頭", "數學符號"]
  
        for i in range(0x2700, 0x27C0): # 雜錦符號 (Dingbats)
            if i in range(0x2700, 0x2719) or i in range(0x274C, 0x275B) or i in range(0x27B0, 0x27B1) or i in range(0x27BF, 0x27C0): # 雜錦
                try:
                    self.dingbats["miscellaneous"].append(chr(i))
                except KeyError:
                    self.dingbats["miscellaneous"] = [chr(i)]
            elif i in range(0x2719, 0x2721): # 十字架
                try:
                    self.dingbats["crosses"].append(chr(i))
                except KeyError:
                    self.dingbats["crosses"] = [chr(i)]
            elif i in range(0x2721, 0x273E) or i in range(0x2742, 0x274C): # 星號與雪花
                try:
                    self.dingbats["starsandsnows"].append(chr(i))
                except KeyError:
                    self.dingbats["starsandsnows"] = [chr(i)]
            elif i in range(0x273E, 0x2742) or i in range(0x2766, 0x2768): # 紋飾
                try:
                    self.dingbats["fleurons"].append(chr(i))
                except KeyError:
                    self.dingbats["fleurons"] = [chr(i)]
            elif i in range(0x275B, 0x2766): # 標點符號
                try:
                    self.dingbats["punctuationmarks"].append(chr(i))
                except KeyError:
                    self.dingbats["punctuationmarks"] = [chr(i)]
            elif i in range(0x2768, 0x2776): # 括號
                try:
                    self.dingbats["brackets"].append(chr(i))
                except KeyError:
                    self.dingbats["brackets"] = [chr(i)]
            elif i in range(0x2776, 0x2794): # 數字
                try:
                    self.dingbats["digits"].append(chr(i))
                except KeyError:
                    self.dingbats["digits"] = [chr(i)]
            elif i in range(0x2794, 0x2795) or i in range(0x2798, 0x27B0) or i in range(0x27B1, 0x27BF): # 箭頭
                try:
                    self.dingbats["arrows"].append(chr(i))
                except KeyError:
                    self.dingbats["arrows"] = [chr(i)]
            elif i in range(0x2795, 0x2798): # 數學符號
                try:
                    self.dingbats["arithmetics"].append(chr(i))
                except KeyError:
                    self.dingbats["arithmetics"] = [chr(i)]

# 僅 Segoe UI Symbol 支援, 候選清單顯示為方格, 故暫時屏敝。
#
#        for i in range(0x1F650, 0x1F680): # 雜錦符號 (Ornamental Dingbats)
#            if i in range(0x1F650, 0x1F668) or i in range(0x1F668, 0x1F66C): # 紋飾
#                try:
#                    self.dingbats["fleurons"].append(chr(i))
#                except KeyError:
#                    self.dingbats["fleurons"] = [chr(i)]
#            elif i in range(0x1F66C, 0x1F670): # 火箭
#                try:
#                    self.dingbats["rockets"].append(chr(i))
#                except KeyError:
#                    self.dingbats["rockets"] = [chr(i)]
#            elif i in range(0x1F670, 0x1F676) or i in range(0x1F67E, 0x1F680): # 雜錦
#                try:
#                    self.dingbats["miscellaneous"].append(chr(i))
#                except KeyError:
#                    self.dingbats["miscellaneous"] = [chr(i)]
#            elif i in range(0x1F676, 0x1F67E): # 標點符號
#                try:
#                    self.dingbats["punctuationmarks"].append(chr(i))
#                except KeyError:
#                    self.dingbats["punctuationmarks"] = [chr(i)]

        self.emoticons = {} # 表情符號
        self.emoticons_keynames = ["表情", "貓咪", "動物", "手勢"]

        for i in range(0x1F600, 0x1F650): # 表情符號 (Emoticons)
            if i in range(0x1F600, 0x1F638) or i in range(0x1F641, 0x1F645): # 表情
                try:
                    self.emoticons["faces"].append(chr(i))
                except KeyError:
                    self.emoticons["faces"] = [chr(i)]
            elif i in range(0x1F638, 0x1F641): # 貓咪
                try:
                    self.emoticons["catfaces"].append(chr(i))
                except KeyError:
                    self.emoticons["catfaces"] = [chr(i)]
            elif i in range(0x1F645, 0x1F650): # 手勢
                try:
                    self.emoticons["gesture"].append(chr(i))
                except KeyError:
                    self.emoticons["gesture"] = [chr(i)]

        self.miscellaneous = {} # 其它符號
        self.miscellaneous_keynames = (["天氣與占星", "其它符號", "棋牌與博弈", "指向符號", "警告標誌", "醫療符號", "宗教與政治", "易經八掛", "表情符號",
                                        "星座符號", "音樂符號", "十字架", "資源回收筒", "地圖指標", "性別符號", "圈號與星號", "系譜符號", "體育運動", "交通標誌"])

        for i in range(0x2600, 0x2700): # 其它符號 (Miscellaneous Symbols)
            if (i in range(0x2600, 0x260E) or i in range(0x2614, 0x2615) or i in range(0x263C, 0x263D) or i in range(0x263D, 0x2648) or
                i in range(0x26B3, 0x26BD) or i in range(0x26C4, 0x26C9) or i in range(0x26E2, 0x26E3)): # 天氣與占星
                try:
                    self.miscellaneous["weathers"].append(chr(i))
                except KeyError:
                    self.miscellaneous["weathers"] = [chr(i)]
            elif (i in range(0x260E, 0x2614) or i in range(0x2615, 0x2616) or i in range(0x2618, 0x261A) or i in range(0x2638, 0x2639) or
                i in range(0x2668, 0x2669) or i in range(0x267E, 0x2680) or i in range(0x2686, 0x268A) or i in range(0x269C, 0x26A0)): # 其它符號
                try:
                    self.miscellaneous["miscellaneous"].append(chr(i))
                except KeyError:
                    self.miscellaneous["miscellaneous"] = [chr(i)]
            elif (i in range(0x2616, 0x2618) or i in range(0x2654, 0x2660) or i in range(0x2660, 0x2668) or i in range(0x2680, 0x2686) or
                i in range(0x26C0, 0x26C4) or i in range(0x26C9, 0x26CC)): # 棋牌與博弈
                try:
                    self.miscellaneous["chess"].append(chr(i))
                except KeyError:
                    self.miscellaneous["chess"] = [chr(i)]
            elif i in range(0x261A, 0x2620): # 指向符號
                try:
                    self.miscellaneous["pointinghand"].append(chr(i))
                except KeyError:
                    self.miscellaneous["pointinghand"] = [chr(i)]
            elif i in range(0x2620, 0x2624) or i in range(0x26A0, 0x26A2): # 警告標誌
                try:
                    self.miscellaneous["warningsigns"].append(chr(i))
                except KeyError:
                    self.miscellaneous["warningsigns"] = [chr(i)]
            elif i in range(0x2624, 0x2626): # 醫療符號
                try:
                    self.miscellaneous["medical"].append(chr(i))
                except KeyError:
                    self.miscellaneous["medical"] = [chr(i)]
            elif i in range(0x2626, 0x2630): # 宗教與政治
                try:
                    self.miscellaneous["religiousandpolitical"].append(chr(i))
                except KeyError:
                    self.miscellaneous["religiousandpolitical"] = [chr(i)]
            elif i in range(0x2630, 0x2638) or i in range(0x268A, 0x2690): # 易經八掛
                try:
                    self.miscellaneous["yijingtrigram"].append(chr(i))
                except KeyError:
                    self.miscellaneous["yijingtrigram"] = [chr(i)]
            elif i in range(0x2639, 0x263C): # 表情符號
                try:
                    self.miscellaneous["emoticons"].append(chr(i))
                except KeyError:
                    self.miscellaneous["emoticons"] = [chr(i)]
            elif i in range(0x2648, 0x2654) or i in range(0x26CE, 0x26CF): # 星座符號
                try:
                    self.miscellaneous["zodiacal"].append(chr(i))
                except KeyError:
                    self.miscellaneous["zodiacal"] = [chr(i)]
            elif i in range(0x2669, 0x2670): # 音樂符號
                try:
                    self.miscellaneous["musical"].append(chr(i))
                except KeyError:
                    self.miscellaneous["musical"] = [chr(i)]
            elif i in range(0x2670, 0x2672): # 十字架
                try:
                    self.miscellaneous["syriaccross"].append(chr(i))
                except KeyError:
                    self.miscellaneous["syriaccross"] = [chr(i)]
            elif i in range(0x2672, 0x267E): # 資源回收筒
                try:
                    self.miscellaneous["recycling"].append(chr(i))
                except KeyError:
                    self.miscellaneous["recycling"] = [chr(i)]
            elif i in range(0x2690, 0x269C) or i in range(0x26E3, 0x26E4) or i in range(0x26E8, 0x2700): # 地圖指標
                try:
                    self.miscellaneous["map"].append(chr(i))
                except KeyError:
                    self.miscellaneous["map"] = [chr(i)]
            elif i in range(0x26A2, 0x26AA) or i in range(0x26B2, 0x26B3): # 性別符號
                try:
                    self.miscellaneous["gender"].append(chr(i))
                except KeyError:
                    self.miscellaneous["gender"] = [chr(i)]
            elif i in range(0x26AA, 0x26AD) or i in range(0x26E4, 0x26E8): # 圈號與星號
                try:
                    self.miscellaneous["circlesandpentagram"].append(chr(i))
                except KeyError:
                    self.miscellaneous["circlesandpentagram"] = [chr(i)]
            elif i in range(0x26AD, 0x26B2): # 系譜符號
                try:
                    self.miscellaneous["genealogical"].append(chr(i))
                except KeyError:
                    self.miscellaneous["genealogical"] = [chr(i)]
            elif i in range(0x26BD, 0x26BF): # 體育運動
                try:
                    self.miscellaneous["sport"].append(chr(i))
                except KeyError:
                    self.miscellaneous["sport"] = [chr(i)]
            elif i in range(0x26CC, 0x26CE) or i in range(0x26CF, 0x26E2): # 交通標誌
                try:
                    self.miscellaneous["trafficsigns"].append(chr(i))
                except KeyError:
                    self.miscellaneous["trafficsigns"] = [chr(i)]

        self.pictographs = {} # 圖形符號
        self.pictographs_keynames = (["人物", "動物", "植物", "浪漫", "愛心", "漫畫風格", "聊天泡泡", "天氣與風景", "地球", "日月星辰", "食物與餐具", "水果與蔬菜",
                                        "飲料", "慶典", "音樂", "娛樂", "遊戲", "體育", "建築與地標", "旗標", "其它", "臉部", "手部", "服飾", "個人護理",
                                        "醫療", "滿分", "金錢", "辦公", "通訊", "影音", "宗教", "使用者介面", "文字指標", "工具", "幾何形狀", "時鐘", "電腦"])
        self.modifiercolor = [] # 調色盤

        for i in range(0x1F300, 0x1F600): # 圖形符號 (Miscellaneous Symbols and Pictographs)
            if i in range(0x1F300, 0x1F30D) or i in range(0x1F321, 0x1F32D): # 天氣與風景
                try:
                    self.pictographs["weatherandlandscape"].append(chr(i))
                except KeyError:
                    self.pictographs["weatherandlandscape"] = [chr(i)]
            elif i in range(0x1F30D, 0x1F311): # 地球
                try:
                    self.pictographs["globe"].append(chr(i))
                except KeyError:
                    self.pictographs["globe"] = [chr(i)]
            elif i in range(0x1F311, 0x1F321): # 日月星辰
                try:
                    self.pictographs["moonsunandstar"].append(chr(i))
                except KeyError:
                    self.pictographs["moonsunandstar"] = [chr(i)]
            elif i in range(0x1F32D, 0x1F330) or i in range(0x1F354, 0x1F375) or i in range(0x1F37D, 0x1F37E): # 食物與餐具
                try:
                    self.pictographs["food"].append(chr(i))
                except KeyError:
                    self.pictographs["food"] = [chr(i)]
            elif i in range(0x1F330, 0x1F345): # 植物
                try:
                    self.pictographs["plant"].append(chr(i))
                except KeyError:
                    self.pictographs["plant"] = [chr(i)]
            elif i in range(0x1F345, 0x1F354): # 水果與蔬菜
                try:
                    self.pictographs["fruitandvegetable"].append(chr(i))
                except KeyError:
                    self.pictographs["fruitandvegetable"] = [chr(i)]
            elif i in range(0x1F375, 0x1F37D) or i in range(0x1F37E, 0x1F380): # 飲料
                try:
                    self.pictographs["beverage"].append(chr(i))
                except KeyError:
                    self.pictographs["beverage"] = [chr(i)]
            elif i in range(0x1F380, 0x1F398): # 慶典
                try:
                    self.pictographs["celebration"].append(chr(i))
                except KeyError:
                    self.pictographs["celebration"] = [chr(i)]
            elif i in range(0x1F398, 0x1F39E) or i in range(0x1F3B5, 0x1F3BD): # 音樂
                try:
                    self.pictographs["musical"].append(chr(i))
                except KeyError:
                    self.pictographs["musical"] = [chr(i)]
            elif i in range(0x1F39E, 0x1F3AE): # 娛樂
                try:
                    self.pictographs["entertainment"].append(chr(i))
                except KeyError:
                    self.pictographs["entertainment"] = [chr(i)]
            elif i in range(0x1F3AE, 0x1F3B5) or i in range(0x1F579, 0x1F57A): # 遊戲
                try:
                    self.pictographs["game"].append(chr(i))
                except KeyError:
                    self.pictographs["game"] = [chr(i)]
            elif i in range(0x1F3BD, 0x1F3D4) or i in range(0x1F3F8, 0x1F3FA): # 體育
                try:
                    self.pictographs["sport"].append(chr(i))
                except KeyError:
                    self.pictographs["sport"] = [chr(i)]
            elif i in range(0x1F3D4, 0x1F3F1) or i in range(0x1F5FA, 0x1F600): # 建築與地標
                try:
                    self.pictographs["buildingandmap"].append(chr(i))
                except KeyError:
                    self.pictographs["buildingandmap"] = [chr(i)]
            elif i in range(0x1F3F1, 0x1F3F5): # 旗標
                try:
                    self.pictographs["flag"].append(chr(i))
                except KeyError:
                    self.pictographs["flag"] = [chr(i)]
            elif (i in range(0x1F3F5, 0x1F3F8) or i in range(0x1F3FA, 0x1F3FB) or i in range(0x1F51E, 0x1F520) or i in range(0x1F52F, 0x1F532) or
                i in range(0x1F54F, 0x1F550) or i in range(0x1F56D, 0x1F577) or i in range(0x1F5DE, 0x1F5E4) or i in range(0x1F5F3, 0x1F5FA)): # 其它
                try:
                    self.pictographs["miscellaneous"].append(chr(i))
                except KeyError:
                    self.pictographs["miscellaneous"] = [chr(i)]
            elif i in range(0x1F3FB, 0x1F400): # 調色盤 (加在 self.modifiercolor)
                self.modifiercolor.append(chr(i))
            elif i in range(0x1F400, 0x1F42D) or i in range(0x1F43E, 0x1F440) or i in range(0x1F577, 0x1F579): # 動物
                try:
                    self.pictographs["animal"].append(chr(i))
                except KeyError:
                    self.pictographs["animal"] = [chr(i)]
            elif i in range(0x1F42D, 0x1F43E): # 動物 (加在 self.emoticons)
                try:
                    self.emoticons["animal"].append(chr(i))
                except KeyError:
                    self.emoticons["animal"] = [chr(i)]
            elif i in range(0x1F440, 0x1F446): # 臉部
                try:
                    self.pictographs["facialparts"].append(chr(i))
                except KeyError:
                    self.pictographs["facialparts"] = [chr(i)]
            elif i in range(0x1F446, 0x1F451) or i in range(0x1F58E, 0x1F5A4): # 手部
                try:
                    self.pictographs["hand"].append(chr(i))
                except KeyError:
                    self.pictographs["hand"] = [chr(i)]
            elif i in range(0x1F451, 0x1F464): # 服飾
                try:
                    self.pictographs["clothing"].append(chr(i))
                except KeyError:
                    self.pictographs["clothing"] = [chr(i)]
            elif i in range(0x1F464, 0x1F484) or i in range(0x1F57A, 0x1F57B): # 人物
                try:
                    self.pictographs["portraitandrole"].append(chr(i))
                except KeyError:
                    self.pictographs["portraitandrole"] = [chr(i)]
            elif i in range(0x1F484, 0x1F489): # 個人護理
                try:
                    self.pictographs["personalcare"].append(chr(i))
                except KeyError:
                    self.pictographs["personalcare"] = [chr(i)]
            elif i in range(0x1F489, 0x1F48B): # 醫療
                try:
                    self.pictographs["medical"].append(chr(i))
                except KeyError:
                    self.pictographs["medical"] = [chr(i)]
            elif i in range(0x1F48B, 0x1F493): # 浪漫
                try:
                    self.pictographs["romance"].append(chr(i))
                except KeyError:
                    self.pictographs["romance"] = [chr(i)]
            elif i in range(0x1F493, 0x1F4A0) or i in range(0x1F5A4, 0x1F5A5): # 愛心
                try:
                    self.pictographs["heart"].append(chr(i))
                except KeyError:
                    self.pictographs["heart"] = [chr(i)]
            elif i in range(0x1F4A0, 0x1F4AE): # 漫畫風格
                try:
                    self.pictographs["comicstyle"].append(chr(i))
                except KeyError:
                    self.pictographs["comicstyle"] = [chr(i)]
            elif i in range(0x1F4AE, 0x1F4B0): # 滿分
                try:
                    self.pictographs["schoolgrade"].append(chr(i))
                except KeyError:
                    self.pictographs["schoolgrade"] = [chr(i)]
            elif i in range(0x1F4B0, 0x1F4BA): # 金錢
                try:
                    self.pictographs["money"].append(chr(i))
                except KeyError:
                    self.pictographs["money"] = [chr(i)]
            elif i in range(0x1F4BA, 0x1F4DD) or i in range(0x1F5B9, 0x1F5BF): # 辦公
                try:
                    self.pictographs["office"].append(chr(i))
                except KeyError:
                    self.pictographs["office"] = [chr(i)]
            elif i in range(0x1F4DD, 0x1F4F7) or i in range(0x1F568, 0x1F56D) or i in range(0x1F57B, 0x1F58E) or i in range(0x1F5E4, 0x1F5E8): # 通訊
                try:
                    self.pictographs["communication"].append(chr(i))
                except KeyError:
                    self.pictographs["communication"] = [chr(i)]
            elif i in range(0x1F4F7, 0x1F4FF): # 影音
                try:
                    self.pictographs["audioandvideo"].append(chr(i))
                except KeyError:
                    self.pictographs["audioandvideo"] = [chr(i)]
            elif i in range(0x1F4FF, 0x1F500) or i in range(0x1F540, 0x1F54F): # 宗教
                try:
                    self.pictographs["religious"].append(chr(i))
                except KeyError:
                    self.pictographs["religious"] = [chr(i)]
            elif i in range(0x1F500, 0x1F519) or i in range(0x1F520, 0x1F525) or i in range(0x1F53A, 0x1F53E) or i in range(0x1F5BF, 0x1F5DE): # 使用者介面
                try:
                    self.pictographs["userinterface"].append(chr(i))
                except KeyError:
                    self.pictographs["userinterface"] = [chr(i)]
            elif i in range(0x1F519, 0x1F51E): # 文字指標
                try:
                    self.pictographs["wordswitharrows"].append(chr(i))
                except KeyError:
                    self.pictographs["wordswitharrows"] = [chr(i)]
            elif i in range(0x1F525, 0x1F52F): # 工具
                try:
                    self.pictographs["tool"].append(chr(i))
                except KeyError:
                    self.pictographs["tool"] = [chr(i)]
            elif i in range(0x1F532, 0x1F53A) or i in range(0x1F53E, 0x1F540): # 幾何形狀
                try:
                    self.pictographs["geometricshapes"].append(chr(i))
                except KeyError:
                    self.pictographs["geometricshapes"] = [chr(i)]
            elif i in range(0x1F550, 0x1F568): # 時鐘
                try:
                    self.pictographs["clockface"].append(chr(i))
                except KeyError:
                    self.pictographs["clockface"] = [chr(i)]
            elif i in range(0x1F5A5, 0x1F5B9): # 電腦
                try:
                    self.pictographs["computer"].append(chr(i))
                except KeyError:
                    self.pictographs["computer"] = [chr(i)]
            elif i in range(0x1F5E8, 0x1F5F3): # 聊天泡泡
                try:
                    self.pictographs["bubble"].append(chr(i))
                except KeyError:
                    self.pictographs["bubble"] = [chr(i)]

        for i in range(0x1F900, 0x1FA00): # 補充符號 (Supplemental Symbols and Pictographs)
            if i in range(0x1F910, 0x1F918) or i in range(0x1F920, 0x1F928): # 表情 (加在 self.emoticons)
                try:
                    self.emoticons["faces"].append(chr(i))
                except KeyError:
                    self.emoticons["faces"] = [chr(i)]
            elif i in range(0x1F918, 0x1F91F): # 手勢 (加在 self.emoticons)
                try:
                    self.emoticons["gesture"].append(chr(i))
                except KeyError:
                    self.emoticons["gesture"] = [chr(i)]
            elif i in range(0x1F930, 0x1F931) or i in range(0x1F933, 0x1F93F): # 人物 (加在 self.pictographs)
                try:
                    self.pictographs["portraitandrole"].append(chr(i))
                except KeyError:
                    self.pictographs["portraitandrole"] = [chr(i)]
            elif i in range(0x1F940, 0x1F94C): # 其它 (加在 self.pictographs)
                try:
                    self.pictographs["miscellaneous"].append(chr(i))
                except KeyError:
                    self.pictographs["miscellaneous"] = [chr(i)]
            elif i in range(0x1F950, 0x1F95F) or i in range(0x1F9C0, 0x1F9C1): # 食物 (加在 self.pictographs)
                try:
                    self.pictographs["food"].append(chr(i))
                except KeyError:
                    self.pictographs["food"] = [chr(i)]
            elif i in range(0x1F980, 0x1F992): # 動物 (加在 self.pictographs)
                try:
                    self.pictographs["animal"].append(chr(i))
                except KeyError:
                    self.pictographs["animal"] = [chr(i)]

        self.transport = {} # 交通運輸
        self.transport_keynames = ["交通工具", "交通標誌", "旅遊住宿", "其它"]

        for i in range(0x1F680, 0x1F700): # 交通運輸 (Transport and Map Symbols)
            if i in range(0x1F680, 0x1F6A5) or i in range(0x1F6E5, 0x1F6ED) or i in range(0x1F6F0, 0x1F6F7): # 交通工具
                try:
                    self.transport["vehicles"].append(chr(i))
                except KeyError:
                    self.transport["vehicles"] = [chr(i)]
            elif i in range(0x1F6A5, 0x1F6A9) or i in range(0x1F6A9, 0x1F6CB) or i in range(0x1F6D0, 0x1F6D3): # 交通標誌
                try:
                    self.transport["trafficsigns"].append(chr(i))
                except KeyError:
                    self.transport["trafficsigns"] = [chr(i)]
            elif i in range(0x1F6CB, 0x1F6D0): # 旅遊住宿
                try:
                    self.transport["accommodation"].append(chr(i))
                except KeyError:
                    self.transport["accommodation"] = [chr(i)]
            elif i in range(0x1F6E0, 0x1F6E5): # 其它
                try:
                    self.transport["miscellaneous"].append(chr(i))
                except KeyError:
                    self.transport["miscellaneous"] = [chr(i)]


    def getCharDef(self, emojitype, keyname):
        if emojitype == "dingbats":
            keyindex = self.dingbats_keynames.index(keyname)
            keys = ["miscellaneous", "crosses", "starsandsnows", "fleurons", "punctuationmarks", "brackets", "digits", "arrows", "arithmetics"] # "rockets" (Ornamental Dingbats)
            return self.dingbats[keys[keyindex]]
        elif emojitype == "emoticons":
            keyindex = self.emoticons_keynames.index(keyname)
            keys = ["faces", "catfaces", "animal", "gesture"]
            return self.emoticons[keys[keyindex]]
        elif emojitype == "miscellaneous":
            keyindex = self.miscellaneous_keynames.index(keyname)
            keys = (["weathers", "miscellaneous", "chess", "pointinghand", "warningsigns", "medical", "religiousandpolitical", "yijingtrigram", "emoticons",
                    "zodiacal", "musical", "syriaccross", "recycling", "map", "gender", "circlesandpentagram", "genealogical", "sport", "trafficsigns"])
            return self.miscellaneous[keys[keyindex]]
        elif emojitype == "pictographs":
            keyindex = self.pictographs_keynames.index(keyname)
            keys = (["portraitandrole", "animal", "plant", "romance", "heart", "comicstyle", "bubble", "weatherandlandscape", "globe", "moonsunandstar",
                    "food", "fruitandvegetable", "beverage", "celebration", "musical", "entertainment", "game", "sport", "buildingandmap", "flag",
                    "miscellaneous", "facialparts", "hand", "clothing", "personalcare", "medical", "schoolgrade", "money", "office", "communication",
                    "audioandvideo", "religious", "userinterface", "wordswitharrows", "tool", "geometricshapes", "clockface", "computer"])
            return self.pictographs[keys[keyindex]]
        elif emojitype == "transport":
            keyindex = self.transport_keynames.index(keyname)
            keys = ["vehicles", "trafficsigns", "accommodation", "miscellaneous"]
            return self.transport[keys[keyindex]]
        return []
        
    def getKeyNames(self, emojidict):
        return emojidict
        
emoji = emoji()
