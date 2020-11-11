$(document).ready(function () {
    $('#start_date').datetimepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
        startView: 2,
        minView: 2,
    });
    $('#end_date').datetimepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
        startView: 2,
        minView: 2,
    });

    function get_target_search_data(target, start_date, end_date){
        $.ajax({
            type: "POST",
            dataType: "JSON",
            url: "../../get_target_search_data/",
            data: {
                target: $('#target').val(),
                start_date: $("#start_date").val(),
                end_date: $("#end_date").val(),
                app_id: $("#app_id").val(),
            },
            success: function (data) {
                if (data.status == 1){
                    $("#form_div").show();
                    loadSearchDataTable(data.data);
                } else {
                    alert(data.info);
                }
            }
        })
    }
    function loadSearchDataTable(data) {
        $("#search_table").dataTable().fnDestroy();
        $('#search_table').dataTable({
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "data": data,
            "columns": [
                {"data": "name"},
                {"data": "code"},
                {"data": "curvalue"},
                {"data": "time"}
            ],
            "columnDefs": [],
            "oLanguage": {
                "sLengthMenu": "每页显示 _MENU_ 条记录",
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
    }

    $("#search").click(function () {
        get_target_search_data();
    })
});
