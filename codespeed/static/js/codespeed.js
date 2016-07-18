function readCheckbox(el) {
    /* Builds a string that holds all checked values in an input form */
    var config = "";
    $(el).each(function() {
        config += $(this).val() + ",";
    });
    // Remove last comma
    config = config.slice(0, -1);
    return config;
}

function getLoadText(text, h) {
    var loadtext = '<div style="text-align:center;">';
    var pstyle = "";
    if (h > 0) {
        h = h - 32;
        if(h < 80) { h = 180; }
        else if (h > 400) { h = 400; }
        pstyle = ' style="line-height:' + h + 'px;"';
    }
    loadtext += '<p' + pstyle + '>'+ text;
    loadtext += '</p></div>';
    return loadtext;
}

$(function() {
    // Check all and none links
    $('.checkall').each(function() {
        var inputs = $(this).parent().children("li").children("input");
        $(this).click(function() {
            inputs.attr("checked", true);
            return false;
        });
    });

    $('.uncheckall').each(function() {
        var inputs = $(this).parent().children("li").children("input");
        $(this).click(function() {
            inputs.attr("checked", false);
            return false;
        });
    });

    $('.togglefold').each(function() {
        var lis = $(this).parent().children("li");
        $(this).click(function() {
            lis.slideToggle();
            return false;
        });
    });
});
