from odoo import api, fields, models


class ResPartner(models.Model):
    """
        DOCSTRING: ResPartner model inherits from res.partner and adds a new field called contributions_ids to the partner.
    """

    _inherit = 'res.partner'

    contribution_ids = fields.One2many(
        'contributions.manager.partner.contribution',
        'partner_id',
        string='Aportaciones / Ahorros'
    )

    def action_add_contribution(self):
        self.ensure_one()
        existing_type_ids = self.contribution_ids.mapped('contribution_type_id').ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Aportación',
            'res_model': 'contributions.manager.partner.contribution',
            'view_mode': 'form',
            'view_id': self.env.ref('tel_capp_csm.view_partner_contribution_form_popup').id,
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'exclude_contribution_type_ids': existing_type_ids,
            },
        }
