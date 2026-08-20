# -*- coding: utf-8 -*-

import datetime
from collections import OrderedDict
from werkzeug.exceptions import NotFound
from odoo import http
from odoo import fields
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.portal.controllers.mail import PortalChatter
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalVendor(CustomerPortal):

    
    def get_domain_my_vendor_lead(self, user):
        if not request.env.is_admin():
            return [
                ('assigned_vendor_id', '=', user.id),
                ('type', '=', 'opportunity')
            ]
        else:
            return [
                ('type', '=', 'opportunity')
            ]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        VendorCrmLead = request.env['crm.lead']
        if 'vendor_lead_count' in counters:
            values['vendor_lead_count'] = (
                VendorCrmLead.search_count(self.get_domain_my_vendor_lead(request.env.user))
                if VendorCrmLead.check_access_rights('read', raise_exception=False)
                else 0
            )
        return values

    @http.route(['/vendor/leads', '/vendor/leads/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_vendor_leads(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        VendorCrmLead = request.env['crm.lead']
        domain = self.get_domain_my_vendor_lead(request.env.user)
        today = fields.Date.today()
        this_week_end_date = fields.Date.to_string(fields.Date.from_string(today) + datetime.timedelta(days=7))

        searchbar_filters = {
            'all': {'label': _('Active'), 'domain': []},
            'today': {'label': _('Today Activities'), 'domain': [('activity_date_deadline', '=', today)]},
            'week': {'label': _('This Week Activities'),
                     'domain': [('activity_date_deadline', '>=', today), ('activity_date_deadline', '<=', this_week_end_date)]},
            'overdue': {'label': _('Overdue Activities'), 'domain': [('activity_date_deadline', '<', today)]},
            'won': {'label': _('Won'), 'domain': [('stage_id.is_won', '=', True)]},
            'lost': {'label': _('Lost'), 'domain': [('active', '=', False), ('probability', '=', 0)]},
        }
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
            'probability': {'label': _('Probability'), 'order': 'probability desc'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
        }

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        if filterby == 'lost':
            VendorCrmLead = VendorCrmLead.with_context(active_test=False)

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        # pager: bypass activities access rights for search but still apply access rules
        leads_sudo = VendorCrmLead.sudo()._search(domain)
        domain = [('id', 'in', leads_sudo)]
        opp_count = VendorCrmLead.search_count(domain)
        pager = request.website.pager(
            url="/vendor/leads",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=opp_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager
        opportunities = VendorCrmLead.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'date': date_begin,
            'opportunities': opportunities,
            'page_name': 'vendor_leads',
            'default_url': '/vendor/leads',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("portal_vendor_leads.portal_my_vendor_leads", values)
    
    @http.route(['''/vendor/leads/<model('crm.lead', "[('type','=', 'opportunity')]"):opp>'''], type='http', auth="user", website=True)
    def portal_vendor_lead_details(self, opp, **kw):
        if opp.type != 'opportunity':
            raise NotFound()
        if not opp.assigned_vendor_id == request.env.user and not request.env.is_admin():
            raise NotFound()
        return request.render(
            "portal_vendor_leads.portal_my_vendor_leads_card", {
                'opportunity': opp,
                'user_activity': opp.sudo().activity_ids.filtered(lambda activity: activity.user_id == request.env.user)[:1],
                'stages': request.env['crm.stage'].search([
                    ('is_won', '!=', True), '|', ('team_id', '=', False), ('team_id', '=', opp.team_id.id)
                ], order='sequence desc, name desc, id desc'),
                'activity_types': request.env['mail.activity.type'].sudo().search(['|', ('res_model', '=', opp._name), ('res_model', '=', False)]),
                'states': request.env['res.country.state'].sudo().search([]),
                'countries': request.env['res.country'].sudo().search([]),
            })


class PortalVendorChatter(PortalChatter):

    @http.route('/mail/chatter_init', type='json', auth='public', website=True)
    def portal_chatter_init(self, res_model, res_id, domain=False, limit=False, **kwargs):
        data = super().portal_chatter_init(res_model, res_id, domain, limit, **kwargs)
        if res_model == 'crm.lead':
            request.session['chatter_model'] = True
            crmRecord = request.env['crm.lead'].sudo().browse(res_id)
            message_partner_ids = crmRecord.message_partner_ids
            if crmRecord and crmRecord.partner_id:
                message_partner_ids = message_partner_ids.filtered(lambda part : part.id != crmRecord.partner_id.id)
            data['options']['message_partner_ids'] = {partner.id: partner.name.replace(' ','_') for partner in message_partner_ids}
        return data
    
    def _portal_post_filter_params(self):
        fields = super()._portal_post_filter_params()
        if request.session.get('chatter_model',False):
            fields += ['lead_partners']
            del request.session['chatter_model']
        return fields
    