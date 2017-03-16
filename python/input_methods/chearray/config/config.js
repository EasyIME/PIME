// 此輸入法模組的資料夾名稱
var imeFolderName = "chearray"

// 此輸入法模組使用的碼表
var selCins = [
    "泰瑞行列30",
    "行列30",
    "行列30大字集",
    "行列40"
];

// 此輸入法模組使用的鍵盤類型
var keyboardNames = [];

// 此輸入法模組在特定碼表須停用的設定項目 (從 0 開始, 100 之後代表全部碼表)
var disableConfigItem = {
    2: ["directShowCand", false],
    3: ["directShowCand", false],
    101: ["selWildcardType", null]
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
