$(document).ready(function () {
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
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
    $('#sample_1 tbody').on('click', 'button#edit', function () {
        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();

        $("#id").val(data.id);
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
        $("#cumulative").val(data.cumulative);
        $("#sort").val(data.sort);

        $("#formula").val(data.formula);

        $("#cycle").val(data.cycle);
        $("#source").val(data.source);
        // $("#sourcetable").val(data.sourcetable);
        // $("#sourcesis").val(data.sourcesis)
        // $("#sourcefields").val(data.sourcefields);
        // $("#sourceconditions").val(data.sourceconditions);
        $('#source_content').val(data.source_content);

        $("#storage").val(data.storage);
        $("#storagetag").val(data.storagetag);
        $("#storagefields").val(data.storagefields);

        // 判断是否展示存储标识
        if (data.storage_type == '列') {
            $('#storagetag').parent().parent().show();
        } else {
            $('#storagetag').parent().parent().hide();
        }

        $('#calculate').hide();
        $('#extract').hide();


        // 操作类型：提取/电表走字 显示数据源配置
        var selected_operation_type = $('#operationtype option:selected').text();
        if (selected_operation_type == '计算') {
            $('#calculate').show();
            $('#calculate_analysis').show();
        }
        if (['提取', '电表走字'].indexOf(selected_operation_type) != -1) {
            $('#extract').show();
        }
    });

    $('#search_adminapp,#search_app,#search_operationtype,#search_cycletype,#search_businesstype,#search_unit').change(function () {
        var table = $('#sample_1').DataTable();
        table.ajax.url("../../target_data?search_app=" + $('#adminapp').val() + "&search_operationtype=" + $('#search_operationtype').val() + "&search_cycletype=" + $('#search_cycletype').val() + "&search_businesstype=" + $('#search_businesstype').val() + "&search_unit=" + $('#search_unit').val()).load();
    })

    $('#error').click(function () {
        $(this).hide()
    })

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
        table.ajax.url("../../target_data?search_app_noselect=" + $('#adminapp').val() + "&search_operationtype=" + $('#search_operationtype1').val() + "&search_cycletype=" + $('#search_cycletype1').val() + "&search_businesstype=" + $('#search_businesstype1').val() + "&search_unit=" + $('#search_unit1').val()).load();
    })

    $('#addapp_save').click(function () {
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
                url: "../../target_importapp/",
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

    })
});