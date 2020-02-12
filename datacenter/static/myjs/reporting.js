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
                        if (full.target_datatype == 'numbervalue'){
                            return "<input id='table1_curvalue_" + full.id + "' name='table1_curvalue'  type='number' value='" + data + "'></input>"
                        }
                        if (full.target_datatype == 'date'){
                            return "<input class='table1_curvaluedate' style = 'width:153px;height:26px;' id='table1_curvaluedate_" + full.id + "' name='table1_curvaluedate'  type='datetime'  value='" + full.curvaluedate + "'></input>"
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
            $('.table1_curvaluedate').datetimepicker({
                format: 'yyyy-mm-dd hh:ii:ss',
                autoclose: true,
            });
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
                        if (full.target_datatype == 'numbervalue'){
                             return "<input id='table2_curvalue_" + full.id + "' name='table2_curvalue'  type='number' value='" + data + "'></input>"
                        }
                        if (full.target_datatype == 'date'){
                            return "<input class='table2_curvaluedate'style = 'width:153px;height:26px;' id='table2_curvaluedate_" + full.id + "' name='table2_curvaluedate'  type='datetime'  value='" + full.curvaluedate + "'></input>"
                        }
                        if (full.target_datatype == 'text'){
                            return "<input  id='table2_curvaluetext_" + full.id + "' name='table2_curvaluetext'  type='text' value='" + full.curvaluetext + "'></input>"
                        }
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
            $('.table2_curvaluedate').datetimepicker({
                format: 'yyyy-mm-dd hh:ii:ss',
                autoclose: true,
            });
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
                        if (full.target_datatype == 'numbervalue'){
                            return "<input id='table3_curvalue_" + full.id + "' name='table3_curvalue'  type='number' value='" + data + "'></input>"
                        }
                        if (full.target_datatype == 'date'){
                            return "<input class='table3_curvaluedate' style = 'width:153px;height:26px;' id='table3_curvaluedate_" + full.id + "' name='table3_curvaluedate'  type='datetime'  value='" + full.curvaluedate + "'></input>"
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
            $('.table3_curvaluedate').datetimepicker({
                format: 'yyyy-mm-dd hh:ii:ss',
                autoclose: true,
            });
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

        "columnDefs": [
            {
            "targets": -5,
            "mRender":function(data,type,full){
                        $('#table4_curvaluedate_' + full.id).datetimepicker({
                            format: 'yyyy-mm-dd hh:ii:ss',
                            autoclose: true,
                        });

                        if (full.target_datatype == 'numbervalue'){
                            return "<input disabled id='table4_curvalue_" + full.id + "' name='table4_curvalue'  type='number' value='" + data + "'></input>"
                        }
                        if (full.target_datatype == 'date'){
                            return "<input disabled style = 'width:153px;height:26px;' id='table4_curvaluedate_" + full.id + "' name='table4_curvaluedate'  type='datetime'  value='" + full.curvaluedate + "'></input>"
                        }
                        if (full.target_datatype == 'text'){
                            return "<input disabled id='table4_curvaluetext_" + full.id + "' name='table4_curvaluetext'  type='text' value='" + full.curvaluetext + "'></input>"
                        }
                    }
            },
            {
            "targets": -4,
            "mRender":function(data,type,full){
                        return "<input disabled id='table4_cumulativemonth_" + full.id + "' name='table4_cumulativemonth'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -3,
            "mRender":function(data,type,full){
                        return "<input disabled id='table4_cumulativequarter_" + full.id + "' name='table4_cumulativequarter'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -2,
            "mRender":function(data,type,full){
                        return "<input disabled id='table4_cumulativehalfyear_" + full.id + "' name='table4_cumulativehalfyear'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -1,
            "mRender":function(data,type,full){
                        return "<input disabled id='table4_cumulativeyear_" + full.id + "' name='table4_cumulativeyear'  type='text' value='" + data + "'></input>"
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
    });
    // 行按钮
    $('#sample_4 tbody').on('change', 'input[name="table4_curvalue"]', function () {
            var table = $('#sample_4').DataTable();
            var data = table.row($(this).parents('tr')).data();
            if(data.target_cumulative=='是') {
                $('#table4_cumulativemonth_' + data.id).val(Number(data.cumulativemonth) - Number(data.curvalue) + Number($('#table4_curvalue_' + data.id).val()))
                $('#table4_cumulativequarter_' + data.id).val(Number(data.cumulativequarter) - Number(data.curvalue) + Number($('#table4_curvalue_' + data.id).val()))
                $('#table4_cumulativehalfyear_' + data.id).val(Number(data.cumulativehalfyear) - Number(data.curvalue) + Number($('#table4_curvalue_' + data.id).val()))
                $('#table4_cumulativeyear_' + data.id).val(Number(data.cumulativeyear) - Number(data.curvalue) + Number($('#table4_curvalue_' + data.id).val()))
            }
    });

    $('#sample_5').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "bPaginate" : false,
        "bFilter" : false,
        "ajax": "../../../reporting_data/?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val()  + "&operationtype=1",
        "columns": [
            {"data": "id"},
            {"data": "target_name"},
            {"data": "target_code"},
            {"data": "target_businesstypename"},
            {"data": "target_unitname"},
            {"data": "target_cumulative"},
            {"data": "zerodata"},
            {"data": "twentyfourdata"},
            {"data": "metervalue"},
            {"data": "target_magnification"},
            {"data": "curvalue"},
            {"data": "cumulativemonth"},
            {"data": "cumulativequarter"},
            {"data": "cumulativehalfyear"},
            {"data": "cumulativeyear"},
            {"data": null},
        ],

        "columnDefs": [
                        {
            "targets": -11,
            "visible": false,
            },
            {
            "targets": -10,
            "mRender":function(data,type,full){
                      return "<input style = 'width:90px;height:26px;' id='table5_zerodata_" + full.id + "' name='table5_zerodata'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -9,
            "mRender":function(data,type,full){
                      return "<input style = 'width:90px;height:26px;'id='table5_twentyfourdata_" + full.id + "' name='table5_twentyfourdata'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -8,
            "mRender":function(data,type,full){
                       return "<input style = 'width:90px;height:26px;' id='table5_metervalue_" + full.id + "' name='table5_metervalue'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -7,
            "mRender":function(data,type,full){
                       return "<input disabled style = 'width:90px;height:26px;' id='table5_magnification_" + full.id + "' name='table5_magnification'  type='text' value='" + full.target_magnification + "'></input>"
                    }
            },
            {
            "targets": -6,
            "mRender":function(data,type,full){
                        if (full.target_datatype == 'numbervalue'){
                            return "<input style = 'width:90px;height:26px;' id='table5_curvalue_" + full.id + "' name='table5_curvalue'  type='number' value='" + data + "'></input>"
                        }
                        if (full.target_datatype == 'date'){
                            return "<input class='table5_curvaluedate' style = 'width:90px;height:26px;' id='table5_curvaluedate_" + full.id + "' name='table5_curvaluedate'  type='datetime'  value='" + full.curvaluedate + "'></input>"
                        }
                        if (full.target_datatype == 'text'){
                            return "<input  style = 'width:90px;height:26px;' id='table5_curvaluetext_" + full.id + "' name='table5_curvaluetext'  type='text' value='" + full.curvaluetext + "'></input>"
                        }
                    }
            },
            {
            "targets": -5,
            "mRender":function(data,type,full){
                        return "<input disabled style = 'width:90px;height:26px;' id='table5_cumulativemonth_" + full.id + "' name='table5_cumulativemonth'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -4,
            "mRender":function(data,type,full){
                        return "<input disabled style = 'width:90px;height:26px;' id='table5_cumulativequarter_" + full.id + "' name='table5_cumulativequarter'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -3,
            "mRender":function(data,type,full){
                        return "<input disabled style = 'width:90px;height:26px;' id='table5_cumulativehalfyear_" + full.id + "' name='table5_cumulativehalfyear'  type='text' value='" + data + "'></input>"
                    }
            },
            {
            "targets": -2,
            "mRender":function(data,type,full){
                        return "<input disabled  style = 'width:90px;height:26px;'id='table5_cumulativeyear_" + full.id + "' name='table5_cumulativeyear'  type='text' value='" + data + "'></input>"
                    }
            },
                        {
            "targets": -1,
            "data": null,
            "width": "100px",
            "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static5'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>"
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
            $('.table5_curvaluedate').datetimepicker({
                format: 'yyyy-mm-dd hh:ii:ss',
                autoclose: true,
            });
            if(data.aoData.length>0)
            {
                $("#new5").hide();
                $("#save5").show();
                $("#del5").show();
            }
            else
            {
                $("#new5").show();
                $("#save5").hide();
                $("#del5").hide();
            }
        }
    });

     // 行按钮
    $('#sample_5 tbody').on('change', 'input[name="table5_zerodata"]', function () {
            var table = $('#sample_5').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $('#table5_metervalue_' + data.id).val(math.number(math.subtract(math.bignumber(Number($('#table5_twentyfourdata_' + data.id).val())),math.bignumber(Number($('#table5_zerodata_' + data.id).val())))))
            $('#table5_curvalue_' + data.id).val(Number($('#table5_metervalue_' + data.id).val()) * Number(data.target_magnification))
            if(data.target_cumulative=='是') {
                $('#table5_cumulativemonth_' + data.id).val(math.number(math.add(math.bignumber(math.number(math.subtract(math.bignumber(Number(data.cumulativemonth)),math.bignumber(Number(data.curvalue))))),math.bignumber(Number($('#table5_curvalue_' + data.id).val())))));   // math.js精度计算
                $('#table5_cumulativequarter_' + data.id).val(math.number(math.add(math.bignumber(math.number(math.subtract(math.bignumber(Number(data.cumulativequarter)),math.bignumber(Number(data.curvalue))))),math.bignumber(Number($('#table5_curvalue_' + data.id).val())))));
                $('#table5_cumulativehalfyear_' + data.id).val(math.number(math.add(math.bignumber(math.number(math.subtract(math.bignumber(Number(data.cumulativehalfyear)),math.bignumber(Number(data.curvalue))))),math.bignumber(Number($('#table5_curvalue_' + data.id).val())))));
                $('#table5_cumulativeyear_' + data.id).val(math.number(math.add(math.bignumber(math.number(math.subtract(math.bignumber(Number(data.cumulativeyear)),math.bignumber(Number(data.curvalue))))),math.bignumber(Number($('#table5_curvalue_' + data.id).val())))))
            }
    });
    $('#sample_5 tbody').on('change', 'input[name="table5_twentyfourdata"]', function () {
            var table = $('#sample_5').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $('#table5_metervalue_' + data.id).val(math.number(math.subtract(math.bignumber(Number($('#table5_twentyfourdata_' + data.id).val())),math.bignumber(Number($('#table5_zerodata_' + data.id).val())))))
            $('#table5_curvalue_' + data.id).val(Number($('#table5_metervalue_' + data.id).val()) * Number(data.target_magnification))
            if(data.target_cumulative=='是') {
                $('#table5_cumulativemonth_' + data.id).val(math.number(math.add(math.bignumber(math.number(math.subtract(math.bignumber(Number(data.cumulativemonth)),math.bignumber(Number(data.curvalue))))),math.bignumber(Number($('#table5_curvalue_' + data.id).val())))));
                $('#table5_cumulativequarter_' + data.id).val(math.number(math.add(math.bignumber(math.number(math.subtract(math.bignumber(Number(data.cumulativequarter)),math.bignumber(Number(data.curvalue))))),math.bignumber(Number($('#table5_curvalue_' + data.id).val())))));
                $('#table5_cumulativehalfyear_' + data.id).val(math.number(math.add(math.bignumber(math.number(math.subtract(math.bignumber(Number(data.cumulativehalfyear)),math.bignumber(Number(data.curvalue))))),math.bignumber(Number($('#table5_curvalue_' + data.id).val())))));
                $('#table5_cumulativeyear_' + data.id).val(math.number(math.add(math.bignumber(math.number(math.subtract(math.bignumber(Number(data.cumulativeyear)),math.bignumber(Number(data.curvalue))))),math.bignumber(Number($('#table5_curvalue_' + data.id).val())))))
            }
    });

    $('#sample_5 tbody').on('click', 'button#edit', function () {
            var table = $('#sample_5').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $("#id").val(data.id);
            $("#cumulative").val(data.target_cumulative);
            $("#curvalue").val(data.curvalue);
            $("#cumulativemonth").val(data.cumulativemonth);
            $("#cumulativequarter").val(data.cumulativequarter);
            $("#cumulativehalfyear").val(data.cumulativehalfyear);
            $("#cumulativeyear").val(data.cumulativehalfyear);

            $("#oldtable_zerodata").val($('#table5_zerodata_' + data.id).val());
            $("#oldtable_twentyfourdata").val($('#table5_zerodata_' + data.id).val());
            $("#oldtable_value").val(Number( $("#oldtable_twentyfourdata").val()) - Number($("#oldtable_zerodata").val()));
            $("#oldtable_magnification").val($('#table5_magnification_' + data.id).val());
            $("#oldtable_finalvalue").val(Number($("#oldtable_value").val()) * Number(data.target_magnification));

            $("#newtable_zerodata").val($('#table5_zerodata_' + data.id).val());
            $("#newtable_twentyfourdata").val($('#table5_twentyfourdata_' + data.id).val());
            $("#newtable_value").val(Number( $("#newtable_twentyfourdata").val()) - Number($("#newtable_zerodata").val()));
            $("#newtable_magnification").val($('#table5_magnification_' + data.id).val());
            $("#newtable_finalvalue").val(Number($("#newtable_value").val()) * Number(data.target_magnification));
            $("#finalvalue").val(Number($("#oldtable_finalvalue").val()) + Number($("#newtable_finalvalue").val()));
    });

    $("#oldtable_zerodata").bind('input propertychange',function (){
            $('#oldtable_value').val(math.number(math.subtract(math.bignumber(Number($("#oldtable_twentyfourdata").val())),math.bignumber(Number($("#oldtable_zerodata").val())))))
            $('#oldtable_finalvalue').val(Number($('#oldtable_value').val()) * Number($("#oldtable_magnification").val()))
            $("#finalvalue").val(math.number(math.add(math.bignumber(Number($("#oldtable_finalvalue").val())),math.bignumber(Number($("#newtable_finalvalue").val())))))
    });
    $("#newtable_zerodata").bind('input propertychange',function (){
            $('#newtable_value').val(math.number(math.subtract(math.bignumber(Number($("#newtable_twentyfourdata").val())),math.bignumber(Number($("#newtable_zerodata").val())))))
            $('#newtable_finalvalue').val(math.number(math.multiply(math.bignumber(Number($("#newtable_value").val())),math.bignumber(Number($("#newtable_magnification").val())))))
            $("#finalvalue").val(math.number(math.add(math.bignumber(Number($("#oldtable_finalvalue").val())),math.bignumber(Number($("#newtable_finalvalue").val())))))
    });
    $("#oldtable_twentyfourdata").bind('input propertychange',function (){
            $('#oldtable_value').val(math.number(math.subtract(math.bignumber(Number($("#oldtable_twentyfourdata").val())),math.bignumber(Number($("#oldtable_zerodata").val())))))
            $('#oldtable_finalvalue').val(Number($('#oldtable_value').val()) * Number($("#oldtable_magnification").val()))
            $("#finalvalue").val(math.number(math.add(math.bignumber(Number($("#oldtable_finalvalue").val())),math.bignumber(Number($("#newtable_finalvalue").val())))))
    });
    $("#newtable_twentyfourdata").bind('input propertychange',function (){
            $('#newtable_value').val(math.number(math.subtract(math.bignumber(Number($("#newtable_twentyfourdata").val())),math.bignumber(Number($("#newtable_zerodata").val())))))
            $('#newtable_finalvalue').val(math.number(math.multiply(math.bignumber(Number($("#newtable_value").val())),math.bignumber(Number($("#newtable_magnification").val())))))
            $("#finalvalue").val(math.number(math.add(math.bignumber(Number($("#oldtable_finalvalue").val())),math.bignumber(Number($("#newtable_finalvalue").val())))))
    });
    $("#newtable_magnification").bind('input propertychange',function (){
            $('#newtable_finalvalue').val(math.number(math.multiply(math.bignumber(Number($("#newtable_value").val())),math.bignumber(Number($("#newtable_magnification").val())))))
            $("#finalvalue").val(math.number(math.add(math.bignumber(Number($("#oldtable_finalvalue").val())),math.bignumber(Number($("#newtable_finalvalue").val())))))

    });

    $('#confirm').click(function () {
            if (confirm("此操作涉及到换表，是否执行换表操作？")){
                  var id = $("#id").val();
                  var cumulative = $("#cumulative").val();
                  var curvalue = $("#curvalue").val();
                  var cumulativemonth  = $("#cumulativemonth").val();
                  var cumulativequarter = $("#cumulativequarter").val();
                  var cumulativehalfyear = $("#cumulativehalfyear").val();
                  var cumulativeyear = $("#cumulativeyear").val();
                  $("#table5_magnification_" + id).val($("#newtable_magnification").val());
                  $("#table5_curvalue_" + id).val($("#finalvalue").val());
                  $("#table5_zerodata_" + id).val($("#oldtable_zerodata").val());
                  $("#table5_twentyfourdata_" + id).val($("#newtable_twentyfourdata").val());
                  $("#table5_metervalue_" + id).val(Number($("#table5_twentyfourdata_" + id).val()) - Number($("#table5_zerodata_" + id).val()));

                  if(cumulative=='是') {
                       $('#table5_cumulativemonth_' + id).val(math.number(math.add(math.bignumber(math.number(math.subtract(math.bignumber(Number(cumulativemonth)), math.bignumber(Number(curvalue))))), math.bignumber(Number($('#table5_curvalue_' + id).val())))));
                       $('#table5_cumulativequarter_' + id).val(math.number(math.add(math.bignumber(math.number(math.subtract(math.bignumber(Number(cumulativequarter)), math.bignumber(Number(curvalue))))), math.bignumber(Number($('#table5_curvalue_' + id).val())))));
                       $('#table5_cumulativehalfyear_' + id).val(math.number(math.add(math.bignumber(math.number(math.subtract(math.bignumber(Number(cumulativehalfyear)), math.bignumber(Number(curvalue))))), math.bignumber(Number($('#table5_curvalue_' + id).val())))));
                       $('#table5_cumulativeyear_' + id).val(math.number(math.add(math.bignumber(math.number(math.subtract(math.bignumber(Number(cumulativeyear)), math.bignumber(Number(curvalue))))), math.bignumber(Number($('#table5_curvalue_' + id).val())))))
                  }

                  $("Element").blur();
                  var savedata=[];
                  savedata.push({"id":$("#id").val(),"reporting_date":$("#reporting_date").val(),"oldtable_zerodata":$("#oldtable_zerodata").val(),"oldtable_twentyfourdata":$("#oldtable_twentyfourdata").val(),"oldtable_value":$("#oldtable_value").val(), "oldtable_magnification":$("#oldtable_magnification").val(),"oldtable_finalvalue":$("#oldtable_finalvalue").val(),
                      "newtable_zerodata":$("#newtable_zerodata").val(),"newtable_twentyfourdata":$("#newtable_twentyfourdata").val(), "newtable_value": $("#newtable_value").val(),"newtable_magnification":$("#newtable_magnification").val(), "newtable_finalvalue":$("#newtable_finalvalue").val(),"finalvalue":$("#finalvalue").val(),
                      });

                  $.ajax({
                        type: "POST",
                        dataType: 'json',
                        url: "../../../reporting_save/",
                        data:
                            {
                                operationtype:"meterchangedata",
                                savedata:JSON.stringify(savedata),
                            },
                  });
                  $('#static5').modal('hide');

            }
            else{
                $('#static5').modal('hide');
            }
    });

    $('#reporting_date').change(function () {
        var table1 = $('#sample_1').DataTable();
        table1.ajax.url("../../../reporting_data?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val() + "&operationtype=15").load();
        var table2 = $('#sample_2').DataTable();
        table2.ajax.url("../../../reporting_data?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val() + "&operationtype=16").load();
        var table3 = $('#sample_3').DataTable();
        table3.ajax.url("../../../reporting_data?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val() + "&operationtype=17").load();
        var table4 = $('#sample_4').DataTable();
        table4.ajax.url("../../../reporting_data?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val() + "&operationtype=0").load();
        var table5 = $('#sample_5').DataTable();
        table5.ajax.url("../../../reporting_data?app=" + $('#app').val() + "&cycletype=" + $('#cycletype').val() + "&reporting_date=" + $('#reporting_date').val() + "&operationtype=1").load();
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
            savedata.push({"id":item.id,"curvalue":$('#table2_curvalue_' + item.id).val(),"curvaluedate":$('#table2_curvaluedate_' + item.id).val(),"curvaluetext":$('#table2_curvaluetext_' + item.id).val(),"cumulativemonth":$('#table2_cumulativemonth_' + item.id).val(),"cumulativequarter":$('#table2_cumulativequarter_' + item.id).val(),"cumulativehalfyear":$('#table2_cumulativehalfyear_' + item.id).val(),"cumulativeyear":$('#table2_cumulativeyear_' + item.id).val()})
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

    $("#new5").click(function () {
        var table = $('#sample_5').DataTable();
        $.ajax({
            type: "POST",
            url: "../../../reporting_new/",
            data:
                {
                    app: $('#app').val(),
                    cycletype:$('#cycletype').val(),
                    reporting_date:$('#reporting_date').val(),
                    operationtype:1,

                },
            success: function (data) {
                if (data == 1) {
                    table.ajax.reload();
                    $("#new5").hide();
                    $("#save5").show();
                    $("#del5").show();
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
    $("#del5").click(function () {
        if (confirm("确定要删除表中数据？")) {
            var table = $('#sample_5').DataTable();
            $.ajax({
                type: "POST",
                url: "../../../reporting_del/",
                data:
                    {
                        app: $('#app').val(),
                        cycletype:$('#cycletype').val(),
                        reporting_date:$('#reporting_date').val(),
                        operationtype:1,

                    },
                success: function (data) {
                    if (data == 1) {
                        table.ajax.reload();
                        $("#new5").show();
                        $("#save5").hide();
                        $("#del5").hide();
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
    $('#save5').click(function () {
        $("Element").blur()
        var table = $('#sample_5').DataTable().data();
        var savedata=[]
    　　$.each(table,function(i,item){
            savedata.push({"id":item.id,"reporting_date":$("#reporting_date").val(),"magnification": $('#table5_magnification_' + item.id).val(),"zerodata":$('#table5_zerodata_' + item.id).val(),"twentyfourdata":$('#table5_twentyfourdata_' + item.id).val(),"metervalue":$('#table5_metervalue_' + item.id).val(),"curvalue":$('#table5_curvalue_' + item.id).val(),"curvaluedate":$('#table5_curvaluedate_' + item.id).val(),"curvaluetext":$('#table5_curvaluetext_' + item.id).val(),"cumulativemonth":$('#table5_cumulativemonth_' + item.id).val(),"cumulativequarter":$('#table5_cumulativequarter_' + item.id).val(),"cumulativehalfyear":$('#table5_cumulativehalfyear_' + item.id).val(),"cumulativeyear":$('#table5_cumulativeyear_' + item.id).val()})
    　　});
        console.log(savedata, '123456')
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../../../reporting_save/",
            data:
                {
                    operationtype:1,
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