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
        "bSort": true,
        "iDisplayLength": 25,
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
            "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>" +
                "<button  id='copy' title='复制' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-copy'></i></button>" +
                "<button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>"
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
        var data_field = {"d": "当前值", "m": "月累积", "s": "季累积", "h": "半年累积", "y": "年累积", 'c': '常数'};
        var data_time = {
            "D": "当天", "L": "前一天", "MS": "月初", "ME": "月末", "LMS": "上月初", "LME": "上月末", "SS": "季初", "SE": "季末",
            "LSS": "上季初", "LSE": "上季末", "HS": "半年初", "HE": "半年末", "LHS": "前个半年初", "LHE": "前个半年末", "YS": "年初",
            "YE": "年末", "LYS": "去年初", "LYE": "去年末", "MAVG": "月平均值", "SAVG": "季平均值", "HAVG": "半年平均值", "YAVG": "年均值",
            "MMAX": "月最大值", "MMIN": "月最小值", "SMAX": "季最大值", "SMIN": "季最小值",
            "HMAX": "半年最大值", "HMIN": "半年最小值", "YMAX": "年最大值", "YMIN": "年最小值", "SLME": "本季上月末"
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

    $('#sample_1 tbody').on('click', 'button#edit, button#copy', function () {

        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();

        if ($(this).context.id == 'edit') {
            $("#id").val(data.id);
        } else {
            $("#id").val('0');
        }
        $("#name").val(data.name);
        $("#code").val(data.code);
        $("#operationtype").val(data.operationtype);
        $('#cumulative').empty();
        if (data.operationtype == '17') {
            $('#cumulative').append('<option value="0" selected>不累计</option>\n' +
                '<option value="1">求和</option>\n' +
                '<option value="2">算术平均</option>\n' +
                '<option value="3">加权平均</option>'
            );
            $('#weight_target').val('').trigger('change').prop('disabled', true);
        } else {
            $('#cumulative').append('<option value="0" selected>不累计</option>\n' +
                '<option value="1">求和</option>\n' +
                '<option value="2">算术平均</option>\n'
            );
        }

        $("#cycletype").val(data.cycletype);
        $("#businesstype").val(data.businesstype);
        $("#unit").val(data.unit);
        $("#magnification").val(data.magnification);
        $("#digit").val(data.digit);
        $("#upperlimit").val(data.upperlimit);
        $("#lowerlimit").val(data.lowerlimit);
        $("#datatype").val(data.datatype);
        $("#cumulative").val(data.cumulative);

        if (data.cumulative == '3') {
            $('#weight_target').val(data.weight_target).trigger('change').removeProp('disabled');
        } else {
            $('#weight_target').val('').trigger('change').prop('disabled', true);
        }


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

        $("#data_from").val(data.data_from);
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

        $('#data_from_div').hide();

        // 数值类型
        $('#cumulate_weight').show();
        $('#upperlimit_lowerlimit').show();
        $('#magnification_digit').show();

        // 数据来源
        if (data.data_from == 'et') {
            $('#data_from_config').show();
        } else {
            $('#data_from_config').hide();
        }

        // 操作类型：提取/电表走字 显示数据源配置
        var selected_operation_type = $('#operationtype option:selected').text();
        if (selected_operation_type == '计算') {
            if (data.data_from == 'et') {
                $('#calculate').hide();
                $('#calculate_analysis').hide();
            } else {
                $('#calculate').show();
                $('#calculate_analysis').show();
            }
            $('#data_from').parent().show();
            $('#data_from').parent().prev().show();
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

    });

    $('#sample_1 tbody').on('click', 'button#copy', function () {

        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();

        $("#id").val("0");
        $("#name").val(data.name);
        $("#code").val(data.code);
        $("#operationtype").val(data.operationtype);
        $("#cycletype").val(data.cycletype);
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

        $('#cumulate_weight').show();
        $('#upperlimit_lowerlimit').show();
        $('#magnification_digit').show();

        // 操作类型：提取/电表走字 显示数据源配置
        var selected_operation_type = $('#operationtype option:selected').text();
        if (selected_operation_type == '计算') {
            if (data.data_from == 'et') {
                $('#calculate').hide();
                $('#calculate_analysis').hide();
            } else {
                $('#calculate').show();
                $('#calculate_analysis').show();
            }
            $('#data_from').parent().show();
            $('#data_from').parent().prev().show();
        }
        if (['提取', '电表走字'].indexOf(selected_operation_type) != -1) {
            $('#extract').show();
        }

        if ($('#datatype option:selected').text() == '日期' || $('#datatype option:selected').text() == '文本') {
            $('#cumulate_weight').hide();
            $('#upperlimit_lowerlimit').hide();
            $('#magnification_digit').hide();
        }
        if ($('#datatype option:selected').text() == '数值') {
            $('#cumulate_weight').show();
            $('#upperlimit_lowerlimit').show();
            $('#magnification_digit').show();
        }

        ajaxFunction();
        analysisFunction();
        $("#formula").bind('input propertychange', function () {
            analysisFunction();
        });
    });

    // 数据来源
    $('#data_from').change(function () {
        var data_from = $(this).val();
        if (data_from == 'et') {
            $('#data_from_config').show();
            $('#calculate').hide();
            $('#calculate_analysis').hide();
        } else {
            $('#data_from_config').hide();
            $('#calculate').show();
            $('#calculate_analysis').show();
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

        $('#data_from_config').hide();
        $('#data_from_div').hide();

        $('#cumulative').empty();

        var selected_operation_type = $('#operationtype option:selected').text();
        if (selected_operation_type == '计算') {
            $('#data_from').val('');
            $('#data_from_div').show();
            $('#cumulative').append('<option value="0" selected>不累计</option>\n' +
                '<option value="1">求和</option>\n' +
                '<option value="2">算术平均</option>\n' +
                '<option value="3">加权平均</option>'
            );
            $('#weight_target').val('').trigger('change').prop('disabled', true);
        } else {
            $('#cumulative').append('<option value="0" selected>不累计</option>\n' +
                '<option value="1">求和</option>\n' +
                '<option value="2">算术平均</option>\n'
            );
        }
        if (['提取', '电表走字'].indexOf(selected_operation_type) != -1) {
            $('#extract').show();
        }
    });

    $('#datatype').change(function () {
        if ($('#datatype option:selected').text() == '日期' || $('#datatype option:selected').text() == '文本') {
            $('#magnification_digit').hide();
            $('#upperlimit_lowerlimit').hide();

            $('#calculate').hide();
            $('#calculate_analysis').hide();

            $('#data_from_config').hide();
            $('#data_from_div').hide();
        }
        if ($('#datatype option:selected').text() == '数值') {
            $('#cumulate_weight').show();
            $('#upperlimit_lowerlimit').show();
            $('#magnification_digit').show();

            // 判断操作类型
            // 判断数据来源
            if ($('#operationtype option:selected').text().trim() == '计算') {
                $('#data_from').parent().show();
                $('#data_from').parent().prev().show();

                if ($('#data_from').val() == 'lc') {
                    $('#calculate').show();
                    $('#calculate_analysis').show();
                    $('#data_from_config').hide();
                } else if (!$('#data_from').val()) {
                    $('#calculate').hide();
                    $('#calculate_analysis').hide();
                    $('#data_from_config').hide();
                } else {
                    $('#calculate').hide();
                    $('#calculate_analysis').hide();
                    $('#data_from_config').show();
                }
            } else {
                $('#calculate').hide();
                $('#calculate_analysis').hide();
                $('#data_from_config').hide();
            }

        }
    });

    $("#new").click(function () {
        // 累计类型
        $('#cumulative').empty();
        $('#cumulative').append('<option value="0" selected>不累计</option>\n' +
            '<option value="1">求和</option>\n' +
            '<option value="2">算术平均</option>\n'
        );

        $('#calculate').hide();
        $('#calculate_analysis').hide();
        $('#extract').hide();

        $("#id").val("0");
        $("#name").val("");
        $("#code").val("");
        $("#operationtype").val("");
        $("#cycletype").val("10");
        $("#businesstype").val("");
        $("#unit").val("");
        $("#magnification").val("1");
        $("#digit").val("2");
        $("#upperlimit").val("");
        $("#lowerlimit").val("");
        $("#datatype").val("numbervalue");

        $("#cumulative").val("0");
        $('#weight_target').val('').trigger('change').prop('disabled', true);

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
        $('#work_edit').empty();

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

        $('#data_from').val('');
        $('#calculate_source').val('');
        $('#calculate_content').val('');
        $('#data_from_div').hide();
        $('#data_from_config').hide();

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
                    weight_target: $('#weight_target').val(),

                    sort: $("#sort").val(),
                    unity: $("#unity").val(),
                    formula: $("#formula").val(),

                    cycle: $("#cycle").val(),
                    source: $("#source").val(),
                    source_content: $('#source_content').val(),
                    storage: $("#storage").val(),
                    storagetag: $("#storagetag").val(),
                    storagefields: $("#storagefields").val(),
                    is_repeat: $("#is_repeat").val(),
                    savetype: 'app',

                    works: $('#work_edit').val(),

                    data_from: $('#data_from').val(),
                    calculate_source: $('#calculate_source').val(),
                    calculate_content: $('#calculate_content').val(),
                },
            success: function (data) {
                var myres = data["res"];
                var mydata = data["data"];
                if (myres == "保存成功。") {
                    $("#id").val(data["data"]);
                    $('#static').modal('hide');
                    table.ajax.reload();

                    loadWeightTargets();
                }
                alert(myres);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });

        ajaxFunction();
    });

    $('#error').click(function () {
        $(this).hide()
    });

    $('#sample_2').dataTable({
        "bAutoWidth": true,
        "bSort": true,
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
    });

    var importData = [];
    // 选中导入指标
    $('#sample_2 tbody').on('click', 'input[name="selecttarget"]', function () {
        if ($(this).prop('checked')) {
            importData.push($(this).val());
        } else {
            for (var i = 0; i < importData.length; i++) {
                if (importData[i] == $(this).val()) {
                    importData.splice(i, 1);
                }
            }
        }
    });

    $('#addadminapp_save').click(function () {
        var table1 = $('#sample_1').DataTable();
        var table2 = $('#sample_2').DataTable();
        if (importData.length < 1) {
            alert("请至少选择一个指标");
        } else {
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: "../../target_importadminapp/",
                data:
                    {
                        adminapp: $("#adminapp").val(),
                        selectedtarget: JSON.stringify(importData),
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


    $('#formula').contextmenu({
        target: '#context-menu2',
        onItem: function (context, e) {
        }
    });

    $('#cycletype').change(function () {
        loadcycleData()
    });


    $('#collect').click(function () {
        getTxt1CursorPosition("formula");

        $("#search_operationtype3").val("");
        $("#search_cycletype3").val("");
        $("#search_businesstype3").val("");
        $("#search_unit3").val("");

        loadcycleData();
        $('#insert_target').modal('show')
    });

    var completed = false;

    function loadcycleData() {
        if (completed) {
            $('#sample_3').dataTable().fnDestroy();
        }
        $('#sample_3').dataTable({
            "bAutoWidth": true,
            "bSort": true,
            "bProcessing": true,
            "ajax": "../../target_data/?&datatype=" + $('#datatype').val(),
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
                "targets": -5,
                "data": null,
                "mRender": function (data, type, full) {
                    var cumulative_info = {
                        "0": "不累计",
                        "1": "求和",
                        "2": "算术平均",
                        "3": "加权平均",
                    };
                    return cumulative_info[full.cumulative]
                }
            }, {
                "targets": -3,
                "data": null,
                "mRender": function (data, type, full) {
                    if (full.cumulative == "0") {
                        return "<select style='width:100px'><option value='d'>当前值</option>"
                    }
                    if (full.cumulative != "0" && full.cycletype_name == "日") {
                        return "<select style='width:100px'><option value='d'>当前值</option><option value='m'>月累计</option><option value='s'>季累计</option><option value='h'>半年累计</option><option value='y'>年累计</option></select>";
                    }
                    if (full.cumulative != "0" && full.cycletype_name == "月") {
                        return "<select style='width:100px'><option value='d'>当前值</option><option value='s'>季累计</option><option value='h'>半年累计</option><option value='y'>年累计</option></select>";
                    }
                    if (full.cumulative != "0" && full.cycletype_name == "季") {
                        return "<select style='width:100px'><option value='d'>当前值</option><option value='h'>半年累计</option><option value='y'>年累计</option></select>";
                    }
                    if (full.cumulative != "0" && full.cycletype_name == "半年") {
                        return "<select style='width:100px'><option value='d'>当前值</option><option value='y'>年累计</option></select>";
                    }
                    if (full.cumulative != "0" && full.cycletype_name == "年") {
                        return "<select style='width:100px'><option value='d'>当前值</option></select>";
                    }
                    if (full.cumulative == null || full.cumulative == '') {
                        return ""
                    }
                    return "";
                },
            }, {
                "targets": -2,
                "data": null,
                "mRender": function (data, type, full) {
                    if ($("#cycletype").val() == '10' && full.cycletype_name == '日') {
                        return "<select style='width:100px'><option value='D'>当天</option><option value='L'>前一天</option><option value='LME'>上月末</option>" +
                            "<option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='MMAX'>月最大值</option><option value='MMIN'>月最小值</option><option value='SMAX'>季最大值</option><option value='SMIN'>季最小值</option>" +
                            "<option value='HMAX'>半年最大值</option><option value='HMIN'>半年最小值</option><option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='MAVG'>月平均值</option><option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option><option value='SLME'>本季上月末</option></select>"

                    }
                    if ($("#cycletype").val() == '10' && full.cycletype_name == '月') {
                        return "<select style='width:100px'><option value='LME'>上月末</option>" +
                            "<option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='SMAX'>季最大值</option><option value='SMIN'>季最小值</option>" +
                            "<option value='HMAX'>半年最大值</option><option value='HMIN'>半年最小值</option><option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option><option value='SLME'>本季上月末</option></select>"

                    }
                    if ($("#cycletype").val() == '10' && full.cycletype_name == '季') {
                        return "<select style='width:100px'><option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option>" +
                            "<option value='HMAX'>半年最大值</option><option value='HMIN'>半年最小值</option><option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option><option value='SLME'>本季上月末</option></select>"

                    }
                    if ($("#cycletype").val() == '10' && full.cycletype_name == '半年') {
                        return "<select style='width:100px'><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='YAVG'>年平均值</option></select>"

                    }
                    if ($("#cycletype").val() == '10' && full.cycletype_name == '年') {
                        return "<select style='width:100px'><option value='LYE'>去年末</option></select>"

                    }

                    if ($("#cycletype").val() == '11' && full.cycletype_name == '日') {
                        return "<select style='width:100px'><option value='ME'>月末</option><option value='LME'>上月末</option>" +
                            "<option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='MMAX'>月最大值</option><option value='MMIN'>月最小值</option><option value='SMAX'>季最大值</option><option value='SMIN'>季最小值</option>" +
                            "<option value='HMAX'>半年最大值</option><option value='HMIN'>半年最小值</option><option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='MAVG'>月平均值</option><option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option><option value='SLME'>本季上月末</option></select>"

                    }
                    if ($("#cycletype").val() == '11' && full.cycletype_name == '月') {
                        return "<select style='width:100px'><option value='ME'>月末</option><option value='LME'>上月末</option>" +
                            "<option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='SMAX'>季最大值</option><option value='SMIN'>季最小值</option>" +
                            "<option value='HMAX'>半年最大值</option><option value='HMIN'>半年最小值</option><option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option><option value='SLME'>本季上月末</option></select>"

                    }
                    if ($("#cycletype").val() == '11' && full.cycletype_name == '季') {
                        return "<select style='width:100px'><option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='HMAX'>半年最大值</option><option value='HMIN'>半年最小值</option>" +
                            "<option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option><option value='SLME'>本季上月末</option></select>"

                    }
                    if ($("#cycletype").val() == '11' && full.cycletype_name == '半年') {
                        return "<select style='width:100px'><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='YAVG'>年平均值</option></select>"

                    }
                    if ($("#cycletype").val() == '11' && full.cycletype_name == '年') {
                        return "<select style='width:100px'><option value='LYE'>去年末</option></select>"

                    }

                    if ($("#cycletype").val() == '12' && full.cycletype_name == '日') {
                        return "<select style='width:100px'><option value='SE'>季末</option><option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='SMAX'>季最大值</option><option value='SMIN'>季最小值</option>" +
                            "<option value='HMAX'>半年最大值</option><option value='HMIN'>半年最小值</option><option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option><option value='SLME'>本季上月末</option></select>"

                    }
                    if ($("#cycletype").val() == '12' && full.cycletype_name == '月') {
                        return "<select style='width:100px'><option value='SE'>季末</option><option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='SMAX'>季最大值</option><option value='SMIN'>季最小值</option>" +
                            "<option value='HMAX'>半年最大值</option><option value='HMIN'>半年最小值</option><option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option><option value='SLME'>本季上月末</option></select>"

                    }
                    if ($("#cycletype").val() == '12' && full.cycletype_name == '季') {
                        return "<select style='width:100px'><option value='SE'>季末</option><option value='LSE'>上季末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='HMAX'>半年最大值</option><option value='HMIN'>半年最小值</option>" +
                            "<option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option><option value='SLME'>本季上月末</option></select>"

                    }
                    if ($("#cycletype").val() == '12' && full.cycletype_name == '半年') {
                        return "<select style='width:100px'><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='YAVG'>年平均值</option></select>"

                    }
                    if ($("#cycletype").val() == '12' && full.cycletype_name == '年') {
                        return "<select style='width:100px'><option value='LYE'>去年末</option></select>"

                    }

                    if ($("#cycletype").val() == '13' && full.cycletype_name == '日') {
                        return "<select style='width:100px'><option value='HE'>半年末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='HMAX'>半年最大值</option><option value='HMIN'>半年最小值</option>" +
                            "<option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                    }
                    if ($("#cycletype").val() == '13' && full.cycletype_name == '月') {
                        return "<select style='width:100px'><option value='HE'>半年末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='HMAX'>半年最大值</option><option value='HMIN'>半年最小值</option>" +
                            "<option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                    }
                    if ($("#cycletype").val() == '13' && full.cycletype_name == '季') {
                        return "<select style='width:100px'><option value='HE'>半年末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='HMAX'>半年最大值</option><option value='HMIN'>半年最小值</option>" +
                            "<option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"

                    }
                    if ($("#cycletype").val() == '13' && full.cycletype_name == '半年') {
                        return "<select style='width:100px'><option value='HE'>半年末</option><option value='LHE'>前个半年末</option>" +
                            "<option value='LYE'>去年末</option><option value='YMAX'>年最大值</option><option value='YMIN'>年最小值</option>" +
                            "<option value='YAVG'>年平均值</option></select>"

                    }
                    if ($("#cycletype").val() == '13' && full.cycletype_name == '年') {
                        return "<select style='width:100px'><option value='LYE'>去年末</option></select>"

                    }

                    if ($("#cycletype").val() == '14' && full.cycletype_name == '日') {
                        return "<select style='width:100px'><option value='YE'>年末</option><option value='LYE'>去年末</option><option value='YMAX'>年最大值</option>" +
                            "<option value='YMIN'>年最小值</option><option value='YAVG'>年平均值</option></select>"

                    }
                    if ($("#cycletype").val() == '14' && full.cycletype_name == '月') {
                        return "<select style='width:100px'><option value='YE'>年末</option><option value='LYE'>去年末</option><option value='YMAX'>年最大值</option>" +
                            "<option value='YMIN'>年最小值</option><option value='YAVG'>年平均值</option></select>"

                    }
                    if ($("#cycletype").val() == '14' && full.cycletype_name == '季') {
                        return "<select style='width:100px'><option value='YE'>年末</option><option value='LYE'>去年末</option><option value='YMAX'>年最大值</option>" +
                            "<option value='YMIN'>年最小值</option><option value='YAVG'>年平均值</option></select>"

                    }
                    if ($("#cycletype").val() == '14' && full.cycletype_name == '半年') {
                        return "<select style='width:100px'><option value='YE'>年末</option><option value='LYE'>去年末</option><option value='YMAX'>年最大值</option>" +
                            "<option value='YMIN'>年最小值</option><option value='YAVG'>年平均值</option></select>"

                    }
                    if ($("#cycletype").val() == '14' && full.cycletype_name == '年') {
                        return "<select style='width:100px'><option value='YE'>年末</option><option value='LYE'>去年末</option></select>"

                    }
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
            },
            initComplete: function (settings, json) {
                completed = true;
            }
        });
    }


    $('#search_adminapp,#search_app,#search_operationtype3,#search_cycletype3,#search_businesstype3,#search_unit3').change(function () {
        var table = $('#sample_3').DataTable();
        table.ajax.url("../../target_data?search_operationtype=" + $('#search_operationtype3').val() + "&search_cycletype=" + $('#search_cycletype3').val() + "&search_businesstype=" + $('#search_businesstype3').val() + "&search_unit=" + $('#search_unit3').val()).load();
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
        $('#insert_target').modal('hide')
    });

    $('#storage').change(function () {
        var storage_id = $(this).val();
        var storage_type = $('#storage_' + storage_id).val();
        if (storage_type == '列') {
            $('#storagetag').parent().parent().show();
        } else {
            $('#storagetag').parent().parent().hide();
        }
    });

    $('#sample_4').dataTable({
        "bAutoWidth": true,
        "bSort": true,
        "bProcessing": true,
        "ajax": "../../constant_data/",
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "code"},
            {"data": "value"},
            {"data": null}
        ],

        "columnDefs": [{
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
            "sZeroRecords": "没有检索到数据",
        },
    });

    $('#sample_4 tbody').on('click', 'button#select', function () {
        var table = $('#sample_4').DataTable();
        var data1 = table.row($(this).parents('tr')).data().code;
        var select = '<' + data1 + ':' + 'c' + '>';
        var data = $('#formula').val();
        var seat = $('#formula').attr("seat");
        data = data.slice(0, seat) + select + data.slice(seat);
        $('#formula').val(data);
        analysisFunction();
        $('#insert_target').modal('hide');
    });

    // 累计类型
    $('#cumulative').change(function () {
        // 加权平均数=>展示，供选择
        // 其他：disabled，val(-1)
        if ($(this).val() == '3') {
            $('#weight_target').removeProp('disabled');
        } else {
            $('#weight_target').val('').trigger('change');
            $('#weight_target').prop('disabled', true);
        }
    });

    function loadWeightTargets() {
        $('#weight_target').select2().empty();
        // 加载加权指标
        $.ajax({
            type: "POST",
            url: "../../load_weight_targets/",
            data: {},
            success: function (data) {
                $("#weight_target").select2({
                    data: eval(data.data),
                    placeholder: {
                        id: '', // the value of the option
                        text: ''
                    },
                    width: null,
                    dropdown: true
                });
            },
            error: function (e) {
                alert("加载加权指标，请于管理员联系。");
            }
        });
    }

    loadWeightTargets();
});

