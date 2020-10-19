function loadElectricDT() {
    if ($.fn.DataTable.isDataTable('#electric_energy_dt')) {
        $('#electric_energy_dt').dataTable().fnDestroy();
    }
    $('#electric_energy_dt').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "destroy": true,
        "ajax": "/get_electric_energy/",
        "columns": [
            {"data": "id"},
            {"data": "extract_time"},
            {"data": "f_electric_energy"},
            {"data": "s_electric_energy"},
            {"data": "a_electric_energy"},
            {"data": null}
        ],
        "columnDefs": [{
            "targets": 0,
            "visible": false
        }, {
            "targets": -1,
            "data": null,
            "defaultContent": "<button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>"
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

$('#electric_energy_dt tbody').on('click', 'button#delrow', function () {
    if (confirm("确定要删除该条数据？")) {
        var table = $('#electric_energy_dt').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $.ajax({
            type: "POST",
            url: "../../electric_energy_del/",
            data:
                {
                    id: data.id,
                },
            success: function (data) {
                if (data['status'] == 1) {
                    table.ajax.reload();
                }
                alert(data['info'])
            },
            error: function (e) {
                alert("删除失败，请于管理员联系。");
            }
        });

    }
});

loadElectricDT();

$('#reporting_date').datetimepicker({
    format: 'yyyy-mm-dd',
    autoclose: true,
    startView: 2,
    minView: 2,
});

$('input[id^="f_start_time"],input[id^="f_end_time"],input[id^="s_start_time"],input[id^="s_end_time"]').datetimepicker({
    format: 'yyyy-mm-dd hh:ii:ss',
    autoclose: true,
});

$('#f_checkbox').bootstrapSwitch({
    onText: "启动",
    offText: "停止",
    size: "small",
    onSwitchChange: function (event, state) {
        if (state == true) {
            $('#f_form input').prop("disabled", false);
        } else {
            $('#f_form input').val("").prop("disabled", true);
        }
    }
});

$('#s_checkbox').bootstrapSwitch({
    onText: "启动",
    offText: "停止",
    size: "small",
    onSwitchChange: function (event, state) {
        if (state == true) {
            $('#s_form input').prop("disabled", false);
        } else {
            $('#s_form input').val("").prop("disabled", true);
        }
    }
});

/**
 * 提取#1 #2上网电量
 */

$('#extract').click(function () {
    $.ajax({
        type: 'POST',
        dataType: 'JSON',
        url: '../../extract_electric_energy/',
        data: $('#f_form').serialize() + '&' + $('#s_form').serialize(),
        success: function (data) {
            var status = data.status,
                info = data.info,
                electric_energy = data.data;
            if (status){
                $('#f_electric_energy').val(electric_energy["f_electric_energy"]);
                $('#s_electric_energy').val(electric_energy["s_electric_energy"]);
            } else {
                alert(info);
            }
            $('#extract').button("reset");
        }
    })
});

/**
 * 保存上网电量
 */
function saveElectricEnergy(f_is_open, s_is_open, f_electric_energy, s_electric_energy, extract_time, table) {
    $.ajax({
        type: "POST",
        dataType: "json",
        url: "../../save_electric_energy/",
        data: {
            f_is_open: f_is_open,
            s_is_open: s_is_open,
            f_electric_energy: f_electric_energy,
            s_electric_energy: s_electric_energy,
            extract_time: extract_time
        },
        success: function (data) {
            var status = data.status,
                info = data.info;
            if (status == 1) {
                table.ajax.reload();
            }
            alert(info);
        }
    });
}

$('#save').click(function () {
    var f_electric_energy = $('#f_electric_energy').val(),
        s_electric_energy = $('#s_electric_energy').val(),
        extract_time = $('#extract_time').val(),
        table = $('#electric_energy_dt').DataTable(),
        f_is_open = 1,
        s_is_open = 1;
    if (!$('#f_checkbox').prop("checked")) {
        f_is_open = 0;
    }
    if (!$('#s_checkbox').prop("checked")) {
        s_is_open = 0;
    }

    // 查看当天记录是否存在
    var t_data = table.data();

    var is_existed = false;
    for (var i = 0; i < t_data.length; i++) {
        var pre_extract_time = t_data[i]['extract_time'];
        if (pre_extract_time == extract_time) {
            is_existed = true;
            break;
        }
    }
    if (is_existed){
        if (confirm("今天已保存过一次，是否再次保存？")){
            saveElectricEnergy(f_is_open, s_is_open, f_electric_energy, s_electric_energy, extract_time, table)
        }
    } else {
        saveElectricEnergy(f_is_open, s_is_open, f_electric_energy, s_electric_energy, extract_time, table)
    }
});

