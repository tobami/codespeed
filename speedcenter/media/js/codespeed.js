function getLoadText(text, h) {
    var loadtext = '<div style="text-align:center;">'
    var pstyle = "";
    if (h > 0) {
        h = h - 32;
        if(h < 80) { h = 200; }
        else if (h > 400) { h = 400; }
        pstyle = ' style="line-height:' + h + 'px;"';
    }
    loadtext += '<p' + pstyle + '>'+ text;
    loadtext += ' <img src="/media/images/ajax-loader.gif" align="bottom"></p></div>';
    return loadtext;
}

function transToLogBars(gridlength, maxwidth, value) {
  //Size bars according to comparison value, using a logarithmic scale, base 2
  c = Math.log(value)/Math.log(2);
  var cmargin = gridlength * 2;
  var cwidth = 1;
  if (c >= 0) {
    cwidth = c * gridlength;
    //Check too fast
    if ((cwidth + cmargin) > maxwidth) { cwidth = maxwidth - 103; }
  } else {
    c = - gridlength * c;
    cwidth = c;
    cmargin = gridlength * 2 - c;
    // Check too slow
    if (cmargin < 0) { cmargin = 0; cwidth = gridlength * 2; }
  }
  var res = new Object();
  res["margin"] = cmargin + "px";
  res["width"] = cwidth + "px";
  return res;
}
