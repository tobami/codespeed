$(function() {
    $("#subnavigation ul li").hover(function() {
        $(this).addClass('highlight');
      }, function() {
        $(this).removeClass('highlight');
      });
});