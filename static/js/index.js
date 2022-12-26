if (vorangezeigt) {
    $.ajax({
        type: 'GET',
        url: '/10001329?' + angefragt_link.replace(';', '&'),
        dataType: 'html',
        success: function(response) {
            $('.vplan-wrapper').remove();
            $('.loaded_content').append(response);
        }
    });
}