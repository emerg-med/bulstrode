// data change tracking and posting
var data_changes = {};

function post_data_changes(evt) {
    if (Object.keys(data_changes).length > 0) {
        var data_changes_in_flight = data_changes;      // keep a local copy in case we need to revert
        data_changes = {};
        $.each(data_changes_in_flight, function(key, value) {
            if ((value.constructor === Array) &&
                (value.length == 0)) {
                // can't send empty arrays so must do this instead
                data_changes_in_flight[key] = '__delete_marker__';     // TODO: magic constant
            }
        });

        var episode_form = $('#episode_form');

        $.ajax({
            type: 'POST',
            mimeType: 'text/plain; charset=x-user-defined',
            url: episode_form.attr('action'),
            dataType: 'json',
            data: {'data': JSON.stringify(data_changes_in_flight)},   //JSON.stringify(data_changes_in_flight),
            success: function (result) {
                // expects result of the form { 'container_id': 'content', ...}
                var collapsed_panels = null;
                $.each(result, function(key, value) {
                    if (key == 'collapsed_panels') {
                        collapsed_panels = value;
                    } else {
                        var container = $('#' + key);
                        container.html(value);

                        if (key == 'accordion_content') {
                            initialise_injury_panel();
                            container.accordion('refresh');
                            initialise_page_dropdowns();
                            initialise_diagnosis_sortable();
                        } else if (key == 'state_icon_content') {
                            initialise_icon_panel();
                        }

                        add_change_handlers(container);      // do this after setting up the dropdowns
                    }
                });

                if (collapsed_panels != null) {
                    var accordion_content = $('#accordion_content');
                    var panel_count = $('.ui.accordion .content').length;

                    for (var count = 0; count < panel_count; count++) {
                        if ($.inArray(count, collapsed_panels) > -1) {
                            accordion_content.accordion('close', count);
                        } else {
                            accordion_content.accordion('open', count);
                        }
                    }
                }
            }
        });
    }

    //don't submit the form
    return false;
}

function post_breach() {
    var breach_form = $('#breach_form');

    $.ajax({
            type: 'POST',
            mimeType: 'text/plain; charset=x-user-defined',
            url: breach_form.attr('action'),
            dataType: 'json',
            data: breach_form.serialize(),
            success: function (result) {
                clear_breach_detail();
            },
            error: function (result) {
                clear_breach_detail();
            }});
}

function new_diagnosis_select_changed(value, text, $selected) {
    $("#diagnoses_grid").sortable("destroy");

    if ($selected == null) {
        return;
    }

    ensure_diagnoses_data();

    var diagnosis_id = value;
    var diagnoses_data = data_changes['id_em_care_diagnosis'];
    // TODO magic constant

    if ($.inArray(diagnosis_id, diagnoses_data) > -1) {
        return;
    }

    diagnoses_data.push({'index': diagnoses_data.length + 1, 'code': diagnosis_id, 'mod': 9});

    var diagnosis_template = $('.diagnosis-item-template');
    var cloned_diagnosis = diagnosis_template.clone(true, true);
    cloned_diagnosis.removeClass('diagnosis-item-template')
                    .addClass('diagnosis-item');
    cloned_diagnosis.find('.diagnosis-narrative')
                    .attr('data-id', diagnosis_id)
                    .text(text);
    cloned_diagnosis.find('.diagnosis-modifier').dropdown(
            {
                onChange: diagnosis_modifier_changed
            }
        );
    cloned_diagnosis.css('display', '');
    //$('#new_diagnosis_select_row').before(cloned_diagnosis);
    $('#diagnoses_grid').append(cloned_diagnosis);

    initialise_diagnosis_sortable();
}

function diagnosis_moved(evt) {
    data_changes['id_em_care_diagnosis'] = null;
    ensure_diagnoses_data();
}

function diagnosis_modifier_changed(value, text, $selected) {
    data_changes['id_em_care_diagnosis'] = undefined;
    ensure_diagnoses_data();
}

function new_investigation_select_changed(value, text, $selected) {
    console.log('new_investigation_select_changed');
    console.log(value);
    console.log(text);
    console.log($selected);

    if ($selected == null) {
        return;
    }

    ensure_investigations_data();

    var investigation_id = value;

    if ($.inArray(investigation_id, data_changes['id_em_care_investigations']) > -1) {
        return;
    }

    data_changes['id_em_care_investigations'].push(investigation_id);

    var investigation_template = $('.investigation-item-template');
    var cloned_investigation = investigation_template.clone(true, true);
    cloned_investigation.removeClass('investigation-item-template')
                        .addClass('investigation-item');
    cloned_investigation.find('.investigation-narrative')
                        .attr('data-id', investigation_id)
                        .text(text);
    cloned_investigation.css('display', '');
//    $('#new_investigation_select_row').before(cloned_investigation);
    $('#investigations_grid').append(cloned_investigation);
}

// TODO this is basically a copy/paste of the code for investigations
function new_treatment_select_changed(value, text, $selected) {
    console.log('new_treatment_select_changed: ');
    if ($selected == null) {
        return;
    }
    console.log('1');

    ensure_treatments_data();
    console.log('2');

    var treatment_id = value;

    if ($.inArray(treatment_id, data_changes['id_em_care_treatments']) > -1) {
        return;
    }
    console.log('3');

    data_changes['id_em_care_treatments'].push(treatment_id);

    var treatment_template = $('.treatment-item-template');
    var cloned_treatment = treatment_template.clone(true, true);
    cloned_treatment.removeClass('treatment-item-template')
                    .addClass('treatment-item');
    cloned_treatment.find('.treatment-narrative')
                    .attr('data-id', treatment_id)
                    .text(text);
    cloned_treatment.css('display', '');
    $('#treatments_grid').append(cloned_treatment);
    console.log('4');
}

// TODO maybe we can break this up a bit more so it's not called every time for everything?
function add_change_handlers($container) {
    $container.find('.track-value-changes').change(function() {
        var self = $(this);
        var value = null;

        if (self[0].type == 'checkbox') {
            value = self.prop('checked');   // checkboxes don't support .val(), which in that case always returns 'on'
        } else {
            value = self.val();
        }

        data_changes[self.prop('id')] = value;
    });

    $container.find('#id_em_care_clinical_narrative_add_button').click(function() {
        var narrative_add_input = $('#id_em_care_clinical_narrative_add');
        var new_note = narrative_add_input.val();

        if (new_note.length > 0) {
            var narrative_span = $('#id_em_care_clinical_narrative');
            var narrative = narrative_span.text();
            if (narrative.length > 0) {
                narrative = narrative + ';' + new_note;
            } else {
                narrative = new_note;
            }
            narrative_span.text(narrative);

            if (data_changes['id_em_care_clinical_narrative'] == undefined) {
                data_changes['id_em_care_clinical_narrative'] = new_note;
            } else {
                data_changes['id_em_care_clinical_narrative'] = data_changes['id_em_care_clinical_narrative'] +
                        ';' + new_note;
            }

            narrative_add_input.val('');
        }
    });

    $container.find('.diagnosis-modifier').change(function(evt) {
        data_changes['id_em_care_diagnosis'] = undefined;
        ensure_diagnoses_data();
    });

    $container.find('.diagnosis-delete').click(function(evt) {
        $(evt.target).closest('.diagnosis-item').remove();
        data_changes['id_em_care_diagnosis'] = null;
        ensure_diagnoses_data();
    });

    $container.find('.investigation-delete').click(function(evt) {
        $(evt.target).closest('.investigation-item').remove();
        data_changes['id_em_care_investigations'] = null;
        ensure_investigations_data();
    });

    // TODO this is basically a copy/paste of the code for investigations
    $container.find('.treatment-delete').click(function(evt) {
        $(evt.target).closest('.treatment-item').remove();
        data_changes['id_em_care_treatments'] = null;
        ensure_treatments_data();
    });

    $container.find('#id_em_care_discharge_status').change(function() {
        var discharge_status_select = $('#id_em_care_discharge_status');
        var discharge_status = parseInt(discharge_status_select.val());

        if (discharge_status == 2018412100) {
            $('#admit_speciality_container').hide();
            $('#transfer_destination_container').show();
        } else if ((discharge_status >= 2018211100) && (discharge_status <= 2018511100)) {
            $('#admit_speciality_container').show();
            $('#transfer_destination_container').hide();
        } else {
            $('#admit_speciality_container').hide();
            $('#transfer_destination_container').hide();
        }

        if (discharge_status < 2018211100) {
            $('discharge_letter_button').show();
        } else {
            $('discharge_letter_button').hide();
        }
    });

    $container.find('#discharge_letter_button').click(function() {
        // TODO: pop up discharge letter and internally set 'information given' flag
        // for now:
        alert('This is a placeholder for the GP letter pop-up');
        data_changes['id_em_care_discharge_information_given'] = true;
    });

    $container.find('#discharge_button').click(function() {
        data_changes['id___complete_discharge__'] = true;      // TODO: magic constant
        $(this).hide();
        $('#discharge_button_clicked_label').show();
    });

    $container.find('#undo_early_discharge_button').click(function() {
//        $('#episode_save_button').show();         TODO why was this in here?
        data_changes['id___undo_early_discharge__'] = true;
        post_data_changes();
    });

    $container.find('#early_discharge_button').click(function() {
        $('#early_discharge_button').remove();
//        $('#episode_save_button').hide();         TODO why was this in here?
        data_changes['id___early_discharge__'] = true;      // TODO: magic constant
        post_data_changes();
    });
}

function breach_cancel_button_action(evt){
    hide_breach_modal();
    clear_breach_detail();
}

function breach_submit_button_action(evt){
    hide_breach_modal();
    post_breach();
    clear_breach_detail();
}

function clear_breach_detail() {
    $('#breach_detail').val('');
}
// TODO this has to be inline in episode.html because it contains a Django template tag... find a better way
//
//function run_transfer_destination_search() {
//....
//}

function ensure_diagnoses_data() {
    var stored_diagnoses = data_changes['id_em_care_diagnosis'];

    if (stored_diagnoses == undefined) {
        stored_diagnoses = [];
        // pick up the existing (page-loaded) diagnoses
        $('.diagnosis-item').each(function(idx, val){
            stored_diagnoses.push({'index': idx + 1,
                                   'code': $(this).find('span').first().data('id').toString(),
                                   'mod': $(this).find('select option:selected').first().val()});
        });
        data_changes['id_em_care_diagnosis'] = stored_diagnoses;
    }
}

function ensure_investigations_data() {
    var stored_investigations = data_changes['id_em_care_investigations'];

    if (stored_investigations == undefined) {
        stored_investigations = [];
        // pick up the existing (page-loaded) investigations
        $('.investigation-item').find('span').each(function(){
            stored_investigations.push($(this).data('id').toString())
        });
        data_changes['id_em_care_investigations'] = stored_investigations;
    }
}

// TODO this is basically a copy/paste of the code for investigations
function ensure_treatments_data() {
    var stored_treatments = data_changes['id_em_care_treatments'];

    if (stored_treatments == undefined) {
        stored_treatments = [];
        // pick up the existing (page-loaded) treatments
        $('.treatment-item').find('span').each(function(){
            stored_treatments.push($(this).data('id').toString())
        });
        data_changes['id_em_care_treatments'] = stored_treatments;
    }
}

function hide_breach_modal() {
    $('.ui.modal.breach').modal('hide');
}
function initialise_diagnosis_sortable() {
    $("#diagnoses_grid").sortable({
        handle: '.diagnosis-handle',
        animation: 150,
        onUpdate: diagnosis_moved
    });
}

function initialise_page_dropdowns() {
    $('.diagnosis-modifier').dropdown(
        {
            onChange: diagnosis_modifier_changed
        }
    );
    $('#id_em_care_chief_complaint_outer_dropdown').dropdown();
    $('#id_assigned_clinician_outer_dropdown').dropdown();
    $('#id_bed_outer_dropdown').dropdown();
    $('#new_treatment_select_outer_dropdown').dropdown(
        {
            action: 'select',
            onChange: new_treatment_select_changed,
        }
    );
    $('#new_investigation_select_outer_dropdown').dropdown(
        {
            action: 'select',
            onChange: new_investigation_select_changed
        }
    );

    initialise_new_diagnosis_dropdown();

    if (typeof initialise_transfer_destination_dropdown != 'undefined') {
        initialise_transfer_destination_dropdown();
        initialise_discharge_dropdowns();
    }
}

function initialise_icon_panel() {
    $('.popup').remove();
    $('#state_icon_content i').popup();
}

// set up
$('document').ready(function() {
    $('#episode_form').submit(post_data_changes);

    var accordion_content = $('#accordion_content');
    accordion_content.accordion(
        {
            exclusive: false
        }
    );

    initialise_page_dropdowns();

    episode_html_ready();
    initialise_injury_panel();
    initialise_icon_panel();

    $('#floating_save_button').click(post_data_changes);

    $('#floating_mobile_save_button').click(post_data_changes);

    $('#breach_cancel_button').click(breach_cancel_button_action);

    $('#breach_submit_button').click(breach_submit_button_action);

    $('.patient-gender').popup();

    $('.inline-patient-header-row').visibility({
        type   : 'fixed'
    });

    $('.floating-patient-header-row').visibility({
        type   : 'fixed'
    });

    initialise_diagnosis_sortable();

    // do this last otherwise we trigger value changed events while setting up the dropdowns
    add_change_handlers($('#pre_diagnosis_content'));
    add_change_handlers($('#additional_content'));
    add_change_handlers(accordion_content);
});