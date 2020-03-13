// 定位公式框中鼠标的位置
function getTxt1CursorPosition(id) {
    var oTxt1 = document.getElementById(id);
    var cursurPosition = -1;
    try {
        if (oTxt1.selectionStart) {
            cursurPosition = oTxt1.selectionStart;
        } else {
            var range = document.selection.createRange();
            range.moveStart("character", -oTxt1.value.length);
            cursurPosition = range.text.length;
        }
    } catch (err) {
        cursurPosition = 0
    }
    $('#formula').attr({'seat': cursurPosition})
}

$(document).ready(function () {
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../../target_data/?search_adminapp=" + $('#adminapp').val(),
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "unity"},
            {"data": "code"},
            {"data": "operationtype_name"},
            {"data": "cycletype_name"},
            {"data": "businesstype_name"},
            {"data": "unit_name"},
            {"data": null}
        ],

        "columnDefs": [{
            "targets": -1,
            "data": null,
            "width": "100px",
            "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>"
        }],
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

        "initComplete": function () {
            ajaxFunction()
        }
    });

    // 行按钮
    $('#sample_1 tbody').on('click', 'button#delrow', function () {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#sample_1').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../../target_del/",
                data:
                    {
                        id: data.id,
                    },
                success: function (data) {
                    if (data == 1) {
                        table.ajax.reload();
                        alert("删除成功！");
                    } else
                        alert("删除失败，请于管理员联系。");
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

            ajaxFunction()
        }
    });

    //公式解析函数
    function analysisFunction() {
        var formula_data = ($("#formula").val()).replace(/\s*/g, "");
        var formula_analysis_data_str = $("#formula_analysis_data").val();
        var formula_analysis_data = JSON.parse(formula_analysis_data_str);
        var data_field = {"d": "当前值", "m": "月累积", "s": "季累积", "h": "半年累积", "y": "年累积"};
        var data_time = {
            "D": "当天", "L": "前一天", "MS": "月初", "ME": "月末", "LMS": "上月初", "LME": "上月末", "SS": "季初", "SE": "季末",
            "LSS": "上季初", "LSE": "上季末", "HS": "半年初", "HE": "半年末", "LHS": "前个半年初", "LHE": "前个半年末", "YS": "年初",
            "YE": "年末", "LYS": "去年初", "LYE": "去年末", "MAVG": "月平均值", "SAVG": "季平均值", "HAVG": "半年平均值", "YAVG": "年均值"
        };

        var formula_data_list = formula_data.split(/[<>]/);
        var pre_data = '';
        var formula_data_pre1 = '';
        var formula_data_pre2 = '';
        var formula_data_pre3 = '';
        for (var i = 0; i < formula_data_list.length; i++) {
            var formula_data_pre = formula_data_list[i].split(':');
            var formula_data_pre_list = formula_data_pre;
            if (formula_data_pre[0] in formula_analysis_data) {
                formula_data_pre1 = formula_analysis_data[formula_data_pre[0]];
                formula_data_pre_list[0] = formula_data_pre1
            } else {
                formula_data_pre1 = formula_data_pre[0]
            }
            if (formula_data_pre[1]) {
                if (formula_data_pre[1] in data_field) {
                    formula_data_pre2 = data_field[formula_data_pre[1]];
                    formula_data_pre_list[1] = formula_data_pre2
                } else {
                    formula_data_pre2 = formula_data_pre[1]
                }
            }
            if (formula_data_pre[2]) {
                if (formula_data_pre[2] in data_time) {
                    formula_data_pre3 = data_time[formula_data_pre[2]];
                    formula_data_pre_list[2] = formula_data_pre3
                } else {
                    formula_data_pre3 = formula_data_pre[2];
                }
            }
            formula_data_pre_list = formula_data_pre_list.join(':');
            formula_data_pre_list = '<' + formula_data_pre_list + '>';
            if (pre_data) {
                pre_data = pre_data.replace('<' + formula_data_list[i] + '>', formula_data_pre_list)
            } else {
                pre_data = formula_data.replace('<' + formula_data_list[i] + '>', formula_data_pre_list)
            }
        }

        if (pre_data != "") {
            $("#formula_analysis").val(pre_data);
        } else {
            $("#formula_analysis").val(formula_data);
        }

    }

    function ajaxFunction() {
        $.ajax({
            type: "GET",
            url: "../../target_formula_data/",
            data: 'formula_analysis_data',
            dataType: 'json',
            success: function (data) {
                $("#formula_analysis_data").val(JSON.stringify(data));
            }
        });
    }

    $('#sample_1 tbody').on('click', 'button#edit', function () {
        $('#sample_3').DataTable().ajax.reload();

        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();

        $("#id").val(data.id);
        $("#name").val(data.name);
        $("#code").val(data.code);
        $("#operationtype").val(data.operationtype);
        $("#cycletype").val(data.cycletype);
        $("#calculate_cycletype").val(data.cycletype_name);
        $("#businesstype").val(data.businesstype);
        $("#unit").val(data.unit);
        $("#magnification").val(data.magnification);
        $("#digit").val(data.digit);
        $("#upperlimit").val(data.upperlimit);
        $("#lowerlimit").val(data.lowerlimit);
        $("#datatype").val(data.datatype);
        $("#cumulative").val(data.cumulative);
        $("#sort").val(data.sort);
        $("#unity").val(data.unity);
        $("#formula").val(data.formula);

        $("#cycle").val(data.cycle);
        $("#source").val(data.source);

        $("#source_content").val(data.source_content);

        $("#storage").val(data.storage);
        $("#storagetag").val(data.storagetag);
        $("#storagefields").val(data.storagefields);
        $("#is_repeat").val(data.is_repeat);
        // 过滤出所有works
        $('#work_edit').empty();

        var works_data = eval(data.works);
        for (var i = 0; i < works_data.length; i++) {
            $('#work_edit').append('<option value="' + works_data[i].id + '">' + works_data[i].name + '</option>');
        }
        $('#work_edit').val(data.work_selected);

        // 判断是否展示存储标识
        if (data.storage_type == '列') {
            $('#storagetag').parent().parent().show();
        } else {
            $('#storagetag').parent().parent().hide();
        }


        $('#calculate').hide();
        $('#calculate_analysis').hide();
        $('#extract').hide();

        $('#is_digit').show();
        $('#digit').show();
        $('#magnification_digit').show();
        $('#upperlimit_lowerlimit').show();


        // 操作类型：提取/电表走字 显示数据源配置
        var selected_operation_type = $('#operationtype option:selected').text();
        if (selected_operation_type == '计算') {
            $('#calculate').show();
            $('#calculate_analysis').show();
        }
        if (['提取', '电表走字'].indexOf(selected_operation_type) != -1) {
            $('#extract').show();
        }

        if ($('#datatype option:selected').text() == '日期' || $('#datatype option:selected').text() == '文本') {
            $('#is_digit').hide();
            $('#digit').hide();
            $('#magnification_digit').hide();
            $('#upperlimit_lowerlimit').hide();
        }
        if ($('#datatype option:selected').text() == '数值') {
            $('#is_digit').show();
            $('#digit').show();
            $('#magnification_digit').show();
            $('#upperlimit_lowerlimit').show();
        }

        ajaxFunction();
        analysisFunction();
        $("#formula").bind('input propertychange', function () {
            analysisFunction();
        });

        if ($('#datatype').val() == 'numbervalue' || $('#datatype').val() == 'date' || $('#datatype').val() == 'text') {
            var table = $('#sample_3').DataTable();
            table.ajax.url("../../target_data?&datatype=" + $('#datatype').val()).load();
        }

    });

    $('#search_adminapp,#search_app,#search_operationtype,#search_cycletype,#search_businesstype,#search_unit,#works').change(function () {
        var table = $('#sample_1').DataTable();
        table.ajax.url("../../target_data?search_adminapp=" + $('#adminapp').val() +
            "&search_operationtype=" + $('#search_operationtype').val() + "&search_cycletype="
            + $('#search_cycletype').val() + "&search_businesstype=" + $('#search_businesstype').val()
            + "&search_unit=" + $('#search_unit').val() + "&works=" + $('#works').val()
        ).load();
    });

    $('#operationtype').change(function () {
        $('#calculate').hide();
        $('#calculate_analysis').hide();
        $('#extract').hide();

        var selected_operation_type = $('#operationtype option:selected').text();
        if (selected_operation_type == '计算') {
            $('#calculate').show();
            $('#calculate_analysis').show();
        }
        if (['提取', '电表走字'].indexOf(selected_operation_type) != -1) {
            $('#extract').show();
        }
    });

    $('#datatype').change(function () {
        if ($('#datatype option:selected').text() == '日期' || $('#datatype option:selected').text() == '文本') {
            $('#is_digit').hide();
            $('#digit').hide();
            $('#magnification_digit').hide();
            $('#upperlimit_lowerlimit').hide();
        }
        if ($('#datatype option:selected').text() == '数值') {
            $('#is_digit').show();
            $('#digit').show();
            $('#magnification_digit').show();
            $('#upperlimit_lowerlimit').show();
        }
    });

    $("#new").click(function () {
        $('#sample_3').DataTable().ajax.reload();

        $('#calculate').hide();
        $('#calculate_analysis').hide();
        $('#extract').hide();

        $("#id").val("0");
        $("#name").val("");
        $("#code").val("");
        $("#operationtype").val("");
        $("#cycletype").val("");
        $("#businesstype").val("");
        $("#unit").val("");
        $("#magnification").val("1");
        $("#digit").val("2");
        $("#upperlimit").val("");
        $("#lowerlimit").val("");
        $("#datatype").val("numbervalue");
        $("#cumulative").val("是");
        $("#sort").val("");
        $("#unity").val("");
        $("#formula").val("");

        $("#cycle").val("");
        $("#source").val("");

        $('#source_content').val('');

        $("#storage").val("");
        $("#storagetag").val("");
        $("#storagefields").val("");
        $("#is_repeat").val("1");

        // 业务
        $('#work_list').empty();

        var work_list = eval($('#work_list').val());
        for (var i = 0; i < work_list.length; i++) {
            if (work_list[i].core == '是') {
                $('#work_edit').append('<option value="' + work_list[i].id + '" selected>' + work_list[i].name + '</option>');
            } else {
                $('#work_edit').append('<option value="' + work_list[i].id + '">' + work_list[i].name + '</option>');
            }
        }

        ajaxFunction();
        analysisFunction();
        $("#formula").bind('input propertychange', function () {
            analysisFunction();
        });

        if ($('#datatype').val() == 'numbervalue') {
            var table = $('#sample_3').DataTable();
            table.ajax.url("../../target_data?&datatype=" + $('#datatype').val()).load();
        }
    });

    $('#save').click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../target_save/",
            data:
                {
                    id: $("#id").val(),
                    name: $("#name").val(),
                    code: $("#code").val(),
                    operationtype: $("#operationtype").val(),
                    cycletype: $("#cycletype").val(),
                    businesstype: $("#businesstype").val(),
                    unit: $("#unit").val(),
                    magnification: $("#magnification").val(),
                    digit: $("#digit").val(),
                    upperlimit: $("#upperlimit").val(),
                    lowerlimit: $("#lowerlimit").val(),
                    adminapp: $("#adminapp").val(),
                    datatype: $("#datatype").val(),
                    cumulative: $("#cumulative").val(),
                    sort: $("#sort").val(),
                    unity: $("#unity").val(),
                    formula: $("#formula").val(),

                    cycle: $("#cycle").val(),
                    source: $("#source").val(),
                    // sourcetable: $("#sourcetable").val(),
                    // sourcesis: $("#sourcesis").val(),
                    // sourcefields: $("#sourcefields").val(),
                    // sourceconditions: $("#sourceconditions").val(),
                    source_content: $('#source_content').val(),
                    storage: $("#storage").val(),
                    storagetag: $("#storagetag").val(),
                    storagefields: $("#storagefields").val(),
                    is_repeat: $("#is_repeat").val(),
                    savetype: 'app',

                    works: $('#work_edit').val(),
                },
            success: function (data) {
                var myres = data["res"];
                var mydata = data["data"];
                if (myres == "保存成功。") {
                    $("#id").val(data["data"]);
                    $('#static').modal('hide');
                    table.ajax.reload();
                }
                alert(myres);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });

        ajaxFunction()
    })

    $('#error').click(function () {
        $(this).hide()
    })

    $('#sample_2').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../../target_data/?search_adminapp=null",
        "columns": [
            {"data": "id"},
            {"data": "id"},
            {"data": "name"},
            {"data": "code"},
            {"data": "operationtype_name"},
            {"data": "cycletype_name"},
            {"data": "businesstype_name"},
            {"data": "unit_name"},
        ],

        "columnDefs": [{
            "targets": 0,
            "mRender": function (data, type, full) {
                return "<input name='selecttarget' type='checkbox' class='checkboxes' value='" + data + "'/>"
            }


        }],
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
        }
    });

    $('#search_operationtype1,#search_cycletype1,#search_businesstype1,#search_unit1').change(function () {
        var table = $('#sample_2').DataTable();
        table.ajax.url("../../target_data?search_adminapp=null" + "&search_operationtype=" + $('#search_operationtype1').val() + "&search_cycletype=" + $('#search_cycletype1').val() + "&search_businesstype=" + $('#search_businesstype1').val() + "&search_unit=" + $('#search_unit1').val()).load();
    })

    $('#addadminapp_save').click(function () {
        var table1 = $('#sample_1').DataTable();
        var table2 = $('#sample_2').DataTable();
        var theArray = []
        $("input[name=selecttarget]:checked").each(function () {
            theArray.push($(this).val());
        });
        if (theArray.length < 1) {
            alert("请至少选择一个指标");
        } else {
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: "../../target_importadminapp/",
                data:
                    {
                        adminapp: $("#adminapp").val(),
                        selectedtarget: theArray,
                    },
                success: function (data) {
                    var myres = data["res"];
                    if (myres == "导入完成。") {
                        table1.ajax.reload();
                        table2.ajax.reload();
                    }
                    alert(myres);
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }

    });

    // 右键菜单栏
    $('#formula').contextmenu({
        target: '#context-menu2',
        onItem: function (context, e) {
        }
    });

    // 点击事件插入指标
    $('#collect').click(function () {
        getTxt1CursorPosition("formula");

        $("#search_operationtype3").val("");
        $("#search_cycletype3").val("");
        $("#search_businesstype3").val("");
        $("#search_unit3").val("");

        $('#myModal').modal('show')

    });

    // 模态框表格数据
    $('#sample_3').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../../target_data/",
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "code"},
            {"data": "cumulative"},
            {"data": "cycletype_name"},
            {"data": null},
            {"data": null},
            {"data": null}
        ],
        "columnDefs": [{
            "targets": -3,
            "data": null,
            "mRender": function (data, type, full) {
                if (full.cumulative == "否") {
                    return "<select style='width:100px'><option value='d'>当前值</option>"
                }
                if (full.cumulative == "是" && full.cycletype_name == "日") {
                    return "<select style='width:100px'><option value='d'>当前值</option><option value='m'>月累计</option><option value='s'>季累计</option><option value='h'>半年累计</option><option value='y'>年累计</option></select>";
                }
                if (full.cumulative == "是" && full.cycletype_name == "月") {
                    return "<select style='width:100px'><option value='d'>当前值</option><option value='s'>季累计</option><option value='h'>半年累计</option><option value='y'>年累计</option></select>";
                }
                if (full.cumulative == "是" && full.cycletype_name == "季") {
                    return "<select style='width:100px'><option value='d'>当前值</option><option value='h'>半年累计</option><option value='y'>年累计</option></select>";
                }
                if (full.cumulative == "是" && full.cycletype_name == "半年") {
                    return "<select style='width:100px'><option value='d'>当前值</option><option value='y'>年累计</option></select>";
                }
                if (full.cumulative == "是" && full.cycletype_name == "年") {
                    return "<select style='width:100px'><option value='d'>当前值</option></select>";
                }
                if (full.cumulative == null || full.cumulative == '') {
                    return ""
                }
            },
        },
            {
                "targets": -2,
                "data": null,
                "mRender": function (data, type, full) {
                    if ($("#calculate_cycletype").val()) {
                        if ($("#calculate_cycletype").val() == '日' && full.cycletype_name == '日') {
                            return "<select style='width:100px'><option value='D'>当天</option><option value='L'>前一天</option><option value='LME'>上月末</option>" +
                                "<option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='MAVG'>月平均值</option><option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '日' && full.cycletype_name == '月') {
                            return "<select style='width:100px'><option value='LME'>上月末</option>" +
                                "<option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '日' && full.cycletype_name == '季') {
                            return "<select style='width:100px'><option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '日' && full.cycletype_name == '半年') {
                            return "<select style='width:100px'><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '日' && full.cycletype_name == '年') {
                            return "<select style='width:100px'><option value='LYE'>去年末</option></select>"

                        }

                        if ($("#calculate_cycletype").val() == '月' && full.cycletype_name == '日') {
                            return "<select style='width:100px'><option value='ME'>月末</option><option value='LME'>上月末</option>" +
                                "<option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='MAVG'>月平均值</option><option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '月' && full.cycletype_name == '月') {
                            return "<select style='width:100px'><option value='ME'>月末</option><option value='LME'>上月末</option>" +
                                "<option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '月' && full.cycletype_name == '季') {
                            return "<select style='width:100px'><option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '月' && full.cycletype_name == '半年') {
                            return "<select style='width:100px'><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '月' && full.cycletype_name == '年') {
                            return "<select style='width:100px'><option value='LYE'>去年末</option></select>"

                        }

                        if ($("#calculate_cycletype").val() == '季' && full.cycletype_name == '日') {
                            return "<select style='width:100px'><option value='SE'>季末</option><option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '季' && full.cycletype_name == '月') {
                            return "<select style='width:100px'><option value='SE'>季末</option><option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '季' && full.cycletype_name == '季') {
                            return "<select style='width:100px'><option value='SE'>季末</option><option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '季' && full.cycletype_name == '半年') {
                            return "<select style='width:100px'><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '季' && full.cycletype_name == '年') {
                            return "<select style='width:100px'><option value='LYE'>去年末</option></select>"

                        }

                        if ($("#calculate_cycletype").val() == '半年' && full.cycletype_name == '日') {
                            return "<select style='width:100px'><option value='HE'>半年末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '半年' && full.cycletype_name == '月') {
                            return "<select style='width:100px'><option value='HE'>半年末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '半年' && full.cycletype_name == '季') {
                            return "<select style='width:100px'><option value='HE'>半年末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '半年' && full.cycletype_name == '半年') {
                            return "<select style='width:100px'><option value='HE'>半年末</option><option value='LHE'>前个半年末</option>" +
                                "<option value='LYE'>去年末</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '半年' && full.cycletype_name == '年') {
                            return "<select style='width:100px'><option value='LYE'>去年末</option></select>"

                        }

                        if ($("#calculate_cycletype").val() == '年' && full.cycletype_name == '日') {
                            return "<select style='width:100px'><option value='YE'>年末</option><option value='LYE'>去年末</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '年' && full.cycletype_name == '月') {
                            return "<select style='width:100px'><option value='YE'>年末</option><option value='LYE'>去年末</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '年' && full.cycletype_name == '季') {
                            return "<select style='width:100px'><option value='YE'>年末</option><option value='LYE'>去年末</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '年' && full.cycletype_name == '半年') {
                            return "<select style='width:100px'><option value='YE'>年末</option><option value='LYE'>去年末</option><option value='YAVG'>年平均值</option></select>"

                        }
                        if ($("#calculate_cycletype").val() == '年' && full.cycletype_name == '年') {
                            return "<select style='width:100px'><option value='YE'>年末</option><option value='LYE'>去年末</option></select>"

                        }
                    } else
                        return ""
                }
            },
            {
                "targets": -1,
                "data": null,
                "defaultContent": "<button  id='select' title='选择'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-check'></i></button>"
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
            "sZeroRecords": "没有检索到数据"
        }
    });

    $('#search_adminapp,#search_app,#search_operationtype3,#search_cycletype3,#search_businesstype3,#search_unit3,#datatype').change(function () {
        var table = $('#sample_3').DataTable();
        table.ajax.url("../../target_data?search_operationtype=" + $('#search_operationtype3').val() + "&search_cycletype=" + $('#search_cycletype3').val() + "&search_businesstype=" + $('#search_businesstype3').val() + "&search_unit=" + $('#search_unit3').val() + "&datatype=" + $('#datatype').val()).load();
    });


    $('#sample_3 tbody').on('click', 'button#select', function () {
        var table = $('#sample_3').DataTable();
        var data1 = table.row($(this).parents('tr')).data().code;
        var data2 = $(this).parent().prev().prev().find('option:selected').val();
        var data3 = $(this).parent().prev().find('option:selected').val();
        var select = '<' + data1 + ':' + data2 + ':' + data3 + '>';
        var data = $('#formula').val();
        var seat = $('#formula').attr("seat");
        data = data.slice(0, seat) + select + data.slice(seat);
        $('#formula').val(data);
        analysisFunction();
        $('#myModal').modal('hide')
    });

    $('#storage').change(function () {
        var storage_id = $(this).val();
        var storage_type = $('#storage_' + storage_id).val();
        console.log(storage_id)
        console.log(storage_type)
        if (storage_type == '列') {
            $('#storagetag').parent().parent().show();
        } else {
            $('#storagetag').parent().parent().hide();
        }
    });
});

