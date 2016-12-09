var chewingConfig = {};
var symbolsChanged = false;
var swkbChanged = false;

function loadConfig() {
    $.get("/config", function(data, status) {
		chewingConfig = data.config;
		$("#symbols").val(data.symbols);
		$("#ez_symbols").val(data.swkb);
        initializeUI();
    }, "json");
}

function saveConfig(callbackFunc) {
    // Check symbols format
    var symbols_array = $("#symbols").val().split("\n");
    for (var i = 0; i < symbols_array.length; i++) {
        if (symbols_array[i].length > 1 && symbols_array[i].search("=") == -1) {
            $("#tabs").tabs( "option", "active", 3);
            $("#symbols").blur();
            
            // Count select range          
            var selectionStart = 1;
            for (var j = 0; j < i; j++) {
                selectionStart += symbols_array[j].length;
            }
            $("#symbols").prop("selectionStart", selectionStart);            
            $("#symbols").prop("selectionEnd",  selectionStart + symbols_array[i].length);            
            alert("特殊符號設定第 " + (i + 1) + " 行格式錯誤\n單行不能超過一個字元，或是沒有'='符號區隔");
            return;
        }
    }    
    
    var data = {
        "config": chewingConfig
    }
    if(symbolsChanged) {
        data.symbols = $("#symbols").val();
    }
    if(swkbChanged) {
        data.swkb = $("#ez_symbols").val();
    }

    $.ajax({
        url: "/config",
        method: "POST",
        success: callbackFunc,
        contentType: "application/json",
        data: JSON.stringify(data),
        dataType:"json"
    });
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
}

// jQuery ready
$(function() {
    // workaround the same origin policy of IE.
    // http://stackoverflow.com/questions/7852225/is-it-safe-to-use-support-cors-true-in-jquery
    $.support.cors = true;

    // show PIME version number
    $("#version").load("/version.txt");

    // setup UI
    $(document).tooltip();

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
			alert("設定已儲存!");
		});
        return false;
    });

    // load configurations and update the UI accordingly
    loadConfig();

    // keep the server alive every 20 second
    window.setInterval(function() {
        $.ajax({
            url: "/keep_alive",
            cache: false  // needs to turn off cache. otherwise the server will be requested only once.
        });
    }, 20 * 1000);
});
