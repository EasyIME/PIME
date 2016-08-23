var apiUrl = "";
var authToken = "";

var defaultConfig ={
    "keyboardLayout": 0,
    "addPhraseForward": true,
    "defaultEnglish": false,
    "candPerRow": 3,
    "easySymbolsWithShift": true,
    "easySymbolsWithCtrl": false,
    "candPerPage": 9,
    "defaultFullSpace": false,
    "selKeyType": "0",
    // "phraseMark": 1,
    "switchLangWithShift": true,
    "enableCapsLock": true,
    "showCandWithSpaceKey": false,
    "fullShapeSymbols": true,
    "colorCandWnd": true,
    "advanceAfterSelection": true,
    "fontSize": 12,
    "outputSimpChinese": false,
    "upperCaseWithShift": false,
    "escCleanAllBuf": false,
    "cursorCandList": true
};

var chewingConfig = {};
var symbolsChanged = false;
var swkbChanged = false;

function loadConfig() {
    $.get(apiUrl + "load/config", function(data, status) {
		chewingConfig = data;
        // add missing values
        for(key in defaultConfig) {
            if(!chewingConfig.hasOwnProperty(key)) {
                chewingConfig[key] = defaultConfig[key];
            }
        }
        initializeUI();
    }, "json");

    // load symbols.dat
	$.get(apiUrl + "load/symbols", function(data, status) {
		$("#symbols").val(data);
	});

    // load swkb.dat
	$.get(apiUrl + "load/swkb", function(data, status) {
		$("#ez_symbols").val(data);
	});
}

function saveConfig(callbackFunc) {
    var str = JSON.stringify(chewingConfig, null, 4);
    var requests = new Array();
    requests.push($.post(apiUrl + "save/config",
        { data: str }
    ));

    if(symbolsChanged) {
        str = $("#symbols").val();
        requests.push($.post(apiUrl + "save/symbols",
            { data: str }
        ));
    }
    if(swkbChanged) {
        str = $("#ez_symbols").val();
        requests.push($.post(apiUrl + "save/swkb",
            { data: str }
        ));
    }
    // jQuery.when() receives any number of arguments, but since we have variable
    // number of arguments, we use javascript method.apply() to workaround the limitation.
    // Reference: http://stackoverflow.com/questions/14777031/what-does-when-apply-somearray-do
    // call the callback function when all requests are done
    $.when.apply($, requests).done(callbackFunc);
}

// update chewingConfig object with the value set by the user
function updateConfig() {
    // get values from checkboxes
    $("input").each(function(index, elem) {
        var item = $(this);
        var id = item.attr("id");
        switch(item.attr("type")) {
        case "checkbox":
            chewingConfig[id] = item.prop("checked");
            break;
        case "text":
            var val = item.val();
            if(typeof chewingConfig[id] == "number") {
                var intVal = parseInt(val);
                if(!isNaN(intVal))
                    val = intVal;
            }
            chewingConfig[id] = val;
            break;
        }
    });
    // selKey
    var selKey = parseInt($("#selKeyType").find(":selected").val());
    if(!isNaN(selKey))
        chewingConfig.selKeyType = selKey;

    // keyboardLayout
    var keyboardLayout = parseInt($("#keyboard_page").find("input:radio:checked").val());
    if(!isNaN(keyboardLayout))
        chewingConfig.keyboardLayout = keyboardLayout;
}

function initializeUI() {

    var selKeys=[
        "1234567890",
        "asdfghjkl;",
        "asdfzxcv89",
        "asdfjkl789",
        "aoeuhtn789",
        "1234qweras"
    ];
    var selKeyType = $("#selKeyType");
    for(var i = 0; i < selKeys.length; ++i) {
        var selKey = selKeys[i];
        var item = '<option value="' + i + '">' + selKey + '</option>';
        selKeyType.append(item);
    }
    selKeyType.children().eq(chewingConfig.selKeyType).prop("selected", true);
    // $("#selKeyType").selectmenu();

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
        "注音二式"
        // wait for update libchewing 5.0
        // "CARPALX",
        // "注音二式"
    ];
    var keyboard_page = $("#keyboard_page");
    for(var i = 0; i < keyboardNames.length; ++i) {
        var id = "kb" + i;
        var name = keyboardNames[i];
        var item = '<input type="radio" id="' + id + '" name="keyboardLayout" value="' + i + '">' +
            '<label for="' + id + '">' + name + '</label><br />';
        keyboard_page.append(item);
    }
    $("#kb" + chewingConfig.keyboardLayout).prop("checked", true);

    // set all initial values
    $("input").each(function(index, elem) {
        var item = $(this);
        var value = chewingConfig[item.attr("id")];
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

    /*
    // resize and center the window
    $(window).load(function() {
        window.resizeTo($(document).width(), $(document).height() + 40);
        window.moveTo((screen.width - $(window).width())/2, (screen.height - $(window).height() - 40)/2);
    });
    */
}

// Microsoft HTA only  :-(
function initAPIUrl() {
    // get port number from HTA command line parameters
    var params = ChewingConfig.commandLine.split(" ")
    if(params.length > 2) {
        authToken = params.pop();
        var port = params.pop();
        apiUrl = "http://localhost:" + port + "/";
    }
}

function closeWindow() {
    $.get(apiUrl + "quit", function() {
        window.close();
    });
}

// jQuery ready
$(function() {

    initAPIUrl();  // initialize the URL of API server
    
    // workaround the same origin policy of IE.
    // http://stackoverflow.com/questions/7852225/is-it-safe-to-use-support-cors-true-in-jquery
    $.support.cors = true;

    // show PIME version number
    $("#version").load("../../../../version.txt");

    // setup UI
    $(document).tooltip();
    $(window).unload(function() {
        alert("unload");
        $.get(apiUrl + "quit");  // ask the server process to quit.
    });

    $("#tabs").tabs({heightStyle:"auto"});

    $("#candPerRow").spinner({min:1, max:10});
    $("#candPerPage").spinner({min:1, max:10});
    $("#fontSize").spinner({min:6, max:200});

    $("#symbols").change(function(){
        symbolsChanged = true;
    });

    $("#ez_symbols").change(function(){
        swkbChanged = true;
    });

    $("#buttons").buttonset();
    // OK button
    $("#ok").click(function() {
        updateConfig(); // update the config based on the state of UI elements
        saveConfig(function() {
            closeWindow(); // called when the save operations are done
        });
        return false;
    });

    // Cancel button
    $("#cancel").click(function() {
        closeWindow();
        return false;
    });
    
    // authenticate to the configuration web service
    $.post(apiUrl + "auth",
        {"token":authToken},
        function(data, status) {
            // load configurations and update the UI accordingly
            loadConfig();

            // keep the server alive every 30 second
            window.setInterval(function() {
                $.ajax({
                    url: apiUrl + "keep_alive",
                    cache: false  // needs to turn off cache. otherwise the server will be requested only once.
                });
            }, 5 * 1000);
        }
    );
});
