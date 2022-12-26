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
document.addEventListener('DOMContentLoaded', function() {
    var elems = document.querySelectorAll('.modal');
    var instances = M.Modal.init(elems, {
        onCloseStart: function(elem) {
            elem.scrollTo(0, 0);
        }
    });
});