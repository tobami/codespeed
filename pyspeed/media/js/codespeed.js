function getLoadText(text, h) {
    //Create loading text
    h = h - 32;
    if(h < 80) { h = 200; }
    var loadtext = '<div style="text-align:center;"><p style="line-height:' + h + 'px;">' + text + '</p></div>';
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
