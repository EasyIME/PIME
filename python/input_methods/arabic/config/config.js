var imeFolderName = "arabic"

// 此輸入法模組使用的碼表
var selCins = [
    "Arabic"
];

// 此輸入法模組使用的鍵盤類型
var keyboardNames = [];

// The setting items that this input method module must disable in a specific code table (starting from 0, after 100 means all code tables)
var disableConfigItem = {
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
