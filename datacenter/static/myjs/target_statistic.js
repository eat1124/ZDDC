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

        var targets = []
        for (var i = 0; i < data.targets.length; i++) {
            targets.push(data.targets[i].target_id);
        }

        $('#multiple_targets').select2('val', targets);
        // 重命名加载
        for (var j = 0; j < data.targets.length; j++) {
            var target = data.targets[j];
            var cumulative_type = target.cumulative_type;
            var curvalue_selected = cumulative_type == 0 ? "selected": "",
                cumulativemonth_selected =  cumulative_type == 1 ? "selected": "",
                cumulativequarter_selected =  cumulative_type == 2 ? "selected": "",
                cumulativehalfyear_selected =  cumulative_type == 3 ? "selected": "",
                cumulativeyear_selected =  cumulative_type == 4 ? "selected": "";
            $('#new_target').append('<div class="form-group" style="margin-left: 0; margin-right: 0" target_id="' + target.target_id + '">\n' +
                '    <div class="col-md-4" style="padding: 0">\n' +
                '        <input type="text" readonly class="form-control" value="' + target.target_name + '">\n' +
                '    </div>\n' +
                '    <div class="col-md-1" style="padding: 0 40px; margin-top:5px">\n' +
                '        <span style="text-align: center; vertical-align: middle;"><i class="fa fa-lg fa-arrow-right" style="color: #00B83F"></i></span>\n' +
                '    </div>\n' +
                '    <div class="col-md-4" style="padding: 0">\n' +
                '        <input type="text" class="form-control" value="' + target.new_target_name + '">\n' +
                '    </div>\n' +
                '    <div class="col-md-2" style="padding: 0;margin-left:20px">\n' +
                '        <select class="form-control" name="cumulative_type_opts">\n' +
                '           <option value="0" ' + curvalue_selected + '>当前值</option>' + 
                '           <option value="1" ' + cumulativemonth_selected + '>月累计值</option>' + 
                '           <option value="2" ' + cumulativequarter_selected + '>季累计值</option>' + 
                '           <option value="3" ' + cumulativehalfyear_selected + '>半年累计值</option>' + 
                '           <option value="4" ' + cumulativeyear_selected + '>年累计值</option>' + 
                '        </select>\n' + 
                '    </div>\n' +
                '</div>');
        }

        $('#single_div').hide();
        $('#multiple_div').show();
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
        var targets = []
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

function displayTargets() {
    $('#single_target').empty();
    $('#multiple_targets').empty();

    for (var i = 1; i < all_targets.length; i++) {
        $('#single_target').append('<option value="' + all_targets[i].id + '">' + all_targets[i].name + '</option>')
        $('#multiple_targets').append('<option value="' + all_targets[i].id + '">' + all_targets[i].name + '</option>')
    }
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
    $('#multiple_targets').select2('val', []);
    $('#single_target').select2('val', "");
    $('#new_target').empty();
    $('#rename_div').show();
    $('#static02').modal('show');
    $('#multiple_div').show();
    $('#single_div').hide();
});

$("#multiple_targets")
    .on("select2:select", function (e) {
        var target = e.params.data;
        $('#new_target').append('<div class="form-group" style="margin-left: 0; margin-right: 0" target_id="' + target.id + '">\n' +
            '    <div class="col-md-4" style="padding: 0">\n' +
            '        <input type="text" readonly class="form-control" value="' + target.text + '">\n' +
            '    </div>\n' +
            '    <div class="col-md-1" style="padding: 0 40px; margin-top:5px">\n' +
            '        <span style="text-align: center; vertical-align: middle;"><i class="fa fa-lg fa-arrow-right" style="color: #00B83F"></i></span>\n' +
            '    </div>\n' +
            '    <div class="col-md-4" style="padding: 0">\n' +
            '        <input type="text" class="form-control" value="' + target.text + '">\n' +
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
    })  // 新增
    .on("select2:unselect", function (e) {
        // 将指定id的div删除
        var target = e.params.data;
        var target_id = target.id;
        $('#new_target').find('div[target_id="' + target_id + '"]').remove();
    });  // 删除

$('#col_load').click(function () {
    // 非空条件
    if ($('#col_name').val()) {
        if ($('#multiple_targets').val()) {
            addOrEdit();
        } else {
            alert('未选择指标。')
        }
    } else {
        alert("列名未填写。")
    }
});

$('#static01').on("show.bs.modal", function () {
    displayTargets();
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
