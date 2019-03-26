$(document).ready(function () {
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../cycle_data/",
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "code"},
            {"data": "minutes"},
            {"data": "create_date"},
            {"data": "sort"},
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
        if (confirm("确定要删除该条数据？")) {
            var table = $('#sample_1').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../cycle_del/",
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
        $("#cycle_name").val(data.name);
        $("#cycle_code").val(data.code);
        $("#minutes").val(data.minutes);
        $("#create_date").val(data.create_date);
        $("#sort").val(data.sort);
    });

    $("#new").click(function () {
        $("#id").val("0");
        $("#cycle_name").val("");
        $("#cycle_code").val("");
        $("#minutes").val("");
        $("#create_date").val("");
        $("#sort").val("");
    });

    $('#save').click(function () {
        var table = $('#sample_1').DataTable();

        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../cycle_save/",
            data: {
                id: $("#id").val(),
                cycle_name: $("#cycle_name").val(),
                cycle_code: $("#cycle_code").val(),
                minutes: $("#minutes").val(),
                create_date: $("#create_date").val(),
                sort: $("#sort").val(),
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
    });

    $('#error').click(function () {
        $(this).hide()
    });
    $('#create_date').datetimepicker({
        autoclose: true,
        format: 'yyyy-mm-dd hh:ii',
    });
});