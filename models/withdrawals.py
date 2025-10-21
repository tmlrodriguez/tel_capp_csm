from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Withdrawal(models.Model):
    """
        DOCSTRING: Withdrawal model representing a monetary withdrawal from a partner’s contribution.
        Each record is a transaction that reduces the partner’s current contribution balance.
    """
    _name = 'contributions.manager.withdrawal'
    _description = 'Partner Withdrawals'
    _inherit = ['mail.thread']
    _rec_name = 'display_name'

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente / Asociado',
        required=True,
        tracking=True
    )
    contribution_type_id = fields.Many2one(
        'contributions.manager.contribution.type',
        string='Tipo de Contribución',
        required=True,
        tracking=True
    )
    amount = fields.Float(
        string='Monto del Retiro',
        required=True,
        tracking=True,
        help="Monto de dinero que el asociado retira de este tipo de contribución."
    )
    date = fields.Date(
        string='Fecha del Retiro',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
        tracking=True
    )
    withdrawal_status = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('registered', 'Contabilizado')
    ], string='Estado', required=True, default='draft', readonly=True, tracking=True)
    move_id = fields.Many2one('account.move', string='Asiento de Registro', readonly=True, copy=False)
    display_name = fields.Char(string='Nombre para Mostrar', compute='_compute_display_name', store=False)

    allowed_contribution_type_ids = fields.Many2many(
        'contributions.manager.contribution.type',
        string='Tipos de Contribución Permitidos',
        compute='_compute_allowed_contribution_types',
        store=False
    )

    # Computed Methods
    @api.depends('partner_id', 'contribution_type_id', 'amount')
    def _compute_display_name(self):
        for rec in self:
            partner = rec.partner_id.name or ''
            ctype = rec.contribution_type_id.contribution_name or ''
            rec.display_name = f"Retiro: {partner} - {ctype} ({rec.amount:.2f})"

    @api.depends('partner_id')
    def _compute_allowed_contribution_types(self):
        for rec in self:
            if rec.partner_id:
                allowed_types = self.env['contributions.manager.partner.contribution'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('enabled', '=', True),
                    ('contribution_type_id.allow_withdrawal', '=', True)
                ]).mapped('contribution_type_id')
                rec.allowed_contribution_type_ids = allowed_types
            else:
                rec.allowed_contribution_type_ids = [(5, 0, 0)]

    # Validations
    @api.constrains('partner_id', 'contribution_type_id', 'amount')
    def _check_withdrawal_validity(self):
        for rec in self:
            if rec.withdrawal_status in ('confirmed', 'registered'):
                continue
            # if rec.amount <= 0:
            #     raise ValidationError("El monto del retiro debe ser mayor que 0.")

            partner_contribution = self.env['contributions.manager.partner.contribution'].search([
                ('partner_id', '=', rec.partner_id.id),
                ('contribution_type_id', '=', rec.contribution_type_id.id),
                ('company_id', '=', rec.company_id.id),
                ('enabled', '=', True)
            ], limit=1)

            if not partner_contribution:
                raise ValidationError("El asociado no tiene este tipo de contribución activa.")

            if not rec.contribution_type_id.allow_withdrawal:
                raise ValidationError("El tipo de contribución no permite retiros.")

            if rec.amount > partner_contribution.current_amount:
                raise ValidationError(
                    f"El monto del retiro ({rec.amount}) no puede superar el monto disponible ({partner_contribution.current_amount})."
                )

    # Overrides
    def unlink(self):
        raise ValidationError("No se puede eliminar un retiro registrado. Contacte a administración para reversas.")

    # Status methods
    def action_confirm(self):
        for rec in self:
            if rec.withdrawal_status != 'draft':
                raise ValidationError("Solo se pueden confirmar retiros en estado borrador.")
            rec.write({'withdrawal_status': 'confirmed'})

    def action_register(self):
        for rec in self:
            if rec.withdrawal_status != 'confirmed':
                raise ValidationError("Solo se pueden contabilizar retiros confirmados.")
            if rec.move_id:
                raise ValidationError("Este retiro ya fue contabilizado.")
            move = rec._create_accounting_move()
            partner_contribution = self.env['contributions.manager.partner.contribution'].search([
                ('partner_id', '=', rec.partner_id.id),
                ('contribution_type_id', '=', rec.contribution_type_id.id),
                ('company_id', '=', rec.company_id.id),
                ('enabled', '=', True)
            ], limit=1)
            if not partner_contribution:
                raise ValidationError(
                    "No se encontró la relación activa entre el asociado y el tipo de contribución."
                )
            # if rec.amount > partner_contribution.current_amount:
            #     raise ValidationError(
            #         f"El monto del retiro ({rec.amount}) excede el saldo disponible ({partner_contribution.current_amount})."
            #     )
            partner_contribution.current_amount -= rec.amount
            rec.write({
                'move_id': move.id,
                'withdrawal_status': 'registered'
            })

    # Internal Methods
    def _create_accounting_move(self):
        self.ensure_one()
        contrib_type = self.contribution_type_id

        journal = contrib_type.journal
        if not journal:
            raise ValidationError("No se ha definido un diario contable para este tipo de contribución.")

        debit_account = contrib_type.saving_account
        credit_account = contrib_type.deposit_bank_account

        move_vals = {
            'ref': f"{self.partner_id.name} - {contrib_type.contribution_name} (Retiro)",
            'date': self.date,
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'line_ids': [
                (0, 0, {
                    'account_id': debit_account.id,
                    'debit': self.amount,
                    'credit': 0.0,
                    'partner_id': self.partner_id.id,
                    'name': f"Retiro {contrib_type.contribution_name}"
                }),
                (0, 0, {
                    'account_id': credit_account.id,
                    'credit': self.amount,
                    'debit': 0.0,
                    'partner_id': self.partner_id.id,
                    'name': f"Retiro {contrib_type.contribution_name}"
                })
            ]
        }
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        return move