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
