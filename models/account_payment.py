from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    journal_internal_use = fields.Boolean(compute='_compute_journal_internal_use', store=False)
    internal_withdrawal_id = fields.Many2one(
        'contributions.manager.withdrawal',
        string='Retiro Uso Interno',
        domain="[('internal_use', '=', True), ('internal_used', '=', False), ('withdrawal_status', '=', 'registered'), ('partner_id', '=', partner_id)]",
        help="Selecciona un retiro marcado como uso interno del cliente."
    )

    @api.depends('journal_id')
    def _compute_journal_internal_use(self):
        for w in self:
            w.journal_internal_use = bool(w.journal_id.internal_use)

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id and getattr(self.journal_id, 'internal_use', False):
            return {'domain': {'internal_withdrawal_id': [
                ('internal_use', '=', True),
                ('internal_used', '=', False),
                ('withdrawal_status', '=', 'registered'),
                ('partner_id', '=', self.partner_id.id),
            ]}}
        else:
            self.internal_withdrawal_id = False
        return {}

    @api.onchange('internal_withdrawal_id')
    def _onchange_internal_withdrawal_id(self):
        if self.internal_withdrawal_id:
            self.amount = self.internal_withdrawal_id.amount

    def _create_payments(self):
        payments = super()._create_payments()
        if self.internal_withdrawal_id:
            payments.write({'internal_withdrawal_id': self.internal_withdrawal_id.id})
            self.internal_withdrawal_id.mark_as_used(
                payment=payments,
                invoice=self.line_ids.move_id if self.line_ids and self.line_ids.move_id else None
            )
        return payments


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    internal_withdrawal_id = fields.Many2one(
        'contributions.manager.withdrawal',
        string='Retiro Uso Interno',
        readonly=True,
        help="Retiro utilizado como fuente del pago."
    )