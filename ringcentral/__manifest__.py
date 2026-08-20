# -*- coding: utf-8 -*-
{
    "name": "Odoo RingCentral Integration",
    "version": "1.1",
    "license": "LGPL-3",
    "category": "Customer Relationship Management",
    "summary": "Connector application for RingCentral integration",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "website": "https://www.serpentcs.com",
    # Dependencies
    "depends": ["point_of_sale", "crm", "sales_team", "project", "web", "account"],  # removed duplicate 'point_of_sale'
    # Data files (views, security)
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/crm_phonecall_view.xml",
        "views/res_users_view.xml",
        "views/company_view.xml",
        "wizard/synch_data_wiz.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # Only include Odoo integration scripts and templates (RingCentral libs loaded dynamically via service)
            "/ringcentral/static/src/lib/audio_field.js",            # custom field widget (AudioField)
            "/ringcentral/static/src/js/panel_view_ringcentral.js",  # main panel component logic
            "/ringcentral/static/src/js/list_view.js",               # extended List view controller (login/sync buttons)
            "/ringcentral/static/src/xml/list_view.xml",             # template for List view buttons
            "/ringcentral/static/src/scss/slidemenu.scss",
            "/ringcentral/static/src/css/ringcentral.css",
            "/ringcentral/static/src/scss/custom_ringcentral.scss",
            "/ringcentral/static/src/xml/call_logs_view.xml",
            "/ringcentral/static/src/js/call_logs_views.js",
            "/ringcentral/static/src/xml/miss_logs_views.xml",
            "/ringcentral/static/src/js/miss_logs_views.js",
            "/ringcentral/static/src/xml/available_extensions.xml",
            "/ringcentral/static/src/js/available_extensions.js",
            "/ringcentral/static/src/xml/contacts_render.xml",
            "/ringcentral/static/src/js/contact_render.js",
            "/ringcentral/static/src/xml/incoming_call.xml",
            "/ringcentral/static/src/js/incoming_call.js",
            "/ringcentral/static/src/xml/active_call.xml",
            "/ringcentral/static/src/js/active_call.js",
            "/ringcentral/static/src/xml/outgoing_call.xml",
            "/ringcentral/static/src/js/outgoing_call.js",
            "/ringcentral/static/src/xml/message_partner.xml",
            "/ringcentral/static/src/js/message_partner.js",
            "/ringcentral/static/src/js/message_chatbox.js",
            "/ringcentral/static/src/xml/message_chatbox.xml",
            "/ringcentral/static/src/xml/ringcentral.xml",
            "/ringcentral/static/src/xml/widget.xml",
            "/ringcentral/static/src/js/phone_field.js",
                    ],
    },
    "images": ["static/description/Banner_Odoo_RingCentral_Integration01.png"],
    "installable": True,
    "application": True,
    "price": 599,
    "currency": "EUR",
}
