
var defaultcinCount = {
    "big5F": 0,
    "big5LF": 0,
    "big5Other": 0,
    "big5S": 0,
    "bopomofo": 0,
    "cjk": 0,
    "cjkCIS": 0,
    "cjkExtA": 0,
    "cjkExtB": 0,
    "cjkExtC": 0,
    "cjkExtD": 0,
    "cjkExtE": 0,
    "cjkOther": 0,
    "phrases": 0,
    "privateuse": 0,
    "totalchardefs": 0
}

var defaultcinName = {
    "checj.json": "酷倉",
    "mscj3.json": "倉頡",
    "mscj3-ext.json": "倉頡(大字集)",
    "cj-ext.json": "雅虎倉頡",
    "cnscj.json": "中標倉頡",
    "thcj.json": "泰瑞倉頡",
    "newcj3.json": "亂倉打鳥",
    "cj5.json": "倉頡五代",
    "newcj.json": "自由大新倉頡",
    "scj6.json": "快倉六代",
    "thphonetic.json": "泰瑞注音",
    "CnsPhonetic.json": "中標注音",
    "bpmf.json": "傳統注音",
    "tharray.json": "泰瑞行列30",
    "array30.json": "行列30",
    "ar30-big.json": "行列30大字集",
    "array40.json": "行列40",
    "thdayi.json": "泰瑞大易四碼",
    "dayi4.json": "大易四碼",
    "dayi3.json": "大易三碼",
    "ez.json": "輕鬆",
    "ezsmall.json": "輕鬆小詞庫",
    "ezmid.json": "輕鬆中詞庫",
    "ezbig.json": "輕鬆大詞庫",
    "thpinyin.json": "泰瑞拼音",
    "pinyin.json": "正體拼音",
    "roman.json": "羅馬拼音",
    "simplecj.json": "正體簡易",
    "simplex.json": "速成",
    "simplex5.json": "簡易五代",
    "liu.json": "嘸蝦米"
}

var selHCins = [
    "泰瑞注音",
    "中標注音",
    "傳統注音"
];

var debugMode = false;
var checjConfig = {};
var cinCount = {};
var CONFIG_URL = '/config';
var VERSION_URL = '/version.txt';
var KEEP_ALIVE_URL = '/keep_alive';
var hasInnerText = (document.getElementsByTagName("body")[0].innerText !== undefined) ? true : false;

var symbolsChanged = false;
var swkbChanged = false;
var fsymbolsChanged = false;
var phraseChanged = false;
var flangsChanged = false;
var extendtableChanged = false;

var symbolsData = "";
var swkbData = "";
var fsymbolsData = "";
var phraseData = "";
var flangsData = "";
var extendtableData = "";

var isIE = (function() {
    var browser = {};
    return function(ver,c) {
        var key = ver ?  ( c ? "is"+c+"IE"+ver : "isIE"+ver ) : "isIE";
        var v = browser[key];
        if (typeof(v) != "undefined") {
            return v;
        }
        if (!ver) {
            v = (navigator.userAgent.indexOf('MSIE') !== -1 || navigator.appVersion.indexOf('Trident/') > 0);
        } else {
            var match = navigator.userAgent.match(/(?:MSIE |Trident\/.*; rv:|Edge\/)(\d+)/);
                if (match) {
                    var v1 = parseInt(match[1]);
                    v = c ?  ( c == 'lt' ?  v1 < ver  :  ( c == 'gt' ?  v1 >  ver : undefined ) ) : v1 == ver;
                } else if (ver <= 9) {
                    var b = document.createElement('b')
                    var s = '<!--[if '+(c ? c : '')+' IE '  + ver + ']><i></i><![endif]-->';
                    b.innerHTML = s;
                    v =  b.getElementsByTagName('i').length == 1;
                } else {
                    v = undefined;
                }
        }
        browser[key] = v;
        return v;
    };
}());

var isOldIE = (isIE() && isIE(9, 'lt'))

if (!isOldIE) {
    includeScriptFile("js/jAlert/jAlert.min.js")
} else {
    includeScriptFile("js/jAlert/jAlert-ie8.min.js")
}

if (!Date.now) {
    Date.now = function() {
        return new Date().valueOf();
    }
}

function loadConfig() {
    $.get(CONFIG_URL, function(data, status) {
        checjConfig = data.config;
        cinCount = data.cincount;
        symbolsData = data.symbols;
        swkbData = data.swkb;
        fsymbolsData = data.fsymbols;
        phraseData = data.phrase;
        flangsData = data.flangs;
        extendtableData = data.extendtable;
    }, "json");
}
loadConfig();

function saveConfig(callbackFunc) {
    var checkState = true
    // Check symbols format
    checkState = checkDataFormat($("#symbols").val(), "2", "#symbols", "特殊符號");
    if (!checkState) {
        return false;
    }

    // Check easy symbols format
    checkState = checkDataFormat($("#ez_symbols").val(), "1", "#ez_symbols", "簡易符號");
    if (!checkState) {
        return false;
    }

    // Check fullshape symbols format
    checkState = checkDataFormat($("#fs_symbols").val(), "2", "#fs_symbols", "全形標點符號");
    if (!checkState) {
        return false;
    }

    // Check user phrase format
    checkState = checkDataFormat($("#phrase").val(), "2", "#phrase", "聯想字詞");
    if (!checkState) {
        return false;
    }

    // Check foreign language format
    checkState = checkDataFormat($("#flangs").val(), "2", "#flangs", "外語文字");
    if (!checkState) {
        return false;
    }

    // Check extendtable format
    checkState = checkDataFormat($("#extendtable").val(), "3", "#extendtable", "擴展碼表");
    if (!checkState) {
        return false;
    }

    var data = {
        "config": checjConfig
    }

    if(symbolsChanged) {
        data.symbols = $("#symbols").val();
    }
    if(swkbChanged) {
        data.swkb = $("#ez_symbols").val();
    }
    if(fsymbolsChanged) {
        data.fsymbols = $("#fs_symbols").val();
    }
    if(phraseChanged) {
        data.phrase = $("#phrase").val();
    }
    if(flangsChanged) {
        data.flangs = $("#flangs").val();
    }
    if(extendtableChanged) {
        data.extendtable = $("#extendtable").val();
    }

    $.ajax({
        url: CONFIG_URL,
        method: "POST",
        async: false,
        success: callbackFunc(),
        contentType: "application/json",
        data: JSON.stringify(data),
        dataType:"json"
    });
}


function setElementText(elemId, elemText) {
    var elem = document.getElementById(elemId);
    if (!hasInnerText) {
        elem.textContent = elemText;
    } else {
        elem.innerText = elemText;
    }
}


function updateCinCountElements() {
    $.get(CONFIG_URL + '?' + Date.now(), function(data, status) {
        cinCountList = data.cincount;
        setElementText('big5F', cinCountList['big5F']);
        setElementText('big5LF', cinCountList['big5LF']);
        setElementText('big5S', cinCountList['big5S']);
        setElementText('big5Other', cinCountList['big5Other']);
        setElementText('bopomofo', cinCountList['bopomofo']);
        setElementText('cjk', cinCountList['cjk']);
        setElementText('cjkExtA', cinCountList['cjkExtA']);
        setElementText('cjkExtB', cinCountList['cjkExtB']);
        setElementText('cjkExtC', cinCountList['cjkExtC']);
        setElementText('cjkExtD', cinCountList['cjkExtD']);
        setElementText('cjkExtE', cinCountList['cjkExtE']);
        setElementText('cjkCIS', cinCountList['cjkCIS']);
        setElementText('cjkOther', cinCountList['cjkOther']);
        setElementText('phrases', cinCountList['phrases']);
        setElementText('privateuse', cinCountList['privateuse']);
        setElementText('totalchardefs', cinCountList['totalchardefs']);
    }, "json");
}


// update checjConfig object with the value set by the user
function updateConfig() {
    // Reset checjConfig, for change config_tool
    rcinFileList = checjConfig.rcinFileList
    checjConfig = {};
    checjConfig['rcinFileList'] = rcinFileList

    // Get values from checkboxes, text and radio
    $("input").each(function (index, inputItem) {
        if (inputItem.name == "") {
            return;
        }
        switch (inputItem.type) {
        case "checkbox":
            checjConfig[inputItem.name] = inputItem.checked;
            break;
        case "text":
        case "number":
            var inputValue = inputItem.value;
            if ($.isNumeric(inputValue)) {
                inputValue = parseInt(inputValue);
            }
            checjConfig[inputItem.name] = inputValue;
            break;
        case "radio":
            if (inputItem.checked === true) {
                checjConfig[inputItem.name] = parseInt(inputItem.value);
            }
            break;
        }
    });

    // Get values from select
    $("select").each(function (index, selectItem) {
        if (selectItem.value) {
            checjConfig[selectItem.name] = parseInt(selectItem.value);
        }
    });
}


function checkDataFormat(checkData, checkType, elementId, dataDesc) {
    var data_array = checkData.split("\n");
    var errorState = false;
    for (var i = 0; i < data_array.length; i++) {
        switch (checkType) {
            case "1":
                if (! /^[A-Za-z] .{1,10}$/.test(data_array[i])) {
                    errorState = true;
                    $.jAlert({
                        'title': '糟糕！',
                        'content': dataDesc + '設定第 ' + (i + 1) + ' 行「'+ data_array[i] +'」格式錯誤！<br>請使用「英文 + 空格 + 符號」的格式。',
                        'theme': 'dark_red',
                        'size': 'md',
                        'blurBackground': true,
                        'closeOnClick': true,
                        'showAnimation': 'zoomIn',
                        'hideAnimation': 'zoomOutDown',
                        'btns': {'text': '關閉', 'theme': 'blue'}
                    });
                }
                break;
            case "2":
                if (data_array[i].length > 1 && data_array[i].search("=") == -1) {
                    errorState = true;
                    $.jAlert({
                        'title': '糟糕！',
                        'content': dataDesc + '設定第 ' + (i + 1) + ' 行格式錯誤！<br>單行不能超過一個字元，或是沒有 = 符號區隔。',
                        'theme': 'dark_red',
                        'size': 'md',
                        'blurBackground': true,
                        'closeOnClick': true,
                        'showAnimation': 'zoomIn',
                        'hideAnimation': 'zoomOutDown',
                        'btns': {'text': '關閉', 'theme': 'blue'}
                    });
                }
                break;
            case "3":
                if (! /^[A-Za-z\d]+ .{1,40}$/.test(data_array[i])) {
                    if (!(data_array.length == 1 && data_array[0].length == 0))
                    {
                        errorState = true;
                        if (data_array[i].length == 0) {
                            alertContent = dataDesc + '設定第 ' + (i + 1) + ' 行為空行！<br>請去除該空行或使用「英數 + 空格 + 字詞」的格式。'
                        }
                        else {
                            alertContent = dataDesc + '設定第 ' + (i + 1) + ' 行「'+ data_array[i] +'」格式錯誤！<br>請使用「英數 + 空格 + 字詞」的格式。'
                        }

                        $.jAlert({
                            'title': '糟糕！',
                            'content': alertContent,
                            'theme': 'dark_red',
                            'size': 'md',
                            'blurBackground': true,
                            'closeOnClick': true,
                            'showAnimation': 'zoomIn',
                            'hideAnimation': 'zoomOutDown',
                            'btns': {'text': '關閉', 'theme': 'blue'}
                        });
                    }
                }
                break;
        }
        if (errorState) {
            $(elementId).blur();
            // Count select range
            var selectionStart = 0;
            for (var j = 0; j < i; j++) {
                selectionStart += data_array[j].length + 1;
            }

            $(elementId).prop("selectionStart", selectionStart);
            $(elementId).prop("selectionEnd", selectionStart + data_array[i].length + 1);
            return false;
        }
    }
    return true;
}


function updateKeyboardLayout() {
    var radios = $('input[type=radio][name=keyboardLayout]');
    var radioval = 0;
    for (var i=0, len=radios.length; i<len; i++) {
        if (radios[i].checked) {
            radioval = radios[i].value;
            break;
        }
    }

    if(imeFolderName == "chephonetic") {
        switch (radioval) {
            case "0":
                $("#keyboard_preview").load("kblayout.htm #keyboard_chephonetic_layout0");
                break;
            case "1":
                $("#keyboard_preview").load("kblayout.htm #keyboard_chephonetic_layout1");
                break;
            case "2":
                $("#keyboard_preview").load("kblayout.htm #keyboard_chephonetic_layout2");
                break;
            case "3":
                $("#keyboard_preview").load("kblayout.htm #keyboard_chephonetic_layout3");
                break;
        }
    }
}


// jQuery ready
$(function() {
    // show PIME version number
    $("#tabs").hide();
    $("#version").load(VERSION_URL);
    $("#navbar_top").load("config.htm #navbar_top");
    $("#typing_page").load("config.htm #typing_page");
    $("#intelligent_page").load("config.htm #intelligent_page");
    $("#ui_page").load("config.htm #ui_page");
    $("#keyboard_page").load("config.htm #keyboard_page");
    $("#cin_count").load("config.htm #cin_count");
    $("#cin_options").load("config.htm #cin_options");
    $("#extendtable_page").load("config.htm #extendtable_page");
    $("#symbols_page").load("config.htm #symbols_page");
    $("#fs_symbols_page").load("config.htm #fs_symbols_page");
    $("#ez_symbols_page").load("config.htm #ez_symbols_page");
    $("#phrase_page").load("config.htm #phrase_page");
    $("#flangs_page").load("config.htm #flangs_page");
    $("#navbar_bottom").load("config.htm #navbar_bottom");
    pageWait();
});

function pageWait() {
    if (document.getElementById("ok")) {
        pageReady();
    }
    else
    {
        window.setTimeout(pageWait,100);
    }
}

function pageReady() {
    updateCinCountElements();
    $('[data-toggle="popover"]').popover()

    $("#symbols").val(symbolsData);
    $("#ez_symbols").val(swkbData);
    $("#fs_symbols").val(fsymbolsData);
    $("#phrase").val(phraseData);
    $("#flangs").val(flangsData);
    $("#extendtable").val(extendtableData);

    if (imeFolderName == "chedayi") {
        $("#candPerRow").TouchSpin({min:1, max:6});
        $("#candPerPage").TouchSpin({min:1, max:6});
    }
    else {
        $("#candPerRow").TouchSpin({min:1, max:10});
        $("#candPerPage").TouchSpin({min:1, max:10});
    }
    $("#candMaxItems").TouchSpin({min:100, max:10000});
    $("#fontSize").TouchSpin({min:6, max:200});

    var selMessageTimes=[
        "０　",
        "１　",
        "２　",
        "３　",
        "４　",
        "５　"
    ];
    var messageDurationTime = $("#messageDurationTime");
    for(var i = 0; i < selMessageTimes.length; ++i) {
        var selMessageTime = selMessageTimes[i];
        var item = '<option value="' + i + '">' + selMessageTime + '</option>';
        messageDurationTime.append(item);
    }
    messageDurationTime.children().eq(checjConfig.messageDurationTime).prop("selected", true);

    var selCinType = $("#selCinType");
    for(var i = 0; i < selCins.length; ++i) {
        var selCin = selCins[i];
        var item = '<option value="' + i + '">' + selCin + '</option>';
        selCinType.append(item);
    }
    selCinType.children().eq(checjConfig.selCinType).prop("selected", true);

    var selRCins = checjConfig["rcinFileList"];
    var selRCinType = $("#selRCinType");
    for(var i = 0; i < selRCins.length; ++i) {
        var selRCin = defaultcinName[selRCins[i]];
        var item = '<option value="' + i + '">' + selRCin + '</option>';
        selRCinType.append(item);
    }
    selRCinType.children().eq(checjConfig.selRCinType).prop("selected", true);

    var selHCinType = $("#selHCinType");
    for(var i = 0; i < selHCins.length; ++i) {
        var selHCin = selHCins[i];
        var item = '<option value="' + i + '">' + selHCin + '</option>';
        selHCinType.append(item);
    }
    selHCinType.children().eq(checjConfig.selHCinType).prop("selected", true);

    var selWildcards=[
        "Ｚ　",
        "＊　"
    ];
    var selWildcardType = $("#selWildcardType");
    for(var i = 0; i < selWildcards.length; ++i) {
        var selWildcard = selWildcards[i];
        var item = '<option value="' + i + '">' + selWildcard + '</option>';
        selWildcardType.append(item);
    }
    selWildcardType.children().eq(checjConfig.selWildcardType).prop("selected", true);

    var keyboard_ddmenu = $("#keyboard_ddmenu");
    if(imeFolderName == "chephonetic") {
        keyboard_ddmenu.show();
    }

    var keyboard_page = $("#keyboard_layout");
    for(var i = 0; i < keyboardNames.length; ++i) {
        var id = "kb" + i;
        var name = keyboardNames[i];
        var item = '<div class="col-xs-6 col-sm-6 col-md-3 col-lg-3"><input type="radio" id="' + id + '" name="keyboardLayout" value="' + i + '">' +
            '<label for="' + id + '">' + name + '</label></div>';
        keyboard_page.append(item);
    }
    $("#kb" + checjConfig.keyboardLayout).prop("checked", true);
    updateKeyboardLayout();

    if(imeFolderName == "chedayi") {
        var selDayiSymbolChars=[
            "＝　",
            "號　"
        ];
        var selDayiSymbolCharType = $("#selDayiSymbolCharType");
        for(var i = 0; i < selDayiSymbolChars.length; ++i) {
            var selDayiSymbolChar = selDayiSymbolChars[i];
            var item = '<option value="' + i + '">' + selDayiSymbolChar + '</option>';
            selDayiSymbolCharType.append(item);
        }
        selDayiSymbolCharType.children().eq(checjConfig.selDayiSymbolCharType).prop("selected", true);
    }

    $("#symbols").change(function(){
        symbolsChanged = true;
    });

    $("#ez_symbols").change(function(){
        swkbChanged = true;
    });

    $("#fs_symbols").change(function(){
        fsymbolsChanged = true;
    });

    $("#phrase").change(function(){
        phraseChanged = true;
    });

    $("#flangs").change(function(){
        flangsChanged = true;
    });

    $("#extendtable").change(function(){
        extendtableChanged = true;
        $("#reLoadTable")[0].checked = true;
    });

    // OK button
    $("#ok").on('click', function () {
        updateConfig(); // update the config based on the state of UI elements
        saveConfig(function() {
            $.jAlert({
            'title': '好耶！',
            'content': '設定成功儲存！',
            'theme': 'blue',
            'size': 'md',
            'blurBackground': true,
            'closeOnClick': true,
            'showAnimation': 'zoomIn',
            'hideAnimation': 'zoomOutDown',
            'btns': {'text': '關閉', 'theme': 'blue'}
            });
        });
        updateCinCountElements();
        return false;
    });

    // set all initial values
    $("input").each(function(index, elem) {
        var item = $(this);
        var value = checjConfig[item.attr("id")];
        switch(item.attr("type")) {
        case "checkbox":
            item.prop("checked", value);
            break;
        case "text":
            item.val(value);
            break;
        }
    });

    // use for select example
    function updateSelExample() {
        var example = ["選", "字", "大", "小", "範", "例"];
        var html="";

        for (number = 1, i = 0, row = 0; number <= $("#candPerPage").val(); number++, i++, row++) {
            if (example[i] == null) {
                i = 0;
            }

            if (row == $("#candPerRow").val()) {
                row = 0;
                html += "<br>";
            }

            html += "<span>" + number.toString().slice(-1) + ".</span> " + example[i] + "&nbsp;&nbsp;";
        }

        $("#selExample").html(html);
    }

    // setup selExample default style
    $("#selExample").css("font-size", $("#fontSize").val() + "pt");
    updateSelExample();

    // trigger event
    $('.ui-spinner-button').click(function() {
        $(this).siblings('input').change();
    });

    $("#ui_page input").on("change", function() {
        $("#selExample").css("font-size", $("#fontSize").val() + "pt");
        updateSelExample();
    });

    $("#ui_page input").on("keydown", function(e) {
        if (e.keyCode == 38 || e.keyCode==40) {
            $("#selExample").css("font-size", $("#fontSize").val() + "pt");
            updateSelExample();
        }
    });

    function disableControlItem() {
        var disabled = []
        for(key in disableConfigItem) {
            if (checjConfig.selCinType == key) {
                if (disabled.indexOf(disableConfigItem[key][0]) < 0) {
                    if (disableConfigItem[key][1] != null) {
                        $('#' + disableConfigItem[key][0])[0].checked = disableConfigItem[key][1];
                    }
                    $('#' + disableConfigItem[key][0])[0].disabled = true;
                    disabled.push(disableConfigItem[key][0])
                }
            } else if (key > 100) {
                if (disableConfigItem[key][1] != null) {
                    $('#' + disableConfigItem[key][0])[0].checked = disableConfigItem[key][1];
                }
                $('#' + disableConfigItem[key][0])[0].disabled = true;
            } else {
                if (disabled.indexOf(disableConfigItem[key][0]) < 0) {
                    $('#' + disableConfigItem[key][0])[0].disabled = false;
                }
            }
        }

        if ($('#compositionBufferMode')[0].checked == false) {
            $("#autoMoveCursorInBrackets")[0].disabled = true;
        } else {
            $("#autoMoveCursorInBrackets")[0].disabled = false;
        }

        if ($('#fullShapeSymbols')[0].checked == false) {
            $("#directOutFSymbols")[0].disabled = true;
        } else {
            $("#directOutFSymbols")[0].disabled = false;
        }

        if ($('#selWildcardType')[0].disabled == true) {
            $("#selWildcardType").val(1);
        }
    }

    disableControlItem();

    // trigger event
    $('#navbars ul li a').click(function(){
        if($('.navbar-toggle').css('display') != 'none' && $(this).attr('href') != '#') {
            $('.navbar-toggle').click();
        }
    });

    $('#compositionBufferMode').click(function() {
        if ($('#compositionBufferMode')[0].checked == false) {
            $("#autoMoveCursorInBrackets")[0].disabled = true;
        } else {
            $("#autoMoveCursorInBrackets")[0].disabled = false;
        }
    });

    $('#fullShapeSymbols').click(function() {
        if ($('#fullShapeSymbols')[0].checked == false) {
            $("#directOutFSymbols")[0].disabled = true;
        } else {
            $("#directOutFSymbols")[0].disabled = false;
        }
    });

    $("#selCinType").change(function() {
        var selCin = parseInt($("#selCinType").find(":selected").val());
        if(!isNaN(selCin))
            checjConfig.selCinType = selCin;
        disableControlItem();
    });


    $('input[type=radio][name=keyboardLayout]').change(function() {
        updateKeyboardLayout();
    });

    if(!debugMode) {
        $("#compositionBufferMode")[0].disabled = true;
        $("#autoMoveCursorInBrackets")[0].disabled = true;
        $("#compositionBufferMode")[0].checked = false;
        $("#autoMoveCursorInBrackets")[0].checked = false;
    } else {
        $('#intelligent_ddmenu').show();
    }


    // keep the server alive every 20 second
    setInterval(function () {
        $.ajax({
            url: KEEP_ALIVE_URL + '?' + Date.now()
        });
    }, 20 * 1000);
}
