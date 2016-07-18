var Comparison = (function(window){

// Localize globals
var readCheckbox = window.readCheckbox, getLoadText = window.getLoadText;

var compdata, bench_units;

function getConfiguration() {
  return {
    exe: readCheckbox("input[name='executables']:checked"),
    ben: readCheckbox("input[name='benchmarks']:checked"),
    env: readCheckbox("input[name='environments']:checked"),
    hor: $("input[name='direction']").is(':checked'),
    bas: $("#baseline option:selected").val(),
    chart: $("#chart_type option:selected").val()
  };
}

function refreshContent() {
  var conf = getConfiguration(),
      exes = conf.exe.split(","),
      bens  = conf.ben.split(","),
      enviros = conf.env.split(","),
      msg = "";

  var h = $("#plotwrapper").height();//get height for error message
  if (exes[0] === "") {
    $("#plotwrapper").html('<p class="warning">No executables selected</p>');
    return false;
  } else if (bens[0] === "") {
    $("#plotwrapper").html('<p class="warning">No benchmarks selected</p>');
    return false;
  } else if (enviros[0] === "") {
    $("#plotwrapper").html('<p class="warning">No environments selected</p>');
    return false;
  } else if (conf.chart === "relative bars" && conf.bas === "none") {
    msg = '<p class="warning">For relative bar charts, you must select a baseline to normalize to.</p>';
    $("#plotwrapper").html(msg);
    return false;
  } else if (conf.chart === "stacked bars" &&  conf.bas !== "none") {
      msg = '<p class="warning">Normalized stacked bars actually represent the weighted arithmetic sum, useful to spot which individual benchmarks take up the most time. Choosing different weightings from the "Normalization" menu will change the totals relative to one another. For the correct way to calculate total bars, the geometric mean must be used (see <a href="http://portal.acm.org/citation.cfm?id=5666.5673 " title="How not to lie with statistics: the correct way to summarize benchmark results">paper</a>)</p>';
  }

  $("#plotwrapper").fadeOut("fast", function() {
    $(this).html(msg).show();
    var plotcounter = 1;
    for (unit in bench_units) {
      var benchmarks = [];
      for (ben in bens) {
        if ($.inArray(parseInt(bens[ben]), bench_units[unit][0]) !== -1) {
          benchmarks.push(bens[ben]);
        }
      }
      if (benchmarks.length === 0) { continue; }

      var plotid = "plot" + plotcounter;
      $("#plotwrapper").append('<div id="' + plotid + '" class="compplot"></div>');
      plotcounter++;
      renderComparisonPlot(plotid, benchmarks, exes, enviros, conf.bas, conf.chart, conf.hor);
    }
  });
}

function savedata(data) {
  if (data.error !== "None") {
    var h = $("#content").height();//get height for error message
    $("#cplot").html(getLoadText(data.error, h));
    return 1;
  }
  delete data.error;
  compdata = data;
  refreshContent();
}

function abortRender(plotid, message) {
    $("#" + plotid).css("border", "dashed 1px grey");
    $("#" + plotid).css("padding", "1em");
    $("#" + plotid).css("width", "400px");
    $("#" + plotid).html(getLoadText(message, 0));
    return -1;
}

function renderComparisonPlot(plotid, benchmarks, exes, enviros, baseline, chart, horizontal) {
    var axislabel = "";
    var title = "";
    var baseline_is_empty = true;
    if (baseline === "none") {
        baseline_is_empty = false;
        if (chart === "stacked bars") { title = "Cumulative "; }
        title += unit;
        axislabel = bench_units[unit][2] + bench_units[unit][1];
    } else {
        if (chart === "stacked bars") {
            title = "Cumulative " + unit + " normalized to " + $("label[for='exe_" + baseline + "']").text();
        } else if (chart === "relative bars") {
            title =  unit + " ratio to " + $("label[for='exe_" + baseline + "']").text();
        } else {
            title = unit + " normalized to " + $("label[for='exe_" + baseline + "']").text();
        }
        axislabel = "Ratio " + bench_units[unit][1];
    }

    var plotdata = [];
    var ticks = [];
    var series = [];
    var barcounter = 0;
    if (chart === "stacked bars" && horizontal) { exes.reverse(); }
    if (chart === "normal bars" || chart === "relative bars") {
        if (horizontal) { benchmarks.reverse(); }
        // Add tick labels
        for (var ben in benchmarks) {
            var benchlabel = $("label[for='benchmark_" + benchmarks[ben] + "']").text();
            ticks.push(benchlabel);
        }
        // Add data
        for (var i in exes) {
            for (var j in enviros) {
                var exe = $("label[for='exe_" + exes[i] + "']").text();
                var env = $("label[for='env_" + enviros[j] + "']").text();
                // for relative bars leave out (don't show) the baseline exe
                if (chart === "relative bars") {
                    if (exe === $("label[for='exe_" + baseline + "']").text()) {
                        continue;
                    }
                }
                series.push({'label': exe + " @ " + env});
                var customdata = [];
                var benchcounter = 0;
                if (baseline !== "none") {
                    if (chart === "relative bars") {
                        axislabel = "<- worse - better ->";
                    }
                }
                for (var b in benchmarks) {
                    benchcounter++;
                    barcounter++;
                    var val = compdata[exes[i]][enviros[j]][benchmarks[b]];
                    if (val !== null) {
                        if (baseline !== "none") {
                            var baseval = compdata[baseline][enviros[j]][benchmarks[b]];
                            if (baseval === null || baseval === 0) {
                                val = 0.0001;
                            } else {
                                baseline_is_empty = false;
                                val = val / baseval;
                                if (chart === "relative bars" && val > 1) {
                                    val = -val;
                                }
                            }
                        }
                    }
                    //Add data
                    if (!horizontal) {
                        customdata.push(val);
                    } else {
                        customdata.push([val, benchcounter]);
                    }
                }
                plotdata.push(customdata);
            }
        }
    } else if (chart === "stacked bars") {
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
            var customdata = [];
            var benchcounter = 0;
            barcounter = 1;
            for (var i in exes) {
                for (var j in enviros) {
                    benchcounter++;
                    var exe = $("label[for='exe_" + exes[i] + "']").text();
                    var env = $("label[for='env_" + enviros[j] + "']").text();
                    var val = compdata[exes[i]][enviros[j]][benchmarks[b]];
                    if (val !== null) {
                        if (baseline !== "none") {
                            var baseval = compdata[baseline][enviros[j]][benchmarks[b]];
                            if (baseval === null || baseval === 0) {
                                var benchlabel = $("label[for='benchmark_" + benchmarks[b] + "']").text();
                                var baselinelabel = $("label[for='exe_" + baseline + "']").text();
                                var msg = "<strong>"+ title + "</strong>" + "<br><br>";
                                msg += "Could not render plot because the chosen baseline has empty results for benchmark " + benchlabel;
                                return abortRender(plotid, msg);
                            } else {
                                baseline_is_empty = false;
                                val = val / baseval;
                            }
                        }
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

    if (baseline_is_empty) {
        var baselinelabel = $("label[for='exe_" + baseline + "']").text();
        var msg = "<strong>"+ title + "</strong>" + "<br><br>";
        msg += "Could not render plot because the chosen baseline is empty";
        return abortRender(plotid, msg);
    }

    // Set plot options and size depending on:
    // - Bar orientation (horizontal/vertical)
    // - Screen width and number of bars being displayed
    var plotwidth = $("#plotwrapper").width();
    var plotheight = $("#" + plotid).height();
    var barWidth = 20;
    var w = 0;
    var h = 0;
    var plotoptions = [];
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
        };

        if (chart === "relative bars") {
            plotoptions.axes.xaxis.min = null;
            plotoptions.axes.xaxis.tickOptions = {formatString:'%.1fx'};
        } else if (chart ==="stacked bars") {
//             plotoptions.axes.xaxis.min = null;
            // Not good when there is a 0 bar. It even shows negative bars when all bars are 0
        }

        // Determine optimal height
        if (chart ==="stacked bars") {
            h = 90 + ticks.length * (plotoptions.seriesDefaults.rendererOptions.barPadding*2 + barWidth);
        } else {
            h = barcounter * (plotoptions.seriesDefaults.rendererOptions.barPadding*2 + barWidth) + benchcounter * plotoptions.seriesDefaults.rendererOptions.barMargin * 2;
        }
        // Adjust plot height
        if (h > 700) {
            h = h/2;
            if (h < 700) { h = 700; }
            else if (h > 2000) { h = 2000; }
            plotoptions.seriesDefaults.rendererOptions.barPadding = 0;
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
        };

        w = barcounter * (plotoptions.seriesDefaults.rendererOptions.barPadding*2 + barWidth) + benchcounter * plotoptions.seriesDefaults.rendererOptions.barMargin * 2 + 60;
        h = plotheight;
        // Check if calculated width is greater than actually available width
        if (w > plotwidth + 75) {
            plotoptions.seriesDefaults.rendererOptions.barPadding = 0;
            plotoptions.seriesDefaults.rendererOptions.barMargin = 10;
            plotoptions.seriesDefaults.shadow = false;
            plotoptions.axes.xaxis.tickOptions.angle = -30;
        }
        if (w > plotwidth) {
            w = plotwidth;
        } else if (w < 320) {
            w = 320;
            plotoptions.seriesDefaults.rendererOptions.barPadding = 15;
            plotoptions.seriesDefaults.rendererOptions.barMargin = 25;
        }
        if (chart === "normal bars" && series.length === 1 && benchmarks.length > 1) {
            plotoptions.axes.xaxis.tickOptions.angle = -30;
        } else if (chart === "stacked bars") {
            plotoptions.axes.xaxis.tickOptions.angle = -60;
            plotoptions.seriesDefaults.rendererOptions.barMargin += 5;
            $("#" + plotid).css("margin-left", "25px");
            h += 60;
        } else if (chart === "relative bars") {
            plotoptions.axes.yaxis.min = null;
//             plotoptions.axes.yaxis.autoscale = false; //It triggers a bug sometimes
            plotoptions.axes.yaxis.tickOptions = {formatString:'%.1fx'};
            plotoptions.axes.xaxis.tickOptions.angle = -30;
        }
    }

    plotoptions.legend = {show: true, location: 'ne'};
    plotoptions.series = series;
    plotoptions.grid = {borderColor: '#9DADC6', shadow: false, drawBorder: true};
    plotoptions.seriesDefaults.shadow = false;
    plotoptions.axesDefaults.tickOptions = {fontFamily:'Arial'};

    // determine conditions for rendering the legend outside the plot area
    var offplot = false;
    if (!horizontal && series.length > 4) { offplot = true; }
    else if (horizontal && series.length > 2*ticks.length) { offplot = true; }

    if (offplot) {
        // Move legend outside plot area to unclutter
        var labels = [];
        for (l in series) {
            labels.push(series[l].label.length);
        }

        var offset = 55 + Math.max.apply( Math, labels ) * 5.4;
        plotoptions.legend.xoffset = -offset;
        $("#" + plotid).css("margin-right", offset + 10);
        if (w + offset > plotwidth) { w = plotwidth - offset -20; }
    } else if (!horizontal && ticks.length <= 2) {
        plotoptions.legend = {show: true, location: 'se'};
    }

    // Set bar type
    if (chart === "stacked bars") {
        plotoptions.stackSeries = true;
    } else if (chart === "relative bars") {
        plotoptions.seriesDefaults.fill = true;
        plotoptions.seriesDefaults.fillToZero = true;
        plotoptions.seriesDefaults.useNegativeColors = false;
    }

    // check that legend does not overflow
    if (series.length > 14) {
        if (!horizontal || (series.length > ticks.length)) {
            var mb = $("#" + plotid).css("margin-bottom").slice(0, -2);
            mb = parseInt(mb, 10) + 4 + (series.length - 14) * 22;
            $("#" + plotid).css("margin-bottom", mb);
        }
    }
    /* End set plot style */

    // Render plot
    $("#" + plotid).css('width', w);
    $("#" + plotid).css('height', h);
    $.jqplot(plotid, plotdata, plotoptions);
}

function init(defaults) {
    bench_units = defaults.bench_units;

    // Set default values
    $("#chart_type").val(defaults.chart_type);
    $("#baseline").val(defaults.baseline);
    $("#direction").prop('checked', defaults.direction === "True");

    var sel = $("input[name='executables']");
    $.each(defaults.executables, function(i, exe) {
        sel.filter("[value='" + exe + "']").prop('checked', true);
    });

    sel = $("input[name='benchmarks']");
    $.each(defaults.benchmarks, function(i, bench) {
        sel.filter("[value='" + bench + "']").prop('checked', true);
    });

    sel = $("input[name='environments']");
    $.each(defaults.environments, function(i, env) {
        sel.filter("[value='" + env + "']").prop('checked', true);
    });

    $("#chart_type, #baseline, #direction, input[name='executables']," +
      "input[name='benchmarks'], input[name='environments']").change(refreshContent);

    $('.checkall, .uncheckall').click(refreshContent);

    $.ajaxSetup ({
      cache: false
    });

    // Get comparison data
    var h = $("#content").height();//get height for loading text
    $("#cplot").html(getLoadText("Loading...", h));
    $.getJSON("json/", savedata);

    $("#permalink").click(function() {
        window.location = "?" + $.param(getConfiguration());
    });
}

return {
    init: init
};

})(window);
