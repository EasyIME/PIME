$(function () {
    var chewingConfig = {},
        symbolsChanged = false,
        swkbChanged = false,
        DEBUG = false,
        CONFIG_URL = '/config',
        VERSION_URL = '/version.txt',
        KEEP_ALIVE_URL = '/keep_alive';

    if (DEBUG) {
        // load data from text file for testing or developing
        CONFIG_URL = 'debug' + CONFIG_URL;
        VERSION_URL = 'debug' + VERSION_URL;
        KEEP_ALIVE_URL = 'debug' + KEEP_ALIVE_URL;
    }

    function loadConfig() {
        $.get(CONFIG_URL, function (data, status) {
            chewingConfig = data.config;
            $("#symbols").val(data.symbols);
            $("#ez_symbols").val(data.swkb);
            initializeUI();
        }, "json");
    }

    function saveConfig(callbackFunc) {
        // Check easy symbols format
        var ez_symbols_array = $("#ez_symbols").val().split("\n");
        for (var i = 0; i < ez_symbols_array.length; i++) {
            if (!/^[A-Za-z] .{1,10}$/.test(ez_symbols_array[i])) {
                // Select error range
                $("#ez_symbols").select();
                var selectionStart = 0;
                for (var j = 0; j < i; j++) {
                    selectionStart += ez_symbols_array[j].length + 1;
                }
                $("#ez_symbols").prop("selectionStart", selectionStart);
                $("#ez_symbols").prop("selectionEnd", selectionStart + ez_symbols_array[i].length + 1);
                swal(
                    '糟糕',
                    '簡易符號輸入設定第 ' + (i + 1) + ' 行 (' + ez_symbols_array[i] + ')格式錯誤\n請使用「英文 + 空格 + 符號」的格式，符號最多10個字元',
                    'error'
                );
                return false;
            }
        }

        // Check symbols format
        var symbols_array = $("#symbols").val().split("\n");
        for (var i = 0; i < symbols_array.length; i++) {
            if (symbols_array[i].length > 1 && symbols_array[i].search("=") == -1) {
                // Select error range
                $("#symbols").select();
                var selectionStart = 1;
                for (var j = 0; j < i; j++) {
                    selectionStart += symbols_array[j].length;
                }
                $("#symbols").prop("selectionStart", selectionStart);
                $("#symbols").prop("selectionEnd", selectionStart + symbols_array[i].length);
                swal(
                    '糟糕',
                    '特殊符號設定第 ' + (i + 1) + ' 行格式錯誤\n單行不能超過一個字元，或是沒有 = 符號區隔',
                    'error'
                );
                return false;
            }
        }

        var data = {
            "config": chewingConfig
        }
        if (symbolsChanged) {
            data.symbols = $("#symbols").val();
        }
        if (swkbChanged) {
            data.swkb = $("#ez_symbols").val();
        }

        $.ajax({
            url: CONFIG_URL,
            method: "POST",
            success: callbackFunc,
            contentType: "application/json",
            data: JSON.stringify(data),
            dataType: "json"
        });
    }

    // update chewingConfig object with the value set by the user
    function updateConfig() {
        // Reset chewingConfig, for change config_tool
        chewingConfig = {};

        // Get values from checkboxes, text and radio
        $("input").each(function (index, inputItem) {
            switch (inputItem.type) {
            case "checkbox":
                chewingConfig[inputItem.name] = inputItem.checked;
                break;
            case "text":
            case "number":
                var inputValue = inputItem.value;
                if ($.isNumeric(inputValue)) {
                    inputValue = parseInt(inputValue);
                }
                chewingConfig[inputItem.name] = inputValue;
                break;
            case "radio":
                if (inputItem.checked === true) {
                    chewingConfig[inputItem.name] = parseInt(inputItem.value);
                }
                break;
            }
        });

        // Get values from select
        $("select").each(function (index, selectItem) {
            if (selectItem.value) {
                chewingConfig[selectItem.name] = parseInt(selectItem.value);
            }
        });
    }

    function initializeUI() {
        // Setup checkbox and text values
        $("input").each(function () {
            switch ($(this).attr("type")) {
            case "checkbox":
                $(this).prop("checked", chewingConfig[$(this).attr("id")]);
                break;
            case "text":
            case "number":
                $(this).val(chewingConfig[$(this).attr("id")]);
                break;
            }
        });

        // Setup select options and values
        var selectOptions = {
            "upDownAction": [
                "移動游標選字",
                "在選字時翻頁"
            ],
            "leftRightAction": [
                "移動游標選字",
                "在選字時翻頁"
            ],
            "spaceKeyAction": {
                1: "叫出選字視窗",
                0: "在選字時翻頁"
            },
            "selKeyType": [
                "1234567890",
                "asdfghjkl;",
                "asdfzxcv89",
                "asdfjkl789",
                "aoeuhtn789",
                "1234qweras"
            ]
        };

        $.each(selectOptions, function (id, options) {
            $.each(options, function (value, optionName) {
                $("#" + id).append('<option value="' + value + '">' + optionName + '</option>');
                if (value == chewingConfig[id]) {
                    $("#" + id + " option:last-child").prop("selected", true);
                }
            });
        });

        $("select").selectpicker();
        $('[data-toggle="popover"]').popover();

        // Setup keybord page
        var keyboardNames = [
            "預設",
            "許氏鍵盤",
            "IBM",
            "精業",
            "倚天",
            "倚天 26 鍵",
            "DVORAK",
            "DVORAK 許氏",
            "大千 26 鍵",
            "漢語拼音",
            "台灣華語羅馬拼音",
            "注音二式",
            "CARPALX"
        ];

        var keyboard_page = $("#keyboard_tab"),
            item = '';

        for (var i = 0; i < keyboardNames.length; ++i) {
            var id = "kb" + i;
            var name = keyboardNames[i];
            item += '<div class="radio radio-info">' +
                '<input type="radio" id="' + id + '" name="keyboardLayout" value="' + i + '">' +
                '<label for="' + id + '">' + name + '</label><br>' +
                '</div>';
        }
        keyboard_page.html(item);

        $.each(keyboardNames, function (value, keybordName) {
            var item = '<input type="radio" id="kb' + value + '" name="keyboardLayout" value="' + value + '">' + '<label for="kb' + value + '">' + keybordName + '</label><br>';
            $("#keyboard_page").append(item);
        });
        $("#kb" + chewingConfig.keyboardLayout).prop("checked", true);

        // Use for select phrase example
        function updateSelExample() {
            var example = ["選", "字", "大", "小", "範", "例"];
            var selectItems = $("#selKeyType option").eq($("#selKeyType").val()).html();
            var html = "";

            for (number = 0, i = 0, row = 0; number < $("#candPerPage").val(); number++, i++, row++) {
                if (example[i] == null) {
                    i = 0;
                }

                if (row == $("#candPerRow").val()) {
                    row = 0;
                    html += "<br>";
                }

                html += "<span>" + selectItems.substr(number, 1) + ".</span> " + example[i] + "";
            }

            $("#selExample").html(html);
            $("#selExample").css("font-size", $("#fontSize").val() + "pt");
        }

        updateSelExample();

        // Register updateSelExample event
        $("#ui_tab input, #ui_tab select").on("change keyup", updateSelExample);
    }

    // workaround the same origin policy of IE.
    // http://stackoverflow.com/questions/7852225/is-it-safe-to-use-support-cors-true-in-jquery
    $.support.cors = true;

    // show PIME version number
    $("#version").load(VERSION_URL);

    // setup UI
    $("#symbols").on('change', function () {
        symbolsChanged = true;
    });

    $("#ez_symbols").on('change', function () {
        swkbChanged = true;
    });

    // OK button
    $("#ok").on('click', function () {
        updateConfig(); // update the config based on the state of UI elements
        saveConfig(function () {
            swal(
                '好耶！',
                '設定成功儲存！',
                'success'
            );
        });
        return false;
    });

    // load configurations and update the UI accordingly
    loadConfig();

    // keep the server alive every 20 second
    setInterval(function () {
        $.ajax({
            url: KEEP_ALIVE_URL + '?' + Date.now()
        });
    }, 20 * 1000);

    return false;
});
