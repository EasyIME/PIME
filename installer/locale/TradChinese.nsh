!define LANG "TRADCHINESE" ; Must be the lang name define by NSIS

!insertmacro LANG_STRING INSTALLER_LANGUAGE_TITLE "安裝程式語言"
!insertmacro LANG_STRING INSTALL_LANGUAGE_MESSAGE "請選擇安裝程式語言"

!insertmacro LANG_STRING PRODUCT_NAME "PIME 輸入法"

!insertmacro LANG_STRING INST_TYPE_STD "標準安裝"
!insertmacro LANG_STRING INST_TYPE_FULL "完整安裝"
!insertmacro LANG_STRING MB_REBOOT_REQUIRED "安裝程式需要重新開機來完成解除安裝。$\r$\n你要立即重新開機嗎？ (若你想要在稍後才重新開機請選擇「否」)"
!insertmacro LANG_STRING PRODUCT_PAGE "PIME 專案網頁"
!insertmacro LANG_STRING PRODUCT_PUBLISHER "PIME 開發團隊"

!insertmacro LANG_STRING AtLeastWinVista_MESSAGE "抱歉，本程式目前只能支援 Windows Vista 以上版本"
!insertmacro LANG_STRING REBOOT_QUESTION "安裝發生錯誤，無法完成。$\r$\n有時是有檔案正在使用中，暫時無法刪除或覆寫。$\n$\n建議重新開機後，再次執行安裝程式。$\r$\n你要立即重新開機嗎？ (若你想要在稍後才重新開機請選擇「否」)"
!insertmacro LANG_STRING INST_FAILED_MESSAGE "安裝發生錯誤，無法完成。$\n$\n有時是有檔案正在使用中，暫時無法刪除或覆寫。$\n$\n建議重新開機後，再次執行安裝程式。"
!insertmacro LANG_STRING UNINSTALL_OLD "偵測到已安裝舊版，是否要移除舊版後繼續安裝新版？"
!insertmacro LANG_STRING DOWNLOAD_VC2015_QUESTION "這個程式需要微軟 VC++ 2015 runtime 更新才能運作，要自動下載安裝？"
!insertmacro LANG_STRING DOWNLOAD_VC2015_FAILED_MESSAGE "無法正確下載，請稍後再試，或手動安裝 VC++ 2015 runtime (x86)"
!insertmacro LANG_STRING INST_VC2015_FAILED_MESSAGE "VC++ 2015 runtime (x86) 並未正確安裝，請參閱相關微軟文件進行更新。"

!insertmacro LANG_STRING SECTION_MAIN "PIME 輸入法平台"
!insertmacro LANG_STRING PYTHON_SECTION_GROUP "Python 輸入法模組"
!insertmacro LANG_STRING PYTHON_CHT_SECTION_GROUP "中文繁體"
!insertmacro LANG_STRING PYTHON_CHS_SECTION_GROUP "中文簡體"
!insertmacro LANG_STRING NODE_SECTION_GROUP "Node 輸入法模組"
!insertmacro LANG_STRING NODE_CHT_SECTION_GROUP "中文繁體"
!insertmacro LANG_STRING NODE_CHS_SECTION_GROUP "中文簡體"

!insertmacro LANG_STRING CHEWING 新酷音
!insertmacro LANG_STRING CHECJ 酷倉
!insertmacro LANG_STRING CHELIU "蝦米 (須自備正版表格檔)"
!insertmacro LANG_STRING CHEARRAY 行列
!insertmacro LANG_STRING CHEDAYI 大易
!insertmacro LANG_STRING CHEPINYIN 拼音
!insertmacro LANG_STRING CHESIMPLEX 速成
!insertmacro LANG_STRING CHEPHONETIC 注音
!insertmacro LANG_STRING CHEEZ 輕鬆
!insertmacro LANG_STRING RIME 中州韻
!insertmacro LANG_STRING EMOJIME emojime
!insertmacro LANG_STRING CHEENG 英數
!insertmacro LANG_STRING BRAILLE_CHEWING "點字酷音"

!insertmacro LANG_STRING SELECT_LIU_FILE "蝦米模組需要「正版」嘸蝦米輸入法的表格檔 (liu-uni.tab) 才能安裝。$\r$\n請選取 liu-uni.tab 檔案所在位置。"
!insertmacro LANG_STRING CANNOT_INSTALL_LIU "缺少 liu-uni.tab 表格檔，無法安裝蝦米輸入法。"

!insertmacro LANG_STRING SecMain_DESC "安裝 $(PRODUCT_NAME) 主程式到你的電腦裏。"
!insertmacro LANG_STRING PYTHON_SECTION_GROUP_DESC "Python 輸入法模組"
!insertmacro LANG_STRING PYTHON_CHT_SECTION_GROUP_DESC "中文繁體"
!insertmacro LANG_STRING PYTHON_CHS_SECTION_GROUP_DESC "中文簡體"
!insertmacro LANG_STRING NODE_SECTION_GROUP_DESC "NODE 輸入法模組"
!insertmacro LANG_STRING NODE_CHT_SECTION_GROUP_DESC "中文繁體"
!insertmacro LANG_STRING NODE_CHS_SECTION_GROUP_DESC "中文簡體"
!insertmacro LANG_STRING chewing_DESC "安裝新酷音輸入法模組。"
!insertmacro LANG_STRING checj_DESC "安裝酷倉輸入法模組。"
!insertmacro LANG_STRING cheliu_DESC "安裝蝦米輸入法模組。"
!insertmacro LANG_STRING chearray_DESC "安裝行列輸入法模組。"
!insertmacro LANG_STRING chedayi_DESC "安裝大易輸入法模組。"
!insertmacro LANG_STRING chepinyin_DESC "安裝拼音輸入法模組。"
!insertmacro LANG_STRING chesimplex_DESC "安裝速成輸入法模組。"
!insertmacro LANG_STRING chephonetic_DESC "安裝注音輸入法模組。"
!insertmacro LANG_STRING cheez_DESC "安裝輕鬆輸入法模組。"
!insertmacro LANG_STRING rime_DESC "安裝中州韻輸入法引擎，內含拼音、注音、倉頡、五筆、粵拼、吳語等數種輸入方案。"
!insertmacro LANG_STRING emojime_DESC "安裝 emojime 輸入法模組。"
!insertmacro LANG_STRING cheeng_DESC "安裝英數輸入法模組。"
!insertmacro LANG_STRING braille_chewing_DESC "安裝點字酷音輸入法模組。"

!insertmacro LANG_STRING SET_CHEWING "設定新酷音輸入法"
!insertmacro LANG_STRING SET_CHEWING_PHRASES "編輯新酷音使用者辭庫"

!insertmacro LANG_STRING SET_CHECJ "設定酷倉輸入法"
!insertmacro LANG_STRING SET_CHELIU "設定蝦米輸入法"
!insertmacro LANG_STRING SET_CHEARRAY "設定行列輸入法"
!insertmacro LANG_STRING SET_CHEDAYI "設定大易輸入法"
!insertmacro LANG_STRING SET_CHEPINYIN "設定拼音輸入法"
!insertmacro LANG_STRING SET_CHESIMPLEX "設定速成輸入法"
!insertmacro LANG_STRING SET_CHEPHONETIC "設定注音輸入法"
!insertmacro LANG_STRING SET_CHEEZ "設定輕鬆輸入法"
!insertmacro LANG_STRING SET_BRAILLE_CHEWING "設定點字酷音輸入法"

!insertmacro LANG_STRING UNINSTALL_PIME "解除安裝 PIME"