function ensure_drugsalcohol_data() {
    if (typeof data_changes == 'undefined') {
        data_changes = [];
    }

    var stored_drugsalcohol = data_changes['id_em_care_inj_drug_alcohol'];

    if (stored_drugsalcohol == undefined) {
        stored_drugsalcohol = [];
        // pick up the existing (page-loaded) items
        $('.drugsalcohol-item').find('span').each(function(){
            stored_drugsalcohol.push($(this).data('id').toString());
        });
        data_changes['id_em_care_inj_drug_alcohol'] = stored_drugsalcohol;
    }
}

function drugsalcohol_select_changed(value, text, $selected) {
    if ($selected == null) {
        return;     // this event fires when calling 'restore defaults'
    }

    ensure_drugsalcohol_data();

    var drugsalcohol_id = value;
    var drugsalcohol_data = data_changes['id_em_care_inj_drug_alcohol'];
    // TODO magic constant
console.log('Before');
console.log(data_changes['id_em_care_inj_drug_alcohol']);
    if ($.inArray(drugsalcohol_id, drugsalcohol_data) > -1) {
        return;
    }

    drugsalcohol_data.push(drugsalcohol_id);
    $('#id_em_care_inj_drug_alcohol').val(JSON.stringify(drugsalcohol_data));
console.log('After');
console.log(JSON.stringify(drugsalcohol_data));

    var drugsalcohol_template = $('.drugsalcohol-item-template');
    var cloned_drugsalcohol = drugsalcohol_template.clone(true, true);
    cloned_drugsalcohol.removeClass('drugsalcohol-item-template')
                       .addClass('drugsalcohol-item');
    cloned_drugsalcohol.find('.drugsalcohol-narrative')
                       .attr('data-id', drugsalcohol_id)
                       .text(text);
    cloned_drugsalcohol.css('display', '');

    $('#new_drugsalcohol_select_row').before(cloned_drugsalcohol);
}

function initialise_injury_panel() {
    $('#new_drugsalcohol_select').dropdown(
        {
            action: 'select',
            onChange: drugsalcohol_select_changed
        }
    );

    if (typeof initialise_injury_dropdowns != 'undefined') {
        initialise_injury_dropdowns();     // TODO has to be in the view as it contains template tags
    }

    $('.drugsalcohol-delete').click(function(evt) {
        $(evt.target).closest('.drugsalcohol-item').remove();
        if (typeof data_changes == 'undefined') {
            data_changes = [];
        }
console.log('Deleting - before');
console.log(data_changes['id_em_care_inj_drug_alcohol']);
        data_changes['id_em_care_inj_drug_alcohol'] = null;
        ensure_drugsalcohol_data();
console.log('After');
console.log(data_changes['id_em_care_inj_drug_alcohol']);
        $('#id_em_care_inj_drug_alcohol').val(JSON.stringify(data_changes['id_em_care_inj_drug_alcohol']));
    });
}