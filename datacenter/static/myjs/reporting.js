$(document).ready(function () {

    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "bPaginate" : false,
        "bFilter" : false,
        "ajax": "../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val()  + "&operationtype=15",
        "columns": [
            {"data": "id"},
            {"data": "target_name"},
            {"data": "target_code"},
            {"data": "target_businesstypename"},
            {"data": "target_unitname"},
            {"data": "curvalue"},
            {"data": "cumulativemonth"},
            {"data": "cumulativequarter"},
            {"data": "cumulativehalfyear"},
            {"data": "cumulativeyear"},
        ],

        "columnDefs": [
            {
            "targets": -5,
            "mRender":function(data,type,full){
                        $('.curvaluedate_').datetimepicker({
                            format: 'yyyy-mm-dd hh:ii:ss',
                            autoclose: true,
                        });

                        if (full.target_datatype == 'numbervalue'){
                            return "<input id='table1_curvalue_" + full.id + "' name='table1_curvalue'  type='number' value='" + data + "'></input>"
                        }
                        if (full.target_datatype == 'date'){
                            return "<input class='curvaluedate_'autocomplete='off' style = 'width:153px;height:26px;' id='table1_curvaluedate_" + full.id + "' name='table1_curvaluedate'  type='datetime'  value='" + full.curvaluedate + "'></input>"
                        }
                        if (full.target_datatype == 'text'){
                            return "<input  id='table1_curvaluetext_" + full.id + "' name='table1_curvaluetext'  type='text' value='" + full.curvaluetext + "'></input>"
                        }
                    }
            },
            {
            "targets": -4,
            "mRender":function(data,type,full){
                        return "<input disabled id='table1_cumulativemonth_" + full.id + "' name='table1_cumulativemonth'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -3,
            "mRender":function(data,type,full){
                        return "<input disabled id='table1_cumulativequarter_" + full.id + "' name='table1_cumulativequarter'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -2,
            "mRender":function(data,type,full){
                        return "<input disabled id='table1_cumulativehalfyear_" + full.id + "' name='table1_cumulativehalfyear'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -1,
            "mRender":function(data,type,full){
                        return "<input disabled id='table1_cumulativeyear_" + full.id + "' name='table1_cumulativeyear'  type='text' value='" + data + "'></input>"
                    }
            },
        ],
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
        "fnDrawCallback": function( data ) {
            if(data.aoData.length>0)
            {
                $("#new1").hide();
                $("#save1").show();
                $("#del1").show();
            }
            else
            {
                $("#new1").show();
                $("#save1").hide();
                $("#del1").hide();
            }
        }
    });

    // 行按钮
    $('#sample_1 tbody').on('change', 'input[name="table1_curvalue"]', function () {
            var table = $('#sample_1').DataTable();
            var data = table.row($(this).parents('tr')).data();
            if(data.target_cumulative=='是') {
                $('#table1_cumulativemonth_' + data.id).val(Number(data.cumulativemonth) - Number(data.curvalue) + Number($('#table1_curvalue_' + data.id).val()))
                $('#table1_cumulativequarter_' + data.id).val(Number(data.cumulativequarter) - Number(data.curvalue) + Number($('#table1_curvalue_' + data.id).val()))
                $('#table1_cumulativehalfyear_' + data.id).val(Number(data.cumulativehalfyear) - Number(data.curvalue) + Number($('#table1_curvalue_' + data.id).val()))
                $('#table1_cumulativeyear_' + data.id).val(Number(data.cumulativeyear) - Number(data.curvalue) + Number($('#table1_curvalue_' + data.id).val()))
            }
    });

    $('#sample_2').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "bPaginate" : false,
        "bFilter" : false,
        "ajax": "../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val()  + "&operationtype=16",
        "columns": [
            {"data": "id"},
            {"data": "target_name"},
            {"data": "target_code"},
            {"data": "target_businesstypename"},
            {"data": "target_unitname"},
            {"data": "curvalue"},
            {"data": "cumulativemonth"},
            {"data": "cumulativequarter"},
            {"data": "cumulativehalfyear"},
            {"data": "cumulativeyear"},
            {"data": null},
        ],

        "columnDefs": [
            {
            "targets": -6,
            "mRender":function(data,type,full){
                        return "<input id='table2_curvalue_" + full.id + "' name='table2_curvalue'  type='number' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -5,
            "mRender":function(data,type,full){
                        return "<input disabled id='table2_cumulativemonth_" + full.id + "' name='table2_cumulativemonth'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -4,
            "mRender":function(data,type,full){
                        return "<input disabled id='table2_cumulativequarter_" + full.id + "' name='table2_cumulativequarter'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -3,
            "mRender":function(data,type,full){
                        return "<input disabled id='table2_cumulativehalfyear_" + full.id + "' name='table2_cumulativehalfyear'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -2,
            "mRender":function(data,type,full){
                        return "<input disabled id='table2_cumulativeyear_" + full.id + "' name='table2_cumulativeyear'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -1,
            "data": null,
            "width": "100px",
            "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static2'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>"
            }
        ],
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
        "fnDrawCallback": function( data ) {
            if(data.aoData.length>0)
            {
                $("#new2").hide();
                $("#save2").show();
                $("#del2").show();
                $("#reset2").show();
            }
            else
            {
                $("#new2").show();
                $("#save2").hide();
                $("#del2").hide();
                $("#reset2").hide();
            }
        }
    });
    // 行按钮
    $('#sample_2 tbody').on('change', 'input[name="table2_curvalue"]', function () {
            var table = $('#sample_2').DataTable();
            var data = table.row($(this).parents('tr')).data();
            if(data.target_cumulative=='是') {
                $('#table2_cumulativemonth_' + data.id).val(Number(data.cumulativemonth) - Number(data.curvalue) + Number($('#table2_curvalue_' + data.id).val()))
                $('#table2_cumulativequarter_' + data.id).val(Number(data.cumulativequarter) - Number(data.curvalue) + Number($('#table2_curvalue_' + data.id).val()))
                $('#table2_cumulativehalfyear_' + data.id).val(Number(data.cumulativehalfyear) - Number(data.curvalue) + Number($('#table2_curvalue_' + data.id).val()))
                $('#table2_cumulativeyear_' + data.id).val(Number(data.cumulativeyear) - Number(data.curvalue) + Number($('#table2_curvalue_' + data.id).val()))
            }
    });

    $('#sample_3').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "bPaginate" : false,
        "bFilter" : false,
        "ajax": "../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val()  + "&operationtype=17",
        "columns": [
            {"data": "id"},
            {"data": "target_name"},
            {"data": "target_code"},
            {"data": "target_businesstypename"},
            {"data": "target_unitname"},
            {"data": "curvalue"},
            {"data": "cumulativemonth"},
            {"data": "cumulativequarter"},
            {"data": "cumulativehalfyear"},
            {"data": "cumulativeyear"},
            {"data": null},
        ],

        "columnDefs": [
            {
            "targets": -6,
            "mRender":function(data,type,full){
                        $('.curvaluedate_').datetimepicker({
                            format: 'yyyy-mm-dd hh:ii:ss',
                            autoclose: true,
                        });

                        if (full.target_datatype == 'numbervalue'){
                            return "<input id='table3_curvalue_" + full.id + "' name='table3_curvalue'  type='number' value='" + data + "'></input>"
                        }
                        if (full.target_datatype == 'date'){
                            return "<input class='curvaluedate_'autocomplete='off' style = 'width:153px;height:26px;' id='table3_curvaluedate_" + full.id + "' name='table3_curvaluedate'  type='datetime'  value='" + full.curvaluedate + "'></input>"
                        }
                        if (full.target_datatype == 'text'){
                            return "<input  id='table3_curvaluetext_" + full.id + "' name='table3_curvaluetext'  type='text' value='" + full.curvaluetext + "'></input>"
                        }
                    }
            },
            {
            "targets": -5,
            "mRender":function(data,type,full){
                        return "<input disabled id='table3_cumulativemonth_" + full.id + "' name='table3_cumulativemonth'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -4,
            "mRender":function(data,type,full){
                        return "<input disabled id='table3_cumulativequarter_" + full.id + "' name='table3_cumulativequarter'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -3,
            "mRender":function(data,type,full){
                        return "<input disabled id='table3_cumulativehalfyear_" + full.id + "' name='table3_cumulativehalfyear'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -2,
            "mRender":function(data,type,full){
                        return "<input disabled id='table3_cumulativeyear_" + full.id + "' name='table3_cumulativeyear'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -1,
            "data": null,
            "width": "100px",
            "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static3'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>"
            }
        ],
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
        "fnDrawCallback": function( data ) {
            if(data.aoData.length>0)
            {
                $("#new3").hide();
                $("#save3").show();
                $("#del3").show();
                $("#reset3").show();
            }
            else
            {
                $("#new3").show();
                $("#save3").hide();
                $("#del3").hide();
                $("#reset3").hide();
            }
        }
    });
    // 行按钮
    $('#sample_3 tbody').on('change', 'input[name="table3_curvalue"]', function () {
            var table = $('#sample_3').DataTable();
            var data = table.row($(this).parents('tr')).data();
            if(data.target_cumulative=='是') {
                $('#table3_cumulativemonth_' + data.id).val(Number(data.cumulativemonth) - Number(data.curvalue) + Number($('#table3_curvalue_' + data.id).val()))
                $('#table3_cumulativequarter_' + data.id).val(Number(data.cumulativequarter) - Number(data.curvalue) + Number($('#table3_curvalue_' + data.id).val()))
                $('#table3_cumulativehalfyear_' + data.id).val(Number(data.cumulativehalfyear) - Number(data.curvalue) + Number($('#table3_curvalue_' + data.id).val()))
                $('#table3_cumulativeyear_' + data.id).val(Number(data.cumulativeyear) - Number(data.curvalue) + Number($('#table3_curvalue_' + data.id).val()))
            }
    });

    $('#sample_4').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "bPaginate" : false,
        "bFilter" : false,
        "ajax": "../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val()  + "&operationtype=0",
        "columns": [
            {"data": "id"},
            {"data": "target_name"},
            {"data": "target_code"},
            {"data": "target_businesstypename"},
            {"data": "target_unitname"},
            {"data": "curvalue"},
            {"data": "cumulativemonth"},
            {"data": "cumulativequarter"},
            {"data": "cumulativehalfyear"},
            {"data": "cumulativeyear"},
        ],

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
    });

    $('#reporting_date').change(function () {
        var table1 = $('#sample_1').DataTable();
        table1.ajax.url("../../../reporting_data?app=" + $('#app').val()  + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val()  + "&operationtype=15").load();
        var table2 = $('#sample_2').DataTable();
        table2.ajax.url("../../../reporting_data?app=" + $('#app').val()  + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val()  + "&operationtype=16").load();
        var table3 = $('#sample_3').DataTable();
        table3.ajax.url("../../../reporting_data?app=" + $('#app').val()  + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val()  + "&operationtype=17").load();
        var table4 = $('#sample_4').DataTable();
        table4.ajax.url("../../../reporting_data?app=" + $('#app').val()  + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val()  + "&operationtype=0").load();
    })


    if($('#cycletype').val()=="10") {
        $('#reporting_date').datetimepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            startView: 2,
            minView: 2,
        });
    }
    if($('#cycletype').val()=="11") {
        $('#reporting_date').datetimepicker({
            format: 'yyyy-mm',
            autoclose: true,
            startView: 3,
            minView: 3,
        });
    }
    if($('#cycletype').val()=="12") {
        $('#reporting_date').datetimepicker({
            format: 'yyyy-mm',
            autoclose: true,
            startView: 3,
            minView: 3,
        });
    }
    if($('#cycletype').val()=="13") {
        $('#reporting_date').datetimepicker({
            format: 'yyyy-mm',
            autoclose: true,
            startView: 3,
            minView: 3,
        });
    }
    if($('#cycletype').val()=="14") {
        $('#reporting_date').datetimepicker({
            format: 'yyyy',
            autoclose: true,
            startView: 4,
            minView: 4,
        });
    }

    $("#new1").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../../../reporting_new/",
            data:
                {
                    app: $('#app').val(),
                    cycletype:$('#cycletype').val(),
                    reporting_date:$('#reporting_date').val(),
                    operationtype:15,

                },
            success: function (data) {
                if (data == 1) {
                    table.ajax.reload();
                    $("#new1").hide();
                    $("#save1").show();
                    $("#del1").show();
                    alert("新增成功！");
                }
                else
                    alert("新增失败，请于管理员联系。");
            },
            error: function (e) {
                alert("新增失败，请于管理员联系。");
            }
        });
    });
    $("#del1").click(function () {
        if (confirm("确定要删除表中数据？")) {
            var table = $('#sample_1').DataTable();
            $.ajax({
                type: "POST",
                url: "../../../reporting_del/",
                data:
                    {
                        app: $('#app').val(),
                        cycletype:$('#cycletype').val(),
                        reporting_date:$('#reporting_date').val(),
                        operationtype:15,

                    },
                success: function (data) {
                    if (data == 1) {
                        table.ajax.reload();
                        $("#new1").show();
                        $("#save1").hide();
                        $("#del1").hide();
                        alert("删除成功！");
                    }
                    else
                        alert("删除失败，请于管理员联系。");
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    $('#save1').click(function () {
        $("Element").blur()
        var table = $('#sample_1').DataTable().data();
        var savedata=[]
    　　$.each(table,function(i,item){
            savedata.push({"id":item.id,"curvalue":$('#table1_curvalue_' + item.id).val(),"curvaluedate":$('#table1_curvaluedate_' + item.id).val(),"curvaluetext":$('#table1_curvaluetext_' + item.id).val(),"cumulativemonth":$('#table1_cumulativemonth_' + item.id).val(),"cumulativequarter":$('#table1_cumulativequarter_' + item.id).val(),"cumulativehalfyear":$('#table1_cumulativehalfyear_' + item.id).val(),"cumulativeyear":$('#table1_cumulativeyear_' + item.id).val()})
    　　});
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../../reporting_save/",
            data:
                {
                    operationtype:15,
                    savedata:JSON.stringify(savedata),
                },
            success: function (data) {
                var myres = data["res"];
                if (myres == "保存成功。") {
                    table.ajax.reload();
                }
                alert(myres);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    })

    $("#new2").click(function () {
        var table = $('#sample_2').DataTable();
        $.ajax({
            type: "POST",
            url: "../../../reporting_new/",
            data:
                {
                    app: $('#app').val(),
                    cycletype:$('#cycletype').val(),
                    reporting_date:$('#reporting_date').val(),
                    operationtype:16,

                },
            success: function (data) {
                if (data == 1) {
                    table.ajax.reload();
                    $("#new2").hide();
                    $("#save2").show();
                    $("#del2").show();
                    $("#reset2").show();
                    alert("新增成功！");
                }
                else
                    alert("新增失败，请于管理员联系。");
            },
            error: function (e) {
                alert("新增失败，请于管理员联系。");
            }
        });
    });
    $("#del2").click(function () {
        if (confirm("确定要删除表中数据？")) {
            var table = $('#sample_2').DataTable();
            $.ajax({
                type: "POST",
                url: "../../../reporting_del/",
                data:
                    {
                        app: $('#app').val(),
                        cycletype:$('#cycletype').val(),
                        reporting_date:$('#reporting_date').val(),
                        operationtype:16,

                    },
                success: function (data) {
                    if (data == 1) {
                        table.ajax.reload();
                        $("#new2").show();
                        $("#save2").hide();
                        $("#del2").hide();
                        $("#reset2").hide();
                        alert("删除成功！");
                    }
                    else
                        alert("删除失败，请于管理员联系。");
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    $('#save2').click(function () {
        $("Element").blur()
        var table = $('#sample_2').DataTable().data();
        var savedata=[]
    　　$.each(table,function(i,item){
            savedata.push({"id":item.id,"curvalue":$('#table2_curvalue_' + item.id).val(),"cumulativemonth":$('#table2_cumulativemonth_' + item.id).val(),"cumulativequarter":$('#table2_cumulativequarter_' + item.id).val(),"cumulativehalfyear":$('#table2_cumulativehalfyear_' + item.id).val(),"cumulativeyear":$('#table2_cumulativeyear_' + item.id).val()})
    　　});
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../../reporting_save/",
            data:
                {
                    operationtype:16,
                    savedata:JSON.stringify(savedata),
                },
            success: function (data) {
                var myres = data["res"];
                if (myres == "保存成功。") {
                    table.ajax.reload();
                }
                alert(myres);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    })

    $("#new3").click(function () {
        var table = $('#sample_3').DataTable();
        $.ajax({
            type: "POST",
            url: "../../../reporting_new/",
            data:
                {
                    app: $('#app').val(),
                    cycletype:$('#cycletype').val(),
                    reporting_date:$('#reporting_date').val(),
                    operationtype:17,

                },
            success: function (data) {
                if (data == 1) {
                    table.ajax.reload();
                    $("#new3").hide();
                    $("#save3").show();
                    $("#del3").show();
                    $("#reset3").show();
                    alert("新增成功！");
                }
                else
                    alert("新增失败，请于管理员联系。");
            },
            error: function (e) {
                alert("新增失败，请于管理员联系。");
            }
        });
    });
    $("#del3").click(function () {
        if (confirm("确定要删除表中数据？")) {
            var table = $('#sample_3').DataTable();
            $.ajax({
                type: "POST",
                url: "../../../reporting_del/",
                data:
                    {
                        app: $('#app').val(),
                        cycletype:$('#cycletype').val(),
                        reporting_date:$('#reporting_date').val(),
                        operationtype:17,

                    },
                success: function (data) {
                    if (data == 1) {
                        table.ajax.reload();
                        $("#new3").show();
                        $("#save3").hide();
                        $("#del3").hide();
                        $("#reset3").hide();
                        alert("删除成功！");
                    }
                    else
                        alert("删除失败，请于管理员联系。");
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    $('#save3').click(function () {
        $("Element").blur()
        var table = $('#sample_3').DataTable().data();
        var savedata=[]
    　　$.each(table,function(i,item){
            savedata.push({"id":item.id,"curvalue":$('#table3_curvalue_' + item.id).val(),"curvaluedate":$('#table3_curvaluedate_' + item.id).val(),"curvaluetext":$('#table3_curvaluetext_' + item.id).val(),"cumulativemonth":$('#table3_cumulativemonth_' + item.id).val(),"cumulativequarter":$('#table3_cumulativequarter_' + item.id).val(),"cumulativehalfyear":$('#table3_cumulativehalfyear_' + item.id).val(),"cumulativeyear":$('#table3_cumulativeyear_' + item.id).val()})
    　　});
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../../reporting_save/",
            data:
                {
                    operationtype:17,
                    savedata:JSON.stringify(savedata),
                },
            success: function (data) {
                var myres = data["res"];
                if (myres == "保存成功。") {
                    table.ajax.reload();
                }
                alert(myres);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    })

});