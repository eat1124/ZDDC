$(document).ready(function () {
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "iDisplayLength": 25,
        "bProcessing": true,
        "ajax": "../../target_data/?search_app=" + $('#adminapp').val(),
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "code"},
            {"data": "operationtype_name"},
            {"data": "cycletype_name"},
            {"data": "businesstype_name"},
            {"data": "unit_name"},
            {"data": "adminapp_name"},
            {"data": "work_selected_name"},
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
        if (confirm("确定要删除该指标的查看权限吗？")) {
            var table = $('#sample_1').DataTable();
            var data = table.row($(this).parents('tr')).data();
            var table2 = $('#sample_2').DataTable();
            $.ajax({
                type: "POST",
                url: "../../target_app_del/",
                data:
                    {
                        id: data.id,
                        adminapp: $("#adminapp").val(),

                    },
                success: function (data) {
                    if (data == 1) {
                        table.ajax.reload();
                        table2.ajax.reload();
                        alert("删除成功！");
                    } else
                        alert("删除失败，请于管理员联系。");
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

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
    $('#sample_1 tbody').on('click', 'button#edit', function () {
        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();

        $("#id").val(data.id);
        $("#name").val(data.name);
        $("#code").val(data.code);
        $("#operationtype").val(data.operationtype);
        $('#cumulative').empty();
        if (data.operationtype == '17') {
            $('#cumulative').append('<option value="0" selected>不累计</option>\n' +
                '<option value="1">求和</option>\n' +
                '<option value="2">算术平均</option>\n' +
                '<option value="3">加权平均</option>\n' +
                '<option value="4">非零算术平均</option>'
            );
            $('#weight_target').val('').trigger('change').prop('disabled', true);

            $('#data_from_div').show();  // 数据来源选项框
        } else {
            $('#cumulative').append('<option value="0" selected>不累计</option>\n' +
                '<option value="1">求和</option>\n' +
                '<option value="2">算术平均</option>\n' +
                '<option value="4">非零算术平均</option>'
            );
            $('#data_from_div').hide();
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
        $('#is_select').val(data.is_select);
        $('#warn_range').val(data.warn_range);
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
    });

    $('#search_adminapp,#search_app,#search_operationtype,#search_cycletype,#search_businesstype,#search_unit, #searchapp, #works').change(function () {
        var filterType = $(this).prop('id');
        if (filterType == 'searchapp') {
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
                workSelectInit('filter');
            }
        }
        var table = $('#sample_1').DataTable();
        table.ajax.url("../../target_data?search_app=" + $('#adminapp').val() + "&search_operationtype=" +
            $('#search_operationtype').val() + "&search_cycletype=" + $('#search_cycletype').val() +
            "&search_businesstype=" + $('#search_businesstype').val() + "&search_unit=" + $('#search_unit').val() +
            "&works=" + $('#works').val() + "&search_adminapp=" + $('#searchapp').val()
        ).load();
    });

    $('#error').click(function () {
        $(this).hide()
    });

    var sample_2_completed = false;
    $('#static1').on('show.bs.modal', function () {
        workSelectInit('import');
        $('#search_operationtype1, #search_cycletype1, #search_businesstype1, #search_unit1, #searchapp1, #works1').val('');

        if (sample_2_completed) {
            $('#sample_2').DataTable().destroy();
        }
        $('#sample_2').dataTable({
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../../target_data/?search_app_noselect=" + $('#adminapp').val(),
            "columns": [
                {"data": "id"},
                {"data": "id"},
                {"data": "name"},
                {"data": "code"},
                {"data": "operationtype_name"},
                {"data": "cycletype_name"},
                {"data": "businesstype_name"},
                {"data": "unit_name"},
                {"data": "adminapp_name"},
                {"data": "work_selected_name"},
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
            },
            "initComplete": function () {
                sample_2_completed = true;
            }
        });
    });

    $('#search_operationtype1, #search_cycletype1, #search_businesstype1, #search_unit1, #searchapp1, #works1').change(function () {
        var filterType = $(this).prop('id');
        if (filterType == 'searchapp1') {
            var app_id = $(this).val();
            if (app_id) {
                $('#works1').empty();
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
                $('#works1').append(pre_work_option);
            } else {
                workSelectInit('import');
            }
        }
        var table = $('#sample_2').DataTable();
        table.ajax.url("../../target_data?search_app_noselect=" + $('#adminapp').val() + "&search_operationtype=" + $('#search_operationtype1').val() +
            "&search_cycletype=" + $('#search_cycletype1').val() + "&search_businesstype=" + $('#search_businesstype1').val() +
            "&search_unit=" + $('#search_unit1').val() + "&works=" + $('#works').val() + "&search_adminapp=" + $('#searchapp').val() +
            "&works=" + $('#works1').val() + "&search_adminapp=" + $('#searchapp1').val()
        ).load();
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


    $('#addapp_save').click(function () {
        var table1 = $('#sample_1').DataTable();
        var table2 = $('#sample_2').DataTable();
        if (importData.length < 1) {
            alert("请至少选择一个指标");
        } else {
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: "../../target_importapp/",
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
    var search_app_list = eval($('#search_app_list').val());

    // 业务下拉框
    function workSelectInit(operate) {
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
        if (operate == 'import') {
            $('#works1').empty();
            $('#works1').append(pre);
        }
        if (operate == 'filter') {
            $('#works').empty();
            $('#works').append(pre);
        }
    }

    workSelectInit('filter');
});