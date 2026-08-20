import json
import logging

import requests
import xmltodict

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class QuickbookExportInvoiceFix(models.Model):
    _inherit = "account.move"

    def _qb_ensure_partner_contact(self, partner_endpoint):
        self.ensure_one()
        if self.partner_id.quickbook_contact_id:
            return

        result = self.env["default.functions"].checkquickbookredundency(
            partner_endpoint, "DisplayName", self.partner_id.name
        )
        query_response = result.get("QueryResponse", {})
        partner_records = query_response.get(partner_endpoint) or []
        if isinstance(partner_records, dict):
            partner_records = [partner_records]

        if partner_records:
            self.partner_id.write({"quickbook_contact_id": partner_records[0].get("Id")})
            self.env.cr.commit()
            return

        self.env["res.partner"].export_contacts(self.partner_id)

    def _qb_ensure_product_item(self, product):
        template = product.product_tmpl_id
        if template.quickbook_product_id:
            return template.quickbook_product_id

        result = self.env["default.functions"].checkquickbookredundency(
            "item", "FullyQualifiedName", template.name
        )
        query_response = result.get("QueryResponse", {})
        items = query_response.get("Item") or []
        if isinstance(items, dict):
            items = [items]

        if items:
            template.write({"quickbook_product_id": items[0].get("Id")})
            self.env.cr.commit()
        else:
            self.env["product.template"].export_items(template)

        return template.quickbook_product_id

    def _qb_build_export_line_items(self):
        self.ensure_one()
        line_items = []
        invoice_lines = self.invoice_line_ids.filtered(
            lambda line: not line.display_type and (line.product_id or line.account_id)
        )

        for line in invoice_lines:
            qty = line.quantity or 0.0
            unit_price = line.price_unit or 0.0
            amount = qty * unit_price

            if self.move_type in ("out_invoice", "out_refund"):
                if not line.product_id:
                    raise ValidationError(
                        _("QuickBooks export requires a product on customer invoice lines.")
                    )

                item_id = self._qb_ensure_product_item(line.product_id)
                tax_code = "TAX" if self.move_type == "out_invoice" else "NON"
                line_items.append(
                    {
                        "DetailType": "SalesItemLineDetail",
                        "Amount": amount,
                        "SalesItemLineDetail": {
                            "ItemRef": {
                                "name": line.product_id.product_tmpl_id.name,
                                "value": item_id,
                            },
                            "TaxCodeRef": {"value": tax_code},
                            "Qty": qty,
                            "UnitPrice": unit_price,
                        },
                    }
                )
                continue

            if line.product_id and line.product_id.type != "service":
                item_id = self._qb_ensure_product_item(line.product_id)
                line_items.append(
                    {
                        "Description": line.name or None,
                        "DetailType": "ItemBasedExpenseLineDetail",
                        "Amount": amount,
                        "ItemBasedExpenseLineDetail": {
                            "ItemRef": {
                                "name": line.product_id.product_tmpl_id.name,
                                "value": item_id,
                            },
                            "TaxCodeRef": {"value": "NON"},
                            "Qty": qty,
                            "UnitPrice": unit_price,
                        },
                    }
                )
                continue

            account_ref = (
                line.account_id.coa_id.account_id
                if line.account_id and line.account_id.coa_id and line.account_id.coa_id.account_id
                else "7"
            )
            line_items.append(
                {
                    "Description": line.name or None,
                    "DetailType": "AccountBasedExpenseLineDetail",
                    "Amount": amount,
                    "AccountBasedExpenseLineDetail": {
                        "AccountRef": {"value": account_ref},
                        "TaxCodeRef": {"value": "NON"},
                    },
                }
            )

        if not line_items:
            raise ValidationError(_("No exportable invoice lines were found for QuickBooks."))

        return line_items

    def export_invoice(self):
        default_functions = self.env["default.functions"]
        current_user = self.env.user
        if current_user.access_token:
            default_functions.check_refreshtoken()

        endpoint_map = {
            "out_invoice": ("Customer", "invoice", "Invoice", "CustomerRef"),
            "in_invoice": ("Vendor", "bill", "Bill", "VendorRef"),
            "out_refund": ("Customer", "creditmemo", "CreditMemo", "CustomerRef"),
            "in_refund": ("Vendor", "vendorcredit", "VendorCredit", "VendorRef"),
        }

        for invoice in self:
            mapping = endpoint_map.get(invoice.move_type)
            if not mapping:
                continue

            partner_endpoint, move_endpoint, query_endpoint, ref_key = mapping
            if invoice.quickbook_invoice_id:
                result = default_functions.checkquickbookredundency(
                    move_endpoint, "id", invoice.quickbook_invoice_id
                )
                if result.get("QueryResponse"):
                    raise ValidationError(_("This account move already exists in QuickBooks."))

            result = default_functions.checkquickbookredundency(
                move_endpoint, "DocNumber", invoice.name
            )
            query_response = result.get("QueryResponse", {})
            existing = query_response.get(query_endpoint) or []
            if isinstance(existing, dict):
                existing = [existing]
            if existing:
                invoice.write({"quickbook_invoice_id": existing[0].get("Id")})
                self.env.cr.commit()
                raise ValidationError(_("This invoice has already been exported."))

            invoice._qb_ensure_partner_contact(partner_endpoint)
            line_items = invoice._qb_build_export_line_items()
            payload = {
                "DocNumber": invoice.name,
                "Line": line_items,
                ref_key: {"value": invoice.partner_id.quickbook_contact_id},
            }

            select_url = self.env["ir.config_parameter"].sudo().get_param(
                "odoo_quickbook.select_url"
            )
            url = (
                f"{select_url}v3/company/{current_user.quickbook_realm_id}/"
                f"{move_endpoint}?minorversion=62"
            )
            headers = {
                "Authorization": f"Bearer {current_user.access_token}",
                "Content-Type": "application/json",
            }
            response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
            if response.status_code != 200:
                _logger.info(response.text)
                raise ValidationError(_(response.text))

            response_data = json.loads(json.dumps(xmltodict.parse(response.text)))
            created_invoice = response_data.get("IntuitResponse", {}).get(query_endpoint, {})
            created_id = created_invoice.get("Id")
            if not created_id:
                raise ValidationError(_("QuickBooks response did not include the exported invoice ID."))

            invoice.write({"quickbook_invoice_id": created_id})
            self.env.cr.commit()
