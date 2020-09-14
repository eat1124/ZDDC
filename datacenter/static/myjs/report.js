$(document).ready(function () {
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../report_data/",
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "code"},
            {"data": "file_name"},
            {"data": "report_type"},
            {"data": "app"},
            {"data": "sort"},
            {"data": null}
        ],

        "columnDefs": [{
            "targets": 1,
            "data": null,
            "render": function (data, type, full) {
                if (full.if_template){
                    return "<span title='模板'><i class='fa fa-bookmark' style='color: #36D7B7'></i></span> " +  full.name;
                } else {
                    return full.name;
                }
            },
        } ,{
            "targets": -1,
            "data": null,
            "width": "100px",
            "render": function (data, type, full) {
                return "<td><button class='btn btn-xs btn-primary' type='button'><a href='/download_file/?file_name'><i class='fa fa-arrow-circle-down' style='color: white'></i></a></button><button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button></td>".replace("file_name", "file_name=" + full.file_name)
            },
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
        if (confirm("确定要删除该条数据？")) {
            var table = $('#sample_1').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../report_del/",
                data: {
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

        }
    });
    $('#sample_1 tbody').on('click', 'button#edit', function () {
        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#id").val(data.id);
        $("#name").val(data.name);
        $("#code").val(data.code);
        $("#report_type").val(data.report_type_num);
        $("#app").val(data.app_id);
        $("#sort").val(data.sort);
        // $("#report_file").val(data.file_name);
        $("span.fileinput-filename").text(data.file_name);
        $("#file_status").attr("class", "fileinput fileinput-exists");

        var if_template = data.if_template;
        $('#if_template').val(if_template);
        if (if_template){
            $('#app_div').hide();
            $('#report_div').hide();
        } else {
            $('#app_div').show();
            $('#report_div').show();
            // 报表信息加载
            $("#report_info_div").empty();
            for (i = 0; i < data.report_info_list.length; i++) {
                $("#report_info_div").append('<div class="col-md-12" style="margin-bottom:9px;">\n' +
                    '    <label class="col-md-2 control-label"><span style="color:red;"></span>名称:</label>\n' +
                    '    <div class="col-md-4">\n' +
                    '        <input type="text" class="form-control" name="report_info_name_' + (i + 1) + '" value="' + data.report_info_list[i].report_info_name + '" placeholder="">\n' +
                    '        <div class="form-control-focus"></div>\n' +
                    '    </div>\n' +
                    '    <label class="col-md-2 control-label"><span style="color:red;"></span>值:</label>\n' +
                    '    <div class="col-md-4">\n' +
                    '        <input type="text" class="form-control" name="report_info_value_' + (i + 1) + '" value="' + data.report_info_list[i].report_info_value + '" placeholder="">\n' +
                    '        <div class="form-control-focus"></div>\n' +
                    '<span hidden>\n' +
                    '    <input type="text" class="form-control" name="report_info_id_' + (i + 1) + '" value="' + data.report_info_list[i].report_info_id + '" placeholder="">\n' +
                    '</span>' +
                    '    </div>\n'
                );
            }
            if ($("#report_info_div").children("div").length > 1) {
                $("#node_del").css("visibility", "visible");
            } else {
                $("#node_del").css("visibility", "hidden");
            }
        }
    });
    $("#new").click(function () {
        $('#if_template').val(0);
        $("span.fileinput-filename").empty();
        $("#file_status").attr("class", "fileinput fileinput-new");

        $("#id").val(0);
        $("#name").val("");
        $("#code").val("");
        $("#report_file").val("");
        $("#report_type").val("");
        $("#app").val("");
        $("#sort").val("");
        $("#node_del").css("visibility", "hidden");

        $("#report_info_div").empty();
        $("#report_info_div").append('<div class="col-md-12" style="margin-bottom:9px;">\n' +
            '    <label class="col-md-2 control-label"><span style="color:red;"></span>名称:</label>\n' +
            '    <div class="col-md-4">\n' +
            '        <input type="text" class="form-control" name="report_info_name_1" placeholder="">\n' +
            '        <div class="form-control-focus"></div>\n' +
            '    </div>\n' +
            '    <label class="col-md-2 control-label"><span style="color:red;"></span>值:</label>\n' +
            '    <div class="col-md-4">\n' +
            '        <input type="text" class="form-control" name="report_info_value_1" placeholder="">\n' +
            '        <div class="form-control-focus"></div>\n' +
            '    </div>\n' +
            '<span hidden>\n' +
            '    <input type="text" class="form-control" name="report_info_id_1" placeholder="">\n' +
            '</span>' +
            '</div>'
        );
    });

    $("#node_new").click(function () {
        var cNum = $("#report_info_div").children("div").length + 1;
        $("#report_info_div").append('<div class="col-md-12" style="margin-bottom:9px;">\n' +
            '    <label class="col-md-2 control-label"><span style="color:red;"></span>名称:</label>\n' +
            '    <div class="col-md-4">\n' +
            '        <input type="text" class="form-control" name="report_info_name_' + cNum + '" placeholder="">\n' +
            '        <div class="form-control-focus"></div>\n' +
            '    </div>\n' +
            '    <label class="col-md-2 control-label"><span style="color:red;"></span>值:</label>\n' +
            '    <div class="col-md-4">\n' +
            '        <input type="text" class="form-control" name="report_info_value_' + cNum + '" placeholder="">\n' +
            '        <div class="form-control-focus"></div>\n' +
            '    </div>\n' +
            '<span hidden>\n' +
            '    <input type="text" class="form-control" name="report_info_id_' + cNum + '" placeholder="">\n' +
            '</span>' +
            '</div>'
        );
        if ($("#report_info_div").children("div").length > 1) {
            $("#node_del").css("visibility", "visible");
        } else {
            $("#node_del").css("visibility", "hidden");
        }
    });

    $("#node_del").click(function () {
        // 删除最后一个子元素
        if ($("#report_info_div").children("div").length > 1) {
            $("#report_info_div").children("div:last-child").remove();

            $("#node_del").css("visibility", "visible");
        } else {
            $("#node_del").css("visibility", "hidden");
        }
    });

    $('#error').click(function () {
        $(this).hide()
    })

    $('#if_template').change(function(){
        var if_template = $(this).val();
        if (if_template == "1"){
            $('#app_div').hide();
            $('#report_div').hide();
        } else {
            $('#app_div').show();
            $('#report_div').show();
        }
    });
});