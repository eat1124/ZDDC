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
                        }

                        // app/circle
                        $('#app_name').val(data.node.data.a_name);
                        $('#circle_name').val(data.node.data.c_name);

                        $('#source_id').val(data.node.data.s_id);
                        $('#app_id').val(data.node.data.a_id);
                        $('#circle_id').val(data.node.data.c_id);
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
});