$(document).ready(function () {
    function getUrl() {
        var url = document.location.toString();
        var arrUrl = url.split("//");

        var start = arrUrl[1].indexOf("/");
        var relUrl = arrUrl[1].substring(start);//stop省略，截取从start开始到结尾的所有字符

        if (relUrl.indexOf("?") != -1) {
            relUrl = relUrl.split("?")[0];
        }
        relUrl = relUrl.split("/");
        var tUrl = "get_report_search_data/";
        for (var i=0; i<relUrl.length; i++){
            if (!relUrl[i]){
                tUrl = "../" + tUrl;
            }
        }
        return tUrl;
    }
    var gUrl = getUrl();
    function getReportSearchTree() {
        $.ajax({
            type: "POST",
            dataType: "json",
            url: gUrl,
            data: {
                "app_id": $('#app_id').val()
            },
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
                "mRender": function(data, type, full) {
                return "<a href='http://" + full.report_server + "/webroot/decision/view/report?viewlet=" + full.relative_file_name + "&curdate=" + $('#reporting_date').val()  + "&op=write" + "' target='_blank'>" + full.name + "</a>"
            }
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