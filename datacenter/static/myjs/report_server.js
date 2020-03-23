$(document).ready(function () {
    $('#save').click(function () {
        $.ajax({
            type: "POST",
            url: "../report_server_save/",
            data: $('#report_server_form').serialize(),
            success: function (data) {
                alert(data.data);
            },
            error: function (e) {
                alert("保存失败，请于客服联系。");
            }
        });
    });
});