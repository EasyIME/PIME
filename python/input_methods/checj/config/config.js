// 此輸入法模組的資料夾名稱
var imeFolderName = "checj"

// 此輸入法模組使用的碼表
var selCins = [
    "酷倉",
    "倉頡",
    "倉頡(大字集)",
    "雅虎倉頡",
    "中標倉頡",
    "泰瑞倉頡",
    "亂倉打鳥",
    "倉頡五代",
    "自由大新倉頡",
    "快倉六代",
    "倉捷"
];

// 此輸入法模組使用的鍵盤類型
var keyboardNames = [];

// 此輸入法模組在特定碼表須停用的設定項目 (從 0 開始, 100 之後代表全部碼表)
var disableConfigItem = {
};


// 以下無須修改
// ==============================================================================================

includeScriptFile("js/config.js")

function includeScriptFile(filename)
{
    var head = document.getElementsByTagName('head')[0];

    script = document.createElement('script');
    script.src = filename;
    script.type = 'text/javascript';

    head.appendChild(script)
}
