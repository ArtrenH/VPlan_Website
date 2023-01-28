var selected_class = null;
var clicked_finished = false;

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
                        $('.checkbox-grid').html('');
                        for (const group of $.parseJSON(response)) {
                            let checkbox_elem = `<label class="col s6 m4 l3"><input id="${group[3]}" type="checkbox" class="filled-in" ${group[4] ? "checked=\"checked\"" : ""}><span>${group[2] != '' ? group[2] : group[0]} ${group[1]}</span></label>`;
                            $('.checkbox-grid').append(checkbox_elem);
                        }
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
        },
        error: function() {
            M.toast({text: 'Beim speichern der Fachauswahl ist ein Fehler aufgetreten!', displayLength: 2000, classes:"error-toast"});
        }
    });
}

navigator.serviceWorker && navigator.serviceWorker.register("/sw.js").then(function(registration) {});
document.addEventListener('DOMContentLoaded', function() {
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
    var dropdown_elems = document.querySelectorAll('.dropdown-trigger');
    var dropdown_instances = M.Dropdown.init(dropdown_elems, {
        coverTrigger: false,
        alignment: 'right',
        constrainWidth: false
    });
    var modal_elems = document.querySelectorAll('.preference_modal');
    var modal_instances = M.Modal.init(modal_elems, {
        onOpenStart: function() {
            clicked_finished = false;
        },
        onCloseStart: function(elem) {
            elem.scrollTo(0, 0);
            if (!clicked_finished) {
                return;
            }
            if (selected_class === null) {return;}
            save_preferences();
        }
    });
});