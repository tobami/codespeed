
function permalink() {
  window.location="?" + $.param(getConfiguration());
}

function readCheckbox(el) {
  config = "";
  $(el).each(function() {
    config += $(this).val() + ",";
  });
  config = config.slice(0, -1);
  return config;
}

function getLoadText(text, h, showloader) {
  var loadtext = '<div style="text-align:center;">'
  var pstyle = "";
  if (h > 0) {
      h = h - 32;
      if(h < 80) { h = 180; }
      else if (h > 400) { h = 400; }
      pstyle = ' style="line-height:' + h + 'px;"';
  }
  loadtext += '<p' + pstyle + '>'+ text;
  if (showloader==true) {
    loadtext += ' <img src="/media/images/ajax-loader.gif" align="bottom">';
  }
  loadtext += '</p></div>';
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

//colors number based on a threshold
function getColorcode(change, theigh, tlow) {
  var colorcode = "status-yellow";
  if(change < tlow) { colorcode = "status-red"; }
  else if(change > theigh) { colorcode = "status-green"; }
  return colorcode;
}

function renderComparisonPlot(plotid, benchmarks, exes, enviros, baseline, chart, horizontal) {        
    var axislabel = "";
    var title = "";
    if (baseline == "none") {
        if (chart == "stacked bars") { title = "Cumulative "; }
        title += unit;
        axislabel = bench_units[unit][2] + bench_units[unit][1];
    } else {
        if (chart == "stacked bars") {
            title = "Cumulative " + unit + " normalized to " + $("label[for='exe_" + baseline + "']").text();
        } else if (chart == "relative bars") {
            title = "Compared to " + $("label[for='exe_" + baseline + "']").text() + " (" + unit + ")";
        } else {
            title = unit + " normalized to " + $("label[for='exe_" + baseline + "']").text();
        }
        axislabel = "Relative " + bench_units[unit][2] + bench_units[unit][1];
    }
    
    var plotdata = new Array();
    var ticks = new Array();
    var series = new Array();
    var barcounter = 0;
    
    if (chart == "normal bars" || chart == "relative bars") {
        if (horizontal) { benchmarks.reverse(); }
        // Add tick labels
        for (var b in benchmarks) {
            var benchlabel = $("label[for='benchmark_" + benchmarks[b] + "']").text();
            ticks.push(benchlabel);
        }
        // Add data
        for (var i in exes) {
          for (var j in enviros) {
            var exe = $("label[for='exe_" + exes[i] + "']").text();
            var env = $("label[for='env_" + enviros[j] + "']").text();
            if (chart == "relative bars") {
                if (exe == $("label[for='exe_" + baseline + "']").text()) {
                    continue;
                }
            }
            series.push({'label': exe + " @ " + env});
            var customdata = new Array();
            var benchcounter = 0;
            
            for (var b in benchmarks) {
              benchcounter++;
              barcounter++;
              var val = compdata[exes[i]][enviros[j]][benchmarks[b]];
              if (baseline != "none") {
                axislabel = "Relative " + bench_units[unit][2] + bench_units[unit][1];
                var baseval = compdata[baseline][enviros[j]][benchmarks[b]]
                if ( baseval == 0 ) { val = 0; }
                else { val = val / baseval; }
                if (chart == "relative bars") {
                    axislabel = "<- worse - better ->";
                    if (val > 1) {
                        val = -val;
                    } else if (val != 0) {
                        val = 1/val;
                    }
                }
              }
              
              if (!horizontal) {
                customdata.push(val);
              } else {
                customdata.push([val, benchcounter]);
              }
            }
            plotdata.push(customdata);
          }
        }
        
    } else if (chart == "stacked bars") {
        if (horizontal) { exes.reverse(); }
        // Add tick labels
        for (var i in exes) {
          for (var j in enviros) {
            var exe = $("label[for='exe_" + exes[i] + "']").text();
            var env = $("label[for='env_" + enviros[j] + "']").text();
            ticks.push(exe + " @ " + env);
          }
        }
        // Add data
        for (var b in benchmarks) {
            var benchlabel = $("label[for='benchmark_" + benchmarks[b] + "']").text();
            series.push({'label': benchlabel});
            var customdata = new Array();
            var benchcounter = 0;
            barcounter = 1;
            for (var i in exes) {
                for (var j in enviros) {
                    benchcounter++;
                    var exe = $("label[for='exe_" + exes[i] + "']").text();
                    var env = $("label[for='env_" + enviros[j] + "']").text();
                    var val = compdata[exes[i]][enviros[j]][benchmarks[b]];
                    if (baseline != "none") {
                        var base = compdata[baseline][enviros[j]][benchmarks[b]]
                        if ( base == 0 ) { val = 0; }
                        else { val = val / base; }
                    }
                    if (!horizontal) {
                        customdata.push(val);
                    } else {
                        customdata.push([val, benchcounter]);
                    }
                }
            }
            plotdata.push(customdata);
        }  
    } else {
        // no valid chart type
        return false;
    }
    
    // Set plot options and size depending on:
    // - Bar orientation (horizontal/vertical)
    // - Screen width and number of bars being displayed
    var plotwidth = $("#plotwrapper").width();
    var plotheight = $("#" + plotid).height();
    var barWidth = 20;
    var w = 0;
    var h = 0;
    var plotoptions = new Object();
    if (horizontal) {
        plotoptions = {
            title: title,
            seriesDefaults: {
                renderer: $.jqplot.BarRenderer,
                rendererOptions: {barDirection: "horizontal", barPadding: 8, barMargin: 15}
            },
            axesDefaults: {
                tickRenderer: $.jqplot.CanvasAxisTickRenderer,
                tickOptions: {angle: 0}
            },
            axes: {
                xaxis: {
                    min: 0,
                    autoscale: true,
                    label: axislabel,
                    labelRenderer: $.jqplot.CanvasAxisLabelRenderer
                },
                yaxis: {
                    renderer: $.jqplot.CategoryAxisRenderer,
                    ticks: ticks
                }
            }
        }
        
        if (chart == "relative bars") {
            plotoptions.axes.xaxis.min = null;
            plotoptions.axes.xaxis.tickOptions = {formatString:'%.1fx'};
        } else if (chart =="stacked bars") {
//             plotoptions.axes.xaxis.min = null;
            // Not good when there is a 0 bar. It even shows negative bars when all bars are 0
        }
        
        //determine optimal height
        if (chart =="stacked bars") {
            h = 90 + ticks.length * (plotoptions.seriesDefaults.rendererOptions.barPadding*2 + barWidth);
        } else {
            h = barcounter * (plotoptions.seriesDefaults.rendererOptions.barPadding*2 + barWidth) + benchcounter * plotoptions.seriesDefaults.rendererOptions.barMargin * 2;
        }
        
        if (h > 820) {
            h = h/2;
            plotoptions.seriesDefaults.rendererOptions.barPadding = 4;
            plotoptions.seriesDefaults.rendererOptions.barMargin = 8;
            plotoptions.seriesDefaults.shadow = false;
        } else if (h < 300) {
            h = 300;
            plotoptions.seriesDefaults.rendererOptions.barPadding = 14;
            plotoptions.seriesDefaults.rendererOptions.barMargin = 25;
        }
        w = plotwidth;
    } else {
        plotoptions = {
            title: title,
            seriesDefaults: {
                renderer: $.jqplot.BarRenderer,
                rendererOptions: {barDirection: "vertical", barPadding: 6, barMargin: 15}
            },
            axesDefaults: {
                tickRenderer: $.jqplot.CanvasAxisTickRenderer
            },
            axes: {
                xaxis: {
                    renderer: $.jqplot.CategoryAxisRenderer,
                    ticks: ticks,
                    tickOptions: {angle: 0}
                },
                yaxis: {
                    min: 0,
                    autoscale: true,//no effect for some plots due to min = 0
                    label: axislabel,
                    labelRenderer: $.jqplot.CanvasAxisLabelRenderer
                }
            }
        }
        
        w = barcounter * (plotoptions.seriesDefaults.rendererOptions.barPadding*2 + barWidth) + benchcounter * plotoptions.seriesDefaults.rendererOptions.barMargin * 2 + 60;
        h = plotheight;
        // Check if calculated width is greater than actually available width
        if (w > plotwidth + 180) {
            plotoptions.seriesDefaults.rendererOptions.barPadding = 4;
            plotoptions.seriesDefaults.rendererOptions.barMargin = 8;
            plotoptions.seriesDefaults.shadow = false;
        }
        if (w > plotwidth + 75) {
            plotoptions.axes.xaxis.tickOptions.angle = -30;
        }
        if (w > plotwidth) {
            w = plotwidth;
        } else if (w < 320) {
            w = 320;
            plotoptions.seriesDefaults.rendererOptions.barPadding = 15;
            plotoptions.seriesDefaults.rendererOptions.barMargin = 25;
        }
        if (chart == "normal bars" && series.length == 1 && benchmarks.length > 1) {
            plotoptions.axes.xaxis.tickOptions.angle = -30;
        } else if (chart == "stacked bars") {
            plotoptions.axes.xaxis.tickOptions.angle = -60;
            plotoptions.seriesDefaults.rendererOptions.barMargin += 5;
            $("#" + plotid).css("margin-left", "25px");
            h += 60;
        } else if (chart == "relative bars") {
            plotoptions.axes.yaxis.min = null;
//             plotoptions.axes.yaxis.autoscale = false; //It triggers a bug sometimes
            plotoptions.axes.yaxis.tickOptions = {formatString:'%.1fx'};
            plotoptions.axes.xaxis.tickOptions.angle = -30;
        }
    }
    
    plotoptions.legend = {show: true, location: 'ne'};
    plotoptions.series = series;
    
    // determine conditions for rendering the legend outside the plot area
    var offplot = false;
    if (!horizontal && (series.length > 4 || ticks.length == 1)) { offplot = true; }
    else if (horizontal && series.length > 2*ticks.length) { offplot = true; }
    
    if (offplot) {
        // Move legend outside plot area to unclutter
        var labels = new Array();
        for (l in series) {
            labels.push(series[l]['label'].length)
        }
        
        var offset = 55 + Math.max.apply( Math, labels ) * 5.4;
        plotoptions.legend.xoffset = -offset;
        $("#" + plotid).css("margin-right", offset + 10);
        if (w + offset > plotwidth) { w = plotwidth - offset -20; }
    }
    
    // Set bar type
    if (chart == "stacked bars") {
        plotoptions.stackSeries = true;
    } else if (chart == "relative bars") {
        plotoptions.seriesDefaults.fill = true;
        plotoptions.seriesDefaults.fillToZero = true;
        plotoptions.seriesDefaults.useNegativeColors = false;
    }
    
    // check that legend does not overflow
    if (series.length > 14) {
        if (!horizontal || (series.length > ticks.length)) {
            var mb = $("#" + plotid).css("margin-bottom").slice(0, -2);
            mb = parseInt(mb) + 4 + (series.length - 14) * 22;
            $("#" + plotid).css("margin-bottom", mb);
        }
    }
    /* End set plot style */
        
    // Render plot
    $("#" + plotid).css('width', w);
    $("#" + plotid).css('height', h);
    plot = $.jqplot(plotid, plotdata, plotoptions);
}
