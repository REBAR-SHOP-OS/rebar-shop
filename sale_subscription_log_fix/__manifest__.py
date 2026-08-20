# -*- coding: utf-8 -*-
{
    "name": "Sale Subscription - Order Log Fix",
    "category": "Sales/Subscription",
    "license": "LGPL-3",
    "version": "1.0.0",
    "summary": """Defensive fix for sale.order.log foreign key violations during demo data generation""",
    "description": """
        This module patches the sale.order.log model from Odoo Enterprise's
        sale_subscription module to prevent PostgreSQL foreign key violations
        that occur when log records are created before their referenced 
        sale.order records exist in the database transaction.
        
        Features:
        - Context flag support to skip log creation during demo data generation
        - Defensive existence checks before creating log entries
        - Comprehensive logging for debugging timing issues
        - Backwards compatible with existing code
        
        Usage:
        To skip log creation during demo data generation or async operations,
        use the context flag:
        
            self.env['sale.order.log'].with_context(
                skip_sale_order_log=True
            ).create(values)
    """,
    "author": "Rebar Shop",
    "website": "https://www.rebar.shop",
    "depends": ["sale_subscription"],
    "installable": True,
    "auto_install": False,
}
