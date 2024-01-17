odoo.define('wika_dashboard.view', function (require) {
    "use strict";

    var core = require('web.core');
    var FieldChar = require('web.basic_fields').FieldChar;

    var _t = core._t;

    FieldChar.include({
        init: function () {
            this._super.apply(this, arguments);
            this.events = _.extend(this.events || {}, {
                'change .o_field_char': 'onChange'
            });
        },
        onChange: function () {
            this._super.apply(this, arguments);
            this.trigger_up('field_changed', {
                dataPointID: this.dataPointID,
                changes: {}
            });
        }
    });

    function onFolderIdChange(folder_id) {
        var $field = $('[name="folder_id"]');
        var value = $field.val();

        if (value === 'Purchase') {
            $field.css('color', 'blue');
            $field.css('font-weight', 'bold');
        } else if (value === 'GR/SES') {
            $field.css('color', 'green');
            $field.css('font-weight', 'bold');
        } else {
            // Reset styles if needed
            $field.css('color', '');
            $field.css('font-weight', '');
        }
    }

    return {
        onFolderIdChange: onFolderIdChange
    };
});
