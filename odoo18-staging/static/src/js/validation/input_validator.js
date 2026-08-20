/** @odoo-module **/

/**
 * @fileoverview Comprehensive input validation service for Rebar Shop
 * 
 * This module provides secure input validation and sanitization capabilities
 * to prevent injection attacks, data corruption, and system instability.
 * Compatible with Odoo 18 module system.
 * 
 * @author Rebar Shop Development Team
 * @version 18.0.1.0.0
 * @since 1.0.0
 * 
 * @example
 * import { InputValidator } from './validation/input_validator';
 * 
 * const validator = new InputValidator();
 * const result = validator.validate(userData, userSchema);
 */

/**
 * Custom error class for validation failures.
 * 
 * @class ValidationError
 * @extends Error
 */
export class ValidationError extends Error {
    /**
     * Creates a new ValidationError.
     * 
     * @constructor
     * @param {string} message - Error message
     * @param {Array<string>} [errors=[]] - Detailed validation errors
     * @param {string} [field] - Field that failed validation
     */
    constructor(message, errors = [], field = null) {
        super(message);
        this.name = 'ValidationError';
        this.errors = errors;
        this.field = field;
        this.timestamp = new Date().toISOString();
    }
}

/**
 * Comprehensive input validation service with sanitization capabilities.
 * 
 * Provides validation for various data types, sanitization for security,
 * and comprehensive error reporting. Designed to prevent injection attacks
 * and ensure data integrity.
 * 
 * @class InputValidator
 * @since 18.0.1.0.0
 * 
 * @example
 * const validator = new InputValidator();
 * 
 * // Validate user input
 * const userData = validator.validate(input, userSchema);
 * 
 * // Validate single field
 * const result = validator.validateField(email, emailRules);
 */
export class InputValidator {
    /**
     * Creates a new InputValidator instance.
     * 
     * @constructor
     * @param {Object} [options={}] - Configuration options
     * @param {boolean} [options.strictMode=true] - Enable strict validation
     * @param {boolean} [options.sanitizeInput=true] - Enable input sanitization
     * @param {number} [options.maxStringLength=10000] - Maximum string length
     */
    constructor(options = {}) {
        /**
         * Validator configuration options
         * @private
         * @type {Object}
         */
        this.options = {
            strictMode: true,
            sanitizeInput: true,
            maxStringLength: 10000,
            ...options
        };
        
        /**
         * Predefined validation schemas
         * @private
         * @type {Object}
         */
        this.schemas = this._initializeSchemas();
    }
    
    /**
     * Validates input data against a schema.
     * 
     * @method validate
     * @param {Object} input - Input data to validate
     * @param {Object} schema - Validation schema
     * @param {Object} [context={}] - Additional validation context
     * @returns {Object} Validated and sanitized data
     * 
     * @throws {ValidationError} When validation fails
     * 
     * @example
     * const userData = validator.validate({
     *     email: 'user@example.com',
     *     age: 25
     * }, {
     *     email: { type: 'email', required: true },
     *     age: { type: 'integer', min: 0, max: 150 }
     * });
     */
    validate(input, schema, context = {}) {
        const errors = [];
        const sanitized = {};
        
        // Validate input is an object
        if (!input || typeof input !== 'object' || Array.isArray(input)) {
            throw new ValidationError('Input must be a non-null object');
        }
        
        // Check required fields
        for (const [field, rules] of Object.entries(schema)) {
            if (rules.required && (input[field] === undefined || input[field] === null)) {
                errors.push(`Field '${field}' is required`);
                continue;
            }
            
            if (input[field] !== undefined && input[field] !== null) {
                try {
                    const result = this.validateField(input[field], rules, field, context);
                    if (result.errors.length > 0) {
                        errors.push(...result.errors);
                    } else {
                        sanitized[field] = result.value;
                    }
                } catch (error) {
                    errors.push(`Field '${field}': ${error.message}`);
                }
            }
        }
        
        // Check for unexpected fields in strict mode
        if (this.options.strictMode) {
            for (const field of Object.keys(input)) {
                if (!schema[field]) {
                    errors.push(`Unexpected field '${field}'`);
                }
            }
        }
        
        if (errors.length > 0) {
            throw new ValidationError('Input validation failed', errors);
        }
        
        return sanitized;
    }
    
    /**
     * Validates a single field against validation rules.
     * 
     * @method validateField
     * @param {*} value - Value to validate
     * @param {Object} rules - Validation rules
     * @param {string} fieldName - Name of the field being validated
     * @param {Object} [context={}] - Additional validation context
     * @returns {Object} Validation result with errors and sanitized value
     * 
     * @example
     * const result = validator.validateField('user@example.com', {
     *     type: 'email',
     *     required: true
     * }, 'email');
     */
    validateField(value, rules, fieldName, context = {}) {
        const errors = [];
        let sanitizedValue = value;
        
        try {
            // Type validation and conversion
            if (rules.type) {
                const typeResult = this._validateType(value, rules.type, fieldName);
                if (typeResult.errors.length > 0) {
                    return { errors: typeResult.errors, value: null };
                }
                sanitizedValue = typeResult.value;
            }
            
            // Sanitization
            if (this.options.sanitizeInput && typeof sanitizedValue === 'string') {
                sanitizedValue = this._sanitizeString(sanitizedValue);
            }
            
            // Pattern validation
            if (rules.pattern && typeof sanitizedValue === 'string') {
                if (!rules.pattern.test(sanitizedValue)) {
                    errors.push(`Field '${fieldName}' does not match required pattern`);
                }
            }
            
            // Length validation
            if (rules.minLength !== undefined) {
                if (sanitizedValue.length < rules.minLength) {
                    errors.push(`Field '${fieldName}' must be at least ${rules.minLength} characters`);
                }
            }
            
            if (rules.maxLength !== undefined) {
                if (sanitizedValue.length > rules.maxLength) {
                    errors.push(`Field '${fieldName}' must not exceed ${rules.maxLength} characters`);
                }
            }
            
            // Numeric range validation
            if (rules.min !== undefined && typeof sanitizedValue === 'number') {
                if (sanitizedValue < rules.min) {
                    errors.push(`Field '${fieldName}' must be at least ${rules.min}`);
                }
            }
            
            if (rules.max !== undefined && typeof sanitizedValue === 'number') {
                if (sanitizedValue > rules.max) {
                    errors.push(`Field '${fieldName}' must not exceed ${rules.max}`);
                }
            }
            
            // Enum validation
            if (rules.enum && !rules.enum.includes(sanitizedValue)) {
                errors.push(`Field '${fieldName}' must be one of: ${rules.enum.join(', ')}`);
            }
            
            // Custom validation function
            if (rules.validator && typeof rules.validator === 'function') {
                const customResult = rules.validator(sanitizedValue, context);
                if (customResult !== true) {
                    errors.push(customResult || `Field '${fieldName}' failed custom validation`);
                }
            }
            
            // Security validations
            this._performSecurityValidation(sanitizedValue, fieldName, errors);
            
        } catch (error) {
            errors.push(`Validation error for field '${fieldName}': ${error.message}`);
        }
        
        return { errors, value: sanitizedValue };
    }
    
    /**
     * Validates and converts value to specified type.
     * 
     * @private
     * @method _validateType
     * @param {*} value - Value to validate
     * @param {string} expectedType - Expected type
     * @param {string} fieldName - Field name for error messages
     * @returns {Object} Type validation result
     */
    _validateType(value, expectedType, fieldName) {
        switch (expectedType) {
            case 'string':
                if (typeof value !== 'string') {
                    return { errors: [`Field '${fieldName}' must be a string`], value: null };
                }
                return { errors: [], value: this._sanitizeString(value) };
                
            case 'email':
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (typeof value !== 'string' || !emailRegex.test(value)) {
                    return { errors: [`Field '${fieldName}' must be a valid email`], value: null };
                }
                return { errors: [], value: value.toLowerCase().trim() };
                
            case 'integer':
                const intValue = parseInt(value, 10);
                if (isNaN(intValue) || intValue.toString() !== value.toString()) {
                    return { errors: [`Field '${fieldName}' must be an integer`], value: null };
                }
                return { errors: [], value: intValue };
                
            case 'float':
                const floatValue = parseFloat(value);
                if (isNaN(floatValue)) {
                    return { errors: [`Field '${fieldName}' must be a number`], value: null };
                }
                return { errors: [], value: floatValue };
                
            case 'boolean':
                if (typeof value === 'boolean') {
                    return { errors: [], value: value };
                }
                if (typeof value === 'string') {
                    const lowerValue = value.toLowerCase();
                    if (['true', '1', 'yes', 'on'].includes(lowerValue)) {
                        return { errors: [], value: true };
                    }
                    if (['false', '0', 'no', 'off'].includes(lowerValue)) {
                        return { errors: [], value: false };
                    }
                }
                return { errors: [`Field '${fieldName}' must be a boolean`], value: null };
                
            case 'array':
                if (!Array.isArray(value)) {
                    return { errors: [`Field '${fieldName}' must be an array`], value: null };
                }
                return { errors: [], value: value };
                
            case 'object':
                if (typeof value !== 'object' || value === null || Array.isArray(value)) {
                    return { errors: [`Field '${fieldName}' must be an object`], value: null };
                }
                return { errors: [], value: this._sanitizeObject(value) };
                
            case 'date':
                const date = new Date(value);
                if (isNaN(date.getTime())) {
                    return { errors: [`Field '${fieldName}' must be a valid date`], value: null };
                }
                return { errors: [], value: date };
                
            case 'url':
                try {
                    const url = new URL(value);
                    // Only allow http and https protocols
                    if (!['http:', 'https:'].includes(url.protocol)) {
                        return { errors: [`Field '${fieldName}' must use http or https protocol`], value: null };
                    }
                    return { errors: [], value: url.toString() };
                } catch (error) {
                    return { errors: [`Field '${fieldName}' must be a valid URL`], value: null };
                }
                
            default:
                return { errors: [`Unknown type '${expectedType}' for field '${fieldName}'`], value: null };
        }
    }
    
    /**
     * Sanitizes string input to prevent security issues.
     * 
     * @private
     * @method _sanitizeString
     * @param {string} str - String to sanitize
     * @returns {string} Sanitized string
     */
    _sanitizeString(str) {
        if (typeof str !== 'string') {
            return str;
        }
        
        // Remove null bytes and control characters except newlines and tabs
        let sanitized = str.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
        
        // Trim whitespace
        sanitized = sanitized.trim();
        
        // Limit length
        if (sanitized.length > this.options.maxStringLength) {
            sanitized = sanitized.substring(0, this.options.maxStringLength);
        }
        
        return sanitized;
    }
    
    /**
     * Sanitizes object properties recursively.
     * 
     * @private
     * @method _sanitizeObject
     * @param {Object} obj - Object to sanitize
     * @returns {Object} Sanitized object
     */
    _sanitizeObject(obj) {
        if (typeof obj !== 'object' || obj === null) {
            return obj;
        }
        
        const sanitized = {};
        for (const [key, value] of Object.entries(obj)) {
            const sanitizedKey = this._sanitizeString(key);
            
            if (typeof value === 'string') {
                sanitized[sanitizedKey] = this._sanitizeString(value);
            } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                sanitized[sanitizedKey] = this._sanitizeObject(value);
            } else {
                sanitized[sanitizedKey] = value;
            }
        }
        
        return sanitized;
    }
    
    /**
     * Performs security-focused validation checks.
     * 
     * @private
     * @method _performSecurityValidation
     * @param {*} value - Value to check
     * @param {string} fieldName - Field name
     * @param {Array} errors - Errors array to append to
     */
    _performSecurityValidation(value, fieldName, errors) {
        if (typeof value !== 'string') {
            return;
        }
        
        // Check for potential SQL injection patterns
        const sqlPatterns = [
            /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)/i,
            /(--|\/\*|\*\/|;)/,
            /(\b(OR|AND)\b.*=.*)/i
        ];
        
        for (const pattern of sqlPatterns) {
            if (pattern.test(value)) {
                errors.push(`Field '${fieldName}' contains potentially dangerous SQL patterns`);
                break;
            }
        }
        
        // Check for potential XSS patterns
        const xssPatterns = [
            /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
            /javascript:/i,
            /on\w+\s*=/i,
            /<iframe\b/i,
            /<object\b/i,
            /<embed\b/i
        ];
        
        for (const pattern of xssPatterns) {
            if (pattern.test(value)) {
                errors.push(`Field '${fieldName}' contains potentially dangerous script content`);
                break;
            }
        }
        
        // Check for path traversal attempts
        if (value.includes('../') || value.includes('..\\')) {
            errors.push(`Field '${fieldName}' contains path traversal patterns`);
        }
        
        // Check for command injection patterns
        const commandPatterns = [
            /[;&|`$()]/,
            /\b(cat|ls|dir|type|copy|del|rm|mv|cp)\b/i
        ];
        
        for (const pattern of commandPatterns) {
            if (pattern.test(value)) {
                errors.push(`Field '${fieldName}' contains potentially dangerous command patterns`);
                break;
            }
        }
    }
    
    /**
     * Initializes predefined validation schemas.
     * 
     * @private
     * @method _initializeSchemas
     * @returns {Object} Predefined schemas
     */
    _initializeSchemas() {
        return {
            user: {
                id: { type: 'integer', min: 1, required: true },
                email: { type: 'email', maxLength: 254, required: true },
                name: { type: 'string', minLength: 1, maxLength: 100, required: true },
                age: { type: 'integer', min: 0, max: 150, required: false }
            },
            
            product: {
                id: { type: 'integer', min: 1, required: true },
                name: { type: 'string', minLength: 1, maxLength: 200, required: true },
                price: { type: 'float', min: 0, required: true },
                category: { type: 'string', enum: ['steel', 'concrete', 'tools', 'accessories'] },
                description: { type: 'string', maxLength: 1000 }
            },
            
            order: {
                id: { type: 'integer', min: 1, required: true },
                user_id: { type: 'integer', min: 1, required: true },
                total: { type: 'float', min: 0, required: true },
                status: { type: 'string', enum: ['draft', 'confirmed', 'shipped', 'delivered', 'cancelled'] }
            }
        };
    }
    
    /**
     * Gets a predefined schema by name.
     * 
     * @method getSchema
     * @param {string} schemaName - Name of the schema
     * @returns {Object|null} Schema object or null if not found
     * 
     * @example
     * const userSchema = validator.getSchema('user');
     * const userData = validator.validate(input, userSchema);
     */
    getSchema(schemaName) {
        return this.schemas[schemaName] || null;
    }
    
    /**
     * Adds a custom validation schema.
     * 
     * @method addSchema
     * @param {string} name - Schema name
     * @param {Object} schema - Schema definition
     * 
     * @example
     * validator.addSchema('customUser', {
     *     username: { type: 'string', pattern: /^[a-zA-Z0-9_]+$/ },
     *     role: { type: 'string', enum: ['admin', 'user', 'guest'] }
     * });
     */
    addSchema(name, schema) {
        this.schemas[name] = schema;
    }
}

export default InputValidator;