function loadUserPhrases() {
    $.get("/user_phrases", function(data, status) {
        if(data.data != undefined) {
            var user_phrases = data.data;
            var rows = [];
            for(var i = 0; i < user_phrases.length; ++i) {
                var item = user_phrases[i];
                var row = '<tr><td><input type="checkbox">' + item.phrase + '</td><td>' + item.bopomofo + '</td></tr>';
                rows.push(row);
            }
            var table_content = rows.join("\n");
            $("#table_content").html(table_content);
        }
    }, "json");
}

// called when the OK button of the "add phrase" dialog is clicked
function onAddPhrase() {
    var phrase = $("#phrase_input").val();
    var bopomofo = $("#bopomofo_input").val();
    var data = {
        add: [
            {
                phrase: phrase,
                bopomofo: bopomofo
            }
        ]
    }
    $.ajax({
        url: "/user_phrases",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify(data),
        dataType: "json",
        success: function() {
            // reload the user phrases
            loadUserPhrases();
            $("#add_dialog").dialog("close");
        }
    });
}

function onRemovePhrase() {
    if(!confirm("確定刪除? (無法復原)"))
        return;

    var phrases = [];
    $("#table_content input[type=checkbox]:checked").each(function(idx, item) {
        var phrase_td = $(item).parent();
        phrases.push({
            phrase: phrase_td.text(),  // 詞彙
            bopomofo: phrase_td.next().text() // 注音
        });
    });
    var data = {
        remove: phrases
    };
    $.ajax({
        url: "/user_phrases",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify(data),
        dataType: "json",
        success: loadUserPhrases
    });
}

// jQuery ready
$(function() {
    // workaround the same origin policy of IE.
    // http://stackoverflow.com/questions/7852225/is-it-safe-to-use-support-cors-true-in-jquery
    $.support.cors = true;

    // setup UI
    // $(document).tooltip();
    $("#buttons").buttonset();
    
    // add phrase dialog
    $("#add_dialog").dialog({
        autoOpen: false,
        buttons: [
            {
                text: "確定",
                click: onAddPhrase
            },
            {
                text: "取消",
                click: function() {
                    $(this).dialog( "close" );
                }
            }
        ]
    });

    $("#add").click(function() {
        $("#phrase_input").val("");
        $("#bopomofo_input").val("");
        $("#add_dialog").dialog("open");
    });
    $("#remove").click(onRemovePhrase);
    $("#reload").click(loadUserPhrases);
    // $("#import").click(onImportPhrase);
    // $("#export").click(onExportPhrase);

    loadUserPhrases();
    
    // keep the server alive every 20 second
    window.setInterval(function() {
        $.ajax({
            url: "/keep_alive",
            cache: false  // needs to turn off cache. otherwise the server will be requested only once.
        });
    }, 20 * 1000);
});
