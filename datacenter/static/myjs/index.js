$.ajax({
    type: "POST",
    dataType: 'json',
    url: "../get_reporting_log/",
    data: {},
    success: function (data) {
        $('#reporting_log').empty();
        for (var i = 0; i < data.data.length; i++) {
            $('#reporting_log').append('<li>\n' +
                '    <div class="col1">\n' +
                '        <div class="cont" style="margin-right: 0">\n' +
                '            <div class="cont-col1">\n' +
                '                <div class="label label-sm label-success">\n' +
                '                    <i class="fa fa-bell-o"></i>\n' +
                '                </div>\n' +
                '            </div>\n' +
                '            <div class="cont-col2">\n' +
                '                <div class="desc"> ' + data.data[i].log + '\n' +
                '                </div>\n' +
                '            </div>\n' +
                '        </div>\n' +
                '    </div>\n' +
                '    <div class="col-md-offset-2 col-md-10" aria-expanded="true" style="padding: 0">\n' +
                '        <div class="panel-body" style="padding: 0">\n' +
                '            <div class="col-md-7"></div>\n' +
                '            <div class="col-md-5" style="font-style: italic;color: #c1cbd0">'+ data.data[i].time +'</div>\n' +
                '        </div>\n' +
                '    </div>\n' +
                '</li>')
        }
    },
});

