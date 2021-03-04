var csrfToken = $('[name="csrfmiddlewaretoken"]').val();
// 加载中样式选择 $(el).show()展示 $(el).hide()隐藏
$.fakeLoader = function (options) {
    var settings = $.extend({
        targetClass: 'fakeLoader',
        bgColor: '#2ecc71',
        spinner: 'spinner2'
    }, options);
    var spinner01 = '<div class="fl fl-spinner spinner1"><div class="double-bounce1"></div><div class="double-bounce2"></div></div>';
    var spinner02 = '<div class="fl fl-spinner spinner2"><div class="spinner-container container1"><div class="circle1"></div><div class="circle2"></div><div class="circle3"></div><div class="circle4"></div></div><div class="spinner-container container2"><div class="circle1"></div><div class="circle2"></div><div class="circle3"></div><div class="circle4"></div></div><div class="spinner-container container3"><div class="circle1"></div><div class="circle2"></div><div class="circle3"></div><div class="circle4"></div></div></div>';
    var spinner03 = '<div class="fl fl-spinner spinner3"><div class="dot1"></div><div class="dot2"></div></div>';
    var spinner04 = '<div class="fl fl-spinner spinner4"></div>';
    var spinner05 = '<div class="fl fl-spinner spinner5"><div class="cube1"></div><div class="cube2"></div></div>';
    var spinner06 = '<div class="fl fl-spinner spinner6"><div class="rect1"></div><div class="rect2"></div><div class="rect3"></div><div class="rect4"></div><div class="rect5"></div></div>';
    var spinner07 = '<div class="fl fl-spinner spinner7"><div class="circ1"></div><div class="circ2"></div><div class="circ3"></div><div class="circ4"></div></div>';

    var el = $('body').find('.' + settings.targetClass);
    el.each(function () {
        var a = settings.spinner;

        switch (a) {
            case 'spinner1':
                el.html(spinner01);
                break;
            case 'spinner2':
                el.html(spinner02);
                break;
            case 'spinner3':
                el.html(spinner03);
                break;
            case 'spinner4':
                el.html(spinner04);
                break;
            case 'spinner5':
                el.html(spinner05);
                break;
            case 'spinner6':
                el.html(spinner06);
                break;
            case 'spinner7':
                el.html(spinner07);
                break;
            default:
                el.html(spinner01);
        }
    });

    el.css({
        'backgroundColor': settings.bgColor
    });
    return el;
};
var el = $.fakeLoader({
    bgColor: "transparent;",
    spinner: "spinner7"
});
var customModal = {
    "show": function () {
        $('#report_search').modal('show');
        $(el).show();
        $(".modal-backdrop").css('opacity', '0.3');
    },
    "hide": function () {
        $('#report_search').modal('hide');
        $(el).hide();
        $(".modal-backdrop").css('opacity', '0.5');
    },
};

function getQueryString(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i");
    var r = window.location.search.substr(1).match(reg);
    if (r != null)
        return unescape(r[2]);
    return null;
}

var date_type = getQueryString("date_type");

function renderSeasonDate(node, sgl, period) {
    var ele = $(node);
    laydate.render({
        elem: node,
        type: 'month',
        format: 'yyyy-第M季度',
        range: sgl ? null : '~',
        min: "1900-1-1",
        max: "2999-12-31",
        btns: ['confirm'],
        ready: function () {
            var hd = $("#layui-laydate" + ele.attr("lay-key"));
            if (hd.length > 0) {
                hd.click(function () {
                    ren($(this));
                });
            }
            ren(hd);
        },

        done: function (value) {
            var finaltime = '';
            if (value) {
                value = value.split('-');
                var year = value[0];
                var season = value[1];
                if (season == '第1季度') {
                    var timeend = '03-31';
                    finaltime = year + '-' + timeend;
                }
                if (season == '第2季度') {
                    var timeend = '06-30';
                    finaltime = year + '-' + timeend
                }
                if (season == '第3季度') {
                    var timeend = '09-30';
                    finaltime = year + '-' + timeend
                }
                if (season == '第4季度') {
                    var timeend = '12-31';
                    finaltime = year + '-' + timeend
                }
            }
            // 处理日期
            if (period == "start") {
                $('#start_daydate').val(finaltime);
            } else {
                $('#end_daydate').val(finaltime);
            }
        }

    });
    var ren = function (thiz) {
        var mls = thiz.find(".laydate-month-list");
        mls.each(function (i, e) {
            $(this).find("li").each(function (inx, ele) {
                var cx = ele.innerHTML;
                if (inx < 4) {
                    ele.innerHTML = cx.replace(/月/g, "季度").replace(/一/g, "第1").replace(/二/g, "第2").replace(/三/g, "第3").replace(/四/g, "第4");
                } else {
                    ele.style.display = "none";
                }
            });
        });
    }
}

function renderYearDate(node, sgl, period) {
    var ele = $(node);
    laydate.render({
        elem: node,
        type: 'month',
        format: 'yyyy-h半年',
        range: sgl ? null : '~',
        min: "1900-1-1",
        max: "2999-12-31",
        btns: ['confirm'],
        ready: function () {
            var hd = $("#layui-laydate" + ele.attr("lay-key"));
            if (hd.length > 0) {
                hd.click(function () {
                    ren($(this));
                });
            }
            ren(hd);
        },

        done: function (value) {
            var finaltime = '';
            if (value) {
                value = value.split('-');
                var year = value[0];
                var halfyear = value[1];

                if (halfyear == '上半年') {
                    var timeend = '06-30';
                    finaltime = year + '-' + timeend
                }
                if (halfyear == '下半年') {
                    var timeend = '12-31';
                    finaltime = year + '-' + timeend
                }
            }
            // 处理日期
            if (period == "start") {
                $('#start_daydate').val(finaltime);
            } else {
                $('#end_daydate').val(finaltime);
            }
        }

    });
    var ren = function (thiz) {
        var mls = thiz.find(".laydate-month-list");
        mls.each(function (i, e) {
            $(this).find("li").each(function (inx, ele) {
                var cx = ele.innerHTML;
                if (inx < 2) {
                    cx = cx.replace(/月/g, "半年");
                    ele.innerHTML = cx.replace(/一/g, "上").replace(/二/g, "下");

                } else {
                    ele.style.display = "none";
                }
            });
        });
    }
}

(function customDateDisplay() {
    if (date_type == "10") {
        $('#start_daydate').datetimepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            startView: 2,
            minView: 2,
        });
        $('#end_daydate').datetimepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            startView: 2,
            minView: 2,
        });
    } else if (date_type == "11") {
        $('#start_daydate').datetimepicker({
            format: 'yyyy-mm',
            autoclose: true,
            startView: 3,
            minView: 3,
        });
        $('#end_daydate').datetimepicker({
            format: 'yyyy-mm',
            autoclose: true,
            startView: 3,
            minView: 3,
        });
    } else if (date_type == "12") {
        renderSeasonDate(document.getElementById('start_date_seasondate'), 1, "start");
        renderSeasonDate(document.getElementById('end_date_seasondate'), 1, "end");
        $('#start_daydate').hide();
        $('#end_daydate').hide();
        $('#start_date_seasondate').show();
        $('#end_date_seasondate').show();
    } else if (date_type == "13") {
        renderYearDate(document.getElementById('start_date_yeardate'), 1, "start");
        renderYearDate(document.getElementById('end_date_yeardate'), 1, "end");
        $('#start_daydate').hide();
        $('#end_daydate').hide();
        $('#start_date_yeardate').show();
        $('#end_date_yeardate').show();
    } else if (date_type == "14") {
        $('#start_daydate').datetimepicker({
            format: 'yyyy',
            autoclose: true,
            startView: 4,
            minView: 4,
        });
        $('#end_daydate').datetimepicker({
            format: 'yyyy',
            autoclose: true,
            startView: 4,
            minView: 4,
        });
    } else {
        alert("不存在该周期形式.")
    }
})();

function getStatisticReport(start_date, end_date, search_id, date_type) {
    customModal.show();
    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../get_statistic_report/?csrfmiddlewaretoken=" + csrfToken + "&" + "start_date=" + start_date + "&end_date=" + end_date + "&search_id=" + search_id + "&date_type=" + date_type,
        data: {
            csrfmiddlewaretoken: csrfToken,
            start_date: start_date,
            end_date: end_date,
            search_id: search_id,
            date_type: date_type,
        },
        success: function (data) {
            customModal.hide();
            var status = data.status,
                info = data.info,
                table_data = data.data,
                v_sums = table_data.v_sums;
            if (status == 1) {
                var head_data = table_data.head_data,
                    body_data = table_data.body_data;
                $('#statistic_report_dt').find('thead').empty();
                $('#statistic_report_dt').find('tbody').empty();

                // thead
                var first_head_tr = '<tr>',
                    second_head_tr = '<tr>';
                for (var i = 0; i < head_data.length; i++) {
                    var col_name = head_data[i]['col_name'],
                        rowspan = head_data[i]['rowspan'],
                        colspan = head_data[i]['colspan'],
                        targets = head_data[i]['targets'];
                    first_head_tr += '<th rowspan="' + rowspan + '" colspan="' + colspan + ' " style="text-align: center;vertical-align: middle;font-weight: bold;">' + col_name + '</th>';

                    if (targets.length > 1) {
                        for (var j = 0; j < targets.length; j++) {
                            second_head_tr += '<th style="text-align: center;vertical-align: middle;font-weight: bold;">' + targets[j]['new_target_name'] + '</th>';
                        }
                    }
                }
                first_head_tr += '</tr>';
                second_head_tr += '</tr>';
                $('#statistic_report_dt').find('thead').append(first_head_tr).append(second_head_tr);

                // tbody
                for (var k = 0; k < body_data.length; k++) {
                    var tbody_tr = '<tr>';
                    tbody_tr += '<td style="text-align: center;">' + body_data[k]['date'] + '</td>';
                    for (var l = 0; l < body_data[k]['target_values'].length; l++) {
                        tbody_tr += '<td style="text-align: right; ">' + body_data[k]['target_values'][l]["value"] + '</td>';
                    }
                    tbody_tr += '</td>';
                    $('#statistic_report_dt').find('tbody').append(tbody_tr);
                }
                /**
                 * 合计
                 */
                var v_sum_tr = '<tr><td style="text-align: center;">合计</td>';
                for (var L = 0; L < v_sums.length; L++) {
                    v_sum_tr += '<td style="text-align: right;"><input name="statistic_type" hidden>' + v_sums[L]["v"] + '</td>';
                }
                v_sum_tr += '</td></tr>';
                $('#statistic_report_dt').find('tbody').append(v_sum_tr);
                /**
                 * 总计
                 */
                var first_zj_tr = '<tr>';
                var td_num = 1;
                for (var m = 0; m < head_data.length; m++) {
                    var col_name = head_data[m]['col_name'],
                        colspan = head_data[m]['colspan'];
                    if (m == 0) {
                        first_zj_tr += '<td colspan="' + colspan + ' " style="text-align: center;">总计</td>';
                    } else {
                        // 合计求和->总计
                        // 根据指标statistic_type求总计
                        var zj_sum = 0;
                        var hj_tds = $('#statistic_report_dt').find('tr').eq(-1).find('td');
                        var statistic_type = null;
                        var avai_num = 0;
                        for (var n = 0; n < colspan; n++) {
                            hj_td = hj_tds.eq(td_num);
                            var c_hj = parseFloat(hj_td.text());
                            statistic_type = hj_td.find("input[name='statistic_type']").val();
                            
                            if (!isNaN(c_hj)) {
                                zj_sum = math.add(math.bignumber(Number(zj_sum)), math.bignumber(Number(c_hj))); // math.js精度计算
                                avai_num += 1;
                            }

                            td_num += 1;
                        }
                        if (statistic_type == '1'){  // 求和
                            // ...
                        } else if (statistic_type == '2'){
                            if (avai_num !=0){
                                zj_sum = (zj_sum/avai_num).toFixed(2)
                            }
                        } else {
                            zj_sum = "-"
                        }

                        first_zj_tr += '<td colspan="' + colspan + ' " style="text-align: center;">' + zj_sum + '</td>';
                    }
                }
                first_zj_tr += '</tr>';
                $('#statistic_report_dt').find('tbody').append(first_zj_tr);

            } else {
                alert(info);
            }
        }
    })
}

getStatisticReport($('#start_daydate').val(), $('#end_daydate').val(), $('#search_id').val(), date_type);

$('#search').click(function () {
    var start_date = $('#start_daydate').val(),
        end_date = $('#end_daydate').val(),
        search_id = $('#search_id').val();
    getStatisticReport(start_date, end_date, search_id, date_type);
});

$('#to_excel').click(function () {
    if (confirm("确定要导出EXCEL文件吗？")) {
        $("#statistic_report_dt").tableExport({fileName: $('#search_name').val(), type: "excel", escape: "false"});
    }
});

