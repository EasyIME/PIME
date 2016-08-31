!define LANG "SIMPCHINESE" ; Must be the lang name define by NSIS

!insertmacro LANG_STRING INSTALLER_LANGUAGE_TITLE "安装程序语言"
!insertmacro LANG_STRING INSTALL_LANGUAGE_MESSAGE "请选择安装程序语言"

!insertmacro LANG_STRING PRODUCT_NAME "PIME 输入法"

!insertmacro LANG_STRING INST_TYPE_STD "标准安装"
!insertmacro LANG_STRING INST_TYPE_FULL "完整安装"
!insertmacro LANG_STRING MB_REBOOT_REQUIRED "安装程序需要重新开机来完成卸载。$\r$\n你要立即重新开机吗？ (若你想要在稍后才重新开机请选择「否」)"
!insertmacro LANG_STRING PRODUCT_PAGE "PIME 项目主页"
!insertmacro LANG_STRING PRODUCT_PUBLISHER "PIME 开发团队"

!insertmacro LANG_STRING AtLeastWinVista_MESSAGE "抱歉，本程序目前只能支持 Windows Vista 以上版本"
!insertmacro LANG_STRING REBOOT_QUESTION "安装发生错误，无法完成。$\r$\n有时是有文件正在使用中，暂时无法删除或覆写。$\n$\n建议重新开机后，再次执行安装程序。$\r$\n你要立即重新开机吗？ (若你想要在稍后才重新开机请选择「否」)"
!insertmacro LANG_STRING INST_FAILED_MESSAGE "安装发生错误，无法完成。$\n$\n有时是有文件正在使用中，暂时无法删除或覆写。$\n$\n建议重新开机后，再次执行安装程序。"
!insertmacro LANG_STRING UNINSTALL_OLD "侦测到已安装旧版，是否要移除旧版后继续安装新版？"
!insertmacro LANG_STRING DOWNLOAD_VC2015_QUESTION "这个程序需要微软 VC++ 2015 runtime 更新才能运作，要自动下载安装？"
!insertmacro LANG_STRING DOWNLOAD_VC2015_FAILED_MESSAGE "无法正确下载，请稍后再试，或手动安装 VC++ 2015 runtime (x86)"
!insertmacro LANG_STRING INST_VC2015_FAILED_MESSAGE "VC++ 2015 runtime (x86) 并未正确安装，请参阅相关微软文档进行更新。"

!insertmacro LANG_STRING IEProtectedPage_TITLE "变更 IE 设置"
!insertmacro LANG_STRING IEProtectedPage_MESSAGE "PIME 输入法须要变更 IE 设置，才能在 IE 里使用。"

!insertmacro LANG_STRING SECTION_MAIN "PIME 输入法平台"
!insertmacro LANG_STRING SECTION_GROUP "输入法模块"

!insertmacro LANG_STRING CHEWING 新酷音
!insertmacro LANG_STRING CHECJ 酷仓
!insertmacro LANG_STRING CHELIU 虾米
!insertmacro LANG_STRING CHEARRAY 行列
!insertmacro LANG_STRING CHEDAYI 大易
!insertmacro LANG_STRING CHEPINYIN 拼音
!insertmacro LANG_STRING CHESIMPLEX 速成
!insertmacro LANG_STRING CHEPHONETIC 注音
!insertmacro LANG_STRING CHEEZ 轻松
!insertmacro LANG_STRING RIME 中州韵
!insertmacro LANG_STRING EMOJIME emojime
!insertmacro LANG_STRING CHEENG 英数

!insertmacro LANG_STRING SecMain_DESC "安装 $(PRODUCT_NAME) 主程序到你的电脑里。"
!insertmacro LANG_STRING chewing_DESC "安装新酷音输入法模块。"
!insertmacro LANG_STRING checj_DESC "安装酷仓输入法模块。"
!insertmacro LANG_STRING cheliu_DESC "安装虾米输入法模块。"
!insertmacro LANG_STRING chearray_DESC "安装行列输入法模块。"
!insertmacro LANG_STRING chedayi_DESC "安装大易输入法模块。"
!insertmacro LANG_STRING chepinyin_DESC "安装拼音输入法模块。"
!insertmacro LANG_STRING chesimplex_DESC "安装速成输入法模块。"
!insertmacro LANG_STRING chephonetic_DESC "安装注音输入法模块。"
!insertmacro LANG_STRING cheez_DESC "安装轻松输入法模块。"
!insertmacro LANG_STRING rime_DESC "安装中州韵输入法引擎，内含拼音、注音、仓颉、五笔、粤拼、吴语等数种输入方案。"
!insertmacro LANG_STRING emojime_DESC "安装 emojime 输入法模块。"
!insertmacro LANG_STRING cheeng_DESC "安装英数输入法模块。"

!insertmacro LANG_STRING SET_CHEWING "设置新酷音输入法"
!insertmacro LANG_STRING SET_CHECJ 设置酷仓输入法
!insertmacro LANG_STRING SET_CHELIU 设置虾米输入法
!insertmacro LANG_STRING SET_CHEARRAY 设置行列输入法
!insertmacro LANG_STRING SET_CHEDAYI 设置大易输入法
!insertmacro LANG_STRING SET_CHEPINYIN 设置拼音输入法
!insertmacro LANG_STRING SET_CHESIMPLEX 设置速成输入法
!insertmacro LANG_STRING SET_CHEPHONETIC 设置注音输入法
!insertmacro LANG_STRING SET_CHEEZ 设置轻松输入法

!insertmacro LANG_STRING UNINSTALL_PIME "卸载 PIME"