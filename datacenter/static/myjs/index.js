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
            var dlzx = data.data.DLZX;
            var xc = data.data.XC;
            var lc = data.data.LC;

            /*
                动力中心
             */
            //  发电量
            var dlzx_fdl_left = $("#tab_1_5").find("div#left_fdl");
            var dlzx_fdl_right = $("#tab_1_5").find("div#right_fdl");

            dlzx_fdl_left.empty();
            dlzx_fdl_right.empty();
            for (var i = 0; i < dlzx.FDL.TARGETS.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    dlzx_fdl_right.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + dlzx.FDL.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + dlzx.FDL.TARGETS[i].value + '</div>\n' +
                        '</div>');
                } else {
                    dlzx_fdl_left.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + dlzx.FDL.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + dlzx.FDL.TARGETS[i].value + '</div>\n' +
                        '</div>')
                }
            }
            var dlzx_fdl_today = $("#tab_1_5").find("tbody#fdl_today");
            dlzx_fdl_today.empty();
            for (var j = 0; j < dlzx.FDL.FDL_LIST.length; j++) {
                dlzx_fdl_today.append('<tr>\n' +
                    '    <td>' + dlzx.FDL.FDL_LIST[j].jz_name + '</td>\n' +
                    '    <td>' + dlzx.FDL.FDL_LIST[j].yest_value + '</td>\n' +
                    '    <td>' + dlzx.FDL.FDL_LIST[j].cumulativemonth + '</td>\n' +
                    '    <td>' + dlzx.FDL.FDL_LIST[j].cumulativeyear + '</td>\n' +
                    '</tr>');
            }
            //  综合
            var dlzx_zh_left = $("#tab_1_5").find("div#left_zh");
            var dlzx_zh_right = $("#tab_1_5").find("div#right_zh");

            dlzx_zh_left.empty();
            dlzx_zh_right.empty();
            for (var i = 0; i < dlzx.ZH.TARGETS.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    dlzx_zh_right.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + dlzx.ZH.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + dlzx.ZH.TARGETS[i].value + '</div>\n' +
                        '</div>');
                } else {
                    dlzx_zh_left.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + dlzx.ZH.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + dlzx.ZH.TARGETS[i].value + '</div>\n' +
                        '</div>')
                }
            }
            //  环保
            var dlzx_hb_left = $("#tab_1_5").find("div#left_hb");
            var dlzx_hb_right = $("#tab_1_5").find("div#right_hb");

            dlzx_hb_left.empty();
            dlzx_hb_right.empty();
            for (var i = 0; i < dlzx.HB.TARGETS.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    dlzx_hb_right.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + dlzx.HB.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + dlzx.HB.TARGETS[i].value + '</div>\n' +
                        '</div>');
                } else {
                    dlzx_hb_left.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + dlzx.HB.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + dlzx.HB.TARGETS[i].value + '</div>\n' +
                        '</div>')
                }
            }
            //  能耗
            var dlzx_nh_left = $("#tab_1_5").find("div#left_nh");
            var dlzx_nh_right = $("#tab_1_5").find("div#right_nh");

            dlzx_nh_left.empty();
            dlzx_nh_right.empty();
            for (var i = 0; i < dlzx.NH.TARGETS.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    dlzx_nh_right.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + dlzx.NH.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + dlzx.NH.TARGETS[i].value + '</div>\n' +
                        '</div>');
                } else {
                    dlzx_nh_left.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + dlzx.NH.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + dlzx.NH.TARGETS[i].value + '</div>\n' +
                        '</div>')
                }
            }

            /*
                新厂
             */
            //  发电量
            var xc_fdl_left = $("#tab_1_4").find("div#left_fdl");
            var xc_fdl_right = $("#tab_1_4").find("div#right_fdl");

            xc_fdl_left.empty();
            xc_fdl_right.empty();
            for (var i = 0; i < xc.FDL.TARGETS.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    xc_fdl_right.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + xc.FDL.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + xc.FDL.TARGETS[i].value + '</div>\n' +
                        '</div>');
                } else {
                    xc_fdl_left.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + xc.FDL.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + xc.FDL.TARGETS[i].value + '</div>\n' +
                        '</div>')
                }
            }
            var xc_fdl_today = $("#tab_1_4").find("tbody#fdl_today");
            xc_fdl_today.empty();
            for (var j = 0; j < xc.FDL.FDL_LIST.length; j++) {
                xc_fdl_today.append('<tr>\n' +
                    '    <td>' + xc.FDL.FDL_LIST[j].jz_name + '</td>\n' +
                    '    <td>' + xc.FDL.FDL_LIST[j].yest_value + '</td>\n' +
                    '    <td>' + xc.FDL.FDL_LIST[j].cumulativemonth + '</td>\n' +
                    '    <td>' + xc.FDL.FDL_LIST[j].cumulativeyear + '</td>\n' +
                    '</tr>');
            }
            //  综合
            var xc_zh_left = $("#tab_1_4").find("div#left_zh");
            var xc_zh_right = $("#tab_1_4").find("div#right_zh");

            xc_zh_left.empty();
            xc_zh_right.empty();
            for (var i = 0; i < xc.ZH.TARGETS.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    xc_zh_right.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + xc.ZH.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + xc.ZH.TARGETS[i].value + '</div>\n' +
                        '</div>');
                } else {
                    xc_zh_left.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + xc.ZH.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + xc.ZH.TARGETS[i].value + '</div>\n' +
                        '</div>')
                }
            }
            //  环保
            var xc_hb_left = $("#tab_1_4").find("div#left_hb");
            var xc_hb_right = $("#tab_1_4").find("div#right_hb");

            xc_hb_left.empty();
            xc_hb_right.empty();
            for (var i = 0; i < xc.HB.TARGETS.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    xc_hb_right.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + xc.HB.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + xc.HB.TARGETS[i].value + '</div>\n' +
                        '</div>');
                } else {
                    xc_hb_left.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + xc.HB.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + xc.HB.TARGETS[i].value + '</div>\n' +
                        '</div>')
                }
            }
            //  能耗
            var xc_nh_left = $("#tab_1_4").find("div#left_nh");
            var xc_nh_right = $("#tab_1_4").find("div#right_nh");

            xc_nh_left.empty();
            xc_nh_right.empty();
            for (var i = 0; i < xc.NH.TARGETS.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    xc_nh_right.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + xc.NH.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + xc.NH.TARGETS[i].value + '</div>\n' +
                        '</div>');
                } else {
                    xc_nh_left.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + xc.NH.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + xc.NH.TARGETS[i].value + '</div>\n' +
                        '</div>')
                }
            }

            /*
                老厂
             */
            //  发电量
            var lc_fdl_left = $("#tab_1_6").find("div#left_fdl");
            var lc_fdl_right = $("#tab_1_6").find("div#right_fdl");

            lc_fdl_left.empty();
            lc_fdl_right.empty();
            for (var i = 0; i < lc.FDL.TARGETS.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    lc_fdl_right.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + lc.FDL.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + lc.FDL.TARGETS[i].value + '</div>\n' +
                        '</div>');
                } else {
                    lc_fdl_left.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + lc.FDL.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + lc.FDL.TARGETS[i].value + '</div>\n' +
                        '</div>')
                }
            }
            var lc_fdl_today = $("#tab_1_6").find("tbody#fdl_today");
            lc_fdl_today.empty();
            for (var j = 0; j < lc.FDL.FDL_LIST.length; j++) {
                lc_fdl_today.append('<tr>\n' +
                    '    <td>' + lc.FDL.FDL_LIST[j].jz_name + '</td>\n' +
                    '    <td>' + lc.FDL.FDL_LIST[j].yest_value + '</td>\n' +
                    '    <td>' + lc.FDL.FDL_LIST[j].cumulativemonth + '</td>\n' +
                    '    <td>' + lc.FDL.FDL_LIST[j].cumulativeyear + '</td>\n' +
                    '</tr>');
            }
            //  综合
            var lc_zh_left = $("#tab_1_6").find("div#left_zh");
            var lc_zh_right = $("#tab_1_6").find("div#right_zh");

            lc_zh_left.empty();
            lc_zh_right.empty();
            for (var i = 0; i < lc.ZH.TARGETS.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    lc_zh_right.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + lc.ZH.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + lc.ZH.TARGETS[i].value + '</div>\n' +
                        '</div>');
                } else {
                    lc_zh_left.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + lc.ZH.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + lc.ZH.TARGETS[i].value + '</div>\n' +
                        '</div>')
                }
            }
            //  环保
            var lc_hb_left = $("#tab_1_6").find("div#left_hb");
            var lc_hb_right = $("#tab_1_6").find("div#right_hb");

            lc_hb_left.empty();
            lc_hb_right.empty();
            for (var i = 0; i < lc.HB.TARGETS.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    lc_hb_right.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + lc.HB.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + lc.HB.TARGETS[i].value + '</div>\n' +
                        '</div>');
                } else {
                    lc_hb_left.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + lc.HB.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + lc.HB.TARGETS[i].value + '</div>\n' +
                        '</div>')
                }
            }
            //  能耗
            var lc_nh_left = $("#tab_1_6").find("div#left_nh");
            var lc_nh_right = $("#tab_1_6").find("div#right_nh");

            lc_nh_left.empty();
            lc_nh_right.empty();
            for (var i = 0; i < lc.NH.TARGETS.length; i++) {
                if ((i + 1) % 2 == 0) {    // 偶数
                    lc_nh_right.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + lc.NH.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + lc.NH.TARGETS[i].value + '</div>\n' +
                        '</div>');
                } else {
                    lc_nh_left.append('<div class="col-md-12">\n' +
                        '    <div class="col-md-8 name" style="padding:0"><span><i class="fa fa-caret-right"></i></span> ' + lc.NH.TARGETS[i].name + ':</div>\n' +
                        '    <div class="col-md-4 value" style="padding:0"> ' + lc.NH.TARGETS[i].value + '</div>\n' +
                        '</div>')
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
