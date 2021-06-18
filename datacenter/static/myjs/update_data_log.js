

$(document).ready(function () {

    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "iDisplayLength": 25,
        "bProcessing": true,
        "ajax": "../../update_data_log_data?start_time=" + $('#start_time').val() + "&end_time=" + $('#end_time').val() + "&adminapp=" + $('#adminapp').val(),
        "columns": [
            {"data": "id"},
            {"data": "target_name"},
            // {"data": "operationtype"},
            {"data": "datadate"},
            {"data": "user"},
            {"data": "write_time"},
            {"data": "work"},
            {"data": "before_curvalue"},
            {"data": "after_curvalue"}
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

    $('#start_time').datetimepicker({
            format: 'yyyy-mm',
            autoclose: true,
            startView: 3,
            minView: 3,
    });
    $('#end_time').datetimepicker({
        format: 'yyyy-mm',
        autoclose: true,
        startView: 3,
        minView: 3,
    });

    $('#start_time,#end_time').change(function () {
        var table = $('#sample_1').DataTable();
        table.ajax.url("../../update_data_log_data?start_time=" + $('#start_time').val() + "&end_time=" + $('#end_time').val() + "&adminapp=" + $('#adminapp').val()).load();
    });

});


