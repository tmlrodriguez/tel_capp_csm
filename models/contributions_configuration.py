from odoo import api, fields, models
from odoo.odoo.exceptions import ValidationError


class SavingsTypes(models.Model):
    """
        DOCSTRING: SavingsTypes model responsible for managing clients savings types.
    """
    _name = 'contributions.manager.savings.type'
    _description = 'Savings Type'
    _rec_name = 'saving_name'
    _inherit = ['mail.thread']

    saving_name = fields.Char(string='Nombre del Tipo de Ahorro', required=True, tracking=True)
    description = fields.Char(string='Descripción del Tipo de Ahorro', required=False, tracking=True)
    journal = fields.Many2one('account.journal', string='Journal', required=True, tracking=True, domain="[('type', 'in', ('bank', 'cash', 'general'))]")
    saving_account = fields.Many2one('account.account', string='Cuenta de Ahorro', required=True, tracking=True, domain="[('account_type', 'in', ('asset_current', 'liability_current'))]")
    interest_payment_account = fields.Many2one('account.account', required=True, string='Cuenta Pago de Interés', tracking=True, domain="[('account_type', '=', 'expense_financial')]")
    interest_rate = fields.Float(string='Tasa de Interés (%)', required=True, tracking=True, help="Tasa de interés anual para este tipo de ahorro.")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
        default=lambda self: self.env.company,
        tracking=True,
        required=True,
    )

    interest_rate_display = fields.Char(string='Tasa de Interes (%)', compute='_compute_interest_rate_display', store=False)

    _sql_constraints = [
        ('unique_savings_type_company', 'UNIQUE(savings_name, company_id)', 'El nombre del ahorro debe ser único por empresa.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._validate_percentage_rates(vals)
            if vals.get('savings_name'):
                vals['savings_name'] = vals['savings_name'].title()
            if vals.get('description'):
                vals['description'] = vals['description'].capitalize()
        return super().create(vals_list)

    def write(self, vals):
        self._validate_percentage_rates(vals)
        if vals.get('savings_name'):
            vals['savings_name'] = vals['savings_name'].title()
        if vals.get('description'):
            vals['description'] = vals['description'].capitalize()
        return super().write(vals)

    # Validations
    def _validate_percentage_rates(self, vals):
        to_check = {
            'interest_rate': 'Interés',
        }
        for field, label in to_check.items():
            if field in vals:
                value = vals[field]
                if value is None:
                    continue
                if value < 0 or value > 100:
                    raise ValidationError(
                        f'El porcentaje de {label} debe estar entre 0% y 100%. Valor recibido: {value}'
                    )

    # UI Changes
    @api.depends('interest_rate')
    def _compute_interest_rate_display(self):
        for record in self:
            record.interest_rate_display = f"{record.interest_rate:.2f}%"


class ContributionsTypes(models.Model):
    """
        DOCSTRING: ContributionsType model responsible for managing clients contributions types.
    """
    _name = 'contributions.manager.contributions.type'
    _description = 'Contributions Type'
    _rec_name = 'contribution_name'
    _inherit = ['mail.thread']

    contribution_name = fields.Char(string='Nombre del Tipo de Contribucion', required=True, tracking=True)
    description = fields.Char(string='Descripción del Tipo de Contribucion', required=False, tracking=True)
    journal = fields.Many2one('account.journal', string='Journal', required=True, tracking=True, domain="[('type', 'in', ('bank', 'cash', 'general'))]")
    saving_account = fields.Many2one('account.account', string='Cuenta de Ahorro', required=True, tracking=True, domain="[('account_type', 'in', ('asset_current', 'liability_current'))]")
    interest_payment_account = fields.Many2one('account.account', required=True, string='Cuenta Pago de Interés', tracking=True, domain="[('account_type', '=', 'expense_financial')]")
    interest_rate = fields.Float(string='Tasa de Interés (%)', required=True, tracking=True, help="Tasa de interés anual para este tipo de ahorro.")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
        default=lambda self: self.env.company,
        tracking=True,
        required=True,
    )

    interest_rate_display = fields.Char(string='Tasa de Interes (%)', compute='_compute_interest_rate_display', store=False)

    _sql_constraints = [
        ('unique_savings_type_company', 'UNIQUE(savings_name, company_id)', 'El nombre de la contribucion debe ser único por empresa.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._validate_percentage_rates(vals)
            if vals.get('contribution_name'):
                vals['contribution_name'] = vals['contribution_name'].title()
            if vals.get('description'):
                vals['description'] = vals['description'].capitalize()
        return super().create(vals_list)

    def write(self, vals):
        self._validate_percentage_rates(vals)
        if vals.get('contribution_name'):
            vals['contribution_name'] = vals['contribution_name'].title()
        if vals.get('description'):
            vals['description'] = vals['description'].capitalize()
        return super().write(vals)

    # Validations
    def _validate_percentage_rates(self, vals):
        to_check = {
            'interest_rate': 'Interés',
        }
        for field, label in to_check.items():
            if field in vals:
                value = vals[field]
                if value is None:
                    continue
                if value < 0 or value > 100:
                    raise ValidationError(
                        f'El porcentaje de {label} debe estar entre 0% y 100%. Valor recibido: {value}'
                    )

    # UI Changes
    @api.depends('interest_rate')
    def _compute_interest_rate_display(self):
        for record in self:
            record.interest_rate_display = f"{record.interest_rate:.2f}%"