# -*- coding: utf-8 -*-
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SaleOrderLog(models.Model):
    """
    Extension of sale.order.log model with defensive checks to prevent
    foreign key violations during demo data generation or async operations.
    
    This patch addresses a PostgreSQL foreign key violation that occurs when
    sale.order.log records are created before their referenced sale.order
    records exist in the database transaction.
    
    Context flags:
    - skip_sale_order_log: When True, skips all log creation
    - skip_sale.order.log: Alternative flag name for skipping log creation
    
    Usage example:
        # During demo data generation or async operations:
        order_log = self.env['sale.order.log'].with_context(
            skip_sale_order_log=True
        ).create(values)
        
        # Or using context manager:
        with self.env['sale.order.log'].with_context(skip_sale_order_log=True):
            # Create operations that would trigger log creation
            pass
    """
    
    _inherit = "sale.order.log"

    def _create_stage_log(self, order_id, event_type, stage_id=None, **kwargs):
        """
        Override to add defensive checks before creating log entries.
        
        This method implements two safety mechanisms:
        1. Context flag check: Allows callers to opt-out of logging by setting
           'skip_sale_order_log' or 'skip_sale.order.log' in the context.
        2. Existence check: Verifies that the referenced sale.order exists
           before attempting to create the log entry.
        
        Args:
            order_id: ID of the sale.order to log
            event_type: Type of event being logged
            stage_id: Optional stage ID
            **kwargs: Additional parameters for log creation
            
        Returns:
            Created sale.order.log record or None if skipped
        """
        # Check if logging is disabled via context flags
        if self.env.context.get('skip_sale_order_log') or \
           self.env.context.get('skip_sale.order.log'):
            _logger.debug(
                "Skipping sale.order.log creation due to context flag "
                "(order_id=%s, event_type=%s)",
                order_id, event_type
            )
            return None
        
        # Defensive check: Verify the sale.order exists before creating log
        if order_id:
            order = self.env['sale.order'].sudo().browse(order_id)
            if not order.exists():
                _logger.warning(
                    "Skipping sale.order.log creation: sale.order %s does not exist "
                    "(event_type=%s). This may indicate a timing issue in demo data "
                    "generation or async operations.",
                    order_id, event_type
                )
                return None
        
        # Proceed with normal log creation using sudo to match existing behavior
        return super(SaleOrderLog, self)._create_stage_log(
            order_id, event_type, stage_id=stage_id, **kwargs
        )

    def create(self, vals_list):
        """
        Override create method to add defensive checks for direct creation.
        
        This provides an additional safety layer when sale.order.log records
        are created directly via create() rather than through _create_stage_log.
        
        Args:
            vals_list: List of value dictionaries or single value dictionary
            
        Returns:
            Created recordset or empty recordset if skipped
        """
        # Check if logging is disabled via context flags
        if self.env.context.get('skip_sale_order_log') or \
           self.env.context.get('skip_sale.order.log'):
            _logger.debug(
                "Skipping sale.order.log create() due to context flag"
            )
            return self.browse()
        
        # Normalize vals_list to always be a list
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        
        # Filter out records where the referenced order doesn't exist
        valid_vals_list = []
        for vals in vals_list:
            order_id = vals.get('order_id')
            if order_id:
                order = self.env['sale.order'].sudo().browse(order_id)
                if not order.exists():
                    _logger.warning(
                        "Skipping sale.order.log creation: sale.order %s does not exist "
                        "(event_type=%s). This may indicate a timing issue in demo data "
                        "generation or async operations.",
                        order_id, vals.get('event_type', 'unknown')
                    )
                    continue
            valid_vals_list.append(vals)
        
        # If all records were filtered out, return empty recordset
        if not valid_vals_list:
            return self.browse()
        
        # Proceed with normal creation using sudo to match existing behavior
        return super(SaleOrderLog, self.sudo()).create(valid_vals_list)
