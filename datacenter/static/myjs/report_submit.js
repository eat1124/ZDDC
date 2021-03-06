$(document).ready(function() {
    function seasonFunction(){
        renderSeasonDate(document.getElementById('season'), 1);
        function renderSeasonDate(ohd, sgl) {
            var ele = $(ohd);
            laydate.render({
                elem: ohd,
                type: 'month',
                format: 'yyyy-第M季度',
                range: sgl ? null : '~',
                min: "1900-1-1",
                max: "2999-12-31",
                btns: ['confirm'],
                ready: function () {
                    var hd = $("#layui-laydate" + ele.attr("lay-key"));
                    if (hd.length > 0) {
                        hd.click(function () {
                            ren($(this));
                        });
                    }
                    ren(hd);
                },

                done: function (value) {
                    var finaltime = '';
                    if (value){
                        value = value.split('-');
                        var year = value[0];
                        var season = value[1];
                        if (season == '第1季度'){
                            var timeend = '03-31';
                            finaltime =  year + '-' + timeend;
                        }
                        if (season == '第2季度'){
                            var timeend = '06-30';
                            finaltime =  year + '-' + timeend
                        }
                        if (season == '第3季度'){
                            var timeend = '09-30';
                            finaltime = year + '-' + timeend
                        }
                        if (season == '第4季度'){
                            var timeend = '12-31';
                            finaltime = year + '-' + timeend
                        }
                    }
                    $('#reporting_date').val(finaltime);
                    var table02 = $('#sample_1').DataTable();
                    table02.ajax.url("../../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_date=" + $('#reporting_date').val() + "&" + "search_report_type=" + $('#search_report_type').val()).load();

                }

            });
            var ren = function (thiz) {
                var mls = thiz.find(".laydate-month-list");
                mls.each(function (i, e) {
                    $(this).find("li").each(function (inx, ele) {
                        var cx = ele.innerHTML;
                        if (inx < 4) {
                            ele.innerHTML = cx.replace(/月/g, "季度").replace(/一/g, "第1").replace(/二/g, "第2").replace(/三/g, "第3").replace(/四/g, "第4");
                        } else {
                            ele.style.display = "none";
                        }
                    });
                });
            }
        }
    }

    function yearFunction(){
        renderYearDate(document.getElementById('year'), 1);
        function renderYearDate(ohd, sgl) {
            var ele = $(ohd);
            laydate.render({
                elem: ohd,
                type: 'month',
                format: 'yyyy-h半年',
                range: sgl ? null : '~',
                min: "1900-1-1",
                max: "2999-12-31",
                btns: [ 'confirm'],
                ready: function () {
                    var hd = $("#layui-laydate" + ele.attr("lay-key"));
                    if (hd.length > 0) {
                        hd.click(function () {
                            ren($(this));
                        });
                    }
                    ren(hd);
                },

                done: function (value) {
                    var finaltime = '';
                    if (value){
                        value = value.split('-');
                        var year = value[0];
                        var halfyear = value[1];

                        if (halfyear == '上半年'){
                            var timeend = '06-30';
                            finaltime = year + '-' + timeend
                        }
                        if (halfyear == '下半年'){
                            var timeend = '12-31';
                            finaltime = year + '-' + timeend
                        }
                    }
                    $('#reporting_date').val(finaltime);
                        var table02 = $('#sample_1').DataTable();
                        table02.ajax.url("../../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_date=" + $('#reporting_date').val() + "&" + "search_report_type=" + $('#search_report_type').val()).load();

                }

            });
            var ren = function (thiz) {
                var mls = thiz.find(".laydate-month-list");
                mls.each(function (i, e) {
                    $(this).find("li").each(function (inx, ele) {
                        var cx = ele.innerHTML;
                        if (inx < 2) {
                            cx = cx.replace(/月/g, "半年");
                            ele.innerHTML = cx.replace(/一/g, "上").replace(/二/g, "下");

                        } else {
                            ele.style.display = "none";
                        }
                    });
                });
            }
        }
    }
    var temp_date = $("#temp_date").val();
    var temp_json_date = JSON.parse(temp_date);
    function customTimePicker(report_type){
        $('#reporting_date').val(temp_json_date[report_type]);

        if (report_type == "22") {
            $('#year').hide();
            $('#season').hide();
            $('#reporting_date').show();
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
            $('#year').hide();
            $('#season').hide();
            $('#reporting_date').show();
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
            seasonFunction();
            $('#reporting_date').hide();
            $('#year').hide();

            var reporting_date = $('#reporting_date').val();
            var value = reporting_date.split('-');
            var year = value[0];
            var month = value[1];
            var finaltime = '';
            if (month == '12'){
                var timeend = '第4季度';
                finaltime = year + '-' + timeend
            }
            if (month == '09'){
                var timeend = '第3季度';
                finaltime = year + '-' + timeend
            }
            if (month == '06'){
                var timeend = '第2季度';
                finaltime = year + '-' + timeend
            }
            if (month == '03'){
                var timeend = '第1季度';
                finaltime = year + '-' + timeend
            }
            $('#season').val(finaltime);
            $('#season').show();
        }
        if (report_type == "25") {
            yearFunction();
            $('#reporting_date').hide();
            $('#season').hide();

            var reporting_date = $('#reporting_date').val();
            var value = reporting_date.split('-');
            var year = value[0];
            var month = value[1];
            var finaltime = '';
            if (month == '12'){
                var timeend = '下半年';
                finaltime = year + '-' + timeend
            }
            if (month == '06'){
                var timeend = '上半年';
                finaltime = year + '-' + timeend
            }
            $('#year').val(finaltime);
            $('#year').show();
        }
        if (report_type == "26") {
            $('#year').hide();
            $('#season').hide();
            $('#reporting_date').show();
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
    }
    var selected_report_type = $("#selected_report_type").val();

    try {
        if (selected_report_type){
            $('#search_report_type').val(selected_report_type);
            customTimePicker(selected_report_type);
        }
    } catch(e){}

    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "iDisplayLength": 25,
        "bProcessing": true,
        "ajax": "../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_date=" + $('#reporting_date').val() + "&" + "search_report_type=" + $('#search_report_type').val(),
        "columns": [
            {"data": "id"},
            { "data": "id" },
            { "data": "name" },
            { "data": "code" },
            { "data": "state" },
            { "data": null }
        ],

        "columnDefs": [{
                "targets": 0,
                "mRender": function (data, type, full) {
                    return "<input id='select_tmp_" + full.id + "' name='selecttmp' type='checkbox' class='checkboxes' value='" + data + "'/>"
                }
            },
            {
            "targets": -4,
            "mRender": function(data, type, full) {
                var reporting_date = $('#reporting_date').val();
                // 月报
                if (full.report_type_id == 23){
                     var curYear = reporting_date.split("-") [0];
                     var curMonth = reporting_date.split("-") [1];
                     return "<a href='http://" + full.report_server + "/webroot/decision/view/report?viewlet=" + full.relative_file_name +
                        "&curYear=" + curYear + "&curMonth=" + curMonth  + "&op=write" + "' target='_blank'>" + full.name + "</a>"
                }
                // 季报
                if (full.report_type_id == 24){
                    // 2020
                    var curYear = reporting_date.split("-") [0];
                    // 03
                    var season = reporting_date.split("-") [1];
                    var curSeason = '';
                    if (season == '03'){
                        curSeason = 1
                    }
                    else if (season == '06'){
                        curSeason = 2
                    }
                    else if (season == '09'){
                        curSeason = 3
                    }
                    else {
                        curSeason = 4
                    }
                     return "<a href='http://" + full.report_server + "/webroot/decision/view/report?viewlet=" + full.relative_file_name +
                        "&curYear=" + curYear + "&curSeason=" + curSeason  + "&op=write" + "' target='_blank'>" + full.name + "</a>"
                }
                // 半年报
                if (full.report_type_id == 25){
                    // 2020
                    var curYear = reporting_date.split("-") [0];
                    // 06
                    var halfyear = reporting_date.split("-") [1];
                    var curHalfyear = '';
                    if (halfyear == '06'){
                        curHalfyear = '上'
                    }else {
                        curHalfyear = '下'
                    }
                    return "<a href='http://" + full.report_server + "/webroot/decision/view/report?viewlet=" + full.relative_file_name +
                        "&curYear=" + curYear + "&curHalfyear=" + curHalfyear  + "&op=write" + "' target='_blank'>" + full.name + "</a>"
                }
                // 年报
                if (full.report_type_id == 26){
                    // 2020
                    var curYear = reporting_date.split("-") [0];
                    return "<a href='http://" + full.report_server + "/webroot/decision/view/report?viewlet=" + full.relative_file_name +
                        "&curYear=" + curYear + "&op=write" + "' target='_blank'>" + full.name + "</a>"
                }
                // 日报
                else {
                    return "<a href='http://" + full.report_server + "/webroot/decision/view/report?viewlet=" + full.relative_file_name +
                    "&curdate=" + $('#reporting_date').val()  + "&op=write" + "' target='_blank'>" + full.name + "</a>"
                }
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
            '            style="color:red; "></span>制表日期</label>\n' +
            '    <div class="col-md-4">\n' +
            '        <input id="write_time" type="date" name="write_time" autocomplete="off" class="form-control "\n' +
            '               placeholder="" value="' + data.write_time + '">\n' +
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
                '        <textarea class="form-control" placeholder=""  id="report_info_value_' + (i + 1) + '" name="report_info_value_' + (i + 1) + '">' + data.report_info_list[i].report_info_value + '</textarea>\n' +
                '        <div class="form-control-focus"></div>\n' +
                '    </div>\n' +
                '</div>')
        }

        $("#look").attr("href", "http://" + data.report_server +  "/webroot/decision/view/report?viewlet=" + data.relative_file_name + "&curdate=" + $('#reporting_date').val())
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
    $('#reporting_date, #write_time, #all_write_time').datetimepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
        startView: 2,
        minView: 2,
    });

    /**
     *  根据报表类型change
     *      seleced_report_type：
     */
    $("#search_report_type").change(function() {
        importData = [];
        $('#reporting_date').datetimepicker("remove");
        var report_type = $("#search_report_type").val();
        customTimePicker(report_type);
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
                    table.ajax.url("../../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_date=" + $('#reporting_date').val() + "&" + "search_report_type=" + $('#search_report_type').val()).load();
                }
                alert(myres);
            },
            error: function(e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    });

    $("#submit_btn").click(function() {
        $("#post_type").val("submit");
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
                    table.ajax.url("../../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_date=" + $('#reporting_date').val() + "&" + "search_report_type=" + $('#search_report_type').val()).load();
                }
                alert(myres);
            },
            error: function(e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    });

    // 选中导入指标
    var importData = [];
    $('#sample_1 tbody').on('click', 'input[name="selecttmp"]', function () {
        if ($(this).prop('checked')) {
            importData.push($(this).val());
        } else {
            for (var i = 0; i < importData.length; i++) {
                if (importData[i] == $(this).val()) {
                    importData.splice(i, 1);
                }
            }
        }
    });

    // 全选报表
    $('#select_all_tmp').click(function () {
        var table = $('#sample_1').DataTable().data();
        if (importData.length < 1){
            $.each(table, function (i, item) {
                $('#select_tmp_' + item.id).prop('checked',true);
                if ($('#select_tmp_' + item.id).prop('checked')){
                    if (importData.indexOf(item.id) == -1){
                        importData.push(item.id)
                    }
                }
            });
        }else {
            $.each(table, function (i, item) {
                $('#select_tmp_' + item.id).prop('checked',false);
                if ($('#select_tmp_' + item.id).prop('checked') == false){
                    for (var i = 0; i < importData.length; i++) {
                        if (importData[i] == $('#select_tmp_' + item.id).val()) {
                            importData.splice(i, 1);
                        }
                    }
                }
            });
            importData = [];
        }
    });

    // 选择制表日期
    $("#release_all_tmp").click(function() {
        if (importData.length < 1) {
            alert("请至少选择一张报表。");
        } else {
            $("#select_write_time").modal("show")
        }
    });

    // 发布所有报表
    $("#release_all_report").click(function() {
        var report_type = $("#search_report_type").val();
        var report_time = $("#reporting_date").val();
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../report_submit_all_tmp/",
            data:
                {
                    app: $('#app').val(),
                    report_type: report_type,
                    report_time: report_time,
                    write_time: $("#all_write_time").val(),
                    report_model_list: JSON.stringify(importData),
                },
            success: function(data) {
                var myres = data["res"];
                if (myres == "发布成功。") {
                    importData = [];
                    $("#select_write_time").modal("hide");
                    var table = $('#sample_1').DataTable();
                    table.ajax.url("../../../report_submit_data/?search_app=" + $('#app').val() + "&" + "search_date=" + $('#reporting_date').val() + "&" + "search_report_type=" + $('#search_report_type').val()).load();
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
    });
});