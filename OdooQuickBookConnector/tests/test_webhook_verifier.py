import json
from contextlib import ExitStack
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import HttpCase

# Every res.config.settings entry point the /quickbook webhook can invoke.
WEBHOOK_ENTRY_POINTS = [
    "import_invoices",
    "import_bills",
    "import_purchase_order",
    "import_sale_order",
    "import_payment",
    "import_vendor_payment",
    "import_credit_memo",
    "import_vendor_credit",
    "import_items",
    "import_customer",
    "update_purchase_order",
    "update_sale_order",
    "update_customer",
    "update_vendor",
]


@tagged("post_install", "-at_install")
class TestWebhookVerifier(HttpCase):
    def test_missing_verifier_token_fails_closed(self):
        """Missing verifier token -> real HTTP 401 and no import is run."""
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("odoo_quickbook.webhook_check", "True")
        params.set_param("odoo_quickbook.quickbook_webhook_verifier_token", False)

        settings_cls = type(self.env["res.config.settings"])
        payload = {
            "eventNotifications": [
                {
                    "realmId": "9341450000000000",
                    "dataChangeEvent": {
                        "entities": [
                            {"name": "Invoice", "id": "1", "operation": "Create"}
                        ]
                    },
                }
            ]
        }
        headers = {
            "Content-Type": "application/json",
            "intuit-signature": "AAAA",
        }

        with ExitStack() as stack:
            mocks = {
                name: stack.enter_context(patch.object(settings_cls, name))
                for name in WEBHOOK_ENTRY_POINTS
            }
            response = self.url_open(
                "/quickbook", data=json.dumps(payload), headers=headers
            )

        self.assertEqual(response.status_code, 401)
        for mock in mocks.values():
            mock.assert_not_called()
