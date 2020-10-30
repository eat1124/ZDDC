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
            $('#navtabs_1').find('a').eq(0).tab('show');
            var DLZX_JYTJ = data.DLZX_JYTJ;
            var LC_JYTJ = data.LC_JYTJ;
            var XC_JYTJ = data.XC_JYTJ;
            setFDLChart(dlzx_fdl_chart, DLZX_JYTJ);
            setFDLChart(lc_fdl_chart, LC_JYTJ);
            setFDLChart(xc_fdl_chart, XC_JYTJ);
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

// 解决图标自适应大小问题
$('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
    $("#xc_fdl").highcharts().reflow();
    $("#dlzx_fdl").highcharts().reflow();
    $("#lc_fdl").highcharts().reflow();
});


function getImportantTargets() {
    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../get_important_targets/",
        data: {},
        success: function (data) {
            $('#navtabs_2').find('a').eq(0).tab('show');
            var rr = data.data["RR"];
                mj = data.data["MJ"];
                jf = data.data["9F"];
            var rr_jyzbs = rr["JYZB"],
                rr_hbzbs = rr["HBZB"];
            var mj_jyzbs = mj["JYZB"],
                mj_hbzbs = mj["HBZB"];
            var jf_jyzbs = jf["JYZB"],
                jf_hbzbs = jf["HBZB"];

            /*
                燃热
             */
            //  经营指标
            var rr_jyzb_left = $("#tab_1_5").find("div#left_fdl");
            var rr_jyzb_right = $("#tab_1_5").find("div#right_fdl");

            rr_jyzb_left.empty();
            for (var i = 0; i < rr_jyzbs.length; i++) {
                rr_jyzb_left.append('<div class="col-md-12" style="margin-bottom: 5px;">\n' +
                    '    <div class="col-md-6 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + rr_jyzbs[i]["target_name"] + ':</div>\n' +
                    '    <div class="col-md-6 value" style="padding:0; text-align: right;"> ' + rr_jyzbs[i]["value"] + ' ' + rr_jyzbs[i]["unit"] + '</div>\n' +
                    '</div>');
            }
            //  环保指标
            var rr_hbzb_left = $("#tab_1_5").find("div#left_zh");
            var rr_hbzb_right = $("#tab_1_5").find("div#right_zh");

            rr_hbzb_left.empty();
            rr_hbzb_right.empty();
            for (var i = 0; i < rr_hbzbs.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    rr_hbzb_right.append('<div class="col-md-12" style="margin-bottom: 5px;">\n' +
                        '    <div class="col-md-6 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + rr_hbzbs[i]["target_name"] + ':</div>\n' +
                        '    <div class="col-md-6 value" style="padding:0; text-align: right;"> ' + rr_hbzbs[i]["value"] + ' ' + rr_hbzbs[i]["unit"] + '</div>\n' +
                        '</div>');
                } else {
                    rr_hbzb_left.append('<div class="col-md-12" style="margin-bottom: 5px;">\n' +
                        '    <div class="col-md-6 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + rr_hbzbs[i]["target_name"] + ':</div>\n' +
                        '    <div class="col-md-6 value" style="padding:0; text-align: right;"> ' + rr_hbzbs[i]["value"] + ' ' + rr_hbzbs[i]["unit"] + '</div>\n' +
                        '</div>');
                }
            }

            /*
                煤机
             */
            //  经营指标
            var mj_jyzb_left = $("#tab_1_4").find("div#left_fdl");
            var mj_jyzb_right = $("#tab_1_4").find("div#right_fdl");

            mj_jyzb_left.empty();
            for (var i = 0; i < mj_jyzbs.length; i++) {
                mj_jyzb_left.append('<div class="col-md-12" style="margin-bottom: 5px;">\n' +
                    '    <div class="col-md-6 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + mj_jyzbs[i]["target_name"] + ':</div>\n' +
                    '    <div class="col-md-6 value" style="padding:0; text-align: right;"> ' + mj_jyzbs[i]["value"] + ' ' + mj_jyzbs[i]["unit"] + '</div>\n' +
                    '</div>');
            }

            //  环保指标
            var mj_hbzb_left = $("#tab_1_4").find("div#left_zh");
            var mj_hbzb_right = $("#tab_1_4").find("div#right_zh");

            mj_hbzb_left.empty();
            mj_hbzb_right.empty();
            for (var i = 0; i < mj_hbzbs.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    mj_hbzb_right.append('<div class="col-md-12" style="margin-bottom: 5px;">\n' +
                        '    <div class="col-md-6 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + mj_hbzbs[i]["target_name"] + ':</div>\n' +
                        '    <div class="col-md-6 value" style="padding:0; text-align: right;"> ' + mj_hbzbs[i]["value"] + ' ' + mj_hbzbs[i]["unit"] + '</div>\n' +
                        '</div>');
                } else {
                    mj_hbzb_left.append('<div class="col-md-12" style="margin-bottom: 5px;">\n' +
                        '    <div class="col-md-6 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + mj_hbzbs[i]["target_name"] + ':</div>\n' +
                        '    <div class="col-md-6 value" style="padding:0; text-align: right;"> ' + mj_hbzbs[i]["value"] + ' ' + mj_hbzbs[i]["unit"] + '</div>\n' +
                        '</div>');
                }
            }

            /*
                9F
             */
            //  经营指标
            var jf_jyzb_left = $("#tab_1_6").find("div#left_fdl");
            var jf_jyzb_right = $("#tab_1_6").find("div#right_fdl");

            jf_jyzb_left.empty();
            jf_jyzb_right.empty();
            for (var i = 0; i < jf_jyzbs.length; i++) {
                jf_jyzb_left.append('<div class="col-md-12" style="margin-bottom: 5px;">\n' +
                    '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + jf_jyzbs[i]["target_name"] + ':</div>\n' +
                    '    <div class="col-md-4 value" style="padding:0; text-align: right;"> ' + jf_jyzbs[i]["value"] + ' ' + jf_jyzbs[i]["unit"] + '</div>\n' +
                    '</div>');
            }
            //  环保指标
            var jf_hbzb_left = $("#tab_1_6").find("div#left_zh");
            var jf_hbzb_right = $("#tab_1_6").find("div#right_zh");

            jf_hbzb_left.empty();
            jf_hbzb_right.empty();
            for (var i = 0; i < jf_hbzbs.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    jf_hbzb_right.append('<div class="col-md-12" style="margin-bottom: 5px;">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + jf_hbzbs[i]["target_name"] + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0; text-align: right;"> ' + jf_hbzbs[i]["value"] + ' ' + jf_hbzbs[i]["unit"] + '</div>\n' +
                        '</div>');
                } else {
                    jf_hbzb_left.append('<div class="col-md-12" style="margin-bottom: 5px;">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + jf_hbzbs[i]["target_name"] + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0; text-align: right;"> ' + jf_hbzbs[i]["value"] + ' ' + jf_hbzbs[i]["unit"] + '</div>\n' +
                        '</div>');
                }
            }
        }
    })
}

getImportantTargets();

/*
Demo Data
{
    "DLZX": {
        "FDL": {
            "FDL_LIST": [{"jz_name": "#1", "yest_value": 0, "cumulativemonth": 0, "cumulativeyear": 0},
                         {"jz_name": "#2", "yest_value": 0, "cumulativemonth": 0, "cumulativeyear": 0}],
            "TARGETS": [{"name": "target1", "value": "v1"}, {"name": "target2", "value": "v2"}]
        },
        "ZH": {
            "TARGETS": [{"name": "target1", "value": "v1"}, {"name": "target2", "value": "v2"}]
        },
        "HB": {
            "TARGETS": [{"name": "target1", "value": "v1"}, {"name": "target2", "value": "v2"}]
        },
        "NH": {
            "TARGETS": [{"name": "target1", "value": "v1"}, {"name": "target2", "value": "v2"}]
        }
    },
    "XC": {
        "FDL": {
            "FDL_LIST": [{"jz_name": "#11", "yest_value": 0, "cumulativemonth": 0, "cumulativeyear": 0},
                         {"jz_name": "#12", "yest_value": 0, "cumulativemonth": 0, "cumulativeyear": 0}],
            "TARGETS": [{"name": "target1", "value": "v1"}, {"name": "target2", "value": "v2"}]
        },
        "ZH": {
            "TARGETS": [{"name": "target1", "value": "v1"}, {"name": "target2", "value": "v2"}]
        },
        "HB": {
            "TARGETS": [{"name": "target1", "value": "v1"}, {"name": "target2", "value": "v2"}]
        },
        "NH": {
            "TARGETS": [{"name": "target1", "value": "v1"}, {"name": "target2", "value": "v2"}]
        }
    },
    "LC": {
        "FDL": {
            "FDL_LIST": [{"jz_name": "#21", "yest_value": 0, "cumulativemonth": 0, "cumulativeyear": 0},
                         {"jz_name": "#22", "yest_value": 0, "cumulativemonth": 0, "cumulativeyear": 0}],
            "TARGETS": [{"name": "target1", "value": "v1"}, {"name": "target2", "value": "v2"}]
        },
        "ZH": {
            "TARGETS": [{"name": "target1", "value": "v1"}, {"name": "target2", "value": "v2"}]
        },
        "HB": {
            "TARGETS": [{"name": "target1", "value": "v1"}, {"name": "target2", "value": "v2"}]
        },
        "NH": {
            "TARGETS": [{"name": "target1", "value": "v1"}, {"name": "target2", "value": "v2"}]
        }
    }
}
 */
