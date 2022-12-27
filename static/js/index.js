function isApple() {
    let platform = navigator?.userAgentData?.platform || navigator?.platform || 'unknown'
    var isMacLike = /(Mac|iPhone|iPod|iPad)/i.test(platform);
    var isIOS = /(iPhone|iPod|iPad)/i.test(platform);
    return isMacLike || isIOS;
}

function copyLink() {
    //navigator.clipboard.writeText(window.location.href);
    // TODO: currently returning false even though it works
    if (navigator.canShare({title: "Better VPlan", url: window.location.href})) {
        navigator.share({title: "Better VPlan", url: window.location.href});
    } else {
        navigator.clipboard.writeText(window.location.href);
        M.toast({text: 'Link kopiert!'});
    }
}

var ajax_response = null;

if (vorangezeigt) {
    if (ajax_response !== null) {ajax_response.abort();}
    get_plan_url('/' + school_number + '?' + angefragt_link.replace(';', '&'));
}

function get_plan_url(url) {
    if (ajax_response !== null) {ajax_response.abort();}
    M.toast({text: 'Lade Plan...', displayLength: 750});
    window.history.replaceState(null, "", url + "&share=true");
    ajax_response = $.ajax({
        type: 'GET',
        url: url,
        dataType: 'html',
        success: function(response) {
            $('.loaded_content').html(response);
            // Not needed as links are now replaced with buttons
            /*$('a.link').click(function(event) {
                event.preventDefault();
                get_plan_url($(event.currentTarget).prop("href"));
            });
            $('a.link').keyup(function(event) {
                if (e.which == 32 || e.which == 13) {
                    event.preventDefault();
                    get_plan_url($(event.currentTarget).prop("href"));
                }
            });*/
            if(isApple()) {
                $('#share-btn span').html('ios_share');
            }
            M.toast({text: 'Plan geladen!', displayLength: 1000});
        },
        error: function(request, status, error) {
            M.toast({text: 'Beim laden des Plans ist ein Fehler aufgetreten!', displayLength: 2000});
        }
    });
}

function get_plan() {
    get_plan_url(`/${school_number}?date=${selected_date}&type=${selected_type}&value=${selected_value}`);
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
            get_plan(selected_type, selected_value);
        },
        firstDay: 1,
        disableDayFn: function(date) {
            return !available_dates.includes(`${date.getFullYear()}${zeroPad(date.getMonth()+1, 2)}${zeroPad(date.getDate(), 2)}`);
        }
    });
});