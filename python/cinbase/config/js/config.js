
var defaultcinCount = {
    "cjkExtEchardefs": 0,
    "cjkchardefs": 0,
    "big5LFchardefs": 0,
    "cjkExtCchardefs": 0,
    "cjkOtherchardefs": 0,
    "cjkExtDchardefs": 0,
    "cjkTotalchardefs": 0,
    "big5Fchardefs": 0,
    "big5Otherchardefs": 0,
    "cjkExtAchardefs": 0,
    "bopomofochardefs": 0,
    "cjkExtBchardefs": 0
}

var defaultcinName = {
    "checj.cin": "酷倉",
    "mscj3.cin": "倉頡",
    "mscj3-ext.cin": "倉頡(大字集)",
    "cj-ext.cin": "雅虎倉頡",
    "cnscj.cin": "中標倉頡",
    "thcj.cin": "泰瑞倉頡",
    "newcj3.cin": "亂倉打鳥",
    "cj5.cin": "倉頡五代",
    "newcj.cin": "自由大新倉頡",
    "scj6.cin": "快倉六代",
    "thphonetic.cin": "泰瑞注音",
    "CnsPhonetic.cin": "中標注音",
    "bpmf.cin": "傳統注音",
    "tharray.cin": "泰瑞行列30",
    "array30.cin": "行列30",
    "ar30-big.cin": "行列30大字集",
    "array40.cin": "行列40",
    "thdayi.cin": "泰瑞大易四碼",
    "dayi4.cin": "大易四碼",
    "dayi3.cin": "大易三碼",
    "ez.cin": "輕鬆",
    "ezsmall.cin": "輕鬆小詞庫",
    "ezmid.cin": "輕鬆中詞庫",
    "ezbig.cin": "輕鬆大詞庫",
    "thpinyin.cin": "泰瑞拼音",
    "pinyin.cin": "正體拼音",
    "roman.cin": "羅馬拼音",
    "simplecj.cin": "正體簡易",
    "simplex.cin": "速成",
    "simplex5.cin": "簡易五代",
    "liu.cin": "嘸蝦米"
}

var debugMode = false;
var checjConfig = {};
var cinCount = {};
var CONFIG_URL = '/config';
var VERSION_URL = '/version.txt';
var KEEP_ALIVE_URL = '/keep_alive';

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

loadConfig();

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
        success: callbackFunc(),
        contentType: "application/json",
        data: JSON.stringify(data),
        dataType:"json"
    });
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
                    swal(
                        '糟糕',
                        dataDesc + '設定第 ' + (i + 1) + ' 行 ('+ data_array[i] +')格式錯誤\n請使用「英文 + 空格 + 符號」的格式',
                        'error'
                    );
                }
                break;
            case "2":
                if (data_array[i].length > 1 && data_array[i].search("=") == -1) {
                    errorState = true;
                    swal(
                        '糟糕',
                        dataDesc + '設定第 ' + (i + 1) + ' 行格式錯誤\n單行不能超過一個字元，或是沒有 = 符號區隔',
                        'error'
                    );
                }
                break;
            case "3":
                if (! /^[A-Za-z\d]+ .{1,40}$/.test(data_array[i])) {
                    if (!data_array[i].length == 0 && i == 0)
                    {
                        errorState = true;
                        swal(
                            '糟糕',
                            dataDesc + '設定第 ' + (i + 1) + ' 行 ('+ data_array[i] +')格式錯誤\n請使用「英數 + 空格 + 字詞」的格式',
                            'error'
                        );
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


// jQuery ready
$(function() {
    // show PIME version number
    $("#tabs").hide();
    $("#version").load(VERSION_URL);
    $("#typing_page").load("config.htm #typing_page")
    $("#cin_count").load("config.htm #cin_count")
    $("#cin_options").load("config.htm #cin_options")
    $("#extendtable_page").load("config.htm #extendtable_page")
    $("#ui_page").load("config.htm #ui_page")
    $("#symbols_page").load("config.htm #symbols_page")
    $("#fs_symbols_page").load("config.htm #fs_symbols_page")
    $("#ez_symbols_page").load("config.htm #ez_symbols_page")
    $("#phrase_page").load("config.htm #phrase_page")
    $("#flangs_page").load("config.htm #flangs_page")
    pageWait();
});

function pageWait() {
    if (document.getElementById("flangs")) {
        pageReady()
    }
    else
    {
        window.setTimeout(pageWait,100);
    }
}

function pageReady() {
    $("#tabs").show();
    $(document).tooltip();
    $("#tabs").tabs({heightStyle:"auto"});

    document.getElementById('bopomofochardefs').innerText = cinCount['bopomofochardefs']
    document.getElementById('big5Fchardefs').innerText = cinCount['big5Fchardefs']
    document.getElementById('big5LFchardefs').innerText = cinCount['big5LFchardefs']
    document.getElementById('big5Otherchardefs').innerText = cinCount['big5Otherchardefs']
    document.getElementById('cjkchardefs').innerText = cinCount['cjkchardefs']
    document.getElementById('cjkExtAchardefs').innerText = cinCount['cjkExtAchardefs']
    document.getElementById('cjkExtBchardefs').innerText = cinCount['cjkExtBchardefs']
    document.getElementById('cjkExtCchardefs').innerText = cinCount['cjkExtCchardefs']
    document.getElementById('cjkExtDchardefs').innerText = cinCount['cjkExtDchardefs']
    document.getElementById('cjkExtEchardefs').innerText = cinCount['cjkExtEchardefs']
    document.getElementById('cjkOtherchardefs').innerText = cinCount['cjkOtherchardefs']
    document.getElementById('cjkTotalchardefs').innerText = cinCount['cjkTotalchardefs']

    $("#symbols").val(symbolsData);
    $("#ez_symbols").val(swkbData);
    $("#fs_symbols").val(fsymbolsData);
    $("#phrase").val(phraseData);
    $("#flangs").val(flangsData);
    $("#extendtable").val(extendtableData);

    if (imeFolderName == "chedayi") {
        $("#candPerRow").spinner({min:1, max:6});
        $("#candPerPage").spinner({min:1, max:6});
    }
    else {
        $("#candPerRow").spinner({min:1, max:10});
        $("#candPerPage").spinner({min:1, max:10});
    }
    $("#candMaxItems").spinner({min:100, max:10000});
    $("#fontSize").spinner({min:6, max:200});

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

    var keyboard_page = $("#keyboard_page");
    for(var i = 0; i < keyboardNames.length; ++i) {
        var id = "kb" + i;
        var name = keyboardNames[i];
        var item = '<input type="radio" id="' + id + '" name="keyboardLayout" value="' + i + '">' +
            '<label for="' + id + '">' + name + '</label><br />';
        keyboard_page.append(item);
    }
    $("#kb" + checjConfig.keyboardLayout).prop("checked", true);

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
            swal(
              '好耶！',
              '設定成功儲存！',
              'success'
            );
        });
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
        
        if ($('#directShowCand')[0].checked == false && $('#compositionBufferMode')[0].checked == false) {
            $("#directCommitString")[0].disabled = false;
        } else {
            $("#directCommitString")[0].checked = false;
            $("#directCommitString")[0].disabled = true;
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
    }
    
    disableControlItem();

    // trigger event
    $('#directShowCand').click(function() {
        if ($('#directShowCand')[0].checked == false && $('#compositionBufferMode')[0].checked == false) {
            $("#directCommitString")[0].disabled = false;
        } else {
            $("#directCommitString")[0].checked = false;
            $("#directCommitString")[0].disabled = true;
        }
    });
    
    $('#compositionBufferMode').click(function() {
        if ($('#compositionBufferMode')[0].checked == false && $('#directShowCand')[0].checked == false) {
            $("#directCommitString")[0].disabled = false;
        } else {
            $("#directCommitString")[0].checked = false;
            $("#directCommitString")[0].disabled = true;
        }
        
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
    
    $("#selCinType").click(function() {
        var selCin = parseInt($("#selCinType").find(":selected").val());
        if(!isNaN(selCin))
            checjConfig.selCinType = selCin;
        disableControlItem();
    });
    
    if(!debugMode) {
        $("#compositionBufferMode")[0].disabled = true;
        $("#autoMoveCursorInBrackets")[0].disabled = true;
        $("#compositionBufferMode")[0].checked = false;
        $("#autoMoveCursorInBrackets")[0].checked = false;
    }
    
    // keep the server alive every 20 second
    setInterval(function () {
        $.ajax({
            url: KEEP_ALIVE_URL + '?' + Date.now()
        });
    }, 20 * 1000);
}
