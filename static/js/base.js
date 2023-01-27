navigator.serviceWorker && navigator.serviceWorker.register("/sw.js").then(function(registration) {});
document.addEventListener('DOMContentLoaded', function() {
    var dropdown_elems = document.querySelectorAll('.dropdown-trigger');
    var dropdown_instances = M.Dropdown.init(dropdown_elems, {
        coverTrigger: false,
        alignment: 'right',
        constrainWidth: false
    });
    var modal_elems = document.querySelectorAll('.preference_modal');
    var modal_instances = M.Modal.init(modal_elems, {
        onOpenStart: function() {
            // Load in all Classes
            alert(1);
        },
        onCloseStart: function(elem) {
            elem.scrollTo(0, 0);
            // Save preferences
            alert(2);
        }
    });
});