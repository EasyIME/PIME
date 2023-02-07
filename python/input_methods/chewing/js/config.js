$(function () {
    var chewingConfig = {},
        symbolsChanged = false,
        swkbChanged = false,
        DEBUG = false,
        CONFIG_URL = "/config",
        VERSION_URL = "/version.txt",
        KEEP_ALIVE_URL = "/keep_alive";

    if (DEBUG) {
        // load data from text file for testing or developing
        CONFIG_URL = "debug" + CONFIG_URL;
        VERSION_URL = "debug" + VERSION_URL;
        KEEP_ALIVE_URL = "debug" + KEEP_ALIVE_URL;
    }

    function loadConfig() {
        $.get(
            CONFIG_URL,
            function (data, status) {
                chewingConfig = data.config;
                $("#symbols").val(data.symbols);
                $("#ez_symbols").val(data.swkb);
                initializeUI();
            },
            "json"
        );
    }

    function saveConfig(callbackFunc) {
        // Check easy symbols format
        let ez_symbols_array = $("#ez_symbols").val().split("\n");
        for (let i = 0; i < ez_symbols_array.length; i++) {
            if (!/^[A-Z][ ].{1,10}$/.test(ez_symbols_array[i])) {
                // Select error range
                $("#ez_symbols").select();
                let selectionStart = 0;
                for (let j = 0; j < i; j++) {
                    selectionStart += ez_symbols_array[j].length + 1;
                }
                $("#ez_symbols").prop("selectionStart", selectionStart);
                $("#ez_symbols").prop("selectionEnd", selectionStart + ez_symbols_array[i].length + 1);
                swal.fire(
                    "輸入錯誤",
                    `第 ${i} 行格式錯誤：<br><b>${ez_symbols_array[i]}</b><br>請使用「英文大寫 + 空格 + 字串」的格式，字串最多10個字元`,
                    "error"
                );
                return false;
            }
        }

        // Check symbols format
        let symbols_array = $("#symbols").val().split("\n");
        for (let i = 0; i < symbols_array.length; i++) {
            if (symbols_array[i].length > 1 && symbols_array[i].search("=") === -1) {
                // Select error range
                $("#symbols").select();
                let selectionStart = 1;
                for (let j = 0; j < i; j++) {
                    selectionStart += symbols_array[j].length;
                }
                $("#symbols").prop("selectionStart", selectionStart);
                $("#symbols").prop("selectionEnd", selectionStart + symbols_array[i].length);
                swal.fire(
                    "輸入錯誤",
                    `特殊符號設定第 ${i + 1} 行格式錯誤：<br><b>${symbols_array[i]}</b><br>單行不能超過一個字元，或是沒有 = 符號區隔`,
                    "error"
                );
                return false;
            }
        }

        let data = {
            config: chewingConfig,
        };

        // Append "\n" on symbols end prevent error
        if (symbolsChanged) {
            if ($("#symbols").val().slice(-1) !== "\n") {
                $("#symbols").val(`${$("#symbols").val()}\n`);
            }
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
            dataType: "json",
        });
    }

    // Update chewingConfig object with the value set by the user
    function updateConfig() {
        // Reset chewingConfig, for change config_tool
        chewingConfig = {};

        // Get values from checkboxes, text and radio
        $(".container input").each(function (index, inputItem) {
            switch (inputItem.type) {
                case "checkbox":
                    chewingConfig[inputItem.name] = inputItem.checked;
                    break;
                case "text":
                case "number":
                    let inputValue = inputItem.value;
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
        $(".container select").each(function (index, selectItem) {
            if (selectItem.value) {
                chewingConfig[selectItem.name] = parseInt(selectItem.value);
            }
        });
    }

    // Initialize UI
    function initializeUI() {
        // Setup checkbox and text values
        $(".container input").each(function () {
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
        let selectOptions = {
            switchLangWithWhichShift: ["左右兩邊都使用", "僅使用左 Shift", "僅使用右 Shift"],
            upDownAction: ["移動游標選字", "在選字時翻頁"],
            leftRightAction: ["移動游標選字（循環）", "在選字時翻頁"],
            spaceKeyAction: {
                1: "叫出選字視窗",
                0: "輸出空格",
                2: "移動到選字頂端",
            },
            spaceKeyCandidatesAction: {
                1: "移動游標（循環）",
                0: "翻頁",
            },
            selKeyType: ["1234567890", "asdfghjkl;", "asdfzxcv89", "asdfjkl789", "aoeuhtn789", "1234qweras"],
            addPhraseForward: ["後方的詞", "前方的詞"],
        };

        $.each(selectOptions, function (id, options) {
            $.each(options, function (value, optionName) {
                $("#" + id).append('<option value="' + value + '">' + optionName + "</option>");
                if (value == chewingConfig[id]) {
                    $(`#${id} option:last-child`).prop("selected", true);
                }
            });
        });

        // Setup switchLangWithWhichShift's default disabled property
        $("#switchLangWithWhichShift").prop("disabled", !chewingConfig["switchLangWithShift"]);

        // Bind Bootstrap
        $(".container select").selectpicker();
        $('[data-toggle="popover"]').popover();

        // When switchLangWithShift's value changed, update switchLangWithWhichShift's disabled property
        $("#switchLangWithShift").on("click", function () {
            $("#switchLangWithWhichShift").prop("disabled", !this.checked).selectpicker("refresh");
        });

        // Bind shift action event
        $("#switchLangWithShift").on("click", function () {
            if (this.checked) {
                $("#shiftMoveCursor").prop("checked", false);
            }
        });
        $("#shiftMoveCursor").on("click", function () {
            if (this.checked) {
                $("#switchLangWithShift").prop("checked", false);
                $("#switchLangWithWhichShift").prop("disabled", true).selectpicker("refresh");
            }
        });

        // Setup select phrase example & Bind updateSelExample event
        updateSelExample();
        $("#ui_tab input, #ui_tab select").on("change keyup", updateSelExample);

        // Setup keybord page
        let keyboardNames = [
            ["預設", "default-chewing"],
            ["許氏鍵盤", "hsu"],
            ["IBM", "ibm"],
            ["精業", "jingye"],
            ["倚天 41 鍵", "et41"],
            ["倚天 26 鍵", "et26"],
            ["DVORAK", "dvorak-chewing"],
            ["DVORAK 許氏鍵盤", "dvorak-hsu"],
            ["大千 26 鍵", "dacian26"],
            ["漢語拼音", "pinyin"],
            ["台灣華語羅馬拼音", "pinyin"],
            ["注音二式", "pinyin"],
            ["CARPALX", "carpalx"],
        ];

        let item = '<img id="keyboard_layouts" src="images\\keyborad_layouts\\pinyin.png" alt="pinyin">';

        for (let i = 0; i < keyboardNames.length; ++i) {
            let id = `kb${i}`;
            let name = keyboardNames[i][0];
            let layout = keyboardNames[i][1];
            item +=
                '<div class="custom-control custom-radio">' +
                '<input class="custom-control-input" type="radio" id="' +
                id +
                '" name="keyboardLayout" value="' +
                i +
                '" data-layout="' +
                layout +
                '">' +
                '<label class="custom-control-label" for="' +
                id +
                '">' +
                name +
                "</label><br>" +
                "</div>";
        }
        $("#keyboard_tab").html(item);

        // Checked keyboard layout radio
        let checkedKetboardLayoutRadio = $(`#kb${chewingConfig.keyboardLayout}`);
        checkedKetboardLayoutRadio.prop("checked", true);
        $("#keyboard_layouts").prop("src", `images/keyborad_layouts/${checkedKetboardLayoutRadio.data("layout")}.png`);
        $("#keyboard_layouts").prop("alt", checkedKetboardLayoutRadio.data("layout"));

        // Bind change keyboard_layouts event
        $("#keyboard_tab input:radio").on("click", function () {
            let layout_file_name = $(this).data("layout");
            $("#keyboard_layouts").fadeOut(200, function () {
                $("#keyboard_layouts").prop("src", `images/keyborad_layouts/${layout_file_name}.png`);
                $("#keyboard_layouts").prop("alt", layout_file_name);
            });

            $("#keyboard_layouts").fadeIn(200);
        });
    }

    // Use for select phrase example
    function updateSelExample() {
        let example = ["選", "字", "視", "窗", "大", "小", "範", "例"];
        let selectItems = $("#selKeyType option").eq($("#selKeyType").val()).html();
        let html = "";

        for (let number = 0, i = 0, row = 0; number < $("#candPerPage").val(); number++, i++, row++) {
            if (example[i] == null) {
                i = 0;
            }

            if (row == $("#candPerRow").val()) {
                row = 0;
                html += "<br>";
            }

            html += `<span>${selectItems.substr(number, 1)}.</span>${example[i]}`;
        }

        $("#selExample").html(html);
        $("#selExample").css("font-size", `${$("#fontSize").val()}pt`);
    }

    // workaround the same origin policy of IE.
    // http://stackoverflow.com/questions/7852225/is-it-safe-to-use-support-cors-true-in-jquery
    $.support.cors = true;

    // Show PIME version number
    $("#version").load(VERSION_URL);

    // Setup UI
    $("#symbols").on("change", function () {
        symbolsChanged = true;
    });

    $("#ez_symbols").on("change", function () {
        swkbChanged = true;
    });

    // OK button
    $("#ok").on("click", function () {
        updateConfig(); // update the config based on the state of UI elements
        saveConfig(function () {
            swal.fire("好耶！", "設定成功儲存！", "success");
        });
        return false;
    });

    // Load configurations and update the UI accordingly
    loadConfig();

    // Keep the server alive every 20 second
    setInterval(function () {
        $.ajax({
            url: KEEP_ALIVE_URL + "?" + Date.now(),
        });
    }, 20 * 1000);

    // Bind test input auto select
    $("#test_input").on("shown.bs.modal", function () {
        $("#test_input_text").val("").select();
    });

    return false;
});
