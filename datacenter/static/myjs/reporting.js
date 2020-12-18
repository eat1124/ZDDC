$(document).ready(function () {
    // 加载中样式初始化
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
    // 加载中样式选择 $(el).show()展示 $(el).hide()隐藏
    var el = $.fakeLoader({
        bgColor: "transparent;",
        spinner: "spinner7"
    });

    function seasonFunction() {
        renderSeasonDate(document.getElementById('season'), 1);

        function renderSeasonDate(ohd, sgl) {
            var ele = $(ohd);
            laydate.render({
                elem: ohd,
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
                    $('#reporting_date').val(finaltime);
                    var table1 = $('#sample_1').DataTable();
                    table1.ajax.url("../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
                        "&reporting_date=" + $('#reporting_date').val() + "&operationtype=15" +
                        "&funid=" + $('#funid').val()).load();
                    var table2 = $('#sample_2').DataTable();
                    table2.ajax.url("../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
                        "&reporting_date=" + $('#reporting_date').val() + "&operationtype=16" +
                        "&funid=" + $('#funid').val()).load();
                    var table3 = $('#sample_3').DataTable();
                    table3.ajax.url("../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
                        "&reporting_date=" + $('#reporting_date').val() + "&operationtype=17" +
                        "&funid=" + $('#funid').val()).load();
                    var table4 = $('#sample_4').DataTable();
                    table4.ajax.url("../../../reporting_search_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val() + "&searchapp=" + $('#searchapp').val()).load();
                    var table5 = $('#sample_5').DataTable();
                    table5.ajax.url("../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
                        "&reporting_date=" + $('#reporting_date').val() + "&operationtype=1" +
                        "&funid=" + $('#funid').val()).load();
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
    }

    function yearFunction() {
        renderYearDate(document.getElementById('year'), 1);

        function renderYearDate(ohd, sgl) {
            var ele = $(ohd);
            laydate.render({
                elem: ohd,
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
                    $('#reporting_date').val(finaltime);
                    var table1 = $('#sample_1').DataTable();
                    table1.ajax.url("../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
                        "&reporting_date=" + $('#reporting_date').val() + "&operationtype=15" +
                        "&funid=" + $('#funid').val()).load();
                    var table2 = $('#sample_2').DataTable();
                    table2.ajax.url("../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
                        "&reporting_date=" + $('#reporting_date').val() + "&operationtype=16" +
                        "&funid=" + $('#funid').val()).load();
                    var table3 = $('#sample_3').DataTable();
                    table3.ajax.url("../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
                        "&reporting_date=" + $('#reporting_date').val() + "&operationtype=17" +
                        "&funid=" + $('#funid').val()).load();
                    var table4 = $('#sample_4').DataTable();
                    table4.ajax.url("../../../reporting_search_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val() + "&searchapp=" + $('#searchapp').val()).load();
                    var table5 = $('#sample_5').DataTable();
                    table5.ajax.url("../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
                        "&reporting_date=" + $('#reporting_date').val() + "&operationtype=1" +
                        "&funid=" + $('#funid').val()).load();
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
    }

    var search_app_list = eval($('#search_app_list').val());

    // 业务下拉框
    function workSelectInit() {
        $('#works').empty();
        var pre = '<option selected value="" >全部</option>';
        for (var i = 0; i < search_app_list.length; i++) {
            if (search_app_list[i].works.length > 0) {
                pre += '<optgroup label="' + search_app_list[i].name + '" class="dropdown-header">';
                for (var j = 0; j < search_app_list[i].works.length; j++) {
                    pre += '<option value="' + search_app_list[i].works[j].id + '">' + search_app_list[i].works[j].name + '</option>';
                }
                pre += '</optgroup>';
            }
        }
        $('#works').append(pre);
    }

    workSelectInit();

    // 数据录入 operationtype 15
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "bPaginate": false,
        "bFilter": false,
        "ajax": "../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
            "&reporting_date=" + $('#reporting_date').val() + "&operationtype=15" + "&funid=" + $('#funid').val(),
        "columns": [
            {"data": "id"},
            {"data": "target_name"},
            {"data": "target_unity"},
            {"data": "target_code"},
            {"data": "target_businesstypename"},
            {"data": "target_unitname"},
            {"data": "todayvalue"},
            {"data": "judgevalue"},
            {"data": "curvalue"},
            {"data": "cumulativemonth"},
            {"data": "cumulativequarter"},
            {"data": "cumulativehalfyear"},
            {"data": "cumulativeyear"},
        ],

        "columnDefs": [
            {
                "targets": 0,
                "visible": false,
            },
            {
                "targets": 3,
                "visible": false,
            },
            {
                "targets": 4,
                "visible": false,
            },
            {
                "targets": 5,
                "visible": false,
            },
            {
                "targets": -7,
                "mRender": function (data, type, full) {
                    //发布之后，把输入框设置为不可修改，取消发布后可以修改，通过字段
                    var disabled = "";
                    if (full.releasestate=='1'){
                        disabled = "disabled"
                    }
                    return "<input " + disabled + " style='margin-top:-5px;width:134px;height:24px;' id='table1_todayvalue_" + full.id + "' name='table1_todayvalue'  type='number' value='" + data + "'></input>"
                }
            },
            {
                "targets": -6,
                "mRender": function (data, type, full) {
                    //发布之后，把输入框设置为不可修改，取消发布后可以修改，通过字段
                    var disabled = "";
                    if (full.releasestate=='1'){
                        disabled = "disabled"
                    }
                    return "<input " + disabled + " style='margin-top:-5px;width:134px;height:24px;' id='table1_judgevalue_" + full.id + "' name='table1_judgevalue'  type='number' value='" + data + "'></input>"

                }
            },
            {
                "targets": -5,
                "mRender": function (data, type, full) {
                    //发布之后，把输入框设置为不可修改，取消发布后可以修改，通过字段
                    var disabled = "";
                    if (full.releasestate=='1'){
                        disabled = "disabled"
                    }
                    if (full.target_datatype == 'numbervalue') {
                        return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table1_curvalue_" + full.id + "' name='table1_curvalue'  type='number' value='" + data + "'></input>"
                    }
                    if (full.target_datatype == 'date') {
                        return "<input " + disabled + " class='table1_curvaluedate' style='margin-top:-5px;width:134px;height:24px;' id='table1_curvaluedate_" + full.id + "' name='table1_curvaluedate'  type='datetime'  value='" + full.curvaluedate + "'></input>"
                    }
                    if (full.target_datatype == 'text') {
                        return "<input " + disabled + " style='margin-top:-5px;width:134px;height:24px;'  id='table1_curvaluetext_" + full.id + "' name='table1_curvaluetext'  type='text' value='" + full.curvaluetext + "'></input>"
                    }
                }
            },
            {
                "targets": -4,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table1_cumulativemonth_" + full.id + "' name='table1_cumulativemonth'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -3,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table1_cumulativequarter_" + full.id + "' name='table1_cumulativequarter'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -2,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table1_cumulativehalfyear_" + full.id + "' name='table1_cumulativehalfyear'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -1,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table1_cumulativeyear_" + full.id + "' name='table1_cumulativeyear'  type='text' value='" + data + "'></input>"
                }
            },
        ],
        "oLanguage": {
            "sLengthMenu": "每页显示 _MENU_ 条记录",
            "sZeroRecords": "抱歉， 没有找到",
            "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
            "sInfoEmpty": "没有数据",
            "sInfoFiltered": "(从 _MAX_ 条数据中检索)",
            "sSearch": "搜索",
            "oPaginate": {
                "sFirst": "首页",
                "sPrevious": "前一页",
                "sNext": "后一页",
                "sLast": "尾页"
            },
            "sZeroRecords": "没有检索到数据",
        },
        // 加载结束回调函数
        "fnDrawCallback": function (data) {
            layui.use('laydate', function () {
                var laydate = layui.laydate;

                $('input[id^="table1_curvaluedate_"]').each(function () {
                    var d_ele = $(this).prop("id");
                    laydate.render({
                        elem: '#' + d_ele,
                        type: 'datetime',
                        theme: '#428bca'
                    });
                });
            });
            if (data.aoData.length > 0) {
                $("#new1").hide();
            } else {
                $("#new1").show();
                $("#save1").hide();
                $("#del1").hide();
                $("#release1").hide();
                $("#gorelease1").hide();
                $("#unrelease1").hide();
                $("#cancel_release1").hide();
            }
        },
        // 创建行回调函数
        "createdRow": function (row, data, index) {
            if (data.target_warn_range){
                var target_warn_range = parseFloat(data.target_warn_range)/100;
                var curvalue = parseFloat(data.curvalue);
                var yesterday_curvalue = parseFloat(data.yesterday_curvalue);
                if ((curvalue > yesterday_curvalue * (1 + target_warn_range)) || (curvalue < yesterday_curvalue / (1 + target_warn_range))){
                    $('td', row).css("color", "#0000FF");
                }
            }
            if ((data.target_upperlimit && data.curvalue > data.target_upperlimit) || (data.target_lowerlimit && data.curvalue < data.target_lowerlimit)){
                $('td', row).css("color", "#0000FF");
            }
            // 1 发布 0 未发布
            // gorelease1 已发布 unrelease1 未发布
            if (data.releasestate == '0') {
                $("#save1").show();
                $("#del1").show();
                $("#release1").show();
                $("#gorelease1").hide();
                $("#unrelease1").show();
                $("#cancel_release1").hide();

            }
            if (data.releasestate == '1') {
                $("#new1").hide();
                $("#save1").hide();
                $("#del1").hide();
                $("#release1").hide();
                $("#unrelease1").hide();
                $("#gorelease1").show();
                $("#cancel_release1").show();
            }

        },
    });
    // 填当前值，月累积、季累积、半年累积、年累积自动累加
    $('#sample_1 tbody').on('change', 'input[name="table1_todayvalue"]', function () {
        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $('#table1_curvalue_' + data.id).val(math.number(math.add(math.bignumber(Number($('#table1_todayvalue_' + data.id).val())), math.bignumber(Number($('#table1_judgevalue_' + data.id).val())))));

        // 累计值 月、季、半年、年
        if (['1', '2', '3', '4'].indexOf(data.target_cumulative) != -1) {
            $.ajax({
                type: "POST",
                url: "../../../ajax_cumulate/",
                data: {
                    cur_value: $('#table1_curvalue_' + data.id).val(),
                    target_id: data.target_id,
                    reporting_date: $('#reporting_date').val(),
                    cycletype: $('#cycletype').val(),
                },
                success: function (ajax_data) {
                    if (ajax_data.status == 1) {
                        $('#table1_cumulativemonth_' + data.id).val(ajax_data.data.cumulativemonth);   // math.js精度计算
                        $('#table1_cumulativequarter_' + data.id).val(ajax_data.data.cumulativequarter);
                        $('#table1_cumulativehalfyear_' + data.id).val(ajax_data.data.cumulativehalfyear);
                        $('#table1_cumulativeyear_' + data.id).val(ajax_data.data.cumulativeyear)
                    } else {
                        alert(ajax_data.data);
                    }
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }
        // 超过上限，低于下限标红
        if ((data.target_upperlimit && Number($('#table1_curvalue_' + data.id).val()) > data.target_upperlimit) || (data.target_lowerlimit && Number($('#table1_curvalue_' + data.id).val()) < data.target_lowerlimit)) {
            $('td', $(this).parents('tr')).css("color", "#0000FF");
        } else {
            $('td', $(this).parents('tr')).css("color", "#000000");
        }
    });

    $('#sample_1 tbody').on('change', 'input[name="table1_judgevalue"]', function () {
        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $('#table1_curvalue_' + data.id).val(math.number(math.add(math.bignumber(Number($('#table1_todayvalue_' + data.id).val())), math.bignumber(Number($('#table1_judgevalue_' + data.id).val())))));

        // 累计值 月、季、半年、年
        if (['1', '2', '3', '4'].indexOf(data.target_cumulative) != -1) {
            $.ajax({
                type: "POST",
                url: "../../../ajax_cumulate/",
                data: {
                    cur_value: $('#table1_curvalue_' + data.id).val(),
                    target_id: data.target_id,
                    reporting_date: $('#reporting_date').val(),
                    cycletype: $('#cycletype').val(),
                },
                success: function (ajax_data) {
                    if (ajax_data.status == 1) {
                        $('#table1_cumulativemonth_' + data.id).val(ajax_data.data.cumulativemonth);   // math.js精度计算
                        $('#table1_cumulativequarter_' + data.id).val(ajax_data.data.cumulativequarter);
                        $('#table1_cumulativehalfyear_' + data.id).val(ajax_data.data.cumulativehalfyear);
                        $('#table1_cumulativeyear_' + data.id).val(ajax_data.data.cumulativeyear)
                    } else {
                        alert(ajax_data.data);
                    }
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }
        // 超过上限，低于下限标红
        if ((data.target_upperlimit && Number($('#table1_curvalue_' + data.id).val()) > data.target_upperlimit) || (data.target_lowerlimit && Number($('#table1_curvalue_' + data.id).val()) < data.target_lowerlimit)) {
            $('td', $(this).parents('tr')).css("color", "#0000FF");
        } else {
            $('td', $(this).parents('tr')).css("color", "#000000");
        }
    });

    // 数据提取 operationtype 16
    $('#sample_2').dataTable({
        "bAutoWidth": true,
        "bSort": true,
        "bProcessing": true,
        "bPaginate": false,
        "bFilter": false,
        "ajax": "../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" +
            $('#reporting_date').val() + "&operationtype=16" + "&funid=" + $('#funid').val(),
        "columns": [
            {"data": "id"},
            {"data": "target_name"},
            {"data": "target_unity"},
            {"data": "target_code"},
            {"data": "target_businesstypename"},
            {"data": "target_unitname"},
            {"data": "todayvalue"},
            {"data": "judgevalue"},
            {"data": "curvalue"},
            {"data": "cumulativemonth"},
            {"data": "cumulativequarter"},
            {"data": "cumulativehalfyear"},
            {"data": "cumulativeyear"},
            {"data": null},
        ],

        "columnDefs": [
            {
                "targets": 0,
                "visible": false,
            },
            {
                "targets": 3,
                "visible": false,
            },
            {
                "targets": 4,
                "visible": false,
            },
            {
                "targets": 5,
                "visible": false,
            },
            {
                "targets": -8,
                "mRender": function (data, type, full) {
                    //发布之后，把输入框设置为不可修改，取消发布后可以修改，通过字段
                    var disabled = "";
                    if (full.releasestate=='1'){
                        disabled = "disabled"
                    }
                    return "<input " + disabled + " style='margin-top:-5px;width:134px;height:24px;' id='table2_todayvalue_" + full.id + "' name='table2_todayvalue'  type='number' value='" + data + "'></input>"
                }
            },
            {
                "targets": -7,
                "mRender": function (data, type, full) {
                    //发布之后，把输入框设置为不可修改，取消发布后可以修改，通过字段
                    var disabled = "";
                    if (full.releasestate=='1'){
                        disabled = "disabled"
                    }
                    return "<input " + disabled + " style='margin-top:-5px;width:134px;height:24px;' id='table2_judgevalue_" + full.id + "' name='table2_judgevalue'  type='number' value='" + data + "'></input>"

                }
            },
            {
                "targets": -6,
                "mRender": function (data, type, full) {
                    var disabled = "";
                    if (full.releasestate=='1'){
                        disabled = "disabled"
                    }
                    if (full.target_datatype == 'numbervalue') {
                        return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table2_curvalue_" + full.id + "' name='table2_curvalue'  type='number' value='" + data + "'></input>"
                    }
                    if (full.target_datatype == 'date') {
                        return "<input " + disabled + " class='table2_curvaluedate'style='margin-top:-5px;width:134px;height:24px;' id='table2_curvaluedate_" + full.id + "' name='table2_curvaluedate'  type='datetime'  value='" + full.curvaluedate + "'></input>"
                    }
                    if (full.target_datatype == 'text') {
                        return "<input " + disabled + " style='margin-top:-5px;width:134px;height:24px;' id='table2_curvaluetext_" + full.id + "' name='table2_curvaluetext'  type='text' value='" + full.curvaluetext + "'></input>"
                    }
                }
            },
            {
                "targets": -5,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table2_cumulativemonth_" + full.id + "' name='table2_cumulativemonth'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -4,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table2_cumulativequarter_" + full.id + "' name='table2_cumulativequarter'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -3,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table2_cumulativehalfyear_" + full.id + "' name='table2_cumulativehalfyear'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -2,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table2_cumulativeyear_" + full.id + "' name='table2_cumulativeyear'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -1,
                "data": null,
                "width": "80px",
                "orderable": false,
                "mRender": function (data, type, full) {
                    var disabled = "";
                    if (full.releasestate=='1'){
                        disabled = "disabled"
                    }
                    return "<button " + disabled + " id='single_reextract' title='重新提取' class='btn btn-xs btn-primary' type='button'><i class='fa fa-hand-paper-o'></i></button>"
                }

            }
        ],
        "oLanguage": {
            "sLengthMenu": "每页显示 _MENU_ 条记录",
            "sZeroRecords": "抱歉， 没有找到",
            "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
            "sInfoEmpty": "没有数据",
            "sInfoFiltered": "(从 _MAX_ 条数据中检索)",
            "sSearch": "搜索",
            "oPaginate": {
                "sFirst": "首页",
                "sPrevious": "前一页",
                "sNext": "后一页",
                "sLast": "尾页"
            },
            "sZeroRecords": "没有检索到数据",
        },
        "fnDrawCallback": function (data) {
            $('.table2_curvaluedate').datetimepicker({
                format: 'yyyy-mm-dd hh:ii:ss',
                autoclose: true,
            });
            if (data.aoData.length > 0) {
                $("#new2").hide();
            } else {
                $("#new2").show();
                $("#save2").hide();
                $("#del2").hide();
                $("#reset2").hide();
                $("#release2").hide();
                $("#gorelease2").hide();
                $("#unrelease2").hide();
                $("#cancel_release2").hide();
            }
        },
        "createdRow": function (row, data, index) {
            if (data.target_warn_range){
                var target_warn_range = parseFloat(data.target_warn_range)/100;
                var curvalue = parseFloat(data.curvalue);
                var yesterday_curvalue = parseFloat(data.yesterday_curvalue);
                if ((curvalue > yesterday_curvalue * (1 + target_warn_range)) || (curvalue < yesterday_curvalue / (1 + target_warn_range))){
                    $('td', row).css("color", "#0000FF");
                }
            }

            if ((data.target_upperlimit && data.curvalue > data.target_upperlimit) || (data.target_lowerlimit && data.curvalue < data.target_lowerlimit)){
                $('td', row).css("color", "#0000FF");
            }

            if (data.releasestate == '0') {
                $("#save2").show();
                $("#del2").show();
                $("#reset2").show();
                $("#release2").show();
                $("#gorelease2").hide();
                $("#unrelease2").show();
                $("#cancel_release2").hide();
            }
            if (data.releasestate == '1') {
                $("#new2").hide();
                $("#save2").hide();
                $("#del2").hide();
                $("#reset2").hide();
                $("#release2").hide();
                $("#unrelease2").hide();
                $("#gorelease2").show();
                $("#cancel_release2").show();
            }


        },
    });
    $('#sample_2 tbody').on('change', 'input[name="table2_todayvalue"]', function () {
        var table = $('#sample_2').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $('#table2_curvalue_' + data.id).val(math.number(math.add(math.bignumber(Number($('#table2_todayvalue_' + data.id).val())), math.bignumber(Number($('#table2_judgevalue_' + data.id).val())))));

        // 累计值 月、季、半年、年
        if (['1', '2', '3', '4'].indexOf(data.target_cumulative) != -1) {
            $.ajax({
                type: "POST",
                url: "../../../ajax_cumulate/",
                data: {
                    cur_value: $('#table2_curvalue_' + data.id).val(),
                    target_id: data.target_id,
                    reporting_date: $('#reporting_date').val(),
                    cycletype: $('#cycletype').val(),
                },
                success: function (ajax_data) {
                    if (ajax_data.status == 1) {
                        $('#table2_cumulativemonth_' + data.id).val(ajax_data.data.cumulativemonth);   // math.js精度计算
                        $('#table2_cumulativequarter_' + data.id).val(ajax_data.data.cumulativequarter);
                        $('#table2_cumulativehalfyear_' + data.id).val(ajax_data.data.cumulativehalfyear);
                        $('#table2_cumulativeyear_' + data.id).val(ajax_data.data.cumulativeyear)
                    } else {
                        alert(ajax_data.data);
                    }
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }
        // 超过上限，低于下限标红
        if ((data.target_upperlimit && Number($('#table2_curvalue_' + data.id).val()) > data.target_upperlimit) || (data.target_lowerlimit && Number($('#table2_curvalue_' + data.id).val()) < data.target_lowerlimit)) {
            $('td', $(this).parents('tr')).css("color", "#0000FF");
        } else {
            $('td', $(this).parents('tr')).css("color", "#000000");
        }
    });

    $('#sample_2 tbody').on('change', 'input[name="table2_judgevalue"]', function () {
        var table = $('#sample_2').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $('#table2_curvalue_' + data.id).val(math.number(math.add(math.bignumber(Number($('#table2_todayvalue_' + data.id).val())), math.bignumber(Number($('#table2_judgevalue_' + data.id).val())))));

        // 累计值 月、季、半年、年
        if (['1', '2', '3', '4'].indexOf(data.target_cumulative) != -1) {
            $.ajax({
                type: "POST",
                url: "../../../ajax_cumulate/",
                data: {
                    cur_value: $('#table2_curvalue_' + data.id).val(),
                    target_id: data.target_id,
                    reporting_date: $('#reporting_date').val(),
                    cycletype: $('#cycletype').val(),
                },
                success: function (ajax_data) {
                    if (ajax_data.status == 1) {
                        $('#table2_cumulativemonth_' + data.id).val(ajax_data.data.cumulativemonth);   // math.js精度计算
                        $('#table2_cumulativequarter_' + data.id).val(ajax_data.data.cumulativequarter);
                        $('#table2_cumulativehalfyear_' + data.id).val(ajax_data.data.cumulativehalfyear);
                        $('#table2_cumulativeyear_' + data.id).val(ajax_data.data.cumulativeyear)
                    } else {
                        alert(ajax_data.data);
                    }
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }
        // 超过上限，低于下限标红
        if ((data.target_upperlimit && Number($('#table2_curvalue_' + data.id).val()) > data.target_upperlimit) || (data.target_lowerlimit && Number($('#table2_curvalue_' + data.id).val()) < data.target_lowerlimit)) {
            $('td', $(this).parents('tr')).css("color", "#0000FF");
        } else {
            $('td', $(this).parents('tr')).css("color", "#000000");
        }
    });

    $('#sample_2 tbody').on('click', 'button#single_reextract', function () {
        if (confirm("是否对当前指标进行重新提取?")) {
            var table = $('#sample_2').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                dataType: "JSON",
                url: "../../../single_reextract/",
                data: {
                    "target_id": data.target_id,
                    "reporting_date": $('#reporting_date').val(),
                },
                success: function (data) {
                    var status = data.status,
                        info = data.info;
                    if (status == 1) {
                        table.ajax.reload();
                    } else {
                        alert(info);
                    }
                }
            })
        }
    });

    // 数据计算 operationtype 17
    $('#sample_3').dataTable({
        "bAutoWidth": true,
        "bSort": true,
        "bProcessing": true,
        "bPaginate": false,
        "bFilter": false,
        "ajax": "../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" +
            $('#reporting_date').val() + "&operationtype=17" + "&funid=" + $('#funid').val(),
        "columns": [
            {"data": "id"},
            {"data": "target_id"},
            {"data": "target_name"},
            {"data": "target_unity"},
            {"data": "target_code"},
            {"data": "target_businesstypename"},
            {"data": "target_unitname"},
            {"data": "todayvalue"},
            {"data": "judgevalue"},
            {"data": "curvalue"},
            {"data": "cumulativemonth"},
            {"data": "cumulativequarter"},
            {"data": "cumulativehalfyear"},
            {"data": "cumulativeyear"},
            {"data": null},
        ],

        "columnDefs": [
            {
                "targets": 0,
                "visible": false,
            },
            {
                "targets": 1,
                "visible": false,
            },
            {
                "targets": 4,
                "visible": false,
            },
            {
                "targets": 5,
                "visible": false,
            },
            {
                "targets": 6,
                "visible": false,
            },
            {
                "targets": -8,
                "mRender": function (data, type, full) {
                    var disabled = "";
                    if (full.releasestate=='1'){
                        disabled = "disabled"
                    }
                    return "<input " + disabled + " style='margin-top:-5px;width:134px;height:24px;' id='table3_todayvalue_" + full.id + "' name='table3_todayvalue'  type='number' value='" + data + "'></input>"
                }
            },
            {
                "targets": -7,
                "mRender": function (data, type, full) {
                    var disabled = "";
                    if (full.releasestate=='1'){
                        disabled = "disabled"
                    }
                    return "<input " + disabled + " style='margin-top:-5px;width:134px;height:24px;' id='table3_judgevalue_" + full.id + "' name='table3_judgevalue'  type='number' value='" + data + "'></input>"

                }
            },
            {
                "targets": -6,
                "mRender": function (data, type, full) {
                    var disabled = "";
                    if (full.releasestate=='1'){
                        disabled = "disabled"
                    }
                    if (full.target_datatype == 'numbervalue') {
                        return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table3_curvalue_" + full.id + "' name='table3_curvalue'  type='number' value='" + data + "'></input>"
                    }
                    if (full.target_datatype == 'date') {
                        return "<input " + disabled + " class='table3_curvaluedate' style='margin-top:-5px;width:134px;height:24px;' id='table3_curvaluedate_" + full.id + "' name='table3_curvaluedate'  type='datetime'  value='" + full.curvaluedate + "'></input>"
                    }
                    if (full.target_datatype == 'text') {
                        return "<input " + disabled + " style='margin-top:-5px;width:134px;height:24px;'  id='table3_curvaluetext_" + full.id + "' name='table3_curvaluetext'  type='text' value='" + full.curvaluetext + "'></input>"
                    }
                }
            },
            {
                "targets": -5,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table3_cumulativemonth_" + full.id + "' name='table3_cumulativemonth'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -4,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table3_cumulativequarter_" + full.id + "' name='table3_cumulativequarter'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -3,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table3_cumulativehalfyear_" + full.id + "' name='table3_cumulativehalfyear'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -2,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:134px;height:24px;' id='table3_cumulativeyear_" + full.id + "' name='table3_cumulativeyear'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -1,
                "data": null,
                "orderable": false,
                "mRender": function (data, type, full) {
                    var disabled = "";
                    if (full.releasestate=='1'){
                        disabled = "disabled"
                    }
                    return "<button " + disabled + " id='edit' title='查看公式' data-toggle='modal'  data-target='#static3'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>" +
                    "<button " + disabled + " id='single_recalculate1' title='重新计算(包括当前指标)' class='btn btn-xs purple-plum' type='button'><i class='fa fa-calculator'></i></button>" +
                    "<button " + disabled + " id='single_recalculate2' title='重新计算(不包括当前指标)' class='btn btn-xs blue-hoki' type='button'><i class='fa fa-calculator'></i></button>"
                }
            }
        ],
        "oLanguage": {
            "sLengthMenu": "每页显示 _MENU_ 条记录",
            "sZeroRecords": "抱歉， 没有找到",
            "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
            "sInfoEmpty": "没有数据",
            "sInfoFiltered": "(从 _MAX_ 条数据中检索)",
            "sSearch": "搜索",
            "oPaginate": {
                "sFirst": "首页",
                "sPrevious": "前一页",
                "sNext": "后一页",
                "sLast": "尾页"
            },
            "sZeroRecords": "没有检索到数据",
        },
        "fnDrawCallback": function (data) {
            $('.table3_curvaluedate').datetimepicker({
                format: 'yyyy-mm-dd hh:ii:ss',
                autoclose: true,
            });
            if (data.aoData.length > 0) {
                $("#new3").hide();
            } else {
                $("#new3").show();
                $("#save3").hide();
                $("#del3").hide();
                $("#reset3").hide();
                $("#release3").hide();
                $("#gorelease3").hide();
                $("#unrelease3").hide();
                $("#cancel_release3").hide();
            }
        },
        "createdRow": function (row, data, index) {
            if (data.target_warn_range){
                var target_warn_range = parseFloat(data.target_warn_range)/100;
                var curvalue = parseFloat(data.curvalue);
                var yesterday_curvalue = parseFloat(data.yesterday_curvalue);
                if ((curvalue > yesterday_curvalue * (1 + target_warn_range)) || (curvalue < yesterday_curvalue / (1 + target_warn_range))){
                    $('td', row).css("color", "#0000FF");
                }
            }
            if ((data.target_upperlimit && data.curvalue > data.target_upperlimit) || (data.target_lowerlimit && data.curvalue < data.target_lowerlimit)){
                $('td', row).css("color", "#0000FF");
            }

            if (data.releasestate == '0') {
                $("#save3").show();
                $("#del3").show();
                $("#reset3").show();
                $("#release3").show();
                $("#gorelease3").hide();
                $("#unrelease3").show();
                $("#cancel_release3").hide();
            }
            if (data.releasestate == '1') {
                $("#new3").hide();
                $("#save3").hide();
                $("#del3").hide();
                $("#reset3").hide();
                $("#release3").hide();
                $("#unrelease3").hide();
                $("#gorelease3").show();
                $("#cancel_release3").show();
            }

        },

    });
    $('#sample_3 tbody').on('change', 'input[name="table3_todayvalue"]', function () {
        var table = $('#sample_3').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $('#table3_curvalue_' + data.id).val(math.number(math.add(math.bignumber(Number($('#table3_todayvalue_' + data.id).val())), math.bignumber(Number($('#table3_judgevalue_' + data.id).val())))));


        // 累计值 月、季、半年、年
        if (['1', '2', '3', '4'].indexOf(data.target_cumulative) != -1) {
            $.ajax({
                type: "POST",
                url: "../../../ajax_cumulate/",
                data: {
                    cur_value: $('#table3_curvalue_' + data.id).val(),
                    target_id: data.target_id,
                    reporting_date: $('#reporting_date').val(),
                    cycletype: $('#cycletype').val(),
                },
                success: function (ajax_data) {
                    if (ajax_data.status == 1) {
                        $('#table3_cumulativemonth_' + data.id).val(ajax_data.data.cumulativemonth);   // math.js精度计算
                        $('#table3_cumulativequarter_' + data.id).val(ajax_data.data.cumulativequarter);
                        $('#table3_cumulativehalfyear_' + data.id).val(ajax_data.data.cumulativehalfyear);
                        $('#table3_cumulativeyear_' + data.id).val(ajax_data.data.cumulativeyear)
                    } else {
                        alert(ajax_data.data);
                    }
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }

        // 超过上限，低于下限标红
        if ((data.target_upperlimit && Number($('#table3_curvalue_' + data.id).val()) > data.target_upperlimit) || (data.target_lowerlimit && Number($('#table3_curvalue_' + data.id).val()) < data.target_lowerlimit)) {
            $('td', $(this).parents('tr')).css("color", "#0000FF");
        } else {
            $('td', $(this).parents('tr')).css("color", "#000000");
        }
    });

    $('#sample_3 tbody').on('change', 'input[name="table3_judgevalue"]', function () {
        var table = $('#sample_3').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $('#table3_curvalue_' + data.id).val(math.number(math.add(math.bignumber(Number($('#table3_todayvalue_' + data.id).val())), math.bignumber(Number($('#table3_judgevalue_' + data.id).val())))));


        // 累计值 月、季、半年、年
        if (['1', '2', '3', '4'].indexOf(data.target_cumulative) != -1) {
            $.ajax({
                type: "POST",
                url: "../../../ajax_cumulate/",
                data: {
                    cur_value: $('#table3_curvalue_' + data.id).val(),
                    target_id: data.target_id,
                    reporting_date: $('#reporting_date').val(),
                    cycletype: $('#cycletype').val(),
                },
                success: function (ajax_data) {
                    if (ajax_data.status == 1) {
                        $('#table3_cumulativemonth_' + data.id).val(ajax_data.data.cumulativemonth);   // math.js精度计算
                        $('#table3_cumulativequarter_' + data.id).val(ajax_data.data.cumulativequarter);
                        $('#table3_cumulativehalfyear_' + data.id).val(ajax_data.data.cumulativehalfyear);
                        $('#table3_cumulativeyear_' + data.id).val(ajax_data.data.cumulativeyear)
                    } else {
                        alert(ajax_data.data);
                    }
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }

        // 超过上限，低于下限标红
        if ((data.target_upperlimit && Number($('#table3_curvalue_' + data.id).val()) > data.target_upperlimit) || (data.target_lowerlimit && Number($('#table3_curvalue_' + data.id).val()) < data.target_lowerlimit)) {
            $('td', $(this).parents('tr')).css("color", "#0000FF");
        } else {
            $('td', $(this).parents('tr')).css("color", "#000000");
        }
    });


    $('#sample_3 tbody').on('click', 'button#edit', function () {
        $("#formuladiv").empty();
        var table = $('#sample_3').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $.getformula(data.id.toString());
    });

    $('#sample_3 tbody').on('click', 'button#single_recalculate1', function () {
        if (confirm("是否对当前指标进行重新计算?")) {
            customModal.show();
            var table = $('#sample_3').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                dataType: "JSON",
                url: "../../../single_recalculate/",
                data: {
                    "target_id": data.target_id,
                    "reporting_date": $('#reporting_date').val(),
                    "recalculate_type": "1",
                },
                success: function (data) {
                    if (data['status'] == 1) {
                        table.ajax.reload();
                    } else {
                        alert(data['info']);
                    }
                    customModal.hide();
                    alert(data['info']);
                },
                error: function (e) {
                    alert("计算失败，请于管理员联系。");
                    // 隐藏滚动条
                    customModal.hide();
                }
            })
        }
    });
    $('#sample_3 tbody').on('click', 'button#single_recalculate2', function () {
        if (confirm("是否对当前指标进行重新计算?")) {
            customModal.show();
            var table = $('#sample_3').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                dataType: "JSON",
                url: "../../../single_recalculate/",
                data: {
                    "target_id": data.target_id,
                    "reporting_date": $('#reporting_date').val(),
                    "recalculate_type": "0",
                },
                success: function (data) {
                    if (data['status'] == 1) {
                        table.ajax.reload();
                    } else {
                        alert(data['info']);
                    }
                    customModal.hide();
                    alert(data['info']);
                },
                error: function (e) {
                    alert("计算失败，请于管理员联系。");
                    // 隐藏滚动条
                    customModal.hide();
                }
            })
        }
    });

    $.formulabtnclick = function () {
        $(".formulabtn").unbind("click");
        $(".formulabtn").click(function () {
            $(this).parent().nextAll().remove();
            $.getformula(this.id.replace("formulabtn_", ""));
        })
    }
    $.getformula = function (btnid) {
        $.ajax({
            type: "POST",
            url: "../../../reporting_formulacalculate/",
            data:
                {
                    id: btnid,
                    cycletype: $('#cycletype').val(),
                    reporting_date: $('#reporting_date').val(),
                },
            success: function (data) {
                $("#formuladiv").append(data);
                $.formulabtnclick();
            },
            error: function (e) {
                alert("公式解析失败，请于管理员联系。");
            }
        });

        //var aa = (parseInt(btnid) +1).toString()
        //$("#formuladiv").append("<div style=\"font-size:18px\"><span style=\"font-size:18px\"  class=\"label label-primary\">#1机组发电量" + aa + "</span><button id='formulabtn_" + aa + "' style=\"font-size:18px;color: #0a6aa1;padding-top:-5px\" type=\"button\" class=\"btn btn-link formulabtn\"><#1_发电量:当前值:当天>221.3</button> + <发电量:当前值:当天>+1+#1机组发电量</span> 123.2<#1_发电量:当前值:当天>+221.3<发电量:当前值:当天>+1=31.12<br><br></div>")
        //$.formulabtnclick();
    }

    // 数据查询
    $('#sample_4').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "bPaginate": false,
        "bFilter": false,
        "ajax": "../../../reporting_search_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val() + "&searchapp=" + $('#searchapp').val(),
        "columns": [
            {"data": "target_name"},
            {"data": "zerodata"},
            {"data": "twentyfourdata"},
            {"data": "todayvalue"},
            {"data": "judgevalue"},
            {"data": "curvalue"},
            {"data": "cumulativemonth"},
            {"data": "cumulativequarter"},
            {"data": "cumulativehalfyear"},
            {"data": "cumulativeyear"},
        ],
        "createdRow": function (row, data, index) {
            if (data.curvalue == "" || data.releasestate == "0") {
                $('td', row).css("color", "#FF0000");
            } else if ((data.target_upperlimit && data.curvalue > data.target_upperlimit) || (data.target_lowerlimit && data.curvalue < data.target_lowerlimit)) {
                $('td', row).css("color", "#0000FF");
            }
        },


        "oLanguage": {
            "sLengthMenu": "每页显示 _MENU_ 条记录",
            "sZeroRecords": "抱歉， 没有找到",
            "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
            "sInfoEmpty": "没有数据",
            "sInfoFiltered": "(从 _MAX_ 条数据中检索)",
            "sSearch": "搜索",
            "oPaginate": {
                "sFirst": "首页",
                "sPrevious": "前一页",
                "sNext": "后一页",
                "sLast": "尾页"
            },
            "sZeroRecords": "没有检索到数据",
        },
    });

    // 电表走字 operationtype 1
    $('#sample_5').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "bPaginate": false,
        "bFilter": false,
        "ajax": "../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
            "&reporting_date=" + $('#reporting_date').val() + "&operationtype=1" +
            "&funid=" + $('#funid').val(),
        "columns": [
            {"data": "id"},
            {"data": "target_name"},
            {"data": "target_code"},
            {"data": "target_unitname"},
            {"data": "target_cumulative"},
            {"data": "zerodata"},
            {"data": "twentyfourdata"},
            {"data": "metervalue"},
            {"data": "target_magnification"},
            {"data": "todayvalue"},
            {"data": "judgevalue"},
            {"data": "curvalue"},
            {"data": "cumulativemonth"},
            {"data": "cumulativequarter"},
            {"data": "cumulativehalfyear"},
            {"data": "cumulativeyear"},
            {"data": null},
        ],

        "columnDefs": [
            {
                "targets": 0,
                "visible": false,
            },
            {
                "targets": -15,
                "visible": false,
            },
            {
                "targets": -14,
                "visible": false,
            },
            {
                "targets": -13,
                "visible": false,
            },
            {
                "targets": -12,
                "mRender": function (data, type, full) {
                    var disabled = "";
                    if (full.releasestate=='1' || full.meterchangedata_id){
                        disabled = "disabled"
                    }
                    return "<input " + disabled + "   style='margin-top:-5px;width:90px;height:24px;' id='table5_zerodata_" + full.id + "' name='table5_zerodata'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -11,
                "mRender": function (data, type, full) {
                    var disabled = "";
                    if (full.releasestate=='1' || full.meterchangedata_id){
                        disabled = "disabled"
                    }
                    return "<input " + disabled + "  style='margin-top:-5px;width:90px;height:24px;'id='table5_twentyfourdata_" + full.id + "' name='table5_twentyfourdata'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -10,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:70px;height:24px;' id='table5_metervalue_" + full.id + "' name='table5_metervalue'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -9,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:70px;height:24px;' id='table5_magnification_" + full.id + "' name='table5_magnification'  type='text' value='" + full.target_magnification + "'></input>"
                }
            },
            {
                "targets": -8,
                "mRender": function (data, type, full) {
                    var disabled = "";
                    if (full.releasestate=='1' || full.meterchangedata_id){
                        disabled = "disabled"
                    }
                    return "<input " + disabled + " style='margin-top:-5px;width:80px;height:24px;' id='table5_todayvalue_" + full.id + "' name='table5_todayvalue'  type='number' value='" + data + "'></input>"
                }
            },
            {
                "targets": -7,
                "mRender": function (data, type, full) {
                    var disabled = "";
                    if (full.releasestate=='1' || full.meterchangedata_id){
                        disabled = "disabled"
                    }
                    return "<input " + disabled + " style='margin-top:-5px;width:80px;height:24px;' id='table5_judgevalue_" + full.id + "' name='table5_judgevalue'  type='number' value='" + data + "'></input>"

                }
            },
            {
                "targets": -6,
                "mRender": function (data, type, full) {
                    var disabled = "";
                    if (full.releasestate=='1' || full.meterchangedata_id){
                        disabled = "disabled"
                    }
                    if (full.target_datatype == 'numbervalue') {
                        return "<input disabled style='margin-top:-5px;width:100px;height:24px;' id='table5_curvalue_" + full.id + "' name='table5_curvalue'  type='number' value='" + data + "'></input>"
                    }
                    if (full.target_datatype == 'date') {
                        return "<input " + disabled + "   class='table5_curvaluedate' style='margin-top:-5px;width:100px;height:24px;' id='table5_curvaluedate_" + full.id + "' name='table5_curvaluedate'  type='datetime'  value='" + full.curvaluedate + "'></input>"
                    }
                    if (full.target_datatype == 'text') {
                        return "<input " + disabled + "   style='margin-top:-5px;width:100px;height:24px;' id='table5_curvaluetext_" + full.id + "' name='table5_curvaluetext'  type='text' value='" + full.curvaluetext + "'></input>"
                    }
                }
            },
            {
                "targets": -5,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:100px;height:24px;' id='table5_cumulativemonth_" + full.id + "' name='table5_cumulativemonth'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -4,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:100px;height:24px;' id='table5_cumulativequarter_" + full.id + "' name='table5_cumulativequarter'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -3,
                "mRender": function (data, type, full) {
                    return "<input disabled style='margin-top:-5px;width:100px;height:24px;' id='table5_cumulativehalfyear_" + full.id + "' name='table5_cumulativehalfyear'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -2,
                "mRender": function (data, type, full) {
                    return "<input disabled  style='margin-top:-5px;width:100px;height:24px;'id='table5_cumulativeyear_" + full.id + "' name='table5_cumulativeyear'  type='text' value='" + data + "'></input>"
                }
            },
            {
                "targets": -1,
                "data": null,
                "width": "10px",
                "mRender": function (data, type, full) {
                    var disabled = "";
                    var class_color = "class='btn btn-xs btn-primary'";
                    if (full.releasestate=='1'){
                        disabled = "disabled"
                    }
                    if (full.meterchangedata_id){
                        class_color = "class='btn btn-xs btn-warning'";
                    }
                    return "<button " + disabled + " id='edit' title='换表' data-toggle='modal'  data-target='#static5' " + class_color + " type='button'><i class='fa fa-edit'></i></button>"
                }
            },
        ],
        "oLanguage": {
            "sLengthMenu": "每页显示 _MENU_ 条记录",
            "sZeroRecords": "抱歉， 没有找到",
            "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
            "sInfoEmpty": "没有数据",
            "sInfoFiltered": "(从 _MAX_ 条数据中检索)",
            "sSearch": "搜索",
            "oPaginate": {
                "sFirst": "首页",
                "sPrevious": "前一页",
                "sNext": "后一页",
                "sLast": "尾页"
            },
            "sZeroRecords": "没有检索到数据",
        },
        "fnDrawCallback": function (data) {
            $('.table5_curvaluedate').datetimepicker({
                format: 'yyyy-mm-dd hh:ii:ss',
                autoclose: true,
            });
            if (data.aoData.length > 0) {
                $("#new5").hide();
            } else {
                $("#new5").show();
                $("#save5").hide();
                $("#del5").hide();
                $("#release5").hide();
                $("#gorelease5").hide();
                $("#unrelease5").hide();
                $("#cancel_release5").hide();
            }
        },
        "createdRow": function (row, data, index) {
            if (data.target_warn_range){
                var target_warn_range = parseFloat(data.target_warn_range)/100;
                var curvalue = parseFloat(data.curvalue);
                var yesterday_curvalue = parseFloat(data.yesterday_curvalue);
                if ((curvalue > yesterday_curvalue * (1 + target_warn_range)) || (curvalue < yesterday_curvalue / (1 + target_warn_range))){
                    $('td', row).css("color", "#0000FF");
                }
            }
            if ((data.target_upperlimit && data.curvalue > data.target_upperlimit) || (data.target_lowerlimit && data.curvalue < data.target_lowerlimit)){
                $('td', row).css("color", "#0000FF");
            }
            if ((data.zerodata == data.twentyfourdata)){
                $('td', row).css("color", "#FF0000");
            }

            if (data.releasestate == '0') {
                $("#save5").show();
                $("#del5").show();
                $("#release5").show();
                $("#gorelease5").hide();
                $("#unrelease5").show();
                $("#cancel_release5").hide();
            }
            if (data.releasestate == '1') {
                $("#new5").hide();
                $("#save5").hide();
                $("#del5").hide();
                $("#release5").hide();
                $("#unrelease5").hide();
                $("#gorelease5").show();
                $("#cancel_release5").show();
            }
        },

    });

    // 0点走字、24点走字、当前值变动，重新计算累积值
    $('#sample_5 tbody').on('change', 'input[name="table5_zerodata"]', function () {
        var table = $('#sample_5').DataTable();
        var data = table.row($(this).parents('tr')).data();

        $('#table5_metervalue_' + data.id).val(math.number(math.subtract(math.bignumber(Number($('#table5_twentyfourdata_' + data.id).val())), math.bignumber(Number($('#table5_zerodata_' + data.id).val())))));
        var curValue = math.number(math.multiply(math.bignumber(Number($('#table5_metervalue_' + data.id).val())), math.bignumber(Number(data.target_magnification))));
        $('#table5_todayvalue_' + data.id).val(curValue);
        $('#table5_curvalue_' + data.id).val(math.number(math.add(math.bignumber(Number($('#table5_todayvalue_' + data.id).val())), math.bignumber(Number($('#table5_judgevalue_' + data.id).val())))));


        // 累计值 月、季、半年、年
        if (['1', '2', '3', '4'].indexOf(data.target_cumulative) != -1) {
            $.ajax({
                type: "POST",
                url: "../../../ajax_cumulate/",
                data: {
                    cur_value: curValue,
                    target_id: data.target_id,
                    reporting_date: $('#reporting_date').val(),
                    cycletype: $('#cycletype').val(),
                },
                success: function (ajax_data) {
                    if (ajax_data.status == 1) {
                        $('#table5_cumulativemonth_' + data.id).val(ajax_data.data.cumulativemonth);   // math.js精度计算
                        $('#table5_cumulativequarter_' + data.id).val(ajax_data.data.cumulativequarter);
                        $('#table5_cumulativehalfyear_' + data.id).val(ajax_data.data.cumulativehalfyear);
                        $('#table5_cumulativeyear_' + data.id).val(ajax_data.data.cumulativeyear)
                    } else {
                        alert(ajax_data.data);
                    }
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }
        // 超过上限，低于下限标红
        if (Number($('#table5_zerodata_' + data.id).val()) == Number($('#table5_twentyfourdata_' + data.id).val())) {
            $('td', $(this).parents('tr')).css("color", "#FF0000");
        } else if ((data.target_upperlimit && Number($('#table5_curvalue_' + data.id).val()) > data.target_upperlimit) || (data.target_lowerlimit && dNumber($('#table5_curvalue_' + data.id).val()) < data.target_lowerlimit)) {
            $('td', $(this).parents('tr')).css("color", "#0000FF");
        } else {
            $('td', $(this).parents('tr')).css("color", "#000000");
        }


    });
    $('#sample_5 tbody').on('change', 'input[name="table5_twentyfourdata"]', function () {
        var table = $('#sample_5').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $('#table5_metervalue_' + data.id).val(math.number(math.subtract(math.bignumber(Number($('#table5_twentyfourdata_' + data.id).val())), math.bignumber(Number($('#table5_zerodata_' + data.id).val())))));
        var curValue = math.number(math.multiply(math.bignumber(Number($('#table5_metervalue_' + data.id).val())), math.bignumber(Number(data.target_magnification))));
        $('#table5_todayvalue_' + data.id).val(curValue);
        $('#table5_curvalue_' + data.id).val(math.number(math.add(math.bignumber(Number($('#table5_todayvalue_' + data.id).val())), math.bignumber(Number($('#table5_judgevalue_' + data.id).val())))));

        // 累计值 月、季、半年、年
        if (['1', '2', '3', '4'].indexOf(data.target_cumulative) != -1) {
            $.ajax({
                type: "POST",
                url: "../../../ajax_cumulate/",
                data: {
                    cur_value: curValue,
                    target_id: data.target_id,
                    reporting_date: $('#reporting_date').val(),
                    cycletype: $('#cycletype').val(),
                },
                success: function (ajax_data) {
                    if (ajax_data.status == 1) {
                        $('#table5_cumulativemonth_' + data.id).val(ajax_data.data.cumulativemonth);   // math.js精度计算
                        $('#table5_cumulativequarter_' + data.id).val(ajax_data.data.cumulativequarter);
                        $('#table5_cumulativehalfyear_' + data.id).val(ajax_data.data.cumulativehalfyear);
                        $('#table5_cumulativeyear_' + data.id).val(ajax_data.data.cumulativeyear)
                    } else {
                        alert(ajax_data.data);
                    }
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }
        // 超过上限，低于下限标红
        if (Number($('#table5_zerodata_' + data.id).val()) == Number($('#table5_twentyfourdata_' + data.id).val())) {
            $('td', $(this).parents('tr')).css("color", "#FF0000");
        } else if ((data.target_upperlimit && (Number($('#table5_curvalue_' + data.id).val()) > data.target_upperlimit)) || (data.target_lowerlimit && Number($('#table5_curvalue_' + data.id).val()) < data.target_lowerlimit)) {
            $('td', $(this).parents('tr')).css("color", "#0000FF");
        } else {
            $('td', $(this).parents('tr')).css("color", "#000000");
        }
    });
    $('#sample_5 tbody').on('change', 'input[name="table5_todayvalue"]', function () {
        var table = $('#sample_5').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $('#table5_curvalue_' + data.id).val(math.number(math.add(math.bignumber(Number($('#table5_todayvalue_' + data.id).val())), math.bignumber(Number($('#table5_judgevalue_' + data.id).val())))));

        // 累计值 月、季、半年、年
        if (['1', '2', '3', '4'].indexOf(data.target_cumulative) != -1) {
            $.ajax({
                type: "POST",
                url: "../../../ajax_cumulate/",
                data: {
                    cur_value: $('#table5_curvalue_' + data.id).val(),
                    target_id: data.target_id,
                    reporting_date: $('#reporting_date').val(),
                    cycletype: $('#cycletype').val(),
                },
                success: function (ajax_data) {
                    if (ajax_data.status == 1) {
                        $('#table5_cumulativemonth_' + data.id).val(ajax_data.data.cumulativemonth);   // math.js精度计算
                        $('#table5_cumulativequarter_' + data.id).val(ajax_data.data.cumulativequarter);
                        $('#table5_cumulativehalfyear_' + data.id).val(ajax_data.data.cumulativehalfyear);
                        $('#table5_cumulativeyear_' + data.id).val(ajax_data.data.cumulativeyear)
                    } else {
                        alert(ajax_data.data);
                    }
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }
    });


    $('#sample_5 tbody').on('change', 'input[name="table5_judgevalue"]', function () {
        var table = $('#sample_5').DataTable();
        var data = table.row($(this).parents('tr')).data();
        // 累计值 月、季、半年、年
        if (['1', '2', '3', '4'].indexOf(data.target_cumulative) != -1) {
            $('#table5_curvalue_' + data.id).val(math.number(math.add(math.bignumber(Number($('#table5_todayvalue_' + data.id).val())), math.bignumber(Number($('#table5_judgevalue_' + data.id).val())))));

            $.ajax({
                type: "POST",
                url: "../../../ajax_cumulate/",
                data: {
                    cur_value: $('#table5_curvalue_' + data.id).val(),
                    target_id: data.target_id,
                    reporting_date: $('#reporting_date').val(),
                    cycletype: $('#cycletype').val(),
                },
                success: function (ajax_data) {
                    if (ajax_data.status == 1) {
                        $('#table5_cumulativemonth_' + data.id).val(ajax_data.data.cumulativemonth);   // math.js精度计算
                        $('#table5_cumulativequarter_' + data.id).val(ajax_data.data.cumulativequarter);
                        $('#table5_cumulativehalfyear_' + data.id).val(ajax_data.data.cumulativehalfyear);
                        $('#table5_cumulativeyear_' + data.id).val(ajax_data.data.cumulativeyear)
                    } else {
                        alert(ajax_data.data);
                    }
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }
    });




    // 电表走字换表
    $('#sample_5 tbody').on('click', 'button#edit', function () {
        var data5 = $('#sample_5').DataTable().data();
        var table = $('#sample_5').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $.each(data5, function (i, item) {
            if (item.id == data.id) {
                data = item;
                return false
            }
        })
        $("#id").val(data.id);
        $("#target_id").val(data.target_id);
        $("#cumulative").val(data.target_cumulative);
        $("#todayvalue").val(data.todayvalue);
        $("#judgevalue").val(data.judgevalue);

        $("#curvalue").val(data.curvalue);
        $("#cumulativemonth").val(data.cumulativemonth);
        $("#cumulativequarter").val(data.cumulativequarter);
        $("#cumulativehalfyear").val(data.cumulativehalfyear);
        $("#cumulativeyear").val(data.cumulativehalfyear);


        $("#meterchangedata_id").val(data.meterchangedata_id);
        if ($("#meterchangedata_id").val()) {
            $("#oldtable_zerodata").val(data.oldtable_zerodata);
            $("#oldtable_twentyfourdata").val(data.oldtable_twentyfourdata);
            $("#oldtable_value").val(data.oldtable_value);
            $("#oldtable_magnification").val(data.oldtable_magnification);
            $("#oldtable_finalvalue").val(data.oldtable_finalvalue);

            $("#newtable_zerodata").val(data.newtable_zerodata);
            $("#newtable_twentyfourdata").val(data.newtable_twentyfourdata);
            $("#newtable_value").val(data.newtable_value);
            $("#newtable_magnification").val(data.newtable_magnification);
            $("#newtable_finalvalue").val(data.newtable_finalvalue);
            $("#finalvalue").val(data.finalvalue);
        } else {
            $("#oldtable_zerodata").val($('#table5_zerodata_' + data.id).val());
            $("#oldtable_twentyfourdata").val($('#table5_zerodata_' + data.id).val());
            $('#oldtable_value').val(math.number(math.subtract(math.bignumber(Number($("#oldtable_twentyfourdata").val())), math.bignumber(Number($("#oldtable_zerodata").val())))));
            $("#oldtable_magnification").val($('#table5_magnification_' + data.id).val());
            $("#oldtable_finalvalue").val(math.number(math.multiply(math.bignumber(Number($("#oldtable_value").val())), math.bignumber(Number(data.target_magnification)))));

            $("#newtable_zerodata").val($('#table5_zerodata_' + data.id).val());
            $("#newtable_twentyfourdata").val($('#table5_twentyfourdata_' + data.id).val());
            $('#newtable_value').val(math.number(math.subtract(math.bignumber(Number($("#newtable_twentyfourdata").val())), math.bignumber(Number($("#newtable_zerodata").val())))));
            $("#newtable_magnification").val($('#table5_magnification_' + data.id).val());
            $('#newtable_finalvalue').val($('#table5_curvalue_' + data.id).val());
            $("#finalvalue").val(math.number(math.add(math.bignumber(Number($("#oldtable_finalvalue").val())), math.bignumber(Number($("#newtable_finalvalue").val())))));
        }
    });

    $("#oldtable_zerodata").bind('input propertychange', function () {
        $('#oldtable_value').val(math.number(math.subtract(math.bignumber(Number($("#oldtable_twentyfourdata").val())), math.bignumber(Number($("#oldtable_zerodata").val())))));
        $("#oldtable_finalvalue").val(math.number(math.multiply(math.bignumber(Number($("#oldtable_value").val())), math.bignumber(Number($("#oldtable_magnification").val())))));
        $("#finalvalue").val(math.number(math.add(math.bignumber(Number($("#oldtable_finalvalue").val())), math.bignumber(Number($("#newtable_finalvalue").val())))))
    });
    $("#newtable_zerodata").bind('input propertychange', function () {
        $('#newtable_value').val(math.number(math.subtract(math.bignumber(Number($("#newtable_twentyfourdata").val())), math.bignumber(Number($("#newtable_zerodata").val())))));
        $('#newtable_finalvalue').val(math.number(math.multiply(math.bignumber(Number($("#newtable_value").val())), math.bignumber(Number($("#newtable_magnification").val())))));
        $("#finalvalue").val(math.number(math.add(math.bignumber(Number($("#oldtable_finalvalue").val())), math.bignumber(Number($("#newtable_finalvalue").val())))))
    });
    $("#oldtable_twentyfourdata").bind('input propertychange', function () {
        $('#oldtable_value').val(math.number(math.subtract(math.bignumber(Number($("#oldtable_twentyfourdata").val())), math.bignumber(Number($("#oldtable_zerodata").val())))));
        $("#oldtable_finalvalue").val(math.number(math.multiply(math.bignumber(Number($("#oldtable_value").val())), math.bignumber(Number($("#oldtable_magnification").val())))));
        $("#finalvalue").val(math.number(math.add(math.bignumber(Number($("#oldtable_finalvalue").val())), math.bignumber(Number($("#newtable_finalvalue").val())))))
    });
    $("#newtable_twentyfourdata").bind('input propertychange', function () {
        $('#newtable_value').val(math.number(math.subtract(math.bignumber(Number($("#newtable_twentyfourdata").val())), math.bignumber(Number($("#newtable_zerodata").val())))));
        $('#newtable_finalvalue').val(math.number(math.multiply(math.bignumber(Number($("#newtable_value").val())), math.bignumber(Number($("#newtable_magnification").val())))));
        $("#finalvalue").val(math.number(math.add(math.bignumber(Number($("#oldtable_finalvalue").val())), math.bignumber(Number($("#newtable_finalvalue").val())))))
    });
    $("#newtable_magnification").bind('input propertychange', function () {
        $('#newtable_finalvalue').val(math.number(math.multiply(math.bignumber(Number($("#newtable_value").val())), math.bignumber(Number($("#newtable_magnification").val())))));
        $("#finalvalue").val(math.number(math.add(math.bignumber(Number($("#oldtable_finalvalue").val())), math.bignumber(Number($("#newtable_finalvalue").val())))))

    });

    $('#confirm').click(function () {
        if (confirm("换表后将新增换表记录，并修改此表计倍率，请谨慎操作！！！\r是否继续换表操作？")) {
            var id = $("#id").val();
            var target_id = $("#target_id").val();
            var cumulative = $("#cumulative").val();
            var curvalue = $("#finalvalue").val();

            $("#table5_magnification_" + id).val($("#newtable_magnification").val());
            $("#table5_todayvalue_" + id).val(curvalue);
            $("#table5_curvalue_" + id).val(curvalue);
            $("#table5_zerodata_" + id).val($("#oldtable_zerodata").val());
            $("#table5_twentyfourdata_" + id).val($("#newtable_twentyfourdata").val());
            $("#table5_metervalue_" + id).val(math.number(math.subtract(math.bignumber(Number($("#table5_twentyfourdata_" + id).val())), math.bignumber(Number($("#table5_zerodata_" + id).val())))));
            $("#table5_curvalue_" + id).attr("disabled", "disabled");
            $("#table5_twentyfourdata_" + id).attr("disabled", "disabled");
            $("#table5_zerodata_" + id).attr("disabled", "disabled");

            // 累计值 月、季、半年、年
            if (['1', '2', '3', '4'].indexOf(cumulative) != -1) {
                $.ajax({
                    type: "POST",
                    url: "../../../ajax_cumulate/",
                    data: {
                        cur_value: curvalue,
                        target_id: target_id,
                        reporting_date: $('#reporting_date').val(),
                        cycletype: $('#cycletype').val(),
                    },
                    success: function (ajax_data) {
                        if (ajax_data.status == 1) {
                            var newcumulativemonth = ajax_data.data.cumulativemonth;
                            var newcumulativequarter = ajax_data.data.cumulativequarter;
                            var newcumulativehalfyear = ajax_data.data.cumulativehalfyear;
                            var newcumulativeyear = ajax_data.data.cumulativeyear;
                            $('#table5_cumulativemonth_' + id).val(newcumulativemonth);   // math.js精度计算
                            $('#table5_cumulativequarter_' + id).val(newcumulativequarter);
                            $('#table5_cumulativehalfyear_' + id).val(newcumulativehalfyear);
                            $('#table5_cumulativeyear_' + id).val(newcumulativeyear);

                            var data5 = $('#sample_5').DataTable().data();
                            $.each(data5, function (i, item) {
                                if (item.id == id) {
                                    data5[i].meterchangedata_id = "0";
                                    data5[i].oldtable_zerodata = $("#oldtable_zerodata").val();
                                    data5[i].oldtable_twentyfourdata = $("#oldtable_twentyfourdata").val();
                                    data5[i].oldtable_value = $("#oldtable_value").val();
                                    data5[i].oldtable_magnification = $("#oldtable_magnification").val();
                                    data5[i].oldtable_finalvalue = $("#oldtable_finalvalue").val();
                                    data5[i].newtable_zerodata = $("#newtable_zerodata").val();
                                    data5[i].newtable_twentyfourdata = $("#newtable_twentyfourdata").val();
                                    data5[i].newtable_value = $("#newtable_value").val();
                                    data5[i].newtable_magnification = $("#newtable_magnification").val();
                                    data5[i].newtable_finalvalue = $("#newtable_finalvalue").val();
                                    data5[i].finalvalue = $("#finalvalue").val();
                                    data5[i].cumulativemonth = newcumulativequarter;
                                    data5[i].cumulativequarter = newcumulativequarter;
                                    data5[i].cumulativehalfyear = newcumulativehalfyear;
                                    data5[i].cumulativeyear = newcumulativeyear;
                                    if (Number($('#table5_zerodata_' + id).val()) == Number($('#table5_twentyfourdata_' + id).val())) {
                                        $('#table5_zerodata_' + id).parent().parent().children().css("color", "#FF0000")
                                    } else if ((data5[i].target_upperlimit && (Number($('#table5_curvalue_' + id).val()) > data5[i].target_upperlimit)) || (data5[i].target_lowerlimit && Number($('#table5_curvalue_' + id).val()) < data5[i].target_lowerlimit)) {
                                        $('#table5_zerodata_' + id).parent().parent().children().css("color", "#0000FF")
                                    } else {
                                        $('#table5_zerodata_' + id).parent().parent().children().css("color", "#000000")
                                    }
                                    return false
                                }
                            })
                        } else {
                            alert(ajax_data.data);
                        }
                    },
                    error: function (e) {
                        alert("页面出现错误，请于管理员联系。");
                    }
                });
            }
            $('#static5').modal('hide');
        } else {
            $('#static5').modal('hide');
        }
    });

    $('#reporting_date').change(function () {
        var table1 = $('#sample_1').DataTable();
        table1.ajax.url("../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
            "&reporting_date=" + $('#reporting_date').val() + "&operationtype=15" +
            "&funid=" + $('#funid').val()).load();
        var table2 = $('#sample_2').DataTable();
        table2.ajax.url("../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
            "&reporting_date=" + $('#reporting_date').val() + "&operationtype=16" +
            "&funid=" + $('#funid').val()).load();
        var table3 = $('#sample_3').DataTable();
        table3.ajax.url("../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
            "&reporting_date=" + $('#reporting_date').val() + "&operationtype=17" +
            "&funid=" + $('#funid').val()).load();
        var table4 = $('#sample_4').DataTable();
        table4.ajax.url("../../../reporting_search_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val() + "&searchapp=" + $('#searchapp').val()).load();
        var table5 = $('#sample_5').DataTable();
        table5.ajax.url("../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
            "&reporting_date=" + $('#reporting_date').val() + "&operationtype=1" +
            "&funid=" + $('#funid').val()).load();

    });
    $('#searchapp').change(function () {
        var app_id = $(this).val();
        if (app_id) {
            $('#works').empty();
            // 应用对应的works
            var pre_work_option = '<option selected value="">全部</option>';
            for (var i = 0; i < search_app_list.length; i++) {
                if (search_app_list[i].id == app_id) {
                    for (var j = 0; j < search_app_list[i].works.length; j++) {
                        pre_work_option += '<option value="' + search_app_list[i].works[j].id + '">' + search_app_list[i].works[j].name + '</option>';
                    }
                    break;
                }
            }
            $('#works').append(pre_work_option);
        } else {
            workSelectInit();
        }

        var table4 = $('#sample_4').DataTable();
        table4.ajax.url("../../../reporting_search_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
            "&reporting_date=" + $('#reporting_date').val() + "&searchapp=" + $('#searchapp').val() +
            "&works=" + $('#works').val()
        ).load();
    });

    $('#works').change(function () {
        var table4 = $('#sample_4').DataTable();
        table4.ajax.url("../../../reporting_search_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
            "&reporting_date=" + $('#reporting_date').val() + "&searchapp=" + $('#searchapp').val() +
            "&works=" + $('#works').val()
        ).load();
    });

    /*
        10 日报
        11 月报
        12 季报
        13 半年报
        14 年报
    */
    if ($('#cycletype').val() == "10") {
        $('#reporting_date').datetimepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            startView: 2,
            minView: 2,
        });
    }
    if ($('#cycletype').val() == "11") {
        $('#reporting_date').datetimepicker({
            format: 'yyyy-mm',
            autoclose: true,
            startView: 3,
            minView: 3,
        });
    }

    if ($('#cycletype').val() == "12") {
        seasonFunction()
        $('#reporting_date').hide();
        $('#season').show()

    }

    if ($('#cycletype').val() == "13") {
        yearFunction()
        $('#reporting_date').hide();
        $('#year').show()

    }
    if ($('#cycletype').val() == "14") {
        $('#reporting_date').datetimepicker({
            format: 'yyyy',
            autoclose: true,
            startView: 4,
            minView: 4,
        });
    }
    function reportingSave(operationtype, savedata, table) {
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../../reporting_save/",
            data: {
                operationtype: operationtype,
                cycletype: $('#cycletype').val(),
                savedata: JSON.stringify(savedata),
                reporting_date: $('#reporting_date').val(),
                funid: $('#funid').val(),
            },
            success: function (data) {
                console.log(data['data'])
                if (data['status'] == 1) {
                    table.ajax.reload();
                }
                alert(data['data']);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    }
    $("#new1").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../../../reporting_new/",
            data:
                {
                    app: $('#app').val(),
                    cycletype: $('#cycletype').val(),
                    reporting_date: $('#reporting_date').val(),
                    operationtype: 15,
                    funid: $('#funid').val(),

                },
            success: function (data) {
                if (data['status'] == 1) {
                    table.ajax.reload();
                    $("#new1").hide();
                    $("#save1").show();
                    $("#del1").show();
                    $("#release1").show();
                }
                alert(data['data']);
            },
            error: function (e) {
                alert("新增失败，请于管理员联系。");
            }
        });
    });
    $("#del1").click(function () {
        if (confirm("确定要删除表中数据？")) {
            var table = $('#sample_1').DataTable();
            $.ajax({
                type: "POST",
                url: "../../../reporting_del/",
                data:
                    {
                        app: $('#app').val(),
                        cycletype: $('#cycletype').val(),
                        reporting_date: $('#reporting_date').val(),
                        operationtype: 15,
                        funid: $('#funid').val(),

                    },
                success: function (data) {
                    if (data['status'] == 1) {
                        $("#new1").show();
                        $("#save1").hide();
                        $("#del1").hide();
                        $("#unrelease1").hide();
                        $("#gorelease1").hide();
                        table.ajax.reload();
                    }
                    alert(data['data']);
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    $('#save1').click(function () {
        $("Element").blur();
        var table = $('#sample_1').DataTable().data();
        var savedata = [];
        $.each(table, function (i, item) {
            savedata.push({
                "id": item.id,
                "target_id": item.target_id,
                "todayvalue": $('#table1_todayvalue_' + item.id).val(),
                "judgevalue": $('#table1_judgevalue_' + item.id).val(),
                "curvalue": $('#table1_curvalue_' + item.id).val(),
                "curvaluedate": $('#table1_curvaluedate_' + item.id).val(),
                "curvaluetext": $('#table1_curvaluetext_' + item.id).val(),
                "cumulativemonth": $('#table1_cumulativemonth_' + item.id).val(),
                "cumulativequarter": $('#table1_cumulativequarter_' + item.id).val(),
                "cumulativehalfyear": $('#table1_cumulativehalfyear_' + item.id).val(),
                "cumulativeyear": $('#table1_cumulativeyear_' + item.id).val()
            })
        });
        reportingSave(15, savedata, table);
    });

    $("#new2").click(function () {
        var table = $('#sample_2').DataTable();
        $.ajax({
            type: "POST",
            url: "../../../reporting_new/",
            data:
                {
                    app: $('#app').val(),
                    cycletype: $('#cycletype').val(),
                    reporting_date: $('#reporting_date').val(),
                    operationtype: 16,
                    funid: $('#funid').val(),

                },
            success: function (data) {
                if (data['status'] == 1) {
                    table.ajax.reload();
                    $("#new2").hide();
                    $("#save2").show();
                    $("#del2").show();
                    $("#reset2").show();
                    $("#release2").show();
                }
                alert(data['data']);
            },
            error: function (e) {
                alert("新增失败，请于管理员联系。");
            }
        });
    });
    $("#del2").click(function () {
        if (confirm("确定要删除表中数据？")) {
            var table = $('#sample_2').DataTable();
            $.ajax({
                type: "POST",
                url: "../../../reporting_del/",
                data:
                    {
                        app: $('#app').val(),
                        cycletype: $('#cycletype').val(),
                        reporting_date: $('#reporting_date').val(),
                        operationtype: 16,
                        funid: $('#funid').val(),

                    },
                success: function (data) {
                    if (data['status'] == 1) {
                        table.ajax.reload();
                        $("#new2").show();
                        $("#save2").hide();
                        $("#del2").hide();
                        $("#reset2").hide();
                        $("#unrelease2").hide();
                        $("#gorelease2").hide();
                    }
                    alert(data['data']);
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    $('#save2').click(function () {
        $("Element").blur();
        var table = $('#sample_2').DataTable().data();
        var savedata = [];
        $.each(table, function (i, item) {
            savedata.push({
                "id": item.id,
                "target_id": item.target_id,
                "todayvalue": $('#table2_todayvalue_' + item.id).val(),
                "judgevalue": $('#table2_judgevalue_' + item.id).val(),
                "curvalue": $('#table2_curvalue_' + item.id).val(),
                "curvaluedate": $('#table2_curvaluedate_' + item.id).val(),
                "curvaluetext": $('#table2_curvaluetext_' + item.id).val(),
                "cumulativemonth": $('#table2_cumulativemonth_' + item.id).val(),
                "cumulativequarter": $('#table2_cumulativequarter_' + item.id).val(),
                "cumulativehalfyear": $('#table2_cumulativehalfyear_' + item.id).val(),
                "cumulativeyear": $('#table2_cumulativeyear_' + item.id).val()
            })
        });
        reportingSave(16, savedata, table);
    });
    $('#reset2').click(function () {
        var table = $('#sample_2').DataTable();
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../../reporting_reextract/",
            data:
                {
                    operationtype: 16,
                    reporting_date: $('#reporting_date').val(),
                    app: $('#app').val(),
                    cycletype: $('#cycletype').val(),
                    funid: $('#funid').val(),
                },
            success: function (data) {
                if (data == 1) {
                    table.ajax.reload();
                    alert("提取成功！");
                } else
                    alert("提取失败，请于管理员联系。");
            },
            error: function (e) {
                alert("提取失败，请于管理员联系。");
            }
        });
    });
    var customModal = {
        "show": function () {
            $('#waiting_calculate').modal('show');
            $(el).show();
            $(".modal-backdrop").css('opacity', '0.3');
        },
        "hide": function () {
            $('#waiting_calculate').modal('hide');
            $(el).hide();
            $(".modal-backdrop").css('opacity', '0.5');
        },
    };
    // 新增数据计算
    $("#new3").click(function () {
        // 滚动条
        customModal.show();
        var table = $('#sample_3').DataTable();
        $.ajax({
            type: "POST",
            url: "../../../reporting_new/",
            data:
                {
                    app: $('#app').val(),
                    cycletype: $('#cycletype').val(),
                    reporting_date: $('#reporting_date').val(),
                    operationtype: 17,
                    funid: $('#funid').val(),

                },
            success: function (data) {
                if (data['status'] == 1) {
                    table.ajax.reload();
                    $("#new3").hide();
                    $("#save3").show();
                    $("#del3").show();
                    $("#reset3").show();
                    $("#release3").show();
                }
                // 隐藏滚动条
                customModal.hide();
                alert(data['data'])
            },
            error: function (e) {
                alert("新增失败，请于管理员联系。");
                // 隐藏滚动条
                customModal.hide();
            }
        });
    });
    $("#del3").click(function () {
        if (confirm("确定要删除表中数据？")) {
            var table = $('#sample_3').DataTable();
            $.ajax({
                type: "POST",
                url: "../../../reporting_del/",
                data:
                    {
                        app: $('#app').val(),
                        cycletype: $('#cycletype').val(),
                        reporting_date: $('#reporting_date').val(),
                        operationtype: 17,
                        funid: $('#funid').val(),

                    },
                success: function (data) {
                    if (data['status'] == 1) {
                        table.ajax.reload();
                        $("#new3").show();
                        $("#save3").hide();
                        $("#del3").hide();
                        $("#reset3").hide();
                        $("#unrelease3").hide();
                        $("#gorelease3").hide();
                    }
                    alert(data['data']);
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    $('#save3').click(function () {
        $("Element").blur();
        var table = $('#sample_3').DataTable().data();
        var savedata = [];
        $.each(table, function (i, item) {
            savedata.push({
                "id": item.id,
                "target_id": item.target_id,
                "todayvalue": $('#table3_todayvalue_' + item.id).val(),
                "judgevalue": $('#table3_judgevalue_' + item.id).val(),
                "curvalue": $('#table3_curvalue_' + item.id).val(),
                "curvaluedate": $('#table3_curvaluedate_' + item.id).val(),
                "curvaluetext": $('#table3_curvaluetext_' + item.id).val(),
                "cumulativemonth": $('#table3_cumulativemonth_' + item.id).val(),
                "cumulativequarter": $('#table3_cumulativequarter_' + item.id).val(),
                "cumulativehalfyear": $('#table3_cumulativehalfyear_' + item.id).val(),
                "cumulativeyear": $('#table3_cumulativeyear_' + item.id).val()
            })
        });
        reportingSave(17, savedata, table);
    });
    $('#reset3').click(function () {
        customModal.show();
        var table = $('#sample_3').DataTable();
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../../reporting_recalculate/",
            data:
                {
                    operationtype: 17,
                    reporting_date: $('#reporting_date').val(),
                    app: $('#app').val(),
                    cycletype: $('#cycletype').val(),
                    funid: $('#funid').val(),
                },
            success: function (data) {
                if (data['status'] == 1) {
                    table.ajax.reload();
                }
                // 隐藏滚动条
                customModal.hide();
                alert(data['data']);
            },
            error: function (e) {
                alert("计算失败，请于管理员联系。");
                // 隐藏滚动条
                customModal.hide();
            }
        });
    });

    $("#new5").click(function () {
        var table = $('#sample_5').DataTable();
        $.ajax({
            type: "POST",
            url: "../../../reporting_new/",
            data:
                {
                    app: $('#app').val(),
                    cycletype: $('#cycletype').val(),
                    reporting_date: $('#reporting_date').val(),
                    operationtype: 1,
                    funid: $('#funid').val(),

                },
            success: function (data) {
                if (data['status'] == 1) {
                    table.ajax.reload();
                    $("#new5").hide();
                    $("#save5").show();
                    $("#del5").show();
                    $("#release5").show();
                }
                alert(data['data'])
            },
            error: function (e) {
                alert("新增失败，请于管理员联系。");
            }
        });
    });
    $("#del5").click(function () {
        if (confirm("确定要删除表中数据？")) {
            var table = $('#sample_5').DataTable();
            $.ajax({
                type: "POST",
                url: "../../../reporting_del/",
                data:
                    {
                        app: $('#app').val(),
                        cycletype: $('#cycletype').val(),
                        reporting_date: $('#reporting_date').val(),
                        operationtype: 1,
                        funid: $('#funid').val(),

                    },
                success: function (data) {
                    if (data['status'] == 1) {
                        table.ajax.reload();
                        $("#new5").show();
                        $("#save5").hide();
                        $("#del5").hide();
                        $("#unrelease5").hide();
                        $("#gorelease5").hide();
                    }
                    alert(data['data']);
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    $('#save5').click(function () {
        $("Element").blur();
        var table = $('#sample_5').DataTable().data();
        var savedata = [];
        $.each(table, function (i, item) {
            savedata.push({
                "id": item.id,
                "target_id": item.target_id,
                "oldtable_zerodata": item.oldtable_zerodata,
                "oldtable_twentyfourdata": item.oldtable_twentyfourdata,
                "oldtable_value": item.oldtable_value,
                "oldtable_magnification": item.oldtable_magnification,
                "oldtable_finalvalue": item.oldtable_finalvalue,
                "newtable_zerodata": item.newtable_zerodata,
                "newtable_twentyfourdata": item.newtable_twentyfourdata,
                "newtable_value": item.newtable_value,
                "newtable_magnification": item.newtable_magnification,
                "newtable_finalvalue": item.newtable_finalvalue,
                "finalvalue": item.finalvalue,
                "reporting_date": $("#reporting_date").val(),
                "magnification": $('#table5_magnification_' + item.id).val(),
                "zerodata": $('#table5_zerodata_' + item.id).val(),
                "twentyfourdata": $('#table5_twentyfourdata_' + item.id).val(),
                "metervalue": $('#table5_metervalue_' + item.id).val(),
                "todayvalue": $('#table5_todayvalue_' + item.id).val(),
                "judgevalue": $('#table5_judgevalue_' + item.id).val(),
                "curvalue": $('#table5_curvalue_' + item.id).val(),
                "curvaluedate": $('#table5_curvaluedate_' + item.id).val(),
                "curvaluetext": $('#table5_curvaluetext_' + item.id).val(),
                "cumulativemonth": $('#table5_cumulativemonth_' + item.id).val(),
                "cumulativequarter": $('#table5_cumulativequarter_' + item.id).val(),
                "cumulativehalfyear": $('#table5_cumulativehalfyear_' + item.id).val(),
                "cumulativeyear": $('#table5_cumulativeyear_' + item.id).val()
            })
        });
        reportingSave(1, savedata, table);
    });

    function reportingRelease(savedata, tables) {
        if (confirm("确定要发布数据？")) {
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: "../../../reporting_release/",
                data:
                    {
                        app: $('#app').val(),
                        cycletype: $('#cycletype').val(),
                        savedata: JSON.stringify(savedata),
                        reporting_date: $('#reporting_date').val(),
                        funid: $('#funid').val(),
                    },
                success: function (data) {
                    if (data['status'] == 1) {
                        for (var i = 0; i < tables.length; i++) {
                            tables[i].ajax.reload();
                        }
                    }
                    alert(data['data']);
                },
                error: function (e) {
                    alert("发布失败，请于管理员联系。");
                }
            });
        }
    }
    function reportingCancelRelease(savedata, tables) {
        if (confirm("确定要取消发布？")) {
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: "../../../reporting_cancel_release/",
                data:
                    {
                        app: $('#app').val(),
                        cycletype: $('#cycletype').val(),
                        savedata: JSON.stringify(savedata),
                        reporting_date: $('#reporting_date').val(),
                        funid: $('#funid').val(),
                    },
                success: function (data) {
                    if (data['status'] == 1) {
                        for (var i = 0; i < tables.length; i++) {
                            tables[i].ajax.reload();
                        }
                    }
                    alert(data['data']);
                },
                error: function (e) {
                    alert("取消发布失败，请于管理员联系。");
                }
            });
        }
    }
    // 发布
    $('#release1,#release2,#release3,#release5').click(function () {
        $("Element").blur();
        var table1 = $('#sample_1').DataTable().data();
        var savedata1 = [];
        $.each(table1, function (i, item) {
            savedata1.push({
                "id": item.id,
            })
        });

        var table2 = $('#sample_2').DataTable().data();
        var savedata2 = [];
        $.each(table2, function (i, item) {
            savedata2.push({
                "id": item.id,
            })
        });

        var table3 = $('#sample_3').DataTable().data();
        var savedata3 = [];
        $.each(table3, function (i, item) {
            savedata3.push({
                "id": item.id,
            })
        });

        var table5 = $('#sample_5').DataTable().data();
        var savedata5 = [];
        $.each(table5, function (i, item) {
            savedata5.push({
                "id": item.id,
            })
        });

        var savedata = {'15': savedata1, '16': savedata2, '17': savedata3, '1': savedata5};

        reportingRelease(savedata, [table1, table2, table3, table5]);
    });
    // 取消发布
    $('#cancel_release1,#cancel_release2,#cancel_release3, #cancel_release5').click(function () {
        $("Element").blur();
        var table1 = $('#sample_1').DataTable().data();
        var savedata1 = [];
        $.each(table1, function (i, item) {
            savedata1.push({
                "id": item.id,
            })
        });

        var table2 = $('#sample_2').DataTable().data();
        var savedata2 = [];
        $.each(table2, function (i, item) {
            savedata2.push({
                "id": item.id,
            })
        });

        var table3 = $('#sample_3').DataTable().data();
        var savedata3 = [];
        $.each(table3, function (i, item) {
            savedata3.push({
                "id": item.id,
            })
        });

        var table5 = $('#sample_5').DataTable().data();
        var savedata5 = [];
        $.each(table5, function (i, item) {
            savedata5.push({
                "id": item.id,
            })
        });

        var savedata = {'15': savedata1, '16': savedata2, '17': savedata3, '1': savedata5};

        reportingCancelRelease(savedata, [table1, table2, table3, table5]);
    });

    // nav_tab切换事件
    // $('#navtabs a').click(function (e) {
    //     var nodeId = $(this).prop('id');
    //     // 数据查询
    //     if (nodeId == 'tabcheck4') {
    //         var table = $('#sample_4').DataTable();
    //         table.ajax.url("../../../reporting_search_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() +
    //             "&reporting_date=" + $('#reporting_date').val() + "&searchapp=" + $('#searchapp').val()
    //         ).load();
    //     }
    // });

});

