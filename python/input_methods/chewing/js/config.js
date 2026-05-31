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
                applyCandidateDefaults();
                $("#symbols").val(data.symbols);
                $("#ez_symbols").val(data.swkb);
                initializeUI();
            },
            "json"
        );
    }

    function applyCandidateDefaults() {
        if (typeof chewingConfig.candidateModernStyle === "undefined") {
            chewingConfig.candidateModernStyle = true;
        }
        if (typeof chewingConfig.candidateStableWidth === "undefined") {
            chewingConfig.candidateStableWidth = true;
        }
        if (typeof chewingConfig.candidateMinWidth === "undefined" || chewingConfig.candidateMinWidth < 160) {
            chewingConfig.candidateMinWidth = 286;
        }
        if (typeof chewingConfig.candidateWrapToMaxWidth === "undefined") {
            chewingConfig.candidateWrapToMaxWidth = true;
        }
        if (typeof chewingConfig.candidateMaxWidth === "undefined" || chewingConfig.candidateMaxWidth < 220) {
            chewingConfig.candidateMaxWidth = 300;
        }
        if (typeof chewingConfig.candidateTheme === "undefined") {
            chewingConfig.candidateTheme = "Night Comfort";
        }
        else if (chewingConfig.candidateTheme === "dark") {
            chewingConfig.candidateTheme = "Night Comfort";
        }
        else if (chewingConfig.candidateTheme === "light") {
            chewingConfig.candidateTheme = "Light";
        }
        if (typeof chewingConfig.candidateKeyStyle === "undefined") {
            chewingConfig.candidateKeyStyle = "keycap";
        }
        else if (chewingConfig.candidateKeyStyle === "underline" || chewingConfig.candidateKeyStyle === "rule" || chewingConfig.candidateKeyStyle === "rule-key") {
            chewingConfig.candidateKeyStyle = "word-anchor";
        }
        if (typeof chewingConfig.candidateMessageStyle === "undefined") {
            chewingConfig.candidateMessageStyle = "badge";
        }
        if (typeof chewingConfig.candidateMessageBehavior === "undefined") {
            chewingConfig.candidateMessageBehavior = "progressive";
        }
        var validCandidateKeyStyles = {
            keycap: true,
            quiet: true,
            divider: true,
            badge: true,
            "accent-dot": true,
            rail: true,
            "monospace-slot": true,
            "word-first": true,
            "soft-capsule": true,
            "left-tag": true,
            "glow-key": true,
            "micro-tab": true,
            "word-anchor": true
        };
        if (!validCandidateKeyStyles[chewingConfig.candidateKeyStyle]) {
            chewingConfig.candidateKeyStyle = "keycap";
        }
        var validCandidateMessageStyles = {
            badge: true,
            bar: true,
            dot: true
        };
        if (!validCandidateMessageStyles[chewingConfig.candidateMessageStyle]) {
            chewingConfig.candidateMessageStyle = "badge";
        }
        var validCandidateMessageBehaviors = {
            fixed: true,
            progressive: true
        };
        if (!validCandidateMessageBehaviors[chewingConfig.candidateMessageBehavior]) {
            chewingConfig.candidateMessageBehavior = "progressive";
        }
        if (typeof chewingConfig.candidatePerRow === "undefined") {
            chewingConfig.candidatePerRow = 6;
        }
        if (typeof chewingConfig.candidateEdgeAvoidance === "undefined") {
            chewingConfig.candidateEdgeAvoidance = true;
        }
    }

    function bindTabsFallback() {
        $('.nav-tabs a[data-toggle="tab"]').on("click", function (event) {
            var target = $(this).attr("href");
            if (!target || target.charAt(0) !== "#") {
                return;
            }

            event.preventDefault();
            if ($.fn.tab) {
                $(this).tab("show");
                return;
            }

            $(this).closest(".nav-tabs").find(".nav-link").removeClass("active");
            $(this).addClass("active");
            $(".tab-content .tab-pane").removeClass("active show in");
            $(target).addClass("active show in");
        });
    }

    var candidateThemeNames = [
        "Night Comfort",
        "Soft Focus",
        "Warm Gray",
        "Graphite",
        "Slate Teal",
        "Olive",
        "Plum",
        "Amber",
        "Light",
        "Paper",
        "Mist Light",
        "Sepia Dim"
    ];

    var candidateThemePalette = {
        "Night Comfort": ["#1b1c20", "#4a4d57", "#30323a", "#e5e8ee", "#a9afba", "#b8c7e8", "#405f8a", "#5e7ea7", "#eef4ff", "#aeb9cf"],
        "Soft Focus": ["#191d21", "#44525a", "#2b343a", "#e4ebee", "#a8b5ba", "#9cc8bd", "#3f6f6b", "#6a9993", "#ecfbf8", "#a4bcb6"],
        "Warm Gray": ["#20201d", "#58554b", "#39372f", "#ebe7dc", "#b7b1a3", "#d7c48e", "#5f684d", "#87936f", "#f7f3e7", "#c1b8a2"],
        "Graphite": ["#12141a", "#444a57", "#292e38", "#f3f5fa", "#aeb5c4", "#8fb3ff", "#4169d7", "#6f92eb", "#edf3ff", "#9eb0d5"],
        "Slate Teal": ["#152027", "#3f5a64", "#263943", "#f0f8fb", "#a5bac2", "#87d4dd", "#2f7f9f", "#60adc8", "#e9fbff", "#98c2ca"],
        "Olive": ["#171b16", "#4b5941", "#2c3328", "#f4f7ef", "#b4bda7", "#b6df88", "#5d7f36", "#91b962", "#f4ffe8", "#b9c8a8"],
        "Plum": ["#1d1721", "#604b66", "#382c3e", "#fbf4ff", "#c0adca", "#e0a7ff", "#7a55b8", "#aa83e6", "#fbf3ff", "#c5a9d1"],
        "Amber": ["#211a12", "#68533a", "#3c2f22", "#fff8ed", "#cfbda4", "#ffc46f", "#9a6730", "#d59a58", "#fff3de", "#d4baa0"],
        "Light": ["#f7f9fc", "#aeb8cb", "#dbe2ed", "#182235", "#657187", "#2f66dc", "#2f6eea", "#1d56c4", "#ffffff", "#44639a"],
        "Paper": ["#fbfaf6", "#b7ac9c", "#e4ded4", "#272119", "#786b5d", "#8a4f17", "#315f87", "#244967", "#f7fbff", "#6f665c"],
        "Mist Light": ["#e9edf0", "#a8b3bc", "#d4dce1", "#24303a", "#66727d", "#426b85", "#5f7f94", "#4b687b", "#f7fbfd", "#577385"],
        "Sepia Dim": ["#28251f", "#5d564a", "#403a31", "#ebe2d3", "#b9ad9a", "#dfc58e", "#6d6547", "#958a63", "#f8efd9", "#c7b79e"]
    };

    var candidateKeyStyleOptions = {
        keycap: "Selected Only Keycap",
        quiet: "Quiet Key",
        divider: "Divider Slim",
        badge: "Badge Minimal",
        "accent-dot": "Accent Dot",
        rail: "Rail Marker",
        "monospace-slot": "Monospace Slot",
        "word-first": "Word First",
        "soft-capsule": "Soft Capsule",
        "left-tag": "Left Tag",
        "glow-key": "Glow Key",
        "micro-tab": "Micro Tab",
        "word-anchor": "Word Anchor"
    };

    var candidateMessageStyleOptions = {
        badge: "A Badge Alert",
        bar: "B Bar Notice",
        dot: "D Dot Signal"
    };

    var candidateMessageBehaviorOptions = {
        fixed: "固定樣式",
        progressive: "打字中低調，確認後明顯"
    };

    var candidateKeyStyleClassNames = [
        "key-style-keycap",
        "key-style-quiet",
        "key-style-divider",
        "key-style-badge",
        "key-style-accent-dot",
        "key-style-rail",
        "key-style-monospace-slot",
        "key-style-word-first",
        "key-style-soft-capsule",
        "key-style-left-tag",
        "key-style-glow-key",
        "key-style-micro-tab",
        "key-style-word-anchor"
    ];

    function getCandidatePreviewSample() {
        var selKeys = $("#selKeyType option:selected").text() || "1234567890";
        return {
            name: "新酷音",
            root: "ㄅ",
            candidates: ["班", "般", "搬", "斑", "伴", "辦", "半", "板", "版", "頒"],
            selKeys: selKeys
        };
    }

    function hexToRgb(color) {
        var value = (color || "").replace("#", "");
        if (value.length !== 6) {
            return null;
        }
        return {
            r: parseInt(value.substr(0, 2), 16),
            g: parseInt(value.substr(2, 2), 16),
            b: parseInt(value.substr(4, 2), 16)
        };
    }

    function blendHex(a, b, percentB) {
        var rgbA = hexToRgb(a);
        var rgbB = hexToRgb(b);
        if (!rgbA || !rgbB) {
            return b;
        }
        var percentA = 100 - percentB;
        var toHex = function (value) {
            var hex = Math.round(value).toString(16);
            return hex.length === 1 ? "0" + hex : hex;
        };
        return "#" +
            toHex((rgbA.r * percentA + rgbB.r * percentB) / 100) +
            toHex((rgbA.g * percentA + rgbB.g * percentB) / 100) +
            toHex((rgbA.b * percentA + rgbB.b * percentB) / 100);
    }

    function colorLuma(color) {
        var rgb = hexToRgb(color);
        if (!rgb) {
            return 0;
        }
        return Math.round((rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000);
    }

    function colorContrastHex(a, b) {
        return Math.abs(colorLuma(a) - colorLuma(b));
    }

    function readableTextOnHex(bg, preferred, alternate) {
        var dark = "#111827";
        var light = "#f8fafc";
        var result = preferred;
        var resultContrast = colorContrastHex(bg, result);
        var alternateContrast = colorContrastHex(bg, alternate);
        if (alternateContrast > resultContrast) {
            result = alternate;
            resultContrast = alternateContrast;
        }
        var darkContrast = colorContrastHex(bg, dark);
        var lightContrast = colorContrastHex(bg, light);
        if (resultContrast < 72 && darkContrast > resultContrast) {
            result = dark;
            resultContrast = darkContrast;
        }
        if (resultContrast < 72 && lightContrast > resultContrast) {
            result = light;
        }
        return result;
    }

    function applyCandidatePreviewTheme(preview, theme, modern) {
        var selectedBg = modern ? blendHex(theme[0], theme[6], 28) : "#000000";
        var selectedFg = modern ? readableTextOnHex(selectedBg, theme[8], theme[3]) : "#ffffff";
        var selectedBorder = modern
            ? (colorContrastHex(selectedBg, theme[7]) >= 38 ? blendHex(theme[7], selectedBg, 28) : blendHex(selectedFg, selectedBg, 40))
            : "#000000";
        preview.css({
            "background-color": modern ? theme[0] : "#ffffff",
            "border-color": modern ? theme[1] : "#000000",
            "border-radius": modern ? "6px" : "0",
            color: modern ? theme[3] : "#000000"
        });
        preview.find(".candidate-preview-header").css("border-bottom-color", modern ? theme[2] : "#d0d0d0");
        preview.find(".candidate-preview-name, .candidate-preview-page").css("color", modern ? theme[4] : "#0000b4");
        preview.find(".candidate-preview-root").css("color", modern ? theme[5] : "#0000b4");
        preview.find(".candidate-preview-key").css("color", modern ? theme[9] : "#0000ff");
        preview.find(".candidate-preview-word").css("color", modern ? theme[3] : "#000000");
        preview.find(".candidate-preview-item.active").css({
            "background-color": selectedBg,
            "border-color": selectedBorder,
            "border-radius": modern ? "6px" : "0",
            color: selectedFg
        });
        preview.find(".candidate-preview-item.active .candidate-preview-key, .candidate-preview-item.active .candidate-preview-word").css("color", selectedFg);
    }

    function applyCandidatePreviewKeyStyle(preview, keyStyle) {
        keyStyle = keyStyle || $("#candidateKeyStyle").val() || chewingConfig.candidateKeyStyle || "keycap";
        preview
            .removeClass(candidateKeyStyleClassNames.join(" "))
            .addClass("key-style-" + keyStyle);
    }

    function fillCandidatePreviewItems(preview, sample) {
        var count = parseInt($("#candidatePerRow").val(), 10) || 4;
        count = Math.max(1, Math.min(count, 10));
        var selKeys = sample.selKeys || "1234567890";
        var body = preview.find(".candidate-preview-body");
        body.empty();

        for (var i = 0; i < count; ++i) {
            var item = $("<span>").addClass("candidate-preview-item");
            if (i === 0) {
                item.addClass("active");
            }
            item.append($("<span>").addClass("candidate-preview-key").text(selKeys.charAt(i % selKeys.length)));
            item.append($("<span>").addClass("candidate-preview-word").text(sample.candidates[i % sample.candidates.length]));
            body.append(item);
        }
    }

    function candidatePreviewFontSize() {
        var fontSize = parseInt($("#fontSize").val(), 10) || 12;
        return Math.max(6, Math.min(fontSize, 48));
    }

    function createCandidatePreview(sample, keyStyle) {
        var preview = $("<div>").addClass("candidate-preview");
        var header = $("<div>").addClass("candidate-preview-header");
        header.append($("<span>").addClass("candidate-preview-name").text(sample.name));
        header.append($("<span>").addClass("candidate-preview-root").text(sample.root));
        header.append($("<span>").addClass("candidate-preview-page").text("1/1"));
        preview.append(header);
        preview.append($("<div>").addClass("candidate-preview-body"));
        fillCandidatePreviewItems(preview, sample);
        applyCandidatePreviewKeyStyle(preview, keyStyle);
        return preview;
    }

    function applyCandidatePreviewMessageTheme(preview, theme, modern) {
        var accent = modern ? theme[7] : "#bf8643";
        var messageBg = modern
            ? (colorLuma(theme[0]) > 165 ? blendHex(theme[0], accent, 8) : blendHex(theme[0], accent, 13))
            : "#fff3dd";
        var messageText = modern
            ? (colorLuma(theme[0]) > 165 ? "#7a430d" : blendHex(theme[3], accent, 38))
            : "#7a430d";
        var badgeText = colorLuma(accent) > 150 ? "#1b1c20" : "#ffffff";
        preview.css({
            "--candidate-message-accent": accent,
            "--candidate-message-bg": messageBg,
            "--candidate-message-text": messageText,
            "--candidate-message-badge-text": badgeText
        });
    }

    function createCandidateMessagePreview(sample, messageStyle) {
        var preview = $("<div>").addClass("candidate-preview candidate-message-preview message-style-" + messageStyle);
        var header = $("<div>").addClass("candidate-preview-header");
        header.append($("<span>").addClass("candidate-preview-name").text(sample.name));
        header.append($("<span>").addClass("candidate-preview-root").text(sample.root + sample.root + sample.root));
        preview.append(header);

        var body = $("<div>").addClass("candidate-preview-body candidate-preview-message-body");
        var row = $("<div>").addClass("candidate-preview-message-row");
        if (messageStyle === "badge") {
            row.append($("<span>").addClass("candidate-preview-message-badge").text("!"));
        }
        else if (messageStyle === "dot") {
            row.append($("<span>").addClass("candidate-preview-message-dot"));
        }
        row.append($("<span>").addClass("candidate-preview-message-text").text("查無組字"));
        body.append(row);
        preview.append(body);
        return preview;
    }

    function createCandidateMessageBehaviorPreview(sample, behavior, selectedStyle) {
        var wrap = $("<div>").addClass("candidate-behavior-preview");
        var typingStyle = behavior === "progressive" ? "dot" : selectedStyle;
        var confirmedStyle = selectedStyle;

        wrap.append($("<div>").addClass("candidate-behavior-label").text(behavior === "progressive" ? "打字中：低調" : "打字中：固定樣式"));
        wrap.append(createCandidateMessagePreview(sample, typingStyle));
        wrap.append($("<div>").addClass("candidate-behavior-label").text(behavior === "progressive" ? "確認後：選用樣式" : "確認後：固定樣式"));
        wrap.append(createCandidateMessagePreview(sample, confirmedStyle));
        return wrap;
    }

    function renderCandidateThemeGallery() {
        var grid = $("#candidateThemeGrid");
        if (!grid.length) {
            return;
        }

        var sample = getCandidatePreviewSample();
        grid.empty();
        for (var i = 0; i < candidateThemeNames.length; ++i) {
            var themeName = candidateThemeNames[i];
            var card = $("<button>").attr("type", "button").addClass("candidate-theme-card").data("theme", themeName);
            var header = $("<div>").addClass("candidate-theme-card-header");
            header.append($("<span>").addClass("candidate-theme-card-name").text(themeName));
            header.append($("<span>").addClass("candidate-theme-card-state"));
            card.append(header);
            card.append(createCandidatePreview(sample));
            grid.append(card);
        }
    }

    function renderCandidateKeyStyleGallery() {
        var grid = $("#candidateKeyStyleGrid");
        if (!grid.length) {
            return;
        }

        var sample = getCandidatePreviewSample();
        grid.empty();
        $.each(candidateKeyStyleOptions, function (styleValue, styleName) {
            var card = $("<button>").attr("type", "button").addClass("candidate-style-card").data("style", styleValue);
            var header = $("<div>").addClass("candidate-style-card-header");
            header.append($("<span>").addClass("candidate-style-card-name").text(styleName));
            header.append($("<span>").addClass("candidate-style-card-state"));
            card.append(header);
            card.append(createCandidatePreview(sample, styleValue));
            grid.append(card);
        });
    }

    function renderCandidateMessageStyleGallery() {
        var grid = $("#candidateMessageStyleGrid");
        if (!grid.length) {
            return;
        }

        var sample = getCandidatePreviewSample();
        grid.empty();
        $.each(candidateMessageStyleOptions, function (styleValue, styleName) {
            var card = $("<button>").attr("type", "button").addClass("candidate-style-card candidate-message-style-card").data("style", styleValue);
            var header = $("<div>").addClass("candidate-style-card-header");
            header.append($("<span>").addClass("candidate-style-card-name").text(styleName));
            header.append($("<span>").addClass("candidate-style-card-state"));
            card.append(header);
            card.append(createCandidateMessagePreview(sample, styleValue));
            grid.append(card);
        });
    }

    function renderCandidateMessageBehaviorGallery() {
        var grid = $("#candidateMessageBehaviorGrid");
        if (!grid.length) {
            return;
        }

        var sample = getCandidatePreviewSample();
        var selectedStyle = $("#candidateMessageStyle").val() || "badge";
        grid.empty();
        $.each(candidateMessageBehaviorOptions, function (behaviorValue, behaviorName) {
            var card = $("<button>").attr("type", "button").addClass("candidate-style-card candidate-message-behavior-card").data("behavior", behaviorValue);
            var header = $("<div>").addClass("candidate-style-card-header");
            header.append($("<span>").addClass("candidate-style-card-name").text(behaviorName));
            header.append($("<span>").addClass("candidate-style-card-state"));
            card.append(header);
            card.append(createCandidateMessageBehaviorPreview(sample, behaviorValue, selectedStyle));
            grid.append(card);
        });
    }

    function updateCandidateThemeGallery() {
        var grid = $("#candidateThemeGrid");
        if (!grid.length) {
            return;
        }

        var selectedTheme = $("#candidateTheme").val() || "Night Comfort";
        var modern = $("#candidateModernStyle").prop("checked");
        var stableWidth = $("#candidateStableWidth").prop("checked");
        var wrapToMaxWidth = $("#candidateWrapToMaxWidth").prop("checked");
        var selectedStyle = $("#candidateKeyStyle").val() || "keycap";
        var sample = getCandidatePreviewSample();
        $("#candidateMinWidth").prop("disabled", !stableWidth);
        $("#candidateMaxWidth").prop("disabled", !wrapToMaxWidth);
        $("#candidateThemeCurrent").text(selectedTheme);

        grid.find(".candidate-theme-card").each(function () {
            var card = $(this);
            var themeName = card.data("theme");
            var selected = themeName === selectedTheme;
            var preview = card.find(".candidate-preview");
            card.toggleClass("selected", selected);
            preview.toggleClass("wrap", wrapToMaxWidth);
            preview.css("font-size", candidatePreviewFontSize() + "pt");
            card.find(".candidate-theme-card-state").text(selected ? "已選" : "");
            preview.find(".candidate-preview-name").text(sample.name);
            preview.find(".candidate-preview-root").text(sample.root);
            fillCandidatePreviewItems(preview, sample);
            applyCandidatePreviewKeyStyle(preview, selectedStyle);
            applyCandidatePreviewTheme(preview, candidateThemePalette[themeName] || candidateThemePalette["Night Comfort"], modern);
        });
    }

    function updateCandidateKeyStyleGallery() {
        var grid = $("#candidateKeyStyleGrid");
        if (!grid.length) {
            return;
        }

        var selectedStyle = $("#candidateKeyStyle").val() || "keycap";
        var selectedTheme = $("#candidateTheme").val() || "Night Comfort";
        var modern = $("#candidateModernStyle").prop("checked");
        var wrapToMaxWidth = $("#candidateWrapToMaxWidth").prop("checked");
        var sample = getCandidatePreviewSample();
        $("#candidateKeyStyleCurrent").text(candidateKeyStyleOptions[selectedStyle] || "");

        grid.find(".candidate-style-card").each(function () {
            var card = $(this);
            var styleValue = card.data("style");
            var selected = styleValue === selectedStyle;
            var preview = card.find(".candidate-preview");
            card.toggleClass("selected", selected);
            preview.toggleClass("wrap", wrapToMaxWidth);
            preview.css("font-size", candidatePreviewFontSize() + "pt");
            card.find(".candidate-style-card-state").text(selected ? "已選" : "");
            preview.find(".candidate-preview-name").text(sample.name);
            preview.find(".candidate-preview-root").text(sample.root);
            fillCandidatePreviewItems(preview, sample);
            applyCandidatePreviewKeyStyle(preview, styleValue);
            applyCandidatePreviewTheme(preview, candidateThemePalette[selectedTheme] || candidateThemePalette["Night Comfort"], modern);
        });
    }

    function updateCandidateMessageStyleGallery() {
        var grid = $("#candidateMessageStyleGrid");
        if (!grid.length) {
            return;
        }

        var selectedStyle = $("#candidateMessageStyle").val() || "badge";
        var selectedTheme = $("#candidateTheme").val() || "Night Comfort";
        var modern = $("#candidateModernStyle").prop("checked");
        var sample = getCandidatePreviewSample();
        $("#candidateMessageStyleCurrent").text(candidateMessageStyleOptions[selectedStyle] || "");

        grid.find(".candidate-message-style-card").each(function () {
            var card = $(this);
            var styleValue = card.data("style");
            var selected = styleValue === selectedStyle;
            var preview = card.find(".candidate-preview");
            card.toggleClass("selected", selected);
            preview.css("font-size", candidatePreviewFontSize() + "pt");
            card.find(".candidate-style-card-state").text(selected ? "已選" : "");
            preview.find(".candidate-preview-name").text(sample.name);
            preview.find(".candidate-preview-root").text(sample.root + sample.root + sample.root);
            applyCandidatePreviewTheme(preview, candidateThemePalette[selectedTheme] || candidateThemePalette["Night Comfort"], modern);
            applyCandidatePreviewMessageTheme(preview, candidateThemePalette[selectedTheme] || candidateThemePalette["Night Comfort"], modern);
        });
    }

    function updateCandidateMessageBehaviorGallery() {
        var grid = $("#candidateMessageBehaviorGrid");
        if (!grid.length) {
            return;
        }

        var selectedBehavior = $("#candidateMessageBehavior").val() || "progressive";
        var selectedStyle = $("#candidateMessageStyle").val() || "badge";
        var selectedTheme = $("#candidateTheme").val() || "Night Comfort";
        var modern = $("#candidateModernStyle").prop("checked");
        var sample = getCandidatePreviewSample();
        $("#candidateMessageBehaviorCurrent").text(candidateMessageBehaviorOptions[selectedBehavior] || "");

        grid.find(".candidate-message-behavior-card").each(function () {
            var card = $(this);
            var behaviorValue = card.data("behavior");
            var selected = behaviorValue === selectedBehavior;
            card.toggleClass("selected", selected);
            card.find(".candidate-style-card-state").text(selected ? "已選" : "");
            card.find(".candidate-behavior-preview").remove();
            card.append(createCandidateMessageBehaviorPreview(sample, behaviorValue, selectedStyle));
            card.find(".candidate-preview").each(function () {
                var preview = $(this);
                preview.css("font-size", candidatePreviewFontSize() + "pt");
                applyCandidatePreviewTheme(preview, candidateThemePalette[selectedTheme] || candidateThemePalette["Night Comfort"], modern);
                applyCandidatePreviewMessageTheme(preview, candidateThemePalette[selectedTheme] || candidateThemePalette["Night Comfort"], modern);
            });
        });
    }

    function updateCandidateAppearanceGalleries() {
        updateCandidateThemeGallery();
        updateCandidateKeyStyleGallery();
        updateCandidateMessageStyleGallery();
        updateCandidateMessageBehaviorGallery();
    }

    function saveConfig(callbackFunc) {
        // Check easy symbols format
        var ez_symbols_array = $("#ez_symbols").val().split("\n");
        for (var i = 0; i < ez_symbols_array.length; i++) {
            if (!/^[A-Z][ ].{1,10}$/.test(ez_symbols_array[i])) {
                // Select error range
                $("#ez_symbols").select();
                var selectionStart = 0;
                for (var j = 0; j < i; j++) {
                    selectionStart += ez_symbols_array[j].length + 1;
                }
                $("#ez_symbols").prop("selectionStart", selectionStart);
                $("#ez_symbols").prop("selectionEnd", selectionStart + ez_symbols_array[i].length + 1);
                swal.fire(
                    "輸入錯誤",
                    "第 " + i + " 行格式錯誤：<br><b>" + ez_symbols_array[i] + "</b><br>請使用「英文大寫 + 空格 + 字串」的格式，字串最多10個字元",
                    "error"
                );
                return false;
            }
        }

        // Check symbols format
        var symbols_array = $("#symbols").val().split("\n");
        for (var i = 0; i < symbols_array.length; i++) {
            if (symbols_array[i].length > 1 && symbols_array[i].search("=") === -1) {
                // Select error range
                $("#symbols").select();
                var selectionStart = 1;
                for (var j = 0; j < i; j++) {
                    selectionStart += symbols_array[j].length;
                }
                $("#symbols").prop("selectionStart", selectionStart);
                $("#symbols").prop("selectionEnd", selectionStart + symbols_array[i].length);
                swal.fire(
                    "輸入錯誤",
                    "特殊符號設定第 " + (i + 1) + " 行格式錯誤：<br><b>" + symbols_array[i] + "</b><br>單行不能超過一個字元，或是沒有 = 符號區隔",
                    "error"
                );
                return false;
            }
        }

        var data = {
            config: chewingConfig
        };

        // Append "\n" on symbols end prevent error
        if (symbolsChanged) {
            if ($("#symbols").val().slice(-1) !== "\n") {
                $("#symbols").val($("#symbols").val() + "\n");
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
            dataType: "json"
        });
    }

    // Update chewingConfig object with the value set by the user
    function updateConfig() {
        // Preserve settings that are not shown on the current page.
        chewingConfig = $.extend(true, {}, chewingConfig);

        // Get values from checkboxes, text, hidden and radio
        $(".container input").each(function (index, inputItem) {
            switch (inputItem.type) {
                case "checkbox":
                    chewingConfig[inputItem.name] = inputItem.checked;
                    break;
                case "text":
                case "hidden":
                case "number":
                    if ($(inputItem).data("value-type") === "string") {
                        chewingConfig[inputItem.name] = inputItem.value;
                    }
                    else {
                        chewingConfig[inputItem.name] = parseInt(inputItem.value, 10);
                    }
                    break;
                case "radio":
                    if (inputItem.checked === true) {
                        chewingConfig[inputItem.name] = parseInt(inputItem.value, 10);
                    }
                    break;
            }
        });

        // Get values from select
        $(".container select").each(function (index, selectItem) {
            if (selectItem.value) {
                if ($(selectItem).data("value-type") === "string") {
                    chewingConfig[selectItem.name] = selectItem.value;
                }
                else {
                    chewingConfig[selectItem.name] = parseInt(selectItem.value, 10);
                }
            }
        });

        if (chewingConfig.candidateTheme) {
            chewingConfig.candidateColors = {};
        }
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
        var selectOptions = {
            switchLangWithWhichShift: ["左右兩邊都使用", "僅使用左 Shift", "僅使用右 Shift"],
            upDownAction: ["移動游標選字", "在選字時翻頁"],
            leftRightAction: ["移動游標選字（循環）", "在選字時翻頁"],
            spaceKeyAction: {
                1: "叫出選字視窗",
                0: "輸出空格"
            },
            spaceKeyCandidatesAction: {
                1: "移動游標（循環）",
                0: "翻頁"
            },
            selKeyType: ["1234567890", "asdfghjkl;", "asdfzxcv89", "asdfjkl789", "aoeuhtn789", "1234qweras"],
            addPhraseForward: ["後方的詞", "前方的詞"]
        };

        $.each(selectOptions, function (id, options) {
            $.each(options, function (value, optionName) {
                $("#" + id).append('<option value="' + value + '">' + optionName + "</option>");
                if (value == chewingConfig[id]) {
                    $("#" + id + " option:last-child").prop("selected", true);
                }
            });
        });

        initializeCandidateWindowSettings();

        // Setup switchLangWithWhichShift's default disabled property
        $("#switchLangWithWhichShift").prop("disabled", !chewingConfig["switchLangWithShift"]);

        // Bind Bootstrap. Keep candidate-window controls native so they match the Dayi settings UI.
        if ($.fn.selectpicker) {
            $(".container select")
                .not(".candidate-theme-select, .candidate_window_settings select, .candidate-window-settings select")
                .selectpicker();
        }
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
        renderCandidateThemeGallery();
        renderCandidateKeyStyleGallery();
        renderCandidateMessageStyleGallery();
        renderCandidateMessageBehaviorGallery();
        updateCandidateAppearanceGalleries();
        $(".candidate-window-settings input, .candidate-window-settings select").on("change keyup", updateCandidateAppearanceGalleries);
        $("#selKeyType").on("change", updateCandidateAppearanceGalleries);
        $("#candidateThemeGrid").on("click", ".candidate-theme-card", function () {
            $("#candidateTheme").val($(this).data("theme"));
            updateCandidateAppearanceGalleries();
        });
        $("#candidateKeyStyleGrid").on("click", ".candidate-style-card", function () {
            $("#candidateKeyStyle").val($(this).data("style"));
            updateCandidateAppearanceGalleries();
        });
        $("#candidateMessageStyleGrid").on("click", ".candidate-message-style-card", function () {
            $("#candidateMessageStyle").val($(this).data("style"));
            updateCandidateAppearanceGalleries();
        });
        $("#candidateMessageBehaviorGrid").on("click", ".candidate-message-behavior-card", function () {
            $("#candidateMessageBehavior").val($(this).data("behavior"));
            updateCandidateAppearanceGalleries();
        });

        // Setup keybord page
        var keyboardNames = [
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
            ["CARPALX", "carpalx"]
        ];

        var item = '<img id="keyboard_layouts" src="images\\keyborad_layouts\\pinyin.png" alt="pinyin">';

        for (var i = 0; i < keyboardNames.length; ++i) {
            var id = "kb" + i;
            var name = keyboardNames[i][0];
            var layout = keyboardNames[i][1];
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
        var checkedKetboardLayoutRadio = $("#kb" + chewingConfig.keyboardLayout);
        checkedKetboardLayoutRadio.prop("checked", true);
        $("#keyboard_layouts").prop("src", "images/keyborad_layouts/" + checkedKetboardLayoutRadio.data("layout") + ".png");
        $("#keyboard_layouts").prop("alt", checkedKetboardLayoutRadio.data("layout"));

        // Bind change keyboard_layouts event
        $("#keyboard_tab input:radio").on("click", function () {
            var layout_file_name = $(this).data("layout");
            $("#keyboard_layouts").fadeOut(200, function () {
                $("#keyboard_layouts").prop("src", "images/keyborad_layouts/" + layout_file_name + ".png");
                $("#keyboard_layouts").prop("alt", layout_file_name);
            });

            $("#keyboard_layouts").fadeIn(200);
        });
    }

    function appendOptions(select, options, selectedValue) {
        var hasSelection = false;
        select.empty();

        $.each(options, function (value, optionName) {
            var itemValue = Array.isArray(options) ? optionName : value;
            var option = $("<option>").attr("value", itemValue).text(optionName);
            if (itemValue == selectedValue) {
                option.prop("selected", true);
                hasSelection = true;
            }
            select.append(option);
        });

        if (!hasSelection) {
            select.children().first().prop("selected", true);
        }
    }

    function setCandidateNumber(id, fallback) {
        var value = parseInt(chewingConfig[id], 10);
        $("#" + id).val(isNaN(value) ? fallback : value);
    }

    function initializeCandidateWindowSettings() {
        appendOptions($("#candidateTheme"), candidateThemeNames, chewingConfig.candidateTheme || "Night Comfort");
        $("#candidateKeyStyle").val(chewingConfig.candidateKeyStyle || "keycap");
        $("#candidateMessageStyle").val(chewingConfig.candidateMessageStyle || "badge");
        $("#candidateMessageBehavior").val(chewingConfig.candidateMessageBehavior || "progressive");

        $("#candidateModernStyle").prop("checked", !!chewingConfig.candidateModernStyle);
        $("#candidateStableWidth").prop("checked", !!chewingConfig.candidateStableWidth);
        $("#candidateEdgeAvoidance").prop("checked", !!chewingConfig.candidateEdgeAvoidance);
        $("#candidateWrapToMaxWidth").prop("checked", !!chewingConfig.candidateWrapToMaxWidth);
        setCandidateNumber("candidatePerRow", 6);
        setCandidateNumber("fontSize", 16);
        setCandidateNumber("candidateMinWidth", 286);
        setCandidateNumber("candidateMaxWidth", 300);
    }

    // Use for select phrase example
    function updateSelExample() {
        var example = ["選", "字", "視", "窗", "大", "小", "範", "例"];
        var selectedIndex = parseInt($("#selKeyType").val(), 10);
        var selectedOption = $("#selKeyType option").eq(isNaN(selectedIndex) ? 0 : selectedIndex);
        var selectItems = selectedOption.length ? selectedOption.html() : "1234567890";
        var candPerPage = parseInt($("#candPerPage").val(), 10) || example.length;
        var candPerRow = parseInt($("#candPerRow").val(), 10) || example.length;
        var html = "";

        for (var number = 0, i = 0, row = 0; number < candPerPage; number++, i++, row++) {
            if (example[i] == null) {
                i = 0;
            }

            if (row == candPerRow) {
                row = 0;
                html += "<br>";
            }

            html += "<span>" + selectItems.substr(number, 1) + ".</span>" + example[i];
        }

        $("#selExample").html(html);
        $("#selExample").css("font-size", $("#fontSize").val() + "pt");
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
            url: KEEP_ALIVE_URL + "?" + Date.now()
        });
    }, 20 * 1000);

    // Bind test input auto select
    $("#test_input").on("shown.bs.modal", function () {
        $("#test_input_text").val("").select();
    });

    bindTabsFallback();

    return false;
});
