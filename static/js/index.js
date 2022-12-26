if (vorangezeigt) {
    $.ajax({
        type: 'GET',
        url: '/' + school_number + '?' + angefragt_link.replace(';', '&'),
        dataType: 'html',
        success: function(response) {
            $('.vplan-wrapper').remove();
            $('.loaded_content').append(response);
        }
    });
}

function get_plan(type, value) {
    $.ajax({
        type: 'GET',
        url: `/${school_number}?date=${selected_date}&type=${type}&value=${value}`,
        dataType: 'html',
        success: function(response) {
            $('.loaded_content').html(response);
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
    const zeroPad = (n, digits) => n.toString().padStart(digits, '0');
    var nextDate = new Date(Date.parse(`${default_date.substring(0, 4)}-${default_date.substring(4, 6)}-${default_date.substring(6, 8)}`));
    var datepicker_elems = document.querySelectorAll('.datepicker');
    var datepicker_instances = M.Datepicker.init(datepicker_elems, {
        autoClose: true,
        defaultDate: nextDate,
        setDefaultDate: true,
        onSelect: function(date) {
            selected_date = `${date.getFullYear()}${zeroPad(date.getMonth()+1, 2)}${zeroPad(date.getDate(), 2)}`;
            document.getElementById('selected_time').innerHTML = `${zeroPad(date.getDate(), 2)}.${zeroPad(date.getMonth()+1, 2)}.${date.getFullYear()}`;
        },
        firstDay: 1,
        disableDayFn: function(date) {
            return !available_dates.includes(`${date.getFullYear()}${zeroPad(date.getMonth()+1, 2)}${zeroPad(date.getDate(), 2)}`);
        }
    });
});