# -*- coding: utf-8 -*-
import logging
import requests
import hashlib
import hmac
from odoo import _, api, fields, models, modules, SUPERUSER_ID, tools,osv
from odoo import http
import json
from odoo.exceptions import ValidationError
from odoo.http import request,Response
import base64
import time


class QuickBooksController(http.Controller):

    @http.route('/getaccess')
    def index(self, **kw):
        try:
            IrConfigParameter = request.env['ir.config_parameter'].sudo()
            client_id = IrConfigParameter.get_param('odoo_quickbook.quickbook_client_id')
            client_secret = IrConfigParameter.get_param('odoo_quickbook.quickbook_secret_key')
            redirect_uri = IrConfigParameter.get_param('odoo_quickbook.quickbook_redirect_url')
            select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
            combined_string = (client_id + ":" + client_secret)
            combined_string_byte = combined_string.encode("ascii")
            combined_string_base64_bytes = base64.b64encode(combined_string_byte)
            combined_string_base64_string = combined_string_base64_bytes.decode("ascii")
            if 'code' in kw:
                authorization_code = kw['code']
                realm_id = kw['realmId']
                header = {
                    'Accept': 'application/json',
                    'Authorization': 'Basic ' + combined_string_base64_string,
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Host': 'oauth.platform.intuit.com'
                }
                payload = {
                    'grant_type': 'authorization_code',
                    'code': authorization_code,
                    'redirect_uri': redirect_uri
                }
                token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer?"
                response = requests.request("POST", token_url, data=payload, headers=header)
                quickbook_response = json.loads(response.text)
                odoo_user = request.env['res.users'].sudo().search([('id', '=', request.env.user.id)])
                if response.status_code == 200:
                    odoo_user.refresh_token = quickbook_response['refresh_token']
                    odoo_user.access_token = quickbook_response['access_token']
                    odoo_user.quickbook_realm_id = realm_id
                    odoo_user.expires_in = int(round(time.time() * 1000))
                    odoo_user.select_url = select_url
                    request.env.cr.commit()
                    request.env['default.functions'].import_coa()
                    request.env['default.functions'].import_tax_agency()
                    request.env['default.functions'].import_taxes()
                    request.env['default.functions'].import_payment_terms()
                    request.env.cr.commit()
                    return request.render("OdooQuickBookConnector.token_redirect_success_page")
                else:
                    raise ValidationError(_("Please check your credentials and try again"))
        except Exception as e:
            raise ValidationError(_(str(e)))

    @http.route('/quickbook', auth='public', type='json')
    def eventchecker(self, **kw):
        try:
            IrConfigParameter = request.env['ir.config_parameter'].sudo()
            if IrConfigParameter.get_param('odoo_quickbook.webhook_check'):
                if 'HTTP_INTUIT_SIGNATURE' in request.httprequest.headers.environ:
                    webhookkey = IrConfigParameter.get_param('odoo_quickbook.quickbook_webhook_verifier_token')
                    if not webhookkey:
                        return Response(status=401)
                    hashed = hmac.new(bytes(webhookkey, 'utf8'), request.httprequest.data, hashlib.sha256)
                    generated_signature = base64.b64encode(hashed.digest()).decode('utf-8')
                    provided_signature = request.httprequest.headers.environ['HTTP_INTUIT_SIGNATURE']
                    if hmac.compare_digest(provided_signature, generated_signature):
                        # events[0]['dataChangeEvent']['entities'][0]['name']
                        events = request.jsonrequest['eventNotifications']
                        for full_event_list in events:
                            for event in full_event_list['dataChangeEvent']['entities']:
                                if event['name'] == 'Invoice':
                                    if event['operation'] == 'Update':
                                        pass
                                    if event['operation'] == 'Create':
                                        request.env['res.config.settings'].import_invoices(event['id'])
                                if event['name'] == 'Bill':
                                    if event['operation'] == 'Update':
                                        pass
                                    if event['operation'] == 'Create':
                                        request.env['res.config.settings'].import_bills(event['id'])
                                if event['name'] == 'PurchaseOrder':
                                    if event['operation'] == 'Update':
                                        request.env['res.config.settings'].update_purchase_order(event['id'])
                                    if event['operation'] == 'Create':
                                        request.env['res.config.settings'].import_purchase_order(event['id'])
                                if event['name'] == 'SalesReceipt':
                                    if event['operation'] == 'Update':
                                        request.env['res.config.settings'].update_sale_order(event['id'])
                                    if event['operation'] == 'Create':
                                        request.env['res.config.settings'].import_sale_order(event['id'])
                                if event['name'] == 'Customer':
                                    if event['operation'] == 'Update':
                                        request.env['res.config.settings'].update_customer(event['id'])
                                    if event['operation'] == 'Create':
                                        pass
                                        # request.env['res.config.settings'].import_customer(event['id'])
                                if event['name'] == 'Vendor':
                                    if event['operation'] == 'Update':
                                        request.env['res.config.settings'].update_vendor(event['id'])
                                    if event['operation'] == 'Create':
                                        # request.env['res.config.settings'].import_vendors(event['id'])
                                        pass
                                if event['name'] == 'Item':
                                    if event['operation'] == 'Update':
                                        pass
                                    if event['operation'] == 'Create':
                                        request.env['res.config.settings'].import_items(event['id'])
                                if event['name'] == 'Payment':
                                    if event['operation'] == 'Update':
                                        pass
                                    if event['operation'] == 'Create':
                                        request.env['res.config.settings'].import_payment(event['id'])
                                if event['name'] == 'BillPayment':
                                    if event['operation'] == 'Update':
                                        pass
                                    if event['operation'] == 'Create':
                                        request.env['res.config.settings'].import_vendor_payment(event['id'])
                                if event['name'] == 'CreditMemo':
                                    if event['operation'] == 'Update':
                                        pass
                                    if event['operation'] == 'Create':
                                        request.env['res.config.settings'].import_credit_memo(event['id'])
                                if event['name'] == 'VendorCredit':
                                    if event['operation'] == 'Update':
                                        pass
                                    if event['operation'] == 'Create':
                                        request.env['res.config.settings'].import_vendor_credit(event['id'])
                        return Response(status=200)
                    else:
                        return Response(status=401)
                else:
                    pass
            else:
                return Response(status=200)
        except Exception as e:
            raise ValidationError(_(str(e)))