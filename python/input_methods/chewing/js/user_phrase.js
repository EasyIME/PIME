// Load user phrases
function loadUserPhrases() {
    // Reload effect
    var loading_message = $("<div>", {
        id: "loading_message",
        css: {
            "font-size": "20px",
            "background-color": "grey",
            "padding": "10px",
            "border-radius": "15px"
        },
        text: "載入詞彙中，請稍後..."
    });
    $("body").LoadingOverlay("show", { color: "rgba(80, 80, 80, 0.8)", fade: [0, 400], custom: loading_message });  
    $("#reload").html("載入中...");
    $("#reload").addClass("ui-state-hover");

    // Get user_phrases
    $.get("/user_phrases", function (data, status) {
        if (data.data != undefined) {
            var table_content = "";
            $.each(data.data, function (i, user_phrase) {
                table_content += '<tr><td><input type="checkbox" data-phrase="' + user_phrase.phrase + '" data-bopomofo="' + user_phrase.bopomofo + '">' + user_phrase.phrase + '</td><td>' + user_phrase.bopomofo + '</td><td><button>刪除「' + user_phrase.phrase + '」</button></td></tr>';
            });
            $("#table_content").html(table_content);
            $("#phrase_count").html("共&nbsp;" + data.data.length + "&nbsp;個詞彙");
        }

        // Reload complete effect
        $.LoadingOverlay("hide", true);
        $("#reload").html("重新載入");
        $("#reload").removeClass("ui-state-hover");

        // Register remove phrase button click event
        $("#table_content button").click(function () {
            var delete_phrase = {
                phrase: $(this).parent().prev().prev().children().data("phrase"),
                bopomofo: $(this).parent().prev().prev().children().data("bopomofo")
            };
            onRemovePhrase(delete_phrase);
        });

        // Register select phrase checked effect
        $("#table_content input").click(function () {
            $(this).parent().parent().toggleClass("phrase_selected");
        });
    }, "json");
}

// called when the OK button of the "add phrase" dialog is clicked
function onAddPhrase() {
    var phrase = $("#phrase_input").val();
    var bopomofo = $("#bopomofo_input").val();

    // Check phrase has repeated
    var phrase_repeated;
    var phrase_repeated_index;
    $("#table_content input[type=checkbox]").each(function (idx, item) {
        if (phrase == $(item).data("phrase")) {
            phrase_repeated = true;
            phrase_repeated_index = idx;
            return false;
        }
    });

    if (phrase_repeated == true) {
        var phrase_repeated_item = $("#table_content input[type=checkbox]:eq(" + phrase_repeated_index + ")");
        $('html, body').animate({ scrollTop: phrase_repeated_item.offset().top - 200 }, 200);
        $("#add_dialog").dialog("close");
        phrase_repeated_item.parent().effect("highlight", { color: '#f2f207' }, 5000);
        phrase_repeated_item.parent().append("<small>（已重複）</small>");
        window.setInterval(function () { phrase_repeated_item.parent().children("small").remove(); }, 4000);
        return;
    }

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
        success: function () {
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

        var confirm_text = "確定刪除以下" + $("#table_content input[type=checkbox]:checked").length + "個詞彙？（此動作無法復原）";
        $("#table_content input[type=checkbox]:checked").each(function (idx, item) {
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
        data: JSON.stringify({ remove: phrases }),
        dataType: "json",
        success: function () {
            alert("刪除詞彙成功！");
            loadUserPhrases();
        }
    });
}

// jQuery ready
$(function () {
    // workaround the same origin policy of IE.
    // http://stackoverflow.com/questions/7852225/is-it-safe-to-use-support-cors-true-in-jquery
    $.support.cors = true;

    // setup UI
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
                click: function () {
                    $(this).dialog("close");
                }
            }
        ]
    });

    $("#add").click(function () {
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
    window.setInterval(function () {
        $.ajax({
            url: "/keep_alive",
            cache: false // needs to turn off cache. otherwise the server will be requested only once.
        });
    }, 20 * 1000);
});