# See LICENSE file for full copyright and licensing details.

{
    "name": "Odoo QuickBooks Payment Gateway",
    "category": "Accounting",
    "license": "LGPL-3",
    "version": "17.0.1.0.2",
    "summary": """Odoo QuickBooks Payment Gateway Integration""",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "website": "https://www.serpentcs.com",
    "depends": ["website_sale"],
    "data": [
        "views/payment_views.xml",
        "data/payment_provider_data.xml",
    ],
    "assets": {
        "web.assets_frontend": ["/quickbooks_payment_scs/static/src/**/*"],
    },
    # "images": ["static/description/banner_worldpay-odoo.jpg"],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "price": 199,
    "currency": "EUR",
    "installable": True,
    # "external_dependencies": {"python": ["intuit-oauth"]},
}
