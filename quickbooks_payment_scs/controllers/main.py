# See LICENSE file for full copyright and licensing details.

import logging
import pprint
import re

from werkzeug.urls import url_join

from odoo import _, fields, http
from odoo.http import request

from odoo.addons.payment.models.payment_provider import ValidationError
from odoo.addons.quickbooks_payment_scs import const

_logger = logging.getLogger(__name__)


class QBPaymentsController(http.Controller):
    _webhook_url = '/qbpayments/webhook'

    @http.route(
        _webhook_url, type='json', auth='public', methods=['GET', 'POST'], csrf=False
    )
    def qbpayment_webhook(self):
        # Retrieve the JSON data from the incoming request
        data = request.get_json_data()
        _logger.info("Received notifications from QuickBooks Payment:\n%s", pprint.pformat(data))

        # Extract notification items and realm ID from the data
        # data = {'eventNotifications': [{'realmId': '9341452420664446', 'dataChangeEvent': {'entities': [{'id': '1864', 'operation': 'Create', 'name': 'Payment', 'lastUpdated': '2024-11-11T10:00:30.000Z'}]}}]}
        notification_items = data.get('eventNotifications', [{}]) and data.get('eventNotifications', [{}])[0].get('dataChangeEvent', {}).get('entities', [])
        realm_id = data.get('eventNotifications', [{}]) and data.get('eventNotifications', [{}])[0].get('realmId', False)

        # Process each notification item
        for notification_item in notification_items:
            payment_id = notification_item.get("id", False)
            payment_name = notification_item.get("name", "")

            # Proceed only if we have a valid realm ID, the notification is for a Payment, and we have a payment ID
            if realm_id and payment_name == "Payment" and payment_id:
                # Find the payment provider based on the realm ID
                provider_sudo = (
                    request.env["payment.provider"].sudo().search([("realm_id", "=", realm_id)], limit=1)
                )
                if not provider_sudo:
                    _logger.warning(
                        "No QuickBooks provider found for webhook realm %s; acknowledging.",
                        realm_id,
                    )
                    continue

                # Construct the API endpoint to retrieve payment details
                find_payment_url = f"/v3/company/{provider_sudo.realm_id}/payment/{payment_id}?minorversion={const.MINORVERSION}"
                api_endpoint = url_join(
                    provider_sudo._quickbooks_payments_get_api_url(), find_payment_url
                )
                # Make a request to the QuickBooks API to get payment details
                payment_response_content = provider_sudo._qbpayments_make_request(
                    endpoint=api_endpoint, payload={}, method="GET"
                )
                _logger.info(
                    "Received payment details %s", pprint.pformat(payment_response_content)
                )
                tx_sudo = request.env['payment.transaction'].sudo()
                try:
                    # Attempt to retrieve the transaction associated with the payment notification
                    tx_sudo = tx_sudo._get_tx_from_notification_data(
                        'qbpayments', payment_response_content
                    )
                except ValidationError:
                    # Warn rather than log the traceback to avoid noise when a POS payment notification
                    # is received and the corresponding `payment.transaction` record is not found.
                    _logger.warning("unable to find the transaction; skipping to acknowledge")
                    continue

                try:
                    # Handle the notification data as if they were feedback of a S2S payment request
                    tx_sudo._handle_notification_data('qbpayments', payment_response_content)
                except ValidationError:  # Acknowledge the notification to avoid getting spammed
                    _logger.exception(
                        "unable to handle the notification data;skipping to acknowledge"
                    )

        # Acknowledge the webhook after processing notifications.
        return {"status": "acknowledged"}

    @http.route(
        "/OAuth2Playground/RedirectUrl/<int:provider_id>",
        type="http",
        auth="public",
        website=True,
    )
    def _return_oauth_url(self, provider_id, **data):
        _logger.info(
            "OAuth2 request response for transaction with reference %s:\n%s",
            provider_id,
            pprint.pformat(data),
        )
        # Check if the provider exists
        provider_sudo = (
            request.env["payment.provider"].sudo().browse(provider_id).exists()
        )
        # Update the provider with the authorization code and realmId
        provider_sudo.sudo().write(
            {
                "auth_code": data.get("code", ""),  # Authorization Code
                "realm_id": data.get("realmId", ""),  # realmId
            }
        )
        # Redirect to the payment provider form
        retun_url = f"/web#id={provider_id}&model=payment.provider&view_type=form"
        return request.redirect(retun_url)

    def _find_or_create_customer(self, tx_sudo, provider_sudo, partner):
        """
        Find or create a customer in QuickBooks.
        This method checks if a customer exists based on the partner's name.
        If found, it returns the customer's ID; if not, it creates a new customer.
        """
        partner = tx_sudo.partner_id.sudo()
        # Use regex to replace anything that is not an alphabet character or a space with an empty string
        partner_name = re.sub(r'[^a-zA-Z\s]', '', tx_sudo.partner_name)
        # f"SELECT * FROM Customer WHERE DisplayName='{partner_name}' AND PrimaryEmailAddr='{tx_sudo.partner_email}'"
        query_statement = (
            f"SELECT * FROM Customer WHERE DisplayName='{partner_name}'"
        )
        find_customer_url = f"/v3/company/{provider_sudo.realm_id}/query?query={query_statement}&minorversion={const.MINORVERSION}"
        api_endpoint = url_join(
            provider_sudo._quickbooks_payments_get_api_url(), find_customer_url
        )

        find_customer_response_content = provider_sudo._qbpayments_make_request(
            endpoint=api_endpoint, payload={}, method="GET"
        )
        _logger.info(
            "Customer Name Exists with data %s",
            pprint.pformat(find_customer_response_content),
        )

        customer_list = find_customer_response_content.get("QueryResponse", {}).get(
            "Customer", []
        )
        if customer_list:
            return customer_list[0].get("Id", False)

        if not partner.quickbook_contact_id:
            # Create customer if not found
            return self._create_customer(tx_sudo, provider_sudo)

        return partner.quickbook_contact_id

    def _create_customer(self, tx_sudo, provider_sudo):
        """
        Create a new customer in QuickBooks.
        Constructs the payload from transaction details and sends a POST request to create a customer.
        """
        customer_creation_url = f"/v3/company/{provider_sudo.realm_id}/customer?minorversion={const.MINORVERSION}"
        api_endpoint = url_join(
            provider_sudo._quickbooks_payments_get_api_url(), customer_creation_url
        )

        customer_payload = {
            "FullyQualifiedName": tx_sudo.partner_name,
            "PrimaryEmailAddr": {"Address": tx_sudo.partner_email},
            "DisplayName": tx_sudo.partner_name,
            "PrimaryPhone": {"FreeFormNumber": tx_sudo.partner_phone or ""},
            "CompanyName": tx_sudo.partner_id.company_name
            or tx_sudo.partner_id.commercial_company_name
            or "ODOO COMPANY",
            "BillAddr": {
                "CountrySubDivisionCode": tx_sudo.partner_country_id.code,
                "City": tx_sudo.partner_city,
                "PostalCode": tx_sudo.partner_zip,
                "Line1": tx_sudo.partner_address,
                "Country": tx_sudo.partner_country_id.code,
            },
            "GivenName": tx_sudo.partner_name,
        }

        customer_response_content = provider_sudo._qbpayments_make_request(
            endpoint=api_endpoint, payload=customer_payload, method="POST"
        )
        _logger.info(
            "Create customer with data %s", pprint.pformat(customer_response_content)
        )

        return customer_response_content.get("Customer", {}).get("Id", "")

    def _create_invoice(
        self,
        tx_sudo,
        provider_sudo,
        reference,
        quickbook_contact_id,
        order,
        invoice,
        currency_sudo,
        currency_USD,
    ):
        """
        Create an invoice in QuickBooks.

        This method constructs and sends an invoice creation request to QuickBooks
        using the provided transaction details. It includes invoice lines generated
        from the sales order or invoice record.

        Args:
            transaction (recordset): The transaction record containing partner details.
            provider (recordset): The provider record containing QuickBooks credentials.
            invoice_reference (str): The reference number for the invoice.
            quickbooks_customer_id (str): The QuickBooks ID of the customer.
            sales_order (recordset): The sales order record used to generate invoice lines.
            invoice_record (recordset): The invoice record if no sales order is provided.
            source_currency (recordset): The currency record of the transaction.
            usd_currency (recordset): The USD currency record for conversion.

        Returns:
            dict: The response content from QuickBooks after creating the invoice.
        """
        invoice_url = f"/v3/company/{provider_sudo.realm_id}/invoice?minorversion={const.MINORVERSION}&include=invoiceLink"
        api_endpoint = url_join(
            provider_sudo._quickbooks_payments_get_api_url(), invoice_url
        )

        # Generate invoice lines
        _logger.info("Generating invoice lines for sales order or invoice record.")

        invoice_lines = self._generate_invoice_lines(
            order, invoice, currency_sudo, currency_USD
        )

        invoice_payload = {
            "CustomerRef": {"value": quickbook_contact_id},
            "Line": invoice_lines,
            "DocNumber": reference,
            "CustomerMemo": {"value": reference},
            "BillEmail": {"Address": tx_sudo.partner_email},
            "EmailStatus": "NeedToSend",
            "AllowOnlineACHPayment": True,
            "AllowOnlineCreditCardPayment": True,
            'AllowOnlinePayment': True,
            "sparse": True,
        }

        # Create invoice in QuickBooks
        _logger.info("Sending request to create invoice in QuickBooks.")
        invoice_response_content = provider_sudo._qbpayments_make_request(
            endpoint=api_endpoint, payload=invoice_payload, method="POST"
        )

        # Log the invoice creation request response
        _logger.info(
            "Create invoice with response data %s",
            pprint.pformat(invoice_response_content),
        )

        # Update InvoiceLink if available
        invoice_link = invoice_response_content.get("Invoice", {}).get(
            "InvoiceLink", ""
        )
        if invoice_link:
            invoice_link = invoice_link.replace(
                "https://developer.intuit.com/comingSoonview",
                "https://connect.intuit.com/t"
                # "https://connect.intuit.com/portal/app/CommerceNetwork/view",
            )
            invoice_response_content.get("Invoice", {}).update(
                {"InvoiceLink": invoice_link}
            )

        return invoice_response_content

    def _generate_invoice_lines(self, order, invoice, currency_sudo, currency_USD):
        """
        Generate invoice lines from the sales order or invoice record.

        This method creates a list of invoice line items based on the provided sales order
        or invoice record. It filters out lines with a price total of zero and converts
        the amounts to USD if necessary.

        Args:
            sales_order (recordset): The sales order record to generate lines from.
            invoice_record (recordset): The invoice record to generate lines from if no sales order is provided.
            source_currency (recordset): The currency record of the transaction.
            usd_currency (recordset): The USD currency record for conversion.

        Returns:
            list: A list of invoice line items formatted for QuickBooks.
        """
        invoice_lines = []

        if order:
            _logger.info("Generating invoice lines from sales order.")
            for line in order.order_line.filtered(lambda line: line.price_total > 0):
                price_total = self._convert_to_usd(
                    line.price_total, currency_sudo, currency_USD
                )
                invoice_lines.append(
                    {
                        "Description": line.product_id.name,
                        "DetailType": "SalesItemLineDetail",
                        "SalesItemLineDetail": {
                            "Qty": line.product_uom_qty,
                            "ItemRef": {"name": line.product_id.name, "value": "1"},
                            "TaxCodeRef": {"value": "2"}
                        },
                        "Amount": price_total,
                    }
                )
        elif invoice:
            _logger.info("Generating invoice lines from invoice record.")
            for line in invoice.invoice_line_ids.filtered(
                lambda line: line.price_total > 0
            ):
                price_total = self._convert_to_usd(
                    line.price_total, currency_sudo, currency_USD
                )
                invoice_lines.append(
                    {
                        "Description": line.product_id.name,
                        "DetailType": "SalesItemLineDetail",
                        "SalesItemLineDetail": {
                            "Qty": line.quantity,
                            "ItemRef": {"name": line.product_id.name, "value": "1"},
                            "TaxCodeRef": {"value": "2"}
                        },
                        "Amount": price_total,
                    }
                )
        return invoice_lines

    def _convert_to_usd(self, amount, currency_sudo, currency_USD):
        """Convert the given amount to USD if necessary."""
        if currency_sudo != currency_USD:
            _logger.info(
                "Converting amount %s from %s to USD.", amount, currency_sudo.name
            )
            return currency_sudo._convert(
                amount,
                currency_USD,
                request.env.user.company_id,
                fields.Date.today(),
            )
        return amount

    @http.route(
        "/payment/qbpayments/charge",
        type="json",
        auth="public",
        website=True,
        csrf=False,
    )
    def qbpayments_payment(
        self, amount, currency_id, provider_id, reference, partner_id
    ):
        # Prepare the payment request to QuickBooks Payments
        _logger.info("Preparing payment request for provider ID: %s", provider_id)
        provider_sudo = (
            request.env["payment.provider"].sudo().browse(provider_id).exists()
        )
        tx_sudo = (
            request.env["payment.transaction"]
            .sudo()
            .search([("reference", "=", reference)])
        )
        currency_sudo = request.env["res.currency"].sudo().browse(currency_id)
        currency_USD = request.env.ref("base.USD")
        partner = tx_sudo.partner_id.sudo()
        order = tx_sudo.sale_order_ids[:1]
        invoice = tx_sudo.invoice_ids[:1]

        provider_sudo._qbpayments_validate_configuration()

        # Find or create customer in QuickBooks
        _logger.info("Finding or creating customer for partner ID: %s", partner_id)
        quickbook_contact_id = self._find_or_create_customer(
            tx_sudo, provider_sudo, partner
        )
        partner.sudo().write({"quickbook_contact_id": quickbook_contact_id})

        # Create invoice in QuickBooks
        _logger.info(
            "Creating invoice in QuickBooks for transaction reference: %s and customer: %s", reference, quickbook_contact_id
        )
        invoice_response_content = self._create_invoice(
            tx_sudo,
            provider_sudo,
            reference,
            partner.quickbook_contact_id,
            order,
            invoice,
            currency_sudo,
            currency_USD,
        )
        tx_sudo.provider_reference = invoice_response_content.get("Invoice", {}).get("Id", False)
        return invoice_response_content
