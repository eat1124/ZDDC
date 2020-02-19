$(document).ready(function () {
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../cycle_data/",
        "columns": [
            {"data": "id"},
            {"data": "name"},
            // 周期类型
            {"data": "schedule_type_display"},
            // 周期时间
            {"data": null},
            {"data": "sort"},
            {"data": null}
        ],

        "columnDefs": [{
            "data": null,
            "targets": -3,
            "render": function (data, type, full) {
                /*
                    日：
                        00:00
                    周：
                        00:00 周六
                    月：
                        00:00 第2天(月)
                 */
                var time = full.hours + ":" + full.minutes;
                var week_map = {1: "周日", 2: "周一", 3: "周二", 4: "周三", 5: "周四", 6: "周五", 7: "周六"};
                var per_week = week_map[full.per_week];
                var per_month = full.per_month;

                if (full.schedule_type == 2) {
                    time += " " + per_week;
                }
                if (full.schedule_type == 3) {
                    time += " 第" + per_month + "天(月)";
                }
                return "<td>" + time + "</td>"
            },
        },{
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
        $("#sort").val(data.sort);

        $("#schedule_type").val(data.schedule_type);

        if (data.schedule_type == 1) {
            $("#per_week_div").hide();
            $("#per_month_div").hide();
        }
        if (data.schedule_type == 2) {
            $("#per_week").val(1);
            $("#per_week_div").show();
            $("#per_month_div").hide();
        }
        if (data.schedule_type == 3) {
            $("#per_month").val(1);
            $("#per_week_div").hide();
            $("#per_month_div").show();
        }


        var per_time = data.hours + ":" + data.minutes;
        $("#per_time").val(per_time).timepicker("setTime", per_time);
        $("#per_week").val(data.per_week != "" ? data.per_week : "").trigger("change");
        $("#per_month").val(data.per_month != "" ? data.per_month : "").trigger("change");

    });

    $("#new").click(function () {
        $("#id").val("0");
        $("#cycle_name").val("");
        $("#minutes").val("");
        $("#create_date").val("");
        $("#sort").val("");


        $("#per_time").val("00:00").timepicker("setTime", "00:00");
        $("#per_week").val("").trigger("change");
        $("#per_month").val("").trigger("change");
        $("#schedule_type").val("");
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
                minutes: $("#minutes").val(),
                create_date: $("#create_date").val(),
                sort: $("#sort").val(),

                schedule_type: $("#schedule_type").val(),
                per_time: $("#per_time").val(),
                per_week: $("#per_week").val(),
                per_month: $("#per_month").val(),
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

    $("#schedule_type").change(function () {
        var schedule_type = $(this).val();
        if (schedule_type == 1) {
            $("#per_week_div").hide();
            $("#per_month_div").hide();
        }
        if (schedule_type == 2) {
            $("#per_week").val(1);
            $("#per_week_div").show();
            $("#per_month_div").hide();
        }
        if (schedule_type == 3) {
            $("#per_month").val(1);
            $("#per_week_div").hide();
            $("#per_month_div").show();
        }
    });


    // time-picker
    $("#per_time").timepicker({
        showMeridian: false,
        minuteStep: 5,
    }).on('show.timepicker', function () {
        $('#static').removeAttr('tabindex');
    }).on('hide.timepicker', function () {
        $('#static').attr('tabindex', -1);
    });
});