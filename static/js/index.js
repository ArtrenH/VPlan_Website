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
    var modal_elems = document.querySelectorAll('.modal');
    var modal_instances = M.Modal.init(modal_elems, {
        onCloseStart: function(elem) {
            elem.scrollTo(0, 0);
        }
    });
    var nextDate = new Date(Date.parse(`${default_date.substring(0, 4)}-${default_date.substring(4, 6)}-${default_date.substring(6, 8)}`));
    var datepicker_elems = document.querySelectorAll('.datepicker');
    var datepicker_instances = M.Datepicker.init(datepicker_elems, {
        autoClose: true,
        defaultDate: nextDate,
        setDefaultDate: true,
        onSelect: function(date) {
            selected_date = `${date.getFullYear()}${date.getMonth()+1}${date.getDate()}`;
            document.getElementById('selected_time').innerHTML = `${date.getDate()}.${date.getMonth()+1}.${date.getFullYear()}`;
        },
        firstDay: 1
    });
});