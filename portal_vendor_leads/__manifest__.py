# -*- coding: utf-8 -*-
{
    'name': "Website Portal Vendor Leads",
    'summary': "Show Assigned Vendor's Leads in website portal",
    'description': """
Show Assigned Vendor's Leads in website portal
    """,
    'author': "Serpent Consulting Services Pvt. Ltd.",
    'website': "https://www.serpentcs.com",
    'category': 'Website',
    'version': '17.0.1.0.0',
    'depends': ['crm', 'portal','website','mail'],
    'data': [
        'security/vendor_portal_security.xml',
        'security/ir.model.access.csv',
        'views/crm_lead_view.xml',
        'views/lead_my_account_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'portal_vendor_leads/static/src/**/*',
        ],
    },
}
