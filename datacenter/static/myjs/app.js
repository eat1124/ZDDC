$(document).ready(function () {
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../app_data/",
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "code"},
            {"data": "remark"},
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
                url: "../app_del/",
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
        $("#app_name").val(data.name);
        $("#app_code").val(data.code);
        $("#remark").val(data.remark);
        $("#sort").val(data.sort);
        work_data = JSON.parse(data.works);
        console.log(typeof (work_data))
        console.log(work_data)
        loadWorkData();
    });

    $("#new").click(function () {
        $("#id").val("0");
        $("#app_name").val("");
        $("#app_code").val("");
        $("#remark").val("");
        $("#sort").val("");
    });

    $('#save').click(function () {
        var table = $('#sample_1').DataTable();
        var table2 = $('#sample_2').DataTable();

        var work_data = JSON.stringify(table2.data().toArray());

        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../app_save/",
            data: {
                id: $("#id").val(),
                app_name: $("#app_name").val(),
                app_code: $("#app_code").val(),
                remark: $("#remark").val(),
                sort: $("#sort").val(),
                work_data: work_data,
            },
            success: function (data) {
                var myres = data["res"];
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


    var work_data = [];
    var completed = false;

    function loadWorkData() {
        if (completed) {
            $('#sample_2').dataTable().fnDestroy();
        }
        $('#sample_2').dataTable({
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "data": work_data,
            "columns": [
                {"title": "序号"},
                {"title": "业务名称"},
                {"title": "业务编号"},
                {"title": "说明"},
                {"title": "核心业务"},
                {"title": "排序"},
                {"title": "操作"}
            ],
            "columnDefs": [{
                "targets": -1,
                "data": null,
                "width": "100px",
                "defaultContent": "<button  id='edit_work' title='编辑' data-toggle='modal'  data-target='#static1'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>" +
                    "<button title='删除'  id='del_work' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>"
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
            initComplete: function (settings, json) {
                completed = true;
            }
        });
        $('#sample_2 tbody').on('click', 'button#del_work', function () {
            if (confirm("确定要删除该条数据？")) {
                var table = $('#sample_2').DataTable();
                table.row($(this).parents('tr')).remove().draw();
            }
        });
        $('#sample_2 tbody').on('click', 'button#edit_work', function () {
            var table = $('#sample_2').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $("#work_id").val(data[0]);
            $("#work_name").val(data[1]);
            $("#work_code").val(data[2]);
            $("#work_remark").val(data[3]);
            $("#core_work").val(data[4]);
            $("#work_sort").val(data[5]);
        });
    }

    $('#static').on('show.bs.modal', function () {
        if ($('#work_id') == '0') {
            work_data = [];
        }
        loadWorkData();
    });

    $("#work_new").click(function () {
        $("#work_id").val("0");
        $("#work_name").val("");
        $("#work_code").val("");
        $("#work_remark").val("");
        $("#core_work").val("");
        $("#work_sort").val("");
    });

    $('#load').click(function () {
        var table = $('#sample_2').DataTable();
        var name = $('#work_name').val();
        var code = $('#work_code').val();
        var remark = $('#work_remark').val();
        var core_work = $('#core_work').val();
        var sort = $('#work_sort').val();
        var work_id = $('#work_id').val();

        if (name) {
            if (code) {
                // load时，区分新增还是修改
                if (work_id == '0') {
                    // 业务名称与业务编号不得重复
                    var name_duplicated = false;
                    table.rows().eq(0).each(function (index) {
                        var row = table.row(index).node();
                        if (name == $(row).children().eq(1).text().trim()) {
                            name_duplicated = true;
                            return;
                        }
                    });

                    if (!name_duplicated) {
                        var code_duplicated = false;
                        table.rows().eq(0).each(function (index) {
                            var row = table.row(index).node();
                            if (code == $(row).children().eq(2).text().trim()) {
                                code_duplicated = true;
                                return;
                            }
                        });
                        if (!code_duplicated) {
                            var load_list = ['暂无', name, code, remark, core_work, sort];
                            table.row.add(load_list).draw();

                            table.rows().eq(0).each(function (index) {
                                var row = table.row(index).node();
                                if ($(row).children().eq(0).text().trim() == '暂无') {
                                    $(row).css('color', 'red');
                                }
                            });
                            $('#static1').modal('hide');
                        } else {
                            alert('业务编号已存在。')
                        }
                    } else {
                        alert('业务名称已存在。')
                    }
                } else {
                    // 修改时，直接修改当前行
                    // ...
                }

            } else {
                alert('业务编号未填写。')
            }
        } else {
            alert('业务名称未填写。')
        }

    });
});