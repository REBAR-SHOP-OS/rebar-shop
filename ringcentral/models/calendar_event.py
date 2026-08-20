# See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo import fields, models
from odoo.http import request, DEFAULT_MAX_CONTENT_LENGTH
import odoo


class CalendarEvents(models.Model):
    _inherit = "calendar.event"

    lead_id = fields.Many2one("crm.lead", string="Lead", readonly=True)


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        user = self.env.user
        session_info = super(Http, self).session_info()
        user_has_group = user.has_group('ringcentral.ringcentral_user')
        session_info.update({
            'user_has_group': user_has_group
        })
        return session_info
