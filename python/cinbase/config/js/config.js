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

var debugMode = false;

// unfortunately, here we use Windows-only features - ActiveX
// However, it's really stupid that Scripting.FileSystemObject does not support UTF-8.
// Luckily, there's an alternative, ADODB.Stream.
// Reference: http://stackoverflow.com/questions/2524703/save-text-file-utf-8-encoded-with-vba
// http://wiki.mcneel.com/developer/scriptsamples/readutf8
function readFile(path) {
    try {
        var stream = new ActiveXObject("ADODB.Stream");
        stream.Charset = "utf-8";
        stream.Open();
        stream.LoadFromFile(path);
        var data = stream.ReadText();
        stream.Close();
        return data;
    }
    catch(err) {
        return ""
    }
}

function writeFile(path, data) {
    try {
        var stream = new ActiveXObject("ADODB.Stream");
        stream.Charset = "utf-8";
        stream.Open();
        stream.WriteText(data);

        // this trick is used to strip unicode BOM
        // Reference: http://stackoverflow.com/questions/31435662/vba-save-a-file-with-utf-8-without-bom
        var binaryStream = new ActiveXObject("ADODB.Stream");
        binaryStream.Type = 1; // adTypeBinary: this is used to strip unicode BOM
        binaryStream.Open();
        stream.Position = 3; // skip unicode BOM
        stream.CopyTo(binaryStream); // convert the UTF8 data to binary
        binaryStream.SaveToFile(path, 2);
        binaryStream.Close();
        stream.Close();
    }
    catch(err) {
        alert(err);
    }
}

// This is Windows-only :-(
function getConfigDir() {
    var shell = new ActiveXObject("WScript.Shell");
    var dirPath = shell.ExpandEnvironmentStrings("%APPDATA%\\PIME");
    // ensure that the folder exists
    var fso = new ActiveXObject("Scripting.FileSystemObject");
    if(!fso.FolderExists(dirPath)) {
        fso.CreateFolder(dirPath);
    }
    dirPath += "\\" + imeFolderName;
    if(!fso.FolderExists(dirPath)) {
        fso.CreateFolder(dirPath);
    }
    return dirPath;
}

// This is Windows-only :-(
function getDataDir() {
    progDir = location.pathname.replace( "input_methods\\" + imeFolderName + "\\config\\config.hta","cinbase\\data")
    return progDir;
}

var checjConfig = null;
var configDir = getConfigDir();
var configFile = configDir + "\\config.json";
var cinCount = null;
var cinCountFile = configDir + "\\cincount.json";
var dataDir = getDataDir();
var userSymbolsFile = configDir + "\\symbols.dat";
var symbolsChanged = false;
var userSwkbFile = configDir + "\\swkb.dat";
var swkbChanged = false;
var userFsymbolsFile = configDir + "\\fsymbols.dat";
var fsymbolsChanged = false;
var userPhraseFile = configDir + "\\userphrase.dat";
var phraseChanged = false;
var userFlangsFile = configDir + "\\flangs.dat";
var flangsChanged = false;

function loadConfig() {
    var str = readFile(configFile);
    try {
        checjConfig = JSON.parse(str);
    }
    catch(err) {
        checjConfig = {};
    }

    // add missing values
    for(key in defaultConfig) {
        if(!checjConfig.hasOwnProperty(key)) {
            checjConfig[key] = defaultConfig[key];
        }
    }

    str = readFile(cinCountFile);
    try {
        cinCount = JSON.parse(str);
    }
    catch(err) {
        cinCount = {};
    }

    // add missing values
    for(key in defaultcinCount) {
        if(!cinCount.hasOwnProperty(key)) {
            cinCount[key] = defaultcinCount[key];
        }
    }

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

    // load symbols.dat
    str = readFile(userSymbolsFile);
    if(str == "")
        str = readFile(dataDir + "\\symbols.dat");
    $("#symbols").val(str);

    // load swkb.dat
    str = readFile(userSwkbFile);
    if(str == "")
        str = readFile(dataDir + "\\swkb.dat");
    $("#ez_symbols").val(str);
    
    // load fsymbols.dat
    str = readFile(userFsymbolsFile);
    if(str == "")
        str = readFile(dataDir + "\\fsymbols.dat");
    $("#fs_symbols").val(str);
    
    // load phrase.dat
    str = readFile(userPhraseFile);
    if(str == "")
        str = readFile(dataDir + "\\userphrase.dat");
    $("#phrase").val(str);
    
    // load flangs.dat
    str = readFile(userFlangsFile);
    if(str == "")
        str = readFile(dataDir + "\\flangs.dat");
    $("#flangs").val(str);
}

function saveConfig() {
    str = JSON.stringify(checjConfig, null, 4);
    writeFile(configFile, str);

    if(symbolsChanged) {
        str = $("#symbols").val();
        writeFile(userSymbolsFile, str);
    }
    if(swkbChanged) {
        str = $("#ez_symbols").val();
        writeFile(userSwkbFile, str);
    }
    if(fsymbolsChanged) {
        str = $("#fs_symbols").val();
        writeFile(userFsymbolsFile, str);
    }
    if(phraseChanged) {
        str = $("#phrase").val();
        writeFile(userPhraseFile, str);
    }
    if(flangsChanged) {
        str = $("#flangs").val();
        writeFile(userFlangsFile, str);
    }
}

// update checjConfig object with the value set by the user
function updateConfig() {
    // get values from checkboxes
    $("input").each(function(index, elem) {
        var item = $(this);
        var id = item.attr("id");
        switch(item.attr("type")) {
        case "checkbox":
            checjConfig[id] = item.prop("checked");
            break;
        case "text":
            var val = item.val();
            if(typeof checjConfig[id] == "number") {
                var intVal = parseInt(val);
                if(!isNaN(intVal))
                    val = intVal;
            }
            checjConfig[id] = val;
            break;
        }
    });
    // selCin
    var selCin = parseInt($("#selCinType").find(":selected").val());
    if(!isNaN(selCin))
        checjConfig.selCinType = selCin;

    // selWildcard
    var selWildcard = parseInt($("#selWildcardType").find(":selected").val());
    if(!isNaN(selWildcard))
        checjConfig.selWildcardType = selWildcard;

    // keyboardLayout
    var keyboardLayout = parseInt($("#keyboard_page").find("input:radio:checked").val());
    if(!isNaN(keyboardLayout))
        checjConfig.keyboardLayout = keyboardLayout;

    // selDayiSymbolChar
    if(imeFolderName == "chedayi") {
        var selDayiSymbolChar = parseInt($("#selDayiSymbolCharType").find(":selected").val());
        if(!isNaN(selDayiSymbolChar))
            checjConfig.selDayiSymbolCharType = selDayiSymbolChar;
    }
}

// jQuery ready
$(function() {
    // show PIME version number
    $("#tabs").hide();
    $("#version").load("../../../../version.txt");
    $("#typing_page").load("../../../cinbase/config/config.htm #typing_page")
    $("#cin_count").load("../../../cinbase/config/config.htm #cin_count")
    $("#ui_page").load("../../../cinbase/config/config.htm #ui_page")
    $("#symbols_page").load("../../../cinbase/config/config.htm #symbols_page")
    $("#fs_symbols_page").load("../../../cinbase/config/config.htm #fs_symbols_page")
    $("#ez_symbols_page").load("../../../cinbase/config/config.htm #ez_symbols_page")
    $("#phrase_page").load("../../../cinbase/config/config.htm #phrase_page")
    $("#flangs_page").load("../../../cinbase/config/config.htm #flangs_page")
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
    loadConfig();
    $(document).tooltip();
    $("#tabs").tabs({heightStyle:"auto"});

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
    
    $("#buttons").buttonset();
    $("#ok").click(function() {
        updateConfig();
        saveConfig();
        window.close();
        return false;
    });

    $("#cancel").click(function() {
        window.close();
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

}
