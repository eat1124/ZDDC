var treedata = "";

// 定义构造树的函数
function customTree() {
    $.ajax({
        type: "POST",
        url: "../custom_source_tree/",
        data: {
            name: $("#name").val(),
            id: $("#id").val(),
            pid: $("#pid").val(),
        },
        dataType: "json",
        success: function (data) {
            JSON.stringify(data.treedata);
            treedata = data.treedata;
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
                                $("#formdiv").show();
                                var inst = jQuery.jstree.reference(data.reference),
                                    obj = inst.get_node(data.reference);

                                $("#group").empty();
                                $("#title").text("新建");
                                $("#id").val("0");
                                $("#pid").val(obj.id);
                                $("#time").val("");
                                $("#skip option:selected").removeProp("selected");
                                $("#approval option:selected").removeProp("selected");
                                $("#group option:selected").removeProp("selected");
                                $("#rto_count_in option:selected").removeProp("selected");
                                $("#name").val("");

                                var groupInfoList = obj.data.allgroups.split("&");
                                for (var i = 0; i < groupInfoList.length - 1; i++) {
                                    var singlegroupInfoList = groupInfoList[i].split("+");
                                    $("#group").append('<option value="' + singlegroupInfoList[0] + '">' + singlegroupInfoList[1] + '</option>')
                                }
                                // inst.add_node(obj);
                            }
                        },
                        "删除": {
                            "label": "删除",
                            "action": function (data) {
                                var inst = jQuery.jstree.reference(data.reference),
                                    obj = inst.get_node(data.reference);
                                if (obj.children.length > 0)
                                    alert("节点下还有其他节点或功能，无法删除。");
                                else if (obj.data.verify == "first_node") {
                                    alert("该项为流程名称，无法删除。");
                                } else {
                                    if (confirm("确定要删除此节点？删除后不可恢复。")) {
                                        $.ajax({
                                            type: "POST",
                                            url: "../del_step/",
                                            data: {
                                                id: obj.id,
                                                process_id: $("#process option:selected").val(),
                                            },
                                            success: function (data) {
                                                if (data == 1) {
                                                    inst.delete_node(obj);
                                                    alert("删除成功！");
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
                        location.reload()
                    } else {
                        if (data.parent == "#") {
                            alert("禁止新建根节点。");
                            location.reload()
                        } else {
                            $.ajax({
                                type: "POST",
                                url: "../move_step/",
                                data: {
                                    id: data.node.id,
                                    parent: data.parent,
                                    old_parent: data.old_parent,
                                    position: data.position,
                                    old_position: data.old_position,
                                    process_id: $("#process option:selected").val(),
                                },
                                success: function (data) {
                                    var selectid = $("#id").val();
                                    if (selectid == moveid) {
                                        var res = data.split('^');
                                        $("#pid").val(res[1]);
                                        $("#pname").val(res[0]);
                                    }
                                },
                                error: function (e) {
                                    alert("移动失败，请于管理员联系。");
                                    location.reload()
                                }
                            });


                        }
                    }
                })
                .bind('select_node.jstree', function (event, data) {
                    if (data.node.data.verify == "first_node") {
                        alert(111111)
                        $("#formdiv").hide();
                    } else {
                        $("#formdiv").show();
                    }
                    $("#formdiv").show();
                    $("#title").text(data.node.text);
                    $("#id").val(data.node.id);
                    $("#pid").val(data.node.parent);
                    $("#name").val(data.node.text);
                    $("#sourcetype").val(data.node.data.sourcetype);
                    $("#code").val(data.node.data.code);
                    $("#sort").val(data.node.data.sort);


                    /*
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
                    */

                })
        },
        error: function (e) {
            alert("流程读取失败，请于客服联系。");
        }
    });
}


customTree();


$('#sample_1 tbody').on('click', 'button#select', function () {
    var table = $('#sample_1').DataTable();
    var data = table.row($(this).parents('tr')).data();
    $("#scriptcode").val(data.code);
    $("#script_name").val(data.name);
    $("#scriptip").val(data.ip);
    // $("#scriptport").val(data.port);
    $("#scripttype").val(data.type);
    // $("#scriptruntype").val(data.runtype);
    $("#scriptusername").val(data.username);
    $("#scriptpassword").val(data.password);
    $("#scriptfilename").val(data.filename);
    // $("#scriptparamtype").val(data.paramtype);
    // $("#scriptparam").val(data.param);
    $("#scriptscriptpath").val(data.scriptpath);
    $("#success_text").val(data.success_text);
    $("#log_address").val(data.log_address);

    // $("#scriptrunpath").val(data.runpath);
    // $("#scriptcommand").val("cd " + $("#scriptscriptpath").val() + ";" + $("#scriptrunpath").val() + "/" + $("#scriptfilename").val() + " " + $("#scriptparam").val());
    // $("#scriptmaxtime").val(data.maxtime);
    // $("#scripttime").val(data.time);
    $('#static1').modal('hide');
});


$('#save').click(function () {
    $.ajax({
        type: "POST",
        url: "../setpsave/",
        data: {
            id: $("#id").val(),
            pid: $("#pid").val(),
            name: $("#name").val(),
            time: $("#time").val(),
            skip: $("#skip").val(),
            approval: $("#approval").val(),
            group: $("#group").val(),
            rto_count_in: $("#rto_count_in").val(),
            new: $("#new").val(),
            process_id: $("#process option:selected").val(),
            remark: $("#remark").val()
        },
        success: function (data) {
            // $("#name_" + $("#id").val()).text($("#name").val());
            // $("#time_" + $("#id").val()).val($("#time").val());
            // $("#approval_" + $("#id").val()).val($("#approval").val());
            // $("#skip_" + $("#id").val()).val($("#skip").val());
            // $("#group_" + $("#id").val()).val($("#group").val());
            // var approvaltext = ""
            // if ($("#approval").val() == "1")
            //     approvaltext = "需审批"
            // var skiptext = ""
            // if ($("#skip").val() == "1")
            //     skiptext = "可跳过"
            // $("#curstring_" + $("#id").val()).text(approvaltext + skiptext);
            if (data["data"]) {
                $("#id").val(data.data);
            }
            alert("保存成功！");
            $('#tree_2').jstree("destroy");

            customTree();
        },
        error: function (e) {
            alert("保存失败，请于客服联系。");
        }
    });
});