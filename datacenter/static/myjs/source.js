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

                                $("#title").text("新建");
                                $("#id").val("0");
                                $("#pid").val(obj.id);

                                $("#name").val("");
                                $("#code").val("");
                                $("#sort").val("");
                                $("#connection").val("");
                                $("#sourcetype option:selected").removeProp("selected");
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
                                            url: "../del_source/",
                                            data: {
                                                id: obj.id,
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
                                url: "../move_source/",
                                data: {
                                    id: data.node.id,
                                    parent: data.parent,
                                    old_parent: data.old_parent,
                                    position: data.position,
                                    old_position: data.old_position,
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
                        $("#formdiv").hide();
                    } else {
                        $("#formdiv").show();
                    }
                    $("#title").text(data.node.text);
                    $("#id").val(data.node.id);
                    $("#pid").val(data.node.parent);
                    $("#name").val(data.node.text);
                    $("#sourcetype").val(data.node.data.sourcetype);
                    $("#code").val(data.node.data.code);
                    $("#sort").val(data.node.data.sort);
                    $("#connection").val(data.node.data.connection);
                    $("#p_name").val(data.node.data.p_name);
                })
        },
        error: function (e) {
            alert("流程读取失败，请于客服联系。");
        }
    });
}


customTree();


$('#save').click(function () {
    $.ajax({
        type: "POST",
        url: "../source_save/",
        data: {
            id: $("#id").val(),
            pid: $("#pid").val(),
            name: $("#name").val(),
            code: $("#code").val(),
            connection: $("#connection").val(),
            sourcetype: $("#sourcetype option:selected").val(),
        },
        success: function (data) {
            if (data["data"]) {
                alert("保存成功！");
                $("#id").val(data.data);
            } else {
                alert(data["result"])
            }
            $('#tree_2').jstree("destroy");
            customTree();
        },
        error: function (e) {
            alert("保存失败，请于客服联系。");
        }
    });
});