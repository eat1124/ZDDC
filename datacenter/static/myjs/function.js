$(function () {
    $('#tree_2').jstree({
        'core': {
            "themes": {
                "responsive": false
            },
            "check_callback": true,
            'data': treedata
        },

        "types": {
            "node": {
                "icon": "fa fa-folder icon-state-warning icon-lg"
            },
            "fun": {
                "icon": "fa fa-file icon-state-warning icon-lg"
            }
        },
        "contextmenu": {
            "items": {
                "create": null,
                "rename": null,
                "remove": null,
                "ccp": null,
                "新建": {
                    "label": "新建",
                    "action": function (data) {
                        var inst = jQuery.jstree.reference(data.reference),
                            obj = inst.get_node(data.reference);
                        if (obj.type == "fun") {
                            alert("无法在功能下新建节点或功能。");
                        } else {
                            $("#app_div").show();
                            $("#works_div").show();
                            $("#visited_url_div").show();
                            $("#new_window_div").show();
                            $('input:radio[name=radio2]')[0].checked = true;
                            $("#title").text("新建");
                            $("#id").val("0");
                            $("#pid").val(obj.id);
                            $("#name").val("");
                            $("#pname").val(obj.text);
                            $("#url").val("");
                            $("#icon").val("");
                            $("#app").val("");

                            $("#save").show();
                        }
                    }
                },
                "删除": {
                    "label": "删除",
                    "action": function (data) {
                        var inst = jQuery.jstree.reference(data.reference),
                            obj = inst.get_node(data.reference);
                        if (obj.children.length > 0)
                            alert("节点下还有其他节点或功能，无法删除。");
                        else {
                            if (confirm("确定要删除此节点？删除后不可恢复。")) {
                                $.ajax({
                                    type: "POST",
                                    url: "../fundel/",
                                    data: {
                                        id: obj.id,
                                    },
                                    success: function (data) {
                                        if (data == 1) {
                                            inst.delete_node(obj);
                                            alert("删除成功！");
                                            window.location.href = '/function/';
                                        } else
                                            alert("删除失败，请于管理员联系。");
                                    },
                                    error: function (e) {
                                        alert("删除失败，请于管理员联系。");
                                    }
                                });
                            }
                        }
                    }
                },
            }
        },
        "plugins": ["contextmenu", "dnd", "types", "role"]
    })
        .on('move_node.jstree', function (e, data) {
            var moveid = data.node.id;
            if (data.old_parent == "#") {
                alert("根节点禁止移动。");
                location.reload();
            } else {
                if (data.parent == "#") {
                    alert("禁止新建根节点。");
                    location.reload();
                } else {
                    $.ajax({
                        type: "POST",
                        url: "../funmove/",
                        data: {
                            id: data.node.id,
                            parent: data.parent,
                            old_parent: data.old_parent,
                            position: data.position,
                            old_position: data.old_position,
                        },
                        success: function (data) {
                            if (data == "类型") {
                                alert("不能移动至功能下。");
                                location.reload();
                            } else {
                                var selectid = $("#id").val();
                                if (selectid == moveid) {
                                    var res = data.split('^')
                                    $("#pid").val(res[1]);
                                    $("#pname").val(res[0]);
                                }
                            }
                        },
                        error: function (e) {
                            alert("移动失败，请于管理员联系。");
                            location.reload();
                        }
                    });


                }
            }
        })
        .bind('select_node.jstree', function (event, data) {
            $("#formdiv").show();
            $("#title").text(data.node.text);
            $("#id").val(data.node.id);
            $("#pid").val(data.node.parent);
            $("#name").val(data.node.text);
            $("#pname").val(data.node.data.pname);
            $("#url").val(data.node.data.url);
            $("#icon").val(data.node.data.icon);
            $('#app_list').val(JSON.stringify(data.node.data.app_list));
            if (data.node.type == "fun") {
                $('input:radio[name=radio2]')[0].checked = true;
                $('#visited_url_div').show();
                $('#new_window_div').show();
            }
            if (data.node.type == "node") {
                $('input:radio[name=radio2]')[1].checked = true;
                $('#visited_url_div').hide();
                $('#new_window_div').hide();
            }
            if (data.node.parent == "#") {
                $("#save").hide();
            } else
                $("#save").show();

            if (data.node.data.app_div_show) {
                $("#app_div").show();
                $("#works_div").show();
            } else {
                $("#app_div").hide();
                $("#works_div").hide();
            }
            $("#app").empty();
            for (var i = 0; i < data.node.data.app_list.length; i++) {
                $("#app").append("<option " + data.node.data.app_list[i].app_state + " value='" + data.node.data.app_list[i].id + "' >" + data.node.data.app_list[i].app_name + "</option>");
            }

            $(".select2, .select2-multiple").select2({
                width: null
            });


            var eventNodeName = event.target.nodeName;
            var eventNodeName = event.target.nodeName;
            if (eventNodeName == 'INS') {
                return;
            } else if (eventNodeName == 'A') {
                var $subject = $(event.target).parent();
                if ($subject.find('ul').length > 0) {
                    $("#title").text($(event.target).text())
                } else {
                    //选择的id值
                    alert($(event.target).parents('li').attr('id'));
                }
            }

            // 业务
            var app_list = data.node.data.app_list;
            var app_id = $('#app').val();
            $('#works').empty();

            var work_options = customWorkOptions(app_id, app_list);
            $('#works').append(work_options);
            $('#works').val(data.node.data.selected_work);
            console.log(data.node.data.new_window)
            $('#new_window').val(data.node.data.new_window);
        });

    function customWorkOptions(app_id, app_list) {
        var pre_works_options = '<option></option>';
        for (var i = 0; i < app_list.length; i++) {
            if (app_list[i].id == app_id) {
                var works = eval(app_list[i].works);
                if (works) {
                    for (var j = 0; j < works.length; j++) {
                        pre_works_options += '<option ' + ' value="' + works[j].id + '">' + works[j].name + ' </option>';
                    }
                }
                break;
            }
        }
        return pre_works_options;
    }

    $('#app').change(function () {
        var app_id = $(this).val();
        var app_list = JSON.parse($('#app_list').val());
        $('#works').empty();
        var work_options = customWorkOptions(app_id, app_list);
        $('#works').append(work_options);
    });

    $("#error").click(function () {
        $(this).hide();
    });
    $(document).ready(function () {
        if ($("#mytype").val() == "fun")
            $('input:radio[name=radio2]')[0].checked = true;
        if ($("#mytype").val() == "node")
            $('input:radio[name=radio2]')[1].checked = true;
        $("input:radio[name=radio2]").change(function () {
            if ($("#fun:checked").val() == "fun") {
                $("#visited_url_div").show();
                $("#app_div").show();
                $("#works_div").show();
                $("#new_window_div").show();
            } else {
                $("#visited_url_div").hide();
                $("#app_div").hide();
                $("#works_div").hide();
                $("#new_window_div").hide();
            }
        })
    });

});