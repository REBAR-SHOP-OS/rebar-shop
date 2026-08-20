# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    assigned_vendor_id = fields.Many2one('res.users', 'Assigned Vendor')
    estimation_weight = fields.Float('Estimation Weight', tracking=True)
    date_vendor_assign = fields.Date(
        'Vendor Assignment Date', compute='_compute_date_vendor_assign',
        copy=True, readonly=True, store=True,
        help="Last date this case was assigned to a vendor")

    @api.depends("assigned_vendor_id")
    def _compute_date_vendor_assign(self):
        for lead in self:
            if not lead.assigned_vendor_id:
                lead.date_vendor_assign = False
            else:
                lead.date_vendor_assign = fields.Date.context_today(lead)

    def add_mail_followers(self):
        for rec in self:
            if rec.assigned_vendor_id:
                mail_followers_exist = self.env["mail.followers"].search([
                    ('res_model', '=', 'crm.lead'),
                    ('res_id', '=', rec.id),
                    ('partner_id', '=', rec.assigned_vendor_id.partner_id.id)])
                if not mail_followers_exist:
                    self.env["mail.followers"].create(
                                {
                                    "res_model": "crm.lead",
                                    "res_id": rec.id,
                                    "partner_id": rec.assigned_vendor_id.partner_id.id
                                }
                            )

    @api.model_create_multi
    def create(self, values_list):
        records = super(CrmLead, self).create(values_list)
        records.add_mail_followers()
        return records

    def write(self, vals):
        result = super(CrmLead, self).write(vals)
        if vals.get('assigned_vendor_id'):
            self.add_mail_followers()
        return result
    
    def update_vendor_lead_portal(self, values):
        self.check_access_rights('write')
        for lead in self:
            lead_values = {
                'expected_revenue': values['expected_revenue'],
                'probability': values['probability'] or False,
                'priority': values['priority'],
                'date_deadline': values['date_deadline'] or False,
                'estimation_weight': values['estimation_weight'],
            }
            # As activities may belong to several users, only the current portal user activity
            # will be modified by the portal form. If no activity exist we create a new one instead
            # that we assign to the portal user.

            user_activity = lead.sudo().activity_ids.filtered(lambda activity: activity.user_id == self.env.user)[:1]
            if values['activity_date_deadline']:
                if user_activity:
                    user_activity.sudo().write({
                        'activity_type_id': values['activity_type_id'],
                        'summary': values['activity_summary'],
                        'date_deadline': values['activity_date_deadline'],
                    })
                else:
                    self.env['mail.activity'].sudo().create({
                        'res_model_id': self.env.ref('crm.model_crm_lead').id,
                        'res_id': lead.id,
                        'user_id': self.env.user.id,
                        'activity_type_id': values['activity_type_id'],
                        'summary': values['activity_summary'],
                        'date_deadline': values['activity_date_deadline'],
                    })
            lead.write(lead_values)

class DiscussChannel(models.Model):
    _inherit = 'crm.lead'
    
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, *args, body='', message_type='notification', **kwargs):
        lead_partners = kwargs.pop('lead_partners', '')
        lead_partners_list = [
            int(partner) for partner in lead_partners.split(',') if partner.isdigit()
        ] if lead_partners else []
        if lead_partners_list:
            kwargs['partner_ids'] = kwargs.get('partner_ids', []) + lead_partners_list
        return super().message_post(*args, body=body, message_type=message_type, **kwargs)
