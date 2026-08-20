import logging
import pprint

from werkzeug.urls import url_join

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    quickbook_contact_id = fields.Char()


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of payment to find the transaction based on QuickBooks Payment data.

        :param str provider_code: The code of the provider that handled the transaction.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If inconsistent data were received.
        :raise ValidationError: If the data match no transaction.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)

        # If the provider is not QuickBooks Payments or
        # if only one transaction is found, return it
        if provider_code != "qbpayments" or len(tx) == 1:
            return tx

        # Attempt to fetch the TxnId from the notification data
        reference = notification_data.get('Payment', {}).get('Line', [{}])[0].get('LinkedTxn', [{}])[0].get('TxnId', False)

        # Attempt to fetch the order reference from LineEx entries
        # values = [entry.get('value', {}).get('Value', 'Value not found') for entry in data.get('Payment', {}).get('Line', [{}])[0].get('LineEx', {}).get('any', [])]
        order_ref = next(
                (entry.get('value', {}).get('Value') for entry in notification_data.get('Payment', {}).get('Line', [{}])[0].get('LineEx', {}).get('any', [])
                if entry.get('value', {}).get('Name') == 'txnReferenceNumber'),
                False
            )
        # Check if both reference and order_ref are missing and raise an error
        if not reference and not order_ref:
            raise ValidationError(
                _("QuickBooks Payment: Received data with missing reference.")
            )

        # Search for the transaction based on the reference and provider code
        tx = self.search([
            ("provider_code", "=", "qbpayments"),
            ("reference", "=", order_ref),
            ("provider_reference", "=", reference)
        ])
        # Raise an error if no matching transaction is found
        if not tx:
            raise ValidationError(
                _(
                    "QuickBooks Payment: No transaction found matching reference %s.",
                    reference,
                )
            )
        return tx

    def _process_notification_data(self, notification_data):
        """Override of payment to process the transaction based on QB Payment data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data were received.
        """
        super()._process_notification_data(notification_data)
        # Check if the provider is QuickBooks Payments
        if self.provider_code != "qbpayments":
            return

        # Extract relevant payment information from the notification data
        payment_reference = notification_data.get('Payment', {}).get('Id', False)
        payment_status = notification_data.get('Payment', {}).get('CreditCardPayment', {}).get('CreditChargeResponse', {}).get('Status', False)
        private_note = notification_data.get('Payment', {}).get('PrivateNote', '')

        # Handle the payment status based on the received data
        if payment_status == "Completed":
            # Update the provider reference and mark the transaction as done
            self.provider_reference = payment_reference
            self._set_done(
                f"Payment Done with Reference Note:'{private_note}', Status: '{payment_status}'"
            )
        elif payment_status == "Unknown":
            # Update the provider reference and mark the transaction as canceled
            self.provider_reference = payment_reference
            self._set_canceled()
        else:
            # Log a warning for any invalid payment statuses received
            _logger.warning(
                "Received data with invalid payment status (%s)"
                " for transaction with reference %s.",
                payment_status, self.reference
            )
            self._set_error(_(
                "QuickBooks Payment: Unknown payment status: %s", payment_status))

        # payment_status = notification_data.get("Payment", {}).get("Id", False)
        # if payment_status:
        #     self.provider_reference = payment_status
        #     cust_name = (
        #         notification_data.get("Payment", {})
        #         .get("CustomerRef", {})
        #         .get("name", {})
        #     )
        #     self._set_done(
        #         f"Payment Done with Customer:'{cust_name}', ID: '{payment_status}'"
        #     )

        # # Update the payment state based on the notification data
        # payment_status = notification_data.get('context', {}).get("paymentStatus", "")
        # transaction_status = notification_data.get('status', '')
        # refund_transaction_type = notification_data.get("type")
        #
        # if payment_status == "Completed" and transaction_status == "CAPTURED":
        #     self.provider_reference = notification_data.get("id", '')
        #     self._set_done("Payment Done")
        #
        # elif refund_transaction_type == "REFUND" and transaction_status == "ISSUED":
        #     self.provider_reference = notification_data.get("id", '')
        #     self._set_done("Refund Payment Done")
        #
        # # elif payment_status in const.PAYMENT_STATUS_MAPPING['cancel']:
        # #     self._set_canceled()
        #
        # else:
        #     _logger.warning(
        #         "Received data with invalid payment status (%s)"
        # " for transaction with reference %s.",
        #         payment_status, self.reference
        #     )
        #     self._set_error(_(
        # "QuickBooks Payment: Unknown payment status: %s", payment_status))

    # def _send_refund_request(self, amount_to_refund=None):
    #     """Override of payment to send a refund request to QuickBooks Payment.
    #
    #     Note: self.ensure_one()
    #
    #     :param float amount_to_refund: The amount to refund
    #     :return: The refund transaction created to process the refund request.
    #     :rtype: recordset of `payment.transaction`
    #     """
    #     refund_tx = super()._send_refund_request(amount_to_refund=amount_to_refund)
    #
    #     # Check if the provider is QuickBooks Payments
    #     if self.provider_code != "qbpayments":
    #         return refund_tx
    #
    #     # Prepare the payload for the refund request
    #     payload = {
    #         "amount": abs(int(refund_tx.amount)),  # Ensure the amount is positive
    #         "description": refund_tx.reference,
    #     }
    #
    #     # Define the refund request URL
    #     REFUND_URL = (
    #         f"/quickbooks/v4/payments/charges/{self.provider_reference}/refunds"
    #     )
    #     endpoint = url_join(self.provider_id._qbpayments_get_api_url(), REFUND_URL)
    #
    #     # Make the refund request to QuickBooks Payments
    #     response_content = refund_tx.provider_id._qbpayments_make_request(
    #         endpoint=endpoint, payload=payload, method="POST"
    #     )
    #     # Log the response from the refund request
    #     _logger.info(
    #         "refund request response for transaction with reference %s:\n%s",
    #         self.reference,
    #         pprint.pformat(response_content),
    #     )
    #
    #     # Handle the refund request response.
    #     refund_tx._handle_notification_data("qbpayments", response_content)
    #
    #     return refund_tx
