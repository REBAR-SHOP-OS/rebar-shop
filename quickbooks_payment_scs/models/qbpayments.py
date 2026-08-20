# See LICENSE file for full copyright and licensing details.

import base64
import json
import logging
import pprint
import uuid

import requests
import xmltodict

from odoo import _, api, fields, models

from odoo.addons.payment.models.payment_provider import ValidationError
from odoo.addons.quickbooks_payment_scs import const

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("qbpayments", "QB Payments")],
        ondelete={"qbpayments": "set default"},
    )
    client_id = fields.Char(required_if_provider="qbpayments")
    client_secret = fields.Char(required_if_provider="qbpayments")
    auth_code = fields.Char(required_if_provider="qbpayments")
    realm_id = fields.Char(required_if_provider="qbpayments")
    access_token = fields.Char(required_if_provider="qbpayments")
    refresh_token = fields.Char(required_if_provider="qbpayments")

    @api.model
    def _quickbooks_payments_get_api_url(self):
        """QuickBooks payments URLs."""
        if self.state == "enabled":
            # Production URL
            return "https://quickbooks.api.intuit.com"
            # TEST URL
        return "https://sandbox-quickbooks.api.intuit.com"

    def _qbpayments_validate_configuration(self, require_refresh=False):
        self.ensure_one()

        missing_fields = []
        if not self.realm_id:
            missing_fields.append("Realm ID")
        if not (self.access_token or self.refresh_token):
            missing_fields.append("Access Token or Refresh Token")
        if require_refresh:
            if not self.client_id:
                missing_fields.append("Client ID")
            if not self.client_secret:
                missing_fields.append("Client Secret")
            if not self.refresh_token:
                missing_fields.append("Refresh Token")

        if missing_fields:
            raise ValidationError(
                _(
                    "QuickBooks Payment: Please configure the following provider fields: %s",
                    ", ".join(missing_fields),
                )
            )

    def _qbpayments_parse_error_payload(self, response):
        try:
            return response.json()
        except ValueError:
            return {"error": response.text}

    def _qbpayments_send_request(self, url, payload, headers, method):
        if method == "GET":
            return requests.get(url, params=payload, headers=headers, timeout=const.TIMEOUT)
        return requests.post(url, json=payload, headers=headers, timeout=const.TIMEOUT)

    def _qbpayments_get_new_access_token(self):
        self.ensure_one()
        self._qbpayments_validate_configuration(require_refresh=True)

        token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Authorization": f"Basic {auth_b64}",
        }
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        try:
            response = requests.post(
                token_url, headers=headers, data=payload, timeout=const.TIMEOUT
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            error_payload = self._qbpayments_parse_error_payload(response)
            _logger.exception(
                "Invalid API request at %s with data:\n%s",
                token_url,
                pprint.pformat(error_payload),
            )
            raise ValidationError(
                _(
                    "QuickBooks Payment: The communication with the API failed. "
                    "QuickBooks Payment gave us the following information: '%s'",
                    error_payload.get("error_description", error_payload.get("error")),
                )
            )

        token_data = response.json()
        _logger.info("Received Updated Token Data: %s", pprint.pformat(token_data))
        self.sudo().write(
            {
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
            }
        )
        self.env.cr.commit()
        return token_data.get("access_token")

    def _qbpayments_make_request(self, endpoint, payload=None, method="POST"):
        """Make a request to QuickBooks Payment API at the specified endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request.
        :param dict payload: The payload of the request.
        :param str method: The HTTP method of the request.
        :return The JSON-formatted content of the response.
        :rtype: dict
        :raise ValidationError: If an HTTP error occurs.
        """
        self.ensure_one()
        self._qbpayments_validate_configuration()

        access_token = self.access_token or self._qbpayments_get_new_access_token()
        if not access_token:
            raise ValidationError(_("Can you please configure payment provider?"))

        url = endpoint
        headers = {
            "authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "content-type": "application/json",
            "request-id": uuid.uuid4().hex,
        }

        try:
            response = self._qbpayments_send_request(url, payload, headers, method)
            if response.status_code == 401 and self.refresh_token:
                access_token = self._qbpayments_get_new_access_token()
                headers["authorization"] = f"Bearer {access_token}"
                response = self._qbpayments_send_request(url, payload, headers, method)

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                _logger.exception(
                    "Invalid API request at %s with data:\n%s",
                    url,
                    pprint.pformat(payload),
                )

                if "application/xml" in response.headers.get("Content-Type", ""):
                    json_response = json.loads(
                        json.dumps(xmltodict.parse(response.text), indent=4)
                    ).get("IntuitResponse", {})
                    error = json_response.get("Fault", {}).get("Error", {})
                    if error:
                        error_details = (
                            f"Error Code: {error.get('@code', '')}, Error Info: "
                            f"{error.get('Message', '')} - {error.get('Detail', '')}"
                        )
                        raise ValidationError(
                            _(
                                "QuickBooks Payment: The communication with the API failed."
                                "quickBooks payment gave us the following "
                                "information: '%s'",
                                error_details,
                            )
                        )

                error_payload = self._qbpayments_parse_error_payload(response)
                if error_payload.get("errors"):
                    error_messages = [
                        f"Error Code: {error.get('code', '')}, Error Info: {error.get('moreInfo', error.get('message', error.get('detail', '')))}"
                        for error in error_payload.get("errors")
                    ]
                elif error_payload.get("Fault", {}).get("Error"):
                    error_messages = [
                        f"Error Code: {error.get('code', '')}, Error Info: {error.get('moreInfo', error.get('message', error.get('detail', error.get('Detail', error.get('Message', '')))))}"
                        for error in error_payload.get("Fault", {}).get("Error")
                    ]
                elif error_payload.get("fault", {}).get("error"):
                    error_messages = [
                        f"Error Code: {error.get('code', '')}, Error Info: {error.get('moreInfo', error.get('message', error.get('detail', '')))}"
                        for error in error_payload.get("fault", {}).get("error")
                    ]
                else:
                    error_messages = [error_payload.get("code", error_payload.get("error", response.text))]
                error_details = ",".join(error_messages)
                raise ValidationError(
                    _(
                        "QuickBooks Payment: The communication with the API failed."
                        "quickBooks payment gave us the following "
                        "information: '%s'",
                        error_details,
                    )
                )

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", url)
            raise ValidationError(
                _("QuickBooks Payment: Could not establish the connection to the API.")
            )
        return response.json()

    def _get_default_payment_method_codes(self):
        """Override of `payment` to return the default payment method codes."""
        default_codes = super()._get_default_payment_method_codes()
        if self.code != "qbpayments":
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES

    def _compute_feature_support_fields(self):
        """Override of `payment` to enable additional features."""
        res = super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == "qbpayments").update(
            {
                "support_express_checkout": True,
                "support_manual_capture": "partial",
                "support_refund": "partial",
                "support_tokenization": True,
            }
        )
        return res

    @api.model
    def _cron_automatically_generate_refresh_token(self):
        provider = self.search([("code", "=", "qbpayments"), ("state", "=", "enabled")], limit=1)
        if provider:
            provider._qbpayments_get_new_access_token()

    # @api.constrains('client_id', 'client_secret', 'state', 'is_published')
    # def _check_auth_code(self):
    #     """
    #     Check if the payment provider has an authorization code.
    #
    #     This method raises a UserError if the provider is published, not disabled,
    #     and lacks an authorization code, prompting the user to generate one.
    #
    #     Raises:
    #     - UserError: If the provider is published and does not have an authorization code.
    #     """
    #     for provider in self:
    #         # Check if the provider needs an authorization code
    #         if not provider.auth_code and provider.is_published and provider.state != "disabled" and not self._context.get("install_filename", False):
    #             raise UserError(_("You need to click 'Generate Authorization Code' button."))
