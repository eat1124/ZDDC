$(document).ready(function () {
    var index = 0;

    function getProcessMonitorTree(circle_id, app_id, source_id) {
        $.ajax({
            type: "POST",
            dataType: "json",
            url: "../get_process_monitor_tree/",
            data: {
                circle_id: circle_id,
                app_id: app_id,
                source_id: source_id,
                index: index
            },
            success: function (data) {
                index += 1;
                var treeData = JSON.parse(data.data);
                console.log(treeData)

                $('#process_monitor_tree').jstree('destroy');
                $('#process_monitor_tree').jstree({
                    'core': {
                        "themes": {
                            "responsive": false
                        },
                        "check_callback": true,
                        'data': treeData
                    },

                    "types": {
                        "node": {
                            "icon": "fa fa-folder icon-state-warning icon-lg"
                        },
                        "file": {
                            "icon": "fa fa-file-o icon-state-warning icon-lg"
                        },
                        "node_grey": {
                            "icon": "fa fa-folder icon-state-default icon-lg"
                        },
                        "file_grey": {
                            "icon": "fa fa-file-o icon-state-default icon-lg"
                        },
                    },
                    "contextmenu": {
                        "items": {
                            "create": null,
                            "rename": null,
                            "remove": null,
                            "ccp": null,
                        }
                    },
                    "plugins": ["types", "role"]
                })
                    .bind('select_node.jstree', function (event, data) {
                        $('#node_id').val(data.node.id);

                        if (data.node.data.type == 'root') {
                            $("#form_div").hide();
                        } else {
                            $("#form_div").show();
                        }

                        $('#source_div, #app_div, #circle_div, #process_exec').hide();

                        // 根据data.node.data.status判断展示开启/关闭/重启按钮
                        if (['已关闭', ''].indexOf(data.node.data.status) != -1) {
                            $('#start').show();
                            $('#stop, #restart').hide();
                        } else if (data.node.data.status == '运行中') {
                            $('#stop, #restart').show();
                            $('#start').hide();
                        } else {
                            $('#start, #stop, #restart').hide();
                        }

                        $("#title").text(data.node.text);

                        $('#source_name').val(data.node.data.s_name);
                        $('#source_code').val(data.node.data.s_code);
                        $('#source_type').val(data.node.data.s_type);

                        if (['source', 'app', 'circle'].indexOf(data.node.data.type) != -1) {
                            $('#source_div').show();
                        }

                        if (['app', 'circle'].indexOf(data.node.data.type) != -1) {
                            $('#app_div').show();
                        }
                        if (data.node.data.type == 'circle') {
                            $('#circle_div').show();
                            $('#process_exec').show();

                            $('#create_time').val(data.node.data.create_time);
                            $('#status').val(data.node.data.status);
                            $('#last_time').val(data.node.data.last_time);


                            // tab
                            $('#navtabs').show();
                        } else {
                            $('#navtabs').hide();
                        }

                        // app/circle
                        $('#app_name').val(data.node.data.a_name);
                        $('#circle_name').val(data.node.data.c_name);

                        $('#source_id').val(data.node.data.s_id);
                        $('#app_id').val(data.node.data.a_id);
                        $('#circle_id').val(data.node.data.c_id);

                        // tab
                        $('#navtabs a:first').tab('show')
                    });
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });


    }

    getProcessMonitorTree("", "", "");
    // 启动/关闭/重启
    $('#start, #stop, #restart').click(function () {
        var operate = $(this).prop('id');
        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '../process_run/',
            data: {
                'operate': operate,
                'source_id': $('#source_id').val(),
                'app_id': $('#app_id').val(),
                'circle_id': $('#circle_id').val()
            },
            success: function (data) {
                if (data.tag == 1) {
                    // 刷新树
                    getProcessMonitorTree($('#circle_id').val(), $('#app_id').val(), $('#source_id').val());

                    // 写入状态，时间
                    if (data.data) {
                        $('#status').val(data.data.status);
                        $('#create_time').val(data.data.create_time);

                        // 根据data.data.status判断展示开启/关闭/重启按钮
                        if (data.data.status == '已关闭') {
                            $('#start').show();
                            $('#stop, #restart').hide();
                        } else if (data.data.status == '运行中') {
                            $('#stop, #restart').show();
                            $('#start').hide();
                        } else {
                            $('#start, #stop, #restart').hide();
                        }
                    }
                }
                alert(data.res);
            },
            error: function () {
                alert('页面出现错误，请于管理员联系。')
            }
        })
    });


    // 切换标签页
    // 2.指标信息
    var sample_2_completed = false;
    var sample_3_completed = false;
    var sample_4_completed = false;
    $('a[data-toggle="tab"]').on('show.bs.tab', function (e) {
        var target_id = e.target.id;
        if (target_id == 'tabcheck2') {
            if (sample_2_completed) {
                var table_2 = $('#sample_2').DataTable();
                table_2.ajax.url("../../pm_target_data/?app_id=" + $('#app_id').val() + "&source_id=" + $('#source_id').val() + "&circle_id=" + $('#circle_id').val()).load();
            } else {
                // 指标信息
                $('#sample_2').dataTable({
                    "bAutoWidth": true,
                    "bSort": false,
                    "bProcessing": true,
                    "ajax": "../../pm_target_data/?app_id=" + $('#app_id').val() + "&source_id=" + $('#source_id').val() + "&circle_id=" + $('#circle_id').val(),
                    "columns": [
                        {"data": "id"},
                        {"data": "id"},
                        {"data": "target_code"},
                        {"data": "target_name"},
                        {"data": "source_content"},
                        {"data": "storage_table_name"},
                        {"data": "storage_fields"},
                    ],

                    "columnDefs": [{
                        "targets": 0,
                        "mRender": function (data, type, full) {
                            return "<input name='selecttarget' type='checkbox' class='checkboxes' value='" + data + "'/>"
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
                    "initComplete": function (settings, json) {
                        sample_2_completed = true;
                    }
                });
            }
        }
        if (target_id == 'tabcheck3') {
            if (sample_3_completed) {
                var table_3 = $('#sample_3').DataTable();
                table_3.ajax.url("../../get_exception_data/?app_id=" + $('#app_id').val() + "&source_id=" + $('#source_id').val() + "&circle_id=" + $('#circle_id').val()).load();
            } else {
                // 指标信息
                $('#sample_3').dataTable({
                    "bAutoWidth": true,
                    "bSort": false,
                    "bProcessing": true,
                    "ajax": "../../get_exception_data/?app_id=" + $('#app_id').val() + "&source_id=" + $('#source_id').val() + "&circle_id=" + $('#circle_id').val(),
                    "columns": [
                        {"data": "id"},
                        {"data": "target_name"},
                        {"data": "extract_error_time"},
                        {"data": "supplement_times"},
                        {"data": "last_supplement_time"},
                    ],

                    "columnDefs": [],
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
                    "initComplete": function (settings, json) {
                        sample_3_completed = true;
                    }
                });
            }
        }
        if (target_id == 'tabcheck4') {
            if (sample_4_completed) {
                var table = $('#sample_4').DataTable();
                table.ajax.url("../../get_log_info/?app_id=" + $('#app_id').val() + "&source_id=" + $('#source_id').val() + "&circle_id=" + $('#circle_id').val()).load();
            } else {
                // 指标信息
                $('#sample_4').dataTable({
                    "bAutoWidth": true,
                    "bSort": false,
                    "bProcessing": true,
                    "ajax": "../../get_log_info/?app_id=" + $('#app_id').val() + "&source_id=" + $('#source_id').val() + "&circle_id=" + $('#circle_id').val(),
                    "columns": [
                        {"data": "id"},
                        { "data": "create_time"},
                        { "data": "content"},
                    ],

                    "columnDefs": [],
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
                    "initComplete": function (settings, json) {
                        sample_4_completed = true;
                    }
                });
            }
        }
    });

    // 测试
    $('#test').click(function () {
        var test_table = $('#sample_2').DataTable();
        var selectArray = []
        $("input[name=selecttarget]:checked").each(function () {
            selectArray.push($(this).val());
        });
        if (selectArray.length < 1) {
            alert("请至少选择一个指标");
        } else {
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: "../../target_test/",
                data:
                {
                    selectedtarget: selectArray,
                },
                success: function (data) {
                    var myres = data["res"];
                    if (myres == "测试成功。") {
                        test_table.ajax.reload();
                    }
                    alert(myres);
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }
    });
    // 补取
    $('#supplement_process').click(function () {
        var supplement_process_table = $('#sample_2').DataTable();
        var selectArray = []
        $("input[name=selecttarget]:checked").each(function () {
            selectArray.push($(this).val());
        });
        if (selectArray.length < 1) {
            alert("请至少选择一个指标");
        } else {
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: "../../supplement_process/",
                data:
                {
                    selectedtarget: selectArray,
                },
                success: function (data) {
                    var myres = data["res"];
                    if (myres == "补取成功。") {
                        supplement_process_table.ajax.reload();
                    }
                    alert(myres);
                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }
    });
});