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
                return "<a href='?file_name=\"" + full.file_name + "\"&date=\"" + full.write_time + "\"'>" + full.name + "</a>"
            }
        }, {
            "targets": -2,
            "mRender": function(data, type, full) {
                if (full.state == "1") {
                    return "<span style='color:green;'>" + full.state_desc + "</span>"
                }
                if (full.state == "0") {
                    return "<span style='color:yellow;'>" + full.state_desc + "</span>"
                }
                if (full.state == "") {
                    return "<span style='color:red;'>" + full.state_desc + "</span>"
                }
            }
        }, {
            "targets": -1,
            "data": null,
            "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>",
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
        // 报表信息加载
        $("#report_info_submit").empty();
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
        // 填报人/填报时间
        $("#report_info_submit").append('<div class="form-group">\n' +
            '        <label class="col-md-2 control-label">' + "填报人" + '</label>\n' +
            '        <div class="col-md-10">\n' +
            '            <input id="person" type="text" name="person" class="form-control "\n' +
            '                   placeholder="" value="' + data.person + '" readonly>\n' +
            '            <div class="form-control-focus"></div>\n' +
            '        </div>\n' +
            '    </div>\n' +
            '    <div class="form-group">\n' +
            '        <label class="col-md-2 control-label">更新日期</label>\n' +
            '        <div class="col-md-10">\n' +
            '            <input id="write_time" type="text" name="write_time" class="form-control "\n' +
            '                   placeholder="" value="' + data.write_time + '" readonly>\n' +
            '            <div class="form-control-focus"></div>\n' +
            '        </div>\n' +
            '    </div>');
        // 报表时间

        // 未创建时的报表时间
        var report_time = data.report_time;
        if (report_time) {
            //..
        } else {
            report_time = $("#reporting_date").val();
        }
        $("#report_info_submit").append('    <div class="form-group">\n' +
            '        <label class="col-md-2 control-label">报表时间</label>\n' +
            '        <div class="col-md-10">\n' +
            '            <input id="report_time" type="datetime" name="report_time" class="form-control "\n' +
            '                   placeholder="" autocomplete="off"  value="' + report_time + '">\n' +
            '            <div class="form-control-focus"></div>\n' +
            '        </div>\n' +
            '    </div>');

        var report_type = $("#search_report_type").val();
        $('#reporting_date').val(temp_json_date[report_type]);

        if (report_type == "22") {
            $('#report_time').datetimepicker({
                format: 'yyyy-mm-dd',
                autoclose: true,
                startView: 2,
                minView: 2,
            });
        }
        if (report_type == "23") {
            $('#report_time').datetimepicker({
                format: 'yyyy-mm',
                autoclose: true,
                startView: 3,
                minView: 3,
            });
        }
        if (report_type == "24") {
            $('#report_time').datetimepicker({
                format: 'yyyy-mm',
                autoclose: true,
                startView: 3,
                minView: 3,
            });
        }
        if (report_type == "25") {
            $('#report_time').datetimepicker({
                format: 'yyyy-mm',
                autoclose: true,
                startView: 3,
                minView: 3,
            });
        }
        if (report_type == "26") {
            $('#report_time').datetimepicker({
                format: 'yyyy',
                autoclose: true,
                startView: 4,
                minView: 4,
            });
        }
    });

    // 默认
    var temp_date = $("#temp_date").val();
    var temp_json_date = JSON.parse(temp_date);
    $('#reporting_date').val(temp_json_date["22"]);
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
        table01.ajax.url("../../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_report_type=" + $('#search_report_type').val(), ).load();
    });

    // 根据时间过滤报表
    $('#reporting_date').change(function() {
        var table02 = $('#sample_1').DataTable();
        table02.ajax.url("../../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_date=" + $('#reporting_date').val() + "&" + "search_report_type=" + $('#search_report_type').val(), ).load();
    });


    var url = window.location.href;

    $("#save").click(function() {
        $("#report_submit_form").attr("action", url);
        $("#report_submit_form").submit();
    });

    $("#submit_btn").click(function() {
        $("#post_type").val("submit")
        $("#report_submit_form").attr("action", url);
        $("#report_submit_form").submit();
    });

    $('#error').click(function() {
        $(this).hide()
    })
});