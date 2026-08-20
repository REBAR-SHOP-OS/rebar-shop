import logging
import re
from odoo.exceptions import ValidationError
from odoo import _, api, fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)
_image_dataurl = re.compile(r'(data:image/[a-z]+?);base64,([a-z0-9+/]{3,}=*)([\'"])', re.I)


class UsersSetting(models.Model):
    _inherit = 'res.users'

    access_token = fields.Char('Access Token', readonly=False)
    refresh_token = fields.Char('Refresh Token', readonly=False)
    expires_in = fields.Char('Expires IN', readonly=False)
    quickbook_realm_id = fields.Char('Realm ID')
    select_url = fields.Selection([
        ('https://sandbox-quickbooks.api.intuit.com/', 'https://sandbox-quickbooks.api.intuit.com/'),
        ('https://quickbooks.api.intuit.com/', 'https://quickbooks.api.intuit.com/')], string='Select Account',
        compute='_compute_url')

    def _compute_url(self):
        IrConfigParameter = request.env['ir.config_parameter'].sudo()
        self.select_url = IrConfigParameter.get_param('odoo_quickbook.select_url')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    quickbook_product_id = fields.Char('QuickBook Product ID')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    quickbook_product_id = fields.Char('QuickBook Product ID')


class PurchaseOrderSetting(models.Model):
    _inherit = 'purchase.order'

    quickbook_purchase_order_id = fields.Char('QuickBook Purchase Order ID')


class SalesOrderSetting(models.Model):
    _inherit = 'sale.order'

    quickbook_sale_order_id = fields.Char('Quickbook sale Order ID')


class TransactionTerms(models.Model):
    _inherit = 'account.payment.term'

    quickbook_payment_term_id = fields.Char('Quickbook Payment term ID')


class InvoiceSetting(models.Model):
    _inherit = 'account.move'

    quickbook_invoice_id = fields.Char('QuickBook Invoice ID')


class PartnerSetting(models.Model):
    _inherit = 'res.partner'

    quickbook_contact_id = fields.Char('Quickbook Contact ID')


class DepartmentSetting(models.Model):
    _inherit = 'hr.department'

    quickbook_department_id = fields.Char('Quickbook Department ID')


class EmployeeSetting(models.Model):
    _inherit = 'hr.employee'

    quickbook_employee_id = fields.Char('Quickbook Employee ID')


class AccountSetting(models.Model):
    _inherit = 'account.account'

    coa_id = fields.Many2one(comodel_name="coa.settings", string="QuickBook Chart Of Account")


class PaymentSetting(models.Model):
    _inherit = 'account.payment'

    quickbook_payment_id = fields.Char('Quickbook Payment ID')

class PaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    quickbook_id = fields.Char('Quickbook ID')

class PaymentMethodLine(models.Model):
    _inherit = 'account.payment.method.line'

    quickbook_id = fields.Char('Quickbook ID')

class AccountTaxSetting(models.Model):
    _inherit = 'account.tax'

    tax_id = fields.Many2one(comodel_name="taxes.settings", string="Quickbook Tax")


class TaxesSetting(models.Model):
    _name = "taxes.settings"
    _description = "Quickbook Taxes"

    tax_type = fields.Char("Tax Type")
    name = fields.Char('Name')
    effective_rate = fields.Char("EffectiveRate")
    status = fields.Char("Status")
    tax_id = fields.Char('ID')
    tax_agency_id = fields.Many2one(comodel_name="taxagency.settings", string="Tax Agency")


class TaxAgencySetting(models.Model):
    _name = "taxagency.settings"
    _description = "QuickBook Tax Agency Setting"

    name = fields.Char('Name')
    Tax_tracked_on_sales = fields.Boolean("Taxes Tracked On Sales")
    Tax_tracked_on_purchase = fields.Boolean("Taxes Tracked On Purchase")
    agency_id = fields.Char('ID')


class ChartOfAccountSetting(models.Model):
    _name = "coa.settings"
    _description = "QuickBook Chart of Account"

    account_id = fields.Char("Account ID")
    name = fields.Char('Name')
    status = fields.Char("Status")
    quickbook_account_classification = fields.Char("Classification")
    currency_id = fields.Many2one(comodel_name="res.currency", string="Account Currency")
    description = fields.Char("Description")

class StockMove(models.Model):
    _inherit = "stock.move"
    _description = "Stock Move"

    description_picking = fields.Text('Description of Picking', related="sale_line_id.name", store=True)
