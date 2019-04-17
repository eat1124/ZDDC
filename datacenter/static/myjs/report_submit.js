$(document).ready(function() {
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_date=" + $('#reporting_date').val() + "&" + "search_report_type=" + $('#search_report_type').val(),
        "columns": [
            { "data": "id" },
            { "data": "name" },
            { "data": "code" },
            { "data": "state" },
            { "data": null }
        ],

        "columnDefs": [{
            "targets": -4,
            "mRender": function(data, type, full) {
                return "<a href='http://192.168.100.151:8075/webroot/decision/view/report?viewlet=" + full.file_name + "&curdate=" + $('#reporting_date').val() + "' target='_blank'>" + full.name + "</a>"
            }
        }, {
            "targets": -2,
            "mRender": function(data, type, full) {
                if (full.state == "已发布") {
                    return "<span style='color:green;'>" + full.state + "</span>"
                }
                if (full.state == "未发布") {
                    return "<span style='color:#FF9933;'>" + full.state + "</span>"
                }
                if (full.state == "未创建") {
                    return "<span style='color:red;'>" + full.state + "</span>"
                }
            }
        }, {
            "targets": -1,
            "data": null,
            "width": "80px",
            "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>",
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
    $('#sample_1 tbody').on('click', 'button#edit', function() {
        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#id").val(data.id);
        $("#name").val(data.name);
        $("#code").val(data.code);
        $("#report_type").val(data.report_type_num);
        $("#sort").val(data.sort);
        // $("#report_file").val(data.file_name);
        $("span.fileinput-filename").text(data.file_name);
        $("#file_status").attr("class", "fileinput fileinput-exists");
        $("#report_model").val(data.id);

        // 报表时间
        var report_time = data.report_time;
        if (report_time) {
            //..
        } else {
            report_time = $("#reporting_date").val();
        }
        $("#report_info_submit").empty();

        $("#report_info_submit").append('    <div class="form-group">\n' +
            '        <label class="col-md-2 control-label">报表时间</label>\n' +
            '        <div class="col-md-10">\n' +
            '            <input id="report_time" type="datetime" name="report_time" class="form-control "\n' +
            '                   placeholder="" autocomplete="off"  value="' + report_time + '" readonly>\n' +
            '            <div class="form-control-focus"></div>\n' +
            '        </div>\n' +
            '    </div>');

        $("#report_info_submit").append('<div class="form-group">\n' +
            '    <label class="col-md-2 control-label"><span\n' +
            '            style="color:red; "></span>填报人</label>\n' +
            '    <div class="col-md-4">\n' +
            '        <input id="person" type="text" name="person" class="form-control "\n' +
            '               placeholder="" value="' + data.person + '" readonly>\n' +
            '        <div class="form-control-focus"></div>\n' +
            '\n' +
            '    </div>\n' +
            '    <label class="col-md-2 control-label"><span\n' +
            '            style="color:red; "></span>更新日期</label>\n' +
            '    <div class="col-md-4">\n' +
            '        <input id="write_time" type="text" name="write_time" class="form-control "\n' +
            '               placeholder="" value="' + data.write_time + '" readonly>\n' +
            '        <div class="form-control-focus"></div>\n' +
            '\n' +
            '    </div>\n' +
            '</div>');

        // 报表信息加载
        for (i = 0; i < data.report_info_list.length; i++) {
            $("#report_info_submit").append('<div class="form-group">\n' +
                '    <label class="col-md-2 control-label">' + data.report_info_list[i].report_info_name + '</label>\n' +
                '    <div class="col-md-10">\n' + '<input hidden id="report_info_name_' + (i + 1) + '" type="text" name="report_info_name_' + (i + 1) + '" value="' + data.report_info_list[i].report_info_name + '">' +
                '<input hidden id="report_info_id_' + (i + 1) + '" type="text" name="report_info_id_' + (i + 1) + '" value="' + data.report_info_list[i].report_info_id + '">' +
                '        <input id="report_info_value_' + (i + 1) + '" type="text" name="report_info_value_' + (i + 1) + '" class="form-control " placeholder="" value="' + data.report_info_list[i].report_info_value + '">\n' +
                '        <div class="form-control-focus"></div>\n' +
                '    </div>\n' +
                '</div>')
        }

        $("#look").attr("href", "http://192.168.100.151:8075/webroot/decision/view/report?viewlet=" + data.file_name + "&curdate=" + $('#reporting_date').val())
    });
    $('#sample_1 tbody').on('click', 'button#delrow', function() {
        if (confirm("确定要删除该条发布数据？")) {
            var table = $('#sample_1').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../../report_submit_del/",
                data: {
                    id: data.id,
                    report_time: data.report_time,
                },
                success: function(data) {
                    if (data == 1) {
                        table.ajax.reload();
                        alert("删除成功！");
                    }
                    if (data == 2) {
                        alert("未创建，不需要删除");
                    }
                    if (data == 0) {
                        alert("删除失败，请于管理员联系。");
                    }
                },
                error: function(e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    // 默认
    var temp_date = $("#temp_date").val();
    var temp_json_date = JSON.parse(temp_date);
    $('#reporting_date').datetimepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
        startView: 2,
        minView: 2,
    });

    // 根据报表类型change
    $("#search_report_type").change(function() {
        $('#reporting_date').datetimepicker("remove");
        var report_type = $("#search_report_type").val();
        $('#reporting_date').val(temp_json_date[report_type]);

        if (report_type == "22") {
            $('#reporting_date').datetimepicker({
                format: 'yyyy-mm-dd',
                autoclose: true,
                startView: 2,
                minView: 2,
            });
            $('#report_time').datetimepicker({
                format: 'yyyy-mm-dd',
                autoclose: true,
                startView: 2,
                minView: 2,
            });
        }
        if (report_type == "23") {
            $('#reporting_date').datetimepicker({
                format: 'yyyy-mm',
                autoclose: true,
                startView: 3,
                minView: 3,
            });
            $('#reoprt_time').datetimepicker({
                format: 'yyyy-mm',
                autoclose: true,
                startView: 3,
                minView: 3,
            });
        }
        if (report_type == "24") {
            $('#reporting_date').datetimepicker({
                format: 'yyyy-mm',
                autoclose: true,
                startView: 3,
                minView: 3,
            });
            $('#report_time').datetimepicker({
                format: 'yyyy-mm',
                autoclose: true,
                startView: 3,
                minView: 3,
            });
        }
        if (report_type == "25") {
            $('#reporting_date').datetimepicker({
                format: 'yyyy-mm',
                autoclose: true,
                startView: 3,
                minView: 3,
            });
            $('#report_time').datetimepicker({
                format: 'yyyy-mm',
                autoclose: true,
                startView: 3,
                minView: 3,
            });
        }
        if (report_type == "26") {
            $('#reporting_date').datetimepicker({
                format: 'yyyy',
                autoclose: true,
                startView: 4,
                minView: 4,
            });
            $('#report_time').datetimepicker({
                format: 'yyyy',
                autoclose: true,
                startView: 4,
                minView: 4,
            });
        }
        var table01 = $('#sample_1').DataTable();
        table01.ajax.url("../../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_date=" + $('#reporting_date').val() + "&" + "search_report_type=" + $('#search_report_type').val()).load();
    });

    // 根据时间过滤报表
    $('#reporting_date').change(function() {
        var table02 = $('#sample_1').DataTable();

        table02.ajax.url("../../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_date=" + $('#reporting_date').val() + "&" + "search_report_type=" + $('#search_report_type').val()).load();
    });


    $("#save").click(function() {
        $("#post_type").val("");
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../report_submit_save/",
            data: $("#report_submit_form").serialize(),
            success: function(data) {
                var myres = data["res"];
                if (myres == "保存成功。") {
                    $('#static').modal('hide');
                    var table = $('#sample_1').DataTable();
                    table.ajax.url("../../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_date=" + $('#reporting_date').val() + "&" + "search_report_type=" + $('#search_report_type').val(), ).load();
                }
                alert(myres);
            },
            error: function(e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    });

    $("#submit_btn").click(function() {
        $("#post_type").val("submit")
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../report_submit_save/",
            data: $("#report_submit_form").serialize(),
            success: function(data) {
                var myres = data["res"];
                if (myres == "保存成功。") {
                    $('#static').modal('hide');
                    var table = $('#sample_1').DataTable();
                    table.ajax.url("../../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_date=" + $('#reporting_date').val() + "&" + "search_report_type=" + $('#search_report_type').val(), ).load();
                }
                alert(myres);
            },
            error: function(e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    });

    $('#error').click(function() {
        $(this).hide()
    })

});