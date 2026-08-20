{
    "name": "Account move Invoice ",
    "license": "LGPL-3",
    "version": "17.0.1.0.0",
    "summary": "Custom module for account invoice generate",
    "description": """
        This is a custom module for account invoice generate.
    """,
    "author": "serpentcs",
    "website": "https://www.serpentcs.com/",
    "depends": ["base", "account", "sale", "stock","delivery"], 
    "data": [
        "views/account_move_view.xml",
        "report/stock_picking_report.xml",
        "report/report_picking_slip.xml"
    ],

    "installable": True,
    "application": True,
    "auto_install": False,
}
