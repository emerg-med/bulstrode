var lock_uuid = null;
var lock_refresh_timeout = null;

function clear_warning_banner() {
    $('#record_locked_banner_message').hide();
}

function clear_error_banner() {
    $('#lock_failed_banner_message').hide();
    $('#lock_expired_banner_message').hide();
    $('#lock_error_banner_message').hide();
}

function show_warning_banner() {
    $('#warning_banner').removeClass('hidden');
}

function hide_warning_banner() {
    clear_warning_banner();
    $('#warning_banner').addClass('hidden');
}

function show_error_banner() {
    $('#error_banner').removeClass('hidden');
}

function hide_error_banner() {
    clear_error_banner();
    $('#error_banner').addClass('hidden');
}

function show_locked_warning_message() {
    clear_warning_banner();
    $('#record_locked_banner_message').css('display', '');
    show_warning_banner();
}

function show_lock_error_message() {
    clear_error_banner();
    $('#lock_error_banner_message').css('display', '');
    show_error_banner();
}

function show_lock_expired_message() {
    clear_error_banner();
    $('#lock_expired_banner_message').css('display', '');
    show_error_banner();

    if (lock_refresh_timeout != null) {
        window.clearInterval(lock_refresh_timeout);
    }
}

function show_lock_failure_message() {
    clear_error_banner();
    $('#lock_failed_banner_message').css('display', '');
    show_error_banner();
}

function hide_lock_steal_option() {
    $('#record_steal_popup').modal('hide');
}

function show_lock_steal_option() {
    $('#record_steal_popup').modal('setting',
        {
            onApprove: function() {
                hide_lock_steal_option();
                try_acquire_lock(true, false);
            },
            onDeny: function() {
                show_lock_failure_message();
                hide_lock_steal_option();
                disable_save();
            },
            closable: false
        }).modal('show');
}

function hide_save() {
    $.each(save_element_selector, function(key, value) {
        $(value).hide();
    });
//    $(save_element_selector).hide();
}

function show_save() {
    $.each(save_element_selector, function(key, value) {
        $(value).css('display', '');
    });
//    $(save_element_selector).css('display', '');
}

function disable_save() {
    $.each(save_element_selector, function(key, value) {
        $(value).remove();
    });
}

function enable_release_on_unload() {
    $(window).unload(release_lock);
}

// TODO: consolidate all these ajax post functions
function try_acquire_lock(force, second_try) {
    var acquire_lock_form = $('#acquire_lock_form');    // TODO don't really need this, it's only to get the 'action'
                                                        // and record id (which contain django form tags so can't live in here)
    hide_save();

    $.ajax({
        type: 'POST',
        mimeType: 'text/plain; charset=x-user-defined',
        url: acquire_lock_form.attr('action'),
        dataType: 'json',
        data: {'data': JSON.stringify({'id': acquire_lock_form.data('id'),
                                       'type': configured_lock_type,
                                       'force': force ? 1 : 0})},
        success: function (result) {
            if (result['result'] == '1') {
                lock_uuid = result['id'];
                enable_release_on_unload();
                lock_refresh_timeout = window.setInterval(try_refresh_lock, 5000);     // TODO magic number
                hide_error_banner();
                show_save();
            } else if (!force) {
                if (!second_try) {
                    show_locked_warning_message();
                    window.setTimeout(function() { try_acquire_lock(false, true); }, 5000);      // TODO magic number
                } else {
                    hide_warning_banner();
                    show_lock_steal_option();
                }
            } else {
                disable_save();
                show_lock_failure_message();
            }
        },
        error: function (result) {
            hide_save();
            show_lock_error_message();
            console.log(result);
            window.setTimeout(function() { try_acquire_lock(false, false); }, 10000);      // TODO magic number
        }
    });
}

function try_refresh_lock() {
    var refresh_lock_form = $('#refresh_lock_form');    // TODO don't really need this, it's only to get the 'action'
                                                        // (which contains django form tags so can't live in here)
    $.ajax({
        type: 'POST',
        mimeType: 'text/plain; charset=x-user-defined',
        url: refresh_lock_form.attr('action'),
        dataType: 'json',
        data: {'data': JSON.stringify({'id': lock_uuid,
                                       'type': configured_lock_type})},
        success: function (result) {
            if (result['result'] == '2') {      // failure due to lock expiry
                disable_save();
                show_lock_expired_message();
            } else if (result['result'] == '3') {
                disable_save();
                show_lock_error_message();
            } else {
                hide_error_banner();
                show_save();
            }
        },
        error: function (result) {
            hide_save();
            show_lock_error_message();
        }
    });
}

// TODO find a better way; this is a synchronous call and so hangs the browser tab until completion
// The purpose of explicitly releasing the lock handles a couple of corner cases - namely a) the user refreshes
// their browser, prompting a reload and claiming the record is locked (since we currently have no persistent session -
// note that the user login may not be sufficient as that appears to be recorded browser-wide rather than tab-local),
// and b) if one user leaves a record and another tries to view it within 10 seconds (this is a minor issue)
function release_lock() {
    var release_lock_form = $('#release_lock_form');    // TODO don't really need this, it's only to get the 'action'
                                                        // (which contains django form tags so can't live in here)
    $.ajax({
        type: 'POST',
        mimeType: 'text/plain; charset=x-user-defined',
        url: release_lock_form.attr('action'),
        data: {'data': JSON.stringify({'id': lock_uuid,
                                       'type': configured_lock_type})},
        async: false
    });
}

var configured_lock_type = 0;
var save_element_selector = [];

function configure_locking(lock_type, save_element) {
    configured_lock_type = lock_type;
    save_element_selector.push(save_element);
}

function add_save_element(save_element) {
    save_element_selector.push(save_element);
}

$('document').ready(function() {
    hide_error_banner();
    hide_warning_banner();
    try_acquire_lock(false, false);
});