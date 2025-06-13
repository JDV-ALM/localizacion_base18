odoo.define('l10n_ve_nc_status.statusbar_payment', function (require) {
    "use strict";
    console.log('🛠️ l10n_ve_nc_status patch loaded');  // <--- línea de debug

    const FormRenderer = require('web.FormRenderer');
    FormRenderer.include({

        _renderHeader: function () {
            // 1) Llamas al original
            const header = this._super(...arguments);
            // 2) En el siguiente tick del event loop, ajustas el texto
            setTimeout(() => {
                const rec = this.state.data;
                if (rec.move_type === 'out_refund' || rec.move_type === 'in_refund') {
                    // Busca cualquier SPAN marcado como “paid” en la cinta
                    this.el.querySelectorAll('.o_form_statusbar_state_paid, .o_form_statusbar_status_paid')
                        .forEach(node => node.textContent = 'Validado');
                }
            }, 0);
            return header;
        },

    });
});
