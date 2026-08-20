{
    'name': 'Rebar Shop - Staging Environment',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Rebar Shop Application - Staging Environment for Odoo 18',
    'description': """
        Staging environment for Rebar Shop application with enhanced security
        and modern JavaScript patterns compatible with Odoo 18.
        
        Features:
        - Secure cryptographic operations
        - Comprehensive input validation
        - Modern ES6+ JavaScript
        - Enhanced error handling
        - Comprehensive testing
    """,
    'author': 'Rebar Shop Development Team',
    'website': 'https://rebarshop.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'sale',
        'stock',
        'account',
        'portal',
    ],
    'external_dependencies': {
        'python': [],
        'bin': []
    },
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/rebar_views.xml',
        'views/templates.xml',
        'data/rebar_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rebar_shop_staging/static/src/js/rebar_shop.js',
            'rebar_shop_staging/static/src/js/crypto/encryption_service.js',
            'rebar_shop_staging/static/src/js/validation/input_validator.js',
            'rebar_shop_staging/static/src/js/utils/error_handler.js',
            'rebar_shop_staging/static/src/css/rebar_shop.css',
        ],
        'web.assets_frontend': [
            'rebar_shop_staging/static/src/js/frontend/shop.js',
            'rebar_shop_staging/static/src/js/crypto/encryption_service.js',
            'rebar_shop_staging/static/src/js/validation/input_validator.js',
            'rebar_shop_staging/static/src/js/utils/error_handler.js',
            'rebar_shop_staging/static/src/css/frontend.css',
        ],
        'web.assets_tests': [
            'rebar_shop_staging/static/tests/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}