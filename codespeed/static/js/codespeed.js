
function permalink() {
    window.location="?" + $.param(getConfiguration());
}

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

function getLoadText(text, h, showloader) {
    var loadtext = '<div style="text-align:center;">';
    var pstyle = "";
    if (h > 0) {
        h = h - 32;
        if(h < 80) { h = 180; }
        else if (h > 400) { h = 400; }
        pstyle = ' style="line-height:' + h + 'px;"';
    }
    loadtext += '<p' + pstyle + '>'+ text;
    if (showloader) {
        loadtext += ' <img src="' + window.STATIC_URL +'images/ajax-loader.gif" align="bottom">';
    }
    loadtext += '</p></div>';
    return loadtext;
}
