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
                        // 写入进程ID
                        $('#cp_id').val(data.node.data.cp_id);
                        cp_id = data.node.data.cp_id;

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
                            
                            tabCheck5();
                        } else {
                            $('#navtabs').hide();
                        }

                        // app/circle
                        $('#app_name').val(data.node.data.a_name);
                        $('#circle_name').val(data.node.data.c_name);

                        $('#source_id').val(data.node.data.s_id);
                        $('#app_id').val(data.node.data.a_id);
                        $('#circle_id').val(data.node.data.c_id);

                        // 固定进程 单独写
                        if (data.node.data.check_type) {
                            $('#circle_div').show();
                            $('#circle_name').parent().parent().hide();
                            $('#process_exec').show();
                            $('#source_name').val(data.node.data.f_s_name);

                            $('#create_time').val(data.node.data.create_time);
                            $('#status').val(data.node.data.status);
                            $('#last_time').val(data.node.data.last_time);

                        } else {
                            $('#circle_name').parent().parent().show();
                        }
                        $('#check_type').val(data.node.data.check_type);

                        // tab
                        $('#navtabs a:first').tab('show');
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
        // 判断固定进程还是动态进程
        var check_type = $('#check_type').val();

        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '../process_run/',
            data: {
                'check_type': check_type,
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
    var cp_id = '';

    function tabCheck1() {
        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '../get_process_monitor_info/',
            data: {
                cp_id: cp_id,
            },
            success: function (data) {
                var status = data.status;
                var pm_data = data.data;
                if (status == 1) {
                    $('#source_name').val(pm_data.source_name);
                    $('#source_code').val(pm_data.source_code);
                    $('#source_type').val(pm_data.source_type);
                    $('#app_name').val(pm_data.app_name);
                    $('#circle_name').val(pm_data.circle_name);
                    $('#create_time').val(pm_data.create_time);
                    $('#last_time').val(pm_data.last_time);
                    $('#status').val(pm_data.status);
                } else {
                    alert(pm_data);
                }
            },
            error: function () {
                alert('页面出现错误，请于管理员联系。')
            }
        });
    }

    function tabCheck2() {
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
                    {"data": null},
                ],

                "columnDefs": [{
                    "targets": 0,
                    "mRender": function (data, type, full) {
                        return "<input name='selecttarget' type='checkbox' class='checkboxes' value='" + data + "'/>"
                    }
                }, {
                    "targets": -1,
                    "data": null,
                    "defaultContent": "<button  id='view' title='查看详情'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-eye'></i></button>"
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
                "initComplete": function (settings, json) {
                    sample_2_completed = true;
                    var supplement_status = json.supplement_status;
                    if (supplement_status == 1) {
                        $('#supplement').hide();
                    } else {
                        $('#supplement').show();
                    }
                }
            });

        }
    }

    function tabCheck3() {
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
                },
                "initComplete": function (settings, json) {
                    sample_3_completed = true;
                }
            });
        }
    }

    function tabCheck4() {
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
                    {"data": "create_time"},
                    {"data": "content"},
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
                },
                "initComplete": function (settings, json) {
                    sample_4_completed = true;
                }
            });
        }
    }

    function tabCheck5() {
        // 根据主进程ID获取补取进程状态
        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '../get_supplement_process_info/',
            data: {
                cp_id: cp_id,
            },
            success: function (data) {
                var status = data.status;

                var sp_data = data.data;
                if (status == 1) {
                    $('#p_id').val(sp_data.p_id);
                    var p_state = sp_data.p_state;
                    if (p_state == 1) {
                        $('#tabcheck5').parent().show();
                        $('#tab_1_5').show();
                        var p_state_str = '运行中';
                        $('#p_state').val(p_state_str);
                        $('#setup_time').val(sp_data.setup_time);
                        $('#update_time').val(sp_data.update_time);
                        $('#supplement_start_time').val(sp_data.start_time);
                        $('#supplement_end_time').val(sp_data.end_time);
                        $('#progress_time').val(sp_data.progress_time);
                    } else {
                        $('#navtabs a:first').tab('show');
                        $('#tabcheck5').parent().hide();
                        $('#tab_1_5').hide();
                        $('#supplement').show();
                    }
                } else {
                    $('#navtabs a:first').tab('show');
                    $('#tabcheck5').parent().hide();
                    $('#tab_1_5').hide();
                    $('#supplement').show();
                }
            },
            error: function () {
                alert('页面出现错误，请于管理员联系。')
            }
        });
    }

    $('a[data-toggle="tab"]').on('show.bs.tab', function (e) {
        cp_id = $('#cp_id').val();
        var target_id = e.target.id;
        if (target_id == 'tabcheck2') {
            tabCheck2();
        }
        if (target_id == 'tabcheck3') {
            tabCheck3();
        }
        if (target_id == 'tabcheck4') {
            tabCheck4();
        }
        if (target_id == 'tabcheck5') {
            tabCheck5();
        }
        if (target_id == 'tabcheck1') {
            tabCheck1();
        }
    });

    // 查看详情
    $('#sample_2 tbody').on('click', 'button#view', function () {
        $('#static').modal('show');
        var table2 = $('#sample_2').DataTable();
        var data = table2.row($(this).parents('tr')).data();

        $('#target_code').val(data.target_code);
        $('#target_name').val(data.target_name);
        $('#source_content').val(data.source_content);
        $('#storage_table_name').val(data.storage_table_name);
        $('#storage_fields').val(data.storage_fields);
    });

    // 测试
    $('#test').click(function () {
        var selectArray = [];
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
                    // 测试结束弹出模态框，展示数据或者错误信息
                    var status = data.status;
                    var result_list = JSON.parse(data.data);

                    if (status == 1) {
                        $('#static2').modal('show');
                        $('#test_data').empty();
                        var target_result = '';
                        for (var i = 0; i < result_list.length; i++) {
                            target_result += '<ul><span style="font-weight:bold; margin-left: -20px;">指标名称：</span>' + result_list[i].target_name +
                                '<li>指标ID：' + result_list[i].target_id + '</li>' +
                                '<li>指标CODE：' + result_list[i].target_code + '</li>' +
                                '<li>查询状态：' + result_list[i].status + '</li>' +
                                '<li>响应数据：' + result_list[i].data + '</li>' +
                                '</ul>'
                        }
                        $('#test_data').append(target_result);
                    } else {
                        alert('测试失败。')
                    }

                },
                error: function (e) {
                    alert("页面出现错误，请于管理员联系。");
                }
            });
        }
    });
    // 补取
    $('#start_time').datetimepicker({
        autoclose: true,
        format: 'yyyy-mm-dd hh:ii:ss',
        minView: 0,
        minuteStep: 1
    });
    $('#end_time').datetimepicker({
        autoclose: true,
        format: 'yyyy-mm-dd hh:ii:ss',
        minView: 0,
        minuteStep: 1
    });
    $('#supplement').click(function () {
        var selectArray = [];
        $("input[name=selecttarget]:checked").each(function () {
            selectArray.push($(this).val());
        });
        if (selectArray.length < 1) {
            alert("请至少选择一个指标");
        } else {
            $('#selectArray').val(selectArray);

            // 弹出模态框
            $('#static1').modal({backdrop: "static"});
            $('#start_time').val('');
            $('#end_time').val('');
        }
    });
    $('#do_supplement').click(function () {
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../supplement_process/",
            data: {
                selectedtarget: $('#selectArray').val(),
                start_time: $('#start_time').val(),
                end_time: $('#end_time').val(),
                cp_id: $('#cp_id').val()
            },
            success: function (data) {
                var status = data.status;
                if (status == 1) {
                    $('#supplement').hide();
                    $('#static1').modal('hide');
                    $('#tabcheck5').parent().show();
                }
                alert(data.data);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    });
    $('#refresh').click(function () {
        // 判断当前激活的TAB来刷新局部
        var tab_id = '';
        $('.tab-pane').each(function () {
            // 如果tab5隐藏了，直接跳转tab1
            if ($(this).attr('class').indexOf('active in') != -1) {
                // 获取激活的tab刷新数据
                tab_id = $(this).prop('id');
                if (tab_id == 'tab_1_1') {
                    tabCheck1();
                } else if (tab_id == 'tab_1_2') {
                    tabCheck2();

                } else if (tab_id == 'tab_1_3') {
                    tabCheck3();

                } else if (tab_id == 'tab_1_4') {
                    tabCheck4();

                } else {
                    tabCheck5();
                }
                return;
            }
        });
    });
});