from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ContributionsTypes(models.Model):
    """
        DOCSTRING: ContributionsType model responsible for managing clients contributions types.
    """
    _name = 'contributions.manager.contribution.type'
    _description = 'Contributions Type'
    _rec_name = 'contribution_name'
    _inherit = ['mail.thread']

    contribution_name = fields.Char(string='Nombre del Tipo de Contribucion o Ahorro', required=True, tracking=True)
    description = fields.Char(string='Descripción del Tipo de Contribucion o Ahorro', required=False, tracking=True)
    allow_withdrawal = fields.Boolean(string='Permitir retiros', required=True, tracking=True, default=True)
    interest_rate = fields.Float(string='Tasa de Interés (%)', required=True, tracking=True, help="Tasa de interés anual para este tipo de ahorro.")
    days_per_year = fields.Selection([('360', '360'), ('365', '365'),], string='Dias por Año', required=True, tracking=True)
    calculation_method = fields.Selection([('DAV', 'Promedio Diario'),], string='Metodo de Calculo', required=True, tracking=True)
    capitalization_date = fields.Selection([('30', '30 de cada mes'),], string='Fecha de Capitalización', required=True, tracking=True)
    deposit_bank_account = fields.Many2one('account.account', string='Cuenta de Banco Deposito de Ahorros', required=True, tracking=True, domain="[('account_type', 'in', ('asset_current', 'liability_current'))]")
    saving_account = fields.Many2one('account.account', string='Cuenta de Ahorro de Cliente', required=True, tracking=True, domain="[('account_type', 'in', ('asset_current', 'liability_current'))]")
    interest_payment_account = fields.Many2one('account.account', required=True, string='Cuenta Gasto por Intereses Pagados', tracking=True, domain="[('account_type', '=', 'expense_financial')]")
    journal = fields.Many2one('account.journal', string='Diario Contable', required=True, tracking=True, domain="[('type', 'in', ('bank', 'cash', 'general'))]")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
        default=lambda self: self.env.company,
        tracking=True,
        required=True,
    )

    interest_rate_display = fields.Char(string='Tasa de Interes (%)', compute='_compute_interest_rate_display', store=False)

    _sql_constraints = [
        ('unique_contribution_type_company', 'UNIQUE(contribution_name, company_id)', 'El nombre de la contribucion debe ser único por empresa.'),
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