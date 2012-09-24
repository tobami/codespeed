var Timeline = (function(window){

// Localize globals
var CHANGES_URL = window.CHANGES_URL, readCheckbox = window.readCheckbox,
    getLoadText = window.getLoadText;

var seriesindex = [],
    baselineColor = "#d8b83f",
    seriesColors = ["#4bb2c5", "#EAA228", "#579575", "#953579", "#839557", "#ff5800", "#958c12", "#4b5de4", "#0085cc"],
    defaults;

function setExeColors() {
  // Set color data attribute for all executables
  $("#executable > div.boxbody > ul > ul > li > input").each(function(index) {
    var color_id = index;
    while (color_id > seriesColors.length) { color_id -= seriesColors.length; }
    $(this).data('color', seriesColors[color_id]);
  });
}

function getColor(exe_id) {
  return $("#executable > div.boxbody")
                          .find("input[value='"+exe_id+"']")
                          .data('color');
}

function shouldPlotEquidistant() {
  return $("#equidistant").is(':checked');
}

function getConfiguration() {
  var config = {
    exe: readCheckbox("input[name='executable']:checked"),
    base: $("#baseline option:selected").val(),
    ben: $("input[name='benchmark']:checked").val(),
    env: $("input[name='environments']:checked").val(),
    revs: $("#revisions option:selected").val(),
    equid: $("#equidistant").is(':checked') ? "on" : "off"
  };

  var branch = readCheckbox("input[name='branch']:checked");
  if (branch) {
    config.bran = branch;
  }

  return config;
}

function permalinkToChanges(commitid, executableid, environment) {
  window.location=CHANGES_URL + "?rev=" + commitid + "&" + "exe=" + executableid + "&env=" + environment;
}

function OnMarkerClickHandler(ev, gridpos, datapos, neighbor, plot) {
  if($("input[name='benchmark']:checked").val() === "grid") { return false; }
  if (neighbor) {
    var commitid = neighbor.data[3];
    // Get executable ID from the seriesindex array
    var executableid = seriesindex[neighbor.seriesIndex];
    var environment = $("input[name='environments']:checked").val();
    permalinkToChanges(commitid, executableid, environment);
  }
}

function renderPlot(data) {
  var plotdata = [],
      series = [],
      lastvalues = [];//hopefully the smallest values for determining significant digits.
  seriesindex = [];
  for (var branch in data.branches) {
    // NOTE: Currently, only the "default" branch is shown in the timeline
    for (var exe_id in data.branches[branch]) {
      // FIXME if (branch !== "default") { label += " - " + branch; }
      var label = $("label[for*='executable" + exe_id + "']").html();
      series.push({"label":  label, "color": getColor(exe_id)});
      seriesindex.push(exe_id);
      plotdata.push(data.branches[branch][exe_id]);
      lastvalues.push(data.branches[branch][exe_id][0][1]);
    }
    //determine significant digits
    var digits = 2;
    var value = Math.min.apply( Math, lastvalues );
    if (value !== 0) {
      while( value < 1 ) {
        value *= 10;
        digits++;
      }
    }
    $("#plotgrid").html('<div id="plot"></div><div id="plotdescription"></div>');

    if (data.benchmark_description) {
      $("#plotdescription").html('<p class="note"><i>' + data.benchmark + '</i>: ' + data.benchmark_description + '</p>');
    }
  }
  if (data.baseline !== "None") {
    series.push({
      "label": $("#baseline option:selected").html(), "color": baselineColor,
      showMarker: false,
      lineWidth: 1.5
    });
    plotdata.push(data.baseline);
  }
  var plotoptions = {
    title: {text: data.benchmark, fontSize: '1.1em'},
    series: series,
    axes:{
      yaxis:{
        label: data.units + data.lessisbetter,
        labelRenderer: $.jqplot.CanvasAxisLabelRenderer,
        min: 0, autoscale:true,
        tickOptions:{formatString:'%.' + digits + 'f'}
      },
      xaxis:{
        renderer: (shouldPlotEquidistant()) ? $.jqplot.CategoryAxisRenderer : $.jqplot.DateAxisRenderer,
        label: 'Commit date',
        labelRenderer: $.jqplot.CanvasAxisLabelRenderer,
        tickOptions:{formatString:'%b %d'},
        pad: 1.01,
        autoscale:true,
        rendererOptions:{sortMergedLabels:true} /* only relevant when
                                $.jqplot.CategoryAxisRenderer is used */ 
      }
    },
    legend: {show: true, location: 'nw'},
    highlighter: {
      tooltipLocation: 'nw',
      yvalues: 4,
      formatString:'<table class="jqplot-highlighter">    <tr><td>date:</td><td>%s</td></tr> <tr><td>result:</td><td>%s</td></tr> <tr><td>std dev:</td><td>%s</td></tr> <tr><td>commit:</td><td>%s</td></tr></table>'
    },
    cursor:{zoom:true, showTooltip:false, clickReset:true}
  };
  if (series.length > 4) {
      // Move legend outside plot area to unclutter
      var labels = [];
      for (var l in series) {
          labels.push(series[l].label.length);
      }

      var offset = 55 + Math.max.apply( Math, labels ) * 5.4;
      plotoptions.legend.location = 'ne';
      plotoptions.legend.xoffset = -offset;
      $("#plot").css("margin-right", offset + 10);
      var w = $("#plot").width();
      $("#plot").css('width', w - offset);
  }
  //Render plot
  $.jqplot('plot',  plotdata, plotoptions);
}

function renderMiniplot(plotid, data) {
  var plotdata = [],
      series = [];

  for (var branch in data.branches) {
    for (var id in data.branches[branch]) {
      series.push({
        "label": $("label[for*='executable" + id + "']").html(),
        "color": getColor(id)
      });
      plotdata.push(data.branches[branch][id]);
    }
  }
  if (data.baseline !== "None") {
    series.push({
      "color": baselineColor,
      showMarker: false,
      lineWidth: 1.5
    });
    plotdata.push(data.baseline);
  }

  var plotoptions = {
    title: {text: data.benchmark, fontSize: '1.1em'},
    seriesDefaults: {lineWidth: 2, markerOptions:{style:'circle', size: 6}},
    series: series,
    axes: {
      yaxis: {
        min: 0, autoscale:true, showTicks: false
      },
      xaxis: {
        renderer:$.jqplot.DateAxisRenderer,
        pad: 1.01,
        autoscale:true,
        showTicks: false
      }
    },
    highlighter: {show:false},
    cursor:{showTooltip: false, style: 'pointer'}
  };
  $.jqplot(plotid, plotdata, plotoptions);
}

function render(data) {
  $("#revisions").attr("disabled", false);
  $("#equidistant").attr("disabled", false);
  $("#plotgrid").html("");
  if(data.error !== "None") {
    var h = $("#content").height();//get height for error message
    $("#plotgrid").html(getLoadText(data.error, h, false));
    return 1;
  } else if ($("input[name='benchmark']:checked").val() === "show_none") {
    var h = $("#content").height();//get height for error message
    $("#plotgrid").html(getLoadText("Please select a benchmark on the left", h, false));
  } else if (data.timelines.length === 0) {
    var h = $("#content").height();//get height for error message
    $("#plotgrid").html(getLoadText("No data available", h, false));
  } else if ($("input[name='benchmark']:checked").val() === "grid"){
    //Render Grid of plots
    $("#revisions").attr("disabled",true);
    $("#equidistant").attr("disabled", true);
    for (var bench in data.timelines) {
      var plotid = "plot_" + data.timelines[bench].benchmark_id;
      $("#plotgrid").append('<div id="' + plotid + '" class="miniplot"></div>');
      $("#" + plotid).click(function() {
        var benchid = $(this).attr("id").slice(5);
        $("#benchmark_" + benchid).attr('checked', true);
        updateUrl();
      });
      renderMiniplot(plotid, data.timelines[bench]);
    }
  } else {
    // render single plot when one benchmark is selected
    renderPlot(data.timelines[0]);
    return 1;
  }
}

function refreshContent() {
  var h = $("#content").height();//get height for loading text
  $("#plotgrid").fadeOut("fast", function() {
    $("#plotgrid").html(getLoadText("Loading...", h, true)).show();
    $.getJSON("json/", getConfiguration(), render);
  });
}

function updateUrl() {
  var cfg = getConfiguration();
  for (var param in cfg) {
    $.address.parameter(param, cfg[param]);
  }
  $.address.update();
}

function valueOrDefault(obj, defaultObj) {
  return (obj) ? obj : defaultObj;
}

function initializeSite(event) {
  setValuesOfInputFields(event);
  $("#revisions"                ).change(updateUrl);
  $("#baseline"                 ).change(updateUrl);
  $("input[name='executable']"  ).change(updateUrl);
  $("input[name='branch']"      ).change(updateUrl);
  $("input[name='benchmark']"   ).change(updateUrl);
  $("input[name='environments']").change(updateUrl);
  $("#equidistant"              ).change(updateUrl);
}

function refreshSite(event) {
  setValuesOfInputFields(event);
  refreshContent();
}

function setValuesOfInputFields(event) {
  // Either set the default value, or the one parsed from the url

  // Reset all checkboxes
  $("input:checkbox").removeAttr('checked');

  $("#revisions").val(valueOrDefault(event.parameters.revs, defaults.revisions));
  $("#baseline").val(valueOrDefault(event.parameters.base, defaults.baseline));

  // Set default selected executables
  var executables = event.parameters.exe ? event.parameters.exe.split(',') : defaults.executables;
  var sel = $("input[name='executable']");

  $.each(executables, function(i, exe) {
    sel.filter("[value='" + exe + "']").attr('checked', true);
  });

  // Set default selected branches
  var branches = event.parameters.bran ? event.parameters.bran.split(',') : defaults.branches;
  sel = $("input[name='branch']");

  $.each(branches, function(i, b) {
    sel.filter("[value='" + b + "']").attr('checked', true);
  });

  // Set default selected benchmark
  var benchmark = valueOrDefault(event.parameters.ben, defaults.benchmark);
  $("input:radio[name='benchmark']")
      .filter("[value='" + benchmark + "']")
      .attr('checked', true);

  // Set default selected environment
  var environment = valueOrDefault(event.parameters.env, defaults.environment);
  $("input:radio[name='environments']")
      .filter("[value='" + environment + "']")
      .attr('checked', true);

  // Add color legend to executable list
  $("#executable div.boxbody > ul > ul > li > input").each(function() {
    $(this).parent()
      .find("div.seriescolor")
      .css("background-color", getColor($(this).attr("id").slice(10)));
  });

  $("#baselinecolor").css("background-color", baselineColor);
  $("#equidistant").attr('checked', valueOrDefault(event.parameters.equid, defaults.equidistant) === "on");
}

function init(def) {
    defaults = def;

    $.ajaxSetup ({
      cache: false
    });

    // Even listener for clicks on plot markers
    $.jqplot.eventListenerHooks.push(['jqplotClick', OnMarkerClickHandler]);

    // Init and change handlers are set to the refreshContent handler
    $.address.init(initializeSite).change(refreshSite);

    $('.checkall, .uncheckall').click(refreshContent);

    setExeColors();

    $("#permalink").click(function() {
        window.location = "?" + $.param(getConfiguration());
    });
}

return {
    init: init
};

})(window);
