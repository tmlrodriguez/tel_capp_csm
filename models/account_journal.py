from odoo import api, models, fields

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    internal_use = fields.Boolean(string='Uso Interno', tracking=True, help="Indica que este diario se utilizará para cruces entre retiros y pagos internos de clientes.")