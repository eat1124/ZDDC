$(document).ready(function () {
    function getReportSearchTree() {
        $.ajax({
            type: "POST",
            dataType: "json",
            url: "../get_report_search_data/",
            data: {},
            success: function (data) {
                var treeData = data.data;
                $('#report_search_tree').jstree('destroy');
                $('#report_search_tree').jstree({
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
                        if (data.node.type == "file") {
                            $('#form_div').show();
                            customReportDataTable(data.node.data);
                        } else {
                            $('#form_div').hide();
                        }
                    });
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    }

    getReportSearchTree();

    function customReportDataTable(data) {
        $("#report_table").dataTable().fnDestroy();
        $('#report_table').dataTable({
            "bAutoWidth": false,
            "bSort": false,
            "bProcessing": true,
            "data": data,
            "columns": [
                {"data": "write_time"},
                {"data": null},
                {"data": "code"},
                {"data": "person"},
                {"data": "report_time"},
            ],
            "columnDefs": [{
                "data": null,
                "targets": -4,
                "render": function (data, type, full) {
                    var name = full.name,
                        url = full.url;
                    return "<td><a href='" + url + "' target='_blank'>" + name + "</a></td>"
                },
            }],
            "oLanguage": {
                "sLengthMenu": "每页显示 _MENU_ 条记录",
                "sZeroRecords": "没有检索到数据",
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
        });
    }


});