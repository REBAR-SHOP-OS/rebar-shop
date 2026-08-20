'crm.lead'# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.tools import format_datetime


class MailMessage(models.Model):
    _inherit = 'mail.message'

    def _portal_message_format(self, properties_names, options=None):
        vals_list = super()._portal_message_format(properties_names, options=options)
        logged_in_portal_partner = self.env.user.partner_id.id
        new_vals_list = []
        is_admin_user = self.env.is_admin()
        if is_admin_user:
            return vals_list
        for val in vals_list:
            msg_rec = self.env['mail.message'].browse(val["id"])
            partner_ids = msg_rec.partner_ids and msg_rec.partner_ids.ids or []
            if val.get("author_id"):
                author_id = int(val.get("author_id")[0])
                partner_ids.append(author_id)
            if self.filtered(lambda ms: ms.id == val.get('id') and \
                             logged_in_portal_partner in partner_ids and \
                             ms.model == 'crm.lead' and \
                             (val.get('date').date() >= \
                             self.env[ms.model].sudo().browse(ms.res_id).date_vendor_assign) \
                             or (val.get('attachment_ids') and logged_in_portal_partner in partner_ids)):
                new_vals_list.append(val)
        return new_vals_list

    @api.model_create_multi
    def create(self, vals):
        note_id = self.env['ir.model.data'].sudo()._xmlid_to_res_id('mail.mt_note')
        discussion_id = self.env['ir.model.data'].sudo()._xmlid_to_res_id('mail.mt_comment')
        for val in vals:
            if val.get('model') == 'crm.lead':
                lead_responsible_partner = self.env['crm.lead'].sudo().\
                    browse(int(val.get('res_id'))).mapped("user_id").mapped("partner_id")
                follower_domain = [
                    ('res_model', '=', 'crm.lead'),
                    ('res_id', '=', val.get('res_id'))
                ]
                if lead_responsible_partner:
                    follower_domain += [("partner_id", "not in", lead_responsible_partner.ids)]
                followers = self.env['mail.followers'].sudo().search(follower_domain)
                # val.update({'subtype_id': note_id})
                if followers:
                    followers.sudo().write({'subtype_ids': [(6,0, [note_id])]})
                # If we change Responsible
                if lead_responsible_partner:
                    main_followers = self.env['mail.followers'].sudo().search([
                        ('partner_id', 'in', lead_responsible_partner.ids),
                        ('res_model', '=', 'crm.lead'),
                        ('res_id', '=', val.get('res_id'))
                    ])
                    main_followers.sudo().write({'subtype_ids': [(6,0, [discussion_id])]})
        msg_record = super().create(vals)
        return msg_record
