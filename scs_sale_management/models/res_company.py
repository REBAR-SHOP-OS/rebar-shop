from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    restricted_models = fields.Many2many(
        "ir.model", string="Models with Delete Restrictions"
    )
