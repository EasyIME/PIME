defaultConfig ={
    "keyboardLayout": 0,
    // "addPhraseForward": true,
    "defaultEnglish": false,
    "candPerRow": 3,
    "easySymbolsWithShift": true,
    //"easySymbolsWithCtrl": false,
    "candPerPage": 9,
    "defaultFullSpace": false,
    "selCinFile": "0",
    // "phraseMark": 1,
    "switchLangWithShift": true,
    // "enableCapsLock": true,
    // "showCandWithSpaceKey": false,
    "fullShapeSymbols": true,
    "colorCandWnd": true,
    // "advanceAfterSelection": true,
    "fontSize": 16,
    "outputSimpChinese": false,
    // "upperCaseWithShift": false,
    // "escCleanAllBuf": false,
    // "cursorCandList": true
};

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
    var dirPath = shell.ExpandEnvironmentStrings("%USERPROFILE%\\PIME");
    // ensure that the folder exists
    var fso = new ActiveXObject("Scripting.FileSystemObject");
    if(!fso.FolderExists(dirPath)) {
        fso.CreateFolder(dirPath);
    }
    dirPath += "\\checj";
    if(!fso.FolderExists(dirPath)) {
        fso.CreateFolder(dirPath);
    }
    return dirPath;
}

// This is Windows-only :-(
function getDataDir() {
    var shell = new ActiveXObject("WScript.Shell");
    var progDir = shell.ExpandEnvironmentStrings("%PROGRAMFILES(x86)%");
    if(progDir.charAt(0) == "%") { // expansion failed
        progDir = shell.ExpandEnvironmentStrings("%PROGRAMFILES");
    }
    // FIXME: it's bad to hard code the path, but is there any better way?
    return progDir + "\\PIME\\server\\input_methods\\checj\\data";
}

var chewingConfig = null;
var configDir = getConfigDir();
var configFile = configDir + "\\config.json";
var dataDir = getDataDir();
var userSymbolsFile = configDir + "\\symbols.dat";
var symbolsChanged = false;
var userSwkbFile = configDir + "\\swkb.dat";
var swkbChanged = false;

function loadConfig() {
    var str = readFile(configFile);
    try {
        chewingConfig = JSON.parse(str);
    }
    catch(err) {
        chewingConfig = {};
    }
    // add missing values
    for(key in defaultConfig) {
        if(!chewingConfig.hasOwnProperty(key)) {
            chewingConfig[key] = defaultConfig[key];
        }
    }

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
}

function saveConfig() {
    str = JSON.stringify(chewingConfig, null, 4);
    writeFile(configFile, str);

    if(symbolsChanged) {
        str = $("#symbols").val();
        writeFile(userSymbolsFile, str);
    }
    if(swkbChanged) {
        str = $("#ez_symbols").val();
        writeFile(userSwkbFile, str);
    }
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
    // selCin
    var selCin = parseInt($("#selCinFile").find(":selected").val());
    if(!isNaN(selCin))
        chewingConfig.selCinFile = selCin;
}

// jQuery ready
$(function() {
    // show PIME version number
    $("#version").load("../../../../version.txt");

    loadConfig();
    $(document).tooltip();
    $("#tabs").tabs({heightStyle:"auto"});

    $("#candPerRow").spinner({min:1, max:10});
    $("#candPerPage").spinner({min:1, max:10});
    $("#fontSize").spinner({min:6, max:200});

    var selCins=[
        "酷倉",
        "倉頡",
        "倉頡(大字集)",
        "中標倉頡",
        "泰瑞倉頡",
        "亂倉打鳥"
    ];
    var selCinFile = $("#selCinFile");
    for(var i = 0; i < selCins.length; ++i) {
        var selCin = selCins[i];
        var item = '<option value="' + i + '">' + selCin + '</option>';
        selCinFile.append(item);
    }
    selCinFile.children().eq(chewingConfig.selCinFile).prop("selected", true);

    $("#symbols").change(function(){
        symbolsChanged = true;
    });

    $("#ez_symbols").change(function(){
        swkbChanged = true;
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
	$("#selExample").css("font-size", $("#fontSize").val() + "px");
	updateSelExample();

	// trigger event
	$('.ui-spinner-button').click(function() {
		$(this).siblings('input').change();		
	});	
	
	$("#ui_page input").on("change", function() {
		$("#selExample").css("font-size", $("#fontSize").val() + "px");
		updateSelExample();
	});
	
	$("#ui_page input").on("keydown", function(e) {
		if (e.keyCode == 38 || e.keyCode==40) {
			$("#selExample").css("font-size", $("#fontSize").val() + "px");
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
});
