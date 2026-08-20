from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        """
        Confirm the sale order and create invoices if necessary.

        This method overrides the default action_confirm method to create invoices
        immediately if the invoice policy is set to 'order' for any of the products
        in the order lines.

        Returns:
            res: The result of the super action_confirm method.
        """
        res = super(SaleOrder, self).action_confirm()
        if self.invoice_status in [
            "to invoice",
            "no",
        ] and "order" in self.order_line.mapped("product_id.invoice_policy"):
            self._create_invoices(final=True, grouped=not True)
        return res
