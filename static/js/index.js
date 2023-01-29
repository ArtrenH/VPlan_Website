function setDate(date) {
    selected_date = `${date.getFullYear()}${zeroPad(date.getMonth()+1, 2)}${zeroPad(date.getDate(), 2)}`;
    document.getElementById('selected_time').innerHTML = `${zeroPad(date.getDate(), 2)}.${zeroPad(date.getMonth()+1, 2)}.${date.getFullYear()}`;
}

function change_day(day_amount) {
    let tmp_date;
    tmp_date = available_dates[(available_dates.indexOf(selected_date)+day_amount)];
    if (typeof tmp_date === 'undefined') {
        M.toast({text: 'Für dieses Datum existiert kein Vertretungsplan!', classes:"error-toast", displayLength: 1000})
        return;
    }
    let new_date = new Date(Date.parse(`${tmp_date.substring(0, 4)}-${tmp_date.substring(4, 6)}-${tmp_date.substring(6, 8)}`));
    datepicker_instance.setDate(new_date);
    setDate(new_date);
}

function isApple() {
    let platform = navigator?.userAgentData?.platform || navigator?.platform || 'unknown'
    var isMacLike = /(Mac|iPhone|iPod|iPad)/i.test(platform);
    var isIOS = /(iPhone|iPod|iPad)/i.test(platform);
    return isMacLike || isIOS;
}

function copyLink() {
    if (navigator.canShare({title: "Better VPlan", url: window.location.href})) {
        navigator.share({title: "Better VPlan", url: window.location.href});
    } else {
        navigator.clipboard.writeText(window.location.href);
        M.toast({text: 'Link kopiert!', classes:"success-toast", displayLength: 1000});
    }
}

var ajax_response = null;

if (vorangezeigt) {
    if (ajax_response !== null) {ajax_response.abort();}
    get_plan();
}

function get_plan_url(url) {
    if (ajax_response !== null) {ajax_response.abort();}
    M.toast({text: 'Lade Plan...', displayLength: 750, classes:"neutral-toast"});
    window.history.replaceState(null, "", url + "&share=true");
    ajax_response = $.ajax({
        type: 'GET',
        url: "/api" + url,
        dataType: 'html',
        success: function(response) {
            $('.loaded_content').html(response);
            $([document.documentElement, document.body]).animate({
                scrollTop: $(".loaded_content").offset().top
            }, 200);
            var collapsible_elems = document.querySelectorAll('.collapsible');
            var collapsible_instances = M.Collapsible.init(collapsible_elems, {});
            M.Toast.dismissAll();
            M.toast({text: 'Plan geladen!', displayLength: 1000, classes:"success-toast"});
        },
        error: function(request, status, error) {
            M.toast({text: 'Beim laden des Plans ist ein Fehler aufgetreten!', displayLength: 2000, classes:"error-toast"});
        }
    });
}

function get_plan() {
    $('.floating-arrow').fadeIn(200);
    if(typeof available_dates[(available_dates.indexOf(selected_date)+1)] === 'undefined') {
        $('.arrow-right').fadeOut(200);
        $('.arrow-right').attr('disabled', true);
    } else {
        $('.arrow-right').fadeIn(200);
        $('.arrow-right').attr('disabled', false);
    }
    if(typeof available_dates[(available_dates.indexOf(selected_date)-1)] === 'undefined') {
        $('.arrow-left').fadeOut(200);
        $('.arrow-left').attr('disabled', true);
    } else {
        $('.arrow-left').fadeIn(200);
        $('.arrow-left').attr('disabled', false);
    }
    if (selected_type == 'klasse' || selected_type == 'klasse_preferences') {
        $('#expand-btn').fadeIn(200);
    } else {
        $('#expand-btn').fadeOut(200);
    }
    if (selected_type == 'klasse' && preferences) {
        selected_type = 'klasse_preferences';
    }
    get_plan_url(`/${school_number}?date=${selected_date}&type=${selected_type}&value=${encodeURIComponent(selected_value)}`);
}

var datepicker_instance;
document.addEventListener('DOMContentLoaded', function() {
    if(isApple()) {
        $('#share-btn span').html('ios_share');
    }
    if (angefragt_values['type'] == "klasse") {
        togglePreferences();
    }
    var modal_elems = document.querySelectorAll('.index-modal');
    var modal_instances = M.Modal.init(modal_elems, {
        onCloseStart: function(elem) {
            elem.scrollTo(0, 0);
        }
    });
    var nextDate = date;
    var datepicker_elems = document.querySelectorAll('.datepicker');
    var datepicker_instances = M.Datepicker.init(datepicker_elems, {
        autoClose: true,
        defaultDate: nextDate,
        setDefaultDate: true,
        onSelect: function(date) {
            setDate(date);
            get_plan();
        },
        firstDay: 1,
        disableDayFn: function(date) {
            return !available_dates.includes(`${date.getFullYear()}${zeroPad(date.getMonth()+1, 2)}${zeroPad(date.getDate(), 2)}`);
        }
    });
    datepicker_instance = datepicker_instances[0];
    var autocomplete_elems = document.querySelectorAll('.autocomplete');
    var autocomplete_instances = M.Autocomplete.init(autocomplete_elems, {
        data: teacher_autocomplete_data,
        limit: 6,
        onAutocomplete: function(option) {
            selected_type = "teacher";
            selected_value = teacher_kuerzel_map[option];
            get_plan();
            $('#teacher-picker-modal .modal-close:not(.dp01)').click();
        }
    });
});

var preferences = true;
function togglePreferences() {
    if ($('#expand-btn span').text() == "remove") {
        $('#expand-btn span').text("add")
    } else {
        $('#expand-btn span').text("remove")
    }
    preferences = !preferences;
    if (!preferences && selected_type == "klasse_preferences") {
        selected_type = "klasse";
    }
}

let touchstartX = 0;
let touchendX = 0;
let min_travel_dst = window.innerWidth/3;
    
function checkDirection() {
  if (touchendX < touchstartX && Math.abs(touchendX - touchstartX) > min_travel_dst) change_day(1);
  if (touchendX > touchstartX && Math.abs(touchendX - touchstartX) > min_travel_dst) change_day(-1);
}

document.addEventListener('touchstart', e => {
  touchstartX = e.changedTouches[0].screenX
})

document.addEventListener('touchend', e => {
  touchendX = e.changedTouches[0].screenX
  checkDirection()
})