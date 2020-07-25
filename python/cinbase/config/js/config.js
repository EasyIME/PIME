var debugMode = false;
var checjConfig = {};
var CONFIG_URL = '/config';
var VERSION_URL = '/version.txt';
var KEEP_ALIVE_URL = '/keep_alive';
var hasInnerText = (document.getElementsByTagName("body")[0].innerText !== undefined) ? true : false;

var symbolsChanged = false;
var swkbChanged = false;
var fsymbolsChanged = false;
var flangsChanged = false;

var symbolsData = "";
var swkbData = "";
var fsymbolsData = "";
var flangsData = "";

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
        symbolsData = data.symbols;
        swkbData = data.swkb;
        fsymbolsData = data.fsymbols;
        flangsData = data.flangs;
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

    // Check foreign language format
    checkState = checkDataFormat($("#flangs").val(), "2", "#flangs", "外語文字");
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
    if(flangsChanged) {
        data.flangs = $("#flangs").val();
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


// update checjConfig object with the value set by the user
function updateConfig() {
    // Reset checjConfig, for change config_tool
    checjConfig = {};

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
    $("#cin_options").load("config.htm #cin_options");
    $("#symbols_page").load("config.htm #symbols_page");
    $("#fs_symbols_page").load("config.htm #fs_symbols_page");
    $("#ez_symbols_page").load("config.htm #ez_symbols_page");
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
    $('[data-toggle="popover"]').popover()

    $("#symbols").val(symbolsData);
    $("#ez_symbols").val(swkbData);
    $("#fs_symbols").val(fsymbolsData);
    $("#flangs").val(flangsData);

    $("#candPerRow").TouchSpin({min:1, max:10});
    $("#candPerPage").TouchSpin({min:1, max:10});

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

    // OK button
    $("#ok").on('click', function () {
        updateConfig(); // update the config based on the state of UI elements
        saveConfig(function() {
            $.jAlert({
            'title': 'Great!',
            'content': 'Settings successfully saved!',
            'theme': 'blue',
            'size': 'md',
            'blurBackground': true,
            'closeOnClick': true,
            'showAnimation': 'zoomIn',
            'hideAnimation': 'zoomOutDown',
            'btns': {'text': 'shut down', 'theme': 'blue'}
            });
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

        if ($('#fullShapeSymbols')[0].checked == false) {
            $("#directOutFSymbols")[0].disabled = true;
        } else {
            $("#directOutFSymbols")[0].disabled = false;
        }
    }

    disableControlItem();

    // trigger event
    $('#navbars ul li a').click(function(){
        if($('.navbar-toggle').css('display') != 'none' && $(this).attr('href') != '#') {
            $('.navbar-toggle').click();
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

    if(debugMode) {
        $('#intelligent_ddmenu').show();
    }

    // keep the server alive every 20 second
    setInterval(function () {
        $.ajax({
            url: KEEP_ALIVE_URL + '?' + Date.now()
        });
    }, 20 * 1000);
}
