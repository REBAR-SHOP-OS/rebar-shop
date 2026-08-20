# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'
    _description = 'Convert Lead to Opportunity (not in mass)'

    name = fields.Selection([
        ('convert', 'Convert to opportunity'),
        ('merge', 'Merge with existing opportunities')
    ], 'Conversion Action',default="convert", readonly=False, store=True, compute_sudo=False)