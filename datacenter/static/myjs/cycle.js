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
                var sub_cycle_data = full.sub_cycle_data,
                    schedule_type = full.schedule_type;

                var sub_cycle_points = ''
                for (var i=0; i< sub_cycle_data.length; i++){
                    var hours = sub_cycle_data[i]['hours'],
                        minutes = sub_cycle_data[i]['minutes'],
                        per_week = sub_cycle_data[i]['per_week'],
                        per_month = sub_cycle_data[i]['per_month'];
                    var per_time = hours + ":" + minutes;
                    var sub_cycle_point = getSubCyclePoint(schedule_type, per_time, per_week, per_month);
                    sub_cycle_points += sub_cycle_point + ","
                }
                if (sub_cycle_points.endsWith(',')){
                    sub_cycle_points = sub_cycle_points.slice(0, -1);
                }

                return "<td>" + sub_cycle_points + "</td>"
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
        var subCycleData = data.sub_cycle_data;

        sub_cycle_data = [];
        for (var i=0; i< subCycleData.length; i++){
            var per_time = subCycleData[i]["hours"] + ":" + subCycleData[i]["minutes"],
                per_week = subCycleData[i]["per_week"],
                per_month = subCycleData[i]["per_month"],
                hours = subCycleData[i]["hours"],
                minutes = subCycleData[i]["minutes"],
                sub_cycle_id = subCycleData[i]["sub_cycle_id"]

            var sub_cycle_point = getSubCyclePoint(data.schedule_type, per_time, per_week, per_month);
            sub_cycle_data.push([sub_cycle_id, sub_cycle_point, hours, minutes, per_week, per_month])
            loadSubCycleData();
        }
    });

    $("#new").click(function () {
        $("#id").val("0");
        $("#cycle_name").val("");
        $("#minutes").val("");
        $("#create_date").val("");
        $("#sort").val("");

        $("#schedule_type").val("1");
    });

    $('#save').click(function () {
        var table = $('#sample_1').DataTable();
        var cycle_point = $('#cycle_point_table').DataTable();
        var cycle_point_data = cycle_point.data();
        var sub_cycle = []
        for (var i=0; i< cycle_point_data.length; i++){
            sub_cycle.push({
                "sub_cycle_id": cycle_point_data[i][0]?cycle_point_data[i][0]:0,
                "hours": cycle_point_data[i][2]?cycle_point_data[i][2]:"",
                "minutes": cycle_point_data[i][3]?cycle_point_data[i][3]:"",
                "per_week": cycle_point_data[i][4]?cycle_point_data[i][4]:"",
                "per_month": cycle_point_data[i][5]?cycle_point_data[i][5]:""
            });
        }

        sub_cycle = JSON.stringify(sub_cycle)
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
                sub_cycle: sub_cycle
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

    // time-picker
    $("#per_time").timepicker({
        showMeridian: false,
        minuteStep: 5,
    }).on('show.timepicker', function () {
        $('#static').removeAttr('tabindex');
    }).on('hide.timepicker', function () {
        $('#static').attr('tabindex', -1);
    });

    // 子周期
    $('#static1').on("show.bs.modal", function(){
        var schedule_type = $('#schedule_type').val();

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
            $("#per_week_div").hide();
            $("#per_month_div").show();
        }
    });

    $('#cycle_point_new').click(function(){
        $('#sub_cycle_id').val('0');
        $("#per_time").val("00:00").timepicker("setTime", "00:00");
        $("#per_week").val("").trigger("change");
        $("#per_month").val("").trigger("change");
    });

    function getSubCyclePoint(schedule_type, per_time, per_week, per_month){
        var sub_cycle_point = "";
        if (schedule_type == 1) {  // day
            sub_cycle_point = "每日" + per_time;
        }
        if (schedule_type == 2) {  // week
            sub_cycle_point = "每周" + per_week + " " + per_time;
        }
        if (schedule_type == 3) {  // month
            sub_cycle_point = "每月第" + per_month + "天" + " " + per_time;
        }
        return sub_cycle_point
    }

    $('#load').click(function(){
        var table = $('#cycle_point_table').DataTable(),
            sub_cycle_id = $('#sub_cycle_id').val(),
            schedule_type = $('#schedule_type').val(),
            per_time = $("#per_time").val(),
            per_week = $("#per_week").val(),
            per_month = $("#per_month").val();
        var hours = "",
            minutes = "";
        var per_time_list = per_time.split(":");
        hours = per_time_list[0].trim();
        minutes = per_time_list[1].trim();

        // 构造时间点
        var sub_cycle_point = getSubCyclePoint(schedule_type, per_time, per_week, per_month);
        if (sub_cycle_id == 0){  // 新增 整合 日 周 月
            var load_list = ['暂无', sub_cycle_point, hours, minutes, per_week, per_month];
            table.row.add(load_list).draw();

            // 飘红
            table.rows().eq(0).each(function (index) {
                var row = table.row(index).node();
                if ($(row).find('td').eq(0).text().trim() == '暂无') {
                    $(row).css('color', 'red');
                }
            });
            $('#static1').modal('hide');
        } else {  // 修改
            // 修改时，直接修改当前行，除本身外不得重复
            table.rows().eq(0).each(function (index) {
                if (index == $('#edit_row').val()) {
                    var dataNode = table.row(index);
                    dataNode.data([sub_cycle_id, sub_cycle_point, hours, minutes, per_week, per_month]).draw();
                    $('#static1').modal('hide');
                }
            });
            $('#static1').modal('hide');
        }

    });
    var sub_cycle_data = [];
    $('#static').on('show.bs.modal', function () {
        if ($('#id').val() == '0') {
            sub_cycle_data = [];
        }
        loadSubCycleData();
    });

    function loadSubCycleData(){
        $('#cycle_point_table').dataTable().fnDestroy();
        $('#cycle_point_table').dataTable({
            "destory": true,
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "data": sub_cycle_data,
            "columns": [
                {"title": "序号"},
                {"title": "时间点"},  // 展示
                {"title": "时"},
                {"title": "分"},
                {"title": "周"},
                {"title": "月"},
                {"title": "操作"}
            ],
            "columnDefs": [{
                "targets": -5,
                "visible": false,
            }, {
                "targets": -4,
                "visible": false,
            }, {
                "targets": -3,
                "visible": false,
            }, {
                "targets": -2,
                "visible": false,
            }, {
                "targets": -1,
                "data": null,
                "defaultContent": "<button  id='edit_cycle_point' title='编辑' data-toggle='modal'  data-target='#static1'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>" +
                    "<button title='删除'  id='del_cycle_point' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>"
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
            },
        });
    }
    $('#cycle_point_table tbody').on('click', 'button#del_cycle_point', function () {
        var table = $('#cycle_point_table').DataTable();
        table.row($(this).parents('tr')).remove().draw();
    });
    $('#cycle_point_table tbody').on('click', 'button#edit_cycle_point', function () {
        var table = $('#cycle_point_table').DataTable();
        var dataNode = table.row($(this).parents('tr'));
        var data = dataNode.data();
        table.rows().eq(0).each(function (index) {
            var row = table.row(index).node();
            if (index == dataNode.index()) {
                var hours = data[2],
                    minutes = data[3],
                    per_week = data[4],
                    per_month = data[5];

                var per_time = hours + ":" + minutes;
                $("#sub_cycle_id").val(data[0]);
                $("#per_time").val(per_time).timepicker("setTime", per_time);
                $("#per_week").val(per_week != "" ? per_week : "").trigger("change");
                $("#per_month").val(per_month != "" ? per_month : "").trigger("change");
                return false;
            }
        });
        // 写入修改的是第几行
        $('#edit_row').val(dataNode.index())
    });
    $('#schedule_type').change(function(){
        sub_cycle_data = [];
        loadSubCycleData();
    });
});