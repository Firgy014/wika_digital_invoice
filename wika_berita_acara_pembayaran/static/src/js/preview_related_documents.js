odoo.define('wika_berita_acara_pembayaran.preview_related_documents', function (require) {
    "use strict";

    var core = require('web.core');
    var FormController = require('web.FormController');
    var FormView = require('web.FormView');
    var FieldMany2ManyTags = require('web.relational_fields').FieldMany2ManyTags;
    var QWeb = core.qweb;
    
    // tesdulsbro;

    FormController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.o_preview_related_docs', function () {
                    self._onPreviewRelatedDocuments();
                });
            }
        },

        _onPreviewRelatedDocuments: function () {
            var self = this;
            var documentIds = this.renderer.state.data.related_document_ids.res_ids;

            if (documentIds.length) {
                this._rpc({
                    model: 'documents.document',
                    method: 'read',
                    args: [documentIds],
                    context: self.initialState.context,
                }).then(function (documents) {
                    var $previewDialog = $(QWeb.render('PreviewRelatedDocuments', {documents: documents}));
                    $previewDialog.appendTo($('body'));
                    $previewDialog.modal('show');
                });
            }
        },
    });

    var PreviewRelatedDocuments = FieldMany2ManyTags.extend({
        init: function () {
            this._super.apply(this, arguments);
            this.previewTemplate = 'PreviewRelatedDocuments';
        },
    });

    FormView.include({
        config: _.extend({}, FormView.prototype.config, {
            PreviewRelatedDocuments: PreviewRelatedDocuments,
        }),
    });

});
