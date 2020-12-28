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
                "width": "350px",
                "targets": -4,
                "mRender": function(data, type, full) {
                    var reporting_date = full.reporting_date;
                    // 月报
                    if (full.report_type_id == 23){
                         var curYear = reporting_date.split("-") [0];
                         var curMonth = reporting_date.split("-") [1];
                         return "<a href='http://" + full.report_server + "/webroot/decision/view/report?viewlet=" + full.relative_file_name +
                            "&curYear=" + curYear + "&curMonth=" + curMonth  + "&op=write" + "' target='_blank'>" + full.name + "</a>"
                    }
                    // 季报
                    if (full.report_type_id == 24){
                        // 2020
                        var curYear = reporting_date.split("-") [0];
                        // 03
                        var season = reporting_date.split("-") [1];
                        var curSeason = '';
                        if (season == '03'){
                            curSeason = 1
                        }
                        else if (season == '06'){
                            curSeason = 2
                        }
                        else if (season == '09'){
                            curSeason = 3
                        }
                        else {
                            curSeason = 4
                        }
                         return "<a href='http://" + full.report_server + "/webroot/decision/view/report?viewlet=" + full.relative_file_name +
                            "&curYear=" + curYear + "&curSeason=" + curSeason  + "&op=write" + "' target='_blank'>" + full.name + "</a>"
                    }
                    // 半年报
                    if (full.report_type_id == 25){
                        // 2020
                        var curYear = reporting_date.split("-") [0];
                        // 06
                        var halfyear = reporting_date.split("-") [1];
                        var curHalfyear = '';
                        if (halfyear == '06'){
                            curHalfyear = '上'
                        }else {
                            curHalfyear = '下'
                        }
                        return "<a href='http://" + full.report_server + "/webroot/decision/view/report?viewlet=" + full.relative_file_name +
                            "&curYear=" + curYear + "&curHalfyear=" + curHalfyear  + "&op=write" + "' target='_blank'>" + full.name + "</a>"
                    }
                    // 年报
                    if (full.report_type_id == 26){
                        // 2020
                        var curYear = reporting_date.split("-") [0];

                        return "<a href='http://" + full.report_server + "/webroot/decision/view/report?viewlet=" + full.relative_file_name +
                            "&curYear=" + curYear + "&op=write" + "' target='_blank'>" + full.name + "</a>"
                    }
                    // 日报
                    else {
                        return "<a href='http://" + full.report_server + "/webroot/decision/view/report?viewlet=" + full.relative_file_name +
                        "&curdate=" + reporting_date  + "&op=write" + "' target='_blank'>" + full.name + "</a>"
                    }
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