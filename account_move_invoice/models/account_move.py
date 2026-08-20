from odoo import models, fields, api, _



class AccountMove(models.Model):
    _inherit = "account.move"

    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', change_default=True)
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string='State')
    country_id = fields.Many2one('res.country', string='Country')
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier")