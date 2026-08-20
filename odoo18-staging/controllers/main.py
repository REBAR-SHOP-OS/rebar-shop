# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError
from werkzeug.exceptions import BadRequest, Unauthorized

_logger = logging.getLogger(__name__)


class RebarShopController(http.Controller):
    """
    Main controller for Rebar Shop with enhanced security and validation.
    Compatible with Odoo 18.
    """

    @http.route('/shop/products', type='json', auth='public', methods=['POST'], csrf=False)
    def get_products(self, domain=None, page=1, limit=12, **kwargs):
        """
        Get products with pagination and filtering.
        
        Args:
            domain: Search domain for products
            page: Page number (1-based)
            limit: Number of products per page
            
        Returns:
            dict: Products data with pagination info
        """
        try:
            # Input validation
            page = max(1, int(page))
            limit = min(max(1, int(limit)), 100)  # Limit between 1-100
            
            # Build domain
            base_domain = [
                ('sale_ok', '=', True),
                ('website_published', '=', True)
            ]
            
            if domain:
                # Validate domain to prevent injection
                if isinstance(domain, list):
                    base_domain.extend(domain)
            
            # Calculate offset
            offset = (page - 1) * limit
            
            # Get products
            Product = request.env['product.product'].sudo()
            products = Product.search(base_domain, limit=limit, offset=offset)
            total_count = Product.search_count(base_domain)
            
            # Prepare product data
            product_data = []
            for product in products:
                product_data.append({
                    'id': product.id,
                    'name': product.name,
                    'list_price': product.list_price,
                    'image_128': f'/web/image/product.product/{product.id}/image_128' if product.image_128 else None,
                    'image_256': f'/web/image/product.product/{product.id}/image_256' if product.image_256 else None,
                    'description_sale': product.description_sale or '',
                    'qty_available': product.qty_available,
                    'website_url': f'/shop/product/{product.id}'
                })
            
            return {
                'products': product_data,
                'total_count': total_count,
                'total_pages': (total_count + limit - 1) // limit,
                'current_page': page,
                'has_next': page * limit < total_count,
                'has_prev': page > 1
            }
            
        except Exception as e:
            _logger.error(f"Error in get_products: {str(e)}")
            return {'error': 'Failed to load products'}

    @http.route('/shop/categories', type='json', auth='public', methods=['POST'], csrf=False)
    def get_categories(self, **kwargs):
        """
        Get product categories.
        
        Returns:
            list: Available product categories
        """
        try:
            Category = request.env['product.public.category'].sudo()
            categories = Category.search([('website_published', '=', True)])
            
            category_data = []
            for category in categories:
                category_data.append({
                    'id': category.id,
                    'name': category.name,
                    'product_count': len(category.product_tmpl_ids)
                })
            
            return category_data
            
        except Exception as e:
            _logger.error(f"Error in get_categories: {str(e)}")
            return {'error': 'Failed to load categories'}

    @http.route('/shop/cart/add', type='json', auth='user', methods=['POST'], csrf=False)
    def add_to_cart(self, product_id, quantity=1, **kwargs):
        """
        Add product to cart.
        
        Args:
            product_id: ID of product to add
            quantity: Quantity to add
            
        Returns:
            dict: Success/error response
        """
        try:
            # Input validation
            if not isinstance(product_id, int) or product_id <= 0:
                raise ValidationError("Invalid product ID")
            
            if not isinstance(quantity, int) or quantity <= 0 or quantity > 1000:
                raise ValidationError("Invalid quantity")
            
            # Check if user is authenticated
            if not request.env.user or request.env.user._is_public():
                raise Unauthorized("Authentication required")
            
            # Get or create sale order
            SaleOrder = request.env['sale.order']
            order = SaleOrder.search([
                ('partner_id', '=', request.env.user.partner_id.id),
                ('state', '=', 'draft')
            ], limit=1)
            
            if not order:
                order = SaleOrder.create({
                    'partner_id': request.env.user.partner_id.id,
                    'state': 'draft'
                })
            
            # Get product
            product = request.env['product.product'].browse(product_id)
            if not product.exists() or not product.sale_ok:
                raise ValidationError("Product not available")
            
            # Check if product already in cart
            existing_line = order.order_line.filtered(
                lambda line: line.product_id.id == product_id
            )
            
            if existing_line:
                existing_line.product_uom_qty += quantity
            else:
                request.env['sale.order.line'].create({
                    'order_id': order.id,
                    'product_id': product_id,
                    'product_uom_qty': quantity,
                    'price_unit': product.list_price
                })
            
            return {
                'success': True,
                'message': f'{product.name} added to cart',
                'cart_count': len(order.order_line)
            }
            
        except ValidationError as e:
            return {'error': str(e)}
        except Unauthorized as e:
            return {'error': 'Authentication required'}
        except Exception as e:
            _logger.error(f"Error in add_to_cart: {str(e)}")
            return {'error': 'Failed to add product to cart'}

    @http.route('/shop/cart', type='json', auth='user', methods=['POST'], csrf=False)
    def get_cart(self, **kwargs):
        """
        Get current user's cart.
        
        Returns:
            dict: Cart data
        """
        try:
            if not request.env.user or request.env.user._is_public():
                return {'error': 'Authentication required'}
            
            # Get current draft order
            order = request.env['sale.order'].search([
                ('partner_id', '=', request.env.user.partner_id.id),
                ('state', '=', 'draft')
            ], limit=1)
            
            if not order:
                return {
                    'lines': [],
                    'total': 0.0,
                    'count': 0
                }
            
            # Prepare cart data
            lines = []
            for line in order.order_line:
                lines.append({
                    'id': line.id,
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.name,
                    'quantity': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'price_subtotal': line.price_subtotal
                })
            
            return {
                'lines': lines,
                'total': order.amount_total,
                'count': len(lines)
            }
            
        except Exception as e:
            _logger.error(f"Error in get_cart: {str(e)}")
            return {'error': 'Failed to load cart'}

    @http.route('/shop/product/<int:product_id>', type='http', auth='public', website=True)
    def product_detail(self, product_id, **kwargs):
        """
        Product detail page.
        
        Args:
            product_id: ID of product to display
            
        Returns:
            Rendered product detail page
        """
        try:
            product = request.env['product.product'].sudo().browse(product_id)
            
            if not product.exists() or not product.website_published:
                return request.not_found()
            
            values = {
                'product': product,
                'main_object': product,
                'product_variant': product,
            }
            
            return request.render('rebar_shop_staging.product_detail', values)
            
        except Exception as e:
            _logger.error(f"Error in product_detail: {str(e)}")
            return request.not_found()

    @http.route('/api/errors', type='json', auth='public', methods=['POST'], csrf=False)
    def log_error(self, **kwargs):
        """
        Endpoint for logging client-side errors.
        
        Returns:
            dict: Success response
        """
        try:
            # Log the error (sanitize sensitive data)
            error_data = {
                'timestamp': kwargs.get('timestamp'),
                'type': kwargs.get('type'),
                'message': kwargs.get('message'),
                'url': kwargs.get('url'),
                'user_agent': request.httprequest.headers.get('User-Agent', '')[:200]
            }
            
            # Remove sensitive information
            sanitized_data = self._sanitize_error_data(error_data)
            
            _logger.error(f"Client error: {json.dumps(sanitized_data)}")
            
            return {'success': True}
            
        except Exception as e:
            _logger.error(f"Error in log_error: {str(e)}")
            return {'error': 'Failed to log error'}

    def _sanitize_error_data(self, data):
        """
        Sanitize error data to remove sensitive information.
        
        Args:
            data: Error data to sanitize
            
        Returns:
            dict: Sanitized error data
        """
        sensitive_patterns = ['password', 'token', 'key', 'secret', 'auth']
        
        sanitized = {}
        for key, value in data.items():
            if any(pattern in key.lower() for pattern in sensitive_patterns):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + '... [TRUNCATED]'
            else:
                sanitized[key] = value
        
        return sanitized