function getSearchStatistic() {
    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../target_statistic_data/",
        data: {},
        success: function (data) {
            var table_data = data.data,
                status = data.status,
                info = data.info;
            if (status == 1) {
                renderStatisticDataTable(table_data);
            }
        }
    })

}

getSearchStatistic();

function renderStatisticDataTable(table_data) {
    $('#search_table').dataTable().fnDestroy();
    $('#search_table').dataTable({
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
            "data": null,
            "width": "80px",
            "defaultContent": "<button id='edit' title='编辑' data-toggle='modal'  data-target='#static01'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>",
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
}

function renderTargetColDataTable(table_data) {
    $('#col_table').dataTable().fnDestroy();
    $('#col_table').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "data": table_data,
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": null},
            {"data": "remark"},
            {"data": null}
        ],
        "columnDefs": [{
            "targets": -3,
            "mRender": function (data, type, full) {
                var targets = full.targets;
                var targets_td = "";
                for (var i = 0; i < targets.length; i++) {
                    targets_td += targets[i].new_target_name + ",";
                }

                return targets_td.endsWith(",") ? targets_td.slice(0, -1) : targets_td;
            }
        }, {
            "targets": -1,
            "data": null,
            "width": "80px",
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
        }
    });
}


$('#search_new').click(function () {
    $('#static01').modal('show');
});

$('#col_new').click(function () {
    $('#targets').val(null).trigger('change');
    $('#new_target').empty();
    $('#static02').modal('show');
});

// 新增
$("#targets").on("select2:select",function(e){
    var target = e.params.data;
    $('#new_target').append('<div class="form-group" style="margin-left: 0; margin-right: 0" target_id="' + target.id + '">\n' +
        '    <div class="col-md-5" style="padding: 0">\n' +
        '        <input type="text" readonly class="form-control" value="' + target.text + '">\n' +
        '    </div>\n' +
        '    <div class="col-md-2" style="padding: 0 40px; margin-top:5px">\n' +
        '        <span style="text-align: center; vertical-align: middle;"><i class="fa fa-lg fa-arrow-right" style="color: #00B83F"></i></span>\n' +
        '    </div>\n' +
        '    <div class="col-md-5" style="padding: 0">\n' +
        '        <input type="text" class="form-control">\n' +
        '    </div>\n' +
        '</div>')
});
// 删除
$("#targets").on("select2:unselect",function(e){
    // 将指定id的div删除
    var target = e.params.data;
    var target_id = target.id;

    $('#new_target').find('div[target_id="' + target_id + '"]').remove();
});

$('#col_load').click(function(){
    // 新增行 修改行
});
