$.ajax({
    type: "POST",
    dataType: 'json',
    url: "../get_reporting_log/",
    data: {},
    success: function (data) {
        $('#reporting_log').empty();
        for (var i = 0; i < data.data.length; i++) {
            $('#reporting_log').append('<li>\n' +
                '    <div class="col1">\n' +
                '        <div class="cont" style="margin-right: 0">\n' +
                '            <div class="cont-col1">\n' +
                '                <div class="label label-sm label-success">\n' +
                '                    <i class="fa fa-bell-o"></i>\n' +
                '                </div>\n' +
                '            </div>\n' +
                '            <div class="cont-col2">\n' +
                '                <div class="desc"> ' + data.data[i].log + '\n' +
                '                </div>\n' +
                '            </div>\n' +
                '        </div>\n' +
                '    </div>\n' +
                '    <div class="col-md-offset-2 col-md-10" aria-expanded="true" style="padding: 0">\n' +
                '        <div class="panel-body" style="padding: 0">\n' +
                '            <div class="col-md-12" style="font-style: italic;color: #c1cbd0; text-align: right">' + data.data[i].time + '</div>\n' +
                '        </div>\n' +
                '    </div>\n' +
                '</li>')
        }
    },
});

// 不换算单位
// Highcharts.setOptions({
//     lang: {
//         numericSymbols: null
//     }
// });

// 动力中心发电量
var dlzx_fdl_chart = new Highcharts.Chart({
    chart: {
        renderTo: 'dlzx_fdl',
        style: {
            fontFamily: 'Open Sans'
        }
    },
    title: {
        text: null,
    },

    xAxis: {
        title: {
            text: '时间'
        },
        reversed: true,
    },
    colors: [
        '#3598dc',
        '#e7505a',
        '#32c5d2',
        '#8e44ad',
    ],
    yAxis: {
        title: {
            text: '发电量 (万千瓦时)'
        },
        plotLines: [{
            value: 0,
            width: 1,
            color: '#808080'
        }]
    },
    tooltip: {
        valueSuffix: '万千瓦时'
    },
    legend: {
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle',
        borderWidth: 0
    },
    series: [{}]
});

// 新厂发电量
var xc_fdl_chart = new Highcharts.Chart({
    chart: {
        renderTo: 'xc_fdl',
        style: {
            fontFamily: 'Open Sans'
        }
    },
    title: {
        text: null,
    },

    xAxis: {
        title: {
            text: '时间'
        },
        reversed: true,
    },
    colors: [
        '#3598dc',
        '#e7505a',
        '#32c5d2',
        '#8e44ad',
    ],
    yAxis: {
        title: {
            text: '发电量 (万千瓦时)'
        },
        plotLines: [{
            value: 0,
            width: 1,
            color: '#808080'
        }]
    },
    tooltip: {
        valueSuffix: '万千瓦时'
    },
    legend: {
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle',
        borderWidth: 0
    },
    series: [{}]
});

// 老厂发电量
var lc_fdl_chart = new Highcharts.Chart({
    chart: {
        renderTo: 'lc_fdl',
        style: {
            fontFamily: 'Open Sans'
        }
    },
    title: {
        text: null,
    },

    xAxis: {
        title: {
            text: '时间'
        },
        reversed: true,
    },
    colors: [
        '#3598dc',
        '#e7505a',
        '#32c5d2',
        '#8e44ad',
    ],
    yAxis: {
        title: {
            text: '发电量 (万千瓦时)'
        },
        plotLines: [{
            value: 0,
            width: 1,
            color: '#808080'
        }]
    },
    tooltip: {
        valueSuffix: '万千瓦时'
    },
    legend: {
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle',
        borderWidth: 0
    },
    series: [{}]
});

function getMonthFDL() {
    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../get_month_fdl/",
        data: {},
        success: function (data) {
            var DLZX_JYTJ = data.DLZX_JYTJ;
            var LC_JYTJ = data.LC_JYTJ;
            setFDLChart(dlzx_fdl_chart, DLZX_JYTJ);
            setFDLChart(lc_fdl_chart, LC_JYTJ);
        },
    })
}

getMonthFDL();

function setFDLChart(chart, data) {
    while (chart.series.length > 0) {
        chart.series[0].remove(true);
    }

    // 设置横轴
    chart.xAxis[0].setCategories(data.categories);

    var fld_list = data.fld_list;
    for (var i = 0; i < fld_list.length; i++) {
        chart.addSeries({
            "name": fld_list[i].name,
            "data": fld_list[i].fdl,
            "color": fld_list[i].color,
        });
    }
}

$('#navtabs a').click(function (e) {
    // 解决图标自适应大小问题
    var tab_id = $(this).prop('id');
    console.log(tab_id)
    if (tab_id == "tabcheck1") {
        $("#xc_fdl").highcharts().reflow();
    }
    if (tab_id == "tabcheck2") {
        console.log(1111)
        $("#dlzx_fdl").highcharts().reflow();
    }
    if (tab_id == "tabcheck3") {
        $("#lc_fdl").highcharts().reflow();
    }
});
