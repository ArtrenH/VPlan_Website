// Old Service worker did some questionable stuff, removing it with this
navigator.serviceWorker.getRegistrations().then(function(registrations) {
    for(let registration of registrations) {
        registration.unregister()
    } 
})

function get(object, key, default_value) {
    var result = object[key];
    return (typeof result !== "undefined") ? result : default_value;
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrf_token);
        }
    }
});

var selected_class = null;
var clicked_finished = false;
var settings_clicked_finished = false;

function reload_preferences(response) {
    $('#all_checkbox').css('display', 'block');
    $('.checkbox-grid').html('');
    for (const group of $.parseJSON(response)) {
        let checkbox_elem = `<label class="col s12 m6 l4 xl3"><input id="${group[0]}" type="checkbox" class="filled-in" ${group[2] ? "checked=\"checked\"" : ""}><span>${group[0]} ${group[1]}</span></label>`;
        $('.checkbox-grid').append(checkbox_elem);
    }
}

function init_selects() {
    var select_elems = document.querySelectorAll('select');
    var select_instances = M.FormSelect.init(select_elems, {
        dropdownOptions: {
            onCloseStart: function(elem) {
                selected_class = elem.value;
                if (selected_class == 'Wähle eine Klasse') {
                    selected_class = null;
                    return;
                }
                $.ajax({
                    type: 'GET',
                    url: `/preferences/${school_number}?course=${encodeURIComponent(selected_class)}`,
                    dataType: 'html',
                    success: function(response) {
                        reload_preferences(response);
                    }
                });
            }
        }
    });
}

function save_preferences() {
    // Save preferences
    let selected_groups = [];
    $('.checkbox-grid input').each(function(){
        if (this.checked) {
            selected_groups.push(this.id);
        }
    });
    $.ajax({
        type: 'POST',
        url: `/preferences/${school_number}?course=${encodeURIComponent(selected_class)}`,
        contentType: 'application/json; charset=utf-8',
        data: JSON.stringify(selected_groups),
        success: function(response) {
            M.toast({text: 'Fachauswahl gespeichert!', classes:"success-toast", displayLength: 1000});
            if (typeof get_plan === "function") {
                get_plan();
            }
        },
        error: function() {
            M.toast({text: 'Beim speichern der Fachauswahl ist ein Fehler aufgetreten!', displayLength: 2000, classes:"error-toast"});
        }
    });
}

function save_settings() {
    USER_SETTINGS = {
        "show_plan_toasts": document.querySelector('#show_plan_toasts input').checked,
        "day_switch_keys": document.querySelector('#day_switch_keys input').checked,
        "background_color": document.querySelector('#background_color input').value,
        "accent_color": document.querySelector('#accent_color input').value
    };
    document.documentElement.style.setProperty('--background_color', USER_SETTINGS['background_color']);
    document.documentElement.style.setProperty('--accent_color', USER_SETTINGS['accent_color']);
    $.ajax({
        type: 'POST',
        url: '/settings',
        contentType: 'application/json; charset=utf-8',
        data: JSON.stringify(USER_SETTINGS),
        success: function(response) {
            M.toast({text: 'Einstellungen gespeichert!', classes:"success-toast", displayLength: 1000});
            if (typeof get_plan === "function") {
                get_plan();
            }
        },
        error: function() {
            M.toast({text: 'Beim speichern der Einstellungen ist ein Fehler aufgetreten!', displayLength: 2000, classes:"error-toast"});
        }
    });
}

function load_settings() {
    document.querySelector('#show_plan_toasts input').checked = get(USER_SETTINGS, "show_plan_toasts", false);
    document.querySelector('#day_switch_keys input').checked = get(USER_SETTINGS, "day_switch_keys", true);
    document.querySelector('#background_color input').value = get(USER_SETTINGS, "background_color", "#121212");
    document.querySelector('#accent_color input').value = get(USER_SETTINGS, "accent_color", "#BB86FC");
}

navigator.serviceWorker && navigator.serviceWorker.register("/sw.js").then(function(registration) {});
document.addEventListener('DOMContentLoaded', function() {
    M.updateTextFields();
    if (typeof school_number !== 'undefined') {
        $.ajax({
            type: 'GET',
            url: `/preferences/${school_number}`,
            dataType: 'html',
            success: function(response) {
                $('#class_select').html(`<option value="" disabled selected>Wähle eine Klasse</option>`);
                let option_elems = '';
                for (const klassenstufe of $.parseJSON(response)) {
                    for (const klasse of klassenstufe) {
                        option_elems += `<option value="${klasse}">${klasse}</option>\n`;
                    }
                }
                $('#class_select').append(option_elems);
                init_selects();
                
            }
        });
    }
    var dropdown_elems = document.querySelectorAll('.dropdown-trigger-preferences');
    var dropdown_instances = M.Dropdown.init(dropdown_elems, {
        coverTrigger: false,
        alignment: 'right',
        constrainWidth: false
    });
    var modal_elems = document.querySelectorAll('.preference_modal');
    var modal_instances = M.Modal.init(modal_elems, {
        onOpenStart: function() {
            if (selected_class !== null && !clicked_finished) {
                $.ajax({
                    type: 'GET',
                    url: `/preferences/${school_number}?course=${encodeURIComponent(selected_class)}`,
                    dataType: 'html',
                    success: function(response) {
                        reload_preferences(response);
                    }
                });
            }
            clicked_finished = false;
        },
        onCloseStart: function(elem) {
            elem.scrollTo(0, 0);
            if (!clicked_finished) {
                $('.checkbox-grid').html('');
                return;
            }
            if (selected_class === null) {return;}
            save_preferences();
        }
    });
    var settings_modal_elems = document.querySelectorAll('.settings_modal');
    var settings_modal_instances = M.Modal.init(settings_modal_elems, {
        onOpenStart: function() {
            settings_clicked_finished = false;
            load_settings();
        },
        onCloseStart: function(elem) {
            elem.scrollTo(0, 0);
            if (!settings_clicked_finished) {
                return;
            }
            save_settings();
        }
    });
});

function togglePasswordVisibility() {
    let x = document.getElementById("pw");
    if (x.type === "password") {
        x.type = "text";
    } else {
        x.type = "password";
    }
}

function delete_account() {
    if (confirm("Willst du wirklich deinen Account löschen?")) {
        $.ajax({
            type: 'DELETE',
            url: `/account`,
            dataType: 'html',
            success: function(response) {
                if ($.parseJSON(response)["success"]) {
                    M.toast({text: 'Account erfolgreich gelöscht!', classes:"success-toast", displayLength: 1000});
                    setTimeout(function (){
                        window.location.href = "/";
                    }, 1000);
                } else {
                    M.toast({text: 'Beim löschen des Accounts ist ein Fehler aufgetreten!', displayLength: 2000, classes:"error-toast"});
                }
            },
            error: function() {
                M.toast({text: 'Beim löschen des Accounts ist ein Fehler aufgetreten!', displayLength: 2000, classes:"error-toast"});
            }
        });
    }
}