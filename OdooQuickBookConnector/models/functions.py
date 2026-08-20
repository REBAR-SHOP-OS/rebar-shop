import logging
import re
import xmltodict
from suds.client import Client
from odoo.exceptions import ValidationError, UserError
from odoo import _, api, fields, models, modules, SUPERUSER_ID, tools
from odoo.http import request, Response
import requests
import json
import base64
from datetime import datetime
import time
from datetime import timedelta
import base64

# Base64 string (truncated for readability)
base64_image = 'iVBORw0KGgoAAAANSUhEUgAAAFgAAABSCAIAAABfbIQFAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAHl0lEQVR4nO2bW5eaShqGKc6gYLet4qnbdsfOvsn//yW5mJmYdAwGBCRqe+BMzQUOi6WCQIP2XuNzpVhA8fJVfYcqwb/+8x35v+fvl7/wv1/+unY3rsy/v/1AEAS9djc+Cjch9tyE2HMTYs9NiD03IfbchNhzE2LPTYg9NyH23ITYcxNiz02IPTch9tyE2IOXfQMIoaZprutmOgvH8WazCQAoqVcn7ljq1SGE0+lUVdUc51qW1e/3L6ZFiUMDQijL8nw+z3f6fD6XZRlCWGyv4ijLIgJb0DQt95P4vj+bzTzPu4xdlGIREMLZbPYeFcLraJo2m80uYBfFCxHYQlFWHYyv6XRathYFCxH0+/22cHBNTdPKni+KFCKwBUVRCu8xhFBRlFLtIsNk6fs+hDChK6qq5vOUKe+uqiqGYa1WK64NAAAAgKJ53m4qIQzDWC6Xu93OcRzf90+2gRDatp2jB5lQFGWxWMQ5ERRFCYJgWfbu7o5hmExXPiOE7/uSJKmqejF/nozv+6ZpJrdZLpeyLLdarW63m946koSwbXsymby9vaXt5ochmFMMwxgMBiRJpjklSTBRFP+JKoS8vb2JopiycawQy+VyuVwW1KWrkf4pTgsRuO5Cu3Q1UgY1p4VwHOcCLuAy2LbtOM7ZZqeF8DzP87yiu3QdUj7Laa+RHDi9BwAAjuMEQeA4juM4giCO43ie5zhOmveWg5TPUnqFKgrHcc1mk6ZpkiQxDAuPe55n27ZhGPP5fL1eX7JLIRcSgiTJXq9Xr9dP/ophGMMwDMPc39/rui5JUknWkcAlhOB5/vHxkabpsy0BAI1Gg2VZURQ3m80F+hZSehWb5/mXl5c0KoSwLPv58+dqtVper44pVwiWZZ+enrKeBSG0LKtarebLI/NR7tB4enqiKCrTKbZt//r1a71el+e5TlKiEM1ms1KppG9vGIaqqrquXyXTLUsIHMcbjUbKxhDC+XwuSVLWdaACKUsImqZTDgrP8xRFOS5VAwAIgqAoiqIokiSD6Mt1XdM0bdu2LKtYF1uWEAzDREOmODzPE0VR1/WD4yzLCoJQqVQIgjieMoNIdLPZzGYzy7IK6XBZQrAse7ZNsPxxoAJJkoIgJC98YhiGYRhN0/V6XVEUTdPebx1lCUEQxNk2iqIoihI9UqvV+v1++qADRdF2u83zvCiK2+02T0f/R1lCnF2k2+120VIoAKBarQ6Hw5MDStf1sCzAcVw01gIAVCqV0Wj0/fv39wSjZQkRV+wOmc1mUXuu1WrD4TAugtI0LXzhvV7vOOjEcfz5+Xk8Hp8t7cZRVuiWXNfZbDaLxSL8ShBEr9d7ZxxJUdTLy0vgXHJQlhAJI9b3/d+/f4dfAQCZ5oUESJJMWP5JpiwhTNOMm8kNwzAMI/zKcVxcep6DRqORz7JKFCJuuG6323AGCfLuAu9LEES73c5xYllC+L4vy/LJn7bbbegsSJLMlI+kodVq5TCKEvPc9Xp9spS+2+3CzxRFpYk4MoFhWI5aRrlpuCzLLMtG33lQawi/siwbjTjOOt3gCnHNQkNgGCbrGl25QjiO8/r6OhqNQqfgum7URqLOwrKsr1+/nr2mJEmSJB0fpyjqy5cvweeU651RSi8BWZb17du3MGo4SLRzu/1k0uR7B1yiFmbb9uvr62QysSzrONcu6aZZr3yhcn5QelmtVgdZaUmVGM/zspa5LrrA4zjOarWKHonGGiRJhoP8gB8/foS+pt1unww9oiYQDfBTmsZpIXLvRMpKEFMEfQUAxBW1og+DYdjZ2lc0ckVRNM2UcfppcRzPMd/koPCKG4IgEMJoPo5hWJpQ5bQQBEFk3YyVD8dxom+vEFRVjQYatVotjXXHtsgXsWfF9/1id6S4rhuteiVvR4wSKwTDMN1u9wK7wVer1cEM+h50XY+OtYeHh5ShSpLNCIKQO73PhCiKhRSjbduO7njFcfzh4SHluUlCoCja7/c/ffpUqVRKnTsty5JlOU2ikYDjOOPxOOo4eZ5PP9OdN5u7uzuO44JqimmaRYVAvu+v1+twU8+fP3983x8MBicV53k+dJkna1mu604mk+i8i+N4pqGdavwEiW3h6/SyLId77iGEQT7y+Ph47O263W7CdSzLikZcCIKgKPr8/Jxp/fmikeUB7XbbcZz5fB6Gw4vFwjRNQRDq9Xqal+n7/nw+V1X1YIoRBIHn+UyduaYQQdnWcZzonlDDMH7+/KmqalC2DzbcH5wY7BgINtYel8sbjUan0/mgSVccKIoOBgOCIHRdj06Wu91uPB5TFMWyLE3TBEFgGAYh9DzPdV3DMHa73bGjAQC02+0cKiBXFwJBEBzHHx8fKYqaTqfR4xDCsAIcPlhCTolh2HA45Hk+X+xzfSEQBAEACILAcZwsy6vV6vhpk3NqDMNqtZogCGlWnuP4EEIEsCw7HA5N05QkKWWsCQCo1WqdToem6Xemyx9ICARBUBRlWXY0GpmmuVgsNpuN4ziu6wb/okIQBACAYViwa5fjuPv7+6x7tOL4WEKE0DTd6XR83w92UodCoCgaalFsHvRBhQhAUTT4m9Yl7nWBe/wjuAmx5ybEnv8CxpHvO7f8QxwAAAAASUVORK5CYII='

image_data = base64.b64decode(base64_image)

_logger = logging.getLogger(__name__)
_image_dataurl = re.compile(r'(data:image/[a-z]+?);base64,([a-z0-9+/]{3,}=*)([\'"])', re.I)


class defaultfunctions(models.Model):
    _name = 'default.functions'
    _description = 'Default functions'

    select_url = fields.Selection([
        ('https://sandbox-quickbooks.api.intuit.com/', 'https://sandbox-quickbooks.api.intuit.com/'),
        ('https://quickbooks.api.intuit.com/', 'https://quickbooks.api.intuit.com/')], string='Select Account',
        compute='_compute_url')

    def _compute_url(self):
        IrConfigParameter = request.env['ir.config_parameter'].sudo()
        self.select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')

    def check_refreshtoken(self):
        try:
            user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
            if user.expires_in:
                expires_in = datetime.fromtimestamp(int(user.expires_in) / 1e3)
                expires_in = expires_in + timedelta(seconds=3600)
                nowDateTime = datetime.now()
                if nowDateTime > expires_in:
                    self.generate_refresh_token()
        except Exception as e:
            raise ValidationError(_(str(e)))

    def generate_refresh_token(self):
        try:
            user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
            if user.refresh_token:
                IrConfigParameter = self.env['ir.config_parameter'].sudo()
                if not IrConfigParameter.get_param(
                        'odoo_quickbook.quickbook_client_id') or not IrConfigParameter.get_param(
                    'odoo_quickbook.quickbook_redirect_url') or not IrConfigParameter.get_param(
                    'odoo_quickbook.quickbook_secret_key'):
                    raise ValidationError("Error! Please enter Quickbooks credentials")
                else:
                    combined_string = (IrConfigParameter.get_param(
                        'odoo_quickbook.quickbook_client_id') + ":" + IrConfigParameter.get_param(
                        'odoo_quickbook.quickbook_secret_key'))
                    combined_string_byte = combined_string.encode("ascii")
                    combined_string_base64_bytes = base64.b64encode(combined_string_byte)
                    combined_string_base64_string = combined_string_base64_bytes.decode("ascii")
                    header = {
                        'Accept': 'application/json',
                        'authorization': "Basic " + combined_string_base64_string,
                        'Content-Type': 'application/x-www-form-urlencoded',
                    }
                    payload = {
                        'grant_type': 'refresh_token',
                        'refresh_token': user.refresh_token
                    }
                    token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer?"
                    response = requests.request("POST", token_url, data=payload, headers=header)
                    if response.status_code == 200:
                        quickbook_refresh_access_response = json.loads(response.text)
                        if 'access_token' not in quickbook_refresh_access_response:
                            raise ValidationError(('Refresh token not fetched.\nPLEASE CROSSCHECK YOUR CREDIENTIALS'))
                        else:
                            user.access_token = quickbook_refresh_access_response['access_token']
                            user.refresh_token = quickbook_refresh_access_response['refresh_token']
                            user.expires_in = int(round(time.time() * 1000))
                            self.env.cr.commit()
                            _logger.info(
                                "Successfully generated credentials for " + user.name + ' at ' + str(datetime.now()))
                    else:
                        _logger.info(
                            "Unsuccessful attempt to fetch token for " + user.name + ' at ' + str(datetime.now()))
        except Exception as e:
            raise ValidationError(_(str(e)))

    def import_coa(self):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].sudo().browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            start_position = 1
            max_results = 100
            has_more = True
            while has_more:
                response = requests.get(url=str(
                    user.select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from Account STARTPOSITION ' + str(
                    start_position) + " MAXRESULTS " + str(max_results) + '&minorversion=62', headers={
                    'Accept': 'application/json',
                    'Authorization': 'Bearer ' + user.access_token
                })
                if response.status_code != 200:
                    _logger.info(response.text)
                    break
                quickbook_coa_response = json.loads(response.text)
                if not quickbook_coa_response['QueryResponse'].get('Account'):
                    break
                if response.status_code == 200:
                    # query?query = select *from Customer & minorversion = 62
                    # /reports/AccountList?
                    quickbook_coa_response = json.loads(response.text)
                    for quickbookcoa in quickbook_coa_response['QueryResponse']['Account']:
                        coa_setting_id = False
                        account_redundecy_check = self.env['coa.settings'].search(
                            [('account_id', '=', quickbookcoa['Id'])])
                        currency = self.env['res.currency'].search(
                            [('name', '=', quickbookcoa['CurrencyRef']['value'])]).id
                        if not account_redundecy_check:

                            coa_setting_id = self.env['coa.settings'].sudo().create({
                                'name': quickbookcoa['Name'],
                                'account_id': quickbookcoa['Id'],
                                'status': quickbookcoa['Active'],
                                'quickbook_account_classification': quickbookcoa['Classification'],
                                'currency_id': currency,
                                'description': quickbookcoa['FullyQualifiedName'],
                            })
                            self.env.cr.commit()
                            _logger.info(
                                "Successfully Created Account : " + quickbookcoa['Name'] + " with Account ID: " +
                                quickbookcoa['Id'])

                            self.env['account.account'].sudo().create({
                                'name': coa_setting_id.name,
                                'code': coa_setting_id.account_id,
                                'coa_id': coa_setting_id.id,
                                'currency_id': currency,
                            })
                            self.env.cr.commit()
                            _logger.info(
                                "Successfully Created Account in account.account: " + quickbookcoa[
                                    'Name'] + " with Quickbook Account ID: " +
                                quickbookcoa['Id'])
                        else:
                            _logger.info(
                                "Account already exists in account.account: " + quickbookcoa[
                                    'Name'] + " with Quickbook Account ID: " +
                                quickbookcoa['Id'])
                    start_position += max_results
                else:
                    _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_tax_agency(self):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].sudo().browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            response = requests.get(url=str(
                user.select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from TaxAgency&minorversion=62',
                                    headers={
                                        'Accept': 'application/json',
                                        'Authorization': 'Bearer ' + user.access_token
                                    })
            if response.status_code == 200:
                quickbook_tax_agencies_response = json.loads(response.text)
                for quickbook_tax_agency in quickbook_tax_agencies_response['QueryResponse']['TaxAgency']:
                    agency_redundancy_check = self.env['taxagency.settings'].sudo().search(
                        [('agency_id', '=', quickbook_tax_agency['Id'])])
                    if agency_redundancy_check:
                        pass
                    else:
                        self.env['taxagency.settings'].create({
                            'name': quickbook_tax_agency['DisplayName'],
                            'Tax_tracked_on_sales': quickbook_tax_agency['TaxTrackedOnSales'],
                            'Tax_tracked_on_purchase': quickbook_tax_agency['TaxTrackedOnPurchases'],
                            'agency_id': quickbook_tax_agency['Id'],
                        })
                        self.env.cr.commit()
                        _logger.info("Successfully Created Tax Agency: " + quickbook_tax_agency['DisplayName'])
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_taxes(self):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].sudo().browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            response = requests.get(url=str(
                user.select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from TaxRate&minorversion=62',
                                    headers={
                                        'Accept': 'application/json',
                                        'Authorization': 'Bearer ' + user.access_token
                                    })
            if response.status_code == 200:
                quickbook_tax_rates_response = json.loads(response.text)
                for quickbook_tax_rate in quickbook_tax_rates_response['QueryResponse']['TaxRate']:
                    tax_redundancy_check = self.env['taxes.settings'].sudo().search(
                        [('tax_id', '=', quickbook_tax_rate['Id'])])
                    if tax_redundancy_check:
                        pass
                    else:
                        agency_id = self.env['taxagency.settings'].sudo().search(
                            [('agency_id', '=', quickbook_tax_rate['AgencyRef']['value'])])
                        self.env['taxes.settings'].create({
                            'tax_type': quickbook_tax_rate['Description'],
                            'name': quickbook_tax_rate['Name'],
                            'effective_rate': quickbook_tax_rate[
                                'RateValue'] if 'RateValue' in quickbook_tax_rate else None,
                            'status': quickbook_tax_rate['Active'],
                            'tax_id': quickbook_tax_rate['Id'],
                            'tax_agency_id': agency_id.id,
                        })
                        self.env.cr.commit()
                        _logger.info("Successfully Created Tax Agency: " + quickbook_tax_rate['Name'])

            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_payment_terms(self):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].sudo().browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            response = requests.get(url=str(
                user.select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from term&minorversion=62',
                                    headers={
                                        'Accept': 'application/json',
                                        'Authorization': 'Bearer ' + user.access_token
                                    })
            if response.status_code == 200:
                quickbook_terms_response = json.loads(response.text)
                for quickbook_term in quickbook_terms_response['QueryResponse']['Term']:
                    term_redundancy_check = self.env['account.payment.term'].sudo().search(
                        [('quickbook_payment_term_id', '=', quickbook_term['Id'])])
                    if term_redundancy_check:
                        pass
                    else:
                        payment_term_id = self.env['account.payment.term'].create({
                            'name': quickbook_term['Name'],
                            'active': quickbook_term['Active'],
                            'quickbook_payment_term_id': quickbook_term['Id'],
                        })
                        for line in payment_term_id.line_ids:
                            line.unlink()
                        self.env['account.payment.term.line'].create({
                            'nb_days': quickbook_term['DueDays'],
                            'value': 'fixed',
                            'delay_type': 'days_after',
                            'payment_id': payment_term_id.id
                        })
                        self.env.cr.commit()
                        _logger.info("Successfully Created Payment Term : " + quickbook_term['Name'])
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def checkquickbookredundency(self, endpoint, filter, filter_value):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].sudo().browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            baseUrl = str(
                user.select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from " + endpoint + " where " + filter + "= '" + str(
                filter_value) + "'&minorversion=62"
            header = {
                'Authorization': "Bearer " + user.access_token,
                'Accept': 'application/json'
            }

            response = requests.request('GET', url=baseUrl, headers=header)
            if response.status_code == 200:
                quickbook_response = json.loads(response.text)
                return quickbook_response
            else:
                message = _(
                    "Failed to fetch data from QuickBooks: %s" % response.text
                )
                _logger.error(message)
                raise ValidationError(message)
        except Exception as e:
            raise ValidationError(str(e))

    def getinvoicelinesitem(self, line_ids, flag, move_type=None):
        #flag 0 indicates invoices and 1 indicate purchase orders 2 indicate sale order
        try:
            lineitems = []
            for id in line_ids:
                if id['product_id']['product_tmpl_id'].quickbook_product_id:
                    pass
                if not id['product_id']['product_tmpl_id'].quickbook_product_id:
                    result = self.env['default.functions'].checkquickbookredundency(
                        "item", "FullyQualifiedName", id['product_id']['product_tmpl_id'].name
                    )
                    if result and 'Item' in result.get('QueryResponse', {}):
                        id['product_id']['product_tmpl_id'].write({
                            'quickbook_product_id': result['QueryResponse']['Item'][0]['Id']
                        })
                        self.env.cr.commit()
                    else:
                        _logger.warning(
                            "Item %s not found in QuickBooks; exporting", id['product_id']['product_tmpl_id'].name
                        )
                        self.env['product.template'].export_items(id['product_id']['product_tmpl_id'])
                if flag == 0:
                    if move_type == 'out_invoice':
                        data = {
                            "DetailType": "SalesItemLineDetail",
                            "Amount": id.quantity * id.price_unit,
                            "SalesItemLineDetail": {
                                "ItemRef": {
                                    "name": id['product_id']['product_tmpl_id'].name,
                                    "value": id['product_id']['product_tmpl_id'].quickbook_product_id
                                },
                                "TaxCodeRef": {
                                    "value": "TAX"
                                },
                                "Qty": id.quantity,
                                "UnitPrice": id.price_unit,
                            }
                        }
                    if move_type == 'out_refund':
                        data = {
                            "DetailType": "SalesItemLineDetail",
                            "Amount": id.quantity * id.price_unit,
                            "SalesItemLineDetail": {
                                "ItemRef": {
                                    "name": id['product_id']['product_tmpl_id'].name,
                                    "value": id['product_id']['product_tmpl_id'].quickbook_product_id
                                },
                                "TaxCodeRef": {
                                    "value": "NON"
                                },
                                "Qty": id.quantity,
                                "UnitPrice": id.price_unit,
                            }
                        }
                    if move_type == 'in_invoice':
                        if id['product_id']['product_tmpl_id'].type == 'service':
                            data = {
                                "Description": id.name if id.name else None,
                                "DetailType": "AccountBasedExpenseLineDetail",
                                "Amount": id.quantity * id.price_unit,
                                "AccountBasedExpenseLineDetail": {
                                    "AccountRef": {
                                        "value": id['account_id']['coa_id']['account_id'] if id['account_id']['coa_id'][
                                            'account_id'] else '7'
                                    },
                                    "TaxCodeRef": {
                                        "value": "NON"
                                    },
                                }
                            }
                        else:
                            data = {
                                "Description": id.name if id.name else None,
                                "DetailType": "ItemBasedExpenseLineDetail",
                                "Amount": id.quantity * id.price_unit,
                                "ItemBasedExpenseLineDetail": {
                                    "ItemRef": {
                                        "name": id['product_id']['product_tmpl_id'].name,
                                        "value": id['product_id']['product_tmpl_id'].quickbook_product_id
                                    },
                                    "TaxCodeRef": {
                                        "value": "NON"
                                    },
                                    "Qty": id.quantity,
                                    "UnitPrice": id.price_unit,
                                }
                            }
                    if move_type == 'in_refund':
                        if id['product_id']['product_tmpl_id'].type == 'service':
                            data = {
                                "Description": id.name if id.name else None,
                                "DetailType": "AccountBasedExpenseLineDetail",
                                "Amount": id.quantity * id.price_unit,
                                "AccountBasedExpenseLineDetail": {
                                    "AccountRef": {
                                        "value": id['account_id']['coa_id']['account_id'] if id['account_id']['coa_id'][
                                            'account_id'] else '7'
                                    },
                                    "TaxCodeRef": {
                                        "value": "NON"
                                    },
                                }
                            }
                        else:
                            data = {
                                "Description": id.name if id.name else None,
                                "DetailType": "ItemBasedExpenseLineDetail",
                                "Amount": id.quantity * id.price_unit,
                                "ItemBasedExpenseLineDetail": {
                                    "ItemRef": {
                                        "name": id['product_id']['product_tmpl_id'].name,
                                        "value": id['product_id']['product_tmpl_id'].quickbook_product_id
                                    },
                                    "TaxCodeRef": {
                                        "value": "NON"
                                    },
                                    "Qty": id.quantity,
                                    "UnitPrice": id.price_unit,
                                }
                            }
                elif flag == 1:
                    data = {
                        "Description": id.name if id.name else None,
                        "DetailType": "ItemBasedExpenseLineDetail",
                        "Amount": id.quantity * id.price_unit,
                        "ItemBasedExpenseLineDetail": {
                            "ItemRef": {
                                "name": id['product_id']['product_tmpl_id'].name,
                                "value": id['product_id']['product_tmpl_id'].quickbook_product_id
                            },
                            "TaxCodeRef": {
                                "value": "NON"
                            },
                            "Qty": id.product_qty,
                            "UnitPrice": id.price_unit,
                        }
                    }
                elif flag == 2:
                    data = {
                        "Description": id.name if id.name else None,
                        "DetailType": "SalesItemLineDetail",
                        "Amount": id.quantity * id.price_unit,
                        "SalesItemLineDetail": {
                            "ItemRef": {
                                "name": id['product_id']['product_tmpl_id'].name,
                                "value": id['product_id']['product_tmpl_id'].quickbook_product_id
                            },
                            "TaxCodeRef": {
                                "value": "TAX"
                            },
                            "Qty": id.product_uom_qty,
                            "UnitPrice": id.price_unit,
                        }
                    }
                lineitems.append(data)
            if (flag == 0 and (move_type == 'out_invoice' or move_type == 'out_refund')) or flag == 2:
                for discont_id in line_ids:
                    if 'discount' in discont_id:
                        if discont_id.discount > 0.0:
                            dicount = {
                                "DetailType": "DiscountLineDetail",
                                # "Amount": 15,
                                "DiscountLineDetail": {
                                    'PercentBased': True,
                                    'DiscountPercent': discont_id.discount
                                }
                            }
                            lineitems.append(dicount)
                            break
            return lineitems
        except Exception as e:
            raise ValidationError(_(str(e)))


class QuickbookSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    quickbook_redirect_url = fields.Char('Redirect URL', compute='_compute_redirect_url',
                                         config_parameter="odoo_quickbook.quickbook_redirect_url")
    quickbook_client_id = fields.Char('Client ID', required=True, config_parameter="odoo_quickbook.quickbook_client_id")
    quickbook_secret_key = fields.Char('Client Secret', required=True,
                                       config_parameter="odoo_quickbook.quickbook_secret_key")
    login_url = fields.Char('Login URL', compute='_compute_url', readonly=True)
    bill_check = fields.Boolean("Bill", config_parameter="odoo_quickbook.bill_check")
    sale_order_check = fields.Boolean("Sale Order", config_parameter="odoo_quickbook.sale_order_check")
    purchase_order_check = fields.Boolean("Purchase Order", config_parameter="odoo_quickbook.purchase_order_check")
    item_check = fields.Boolean("Items", config_parameter="odoo_quickbook.item_check")
    customer_check = fields.Boolean("Customer", config_parameter="odoo_quickbook.customer_check")
    vendor_check = fields.Boolean("Vendor", config_parameter="odoo_quickbook.vendor_check")
    invoice_check = fields.Boolean("Invoices", config_parameter="odoo_quickbook.invoice_check")
    credit_memo_check = fields.Boolean("Credit Notes", config_parameter="odoo_quickbook.credit_memo_check")
    vendor_refund_check = fields.Boolean("Vendor Refund", config_parameter="odoo_quickbook.vendor_refund_check")
    payment_method_check = fields.Boolean("Payment Method", config_parameter="odoo_quickbook.payment_method_check")
    reconcile_check = fields.Boolean("Reconcile", config_parameter="odoo_quickbook.reconcile_check")
    customer_payment_check = fields.Boolean("Customer Payment",
                                            config_parameter="odoo_quickbook.customer_payment_check")
    vendor_bill_payment = fields.Boolean("Vendor Bill Payment", config_parameter="odoo_quickbook.vendor_bill_payment")
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    date_filter = fields.Boolean("Date Filter", config_parameter="odoo_quickbook.date_filter")
    webhook_check = fields.Boolean("Webhook Check")
    select_url = fields.Selection([
        ('https://sandbox-quickbooks.api.intuit.com/', 'https://sandbox-quickbooks.api.intuit.com/'),
        ('https://quickbooks.api.intuit.com/', 'https://quickbooks.api.intuit.com/')], string='Select Account',
        config_parameter='odoo_quickbook.select_url', default='https://sandbox-quickbooks.api.intuit.com/')

    def set_values(self):
        res = super(QuickbookSetting, self).set_values()
        self.env['ir.config_parameter'].set_param('odoo_quickbook.from_date', self.from_date)
        self.env['ir.config_parameter'].set_param('odoo_quickbook.to_date', self.to_date)

    @api.model
    def get_values(self):
        res = super(QuickbookSetting, self).get_values()
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        from_date = IrConfigParameter.get_param('odoo_quickbook.from_date', self.from_date)
        to_date = IrConfigParameter.get_param('odoo_quickbook.to_date', self.to_date)
        res.update(
            from_date=from_date if from_date else None,
            to_date=to_date if to_date else None,
        )
        return res

    @api.depends('quickbook_redirect_url', 'quickbook_client_id')
    def _compute_url(self):
        IrConfigParameter = request.env['ir.config_parameter'].sudo()
        redirect_url = IrConfigParameter.get_param('odoo_quickbook.quickbook_redirect_url')
        client_id = IrConfigParameter.get_param('odoo_quickbook.quickbook_client_id')
        scope = 'com.intuit.quickbooks.accounting'
        self.login_url = 'https://appcenter.intuit.com/connect/oauth2?client_id=' + client_id + '&response_type=code&scope=' + scope + '&redirect_uri=' + redirect_url + '&state=' + redirect_url + ''

    @api.depends('quickbook_redirect_url', 'quickbook_client_id')
    def _compute_redirect_url(self):
        base_url = request.httprequest.url_root + 'getaccess'
        self.quickbook_redirect_url = base_url
        # self.quickbook_redirect_url = 'https://962e-154-57-217-90.ngrok-free.app/getaccess'

    def authorization(self):
        return {
            'name': 'Go to website',
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.login_url,
        }

    def import_customer(self, id=None):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have Quickbooks credentials!\nPlease specify the credentials in settings.")
                    raise ValidationError(
                        ("No user have Quickbooks credentials!\nPlease specify the credentials in settings."))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            start_position = 1
            max_results = 100

            while True:
                if id:
                    url_used = request.env['ir.config_parameter'].sudo().get_param('odoo_quickbook.select_url')
                    url = str(
                        url_used) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from Customer where Id='" + str(
                        id) + "'&minorversion=62"
                else:
                    IrConfigParameter = request.env['ir.config_parameter'].sudo()
                    select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                    url = str(
                        select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from Customer STARTPOSITION " + str(
                        start_position) + " MAXRESULTS " + str(max_results) + "&minorversion=62"
                response = requests.get(url=url, headers={
                    'Accept': 'application/json',
                    'Authorization': 'Bearer ' + user.access_token
                })
                if response.status_code != 200:
                    _logger.info(response.text)
                    break
                quickbook_customers = json.loads(response.text)
                if not quickbook_customers['QueryResponse'].get('Customer'):
                    break
                if response.status_code == 200:
                    quickbook_customers = json.loads(response.text)
                    for quickbook_customer in quickbook_customers['QueryResponse']['Customer']:
                        contact_parent_id = ""
                        contact_redundancy_check = self.env['res.partner'].sudo().search(
                            [('quickbook_contact_id', '=', quickbook_customer['Id'])])
                        if contact_redundancy_check:
                            pass
                        else:
                            if quickbook_customer['DisplayName'] == 'Administrator':
                                contact = self.env['res.partner'].sudo().search([('name', '=', 'Administrator')])
                                if contact:
                                    contact.write({
                                        'quickbook_contact_id': quickbook_customer['Id'],
                                    })
                                    self.env.cr.commit()
                            else:
                                if "ParentRef" in quickbook_customer:
                                    contact_parent_id = self.env['res.partner'].sudo().search(
                                        [('quickbook_contact_id', '=', quickbook_customer['ParentRef']['value'])]).id
                                partner_id = self.env['res.partner'].sudo().create({
                                    'quickbook_contact_id': quickbook_customer['Id'],
                                    'active': quickbook_customer['Active'],
                                    'phone': quickbook_customer['PrimaryPhone'][
                                        'FreeFormNumber'] if 'PrimaryPhone' in quickbook_customer else None,
                                    # 'mobile': mobile_number,
                                    'name': quickbook_customer['DisplayName'],
                                    'email': quickbook_customer['PrimaryEmailAddr'][
                                        'Address'] if 'PrimaryEmailAddr' in quickbook_customer else None,
                                    'parent_id': contact_parent_id if contact_parent_id else None,
                                    'customer_rank': 1,
                                })
                                if "BillAddr" in quickbook_customer:
                                    country_id = ''
                                    state_id = ''
                                    if 'Country' in quickbook_customer["BillAddr"]:
                                        country_id = self.env['res.country'].sudo().search(
                                            [('name', '=', quickbook_customer["BillAddr"]['Country'])]).id
                                    if "CountrySubDivisionCode" in quickbook_customer["BillAddr"]:
                                        state_id = self.env['res.country.state'].sudo().search(
                                            [('code', '=', quickbook_customer["BillAddr"]["CountrySubDivisionCode"]),
                                             ('country_id', '=', country_id)]).id
                                    self.env['res.partner'].sudo().create({
                                        'city': quickbook_customer["BillAddr"]["City"] if "City" in quickbook_customer[
                                            "BillAddr"] else None,
                                        'street': quickbook_customer["BillAddr"]['Line1'] if "Line1" in
                                                                                             quickbook_customer[
                                                                                                 "BillAddr"] else None,
                                        'street2': quickbook_customer["BillAddr"]['Line2'] if "Line2" in
                                                                                              quickbook_customer[
                                                                                                  "BillAddr"] else None,
                                        'country_id': country_id if country_id else None,
                                        'type': 'invoice',
                                        'state_id': state_id if state_id else None,
                                        'zip': quickbook_customer["BillAddr"]["PostalCode"] if "PostalCode" in
                                                                                               quickbook_customer[
                                                                                                   "BillAddr"] else None,
                                        'parent_id': partner_id.id
                                    })
                                if "ShipAddr" in quickbook_customer:
                                    country_id = ''
                                    state_id = ''
                                    if 'Country' in quickbook_customer["ShipAddr"]:
                                        country_id = self.env['res.country'].sudo().search(
                                            [('name', '=', quickbook_customer["ShipAddr"]['Country'])]).id
                                    if "CountrySubDivisionCode" in quickbook_customer["ShipAddr"]:
                                        state_id = self.env['res.country.state'].sudo().search(
                                            [('name', '=', quickbook_customer["ShipAddr"]["CountrySubDivisionCode"]),
                                             ('country_id', '=', country_id)]).id
                                    self.env['res.partner'].sudo().create({
                                        'city': quickbook_customer["ShipAddr"]["City"] if "City" in quickbook_customer[
                                            "ShipAddr"] else None,
                                        'street': quickbook_customer["ShipAddr"]['Line1'] if "Line1" in
                                                                                             quickbook_customer[
                                                                                                 "ShipAddr"] else None,
                                        'street2': quickbook_customer["ShipAddr"]['Line2'] if "Line2" in
                                                                                              quickbook_customer[
                                                                                                  "ShipAddr"] else None,
                                        'country_id': country_id if country_id else None,
                                        'type': 'delivery',
                                        'state_id': state_id if state_id else None,
                                        'zip': quickbook_customer["ShipAddr"]["PostalCode"] if "PostalCode" in
                                                                                               quickbook_customer[
                                                                                                   "ShipAddr"] else None,
                                        'parent_id': partner_id.id
                                    })
                                self.env.cr.commit()
                                _logger.info("successfully Created : " + quickbook_customer[
                                    'DisplayName'] + " with Contact ID: " + quickbook_customer['Id'])
                    start_position += max_results
                    print('==================', start_position)
                else:
                    _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_vendors(self, id=None):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            start_position = 1
            max_results = 100
            while True:
                if id:
                    url_used = request.env['ir.config_parameter'].sudo().get_param('odoo_quickbook.select_url')
                    url = str(
                        url_used) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from Vendor where Id='" + str(
                        id) + "'&minorversion=62"
                else:
                    IrConfigParameter = request.env['ir.config_parameter'].sudo()
                    select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                    url = str(
                        select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from Vendor STARTPOSITION " + str(
                        start_position) + " MAXRESULTS " + str(max_results) + "&minorversion=62"
                response = requests.get(url=url, headers={
                    'Accept': 'application/json',
                    'Authorization': 'Bearer ' + user.access_token
                })
                if response.status_code != 200:
                    _logger.info(response.text)
                    break
                quickbook_customers = json.loads(response.text)
                if not quickbook_customers['QueryResponse'].get('Vendor'):
                    break
                if response.status_code == 200:
                    quickbook_vendors = json.loads(response.text)
                    for quickbook_vendor in quickbook_vendors['QueryResponse']['Vendor']:
                        contact_parent_id = ""
                        contact_redundancy_check = self.env['res.partner'].sudo().search(
                            [('quickbook_contact_id', '=', quickbook_vendor['Id'])])
                        if contact_redundancy_check:
                            pass
                        else:
                            if quickbook_vendor['DisplayName'] == 'Administrator':
                                contact = self.env['res.partner'].sudo().search([('name', '=', 'Administrator')])
                                if contact:
                                    contact.write({
                                        'quickbook_contact_id': quickbook_vendor['Id'],
                                    })
                                    self.env.cr.commit()
                            else:
                                if "ParentRef" in quickbook_vendor:
                                    contact_parent_id = self.env['res.partner'].sudo().search(
                                        [('quickbook_contact_id', '=', quickbook_vendor['ParentRef']['value'])]).id
                                partner_id = self.env['res.partner'].sudo().create({
                                    'quickbook_contact_id': quickbook_vendor['Id'],
                                    'active': quickbook_vendor['Active'],
                                    'phone': quickbook_vendor['PrimaryPhone'][
                                        'FreeFormNumber'] if 'PrimaryPhone' in quickbook_vendor else None,
                                    # 'mobile': mobile_number,
                                    'name': quickbook_vendor['DisplayName'],
                                    'email': quickbook_vendor['PrimaryEmailAddr'][
                                        'Address'] if 'PrimaryEmailAddr' in quickbook_vendor else None,
                                    'parent_id': contact_parent_id if contact_parent_id else None,
                                    'supplier_rank': 1,
                                })
                                if "BillAddr" in quickbook_vendor:
                                    country_id = ''
                                    state_id = ''
                                    if 'Country' in quickbook_vendor["BillAddr"]:
                                        country_id = self.env['res.country'].sudo().search(
                                            [('name', '=', quickbook_vendor["BillAddr"]['Country'])]).id
                                    if "CountrySubDivisionCode" in quickbook_vendor["BillAddr"]:
                                        state_id = self.env['res.country.state'].sudo().search(
                                            [('code', '=', quickbook_vendor["BillAddr"]["CountrySubDivisionCode"]),
                                             ('country_id', '=', country_id)]).id
                                    self.env['res.partner'].sudo().create({
                                        'city': quickbook_vendor["BillAddr"]["City"] if "City" in quickbook_vendor[
                                            "BillAddr"] else None,
                                        'street': quickbook_vendor["BillAddr"]['Line1'] if "Line1" in quickbook_vendor[
                                            "BillAddr"] else None,
                                        'street2': quickbook_vendor["BillAddr"]['Line2'] if "Line2" in quickbook_vendor[
                                            "BillAddr"] else None,
                                        'country_id': country_id if country_id else None,
                                        'type': 'invoice',
                                        'state_id': state_id if state_id else None,
                                        'zip': quickbook_vendor["BillAddr"]["PostalCode"] if "PostalCode" in
                                                                                             quickbook_vendor[
                                                                                                 "BillAddr"] else None,
                                        'parent_id': partner_id.id
                                    })
                                if "ShipAddr" in quickbook_vendor:
                                    country_id = ''
                                    state_id = ''
                                    if 'Country' in quickbook_vendor["ShipAddr"]:
                                        country_id = self.env['res.country'].sudo().search(
                                            [('name', '=', quickbook_vendor["ShipAddr"]['Country'])]).id
                                    if "CountrySubDivisionCode" in quickbook_vendor["ShipAddr"]:
                                        state_id = self.env['res.country.state'].sudo().search(
                                            [('name', '=', quickbook_vendor["ShipAddr"]["CountrySubDivisionCode"]),
                                             ('country_id', '=', country_id)]).id
                                    self.env['res.partner'].sudo().create({
                                        'city': quickbook_vendor["ShipAddr"]["City"] if "City" in quickbook_vendor[
                                            "ShipAddr"] else None,
                                        'street': quickbook_vendor["ShipAddr"]['Line1'] if "Line1" in quickbook_vendor[
                                            "ShipAddr"] else None,
                                        'street2': quickbook_vendor["ShipAddr"]['Line2'] if "Line2" in quickbook_vendor[
                                            "ShipAddr"] else None,
                                        'country_id': country_id if country_id else None,
                                        'type': 'delivery',
                                        'state_id': state_id if state_id else None,
                                        'zip': quickbook_vendor["ShipAddr"]["PostalCode"] if "PostalCode" in
                                                                                             quickbook_vendor[
                                                                                                 "ShipAddr"] else None,
                                        'parent_id': partner_id.id
                                    })
                                self.env.cr.commit()
                                _logger.info(
                                    "successfully Created : " + quickbook_vendor['DisplayName'] + " with Contact ID: " +
                                    quickbook_vendor['Id'])
                    start_position += max_results
                    print('==================', start_position)
                else:
                    _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_items(self, id=None):
        try:
            odoo_expense_account = ''
            odoo_type = ''
            odoo_income_account = ''
            odoo_inventory_account = ''
            ExpenseAccountRef = ''
            IncomeAccountRef = ''
            AssetAccountRef = ''
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have Quickbooks credentials!\nPlease specify the credentials in settings.")
                    raise ValidationError(
                        ("No user have Quickbooks credentials!\nPlease specify the credentials in settings."))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                url_used = request.env['ir.config_parameter'].sudo().get_param('odoo_quickbook.select_url')
                url = str(
                    url_used) + 'v3/company/' + user.quickbook_realm_id + "/query?query=select * from Item where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from Item&minorversion=62'
            response = requests.get(url=url, headers={
                'Authorization': "Bearer " + user.access_token,
                'Accept': 'application/json',
            })
            if response.status_code == 200:
                quickbook_items = json.loads(response.text)
                for quickbook_item in quickbook_items['QueryResponse']['Item']:
                    item_redundecy_check = self.env['product.template'].sudo().search(
                        [('quickbook_product_id', '=', quickbook_item['Id'])])
                    if item_redundecy_check:
                        pass
                    else:
                        if quickbook_item['Name'] == 'Expenses':
                            product = self.env['product.template'].sudo().search([('name', '=', 'Expenses')])
                            if product:
                                product.write({
                                    'quickbook_product_id': quickbook_item['Id'],
                                })
                            pass
                        else:
                            if 'ExpenseAccountRef' in quickbook_item:
                                ExpenseAccountRef = self.env['coa.settings'].sudo().search(
                                    [('account_id', '=', quickbook_item['ExpenseAccountRef']['value'])]).id
                            if 'IncomeAccountRef' in quickbook_item:
                                IncomeAccountRef = self.env['coa.settings'].sudo().search(
                                    [('account_id', '=', quickbook_item['IncomeAccountRef']['value'])]).id
                            if 'AssetAccountRef' in quickbook_item:
                                AssetAccountRef = self.env['coa.settings'].sudo().search(
                                    [('account_id', '=', quickbook_item['AssetAccountRef']['value'])]).id
                            if ExpenseAccountRef:
                                odoo_expense_account = self.env['account.account'].sudo().search(
                                    [('coa_id', '=', ExpenseAccountRef)]).id
                            if IncomeAccountRef:
                                odoo_income_account = self.env['account.account'].sudo().search(
                                    [('coa_id', '=', IncomeAccountRef)]).id
                            if AssetAccountRef:
                                odoo_inventory_account = self.env['account.account'].sudo().search(
                                    [('coa_id', '=', AssetAccountRef)]).id
                            if quickbook_item['Type'] == 'Inventory':
                                odoo_type = 'product'
                            elif quickbook_item['Type'] == 'NonInventory':
                                odoo_type = 'consu'
                            elif quickbook_item['Type'] == 'Service':
                                odoo_type = 'service'
                            else:
                                odoo_type = 'service'
                            taxes = []
                            if 'SalesTaxCodeRefs' in quickbook_item:
                                for tax_code_ref in quickbook_item['SalesTaxCodeRefs']:
                                    if 'value' in tax_code_ref:
                                        quickbook_item_tax_id = self.env['taxes.settings'].sudo().search(
                                            [('tax_id', '=', tax_code_ref['value'])], limit=1).id
                                        if not quickbook_item_tax_id:
                                            quickbook_item_tax_id = self.env['taxes.settings'].sudo().search(
                                                [('tax_id', '=', tax_code_ref['name'])], limit=1).id
                                        item_tax_id = self.env['account.tax'].sudo().search(
                                            [('tax_id', '=', quickbook_item_tax_id), ('type_tax_use', '=', 'sale')],
                                            limit=1).id
                                        if item_tax_id:
                                            taxes.append(item_tax_id)

                            self.env['product.template'].sudo().create({
                                'quickbook_product_id': quickbook_item['Id'],
                                'description': quickbook_item[
                                    'Description'] if 'Description' in quickbook_item else None,
                                'list_price': quickbook_item['UnitPrice'] if 'UnitPrice' in quickbook_item else None,
                                'property_account_expense_id': odoo_expense_account if odoo_expense_account else None,
                                'standard_price': quickbook_item[
                                    'PurchaseCost'] if 'PurchaseCost' in quickbook_item else None,
                                'property_account_income_id': odoo_income_account if odoo_income_account else None,
                                'name': quickbook_item['Name'],
                                'type': odoo_type,
                                # 'taxes_id': [[6, 0, taxes]],
                                'taxes_id': False,
                                'property_account_creditor_price_difference': odoo_inventory_account if odoo_inventory_account else None,
                            })
                            self.env.cr.commit()
                            _logger.info("Successfully created Item: " + quickbook_item['Name'] + " with  Item ID: " +
                                         quickbook_item['Id'])
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_purchase_order(self, id=None):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from PurchaseOrder where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from PurchaseOrder&minorversion=62'
            response = requests.get(url, headers={
                'Authorization': "Bearer " + user.access_token,
                'Accept': 'application/json'})
            if response.status_code == 200:
                quickbook_purchase_orders = json.loads(response.text)
                if not 'PurchaseOrder' in quickbook_purchase_orders['QueryResponse']:
                    raise ValidationError(("No Purchase Order exists in QuickBooks to be imported at this time."))
                for quickbook_purchase_order in quickbook_purchase_orders['QueryResponse']['PurchaseOrder']:
                    purchase_order_redundecy_check = self.env['purchase.order'].sudo().search(
                        [('quickbook_purchase_order_id', '=', quickbook_purchase_order['Id'])])
                    if purchase_order_redundecy_check:
                        pass
                    else:
                        purchase_order_partner = self.env['res.partner'].sudo().search(
                            [('quickbook_contact_id', '=', quickbook_purchase_order['VendorRef']['value'])])
                        if not purchase_order_partner:
                            result = self.env['default.functions'].checkquickbookredundency("Vendor", "Id",
                                                                                            quickbook_purchase_order[
                                                                                                'VendorRef']['value'])
                            if 'Vendor' in result['QueryResponse']:
                                purchase_order_partner = self.env['res.partner'].sudo().search(
                                    [('name', '=', result['QueryResponse']['Vendor'][0]['DisplayName'])])
                                if not purchase_order_partner:
                                    self.env['res.config.settings'].import_vendors(
                                        quickbook_purchase_order['VendorRef']['value'])
                                    purchase_order_partner = self.env['res.partner'].sudo().search(
                                        [('quickbook_contact_id', '=', quickbook_purchase_order['VendorRef']['value'])])
                        line_vals = []
                        for item in quickbook_purchase_order['Line']:
                            if 'AccountBasedExpenseLineDetail' in item:
                                odoo_product = self.env['product.template'].sudo().search([('name', '=', 'Expenses')])
                                if odoo_product:
                                    odoo_product_product = self.env['product.product'].sudo().search(
                                        [('product_tmpl_id', '=', odoo_product.id)])
                                    line_vals.append((0, 0, {
                                        'product_id': odoo_product_product.id,
                                        "product_qty": 1,
                                        'price_unit': item['Amount'],
                                    }))
                            if 'ItemBasedExpenseLineDetail' in item:
                                odoo_product = self.env['product.template'].sudo().search([('quickbook_product_id', '=',
                                                                                            item[
                                                                                                'ItemBasedExpenseLineDetail'][
                                                                                                'ItemRef']['value'])])
                                if not odoo_product:
                                    result = self.env['default.functions'].checkquickbookredundency("Item", "Id", item[
                                        'ItemBasedExpenseLineDetail']['ItemRef']['value'])
                                    if 'Item' in result['QueryResponse']:
                                        odoo_product = self.env['product.template'].sudo().search(
                                            [('name', '=', result['QueryResponse']['Item'][0]['Name'])])
                                        if not odoo_product:
                                            self.env['res.config.settings'].import_items(
                                                item['ItemBasedExpenseLineDetail']['ItemRef']['value'])
                                            odoo_product = self.env['product.template'].sudo().search([(
                                                'quickbook_product_id',
                                                '=', item[
                                                    'ItemBasedExpenseLineDetail'][
                                                    'ItemRef'][
                                                    'value'])])
                                if odoo_product:
                                    odoo_product_product = self.env['product.product'].sudo().search(
                                        [('product_tmpl_id', '=', odoo_product.id)])
                                    line_vals.append((0, 0, {
                                        'product_id': odoo_product_product.id,
                                        "product_qty": item['ItemBasedExpenseLineDetail']['Qty'] if 'Qty' in item[
                                            'ItemBasedExpenseLineDetail'] else 1,
                                        'price_unit': item['ItemBasedExpenseLineDetail']['UnitPrice'] if 'UnitPrice' in
                                                                                                         item[
                                                                                                             'ItemBasedExpenseLineDetail'] else None,
                                    }))
                        if quickbook_purchase_order['POStatus'] == 'Open':
                            state = 'draft'
                        if quickbook_purchase_order['POStatus'] == 'Closed':
                            state = 'purchase'
                        if 'DocNumber' in quickbook_purchase_order:
                            self.env['purchase.order'].sudo().create({
                                'quickbook_purchase_order_id': quickbook_purchase_order['Id'],
                                'state': state,
                                'name': quickbook_purchase_order[
                                    'DocNumber'] if 'DocNumber' in quickbook_purchase_order else "",
                                'partner_id': purchase_order_partner.id,
                                'date_order': quickbook_purchase_order[
                                    'TxnDate'] if 'TxnDate' in quickbook_purchase_order else None,
                                'order_line': line_vals,
                            })
                            self.env.cr.commit()
                        else:
                            self.env['purchase.order'].sudo().create({
                                'quickbook_purchase_order_id': quickbook_purchase_order['Id'],
                                'state': state,
                                'partner_id': purchase_order_partner.id,
                                'date_order': quickbook_purchase_order[
                                    'TxnDate'] if 'TxnDate' in quickbook_purchase_order else None,
                                'order_line': line_vals,
                            })
                            self.env.cr.commit()
                        if 'DocNumber' in quickbook_purchase_order:
                            _logger.info("successfully Created Purchase Order: " + quickbook_purchase_order[
                                'DocNumber'] + " with Purchase ID: " + quickbook_purchase_order['Id'])
                        else:
                            _logger.info(
                                "successfully Created Purchase Order  with Purchase ID: " + quickbook_purchase_order[
                                    'Id'])
            else:
                _logger.info(response.text)
        except Exception as e:
            raise ValidationError(_(str(e)))

    def import_sale_order(self, id=None):
        try:
            odoo_product_product = ''
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from SalesReceipt where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from SalesReceipt&minorversion=62'
            response = requests.get(url=url,
                                    headers={
                                        'Authorization': "Bearer " + user.access_token,
                                        'Accept': 'application/json'})
            if response.status_code == 200:
                quickbook_sales_orders = json.loads(response.text)
                if not 'SalesReceipt' in quickbook_sales_orders['QueryResponse']:
                    raise ValidationError(("No Sales Receipts exist in QuickBooks to be imported at this time."))
                for quickbook_sale_order in quickbook_sales_orders['QueryResponse']['SalesReceipt']:
                    dicount = 0
                    sale_order_redundancy_check = self.env['sale.order'].sudo().search(
                        [('quickbook_sale_order_id', '=', quickbook_sale_order['Id'])])
                    if sale_order_redundancy_check:
                        pass
                    else:
                        if 'CustomerRef' in quickbook_sale_order:
                            sale_order_partner = self.env['res.partner'].sudo().search(
                                [('quickbook_contact_id', '=', quickbook_sale_order['CustomerRef']['value'])])
                            if not sale_order_partner:
                                result = self.env['default.functions'].checkquickbookredundency("Customer", "Id",
                                                                                                quickbook_sale_order[
                                                                                                    'CustomerRef'][
                                                                                                    'value'])
                                if 'Customer' in result['QueryResponse']:
                                    sale_order_partner = self.env['res.partner'].sudo().search(
                                        [('name', '=', result['QueryResponse']['Customer'][0]['DisplayName'])])
                                    if not sale_order_partner:
                                        self.env['res.config.settings'].import_customer(
                                            quickbook_sale_order['CustomerRef']['value'])
                                        sale_order_partner = self.env['res.partner'].sudo().search([(
                                            'quickbook_contact_id',
                                            '=',
                                            quickbook_sale_order[
                                                'CustomerRef'][
                                                'value'])])
                        else:
                            sale_order_partner = self.env['res.partner'].sudo().search([('name', '=', 'Administrator')])
                        line_vals = []
                        for item in quickbook_sale_order['Line']:
                            taxes = []
                            if item['DetailType'] == 'SalesItemLineDetail':
                                for discount_loop in quickbook_sale_order['Line']:
                                    if discount_loop['DetailType'] == 'DiscountLineDetail':
                                        dicount = discount_loop['DiscountLineDetail']['DiscountPercent']
                                odoo_product = self.env['product.template'].sudo().search(
                                    [('quickbook_product_id', '=', item['SalesItemLineDetail']['ItemRef']['value'])])
                                if not odoo_product:
                                    result = self.env['default.functions'].checkquickbookredundency("Item", "Id", item[
                                        'SalesItemLineDetail']['ItemRef']['value'])
                                    if 'Item' in result['QueryResponse']:
                                        odoo_product = self.env['product.template'].sudo().search(
                                            [('name', '=', result['QueryResponse']['Item'][0]['Name'])])
                                        if not odoo_product:
                                            self.env['res.config.settings'].import_items(
                                                item['SalesItemLineDetail']['ItemRef']['value'])
                                            odoo_product = self.env['product.template'].sudo().search([(
                                                'quickbook_product_id',
                                                '=', item[
                                                    'SalesItemLineDetail'][
                                                    'ItemRef'][
                                                    'value'])])
                                if odoo_product:
                                    odoo_product_product = self.env['product.product'].sudo().search(
                                        [('product_tmpl_id', '=', odoo_product.id)])
                                if 'TaxCodeRef' in item['SalesItemLineDetail']:
                                    if item['SalesItemLineDetail']['TaxCodeRef']['value'] == 'TAX':
                                        if 'TaxLine' in quickbook_sale_order['TxnTaxDetail']:
                                            for tax in quickbook_sale_order['TxnTaxDetail']['TaxLine']:
                                                quickbook_item_tax_id = self.env['taxes.settings'].sudo().search(
                                                    [('tax_id', '=', tax['TaxLineDetail']['TaxRateRef']['value'])]).id
                                                item_tax_id = self.env['account.tax'].sudo().search(
                                                    [('tax_id', '=', quickbook_item_tax_id),
                                                     ('type_tax_use', '=', 'sale')]).id
                                                if item_tax_id:
                                                    taxes.append(item_tax_id)
                                if 'UnitPrice' in item['SalesItemLineDetail']:
                                    price = item['SalesItemLineDetail']['UnitPrice']
                                elif 'MarkupInfo' in item['SalesItemLineDetail']:
                                    price = item['SalesItemLineDetail']['MarkupInfo']['Value']
                                line_vals.append((0, 0, {
                                    'product_id': odoo_product_product.id,
                                    "product_uom_qty": item['SalesItemLineDetail']['Qty'] if 'Qty' in item[
                                        'SalesItemLineDetail'] else 1,
                                    'discount': dicount,
                                    'price_unit': price,
                                    'tax_id': [[6, 0, taxes]]
                                }))
                            elif item['DetailType'] == 'DiscountLineDetail':
                                pass
                        if 'DocNumber' in quickbook_sale_order:
                            self.env['sale.order'].sudo().create({
                                'quickbook_sale_order_id': quickbook_sale_order['Id'],
                                'state': 'draft',
                                'name': quickbook_sale_order[
                                    'DocNumber'] if 'DocNumber' in quickbook_sale_order else "",
                                'partner_id': sale_order_partner.id,
                                'date_order': quickbook_sale_order[
                                    'TxnDate'] if 'TxnDate' in quickbook_sale_order else None,
                                'order_line': line_vals,
                            })
                            self.env.cr.commit()
                        else:
                            self.env['sale.order'].sudo().create({
                                'quickbook_sale_order_id': quickbook_sale_order['Id'],
                                'state': 'draft',
                                'partner_id': sale_order_partner.id,
                                'date_order': quickbook_sale_order[
                                    'TxnDate'] if 'TxnDate' in quickbook_sale_order else None,
                                'order_line': line_vals,
                            })
                            self.env.cr.commit()
                        if 'DocNumber' in quickbook_sale_order:
                            _logger.info("successfully Created Sale Order: " + quickbook_sale_order[
                                'DocNumber'] + " with Sale Order ID: " + quickbook_sale_order['Id'])
                        else:
                            _logger.info("successfully Created Sale Order  with ID: " + quickbook_sale_order['Id'])
            else:
                _logger.info(response.text)
        except Exception as e:
            raise ValidationError(_(str(e)))

    def import_bills(self, id=None):
        try:
            odoo_account = ''
            odoo_product_product = ''
            odoo_payment_term = ''
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from Bill where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from Bill&minorversion=62'
            response = requests.get(url=url,
                                    headers={
                                        'Authorization': "Bearer " + user.access_token,
                                        'Accept': 'application/json'})
            if response.status_code == 200:
                quickbook_bills = json.loads(response.text)
                if not 'Bill' in quickbook_bills['QueryResponse']:
                    raise ValidationError("No Bill exists in QuickBooks to be imported at this time.")
                for quickbook_bill in quickbook_bills['QueryResponse']['Bill']:
                    currency_id = self.env['res.currency'].sudo().search(
                        [('name', '=', quickbook_bill['CurrencyRef']['value'])])
                    account_journal = self.env['account.journal'].sudo().search([('name', '=', 'Vendor Bills')])
                    account_journal.sudo().write({
                        'currency_id': currency_id.id
                    })
                    self.env.cr.commit()

                    bill_redundecy_check = self.env['account.move'].sudo().search(
                        [('quickbook_invoice_id', '=', quickbook_bill['Id'])])
                    if bill_redundecy_check:
                        pass
                    else:
                        bill_partner = self.env['res.partner'].sudo().search(
                            [('quickbook_contact_id', '=', quickbook_bill['VendorRef']['value'])])
                        if not bill_partner:
                            result = self.env['default.functions'].checkquickbookredundency("Vendor", "Id",
                                                                                            quickbook_bill['VendorRef'][
                                                                                                'value'])
                            if 'Vendor' in result['QueryResponse']:
                                bill_partner = self.env['res.partner'].sudo().search(
                                    [('name', '=', result['QueryResponse']['Vendor'][0]['DisplayName'])])
                                if not bill_partner:
                                    self.env['res.config.settings'].import_vendors(quickbook_bill['VendorRef']['value'])
                                    bill_partner = self.env['res.partner'].sudo().search(
                                        [('quickbook_contact_id', '=', quickbook_bill['VendorRef']['value'])])
                        line_vals = []

                        quickbook_account = False
                        odoo_account = False
                        for item in quickbook_bill['Line']:
                            if 'AccountBasedExpenseLineDetail' in item:
                                odoo_product = self.env['product.template'].sudo().search([('name', '=', 'Expenses')])
                                if odoo_product:
                                    odoo_product_product = self.env['product.product'].sudo().search(
                                        [('product_tmpl_id', '=', odoo_product.id)])
                                if 'AccountRef' in item['AccountBasedExpenseLineDetail']:
                                    quickbook_account = self.env['coa.settings'].sudo().search([('account_id', '=',
                                                                                                 item[
                                                                                                     'AccountBasedExpenseLineDetail'][
                                                                                                     'AccountRef'][
                                                                                                     'value'])])
                                    if quickbook_account:
                                        odoo_account = self.env['account.account'].sudo().search(
                                            [('coa_id', '=', quickbook_account.id)])
                                        if odoo_account:
                                            odoo_account = self.env['account.account'].sudo().search(
                                                [('coa_id', '=', quickbook_account.id)])[0].id
                                line_vals.append((0, 0, {
                                    'account_id': odoo_account,
                                    'product_id': odoo_product_product.id,
                                    "quantity": 1,
                                    'price_unit': item['Amount'],
                                    'currency_id': currency_id.id,
                                    'journal_id': account_journal.id
                                    # 'tax_ids': [[6, 0, odoo_taxes]]
                                }))
                            elif 'ItemBasedExpenseLineDetail' in item:
                                odoo_product = self.env['product.template'].sudo().search([('quickbook_product_id', '=',
                                                                                            item[
                                                                                                'ItemBasedExpenseLineDetail'][
                                                                                                'ItemRef']['value'])])
                                if not odoo_product:
                                    result = self.env['default.functions'].checkquickbookredundency("Item", "Id", item[
                                        'ItemBasedExpenseLineDetail']['ItemRef']['value'])
                                    if 'Item' in result['QueryResponse']:
                                        odoo_product = self.env['product.template'].sudo().search(
                                            [('name', '=', result['QueryResponse']['Item'][0]['Name'])])
                                        if not odoo_product:
                                            self.env['res.config.settings'].import_items(
                                                item['ItemBasedExpenseLineDetail']['ItemRef']['value'])
                                            odoo_product = self.env['product.template'].sudo().search([(
                                                'quickbook_product_id',
                                                '=', item[
                                                    'ItemBasedExpenseLineDetail'][
                                                    'ItemRef'][
                                                    'value'])])
                                if odoo_product:
                                    odoo_product_product = self.env['product.product'].sudo().search(
                                        [('product_tmpl_id', '=', odoo_product.id)])
                                if 'AccountRef' in item['ItemBasedExpenseLineDetail']:
                                    quickbook_account = self.env['coa.settings'].sudo().search([('account_id', '=',
                                                                                                 item[
                                                                                                     'AccountBasedExpenseLineDetail'][
                                                                                                     'AccountRef'][
                                                                                                     'value'])])
                                    if quickbook_account:
                                        odoo_account = self.env['account.account'].sudo().search(
                                            [('coa_id', '=', quickbook_account.id)])
                                        if odoo_account:
                                            odoo_account = self.env['account.account'].sudo().search(
                                                [('coa_id', '=', quickbook_account.id)])[0].id
                                line_vals.append((0, 0, {
                                    'account_id': odoo_account,
                                    'product_id': odoo_product_product.id,
                                    "quantity": item['ItemBasedExpenseLineDetail']['Qty'] if 'Qty' in item[
                                        'ItemBasedExpenseLineDetail'] else None,
                                    'price_unit': item['ItemBasedExpenseLineDetail']['UnitPrice'] if 'UnitPrice' in
                                                                                                     item[
                                                                                                         'ItemBasedExpenseLineDetail'] else None,
                                    'currency_id': currency_id.id,
                                    'journal_id': account_journal.id
                                }))

                        if 'TxnTaxDetail' in quickbook_bill:
                            odoo_tax_product = False
                            odoo_tax = self.env['product.template'].sudo().search([('name', '=', 'Taxes')])
                            if odoo_tax:

                                odoo_tax_product = self.env['product.product'].sudo().search(
                                    [('product_tmpl_id', '=', odoo_tax.id)])

                                if quickbook_account:
                                    odoo_account = self.env['account.account'].sudo().search(
                                        [('coa_id', '=', quickbook_account.id)])
                                    if odoo_account:
                                        odoo_account = self.env['account.account'].sudo().search(
                                            [('coa_id', '=', quickbook_account.id)])[0].id

                                line_vals.append((0, 0, {
                                    'account_id': odoo_account,
                                    'product_id': odoo_tax_product.id,
                                    "quantity": 1,
                                    'price_unit': quickbook_bill['TxnTaxDetail']['TotalTax'],
                                    'currency_id': currency_id.id,
                                    'journal_id': 2
                                }))
                        if 'SalesTermRef' in quickbook_bill:
                            odoo_payment_term = self.env['account.payment.term'].sudo().search(
                                [('quickbook_payment_term_id', '=', quickbook_bill['SalesTermRef']['value'])]).id
                        if 'DocNumber' in quickbook_bill:
                            self.env['account.move'].sudo().create({
                                'quickbook_invoice_id': quickbook_bill['Id'],
                                'name': quickbook_bill['DocNumber'] if 'DocNumber' in quickbook_bill else "",
                                'invoice_payment_term_id': odoo_payment_term if odoo_payment_term else None,
                                'partner_id': bill_partner.id,
                                'journal_id': 2,
                                'move_type': 'in_invoice',
                                "invoice_date": quickbook_bill['TxnDate'] if 'TxnDate' in quickbook_bill else None,
                                'invoice_line_ids': line_vals,
                            })
                            self.env.cr.commit()
                        else:
                            self.env['account.move'].sudo().create({
                                'quickbook_invoice_id': quickbook_bill['Id'],
                                'invoice_payment_term_id': odoo_payment_term if odoo_payment_term else None,
                                'partner_id': bill_partner.id,
                                'move_type': 'in_invoice',
                                "invoice_date": quickbook_bill['TxnDate'] if 'TxnDate' in quickbook_bill else None,
                                'invoice_line_ids': line_vals,
                                'journal_id': 2

                            })
                            self.env.cr.commit()
                        if 'DocNumber' in quickbook_bill:
                            _logger.info(
                                "successfully Created Bill: " + quickbook_bill['DocNumber'] + " with Bill ID: " +
                                quickbook_bill['Id'])
                        else:
                            _logger.info("successfully Created Bill  with ID: " + quickbook_bill['Id'])
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_invoices(self, id=None):
        try:
            odoo_account = ''
            odoo_product_product = ''
            odoo_payment_term = ''
            price = 0
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have Quickbook credentials!\nPlease specify the credentials in settings")
                    raise ValidationError(
                        ("No user have Quickbook credentials!\nPlease specify the credentials in settings"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from Invoice where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + 'v3/company/' + user.quickbook_realm_id + ('/query?query=select * from Invoice STARTPOSITION 1 MAXRESULTS 225&minorversion=62')
            response = requests.get(url=url, headers={
                'Authorization': "Bearer " + user.access_token,
                'Accept': 'application/json'})
            if response.status_code == 200:
                quickbook_invoices = json.loads(response.text)
                if not 'Invoice' in quickbook_invoices['QueryResponse']:
                    raise ValidationError(("No Invoice exists in QuickBooks to be imported at this time."))
                for quickbook_invoice in quickbook_invoices['QueryResponse']['Invoice']:
                    dicount = 0
                    self.env['account.move'].sudo().search(
                        [('quickbook_invoice_id', '=', quickbook_invoice['Id'])])

                    invoice_partner = self.env['res.partner'].sudo().search(
                        [('quickbook_contact_id', '=', quickbook_invoice['CustomerRef']['value'])])
                    if not invoice_partner:
                        result = self.env['default.functions'].checkquickbookredundency("Customer", "Id",
                                                                                        quickbook_invoice[
                                                                                            'CustomerRef']['value'])
                        if 'Customer' in result['QueryResponse']:
                            invoice_partner = self.env['res.partner'].sudo().search(
                                [('name', '=', result['QueryResponse']['Customer'][0]['DisplayName'])])
                            if not invoice_partner:
                                self.env['res.config.settings'].import_customer(
                                    quickbook_invoice['CustomerRef']['value'])
                                invoice_partner = self.env['res.partner'].sudo().search(
                                    [('quickbook_contact_id', '=', quickbook_invoice['CustomerRef']['value'])])
                    currency = self.env['res.currency'].sudo().search(
                        [('name', '=', quickbook_invoice['CurrencyRef']['value'])]).id
                    date = quickbook_invoice['MetaData']['CreateTime'].split('T')[0]
                    line_vals = []
                    for item in quickbook_invoice['Line']:
                        taxes = []
                        quickbook_account = False
                        if item['DetailType'] == 'SalesItemLineDetail':
                            for discount_loop in quickbook_invoice['Line']:
                                if discount_loop['DetailType'] == 'DiscountLineDetail':
                                    dicount = discount_loop['DiscountLineDetail']['DiscountPercent']
                            odoo_product = self.env['product.template'].sudo().search(
                                [('quickbook_product_id', '=', item['SalesItemLineDetail']['ItemRef']['value'])])
                            if not odoo_product:
                                if item['SalesItemLineDetail']['ItemRef']['value'] == "SHIPPING_ITEM_ID":
                                    odoo_product = self.env['product.template'].sudo().search(
                                        [('name', '=', 'Shipping Charges')])
                                    if not odoo_product:
                                        odoo_product = self.env['product.template'].sudo().create({
                                            'name': 'Shipping Charges',
                                            'list_price': 0,
                                            'standard_price': 0,
                                            'taxes_id': [(6, 0, [])],
                                            'supplier_taxes_id': [(6, 0, [])],
                                        })
                                        self.env.cr.commit()

                                else:
                                    result = self.env['default.functions'].checkquickbookredundency("Item", "Id",
                                                                                                    item[
                                                                                                        'SalesItemLineDetail'][
                                                                                                        'ItemRef'][
                                                                                                        'value'])

                                    if 'Item' in result['QueryResponse']:
                                        odoo_product = self.env['product.template'].sudo().search(
                                            [('name', '=', result['QueryResponse']['Item'][0]['Name'])])
                                        if not odoo_product:
                                            self.env['res.config.settings'].import_items(
                                                item['SalesItemLineDetail']['ItemRef']['value'])
                                            odoo_product = self.env['product.template'].sudo().search([(
                                                'quickbook_product_id',
                                                '=', item[
                                                    'SalesItemLineDetail'][
                                                    'ItemRef'][
                                                    'value'])])
                            if odoo_product:
                                odoo_product_product = self.env['product.product'].sudo().search(
                                    [('product_tmpl_id', '=', odoo_product.id)])
                            if 'ItemAccountRef' in item['SalesItemLineDetail']:
                                quickbook_account = self.env['coa.settings'].sudo().search(
                                    [('account_id', '=', item['SalesItemLineDetail']['ItemAccountRef']['value'])])
                                if quickbook_account:
                                    odoo_account = self.env['account.account'].sudo().search(
                                        [('coa_id', '=', quickbook_account.id)])
                                    if odoo_account:
                                        odoo_account = self.env['account.account'].sudo().search(
                                            [('coa_id', '=', quickbook_account.id)], limit=1).id
                            if 'TaxCodeRef' in item['SalesItemLineDetail']:
                                if item['SalesItemLineDetail']['TaxCodeRef']['value'] == 'TAX':
                                    if 'TaxLine' in quickbook_invoice['TxnTaxDetail']:
                                        for tax in quickbook_invoice['TxnTaxDetail']['TaxLine']:
                                            quickbook_item_tax_id = self.env['taxes.settings'].sudo().search(
                                                [('tax_id', '=', tax['TaxLineDetail']['TaxRateRef']['value'])]).id
                                            item_tax_id = self.env['account.tax'].sudo().search(
                                                [('tax_id', '=', quickbook_item_tax_id),
                                                 ('type_tax_use', '=', 'sale')]).id
                                            if item_tax_id:
                                                taxes.append(item_tax_id)
                            if 'UnitPrice' in item['SalesItemLineDetail']:
                                price = item['SalesItemLineDetail']['UnitPrice']
                            elif 'MarkupInfo' in item['SalesItemLineDetail']:
                                price = item['SalesItemLineDetail']['MarkupInfo']['Value']
                            if odoo_product.name == 'Shipping Charges':
                                price = item['Amount']
                            line_vals.append((0, 0, {
                                'account_id': odoo_account if odoo_account else False,
                                'product_id': odoo_product_product.id,
                                'discount': dicount,
                                "quantity": item['SalesItemLineDetail']['Qty'] if 'Qty' in item[
                                    'SalesItemLineDetail'] else 1,
                                'price_unit': price,
                                'tax_ids': [[6, 0, taxes]] if taxes else False
                            }))
                        elif item['DetailType'] == 'DiscountLineDetail':
                            pass
                        elif item['DetailType'] == 'SubTotalLineDetail':
                            pass
                    if 'TxnTaxDetail' in quickbook_invoice:
                        odoo_tax_product = False
                        odoo_tax = self.env['product.template'].sudo().search(
                            [('name', '=', 'Taxes')])
                        if odoo_tax:
                            odoo_tax_product = self.env['product.product'].sudo().search(
                                [('product_tmpl_id', '=', odoo_tax.id)])

                            if quickbook_account:
                                odoo_account = self.env['account.account'].sudo().search(
                                    [('coa_id', '=', quickbook_account.id)])
                                if odoo_account:
                                    odoo_account = self.env['account.account'].sudo().search(
                                        [('coa_id', '=', quickbook_account.id)])[0].id

                            line_vals.append((0, 0, {
                                'account_id': odoo_account,
                                'product_id': odoo_tax_product.id,
                                "quantity": 1,
                                'price_unit': quickbook_invoice['TxnTaxDetail']['TotalTax'],

                            }))

                    if 'SalesTermRef' in quickbook_invoice:
                        odoo_payment_term = self.env['account.payment.term'].sudo().search(
                            [('quickbook_payment_term_id', '=', quickbook_invoice['SalesTermRef']['value'])]).id

                    state = ''
                    if quickbook_invoice['Balance'] == quickbook_invoice['TotalAmt'] and quickbook_invoice[
                        'TotalAmt'] != 0:
                        state = 'draft'
                    elif quickbook_invoice['Balance'] == quickbook_invoice['TotalAmt'] and quickbook_invoice[
                        'TotalAmt'] == 0:
                        state = 'cancel'
                    elif quickbook_invoice['Balance'] == 0:
                        state = 'posted'


                    odoo_invoice = self.env['account.move'].sudo().search(
                        [('quickbook_invoice_id', '=', quickbook_invoice['Id'])])
                    if not odoo_invoice:
                        odoo_invoice = self.env['account.move'].sudo().create({
                            'quickbook_invoice_id': quickbook_invoice['Id'],
                            'name': quickbook_invoice['DocNumber'] if 'DocNumber' in quickbook_invoice else "",
                            'partner_id': invoice_partner.id,
                            'invoice_payment_term_id': odoo_payment_term if odoo_payment_term else None,
                            'currency_id': currency if currency else 1,
                            'move_type': 'out_invoice',
                            # 'journal_id': journal_id,
                            'invoice_date': quickbook_invoice[
                                'TxnDate'] if 'TxnDate' in quickbook_invoice else None,
                            "invoice_date_due": quickbook_invoice['DueDate'],
                            'invoice_line_ids': line_vals,
                        })


                        self.env.cr.commit()


                        if state=='posted':
                            odoo_invoice.action_post()
                            # pass
                            self.env.cr.commit()
                        elif state=='cancel':
                            odoo_invoice.button_cancel()
                            # pass

                    if 'DocNumber' in quickbook_invoice:
                        _logger.info("Successfully Created Invoice: " + quickbook_invoice['DocNumber'] + "with "
                                                                                                         "Invoice"
                                                                                                         " ID: "
                                     + quickbook_invoice['Id'])
                    else:
                        _logger.info("Successfully Updated Invoice with ID: " + quickbook_invoice['Id'])
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_taxes(self, id=None):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have Quickbooks credentials!\nPlease specify the credentials in settings")
                    raise ValidationError(
                        ("No user have Quickbooks credentials!\nPlease specify the credentials in settings"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from TaxRate where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from TaxRate&minorversion=62'
            response = requests.get(url=url, headers={
                'Authorization': "Bearer " + user.access_token,
                'Accept': 'application/json'})
            if response.status_code == 200:
                quickbook_tax_rates_response = json.loads(response.text)
                for quickbook_tax_rate in quickbook_tax_rates_response['QueryResponse']['TaxRate']:
                    tax_redundancy_check = self.env['taxes.settings'].sudo().search(
                        [('tax_id', '=', quickbook_tax_rate['Id'])])
                    if tax_redundancy_check:
                        pass
                    else:
                        agency_id = self.env['taxagency.settings'].sudo().search(
                            [('agency_id', '=', quickbook_tax_rate['AgencyRef']['value'])])
                        self.env['taxes.settings'].sudo().create({
                            'tax_type': quickbook_tax_rate['Description'],
                            'name': quickbook_tax_rate['Name'],
                            'effective_rate': quickbook_tax_rate[
                                'RateValue'] if 'RateValue' in quickbook_tax_rate else None,
                            'status': quickbook_tax_rate['Active'],
                            'tax_id': quickbook_tax_rate['Id'],
                            'tax_agency_id': agency_id.id,
                        })
                        self.env.cr.commit()
                        _logger.info("successfully Created Tax Agency: " + quickbook_tax_rate['Name'])

            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_departments(self, id=None):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from Department where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from Department&minorversion=62'
            response = requests.get(url=url, headers={
                'Authorization': "Bearer " + user.access_token,
                'Accept': 'application/json'})
            if response.status_code == 200:
                quickbook_departments_response = json.loads(response.text)
                if 'Department' in quickbook_departments_response['QueryResponse']:
                    for quickbook_department in quickbook_departments_response['QueryResponse']['Department']:
                        department_redundancy_check = self.env['hr.department'].sudo().search(
                            [('quickbook_department_id', '=', quickbook_department['Id'])])
                        if department_redundancy_check:
                            pass
                        else:
                            self.env['hr.department'].sudo().create({
                                'display_name': quickbook_department['FullyQualifiedName'],
                                'name': quickbook_department['Name'],
                                'quickbook_department_id': quickbook_department['Id'],
                            })
                            self.env.cr.commit()
                            _logger.info("successfully Created Department: " + quickbook_department['Name'])
                else:
                    pass
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_employee(self, id=None):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from Employee where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from Employee&minorversion=62'
            response = requests.get(url=url, headers={
                'Authorization': "Bearer " + user.access_token,
                'Accept': 'application/json'})
            if response.status_code == 200:
                quickbook_employees_response = json.loads(response.text)
                if 'Employee' in quickbook_employees_response['QueryResponse']:
                    for quickbook_employee in quickbook_employees_response['QueryResponse']['Employee']:
                        address_id = ''
                        gender = ''
                        employee_redundancy_check = self.env['hr.employee'].sudo().search(
                            [('quickbook_employee_id', '=', quickbook_employee['Id'])])
                        if employee_redundancy_check:
                            pass
                        else:
                            if "PrimaryAddr" in quickbook_employee:
                                country_id = ''
                                state_id = ''
                                if 'Country' in quickbook_employee["PrimaryAddr"]:
                                    country_id = self.env['res.country'].sudo().search(
                                        [('name', '=', quickbook_employee["PrimaryAddr"]['Country'])]).id
                                if "CountrySubDivisionCode" in quickbook_employee["PrimaryAddr"]:
                                    state_id = self.env['res.country.state'].sudo().search(
                                        [('code', '=', quickbook_employee["PrimaryAddr"]["CountrySubDivisionCode"]),
                                         ('country_id', '=', country_id)]).id
                                address_id = self.env['res.partner'].sudo().create({
                                    'city': quickbook_employee["PrimaryAddr"]["City"] if "City" in quickbook_employee[
                                        "PrimaryAddr"] else None,
                                    'street': quickbook_employee["PrimaryAddr"]['Line1'] if "Line1" in
                                                                                            quickbook_employee[
                                                                                                "PrimaryAddr"] else None,
                                    'street2': quickbook_employee["PrimaryAddr"]['Line2'] if "Line2" in
                                                                                             quickbook_employee[
                                                                                                 "PrimaryAddr"] else None,
                                    'country_id': country_id if country_id else None,
                                    'type': 'invoice',
                                    'state_id': state_id if state_id else None,
                                    'zip': quickbook_employee["PrimaryAddr"]["PostalCode"] if "PostalCode" in
                                                                                              quickbook_employee[
                                                                                                  "PrimaryAddr"] else None,
                                })
                            if 'Gender' in quickbook_employee:
                                if quickbook_employee['Gender'] == 'Male':
                                    gender = 'male'
                                if quickbook_employee['Gender'] == 'Female':
                                    gender = 'female'
                            self.env['hr.employee'].sudo().create({
                                'quickbook_employee_id': quickbook_employee['Id'],
                                'display_name': quickbook_employee['DisplayName'],
                                'name': quickbook_employee['DisplayName'],
                                'active': quickbook_employee['Active'] if 'Active' in quickbook_employee else None,
                                'identification_id': quickbook_employee[
                                    'EmployeeNumber'] if 'EmployeeNumber' in quickbook_employee else None,
                                'ssnid': quickbook_employee['SSN'] if 'SSN' in quickbook_employee else None,
                                'birthday': quickbook_employee[
                                    'BirthDate'] if 'BirthDate' in quickbook_employee else None,
                                'gender': gender if gender else None,
                                # 'quickbook_department_id': quickbook_employee['HiredDate'] if 'PrimaryPhone' in quickbook_employee else None,
                                'departure_date': quickbook_employee[
                                    'ReleasedDate'] if 'ReleasedDate' in quickbook_employee else None,
                                'phone': quickbook_employee['PrimaryPhone'][
                                    'FreeFormNumber'] if 'PrimaryPhone' in quickbook_employee else None,
                                'emergency_phone': quickbook_employee['Mobile'][
                                    'FreeFormNumber'] if 'Mobile' in quickbook_employee else None,
                                'private_email': quickbook_employee['PrimaryEmailAddr'][
                                    'Address'] if 'PrimaryEmailAddr' in quickbook_employee else None,
                                'address_home_id': address_id.id if address_id else None,
                            })
                            self.env.cr.commit()
                            _logger.info("successfully Created Employee: " + quickbook_employee['DisplayName'])
                else:
                    pass
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_payment_method(self, id=None):
        try:

            context = self._context
            start_position = 1
            max_results = 100
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            while True:
                if id:
                    IrConfigParameter = request.env['ir.config_parameter'].sudo()
                    select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                    url = str(
                        select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from PaymentMethod where Id='" + str(
                        id) + "'&minorversion=62"
                else:
                    IrConfigParameter = request.env['ir.config_parameter'].sudo()
                    select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                    url = str(
                        select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from PaymentMethod STARTPOSITION ' + str(
                        start_position) + " MAXRESULTS " + str(max_results) + '&minorversion=62'
                response = requests.get(
                    url=url, headers={
                        'Accept': 'application/json',
                        'Authorization': 'Bearer ' + user.access_token
                    })
                if response.status_code != 200:
                    _logger.info(response.text)
                    break
                quickbook_payment_method_response = json.loads(response.text)
                if not quickbook_payment_method_response['QueryResponse'].get('PaymentMethod'):
                    break
                if response.status_code == 200:
                    for quickbook_payment in quickbook_payment_method_response['QueryResponse']['PaymentMethod']:
                        odoo_payment = self.env['account.payment.method'].sudo().search(
                            [('quickbook_id', '=', quickbook_payment['Id'])])
                        data = {
                            'name': quickbook_payment['Name'],
                            'code': quickbook_payment['Name'].lower(),
                            'quickbook_id': quickbook_payment['Id'],
                            'payment_type': 'inbound'
                        }
                        if not odoo_payment:
                            odoo_payment = self.env['account.payment.method'].sudo().create(data)
                        else:
                            odoo_payment.sudo().write(data)
                        qb_payment = self.env['account.payment.method.line'].sudo().search(
                            [('quickbook_id', '=', quickbook_payment['Id'])])
                        data = {
                            'name': odoo_payment.name,
                            'code': quickbook_payment['Type'],
                            'payment_method_id': odoo_payment.id,
                            'quickbook_id': odoo_payment.quickbook_id,
                            'available_payment_method_ids': [(6, 0, [odoo_payment.id])],
                        }
                        if not qb_payment:
                            self.env['account.payment.method.line'].sudo().create(data)
                        else:
                            qb_payment.sudo().write(data)
                        self.env.cr.commit()
                        _logger.info("successfully Created Payment Method : " + quickbook_payment['Id'])
                else:
                    _logger.info(response.text)

                start_position += max_results
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_vendor_payment(self, id=None):
        try:
            payment_partner = ""
            partner_type = ""
            move_id = ''
            payment_type = ''
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from BillPayment where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from BillPayment&minorversion=62'
            response = requests.get(
                url=url, headers={
                    'Accept': 'application/json',
                    'Authorization': 'Bearer ' + user.access_token
                })
            if response.status_code == 200:
                quickbook_terms_response = json.loads(response.text)
                for quickbook_term in quickbook_terms_response['QueryResponse']['BillPayment']:
                    term_redundancy_check = self.env['account.payment'].sudo().search(
                        [('quickbook_payment_id', '=', quickbook_term['Id'])])
                    if term_redundancy_check:
                        pass
                    else:
                        for payemt_line in quickbook_term['Line']:
                            if 'VendorRef' in quickbook_term:
                                payment_partner = self.env['res.partner'].sudo().search(
                                    [('quickbook_contact_id', '=', quickbook_term['VendorRef']['value'])])
                                if not payment_partner:
                                    result = self.env['default.functions'].checkquickbookredundency("Vendor", "Id",
                                                                                                    quickbook_term[
                                                                                                        'VendorRef'][
                                                                                                        'value'])
                                    if 'Vendor' in result['QueryResponse']:
                                        payment_partner = self.env['res.partner'].sudo().search(
                                            [('name', '=', result['QueryResponse']['Vendor'][0]['DisplayName'])])
                                        if not payment_partner:
                                            self.env['res.config.settings'].import_customer(
                                                quickbook_term['VendorRef']['value'])
                                            payment_partner = self.env['res.partner'].sudo().search(
                                                [('quickbook_contact_id', '=', quickbook_term['VendorRef']['Value'])])
                            journal_id = self.env['account.journal'].sudo().search([('name', '=', 'Cash')]).id
                            if 'LinkedTxn' in payemt_line:
                                move_id = self.env['account.move'].sudo().search(
                                    [('quickbook_invoice_id', '=', payemt_line['LinkedTxn'][0]['TxnId'])])
                            if payment_partner.supplier_rank >= 1:
                                partner_type = 'supplier'
                            if payemt_line['LinkedTxn'][0]['TxnType'] == 'Bill':
                                payment_type = 'outbound'
                            if payemt_line['LinkedTxn'][0]['TxnType'] == 'VendorCredit':
                                payment_type = 'inbound'
                            self.env['account.payment'].create({
                                'journal_id': journal_id,
                                # 'name' : None,
                                # 'move_id': move_id.id if move_id else None,
                                'partner_id': payment_partner.id,
                                'quickbook_payment_id': quickbook_term['Id'],
                                'partner_type': partner_type,
                                'payment_type': payment_type,
                                'amount': payemt_line['Amount'],
                                'ref': move_id.name if move_id else None,
                            })
                            self.env.cr.commit()
                            _logger.info("successfully Created Vendor Payment : " + quickbook_term['Id'])
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_credit_memo(self, id=None):
        try:
            odoo_account = ''
            odoo_product_product = ''
            price = 0
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from CreditMemo where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from CreditMemo&minorversion=62'
            response = requests.get(url=url, headers={
                'Authorization': "Bearer " + user.access_token,
                'Accept': 'application/json'})
            if response.status_code == 200:
                quickbook_credit_memo = json.loads(response.text)
                if not 'CreditMemo' in quickbook_credit_memo['QueryResponse']:
                    raise ValidationError("No CreditMemo exists in QuickBooks to be imported at this time.")
                for credit_memo in quickbook_credit_memo['QueryResponse']['CreditMemo']:
                    dicount = 0
                    invoice_redundancy_check = self.env['account.move'].sudo().search(
                        [('quickbook_invoice_id', '=', credit_memo['Id'])])
                    if invoice_redundancy_check:
                        pass
                    else:
                        invoice_partner = self.env['res.partner'].sudo().search(
                            [('quickbook_contact_id', '=', credit_memo['CustomerRef']['value'])])
                        if not invoice_partner:
                            result = self.env['default.functions'].checkquickbookredundency("Customer", "Id",
                                                                                            credit_memo['CustomerRef'][
                                                                                                'value'])
                            if 'Customer' in result['QueryResponse']:
                                invoice_partner = self.env['res.partner'].sudo().search(
                                    [('name', '=', result['QueryResponse']['Customer'][0]['DisplayName'])])
                                if not invoice_partner:
                                    self.env['res.config.settings'].import_customer(credit_memo['CustomerRef']['value'])
                                    invoice_partner = self.env['res.partner'].sudo().search(
                                        [('quickbook_contact_id', '=', credit_memo['CustomerRef']['value'])])
                        currency = self.env['res.currency'].sudo().search(
                            [('name', '=', credit_memo['CurrencyRef']['value'])]).id
                        date = credit_memo['MetaData']['CreateTime'].split('T')[0]
                        line_vals = []
                        for item in credit_memo['Line']:
                            taxes = []
                            if item['DetailType'] == 'SalesItemLineDetail':
                                for discount_loop in credit_memo['Line']:
                                    if discount_loop['DetailType'] == 'DiscountLineDetail':
                                        dicount = discount_loop['DiscountLineDetail']['DiscountPercent']
                                odoo_product = self.env['product.template'].sudo().search(
                                    [('quickbook_product_id', '=', item['SalesItemLineDetail']['ItemRef']['value'])])
                                if not odoo_product:
                                    result = self.env['default.functions'].checkquickbookredundency("Item", "Id", item[
                                        'SalesItemLineDetail']['ItemRef']['value'])
                                    if 'Item' in result['QueryResponse']:
                                        odoo_product = self.env['product.template'].sudo().search(
                                            [('name', '=', result['QueryResponse']['Item'][0]['Name'])])
                                        if not odoo_product:
                                            self.env['res.config.settings'].import_items(
                                                item['SalesItemLineDetail']['ItemRef']['value'])
                                            odoo_product = self.env['product.template'].sudo().search([(
                                                'quickbook_product_id',
                                                '=', item[
                                                    'SalesItemLineDetail'][
                                                    'ItemRef'][
                                                    'value'])])
                                if odoo_product:
                                    odoo_product_product = self.env['product.product'].sudo().search(
                                        [('product_tmpl_id', '=', odoo_product.id)])
                                if 'ItemAccountRef' in item['SalesItemLineDetail']:
                                    quickbook_account = self.env['coa.settings'].sudo().search(
                                        [('account_id', '=', item['SalesItemLineDetail']['ItemAccountRef']['value'])])
                                    if quickbook_account:
                                        odoo_account = self.env['account.account'].sudo().search(
                                            [('coa_id', '=', quickbook_account.id)])
                                        if not odoo_account:
                                            odoo_account = self.env['account.account'].sudo().search(
                                                [('coa_id', '=', quickbook_account.id)])[0].id
                                if 'TaxCodeRef' in item['SalesItemLineDetail']:
                                    if item['SalesItemLineDetail']['TaxCodeRef']['value'] == 'TAX':
                                        if 'TaxLine' in credit_memo['TxnTaxDetail']:
                                            for tax in credit_memo['TxnTaxDetail']['TaxLine']:
                                                quickbook_item_tax_id = self.env['taxes.settings'].sudo().search(
                                                    [('tax_id', '=', tax['TaxLineDetail']['TaxRateRef']['value'])]).id
                                                item_tax_id = self.env['account.tax'].sudo().search(
                                                    [('tax_id', '=', quickbook_item_tax_id),
                                                     ('type_tax_use', '=', 'sale')]).id
                                                if item_tax_id:
                                                    taxes.append(item_tax_id)
                                if 'UnitPrice' in item['SalesItemLineDetail']:
                                    price = item['SalesItemLineDetail']['UnitPrice']
                                elif 'MarkupInfo' in item['SalesItemLineDetail']:
                                    price = item['SalesItemLineDetail']['MarkupInfo']['Value']
                                line_vals.append((0, 0, {
                                    'account_id': odoo_account,
                                    'product_id': odoo_product_product.id,
                                    'discount': dicount,
                                    "quantity": item['SalesItemLineDetail']['Qty'] if 'Qty' in item[
                                        'SalesItemLineDetail'] else 1,
                                    'price_unit': price,
                                    'tax_ids': [[6, 0, taxes]]
                                }))
                            elif item['DetailType'] == 'DiscountLineDetail':
                                pass
                            elif item['DetailType'] == 'SubTotalLineDetail':
                                pass
                        self.env['account.move'].sudo().create({
                            'quickbook_invoice_id': credit_memo['Id'],
                            'name': credit_memo['DocNumber'] if 'DocNumber' in credit_memo else "",
                            'partner_id': invoice_partner.id,
                            'currency_id': currency,
                            'move_type': 'out_refund',
                            # 'journal_id': journal_id,
                            'invoice_date': credit_memo['TxnDate'] if 'TxnDate' in credit_memo else date,
                            'invoice_line_ids': line_vals,
                        })
                        self.env.cr.commit()
                        if 'DocNumber' in credit_memo:
                            _logger.info("successfully Created Credit Memo: " + credit_memo[
                                'DocNumber'] + " with Credit Memo ID: " + credit_memo['Id'])
                        else:
                            _logger.info("successfully Created Credit Memo with ID: " + credit_memo['Id'])
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_vendor_credit(self, id=None):
        try:
            odoo_account = ''
            odoo_product_product = ''
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from vendorcredit where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from vendorcredit&minorversion=62'
            response = requests.get(url=url,
                                    headers={
                                        'Authorization': "Bearer " + user.access_token,
                                        'Accept': 'application/json'})
            if response.status_code == 200:
                quickbook_vendor_credits = json.loads(response.text)
                if not 'VendorCredit' in quickbook_vendor_credits['QueryResponse']:
                    raise ValidationError("No VendorCredit exists in QuickBooks to be imported at this time.")
                for quickbook_vendor_credit in quickbook_vendor_credits['QueryResponse']['VendorCredit']:
                    quickbook_vendor_credit_redundency_check = self.env['account.move'].sudo().search(
                        [('quickbook_invoice_id', '=', quickbook_vendor_credit['Id'])])
                    if quickbook_vendor_credit_redundency_check:
                        pass
                    else:
                        bill_partner = self.env['res.partner'].sudo().search(
                            [('quickbook_contact_id', '=', quickbook_vendor_credit['VendorRef']['value'])])
                        if not bill_partner:
                            result = self.env['default.functions'].checkquickbookredundency("Vendor", "Id",
                                                                                            quickbook_vendor_credit[
                                                                                                'VendorRef']['value'])
                            if 'Vendor' in result['QueryResponse']:
                                bill_partner = self.env['res.partner'].sudo().search(
                                    [('name', '=', result['QueryResponse']['Vendor'][0]['DisplayName'])])
                                if not bill_partner:
                                    self.env['res.config.settings'].import_customer(
                                        quickbook_vendor_credit['VendorRef']['value'])
                                    bill_partner = self.env['res.partner'].sudo().search(
                                        [('quickbook_contact_id', '=', quickbook_vendor_credit['VendorRef']['value'])])
                        line_vals = []
                        for item in quickbook_vendor_credit['Line']:
                            if 'AccountBasedExpenseLineDetail' in item:
                                odoo_product = self.env['product.template'].sudo().search([('name', '=', 'Expenses')])
                                if odoo_product:
                                    odoo_product_product = self.env['product.product'].sudo().search(
                                        [('product_tmpl_id', '=', odoo_product.id)])
                                if 'AccountRef' in item['AccountBasedExpenseLineDetail']:
                                    quickbook_account = self.env['coa.settings'].sudo().search([('account_id', '=',
                                                                                                 item[
                                                                                                     'AccountBasedExpenseLineDetail'][
                                                                                                     'AccountRef'][
                                                                                                     'value'])])
                                    if quickbook_account:
                                        odoo_account = self.env['account.account'].sudo().search(
                                            [('coa_id', '=', quickbook_account.id)])
                                        if odoo_account:
                                            odoo_account = self.env['account.account'].sudo().search(
                                                [('coa_id', '=', quickbook_account.id)])[0].id
                                line_vals.append((0, 0, {
                                    'account_id': odoo_account,
                                    'product_id': odoo_product_product.id,
                                    "quantity": 1,
                                    'price_unit': item['Amount'],
                                    # 'tax_ids': [[6, 0, odoo_taxes]]
                                }))
                            elif 'ItemBasedExpenseLineDetail' in item:
                                odoo_product = self.env['product.template'].sudo().search([('quickbook_product_id', '=',
                                                                                            item[
                                                                                                'ItemBasedExpenseLineDetail'][
                                                                                                'ItemRef']['value'])])
                                if not odoo_product:
                                    result = self.env['default.functions'].checkquickbookredundency("Item", "Id", item[
                                        'ItemBasedExpenseLineDetail']['ItemRef']['value'])
                                    if 'Item' in result['QueryResponse']:
                                        odoo_product = self.env['product.template'].sudo().search(
                                            [('name', '=', result['QueryResponse']['Item'][0]['Name'])])
                                        if not odoo_product:
                                            self.env['res.config.settings'].import_items(
                                                item['ItemBasedExpenseLineDetail']['ItemRef']['value'])
                                            odoo_product = self.env['product.template'].sudo().search([(
                                                'quickbook_product_id',
                                                '=', item[
                                                    'ItemBasedExpenseLineDetail'][
                                                    'ItemRef'][
                                                    'value'])])
                                if odoo_product:
                                    odoo_product_product = self.env['product.product'].sudo().search(
                                        [('product_tmpl_id', '=', odoo_product.id)])
                                if 'AccountRef' in item['ItemBasedExpenseLineDetail']:
                                    quickbook_account = self.env['coa.settings'].sudo().search([('account_id', '=',
                                                                                                 item[
                                                                                                     'AccountBasedExpenseLineDetail'][
                                                                                                     'AccountRef'][
                                                                                                     'value'])])
                                    if quickbook_account:
                                        odoo_account = self.env['account.account'].sudo().search(
                                            [('coa_id', '=', quickbook_account.id)])
                                        if odoo_account:
                                            odoo_account = self.env['account.account'].sudo().search(
                                                [('coa_id', '=', quickbook_account.id)])[0].id
                                line_vals.append((0, 0, {
                                    'account_id': odoo_account,
                                    'product_id': odoo_product_product.id,
                                    "quantity": item['ItemBasedExpenseLineDetail']['Qty'] if 'Qty' in item[
                                        'ItemBasedExpenseLineDetail'] else None,
                                    'price_unit': item['ItemBasedExpenseLineDetail']['UnitPrice'] if 'UnitPrice' in
                                                                                                     item[
                                                                                                         'ItemBasedExpenseLineDetail'] else None,
                                }))
                        self.env['account.move'].sudo().create({
                            'quickbook_invoice_id': quickbook_vendor_credit['Id'],
                            'name': quickbook_vendor_credit[
                                'DocNumber'] if 'DocNumber' in quickbook_vendor_credit else None,
                            'partner_id': bill_partner.id,
                            'move_type': 'in_refund',
                            # "invoice_date": quickbook_vendor_credit['DueDate'],
                            'invoice_line_ids': line_vals,
                        })
                        self.env.cr.commit()
                        if 'DocNumber' in quickbook_vendor_credit:
                            _logger.info("successfully Created Vendor Refund: " + quickbook_vendor_credit[
                                'DocNumber'] + " with Vendor Refund ID: " + quickbook_vendor_credit['Id'])
                        else:
                            _logger.info("successfully Created Vendor Refund with ID: " + quickbook_vendor_credit['Id'])
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def reconcile_action(self, id=None):
        moves = self.env['account.move'].sudo().search([])
        for move in moves:
            if move.payment_state == 'not_paid':
                move.reconcile()

    def import_payment(self, id=None):
        try:
            payment_partner = ""
            partner_type = ""
            move_id = ''
            payment_type = ''
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from Payment where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from Payment&minorversion=62'
            response = requests.get(
                url=url, headers={
                    'Accept': 'application/json',
                    'Authorization': 'Bearer ' + user.access_token
                })
            if response.status_code == 200:
                quickbook_terms_response = json.loads(response.text)
                for quickbook_term in quickbook_terms_response['QueryResponse']['Payment']:
                    term_redundancy_check = self.env['account.payment'].sudo().search(
                        [('quickbook_payment_id', '=', quickbook_term['Id'])])

                    for payemt_line in quickbook_term['Line']:
                        if 'CustomerRef' in quickbook_term:
                            payment_partner = self.env['res.partner'].sudo().search(
                                [('quickbook_contact_id', '=', quickbook_term['CustomerRef']['value'])])
                            if not payment_partner:
                                result = self.env['default.functions'].checkquickbookredundency("Customer", "Id",
                                                                                                quickbook_term[
                                                                                                    'CustomerRef'][
                                                                                                    'value'])
                                if 'Customer' in result['QueryResponse']:
                                    payment_partner = self.env['res.partner'].sudo().search(
                                        [('name', '=', result['QueryResponse']['Customer'][0]['DisplayName'])])
                                    if not payment_partner:
                                        self.env['res.config.settings'].import_customer(
                                            quickbook_term['CustomerRef']['value'])
                                        payment_partner = self.env['res.partner'].sudo().search(
                                            [('quickbook_contact_id', '=', quickbook_term['CustomerRef']['Value'])])
                        journal_id = self.env['account.journal'].sudo().search([('name', '=', 'Cash')]).id

                        if 'LinkedTxn' in payemt_line:
                            move_id = self.env['account.move'].sudo().search(
                                [('quickbook_invoice_id', '=', payemt_line['LinkedTxn'][0]['TxnId'])])
                        if payment_partner.customer_rank >= 1:
                            partner_type = 'customer'
                        if payemt_line['LinkedTxn'][0]['TxnType'] == 'Invoice':
                            payment_type = 'inbound'
                        if payemt_line['LinkedTxn'][0]['TxnType'] == 'CreditMemo':
                            payment_type = 'outbound'
                        odoo_payment = self.env['account.payment'].search([('quickbook_payment_id', '=', quickbook_term['Id'])])
                        if not odoo_payment:
                            pay = self.env['account.payment'].sudo().create({
                                'journal_id': journal_id,
                                # 'name': None,
                                # 'move_id': move_id.id if move_id else None,
                                'partner_id': payment_partner.id,
                                'quickbook_payment_id': quickbook_term['Id'],
                                'partner_type': partner_type,
                                'payment_type': payment_type,
                                'amount': payemt_line['Amount'],
                                'ref': move_id.name if move_id else None,
                            })
                            pay.action_post()
                            self.env.cr.commit()
                            _logger.info("successfully Created Payment Term : " + quickbook_term['Id'])
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def import_data(self):
        try:
            IrConfigParameter = self.env['ir.config_parameter'].sudo()
            customer_check = IrConfigParameter.get_param('odoo_quickbook.customer_check')
            vendor_check = IrConfigParameter.get_param('odoo_quickbook.vendor_check')
            item_check = IrConfigParameter.get_param('odoo_quickbook.item_check')
            purchase_order_check = IrConfigParameter.get_param('odoo_quickbook.purchase_order_check')
            sale_order_check = IrConfigParameter.get_param('odoo_quickbook.sale_order_check')
            bill_check = IrConfigParameter.get_param('odoo_quickbook.bill_check')
            invoice_check = IrConfigParameter.get_param('odoo_quickbook.invoice_check')
            credit_memo_check = IrConfigParameter.get_param('odoo_quickbook.credit_memo_check')
            vendor_refund_check = IrConfigParameter.get_param('odoo_quickbook.vendor_refund_check')
            customer_payment_check = IrConfigParameter.get_param('odoo_quickbook.customer_payment_check')
            vendor_bill_payment = IrConfigParameter.get_param('odoo_quickbook.vendor_bill_payment')
            payment_method_check = IrConfigParameter.get_param('odoo_quickbook.payment_method_check')
            reconcile_check = IrConfigParameter.get_param('odoo_quickbook.reconcile_check')
            if payment_method_check:
                self.import_payment_method()
            if customer_check:
                self.import_customer()
            if vendor_check:
                self.import_vendors()
            if item_check:
                self.import_items()
            if purchase_order_check:
                self.import_purchase_order()
            if sale_order_check:
                self.import_sale_order()
            if bill_check:
                self.import_bills()
            if invoice_check:
                self.import_invoices()
            if credit_memo_check:
                self.import_credit_memo()
            if vendor_refund_check:
                self.import_vendor_credit()
            if customer_payment_check:
                self.import_payment()
            if vendor_bill_payment:
                self.import_vendor_payment()
            if reconcile_check:
                self.reconcile_action()
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def update_items(self, id=None):
        try:
            odoo_expense_account = ''
            odoo_type = ''
            odoo_income_account = ''
            odoo_inventory_account = ''
            ExpenseAccountRef = ''
            IncomeAccountRef = ''
            AssetAccountRef = ''
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from Item where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from Item&minorversion=62'
            response = requests.get(url=url, headers={
                'Authorization': "Bearer " + user.access_token,
                'Accept': 'application/json',
            })
            if response.status_code == 200:
                quickbook_items = json.loads(response.text)
                for quickbook_item in quickbook_items['QueryResponse']['Item']:
                    item_redundecy_check = self.env['product.template'].sudo().search(
                        [('quickbook_product_id', '=', quickbook_item['Id'])])
                    if item_redundecy_check:
                        if 'ExpenseAccountRef' in quickbook_item:
                            ExpenseAccountRef = self.env['coa.settings'].sudo().search(
                                [('account_id', '=', quickbook_item['ExpenseAccountRef']['value'])]).id
                        if 'IncomeAccountRef' in quickbook_item:
                            IncomeAccountRef = self.env['coa.settings'].sudo().search(
                                [('account_id', '=', quickbook_item['IncomeAccountRef']['value'])]).id
                        if 'AssetAccountRef' in quickbook_item:
                            AssetAccountRef = self.env['coa.settings'].sudo().search(
                                [('account_id', '=', quickbook_item['AssetAccountRef']['value'])]).id
                        if ExpenseAccountRef:
                            odoo_expense_account = self.env['account.account'].sudo().search(
                                [('coa_id', '=', ExpenseAccountRef)]).id
                        if IncomeAccountRef:
                            odoo_income_account = self.env['account.account'].sudo().search(
                                [('coa_id', '=', IncomeAccountRef)]).id
                        if AssetAccountRef:
                            odoo_inventory_account = self.env['account.account'].sudo().search(
                                [('coa_id', '=', AssetAccountRef)]).id
                        if quickbook_item['Type'] == 'Service':
                            odoo_type = 'service'
                        if quickbook_item['Type'] == 'Inventory':
                            odoo_type = 'consu'
                        item_redundecy_check.write({
                            'quickbook_product_id': quickbook_item['Id'],
                            'description': quickbook_item['Description'] if 'Description' in quickbook_item else None,
                            'list_price': quickbook_item['UnitPrice'] if 'UnitPrice' in quickbook_item else None,
                            'property_account_expense_id': odoo_expense_account if odoo_expense_account else None,
                            'standard_price': quickbook_item[
                                'PurchaseCost'] if 'PurchaseCost' in quickbook_item else None,
                            'property_account_income_id': odoo_income_account if odoo_income_account else None,
                            'name': quickbook_item['Name'],
                            'type': odoo_type,
                            'property_account_creditor_price_difference': odoo_inventory_account if odoo_inventory_account else None,
                        })
                        self.env.cr.commit()
                        _logger.info("successfully Updated Item: " + quickbook_item['Name'] + " with  Item ID: " +
                                     quickbook_item['Id'])
                    else:
                        _logger.info("Product not found against id: " + quickbook_item['Id'])
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def update_taxes(self, id=None):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from TaxRate where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from TaxRate&minorversion=62'
            response = requests.get(url=url, headers={
                'Authorization': "Bearer " + user.access_token,
                'Accept': 'application/json'})
            if response.status_code == 200:
                quickbook_tax_rates_response = json.loads(response.text)
                for quickbook_tax_rate in quickbook_tax_rates_response['QueryResponse']['TaxRate']:
                    tax_redundancy_check = self.env['taxes.settings'].sudo().search(
                        [('tax_id', '=', quickbook_tax_rate['Id'])])
                    if tax_redundancy_check:
                        agency_id = self.env['taxagency.settings'].sudo().search(
                            [('agency_id', '=', quickbook_tax_rate['AgencyRef']['value'])])
                        tax_redundancy_check.write({
                            'tax_type': quickbook_tax_rate['Description'],
                            'name': quickbook_tax_rate['Name'],
                            'effective_rate': quickbook_tax_rate[
                                'RateValue'] if 'RateValue' in quickbook_tax_rate else None,
                            'status': quickbook_tax_rate['Active'],
                            'tax_id': quickbook_tax_rate['Id'],
                            'tax_agency_id': agency_id.id,
                        })
                        self.env.cr.commit()
                        _logger.info("successfully Updated Tax Agency: " + quickbook_tax_rate['Name'])
                    else:
                        _logger.info("Tax not found: " + quickbook_tax_rate['Name'])

            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def update_sale_order(self, id=None):
        try:

            odoo_product_product = ''
            odoo_taxes = ''
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select * from SalesReceipt where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from SalesReceipt&minorversion=62'
            response = requests.get(url=url,
                                    headers={
                                        'Authorization': "Bearer " + user.access_token,
                                        'Accept': 'application/json'})
            if response.status_code == 200:
                quickbook_sales_orders = json.loads(response.text)
                for quickbook_sale_order in quickbook_sales_orders['QueryResponse']['SalesReceipt']:
                    dicount = 0
                    sale_order_redundancy_check = self.env['sale.order'].sudo().search(
                        [('quickbook_sale_order_id', '=', quickbook_sale_order['Id'])])
                    if sale_order_redundancy_check:
                        for line_item in sale_order_redundancy_check.order_line:
                            line_item.unlink()
                        if 'CustomerRef' in quickbook_sale_order:
                            sale_order_partner = self.env['res.partner'].sudo().search(
                                [('quickbook_contact_id', '=', quickbook_sale_order['CustomerRef']['value'])])
                        else:
                            sale_order_partner = self.env['res.partner'].sudo().search([('name', '=', 'Administrator')])
                        line_vals = []
                        for item in quickbook_sale_order['Line']:
                            taxes = []
                            if item['DetailType'] == 'SalesItemLineDetail':
                                for discount_loop in quickbook_sale_order['Line']:
                                    if discount_loop['DetailType'] == 'DiscountLineDetail':
                                        dicount = discount_loop['DiscountLineDetail']['DiscountPercent']
                                odoo_product = self.env['product.template'].sudo().search(
                                    [('quickbook_product_id', '=', item['SalesItemLineDetail']['ItemRef']['value'])])
                                if odoo_product:
                                    odoo_product_product = self.env['product.product'].sudo().search(
                                        [('product_tmpl_id', '=', odoo_product.id)])
                                if 'TaxCodeRef' in item['SalesItemLineDetail']:
                                    if item['SalesItemLineDetail']['TaxCodeRef']['value'] == 'TAX':
                                        if 'TaxLine' in quickbook_sale_order['TxnTaxDetail']:
                                            for tax in quickbook_sale_order['TxnTaxDetail']['TaxLine']:
                                                quickbook_item_tax_id = self.env['taxes.settings'].sudo().search(
                                                    [('tax_id', '=', tax['TaxLineDetail']['TaxRateRef']['value'])]).id
                                                item_tax_id = self.env['account.tax'].sudo().search(
                                                    [('tax_id', '=', quickbook_item_tax_id),
                                                     ('type_tax_use', '=', 'sale')]).id
                                                if item_tax_id:
                                                    taxes.append(item_tax_id)
                                if 'UnitPrice' in item['SalesItemLineDetail']:
                                    price = item['SalesItemLineDetail']['UnitPrice']
                                elif 'MarkupInfo' in item['SalesItemLineDetail']:
                                    price = item['SalesItemLineDetail']['MarkupInfo']['Value']
                                line_vals.append((0, 0, {
                                    'product_id': odoo_product_product.id,
                                    "product_uom_qty": item['SalesItemLineDetail']['Qty'] if 'Qty' in item[
                                        'SalesItemLineDetail'] else 1,
                                    'discount': dicount,
                                    'price_unit': price,
                                    'tax_id': [[6, 0, taxes]]
                                }))
                            elif item['DetailType'] == 'DiscountLineDetail':
                                pass
                        sale_order_redundancy_check.write({
                            'quickbook_sale_order_id': quickbook_sale_order['Id'],
                            'state': 'draft',
                            'name': quickbook_sale_order['DocNumber'],
                            'partner_id': sale_order_partner.id,
                            'date_order': quickbook_sale_order[
                                'TxnDate'] if 'TxnDate' in quickbook_sale_order else None,
                            'order_line': line_vals,
                        })
                        self.env.cr.commit()
                        if 'DocNumber' in quickbook_sale_order:
                            _logger.info("successfully Updated Sale Order: " + quickbook_sale_order[
                                'DocNumber'] + " with Sale Order ID: " + quickbook_sale_order['Id'])
                        else:
                            _logger.info("successfully updated Sale Order with ID: " + quickbook_sale_order['Id'])
                    else:
                        _logger.info(" Sale Order with ID: " + quickbook_sale_order['Id'] + " Not found")
            else:
                _logger.info(response.text)
        except Exception as e:
            raise ValidationError(_(str(e)))

    def update_purchase_order(self, id=None):
        try:
            odoo_product_product = ''
            odoo_taxes = ''
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select *from PurchaseOrder where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select *from PurchaseOrder&minorversion=62'
            response = requests.get(url, headers={
                'Authorization': "Bearer " + user.access_token,
                'Accept': 'application/json'})
            if response.status_code == 200:
                quickbook_purchase_orders = json.loads(response.text)
                for quickbook_purchase_order in quickbook_purchase_orders['QueryResponse']['PurchaseOrder']:
                    purchase_order_redundecy_check = self.env['purchase.order'].sudo().search(
                        [('quickbook_purchase_order_id', '=', quickbook_purchase_order['Id'])])
                    if purchase_order_redundecy_check:
                        for line_item in purchase_order_redundecy_check.order_line:
                            line_item.unlink()
                        purchase_order_partner = self.env['res.partner'].sudo().search(
                            [('quickbook_contact_id', '=', quickbook_purchase_order['VendorRef']['value'])])
                        line_vals = []
                        for item in quickbook_purchase_order['Line']:
                            if 'AccountBasedExpenseLineDetail' in item:
                                odoo_product = self.env['product.template'].sudo().search([('name', '=', 'Expenses')])
                                if odoo_product:
                                    odoo_product_product = self.env['product.product'].sudo().search(
                                        [('product_tmpl_id', '=', odoo_product.id)])
                                    line_vals.append((0, 0, {
                                        'product_id': odoo_product_product.id,
                                        "product_qty": 1,
                                        'price_unit': item['Amount'],
                                    }))
                            if 'ItemBasedExpenseLineDetail' in item:
                                odoo_product = self.env['product.template'].sudo().search([('quickbook_product_id', '=',
                                                                                            item[
                                                                                                'ItemBasedExpenseLineDetail'][
                                                                                                'ItemRef']['value'])])
                                if odoo_product:
                                    odoo_product_product = self.env['product.product'].sudo().search(
                                        [('product_tmpl_id', '=', odoo_product.id)])
                                    line_vals.append((0, 0, {
                                        'product_id': odoo_product_product.id,
                                        "product_qty": item['ItemBasedExpenseLineDetail']['Qty'] if 'Qty' in item[
                                            'ItemBasedExpenseLineDetail'] else 1,
                                        'price_unit': item['ItemBasedExpenseLineDetail']['UnitPrice'] if 'UnitPrice' in
                                                                                                         item[
                                                                                                             'ItemBasedExpenseLineDetail'] else None,
                                    }))
                        if quickbook_purchase_order['POStatus'] == 'Open':
                            state = 'draft'
                        if quickbook_purchase_order['POStatus'] == 'Closed':
                            state = 'purchase'
                        purchase_order_redundecy_check.write({
                            'quickbook_purchase_order_id': quickbook_purchase_order['Id'],
                            'state': state,
                            'name': quickbook_purchase_order['DocNumber'],
                            'partner_id': purchase_order_partner.id,
                            'date_order': purchase_order_partner[
                                'TxnDate'] if 'TxnDate' in purchase_order_partner else None,
                            'order_line': line_vals,
                        })
                        self.env.cr.commit()
                        if 'DocNumber' in quickbook_purchase_order:
                            _logger.info("successfully Updated Purchase Order: " + quickbook_purchase_order[
                                'DocNumber'] + " with Purchase Order ID: " + quickbook_purchase_order['Id'])
                        else:
                            _logger.info(
                                "successfully updated Purchase Order with ID: " + quickbook_purchase_order['Id'])
                    else:
                        _logger.info(" Sale Order with ID: " + quickbook_purchase_order['Id'] + " Not found")

            else:
                _logger.info(response.text)
        except Exception as e:
            raise ValidationError(_(str(e)))

    def update_customer(self, id=None):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select *from Customer where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from Customer&minorversion=62'
            response = requests.get(url=url, headers={
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + user.access_token
            })
            if response.status_code == 200:
                quickbook_customers = json.loads(response.text)
                for quickbook_customer in quickbook_customers['QueryResponse']['Customer']:
                    contact_parent_id = ""
                    contact_redundancy_check = self.env['res.partner'].sudo().search(
                        [('quickbook_contact_id', '=', quickbook_customer['Id'])])
                    if contact_redundancy_check:
                        if "ParentRef" in quickbook_customer:
                            contact_parent_id = self.env['res.partner'].sudo().search(
                                [('quickbook_contact_id', '=', quickbook_customer['ParentRef']['value'])]).id
                        contact_redundancy_check.write({
                            'quickbook_contact_id': quickbook_customer['Id'],
                            'active': quickbook_customer['Active'],
                            'phone': quickbook_customer['PrimaryPhone'][
                                'FreeFormNumber'] if 'PrimaryPhone' in quickbook_customer else None,
                            # 'mobile': mobile_number,
                            'name': quickbook_customer['DisplayName'],
                            'email': quickbook_customer['PrimaryEmailAddr'][
                                'Address'] if 'PrimaryEmailAddr' in quickbook_customer else None,
                            'parent_id': contact_parent_id if contact_parent_id else None,
                            'customer_rank': 1,
                        })
                        childids = contact_redundancy_check.child_ids
                        if childids:
                            for child in childids:
                                if child.type == "invoice":
                                    if "BillAddr" in quickbook_customer:
                                        country_id = ''
                                        state_id = ''
                                        if 'Country' in quickbook_customer["BillAddr"]:
                                            country_id = self.env['res.country'].sudo().search(
                                                [('name', '=', quickbook_customer["BillAddr"]['Country'])]).id
                                        if "CountrySubDivisionCode" in quickbook_customer["BillAddr"]:
                                            state_id = self.env['res.country.state'].sudo().search([('code', '=',
                                                                                                     quickbook_customer[
                                                                                                         "BillAddr"][
                                                                                                         "CountrySubDivisionCode"]),
                                                                                                    ('country_id', '=',
                                                                                                     country_id)]).id
                                        child.write({
                                            'city': quickbook_customer["BillAddr"]["City"] if "City" in
                                                                                              quickbook_customer[
                                                                                                  "BillAddr"] else None,
                                            'street': quickbook_customer["BillAddr"]['Line1'] if "Line1" in
                                                                                                 quickbook_customer[
                                                                                                     "BillAddr"] else None,
                                            'street2': quickbook_customer["BillAddr"]['Line2'] if "Line2" in
                                                                                                  quickbook_customer[
                                                                                                      "BillAddr"] else None,
                                            'country_id': country_id if country_id else None,
                                            'type': 'invoice',
                                            'state_id': state_id if state_id else None,
                                            'zip': quickbook_customer["BillAddr"]["PostalCode"] if "PostalCode" in
                                                                                                   quickbook_customer[
                                                                                                       "BillAddr"] else None,
                                        })
                                elif child.type == "delivery":
                                    if "ShipAddr" in quickbook_customer:
                                        country_id = ''
                                        state_id = ''
                                        if 'Country' in quickbook_customer["ShipAddr"]:
                                            country_id = self.env['res.country'].sudo().search(
                                                [('name', '=', quickbook_customer["ShipAddr"]['Country'])]).id
                                        if "CountrySubDivisionCode" in quickbook_customer["ShipAddr"]:
                                            state_id = self.env['res.country.state'].sudo().search([('name', '=',
                                                                                                     quickbook_customer[
                                                                                                         "ShipAddr"][
                                                                                                         "CountrySubDivisionCode"]),
                                                                                                    ('country_id', '=',
                                                                                                     country_id)]).id
                                        child.write({
                                            'city': quickbook_customer["ShipAddr"]["City"] if "City" in
                                                                                              quickbook_customer[
                                                                                                  "ShipAddr"] else None,
                                            'street': quickbook_customer["ShipAddr"]['Line1'] if "Line1" in
                                                                                                 quickbook_customer[
                                                                                                     "ShipAddr"] else None,
                                            'street2': quickbook_customer["ShipAddr"]['Line2'] if "Line2" in
                                                                                                  quickbook_customer[
                                                                                                      "ShipAddr"] else None,
                                            'country_id': country_id if country_id else None,
                                            'type': 'delivery',
                                            'state_id': state_id if state_id else None,
                                            'zip': quickbook_customer["ShipAddr"]["PostalCode"] if "PostalCode" in
                                                                                                   quickbook_customer[
                                                                                                       "ShipAddr"] else None,
                                        })
                                    self.env.cr.commit()
                        _logger.info(
                            "successfully Created : " + quickbook_customer['DisplayName'] + " with Contact ID: " +
                            quickbook_customer['Id'])
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def update_vendor(self, id=None):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if not user:
                user_check = self.env['res.users'].sudo().search([('access_token', '!=', '')])
                if user_check:
                    user = self.env['res.users'].sudo().search([('access_token', '!=', '')])[0]
                else:
                    _logger.info("No user have quickbook credentials ! Please specify the credentials in setting")
                    raise ValidationError(
                        ("No user have quickbook credentials ! Please specify the credentials in setting"))
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if id:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + "/query?query=select *from Vendor where Id='" + str(
                    id) + "'&minorversion=62"
            else:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(
                    select_url) + '/v3/company/' + user.quickbook_realm_id + '/query?query=select * from Vendor&minorversion=62'
            response = requests.get(url=url, headers={
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + user.access_token
            })
            if response.status_code == 200:
                quickbook_vendors = json.loads(response.text)
                for quickbook_vendor in quickbook_vendors['QueryResponse']['Vendor']:
                    contact_parent_id = ""
                    contact_redundancy_check = self.env['res.partner'].sudo().search(
                        [('quickbook_contact_id', '=', quickbook_vendor['Id'])])
                    if contact_redundancy_check:
                        if "ParentRef" in quickbook_vendor:
                            contact_parent_id = self.env['res.partner'].sudo().search(
                                [('quickbook_contact_id', '=', quickbook_vendor['ParentRef']['value'])]).id
                        contact_redundancy_check.write({
                            'quickbook_contact_id': quickbook_vendor['Id'],
                            'active': quickbook_vendor['Active'],
                            'phone': quickbook_vendor['PrimaryPhone'][
                                'FreeFormNumber'] if 'PrimaryPhone' in quickbook_vendor else None,
                            # 'mobile': mobile_number,
                            'name': quickbook_vendor['DisplayName'],
                            'email': quickbook_vendor['PrimaryEmailAddr'][
                                'Address'] if 'PrimaryEmailAddr' in quickbook_vendor else None,
                            'parent_id': contact_parent_id if contact_parent_id else None,
                            'customer_rank': 1,
                        })
                        childids = contact_redundancy_check.child_ids
                        if childids:
                            for child in childids:
                                if child.type == "invoice":
                                    if "BillAddr" in quickbook_vendor:
                                        country_id = ''
                                        state_id = ''
                                        if 'Country' in quickbook_vendor["BillAddr"]:
                                            country_id = self.env['res.country'].sudo().search(
                                                [('name', '=', quickbook_vendor["BillAddr"]['Country'])]).id
                                        if "CountrySubDivisionCode" in quickbook_vendor["BillAddr"]:
                                            state_id = self.env['res.country.state'].sudo().search(
                                                [('code', '=', quickbook_vendor["BillAddr"]["CountrySubDivisionCode"]),
                                                 ('country_id', '=', country_id)]).id
                                        child.write({
                                            'city': quickbook_vendor["BillAddr"]["City"] if "City" in quickbook_vendor[
                                                "BillAddr"] else None,
                                            'street': quickbook_vendor["BillAddr"]['Line1'] if "Line1" in
                                                                                               quickbook_vendor[
                                                                                                   "BillAddr"] else None,
                                            'street2': quickbook_vendor["BillAddr"]['Line2'] if "Line2" in
                                                                                                quickbook_vendor[
                                                                                                    "BillAddr"] else None,
                                            'country_id': country_id if country_id else None,
                                            'type': 'invoice',
                                            'state_id': state_id if state_id else None,
                                            'zip': quickbook_vendor["BillAddr"]["PostalCode"] if "PostalCode" in
                                                                                                 quickbook_vendor[
                                                                                                     "BillAddr"] else None,
                                        })
                                if child.type == "invoice":
                                    if "ShipAddr" in quickbook_vendor:
                                        country_id = ''
                                        state_id = ''
                                        if 'Country' in quickbook_vendor["ShipAddr"]:
                                            country_id = self.env['res.country'].sudo().search(
                                                [('name', '=', quickbook_vendor["ShipAddr"]['Country'])]).id
                                        if "CountrySubDivisionCode" in quickbook_vendor["ShipAddr"]:
                                            state_id = self.env['res.country.state'].sudo().search(
                                                [('name', '=', quickbook_vendor["ShipAddr"]["CountrySubDivisionCode"]),
                                                 ('country_id', '=', country_id)]).id
                                        child.write({
                                            'city': quickbook_vendor["ShipAddr"]["City"] if "City" in quickbook_vendor[
                                                "ShipAddr"] else None,
                                            'street': quickbook_vendor["ShipAddr"]['Line1'] if "Line1" in
                                                                                               quickbook_vendor[
                                                                                                   "ShipAddr"] else None,
                                            'street2': quickbook_vendor["ShipAddr"]['Line2'] if "Line2" in
                                                                                                quickbook_vendor[
                                                                                                    "ShipAddr"] else None,
                                            'country_id': country_id if country_id else None,
                                            'type': 'delivery',
                                            'state_id': state_id if state_id else None,
                                            'zip': quickbook_vendor["ShipAddr"]["PostalCode"] if "PostalCode" in
                                                                                                 quickbook_vendor[
                                                                                                     "ShipAddr"] else None,
                                        })
                                    self.env.cr.commit()
                        _logger.info(
                            "successfully Created : " + quickbook_vendor['DisplayName'] + " with Contact ID: " +
                            quickbook_vendor['Id'])
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))


class QuickbookExportContact(models.Model):
    _inherit = 'res.partner'

    def export_contacts(self, partner_id):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            if partner_id.customer_rank:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(select_url) + 'v3/company/' + user.quickbook_realm_id + '/customer'
                payload = {
                    "FullyQualifiedName": partner_id.name,
                    "PrimaryEmailAddr": {
                        "Address": partner_id.email if partner_id.email else None
                    },
                    "DisplayName": partner_id.name,
                    "PrimaryPhone": {
                        "FreeFormNumber": partner_id.phone if partner_id.phone else None
                    },
                    "CompanyName": partner_id.name,
                }
                header = {
                    'Authorization': 'Bearer ' + user.access_token,
                    'Content-Type': 'application/json',
                }
                response = requests.request("POST", url, data=json.dumps(payload), headers=header)
                if response.status_code == 200:
                    response_data = xmltodict.parse(response.text)
                    response_data_str_json = json.dumps(response_data)
                    response_data_json = json.loads(response_data_str_json)
                    partner_id.write({
                        'quickbook_contact_id': response_data_json['IntuitResponse']['Customer']['Id']
                    })
                    self.env.cr.commit()
            elif partner_id.supplier_rank:
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                url = str(select_url) + 'v3/company/' + user.quickbook_realm_id + '/vendor'
                payload = {
                    "FullyQualifiedName": partner_id.name,
                    "PrimaryEmailAddr": {
                        "Address": partner_id.email if partner_id.email else None
                    },
                    "DisplayName": partner_id.name,
                    "PrimaryPhone": {
                        "FreeFormNumber": partner_id.phone if partner_id.phone else None
                    },
                    "CompanyName": partner_id.name,
                }
                header = {
                    'Authorization': 'Bearer ' + user.access_token,
                    'Content-Type': 'application/json',
                }
                response = requests.request("POST", url, data=json.dumps(payload), headers=header)
                if response.status_code == 200:
                    response_data = xmltodict.parse(response.text)
                    response_data_str_json = json.dumps(response_data)
                    response_data_json = json.loads(response_data_str_json)
                    partner_id.write({
                        'quickbook_contact_id': response_data_json['IntuitResponse']['Vendor']['Id']
                    })
                    self.env.cr.commit()
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))


class QuickbookExportItem(models.Model):
    _inherit = 'product.template'

    def export_items(self, product):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            IrConfigParameter = request.env['ir.config_parameter'].sudo()
            select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
            url = str(select_url) + 'v3/company/' + user.quickbook_realm_id + '/item'
            payload = {
                "TrackQtyOnHand": False,
                "Name": product.name,
                "IncomeAccountRef": {
                    "name": "Sales of Product Income",
                    "value": "79"
                },
            }
            header = {
                'Authorization': 'Bearer ' + user.access_token,
                'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, data=json.dumps(payload), headers=header)
            if response.status_code == 200:
                response_data = xmltodict.parse(response.text)
                response_data_str_json = json.dumps(response_data)
                response_data_json = json.loads(response_data_str_json)
                product.write({
                    'quickbook_product_id': response_data_json['IntuitResponse']['Item']['Id']
                })
                self.env.cr.commit()
            else:
                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))


class QuickbookExportSaleOrder(models.Model):
    _inherit = 'sale.order'

    def export_sale_order(self):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            for sale_order in self:
                if sale_order.quickbook_sale_order_id:
                    result = self.env['default.functions'].checkquickbookredundency("salesreceipt", "id",
                                                                                    sale_order.quickbook_sale_order_id)
                    if result['QueryResponse']['SalesReceipt']:
                        raise ValidationError(("This salesreceipt has already Exported to Quickbook "))
                    else:
                        raise ValidationError(("Seems that the sale order has been deleted or modified"))
                else:
                    result = self.env['default.functions'].checkquickbookredundency("salesreceipt", "DocNumber",
                                                                                    sale_order.name)
                    if result['QueryResponse']:
                        sale_order.write({
                            'quickbook_sale_order_id': result['QueryResponse']['SalesReceipt'][0]['Id']
                        })
                        self.env.cr.commit()
                        raise ValidationError(("This salesreceipt has already been Exported"))
                    else:
                        if sale_order.partner_id.quickbook_contact_id:
                            pass
                        elif not sale_order.partner_id.quickbook_contact_id:
                            result = self.env['default.functions'].checkquickbookredundency("Customer", "DisplayName",
                                                                                            sale_order.partner_id.name)
                            if 'Customer' in result['QueryResponse']:
                                sale_order.partner_id.write({
                                    'quickbook_contact_id': result['QueryResponse']['Customer'][0]['Id'],
                                })
                                self.env.cr.commit()
                            elif 'Vendor' in result['QueryResponse']:
                                sale_order.partner_id.write({
                                    'quickbook_contact_id': result['QueryResponse']['Vendor'][0]['Id'],
                                })
                                self.env.cr.commit()
                            else:
                                self.env['res.partner'].export_contacts(sale_order.partner_id)
                        lineitems = self.env['default.functions'].getinvoicelinesitem(sale_order['order_line'], 2)
                        payload = {
                            "Line": lineitems,
                            "DocNumber": sale_order.name,
                            "CustomerRef": {
                                "name": sale_order.partner_id.name,
                                "value": sale_order.partner_id.quickbook_contact_id
                            },
                        }
                        header = {
                            'Authorization': 'Bearer ' + user.access_token,
                            'Content-Type': 'application/json',
                        }
                        IrConfigParameter = request.env['ir.config_parameter'].sudo()
                        select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                        url = str(
                            select_url) + 'v3/company/' + user.quickbook_realm_id + '/salesreceipt?minorversion=62'
                        response = requests.request("POST", url, data=json.dumps(payload), headers=header)
                        if response.status_code == 200:
                            response_data = xmltodict.parse(response.text)
                            response_data_str_json = json.dumps(response_data)
                            response_data_json = json.loads(response_data_str_json)
                            sale_order.write({
                                'quickbook_sale_order_id': response_data_json['IntuitResponse']['SalesReceipt']['Id']
                            })
                            self.env.cr.commit()
                        else:
                            _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))


class QuickbookExportPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def export_purchase_order(self):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            for purchase_order in self:
                if purchase_order.quickbook_purchase_order_id:
                    result = self.env['default.functions'].checkquickbookredundency("purchaseorder", "id",
                                                                                    purchase_order.quickbook_purchase_order_id)
                    if result['QueryResponse']['PurchaseOrder']:
                        raise ValidationError(("This Purchase Order has already Exported to Quickbook "))
                    else:
                        raise ValidationError(("Seems that the Purchase Order has been deleted or modified"))
                else:
                    result = self.env['default.functions'].checkquickbookredundency("purchaseorder", "DocNumber",
                                                                                    purchase_order.name)
                    if result['QueryResponse']:
                        purchase_order.write({
                            'quickbook_purchase_order_id': result['QueryResponse']['PurchaseOrder'][0]['Id']
                        })
                        self.env.cr.commit()
                        raise ValidationError(("This Purchase Order has already been Exported"))
                    else:
                        if purchase_order.partner_id.quickbook_contact_id:
                            pass
                        elif not purchase_order.partner_id.quickbook_contact_id:
                            result = self.env['default.functions'].checkquickbookredundency("vendor", "DisplayName",
                                                                                            purchase_order.partner_id.name)
                            if 'Customer' in result['QueryResponse']:
                                purchase_order.partner_id.write({
                                    'quickbook_contact_id': result['QueryResponse']['Customer'][0]['Id'],
                                })
                                self.env.cr.commit()
                            elif 'Vendor' in result['QueryResponse']:
                                purchase_order.partner_id.write({
                                    'quickbook_contact_id': result['QueryResponse']['Vendor'][0]['Id'],
                                })
                                self.env.cr.commit()
                            else:
                                self.env['res.partner'].export_contacts(purchase_order.partner_id)
                        lineitems = self.env['default.functions'].getinvoicelinesitem(purchase_order['order_line'], 1)
                        payload = {
                            "Line": lineitems,
                            "DocNumber": purchase_order.name,
                            "VendorRef": {
                                "name": purchase_order.partner_id.name,
                                "value": purchase_order.partner_id.quickbook_contact_id
                            },
                            "APAccountRef": {
                                "name": "Accounts Payable (A/P)",
                                "value": "33"
                            },
                        }
                        header = {
                            'Authorization': 'Bearer ' + user.access_token,
                            'Content-Type': 'application/json',
                        }
                        IrConfigParameter = request.env['ir.config_parameter'].sudo()
                        select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                        url = str(
                            select_url) + 'v3/company/' + user.quickbook_realm_id + '/purchaseorder?minorversion=62'
                        response = requests.request("POST", url, data=json.dumps(payload), headers=header)
                        if response.status_code == 200:
                            response_data = xmltodict.parse(response.text)
                            response_data_str_json = json.dumps(response_data)
                            response_data_json = json.loads(response_data_str_json)
                            purchase_order.write({
                                'quickbook_purchase_order_id': response_data_json['IntuitResponse']['PurchaseOrder'][
                                    'Id']
                            })
                            self.env.cr.commit()
                        else:
                            _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))


class QuickbookExportInvoice(models.Model):
    _inherit = 'account.move'

    def reconcile(self):
        for invoice_name in self:
            payments = self.env['account.payment'].sudo().search([('ref', '=', invoice_name.name)])
            for payment in payments:
                payment_ref = self.env['account.move.line'].search([('move_name', '=', payment.name)])
                index = len(payment_ref) - 1
                invoice_name.js_assign_outstanding_line(payment_ref[index].id)

    def export_invoice(self):
        try:
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            for invoice in self:
                if invoice['move_type'] == "out_invoice":
                    partner_endpoint = "Customer"
                    move_endpoint = 'invoice'
                    query_endpoint = 'Invoice'
                if invoice['move_type'] == "in_invoice":
                    partner_endpoint = "Vendor"
                    move_endpoint = 'bill'
                    query_endpoint = 'Bill'
                if invoice['move_type'] == "out_refund":
                    partner_endpoint = "Customer"
                    move_endpoint = 'creditmemo'
                    query_endpoint = 'CreditMemo'
                if invoice['move_type'] == "in_refund":
                    partner_endpoint = "Vendor"
                    move_endpoint = 'vendorcredit'
                    query_endpoint = 'VendorCredit'
                if invoice.quickbook_invoice_id:
                    result = self.env['default.functions'].checkquickbookredundency(move_endpoint, "id",
                                                                                    invoice.quickbook_invoice_id)
                    if result['QueryResponse']:
                        raise ValidationError(("This Account Move  already Exist in Quickbook "))
                else:
                    result = self.env['default.functions'].checkquickbookredundency(move_endpoint, "DocNumber",
                                                                                    invoice.name)
                    if result['QueryResponse']:
                        invoice.write({
                            'quickbook_invoice_id': result['QueryResponse'][query_endpoint][0]['Id']
                        })
                        self.env.cr.commit()
                        raise ValidationError(("This Invoice has already been Exported"))
                    else:
                        if invoice.partner_id.quickbook_contact_id:
                            pass
                        elif not invoice.partner_id.quickbook_contact_id:
                            result = self.env['default.functions'].checkquickbookredundency(partner_endpoint,
                                                                                            "DisplayName",
                                                                                            invoice.partner_id.name)
                            if partner_endpoint in result['QueryResponse']:
                                invoice.partner_id.write({
                                    'quickbook_contact_id': result['QueryResponse'][partner_endpoint][0]['Id'],
                                })
                                self.env.cr.commit()
                            else:
                                self.env['res.partner'].export_contacts(invoice.partner_id)
                        lineitems = self.env['default.functions'].getinvoicelinesitem(invoice['invoice_line_ids'], 0,
                                                                                      invoice['move_type'])
                        header = {
                            'Authorization': 'Bearer ' + user.access_token,
                            'Content-Type': 'application/json',
                        }
                        if invoice['move_type'] == "out_invoice":
                            payload = {
                                "DocNumber": invoice.name,
                                "Line": lineitems,
                                "CustomerRef": {
                                    "value": invoice.partner_id.quickbook_contact_id
                                }
                            }
                        if invoice['move_type'] == "in_invoice":
                            payload = {
                                "DocNumber": invoice.name,
                                "Line": lineitems,
                                "VendorRef": {
                                    "value": invoice.partner_id.quickbook_contact_id
                                }
                            }
                        if invoice['move_type'] == "out_refund":
                            payload = {
                                "DocNumber": invoice.name,
                                "Line": lineitems,
                                "CustomerRef": {
                                    "value": invoice.partner_id.quickbook_contact_id
                                }
                            }
                        if invoice['move_type'] == "in_refund":
                            payload = {
                                "DocNumber": invoice.name,
                                "Line": lineitems,
                                "VendorRef": {
                                    "value": invoice.partner_id.quickbook_contact_id
                                }
                            }
                        IrConfigParameter = request.env['ir.config_parameter'].sudo()
                        select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                        url = str(
                            select_url) + 'v3/company/' + user.quickbook_realm_id + '/' + move_endpoint + '?minorversion=62'
                        response = requests.request("POST", url, data=json.dumps(payload), headers=header)
                        if response.status_code == 200:
                            response_data = xmltodict.parse(response.text)
                            response_data_str_json = json.dumps(response_data)
                            response_data_json = json.loads(response_data_str_json)
                            invoice.write({
                                'quickbook_invoice_id': response_data_json['IntuitResponse'][query_endpoint]['Id']
                            })
                            self.env.cr.commit()
                        else:
                            _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))


class QuickbookExportPayments(models.Model):
    _inherit = 'account.payment'

    def export_payment(self):
        try:
            move_id = ''
            context = self._context
            current_uid = context.get('uid')
            user = self.env['res.users'].browse(current_uid)
            if user.access_token:
                self.env['default.functions'].check_refreshtoken()
            for payment in self:
                if payment.move_id.partner_id.customer_rank > 1:
                    IrConfigParameter = request.env['ir.config_parameter'].sudo()
                    select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                    url = str(select_url) + 'v3/company/' + user.quickbook_realm_id + '/payment'
                    if payment.quickbook_payment_id:
                        result = self.env['default.functions'].checkquickbookredundency("payment", "id",
                                                                                        payment.quickbook_payment_id)
                        if result['QueryResponse']['Payment']:
                            raise ValidationError(("This Payment already Exist to Quickbook "))
                        else:
                            raise ValidationError(("Seems that the sale order has been deleted or modified"))
                    else:
                        if payment.state == 'Draft':
                            raise ValidationError(
                                'You cannot export draft state payments please post it and then export')
                        else:
                            if payment.ref:
                                linked_move = self.env['account.move'].sudo().search([('name', '=', payment.ref)])
                                result = self.env['default.functions'].checkquickbookredundency("Invoice", "Id",
                                                                                                linked_move.quickbook_invoice_id)
                                if not result['QueryResponse']['Invoice']:
                                    raise ValidationError((
                                        "This Account Move is not present in QuickBooks kinldy export the invoice first"))
                                if linked_move:
                                    move_id = linked_move.quickbook_invoice_id
                                else:
                                    move_id = None
                            Payload = {
                                "SyncToken": "0",
                                "domain": "QBO",
                                "DepositToAccountRef": {
                                    "value": "4"
                                },
                                "UnappliedAmt": payment.amount,
                                "TxnDate": str(payment.date),
                                "TotalAmt": payment.amount,
                                "ProcessPayment": False,
                                "sparse": False,
                                "Line": [{
                                    'Amount': payment.amount,
                                    'LinkedTxn': [{
                                        'TxnId': move_id,
                                        'TxnType': 'Invoice',
                                    }]
                                }] if move_id else None,
                                "CustomerRef": {
                                    "name": payment.partner_id.name,
                                    "value": payment.partner_id.quickbook_contact_id
                                },
                            }
                            header = {
                                'Authorization': 'Bearer ' + user.access_token,
                                'Content-Type': 'application/json',
                            }
                            response = requests.request("POST", url, data=json.dumps(Payload), headers=header)
                            if response.status_code == 200:
                                response_data = xmltodict.parse(response.text)
                                response_data_str_json = json.dumps(response_data)
                                response_data_json = json.loads(response_data_str_json)
                                payment.write({
                                    'quickbook_payment_id': response_data_json['IntuitResponse']['Payment']['Id']
                                })
                                self.env.cr.commit()
                            else:
                                _logger.info(response.text)
                if payment.move_id.partner_id.supplier_rank > 1:
                    IrConfigParameter = request.env['ir.config_parameter'].sudo()
                    select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')
                    url = str(select_url) + 'v3/company/' + user.quickbook_realm_id + '/billpayment'
                    if payment.quickbook_payment_id:
                        result = self.env['default.functions'].checkquickbookredundency("billpayment", "id",
                                                                                        payment.quickbook_payment_id)
                        if result['QueryResponse']['Payment']:
                            raise ValidationError(("This Payment already Exist to Quickbook "))
                        else:
                            raise ValidationError(("Seems that the Payment has been deleted or modified"))
                    else:
                        if payment.state == 'Draft':
                            raise ValidationError(
                                'You cannot export draft state payments please post it and then export')
                        else:
                            if payment.ref:
                                linked_move = self.env['account.move'].sudo().search([('name', '=', payment.ref)])
                                result = self.env['default.functions'].checkquickbookredundency("Bill", "Id",
                                                                                                linked_move.quickbook_invoice_id)
                                if not result['QueryResponse']['Bill']:
                                    raise ValidationError((
                                        "This Account Move is not present in QuickBooks kinldy export the Linked Bill first"))
                                if linked_move:
                                    move_id = linked_move.quickbook_invoice_id
                                else:
                                    move_id = None
                            Payload = {
                                "SyncToken": "0",
                                "domain": "QBO",
                                "PayType": "Check",
                                "TxnDate": str(payment.date),
                                "TotalAmt": payment.amount,
                                "Line": [{
                                    'Amount': payment.amount,
                                    'LinkedTxn': [{
                                        'TxnId': move_id,
                                        'TxnType': 'Bill',
                                    }]
                                }] if move_id else None,
                                "VendorRef": {
                                    "name": payment.partner_id.name,
                                    "value": payment.partner_id.quickbook_contact_id
                                },
                                "CheckPayment": {
                                    "BankAccountRef": {
                                        "name": "Checking",
                                        "value": "35"
                                    }
                                }
                            }
                            header = {
                                'Authorization': 'Bearer ' + user.access_token,
                                'Content-Type': 'application/json',
                            }
                            response = requests.request("POST", url, data=json.dumps(Payload), headers=header)
                            if response.status_code == 200:
                                response_data = xmltodict.parse(response.text)
                                response_data_str_json = json.dumps(response_data)
                                response_data_json = json.loads(response_data_str_json)
                                payment.write({
                                    'quickbook_payment_id': response_data_json['IntuitResponse']['Payment']['Id']
                                })
                                self.env.cr.commit()
                            else:
                                _logger.info(response.text)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_(str(e)))

    def reconcile_payment(self):
        for payment in self:
            payment_ref = self.env['account.move.line'].search([('move_id', '=', payment.name)])
            if payment_ref:
                _logger.warning(
                    "Skipping reconciliation. 'account.reconciliation.widget' is deprecated in Odoo 17 and has been removed."
                )
                continue
