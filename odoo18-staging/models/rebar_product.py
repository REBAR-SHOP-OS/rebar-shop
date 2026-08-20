# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class RebarProduct(models.Model):
    """
    Enhanced product model for Rebar Shop with additional validation
    and security features for Odoo 18.
    """
    _inherit = 'product.product'

    # Additional fields for rebar products
    steel_grade = fields.Selection([
        ('grade_40', 'Grade 40'),
        ('grade_60', 'Grade 60'),
        ('grade_75', 'Grade 75'),
        ('grade_80', 'Grade 80'),
    ], string='Steel Grade')
    
    diameter = fields.Float(
        string='Diameter (mm)',
        help='Diameter of the rebar in millimeters'
    )
    
    length = fields.Float(
        string='Length (m)',
        help='Standard length in meters'
    )
    
    weight_per_meter = fields.Float(
        string='Weight per Meter (kg)',
        help='Weight per meter in kilograms'
    )
    
    surface_type = fields.Selection([
        ('plain', 'Plain'),
        ('deformed', 'Deformed'),
        ('ribbed', 'Ribbed'),
    ], string='Surface Type')
    
    coating = fields.Selection([
        ('none', 'None'),
        ('epoxy', 'Epoxy Coated'),
        ('galvanized', 'Galvanized'),
        ('stainless', 'Stainless Steel'),
    ], string='Coating')
    
    tensile_strength = fields.Float(
        string='Tensile Strength (MPa)',
        help='Minimum tensile strength in megapascals'
    )
    
    yield_strength = fields.Float(
        string='Yield Strength (MPa)',
        help='Minimum yield strength in megapascals'
    )
    
    certification = fields.Text(
        string='Certification',
        help='Quality certifications and standards'
    )
    
    # Security and validation fields
    is_hazardous = fields.Boolean(
        string='Hazardous Material',
        default=False,
        help='Mark if product requires special handling'
    )
    
    safety_notes = fields.Text(
        string='Safety Notes',
        help='Important safety information for handling'
    )

    @api.constrains('diameter')
    def _check_diameter(self):
        """Validate diameter is within reasonable range."""
        for record in self:
            if record.diameter and (record.diameter < 0 or record.diameter > 100):
                raise ValidationError("Diameter must be between 0 and 100 mm")

    @api.constrains('length')
    def _check_length(self):
        """Validate length is within reasonable range."""
        for record in self:
            if record.length and (record.length < 0 or record.length > 50):
                raise ValidationError("Length must be between 0 and 50 meters")

    @api.constrains('weight_per_meter')
    def _check_weight_per_meter(self):
        """Validate weight per meter is positive."""
        for record in self:
            if record.weight_per_meter and record.weight_per_meter < 0:
                raise ValidationError("Weight per meter must be positive")

    @api.constrains('tensile_strength', 'yield_strength')
    def _check_strength_values(self):
        """Validate strength values are reasonable."""
        for record in self:
            if record.tensile_strength and (record.tensile_strength < 0 or record.tensile_strength > 2000):
                raise ValidationError("Tensile strength must be between 0 and 2000 MPa")
            
            if record.yield_strength and (record.yield_strength < 0 or record.yield_strength > 2000):
                raise ValidationError("Yield strength must be between 0 and 2000 MPa")
            
            if (record.tensile_strength and record.yield_strength and 
                record.yield_strength > record.tensile_strength):
                raise ValidationError("Yield strength cannot exceed tensile strength")

    @api.constrains('name')
    def _check_product_name(self):
        """Validate product name for security."""
        for record in self:
            if record.name:
                # Check for potentially dangerous patterns
                dangerous_patterns = [
                    r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
                    r'javascript:',
                    r'on\w+\s*=',
                    r'[;&|`$()]'
                ]
                
                for pattern in dangerous_patterns:
                    if re.search(pattern, record.name, re.IGNORECASE):
                        raise ValidationError("Product name contains invalid characters")

    @api.model
    def create(self, vals):
        """Override create to add additional validation."""
        # Sanitize text fields
        if 'name' in vals:
            vals['name'] = self._sanitize_text(vals['name'])
        
        if 'description_sale' in vals:
            vals['description_sale'] = self._sanitize_text(vals['description_sale'])
        
        if 'certification' in vals:
            vals['certification'] = self._sanitize_text(vals['certification'])
        
        if 'safety_notes' in vals:
            vals['safety_notes'] = self._sanitize_text(vals['safety_notes'])
        
        return super().create(vals)

    def write(self, vals):
        """Override write to add additional validation."""
        # Sanitize text fields
        if 'name' in vals:
            vals['name'] = self._sanitize_text(vals['name'])
        
        if 'description_sale' in vals:
            vals['description_sale'] = self._sanitize_text(vals['description_sale'])
        
        if 'certification' in vals:
            vals['certification'] = self._sanitize_text(vals['certification'])
        
        if 'safety_notes' in vals:
            vals['safety_notes'] = self._sanitize_text(vals['safety_notes'])
        
        return super().write(vals)

    def _sanitize_text(self, text):
        """
        Sanitize text input to prevent XSS and other attacks.
        
        Args:
            text: Text to sanitize
            
        Returns:
            str: Sanitized text
        """
        if not text:
            return text
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Remove potentially dangerous HTML/JS patterns
        dangerous_patterns = [
            r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe\b',
            r'<object\b',
            r'<embed\b'
        ]
        
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Limit length
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000]
        
        return sanitized.strip()

    @api.model
    def search_products_secure(self, search_term, category_id=None, limit=50):
        """
        Secure product search with input validation.
        
        Args:
            search_term: Search term (validated)
            category_id: Category ID (optional)
            limit: Maximum results
            
        Returns:
            recordset: Matching products
        """
        # Validate search term
        if search_term:
            # Remove dangerous characters
            search_term = re.sub(r'[^\w\s\-_]', '', search_term)
            search_term = search_term.strip()
            
            if len(search_term) > 100:
                search_term = search_term[:100]
        
        # Build domain
        domain = [
            ('sale_ok', '=', True),
            ('active', '=', True)
        ]
        
        if search_term:
            domain.append(('name', 'ilike', search_term))
        
        if category_id:
            try:
                category_id = int(category_id)
                domain.append(('categ_id', '=', category_id))
            except (ValueError, TypeError):
                pass  # Ignore invalid category ID
        
        # Limit results
        limit = min(max(1, int(limit or 50)), 100)
        
        return self.search(domain, limit=limit)

    def get_product_data_secure(self):
        """
        Get product data with sensitive information filtered.
        
        Returns:
            dict: Safe product data
        """
        self.ensure_one()
        
        return {
            'id': self.id,
            'name': self.name,
            'list_price': self.list_price,
            'description_sale': self.description_sale,
            'steel_grade': self.steel_grade,
            'diameter': self.diameter,
            'length': self.length,
            'weight_per_meter': self.weight_per_meter,
            'surface_type': self.surface_type,
            'coating': self.coating,
            'tensile_strength': self.tensile_strength,
            'yield_strength': self.yield_strength,
            'is_hazardous': self.is_hazardous,
            'safety_notes': self.safety_notes,
            'qty_available': self.qty_available,
            'image_url': f'/web/image/product.product/{self.id}/image_256' if self.image_256 else None
        }


class RebarProductCategory(models.Model):
    """Enhanced product category for rebar products."""
    _inherit = 'product.category'

    category_type = fields.Selection([
        ('steel', 'Steel Products'),
        ('concrete', 'Concrete Products'),
        ('tools', 'Tools & Equipment'),
        ('accessories', 'Accessories'),
        ('safety', 'Safety Equipment'),
    ], string='Category Type')
    
    requires_certification = fields.Boolean(
        string='Requires Certification',
        default=False,
        help='Products in this category require quality certification'
    )
    
    safety_level = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ], string='Safety Level', default='low')

    @api.constrains('name')
    def _check_category_name(self):
        """Validate category name for security."""
        for record in self:
            if record.name:
                # Check for potentially dangerous patterns
                if re.search(r'[<>"\';]', record.name):
                    raise ValidationError("Category name contains invalid characters")