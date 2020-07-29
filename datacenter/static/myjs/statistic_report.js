var csrfToken = $('[name="csrfmiddlewaretoken"]').val();

$('#start_date').datetimepicker({
    format: 'yyyy-mm-dd',
    autoclose: true,
    startView: 2,
    minView: 2,
});
$('#end_date').datetimepicker({
    format: 'yyyy-mm-dd',
    autoclose: true,
    startView: 2,
    minView: 2,
});


function getStatisticReport(start_date, end_date, search_id) {
    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../get_statistic_report/?start_date=" + start_date + "&end_date=" + end_date + "&search_id=" + search_id,
        data: {
            csrfmiddlewaretoken: csrfToken
        },
        success: function (data) {
            var status = data.status,
                info = data.info,
                table_data = data.data;
            if (status == 1) {
                var head_data = table_data.head_data,
                    body_data = table_data.body_data;
                $('#statistic_report_dt').find('thead').empty();
                $('#statistic_report_dt').find('tbody').empty();

                // thead
                var first_head_tr = '<tr>',
                    second_head_tr = '<tr>';
                for (var i = 0; i < head_data.length; i++) {
                    var col_name = head_data[i]['col_name'],
                        rowspan = head_data[i]['rowspan'],
                        colspan = head_data[i]['colspan'],
                        targets = head_data[i]['targets'];
                    first_head_tr += '<th rowspan="' + rowspan + '" colspan="' + colspan + ' " style="text-align: center;vertical-align: middle;font-weight: bold;">' + col_name + '</th>';

                    if (targets.length > 1) {
                        for (var j = 0; j < targets.length; j++) {
                            second_head_tr += '<th style="text-align: center;vertical-align: middle;font-weight: bold;">' + targets[j]['target_name'] + '</th>';
                        }
                    }
                }
                first_head_tr += '</tr>';
                second_head_tr += '</tr>';
                $('#statistic_report_dt').find('thead').append(first_head_tr).append(second_head_tr);

                // tbody
                for (var k = 0; k < body_data.length; k++) {
                    var tbody_tr = '<tr>';
                    tbody_tr += '<td style="text-align: center;">' + body_data[k]['date'] + '</td>';
                    for (var l = 0; l < body_data[k]['target_values'].length; l++) {
                        tbody_tr += '<td style="text-align: right;">' + body_data[k]['target_values'][l] + '</td>';
                    }
                    tbody_tr += '</td>';
                    $('#statistic_report_dt').find('tbody').append(tbody_tr);
                }
            } else {
                alert(info);
            }
        }
    })
}

getStatisticReport($('#start_date').val(), $('#end_date').val(), $('#search_id').val());

$('#search').click(function () {
    var start_date = $('#start_date').val(),
        end_date = $('#end_date').val(),
        search_id = $('#search_id').val();
    getStatisticReport(start_date, end_date, search_id);
})

