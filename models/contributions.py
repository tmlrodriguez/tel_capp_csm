from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class PartnerContribution(models.Model):
    """
        DOCSTRING:
        PartnerContribution model responsible for linking partners with their contribution types.
        Tracks contribution type, current amount, and activation status.
    """
    _name = 'contributions.manager.partner.contribution'
    _description = 'Partner Contributions'
    _rec_name = 'display_name'
    _inherit = ['mail.thread']

    partner_id = fields.Many2one('res.partner', string='Cliente / Asociado', required=True, tracking=True, ondelete='restrict')
    contribution_type_id = fields.Many2one('contributions.manager.contribution.type', string='Tipo de Contribución', required=True, tracking=True, ondelete='restrict')
    current_amount = fields.Float(string='Monto Actual', required=True, tracking=True, default=0.0, help="Monto total actualmente acumulado en esta contribución.")
    enabled = fields.Boolean(string='Activo', default=True, tracking=True, help="Indica si esta contribución está activa para el cliente.")
    deposit_bank_account = fields.Many2one(string='Cuenta de Banco Deposito de Ahorros', related='contribution_type_id.deposit_bank_account', readonly=True, store=False)
    saving_account = fields.Many2one(string='Cuenta de Ahorro de Cliente', related='contribution_type_id.saving_account', readonly=True, store=False)
    interest_payment_account = fields.Many2one(string='Cuenta Gasto por Intereses Pagados', related='contribution_type_id.interest_payment_account', readonly=True, store=False)
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.company, tracking=True, required=True)
    display_name = fields.Char(string='Nombre para Mostrar', compute='_compute_display_name', store=False)

    _sql_constraints = [
        ('unique_contribution_partner_type', 'UNIQUE(partner_id, contribution_type_id, company_id)', 'El socio solo puede asignar este tipo de contribución una vez.'),
    ]

    # Validations
    @api.constrains('current_amount')
    def _check_non_negative_amount(self):
        for record in self:
            if record.current_amount < 0:
                raise ValidationError("El monto actual no puede ser negativo.")

    # Overridden Methods
    def unlink(self):
        for rec in self:
            if rec.current_amount > 0:
                raise ValidationError(
                    f"No se puede eliminar la aportación '{rec.contribution_type_id.contribution_name}' "
                    f"porque tiene un monto actual de {rec.current_amount}."
                )
        return super().unlink()

    # Methods
    def action_save_popup(self):
        self.ensure_one()
        self.write({
            'enabled': self.enabled,
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_view_contributions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f"Aportaciones de {self.partner_id.name} - {self.contribution_type_id.contribution_name}",
            'res_model': 'contributions.manager.contribution',
            'view_mode': 'list',
            'target': 'new',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('contribution_type_id', '=', self.contribution_type_id.id),
            ],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_contribution_type_id': self.contribution_type_id.id,
                'create': False,
                'edit': False,
                'delete': False,
            },
        }

    def action_view_withdrawals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f"Aportaciones de {self.partner_id.name} - {self.contribution_type_id.contribution_name}",
            'res_model': 'contributions.manager.withdrawal',
            'view_mode': 'list',
            'target': 'new',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('contribution_type_id', '=', self.contribution_type_id.id),
            ],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_contribution_type_id': self.contribution_type_id.id,
                'create': False,
                'edit': False,
                'delete': False,
            },
        }


class Contribution(models.Model):
    """
        DOCSTRING: Contribution Model representing an actual monetary contribution made by a partner.
        Each record is a single deposit/transaction toward an active partner contribution.
    """
    _name = 'contributions.manager.contribution'
    _description = 'Partner Contribution Transactions'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    reference = fields.Char(string='Referencia', readonly=True, copy=False, default=lambda self: _('New'), tracking=True)
    partner_id = fields.Many2one('res.partner', string='Cliente / Asociado', required=True, tracking=True)
    contribution_type_id = fields.Many2one('contributions.manager.contribution.type', string='Tipo de Contribución', required=True, tracking=True)
    amount = fields.Float(string='Monto de la Aportación', required=True, tracking=True, help="Monto de dinero que el asociado aporta a este tipo de contribución.")
    date = fields.Date(string='Fecha de Aportación', default=fields.Date.context_today, required=True, tracking=True)
    company_id = fields.Many2one('res.company',string='Empresa', required=True, default=lambda self: self.env.company, tracking=True)
    contribution_status = fields.Selection([
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

    # Overrides
    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('contributions.manager.contribution') or _('New')
        return super(Contribution, self).create(vals)

    def unlink(self):
        raise ValidationError("No se puede eliminar una aportación registrada. Contacte a administración para reversas.")

    # Computed Fields
    @api.depends('partner_id', 'contribution_type_id', 'amount')
    def _compute_display_name(self):
        for rec in self:
            partner = rec.partner_id.name or ''
            ctype = rec.contribution_type_id.contribution_name or ''
            rec.display_name = f"{partner} - {ctype} ({rec.amount:.2f})"

    # Validations
    @api.constrains('partner_id', 'contribution_type_id', 'amount')
    def _check_partner_contribution_validity(self):
        for rec in self:
            if rec.contribution_status in ('confirmed', 'registered'):
                continue
            if rec.amount <= 0:
                raise ValidationError("El monto de la aportación debe ser mayor que 0.")

            partner_contribution = self.env['contributions.manager.partner.contribution'].search([
                ('partner_id', '=', rec.partner_id.id),
                ('contribution_type_id', '=', rec.contribution_type_id.id),
                ('company_id', '=', rec.company_id.id),
                ('enabled', '=', True)
            ], limit=1)

            if not partner_contribution:
                raise ValidationError(
                    "Este asociado no tiene asignado este tipo de contribución activa. "
                    "No se puede registrar esta aportación."
                )

    # State Change Methods
    def action_confirm(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("El monto de la aportación debe ser mayor que 0.")
            if rec.contribution_status != 'draft':
                raise ValidationError("Solo se pueden confirmar aportaciones en estado borrador.")
            rec.write({'contribution_status': 'confirmed'})

    def action_register(self):
        for rec in self:
            if rec.contribution_status != 'confirmed':
                raise ValidationError("Solo se pueden contabilizar aportaciones confirmadas.")
            if rec.move_id:
                raise ValidationError("Esta aportación ya fue contabilizada.")
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
            partner_contribution.current_amount += rec.amount
            rec.write({
                'move_id': move.id,
                'contribution_status': 'registered'
            })

    # Internal methods
    def _create_accounting_move(self):
        self.ensure_one()
        contrib_type = self.contribution_type_id

        journal = contrib_type.journal
        if not journal:
            raise ValidationError("No se ha definido un diario contable para este tipo de contribución.")

        debit_account = contrib_type.deposit_bank_account
        credit_account = contrib_type.saving_account

        if not debit_account or not credit_account:
            raise ValidationError(
                "Las cuentas contables no están configuradas correctamente en el tipo de contribución."
            )

        move_vals = {
            'ref': self.reference,
            'date': self.date,
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'line_ids': [
                (0, 0, {
                    'account_id': debit_account.id,
                    'debit': self.amount,
                    'credit': 0.0,
                    'partner_id': self.partner_id.id,
                    'name': f"Aportación {contrib_type.contribution_name}"
                }),
                (0, 0, {
                    'account_id': credit_account.id,
                    'credit': self.amount,
                    'debit': 0.0,
                    'partner_id': self.partner_id.id,
                    'name': f"Aportación {contrib_type.contribution_name}"
                })
            ]
        }
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        return move

    # UI Changes
    @api.depends('partner_id')
    def _compute_allowed_contribution_types(self):
        for rec in self:
            if rec.partner_id:
                allowed_types = self.env['contributions.manager.partner.contribution'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('enabled', '=', True)
                ]).mapped('contribution_type_id')
                rec.allowed_contribution_type_ids = allowed_types
            else:
                rec.allowed_contribution_type_ids = [(5, 0, 0)]
