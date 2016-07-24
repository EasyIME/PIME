// 此輸入法模組的資料夾名稱
var imeFolderName = "chesimplex"

// 此輸入法模組使用的碼表
var selCins = [
    "正體簡易",
    "速成",
    "簡易五代"
];

// 此輸入法模組使用的鍵盤類型
var keyboardNames = [];

// 載入此輸入法模組預設設定值
defaultConfig = loadDefaultConfig("config.json")

// 此輸入法模組在特定碼表須停用的設定項目 (從 0 開始, 100 之後代表全部碼表)
var disableConfigItem = {
};


// 以下無須修改
// ==============================================================================================
var configScriptFile = getScriptDir() + "\\config.js"
includeScriptFile(configScriptFile)

function loadDefaultConfig(configFile) {
    try {
        var stream = new ActiveXObject("ADODB.Stream");
        stream.Charset = "utf-8";
        stream.Open();
        stream.LoadFromFile(location.pathname.replace("config.hta", configFile));
        var data = stream.ReadText();
        stream.Close();
        return JSON.parse(data);
    }
    catch(err) {
        return {}
    }
}

function includeScriptFile(filename)
{
	var head = document.getElementsByTagName('head')[0];
	
	script = document.createElement('script');
	script.src = filename;
	script.type = 'text/javascript';
	
	head.appendChild(script)
}

// This is Windows-only :-(
function getScriptDir() {
    progDir = location.pathname.replace("input_methods\\" + imeFolderName + "\\config\\config.hta","cinbase\\config\\js")
    return progDir;
}