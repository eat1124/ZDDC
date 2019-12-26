// 定位公式框中鼠标的位置
function getTxt1CursorPosition(id){
    var oTxt1 = document.getElementById(id);
    var cursurPosition=-1;
    try{
        if(oTxt1.selectionStart){//非IE浏览器
            cursurPosition= oTxt1.selectionStart;
            }else{//IE

            var range = document.selection.createRange();
            range.moveStart("character",-oTxt1.value.length);
            cursurPosition=range.text.length;
            }
        }catch(err){
        cursurPosition=0
     }
    $('#formula').attr({'seat':cursurPosition})
}

$(document).ready(function () {
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../../target_data/?search_adminapp=" + $('#adminapp').val(),
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "code"},
            {"data": "operationtype_name"},
            {"data": "cycletype_name"},
            {"data": "businesstype_name"},
            {"data": "unit_name"},
            {"data": null}
        ],

        "columnDefs": [{
            "targets": -1,
            "data": null,
            "width": "100px",
            "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>"
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
        }
    });

    // 行按钮
    $('#sample_1 tbody').on('click', 'button#delrow', function () {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#sample_1').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../../target_del/",
                data:
                    {
                        id: data.id,
                    },
                success: function (data) {
                    if (data == 1) {
                        table.ajax.reload();
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
    $('#sample_1 tbody').on('click', 'button#edit', function () {
        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();

        $("#id").val(data.id);
        $("#name").val(data.name);
        $("#code").val(data.code);
        $("#operationtype").val(data.operationtype);
        $("#cycletype").val(data.cycletype);
        $("#businesstype").val(data.businesstype);
        $("#unit").val(data.unit);
        $("#magnification").val(data.magnification);
        $("#digit").val(data.digit);
        $("#upperlimit").val(data.upperlimit);
        $("#lowerlimit").val(data.lowerlimit);
        $("#cumulative").val(data.cumulative);
        $("#sort").val(data.sort);

        $("#formula").val(data.formula);

        $("#cycle").val(data.cycle);
        $("#source").val(data.source);
        $("#sourcetable").val(data.sourcetable);
        $("#sourcesis").val(data.sourcesis);
        $("#sourcefields").val(data.sourcefields);
        $("#sourceconditions").val(data.sourceconditions);
        $("#storage").val(data.storage);
        $("#storagetag").val(data.storagetag);
        $("#storagefields").val(data.storagefields);

        $('#calculate').hide();
        $('#extract').hide();
        if($('#operationtype option:selected').text()=='计算'){
            $('#calculate').show();
        }
        if($('#operationtype option:selected').text()=='提取'){
            $('#extract').show();
        }
    });

    $('#search_adminapp,#search_app,#search_operationtype,#search_cycletype,#search_businesstype,#search_unit').change(function () {
        var table = $('#sample_1').DataTable();
        table.ajax.url("../../target_data?search_adminapp=" + $('#adminapp').val()  + "&search_operationtype=" + $('#search_operationtype').val() + "&search_cycletype=" + $('#search_cycletype').val() + "&search_businesstype=" + $('#search_businesstype').val() + "&search_unit=" + $('#search_unit').val()).load();
    })

    $('#operationtype').change(function () {
        $('#calculate').hide();
        $('#extract').hide();
        if($('#operationtype option:selected').text()=='计算'){
            $('#calculate').show();
        }
        if($('#operationtype option:selected').text()=='提取'){
            $('#extract').show();
        }
    })

    $("#new").click(function () {
        $('#calculate').hide();
        $('#extract').hide();

        $("#id").val("0");
        $("#name").val("");
        $("#code").val("");
        $("#operationtype").val("");
        $("#cycletype").val("");
        $("#businesstype").val("");
        $("#unit").val("");
        $("#magnification").val("1");
        $("#digit").val("2");
        $("#upperlimit").val("");
        $("#lowerlimit").val("");
        $("#cumulative").val("是");
        $("#sort").val("");

        $("#formula").val("");

        $("#cycle").val("");
        $("#source").val("");
        $("#sourcetable").val("");
        $("#sourcesis").val("");
        $("#sourcefields").val("");
        $("#sourceconditions").val("");
        $("#storage").val("");
        $("#storagetag").val("");
        $("#storagefields").val("");
    });

    $('#save').click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../target_save/",
            data:
                {
                    id: $("#id").val(),
                    name: $("#name").val(),
                    code: $("#code").val(),
                    operationtype: $("#operationtype").val(),
                    cycletype: $("#cycletype").val(),
                    businesstype: $("#businesstype").val(),
                    unit: $("#unit").val(),
                    magnification: $("#magnification").val(),
                    digit: $("#digit").val(),
                    upperlimit: $("#upperlimit").val(),
                    lowerlimit: $("#lowerlimit").val(),
                    adminapp: $("#adminapp").val(),
                    cumulative: $("#cumulative").val(),
                    sort: $("#sort").val(),

                    formula: $("#formula").val(),

                    cycle: $("#cycle").val(),
                    source: $("#source").val(),
                    sourcetable: $("#sourcetable").val(),
                    sourcesis: $("#sourcesis").val(),
                    sourcefields: $("#sourcefields").val(),
                    sourceconditions: $("#sourceconditions").val(),
                    storage: $("#storage").val(),
                    storagetag: $("#storagetag").val(),
                    storagefields: $("#storagefields").val(),

                    savetype:'app',
                },
            success: function (data) {
                var myres = data["res"];
                var mydata = data["data"];
                if (myres == "保存成功。") {
                    $("#id").val(data["data"]);
                    $('#static').modal('hide');
                    table.ajax.reload();
                }
                alert(myres);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    })

    $('#error').click(function () {
        $(this).hide()
    })

    $('#sample_2').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../../target_data/?search_adminapp=null",
        "columns": [
            {"data": "id"},
            {"data": "id"},
            {"data": "name"},
            {"data": "code"},
            {"data": "operationtype_name"},
            {"data": "cycletype_name"},
            {"data": "businesstype_name"},
            {"data": "unit_name"},
        ],

        "columnDefs": [{
            "targets": 0,
            "mRender":function(data,type,full){
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
        }
    });

    $('#search_operationtype1,#search_cycletype1,#search_businesstype1,#search_unit1').change(function () {
        var table = $('#sample_2').DataTable();
        table.ajax.url("../../target_data?search_adminapp=null" + "&search_operationtype=" + $('#search_operationtype1').val() + "&search_cycletype=" + $('#search_cycletype1').val() + "&search_businesstype=" + $('#search_businesstype1').val() + "&search_unit=" + $('#search_unit1').val()).load();
    })

    $('#addadminapp_save').click(function () {
         var table1 = $('#sample_1').DataTable();
         var table2 = $('#sample_2').DataTable();
        var theArray = []
        $("input[name=selecttarget]:checked").each(function() {
            theArray.push($(this).val());
        });
        if(theArray.length<1){
           alert("请至少选择一个指标");
        }
       else {
            $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../target_importadminapp/",
            data:
                {
                    adminapp: $("#adminapp").val(),
                    selectedtarget:theArray,
                },
            success: function (data) {
                var myres = data["res"];
                if (myres == "导入完成。") {
                    table1.ajax.reload();
                    table2.ajax.reload();
                }
                alert(myres);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
        }

    });

    // 右键菜单栏
    $('#formula').contextmenu({
        target: '#context-menu2',
        onItem: function (context, e) {
        }
    });

    // 点击事件提取指标
    $('#collect').click(function () {
        getTxt1CursorPosition("formula");
        $('#myModal').modal('show')
    });

    // 模态框表格数据
    $('#sample_3').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../../target_data/?search_adminapp=" + $('#adminapp').val(),
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "code"},
            {"data": null},
            {"data": null},
            {"data": null}
        ],
        "columnDefs": [{
            "targets": -3,
            "data": null,
            "defaultContent":"<select style='width:100px'><option value='d'>当日值</option><option value='m'>月累计</option>" +
            "<option value='s'>季累计</option><option value='h'>半年累计</option><option value='y'>年累计</option></select>"
        },
        {
            "targets": -2,
            "data": null,
            "defaultContent": "<select style='width:100px'><option value='D'>当天</option><option value='L'>前一天</option>" +
            "<option value='MS'>月初</option><option value='ME'>月末</option><option value='LMS'>上月初</option><option value='LME'>上月末</option>" +
            "<option value='SS'>季初</option><option value='SE'>季末</option><option value='LSS'>上季初</option><option value='LSE'>上季末</option>" +
            "<option value='HS'>半年初</option><option value='HE'>半年末</option><option value='LHS'>前个半年初</option><option value='LHE'>前个半年末</option>" +
            "<option value='YS'>年初</option><option value='YE'>年末</option><option value='LYS'>去年初</option><option value='LYE'>去年末</option>" +
            "<option value='MAVG'>月平均值</option><option value='SAVG'>季平均值</option><option value='HAVG'>半年平均值</option><option value='YAVG'>年平均值</option></select>"
        },
        {
            "targets": -1,
            "data": null,
            "defaultContent": "<button  id='select' title='选择'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-check'></i></button>"
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
            "sZeroRecords": "没有检索到数据"
        }
    });

    $('#search_adminapp,#search_app,#search_operationtype3,#search_cycletype3,#search_businesstype3,#search_unit3').change(function () {
        var table = $('#sample_3').DataTable();
        table.ajax.url("../../target_data?search_adminapp=" + $('#adminapp').val()  + "&search_operationtype=" + $('#search_operationtype3').val() + "&search_cycletype=" + $('#search_cycletype3').val() + "&search_businesstype=" + $('#search_businesstype3').val() + "&search_unit=" + $('#search_unit3').val()).load();
    });

    $('#sample_3 tbody').on('click', 'button#select', function () {
        var table = $('#sample_3').DataTable();
        var data1 = table.row($(this).parents('tr')).data().code;
        var data2 =$(this).parent().prev().prev().find('option:selected').val();
        var data3 =$(this).parent().prev().find('option:selected').val();
        var select = data1 + ':' + data2 + ':' + data3;
        var data =  $('#formula').val();
        var seat = $('#formula').attr("seat");
        data = data.slice(0,seat)+ select + data.slice(seat);
        $('#formula').val(data);
        $('#myModal').modal('hide')
    });

});

