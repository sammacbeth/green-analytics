function format_timestamp(timestamp, period) {
    var d = new Date(timestamp);
    return $.plot.formatDate(d, "%b %d");

}

$(function () {
    $("div.metric div.sparkline").each(function (index, elem) {
        var e = $(elem);
        var value_element = e.parent().find('div.till_now');
        var timestamp_element = e.parent().find('div.timestamp');
        var original_value = value_element.html();
        var original_ts_value = timestamp_element.text();

       var url = "/metric_details?name=" + e.data('metric');
        //var url = "http://192.168.5.239/dashboard_json_files/" + e.data('metric') + ".json";
        //var url = "konark.php?url=http://192.168.5.239/dashboard_json_files/" + e.data('metric') + ".json";
        $.getJSON(url, function(response) {
            // flot time series data needs to be in *milliseconds*, not seconds.
            // fixing this in Python would be easier but would limit reuse.
            for (var i=0; i < response.data.length; i++) {
                response.data[i][0] = response.data[i][0] * 1000;
            };
            var options = {
                xaxis: {show: false, mode: "time"},
                yaxis: {show: false, min: 0},
                grid: {borderWidth: 0, hoverable: true},
                colors: ["yellow"]
            };

             options.bars = {
                    show: true,
                    barWidth: 40 * 60 * 60 * 1000,
                    fillColor: "yellow",
                    lineWidth: 2,
                    align: "center",
                };

            $.plot(e, [response.data], options);

            e.bind('plothover', function(event, pos, item) {
                if (item) {
                    value_element.html(item.datapoint[1]);
                    var d = format_timestamp(item.datapoint[0], "daily");
                    timestamp_element.html(d);
                } else {
                    value_element.html(original_value);
                    timestamp_element.html(original_ts_value);
                }
            });
        });

//        e.click(function() {
//            window.location = "/metric_konark/" + e.data('metric') + '/';
//        })
    });

    var a = $(".sortable").sort(function(a,b) {
        return $(a).attr("rel") - $(b).attr("rel");
    });
    var cont = $("#container");
    $.each(a,function(i,el) {
        cont.append(el);
    });


});
