$(document).ready(function () {
    $('#sample_process_monitor').dataTable({
        "searching": false,
        "paging": false,
        "info": false,
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": false,
        "ajax": "../process_monitor_data/",
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "code"},
            {"data": "sourcetype_name"},
            {"data": "create_time"},
            {"data": "last_time"},
            {"data": "status"},
            {"data": "source_type_list"},
            {"data": null}
        ],

        "columnDefs": [{
            "targets": -2,
            "visible": false,
        },{
            "targets": -1,
            "data": null,
            "width": "100px", // fa fa-power-off
            "defaultContent": "<button  id='create' title='启动' class='btn btn-xs btn-primary' type='button'><i class='fa fa-play'></i></button><button title='关闭'  id='destroy' class='btn btn-xs btn-primary' type='button'><i class='fa fa-stop'></i></button><button title='编辑'  id='edit'  data-toggle='modal'  data-target='#static'   class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>"
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
    $('#sample_process_monitor tbody').on('click', 'button#edit', function () {
        var table = $('#sample_process_monitor').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#id").val(data.id);
        $("#name").val(data.name);
        $("#code").val(data.code);
        $("#sourcetype").empty();
        for (i = 0; i <= data.source_type_list.length; i++) {
            $("#sourcetype").append('<option value="' + data.source_type_list[i].source_type_id + '" ' + data.source_type_list[i].source_if_selected + '>\n' +
            data.source_type_list[i].source_type + '</option>');
        }


    });
    $('#sample_process_monitor tbody').on('click', 'button#create', function () {
        if (confirm("确定要启动该程序吗？")) {
            var table = $('#sample_process_monitor').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../process_run/",
                data: {
                    id: data.id,
                },
                success: function (data) {
                    var myres = data["res"];
                    if (myres === "程序启动成功。") {
                        table.ajax.reload();
                    }
                    alert(myres);
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });

        }
    });
    $('#sample_process_monitor tbody').on('click', 'button#destroy', function () {
        if (confirm("确定要终止该进程吗？")) {
            var table = $('#sample_process_monitor').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../process_destroy/",
                data: {
                    id: data.id,
                },
                success: function (data) {
                    var myres = data["res"];
                    if (myres === "程序终止成功。") {
                        table.ajax.reload();
                    }
                    alert(myres);
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }
    });

    $('#save').click(function () {
        var table = $('#sample_process_monitor').DataTable();

        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../create_process/",
            data: {
                id: $("#id").val(),
                name: $("#name").val(),
                code: $("#code").val(),
                sourcetype: $("#sourcetype").val(),
            },
            success: function (data) {
                var myres = data["res"];
                if (myres == "保存成功。") {
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

    // setInterval(function () {
    //     var table = $('#sample_process_monitor').DataTable();
    //     table.ajax.reload();
    //     console.log("refresh")
    // }, 2000);

    // var end = false;

    // function customOurInterval() {
    //     // body...
    //     setTimeout(function() {
    //         // do something 定时任务
    //         // 处理时对end标志进行修改，end=True表示停止（取消定时器）。
    //         console.log("refresh");
    //         if (window.location.href.indexOf("process_monitor") != -1) {
    //             var table = $('#sample_process_monitor').DataTable();
    //             table.ajax.reload();
    //             end = false
    //         } else {
    //             end = true
    //         }

    //         if (!end) {
    //             // 循环(arguments.callee获取当前执行函数的引用)
    //             setTimeout(arguments.callee, 2000);
    //         } else {
    //             end = false;
    //         }
    //     }, 2000);
    // }

    // customOurInterval();

});