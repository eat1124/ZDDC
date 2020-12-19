function getSearchStatistic() {
    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../../target_statistic_data/",
        data: {},
        success: function (data) {
            var table_data = data.data,
                status = data.status,
                info = data.info;
            if (status == 1) {
                renderStatisticDataTable(table_data);
            }
        }
    });
}

function renderStatisticDataTable(table_data) {
    $('#search_table').dataTable().fnDestroy();
    $('#search_table').dataTable({
        "ordering": true,
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "data": table_data,
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "type_name"},
            {"data": "remark"},
            {"data": null}
        ],
        "columnDefs": [{
            "targets": -1,
            "width": "80px",
            "data": null,
            "mRender": function (data, type, full) {
                var date_type = data.type;
                var search_id = full.id;
                var href = '/statistic_report/?search_id=' + search_id + "&date_type=" + date_type;
                return "<button id='edit' title='编辑' data-toggle='modal'  data-target='#static01'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>" +
                    "<button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>" +
                    "<a href='" + href + "' title='查看报表' target='_blank' class='btn btn-xs btn-primary' type='button'><i class='fa fa-external-link'></i></a>";
            }
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
    $('#search_table tbody').on('click', 'button#edit', function () {
        var table = $('#search_table').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#search_statistic_id").val(data.id);
        $("#search_name").val(data.name);
        $("#search_type").val(data.type);
        $("#search_remark").val(data.remark);
        // 指标列dataTable
        renderTargetColDataTable(data.target_col);
    });
    $('#search_table tbody').on('click', 'button#delrow', function () {
        if (confirm("确定要删除该条发布数据？")) {
            var table = $('#search_table').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../../target_statistic_del/",
                data: {
                    id: data.id,
                },
                success: function (data) {
                    if (data.status == 1) {
                        table.ajax.url("../../target_statistic_data/").load();
                        alert("删除成功！");
                    }
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
}

function renderTargetColDataTable(table_data) {
    $('#col_table').dataTable().fnDestroy();
    $('#col_table').dataTable({
        "ordering": false,
        "bAutoWidth": false,
        "bSort": false,
        "bProcessing": true,
        "searching": false,
        "bLengthChange": false,
        "info": false, //去左下角
        "paging": false,  //去右下角
        "data": table_data,
        "columns": [
            {"data": "name"},
            {"data": "statistic_type"},
            {"data": null},
            {"data": null}
        ],
        "columnDefs": [{
            "targets": -4,
            "width": "20%",
        }, {
            "targets": -2,
            "width": "55%",
            "mRender": function (data, type, full) {
                var targets = full.targets;
                var targets_td = "";
                for (var i = 0; i < targets.length; i++) {
                    targets_td += targets[i].new_target_name + ",";
                }
                targets_td = targets_td.endsWith(",") ? targets_td.slice(0, -1) : targets_td;

                return targets_td;
            }
        }, {
            "targets": -1,
            "data": null,
            "width": "15%",
            "defaultContent": "<button id='edit' title='编辑' data-toggle='modal'  data-target='#static02'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>",
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
        },
        "fnDrawCallback": function (oSettings) {  // 移除首列默认的排序图标
            $("#col_table thead th:first").removeClass("sorting_asc");
        }
    });
    $('#col_table tbody').on('click', 'button#edit', function () {
        var table = $('#col_table').DataTable();
        var data = table.row($(this).parents('tr')).data();
        // 预先清空
        $('#new_target').empty();
        $("#col_id").val(table.row($(this).parents('tr')).index() + 1);
        $("#col_name").val(data.name);
        $("#statistic_type").val(data.statistic_type);
        $("#col_remark").val(data.remark);

        var targets = [];
        for (var i = 0; i < data.targets.length; i++) {
            var target_id = data.targets[i].target_id;
            var target_name = data.targets[i].target_name;
            var t_data = target_id + ":"  + target_name;
            targets.push(t_data);
        }
        var target_name_list = [];
        $('#exist_target').val(targets);
        for (var i = 0; i < targets.length; i++){
            var target_id = targets[i].split(':')[0];
            var target_name = targets[i].split(':')[1];
            target_name_list.push(target_name);
            $('#new_target').append('<div class="form-group" style="margin-left: 0; margin-right: 0" target_id="' + target_id + '">\n' +
                '    <div class="col-md-4" style="padding: 0">\n' +
                '        <input type="text" readonly class="form-control" value="' + target_name + '">\n' +
                '    </div>\n' +
                '    <div class="col-md-1" style="padding: 0 40px; margin-top:5px">\n' +
                '        <span style="text-align: center; vertical-align: middle;"><i class="fa fa-lg fa-arrow-right" style="color: #00B83F"></i></span>\n' +
                '    </div>\n' +
                '    <div class="col-md-4" style="padding: 0">\n' +
                '        <input type="text" class="form-control" value="' + target_name + '">\n' +
                '    </div>\n' +
                '    <div class="col-md-2" style="padding: 0;margin-left:20px">\n' +
                '        <select class="form-control">\n' +
                '           <option value="0">当前值</option>' +
                '           <option value="1">月累计值</option>' +
                '           <option value="2">季累计值</option>' +
                '           <option value="3">半年累计值</option>' +
                '           <option value="4">年累计值</option>' +
                '        </select>\n' +
                '    </div>\n' +
                '</div>');
        }
        $('#target_data').val(target_name_list);
        $('#rename_div').show();
    });
    $('#col_table tbody').on('click', 'button#delrow', function () {
        var table = $('#col_table').DataTable();
        table.rows($(this).parents('tr')).remove().draw();
    });
}

function addOrEdit() {
    // 新增行 修改行
    var table = $('#col_table').DataTable();
    var col_id = $('#col_id').val();
    if (col_id == 0) {  // 新增
        // new_target下的target_id target_name new_target_name
        var targets = [];
        $('#new_target').children().each(function () {
            var target_id = $(this).attr("target_id"),
                target_name = $(this).children().eq(0).find('input').val(),
                new_target_name = $(this).children().eq(2).find('input').val(),
                cumulative_type = $(this).children().eq(3).find('select').val();
            targets.push({
                'target_id': target_id,
                'target_name': target_name,
                'new_target_name': new_target_name,
                'cumulative_type': cumulative_type,
            });
        });
        table.row.add({
            "name": $('#col_name').val(),
            "targets": targets,
            "remark": $('#col_remark').val(),
            "statistic_type": $('#statistic_type').val(),
        }).draw();
    } else {
        // 修改
        var targets = []
        var index = col_id - 1;
        var c_row = table.row(index);
        $('#new_target').children().each(function () {
            var target_id = $(this).attr("target_id"),
                target_name = $(this).children().eq(0).find('input').val(),
                new_target_name = $(this).children().eq(2).find('input').val(),
                cumulative_type = $(this).children().eq(3).find('select').val();
            targets.push({
                'target_id': target_id,
                'target_name': target_name,
                'new_target_name': new_target_name,
                'cumulative_type': cumulative_type,
            });
        });
        c_row.data({
            "name": $('#col_name').val(),
            "targets": targets,
            "remark": $('#col_remark').val(),
            "statistic_type": $('#statistic_type').val(),
        }).draw();
    }

    $('#static02').hide();
}

getSearchStatistic();

$('#search_new').click(function () {
    $('#search_statistic_id').val(0);
    $('#search_name').val('');
    $('#search_type').val('');
    $('#search_remark').val('');
    $('#static01').modal('show');
    renderTargetColDataTable([]);
});

$('#col_new').click(function () {
    $('#col_id').val(0);
    $('#col_name').val('');
    $('#col_remark').val('');
    $('#target_data').val('');
    $('#new_target').empty();
    $('#rename_div').show();
    $('#static02').modal('show');
    $('#exist_target').val('');
});

$('#col_load').click(function () {
    // 非空条件
    if ($('#col_name').val()) {
        if ($('#target_data').val()) {
            addOrEdit();
        } else {
            alert('未选择指标。')
        }
    } else {
        alert("列名未填写。");
    }
});

$('#statistic_save').click(function () {
    var search_table = $('#search_table').DataTable();
    var col_table = $('#col_table').DataTable();
    var col_table_data = col_table.rows().data();

    var col_data = [];
    for (var i = 0; i < col_table_data.length; i++) {
        col_data.push(col_table_data[i]);
    }

    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../../target_statistic_save/",
        data: {
            "id": $('#search_statistic_id').val(),
            "name": $('#search_name').val(),
            "type": $('#search_type').val(),
            "remark": $('#search_remark').val(),
            "col_data": JSON.stringify(col_data)
        },
        success: function (data) {
            if (data.status == 1) {
                $('#static01').hide();
                $('.modal-backdrop').remove();
                search_table.ajax.url("../../target_statistic_data/").load();
            }
            alert(data.info);
        }
    });
});

loadtargetData();
var completed = false;
function loadtargetData() {
    if (completed) {
        var table_1 = $('#sample_1').DataTable();
        table_1.ajax.url("../../target_insert_data/?app_id=" + $('#app_id').val()).load();
        }
    else {
        $('#sample_1').dataTable({
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../../target_insert_data/?app_id=" + $('#app_id').val(),
            "columns": [
                {"data": "id"},
                {"data": "id"},
                {"data": "name"},
                {"data": "code"},
                {"data": "cycletype"},
                {"data": "cumulative"}

            ],
            "columnDefs": [{
                "targets": 0,
                "mRender": function (data, type, full) {
                    var checked = '';
                    var exist_target_id = $('#exist_target').val().split(',');
                    var target_id = full.id.toString();
                    var target_name = full.name;
                    t_target = target_id + ':' + target_name;
                    if (exist_target_id.indexOf(t_target) !=-1){
                       checked = 'checked'
                    }
                    var id = full.id;
                    var target_name = full.name;
                    var t_target = id + ':' + target_name;
                    return "<input " + checked + " id='select_target_" + id + "' name='selecttarget' type='checkbox' class='checkboxes' value='" + t_target + "'/>"
                }
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
            "initComplete": function () {
                completed = true;
                importData = [];
            },
        });
    }
    importData = [];
}

// 复选框选择指标
var importData = [];
$('#sample_1 tbody').on('click', 'input[name="selecttarget"]', function () {
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

// 载入指标
$('#collect').click(function () {
    loadtargetData();
    $('#insert_target').modal('show');
    var exist_target_id = $('#exist_target').val();
    if (exist_target_id){
        exist_target_id = exist_target_id.split(',');
        for (var i=0; i < exist_target_id.length; i++){
            if (importData.indexOf(exist_target_id[i]) == -1){
                importData.push(exist_target_id[i])
            }
        }
    }
});

// 保存载入指标
$('#addapp_save').click(function () {
    $("Element").blur();
    var table = $('#sample_1').DataTable().data();
    $.each(table, function (i, item) {
        if ($('#select_target_' + item.id).prop('checked')) {
            var t_name = item.id + ':' + item.name;
            if (importData.indexOf(t_name) == -1 ){
                importData.push(t_name);
            }
        }
    });
    if (importData.length < 1) {
        alert("请至少选择一个指标");
    } else {
        var target_list = [];
        var exist_target_id = [];
        $('#insert_target').modal('hide');
        $('#new_target').empty();
        for (var i = 0; i < importData.length; i++){
            var target_id = importData[i].split(':')[0];
            var target_name = importData[i].split(':')[1];
            target_list.push(target_name);
            exist_target_id.push(target_id + ':' + target_name);
            $('#new_target').append('<div class="form-group" style="margin-left: 0; margin-right: 0" target_id="' + target_id + '">\n' +
                '    <div class="col-md-4" style="padding: 0">\n' +
                '        <input type="text" readonly class="form-control" value="' + target_name + '">\n' +
                '    </div>\n' +
                '    <div class="col-md-1" style="padding: 0 40px; margin-top:5px">\n' +
                '        <span style="text-align: center; vertical-align: middle;"><i class="fa fa-lg fa-arrow-right" style="color: #00B83F"></i></span>\n' +
                '    </div>\n' +
                '    <div class="col-md-4" style="padding: 0">\n' +
                '        <input type="text" class="form-control" value="' + target_name + '">\n' +
                '    </div>\n' +
                '    <div class="col-md-2" style="padding: 0;margin-left:20px">\n' +
                '        <select class="form-control">\n' +
                '           <option value="0">当前值</option>' +
                '           <option value="1">月累计值</option>' +
                '           <option value="2">季累计值</option>' +
                '           <option value="3">半年累计值</option>' +
                '           <option value="4">年累计值</option>' +
                '        </select>\n' +
                '    </div>\n' +
                '</div>');
        }
        $('#target_data').val(target_list);
        $('#exist_target').val(exist_target_id);
    }
});

// 全选
$('#select_all_target').click(function () {
     var table = $('#sample_1').DataTable().data();
     $.each(table, function (i, item) {
         $('#select_target_' + item.id).prop('checked',true);
     });
});

// 取消全选
$('#select_all_cancel').click(function () {
     importData = [];
     var table = $('#sample_1').DataTable().data();
     $.each(table, function (i, item) {
            $('#select_target_' + item.id).prop('checked',false)
     });
});

