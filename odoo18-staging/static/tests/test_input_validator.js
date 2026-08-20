/** @odoo-module **/

import { InputValidator, ValidationError } from "../src/js/validation/input_validator";

QUnit.module('InputValidator Tests', function() {
    
    QUnit.test('should create InputValidator with default options', function(assert) {
        const validator = new InputValidator();
        
        assert.ok(validator instanceof InputValidator, 'Validator instance created');
        assert.equal(validator.options.strictMode, true, 'Strict mode enabled by default');
        assert.equal(validator.options.sanitizeInput, true, 'Input sanitization enabled by default');
    });
    
    QUnit.test('should validate string fields', function(assert) {
        const validator = new InputValidator();
        
        const result = validator.validateField('test string', {
            type: 'string',
            maxLength: 20
        }, 'testField');
        
        assert.equal(result.errors.length, 0, 'No validation errors');
        assert.equal(result.value, 'test string', 'Value preserved');
    });
    
    QUnit.test('should validate email fields', function(assert) {
        const validator = new InputValidator();
        
        // Valid email
        const validResult = validator.validateField('user@example.com', {
            type: 'email'
        }, 'email');
        
        assert.equal(validResult.errors.length, 0, 'Valid email passes');
        assert.equal(validResult.value, 'user@example.com', 'Email value preserved');
        
        // Invalid email
        const invalidResult = validator.validateField('invalid-email', {
            type: 'email'
        }, 'email');
        
        assert.ok(invalidResult.errors.length > 0, 'Invalid email fails validation');
    });
    
    QUnit.test('should validate integer fields', function(assert) {
        const validator = new InputValidator();
        
        // Valid integer
        const validResult = validator.validateField('123', {
            type: 'integer',
            min: 1,
            max: 1000
        }, 'count');
        
        assert.equal(validResult.errors.length, 0, 'Valid integer passes');
        assert.equal(validResult.value, 123, 'Integer converted correctly');
        
        // Invalid integer
        const invalidResult = validator.validateField('not-a-number', {
            type: 'integer'
        }, 'count');
        
        assert.ok(invalidResult.errors.length > 0, 'Invalid integer fails validation');
    });
    
    QUnit.test('should validate with patterns', function(assert) {
        const validator = new InputValidator();
        
        // Valid pattern
        const validResult = validator.validateField('abc123', {
            type: 'string',
            pattern: /^[a-z0-9]+$/
        }, 'code');
        
        assert.equal(validResult.errors.length, 0, 'Valid pattern passes');
        
        // Invalid pattern
        const invalidResult = validator.validateField('ABC!@#', {
            type: 'string',
            pattern: /^[a-z0-9]+$/
        }, 'code');
        
        assert.ok(invalidResult.errors.length > 0, 'Invalid pattern fails validation');
    });
    
    QUnit.test('should validate length constraints', function(assert) {
        const validator = new InputValidator();
        
        // Too short
        const shortResult = validator.validateField('ab', {
            type: 'string',
            minLength: 5
        }, 'name');
        
        assert.ok(shortResult.errors.length > 0, 'Too short string fails validation');
        
        // Too long
        const longResult = validator.validateField('abcdefghijk', {
            type: 'string',
            maxLength: 5
        }, 'name');
        
        assert.ok(longResult.errors.length > 0, 'Too long string fails validation');
    });
    
    QUnit.test('should validate enum values', function(assert) {
        const validator = new InputValidator();
        
        // Valid enum
        const validResult = validator.validateField('admin', {
            type: 'string',
            enum: ['admin', 'user', 'guest']
        }, 'role');
        
        assert.equal(validResult.errors.length, 0, 'Valid enum value passes');
        
        // Invalid enum
        const invalidResult = validator.validateField('superuser', {
            type: 'string',
            enum: ['admin', 'user', 'guest']
        }, 'role');
        
        assert.ok(invalidResult.errors.length > 0, 'Invalid enum value fails validation');
    });
    
    QUnit.test('should detect SQL injection patterns', function(assert) {
        const validator = new InputValidator();
        
        const maliciousInputs = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "UNION SELECT * FROM passwords"
        ];
        
        maliciousInputs.forEach(input => {
            const result = validator.validateField(input, {
                type: 'string'
            }, 'userInput');
            
            assert.ok(result.errors.length > 0, `SQL injection pattern detected: ${input}`);
        });
    });
    
    QUnit.test('should detect XSS patterns', function(assert) {
        const validator = new InputValidator();
        
        const maliciousInputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img onerror='alert(1)' src='x'>"
        ];
        
        maliciousInputs.forEach(input => {
            const result = validator.validateField(input, {
                type: 'string'
            }, 'userInput');
            
            assert.ok(result.errors.length > 0, `XSS pattern detected: ${input}`);
        });
    });
    
    QUnit.test('should sanitize string input', function(assert) {
        const validator = new InputValidator();
        
        const result = validator.validateField('  test\x00string\x1F  ', {
            type: 'string'
        }, 'text');
        
        assert.equal(result.value, 'teststring', 'Control characters removed and trimmed');
    });
    
    QUnit.test('should validate complete objects', function(assert) {
        const validator = new InputValidator();
        
        const schema = {
            name: { type: 'string', required: true, minLength: 2 },
            email: { type: 'email', required: true },
            age: { type: 'integer', min: 0, max: 150 }
        };
        
        const validData = {
            name: 'John Doe',
            email: 'john@example.com',
            age: 30
        };
        
        const result = validator.validate(validData, schema);
        
        assert.equal(result.name, 'John Doe', 'Name validated');
        assert.equal(result.email, 'john@example.com', 'Email validated');
        assert.equal(result.age, 30, 'Age validated');
    });
    
    QUnit.test('should reject missing required fields', function(assert) {
        const validator = new InputValidator();
        
        const schema = {
            name: { type: 'string', required: true },
            email: { type: 'email', required: true }
        };
        
        const incompleteData = {
            name: 'John Doe'
            // email missing
        };
        
        assert.throws(
            () => validator.validate(incompleteData, schema),
            ValidationError,
            'Missing required field should throw ValidationError'
        );
    });
    
    QUnit.test('should reject unexpected fields in strict mode', function(assert) {
        const validator = new InputValidator({ strictMode: true });
        
        const schema = {
            name: { type: 'string', required: true }
        };
        
        const dataWithExtra = {
            name: 'John Doe',
            unexpectedField: 'value'
        };
        
        assert.throws(
            () => validator.validate(dataWithExtra, schema),
            ValidationError,
            'Unexpected field should throw ValidationError in strict mode'
        );
    });
    
    QUnit.test('should get predefined schemas', function(assert) {
        const validator = new InputValidator();
        
        const userSchema = validator.getSchema('user');
        
        assert.ok(userSchema, 'User schema exists');
        assert.ok(userSchema.email, 'User schema has email field');
        assert.ok(userSchema.name, 'User schema has name field');
    });
    
    QUnit.test('should add custom schemas', function(assert) {
        const validator = new InputValidator();
        
        const customSchema = {
            username: { type: 'string', pattern: /^[a-zA-Z0-9_]+$/ },
            role: { type: 'string', enum: ['admin', 'user'] }
        };
        
        validator.addSchema('customUser', customSchema);
        
        const retrievedSchema = validator.getSchema('customUser');
        
        assert.deepEqual(retrievedSchema, customSchema, 'Custom schema added and retrieved');
    });
});