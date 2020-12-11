

$(document).ready(function () {

    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "iDisplayLength": 25,
        "bProcessing": true,
        "ajax": "../reporting_log_data?start_time=" + $('#start_time').val() + "&end_time=" + $('#end_time').val(),
        "columns": [
            {"data": "id"},
            {"data": "user"},
            {"data": "write_time"},
            {"data": "log"},

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
        autoclose: true,
        minView: "month",
        format: 'yyyy-mm-dd',
    });

    $('#end_time').datetimepicker({
        autoclose: true,
        minView: "month",
        format: 'yyyy-mm-dd',
    });

    $('#start_time,#end_time').change(function () {
        var table = $('#sample_1').DataTable();
        table.ajax.url("../reporting_log_data?start_time=" + $('#start_time').val() + "&end_time=" + $('#end_time').val()).load();
    });

});


