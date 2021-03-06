var targets_sorted = [];

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
        "bAutoWidth": true,
        "bSort": false,
        "iDisplayLength": 25,
        "bProcessing": true,
        "data": table_data,
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "type_name"},
            {"data": "remark"},
            {"data": null}
        ],
        "columnDefs": [
            {
            "targets": -5,
            "width": "50px",
        },
            {
            "targets": -4,
            "mRender": function (data, type, full) {
                var href = '/statistic_report/?search_id=' + full.id + "&date_type=" + full.type;
                return "<a href='" + href + "' target='_blank'>" + full.name + "</a>";
            }
        },
            {
            "targets": -1,
            "width": "40px",
            "data": null,
            "mRender": function (data, type, full) {
                return "<button id='edit' title='编辑' data-toggle='modal'  data-target='#static01'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>" +
                    "<button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>"
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
        $("#search_sort").val(data.sort);

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
            {"data": null},
            {"data": null}
        ],
        "columnDefs": [{
            "targets": -3,
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
        targets_sorted = [];
        var table = $('#col_table').DataTable();
        var data = table.row($(this).parents('tr')).data();
        // 预先清空
        $('#new_target').empty();
        $("#col_id").val(table.row($(this).parents('tr')).index() + 1);
        $("#col_name").val(data.name);
        $("#col_remark").val(data.remark);
        for (var i = 0; i < data.targets.length; i++) {
            var target_id = data.targets[i].target_id;
            var target_name = data.targets[i].target_name;
            var target_cumulative = data.targets[i].cumulative_type;
            var t_data = target_id + ":"  + target_name + ":" + target_cumulative;
            targets_sorted.push(t_data);
        }
        $('#exist_target').val(targets_sorted);
        edit_reorder();
        $('#rename_div').show();
    });
    $('#col_table tbody').on('click', 'button#delrow', function () {
        var table = $('#col_table').DataTable();
        table.rows($(this).parents('tr')).remove().draw();
    });
}

//列信息配置
function edit_reorder(){
    $('#new_target').empty();
    var target_name_list = [];
    for (var i = 0; i < targets_sorted.length; i++){
        var target_id = targets_sorted[i].split(':')[0];
        var target_name = targets_sorted[i].split(':')[1];
        var target_cumulative = targets_sorted[i].split(':')[2];
        target_name_list.push(target_name);
        if (target_cumulative == '0'){
            var selected0 = 'selected';
            var selected1 = '';
            var selected2 = '';
            var selected3 = '';
            var selected4 = '';
        }
        if (target_cumulative == '1'){
            var selected0 = '';
            var selected1 = 'selected';
            var selected2 = '';
            var selected3 = '';
            var selected4 = '';
        }
        if (target_cumulative == '2'){
            var selected0 = '';
            var selected1 = '';
            var selected2 = 'selected';
            var selected3 = '';
            var selected4 = '';
        }
        if (target_cumulative == '3'){
            var selected0 = '';
            var selected1 = '';
            var selected2 = '';
            var selected3 = 'selected';
            var selected4 = '';
        }
        if (target_cumulative == '4'){
            var selected0 = '';
            var selected1 = '';
            var selected2 = '';
            var selected3 = '';
            var selected4 = 'selected';
        }
        $('#new_target').append('<div class="form-group" style="margin-left: 0; margin-right: 0" target_id="' + target_id + '">\n' +
            '    <div class="col-md-3" style="padding: 0">\n' +
            '        <input type="text" readonly class="form-control" value="' + target_name + '">\n' +
            '    </div>\n' +
            '    <div class="col-md-1" style="padding: 0 20px; margin-top:5px">\n' +
            '        <span style="text-align: center; vertical-align: middle;" title="重命名"><i class="fa fa-lg fa-arrow-right" style="color: #00B83F"></i></span>\n' +
            '    </div>\n' +
            '    <div class="col-md-3" style="padding: 0">\n' +
            '        <input type="text" class="form-control" value="' + target_name + '">\n' +
            '    </div>\n' +
            '    <div class="col-md-2" style="padding: 0;margin-left:20px">\n' +
            '        <select class="form-control" value="' + target_cumulative + '">\n' +
            '           <option ' + selected0 + ' value="0">当前值</option>' +
            '           <option ' + selected1 + ' value="1">月累计值</option>' +
            '           <option ' + selected2 + ' value="2">季累计值</option>' +
            '           <option ' + selected3 + ' value="3">半年累计值</option>' +
            '           <option ' + selected4 + ' value="4">年累计值</option>' +
            '        </select>\n' +
            '    </div>\n' +
            '    <div class="col-md-2" style="padding: 0;margin-top:5px;margin-left:20px">\n' +
            '        <a href="javascript:edit_doUp(' + i + ');"  title="上移"><i class="fa fa-lg fa fa-arrow-up" style="color: #00B83F"></i></a>\n' +
            '        <a href="javascript:edit_doDown(' + i + ');"  title="下移"><i class="fa fa-lg fa-arrow-down" style="color: #00B83F;margin-left:20px"></i></a>\n' +
            '        <a href="javascript:edit_del(' + i + ');" title="删除"><i class="fa fa-trash-o fa-lg" style="color: #00B83F;margin-left:20px;font-weight:bold"></i></a>\n' +
            '    </div>\n' +
            '</div>');
    }
    $('#target_data').val(target_name_list);
}

//编辑上移
function edit_doUp(i) {
    if (i == 0) {
        return;
    }
    var tem = targets_sorted[i - 1];
    targets_sorted[i - 1] = targets_sorted[i];
    targets_sorted[i] = tem;
    edit_reorder();
}

//编辑下移
function edit_doDown(i) {
    if (i == targets_sorted.length - 1) {
        return;
    }
    var tem = targets_sorted[i + 1];
    targets_sorted[i + 1] = targets_sorted[i];
    targets_sorted[i] = tem;
    edit_reorder();
}

//编辑删除
function edit_del(i) {
    targets_sorted.splice(i,1);
    edit_reorder();
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
        }).draw();
    } else {
        // 修改
        var targets = [];
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
    $('#search_sort').val('');
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
            "sort": $('#search_sort').val(),
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
        table_1.ajax.url("../../target_insert_data/?search_adminapp=" + $('#app_id').val()).load();
        }
    else {
        $('#sample_1').dataTable({
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../../target_insert_data/?search_adminapp=" + $('#app_id').val(),
            "columns": [
                {"data": "id"},
                {"data": "id"},
                {"data": "name"},
                {"data": "code"},
                {"data": "cycletype_name"},
                {"data": "cumulative"}

            ],
            "columnDefs": [{
                "targets": 0,
                "mRender": function (data, type, full) {
                    var checked = '';
                    var exist_target_id = [];
                    var exist_target = $('#exist_target').val().split(',');
                    for (var i=0; i < exist_target.length; i++){
                        exist_target_id.push(exist_target[i].split(':')[0])
                    }
                    var target_id = full.id.toString();
                    if (exist_target_id.indexOf(target_id) !=-1){
                       checked = 'checked'
                    }
                    var t_target = full.id + ':' + full.name;
                    return "<input " + checked + " id='select_target_" + full.id + "' name='selecttarget' type='checkbox' class='checkboxes' value='" + t_target + "'/>"
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
            if (importData[i] == $(this).val() || importData[i].split(':')[0] == $(this).val().split(':')[0]) {
                importData.splice(i, 1);
            }
        }
    }
});

// 载入指标
$('#collect').click(function () {
    loadtargetData();
    $('#insert_target').modal('show');
    var exist_target = $('#exist_target').val();
    if (exist_target){
        exist_target = exist_target.split(',');
        for (var i=0; i < exist_target.length; i++){
            if (importData.indexOf(exist_target[i]) == -1){
                importData.push(exist_target[i])
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
            for (var i = 0; i < importData.length; i++){
                var exist_target_id = importData[i].split(':')[0];
                if (item.id == exist_target_id){
                    importData.splice(i, 1)
                }
            }
            if (importData.indexOf(t_name) == -1 ){
                importData.push(t_name);
            }
        }
    });
    if (importData.length < 1) {
        alert("请至少选择一个指标。");
    } else {
        new_reorder();
    }
});

//列信息配置
function new_reorder(){
    var target_list = [];
    var exist_target = [];
    $('#insert_target').modal('hide');
    $('#new_target').empty();
    for (var i = 0; i < importData.length; i++){
        var target_id = importData[i].split(':')[0];
        var target_name = importData[i].split(':')[1];
        target_list.push(target_name);
        exist_target.push(target_id + ':' + target_name);
        $('#new_target').append('<div class="form-group" style="margin-left: 0; margin-right: 0" target_id="' + target_id + '">\n' +
            '    <div class="col-md-3" style="padding: 0">\n' +
            '        <input type="text" readonly class="form-control" value="' + target_name + '">\n' +
            '    </div>\n' +
            '    <div class="col-md-1" style="padding: 0 20px; margin-top:5px">\n' +
            '        <span style="text-align: center; vertical-align: middle;" title="重命名"><i class="fa fa-lg fa-arrow-right" style="color: #00B83F"></i></span>\n' +
            '    </div>\n' +
            '    <div class="col-md-3" style="padding: 0">\n' +
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
            '    <div class="col-md-2" style="padding: 0;margin-top:5px;margin-left:25px">\n' +
            '        <a href="javascript:new_doUp(' + i + ');"  title="上移"><i class="fa fa-lg fa fa-arrow-up" style="color: #00B83F"></i></a>\n' +
            '        <a href="javascript:new_doDown(' + i + ');"  title="下移"><i class="fa fa-lg fa-arrow-down" style="color: #00B83F;margin-left:20px"></i></a>\n' +
            '        <a href="javascript:new_del(' + i + ');" title="删除"><i class="fa fa-trash-o fa-lg" style="color: #00B83F;margin-left:20px;font-weight:bold"></i></a>\n' +
            '    </div>\n' +
            '</div>');
    }
    $('#target_data').val(target_list);
    $('#exist_target').val(exist_target);
}

//新增上移
function new_doUp(i) {
    if (i == 0) {
        return;
    }
    var tem = importData[i - 1];
    importData[i - 1] = importData[i];
    importData[i] = tem;
    new_reorder();
}

//新增下移
function new_doDown(i) {
    if (i == importData.length - 1) {
        return;
    }
    var tem = importData[i + 1];
    importData[i + 1] = importData[i];
    importData[i] = tem;
    new_reorder();
}

// 新增删除
function new_del(i) {
    importData.splice(i,1);
    new_reorder();
}


// 本页全选
$('#select_all_target').click(function () {
     var table = $('#sample_1').DataTable().data();
     $.each(table, function (i, item) {
         $('#select_target_' + item.id).prop('checked',true);
         if ($('#select_target_' + item.id).prop('checked')){
             if (importData.indexOf(item.id + ':' + item.name) == -1){
                 importData.push(item.id + ':' + item.name)
             }
         }
     });
});

// 取消全选
$('#select_all_cancel').click(function () {
    var table = $('#sample_1').DataTable().data();
    $.each(table, function (i, item) {
        $('#select_target_' + item.id).prop('checked',false);
        if ($('#select_target_' + item.id).prop('checked') == false){
            for (var i = 0; i < importData.length; i++) {
                if (importData[i] == $('#select_target_' + item.id).val()) {
                    importData.splice(i, 1);
                }
            }
        }
    });
});

