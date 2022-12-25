navigator.serviceWorker && navigator.serviceWorker.register("/sw.js").then(function(registration) {});



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

/*$.ajax({
    type: 'GET',
    url: '/10001329?date=20221221&type=klasse&klasse=JG12',
    dataType: 'html',
    success: function(response) {
        $('.vplan-wrapper').remove();
        $('.loaded_content').append(response);
    }
});*/