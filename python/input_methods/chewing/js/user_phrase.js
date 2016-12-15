function loadUserPhrases() {
    // Loading effect
    $("#reload .ui-button-text").html("載入中...");
    $("#reload").addClass("ui-state-hover");

    $.get("/user_phrases", function(data, status) {
        if (data.data != undefined) {
            var user_phrases = data.data;
            var table_content = "";
            for (var i = 0; i < user_phrases.length; ++i) {
                table_content += '<tr><td><input type="checkbox" data-phrase="' + user_phrases[i].phrase + '" data-bopomofo="' + user_phrases[i].bopomofo + '">' + user_phrases[i].phrase + '</td><td>' + user_phrases[i].bopomofo + '</td><td><button class="remove_phrase">刪除「' + user_phrases[i].phrase + '」</button></td></tr>';
            }
            $("#table_content").html(table_content);
        }

        $("#phrase_count").html("共&nbsp;" + user_phrases.length + "&nbsp;個詞彙");

        // Disable loading effect
        $("#reload .ui-button-text").html("重新載入");
        $("#reload").removeClass("ui-state-hover");

        // Register remove phrase button click event
        $(".remove_phrase").click(function() {
            var delete_phrase = {
                phrase: $(this).parent().prev().prev().children().data("phrase"),
                bopomofo: $(this).parent().prev().prev().children().data("bopomofo")
            };
            onRemovePhrase(delete_phrase);
        });

        // Register select phrase checked effect
        $("#table_content input").click(function() {
            $(this).parent().parent().toggleClass("phrase_selected");
        });
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

// Execute remove phrase
function onRemovePhrase(delete_phrase) {
    var phrases = [];
    if (delete_phrase.phrase == null) {
        if ($("#table_content input[type=checkbox]:checked").length == 0)
            return;

        var confirm_text = "確定刪除以下詞彙？（此動作無法復原）";
        $("#table_content input[type=checkbox]:checked").each(function(idx, item) {
            confirm_text += "\n- " + $(item).data("phrase");
            phrases.push({
                phrase: $(item).data("phrase"), // 詞彙
                bopomofo: $(item).data("bopomofo") // 注音
            });
        });
    } else {
        var confirm_text = "確定刪除詞彙「" + delete_phrase.phrase + "」？（此動作無法復原）";
        phrases.push(delete_phrase);
    }

    if (!confirm(confirm_text))
        return;

    $.ajax({
        url: "/user_phrases",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({remove: phrases}),
        dataType: "json",
        success: function() {
            alert("刪除詞彙成功！");
            loadUserPhrases();
        }
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
            }, {
                text: "取消",
                click: function() {
                    $(this).dialog("close");
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
            url: "/keep_alive", cache: false // needs to turn off cache. otherwise the server will be requested only once.
        });
    }, 20 * 1000);
});
