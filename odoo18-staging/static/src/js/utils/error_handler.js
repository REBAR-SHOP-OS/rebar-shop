/** @odoo-module **/

/**
 * @fileoverview Centralized error handling service for Rebar Shop
 * 
 * This module provides standardized error handling, logging, and user
 * notification capabilities. Compatible with Odoo 18 module system.
 * 
 * @author Rebar Shop Development Team
 * @version 18.0.1.0.0
 * @since 1.0.0
 * 
 * @example
 * import { ErrorHandler } from './utils/error_handler';
 * 
 * const errorHandler = new ErrorHandler();
 * const handledError = errorHandler.handle(error, context);
 */

/**
 * Custom error class for API-related errors.
 * 
 * @class APIError
 * @extends Error
 */
export class APIError extends Error {
    /**
     * Creates a new APIError.
     * 
     * @constructor
     * @param {string} message - Error message
     * @param {number} statusCode - HTTP status code
     * @param {string} endpoint - API endpoint that failed
     * @param {Error} [cause] - Original error cause
     */
    constructor(message, statusCode, endpoint, cause) {
        super(message);
        this.name = 'APIError';
        this.statusCode = statusCode;
        this.endpoint = endpoint;
        this.cause = cause;
        this.timestamp = new Date().toISOString();
    }
}

/**
 * Custom error class for business logic errors.
 * 
 * @class BusinessError
 * @extends Error
 */
export class BusinessError extends Error {
    /**
     * Creates a new BusinessError.
     * 
     * @constructor
     * @param {string} message - Error message
     * @param {string} code - Business error code
     * @param {Object} [context] - Additional error context
     */
    constructor(message, code, context = {}) {
        super(message);
        this.name = 'BusinessError';
        this.code = code;
        this.context = context;
        this.timestamp = new Date().toISOString();
    }
}

/**
 * Centralized error handling service with logging and notification capabilities.
 * 
 * Provides consistent error handling patterns, secure logging without
 * sensitive data exposure, and user-friendly error messages.
 * 
 * @class ErrorHandler
 * @since 18.0.1.0.0
 * 
 * @example
 * const errorHandler = new ErrorHandler();
 * 
 * try {
 *     await riskyOperation();
 * } catch (error) {
 *     const handledError = errorHandler.handle(error, {
 *         component: 'MyComponent',
 *         operation: 'riskyOperation'
 *     });
 * }
 */
export class ErrorHandler {
    /**
     * Creates a new ErrorHandler instance.
     * 
     * @constructor
     * @param {Object} [options={}] - Configuration options
     * @param {boolean} [options.logToConsole=true] - Enable console logging
     * @param {boolean} [options.logToServer=false] - Enable server logging
     * @param {string} [options.logLevel='error'] - Default log level
     * @param {boolean} [options.sanitizeLogs=true] - Sanitize sensitive data in logs
     */
    constructor(options = {}) {
        /**
         * Error handler configuration
         * @private
         * @type {Object}
         */
        this.options = {
            logToConsole: true,
            logToServer: false,
            logLevel: 'error',
            sanitizeLogs: true,
            ...options
        };
        
        /**
         * Error statistics for monitoring
         * @private
         * @type {Object}
         */
        this.stats = {
            totalErrors: 0,
            errorsByType: {},
            errorsByComponent: {},
            lastError: null
        };
        
        /**
         * Sensitive data patterns to exclude from logs
         * @private
         * @type {Array<RegExp>}
         */
        this.sensitivePatterns = [
            /password/i,
            /token/i,
            /key/i,
            /secret/i,
            /auth/i,
            /credential/i,
            /session/i
        ];
    }
    
    /**
     * Handles an error with appropriate logging and user notification.
     * 
     * @method handle
     * @param {Error} error - Error to handle
     * @param {Object} [context={}] - Additional error context
     * @param {Object} [options={}] - Handling options
     * @returns {Error} Processed error for re-throwing or user display
     * 
     * @example
     * try {
     *     await apiCall();
     * } catch (error) {
     *     const handledError = errorHandler.handle(error, {
     *         component: 'ProductService',
     *         method: 'loadProducts',
     *         userId: 123
     *     });
     *     throw handledError;
     * }
     */
    handle(error, context = {}, options = {}) {
        try {
            // Update statistics
            this._updateStats(error, context);
            
            // Create error information object
            const errorInfo = this._createErrorInfo(error, context);
            
            // Log the error
            this._logError(errorInfo, options);
            
            // Report to monitoring system if configured
            if (this.options.logToServer) {
                this._reportError(errorInfo);
            }
            
            // Create user-friendly error
            const userError = this._createUserFriendlyError(error, context);
            
            return userError;
            
        } catch (handlingError) {
            // Fallback error handling
            console.error('Error in error handler:', handlingError);
            return new Error('An unexpected error occurred');
        }
    }
    
    /**
     * Handles async operations with automatic error handling.
     * 
     * @async
     * @method handleAsync
     * @param {Function} operation - Async operation to execute
     * @param {Object} [context={}] - Operation context
     * @returns {Promise<*>} Operation result or handled error
     * 
     * @example
     * const result = await errorHandler.handleAsync(
     *     () => fetchUserData(userId),
     *     { component: 'UserService', operation: 'fetchUserData' }
     * );
     */
    async handleAsync(operation, context = {}) {
        try {
            return await operation();
        } catch (error) {
            const handledError = this.handle(error, context);
            throw handledError;
        }
    }
    
    /**
     * Creates detailed error information for logging.
     * 
     * @private
     * @method _createErrorInfo
     * @param {Error} error - Original error
     * @param {Object} context - Error context
     * @returns {Object} Detailed error information
     */
    _createErrorInfo(error, context) {
        const errorInfo = {
            name: error.name || 'Error',
            message: error.message || 'Unknown error',
            stack: error.stack,
            timestamp: new Date().toISOString(),
            context: this._sanitizeContext(context),
            type: this._classifyError(error),
            severity: this._determineSeverity(error, context)
        };
        
        // Add specific error properties
        if (error.statusCode) {
            errorInfo.statusCode = error.statusCode;
        }
        
        if (error.endpoint) {
            errorInfo.endpoint = error.endpoint;
        }
        
        if (error.code) {
            errorInfo.code = error.code;
        }
        
        // Add browser/environment information
        if (typeof window !== 'undefined') {
            errorInfo.userAgent = navigator.userAgent;
            errorInfo.url = window.location.href;
        }
        
        return errorInfo;
    }
    
    /**
     * Logs error information based on configuration.
     * 
     * @private
     * @method _logError
     * @param {Object} errorInfo - Error information to log
     * @param {Object} options - Logging options
     */
    _logError(errorInfo, options = {}) {
        if (!this.options.logToConsole && !options.forceLog) {
            return;
        }
        
        const logLevel = options.logLevel || this.options.logLevel;
        const logMethod = console[logLevel] || console.error;
        
        // Create sanitized log entry
        const logEntry = {
            timestamp: errorInfo.timestamp,
            type: errorInfo.type,
            severity: errorInfo.severity,
            message: errorInfo.message,
            context: errorInfo.context
        };
        
        // Add stack trace for development
        if (process.env.NODE_ENV === 'development') {
            logEntry.stack = errorInfo.stack;
        }
        
        // Log based on severity
        switch (errorInfo.severity) {
            case 'critical':
                console.error('🚨 CRITICAL ERROR:', logEntry);
                break;
            case 'high':
                console.error('❌ ERROR:', logEntry);
                break;
            case 'medium':
                console.warn('⚠️ WARNING:', logEntry);
                break;
            case 'low':
                console.info('ℹ️ INFO:', logEntry);
                break;
            default:
                logMethod('🐛 ERROR:', logEntry);
        }
    }
    
    /**
     * Reports error to external monitoring system.
     * 
     * @private
     * @async
     * @method _reportError
     * @param {Object} errorInfo - Error information to report
     */
    async _reportError(errorInfo) {
        try {
            // This would integrate with external error reporting service
            // like Sentry, Rollbar, or custom logging endpoint
            
            const reportData = {
                ...errorInfo,
                environment: process.env.NODE_ENV || 'unknown',
                version: '18.0.1.0.0',
                userId: this._getCurrentUserId()
            };
            
            // Example: Send to logging endpoint
            // await fetch('/api/errors', {
            //     method: 'POST',
            //     headers: { 'Content-Type': 'application/json' },
            //     body: JSON.stringify(reportData)
            // });
            
        } catch (reportingError) {
            console.error('Failed to report error:', reportingError);
        }
    }
    
    /**
     * Creates user-friendly error message.
     * 
     * @private
     * @method _createUserFriendlyError
     * @param {Error} error - Original error
     * @param {Object} context - Error context
     * @returns {Error} User-friendly error
     */
    _createUserFriendlyError(error, context) {
        // Map technical errors to user-friendly messages
        const errorMappings = {
            'CryptographicError': 'Security operation failed. Please try again.',
            'ValidationError': 'Invalid input provided. Please check your data.',
            'APIError': 'Service temporarily unavailable. Please try again later.',
            'BusinessError': error.message, // Business errors are already user-friendly
            'NetworkError': 'Network connection failed. Please check your internet connection.',
            'TimeoutError': 'Operation timed out. Please try again.',
            'AuthenticationError': 'Authentication failed. Please log in again.',
            'AuthorizationError': 'You do not have permission to perform this action.'
        };
        
        const userMessage = errorMappings[error.name] || 
                           errorMappings[error.constructor.name] ||
                           'An unexpected error occurred. Please try again.';
        
        const userError = new Error(userMessage);
        userError.name = 'UserError';
        userError.originalError = error.name;
        userError.timestamp = new Date().toISOString();
        
        return userError;
    }
    
    /**
     * Classifies error type for better handling.
     * 
     * @private
     * @method _classifyError
     * @param {Error} error - Error to classify
     * @returns {string} Error classification
     */
    _classifyError(error) {
        if (error.name) {
            return error.name;
        }
        
        if (error.statusCode) {
            if (error.statusCode >= 400 && error.statusCode < 500) {
                return 'ClientError';
            }
            if (error.statusCode >= 500) {
                return 'ServerError';
            }
        }
        
        if (error.message) {
            if (error.message.includes('network') || error.message.includes('fetch')) {
                return 'NetworkError';
            }
            if (error.message.includes('timeout')) {
                return 'TimeoutError';
            }
            if (error.message.includes('permission') || error.message.includes('unauthorized')) {
                return 'AuthorizationError';
            }
        }
        
        return 'UnknownError';
    }
    
    /**
     * Determines error severity level.
     * 
     * @private
     * @method _determineSeverity
     * @param {Error} error - Error to evaluate
     * @param {Object} context - Error context
     * @returns {string} Severity level
     */
    _determineSeverity(error, context) {
        // Critical errors that require immediate attention
        const criticalErrors = ['CryptographicError', 'SecurityError', 'DataCorruptionError'];
        if (criticalErrors.includes(error.name)) {
            return 'critical';
        }
        
        // High severity errors
        const highSeverityErrors = ['APIError', 'DatabaseError', 'AuthenticationError'];
        if (highSeverityErrors.includes(error.name)) {
            return 'high';
        }
        
        // Medium severity errors
        const mediumSeverityErrors = ['ValidationError', 'BusinessError', 'NetworkError'];
        if (mediumSeverityErrors.includes(error.name)) {
            return 'medium';
        }
        
        // Check context for severity indicators
        if (context.critical || context.severity === 'critical') {
            return 'critical';
        }
        
        if (context.silent) {
            return 'low';
        }
        
        return 'medium';
    }
    
    /**
     * Sanitizes context to remove sensitive information.
     * 
     * @private
     * @method _sanitizeContext
     * @param {Object} context - Context to sanitize
     * @returns {Object} Sanitized context
     */
    _sanitizeContext(context) {
        if (!this.options.sanitizeLogs) {
            return context;
        }
        
        const sanitized = {};
        
        for (const [key, value] of Object.entries(context)) {
            // Check if key contains sensitive information
            const isSensitive = this.sensitivePatterns.some(pattern => pattern.test(key));
            
            if (isSensitive) {
                sanitized[key] = '[REDACTED]';
            } else if (typeof value === 'object' && value !== null) {
                sanitized[key] = this._sanitizeContext(value);
            } else if (typeof value === 'string' && value.length > 1000) {
                // Truncate very long strings
                sanitized[key] = value.substring(0, 1000) + '... [TRUNCATED]';
            } else {
                sanitized[key] = value;
            }
        }
        
        return sanitized;
    }
    
    /**
     * Updates error statistics for monitoring.
     * 
     * @private
     * @method _updateStats
     * @param {Error} error - Error to record
     * @param {Object} context - Error context
     */
    _updateStats(error, context) {
        this.stats.totalErrors++;
        this.stats.lastError = new Date().toISOString();
        
        // Count by error type
        const errorType = error.name || 'Unknown';
        this.stats.errorsByType[errorType] = (this.stats.errorsByType[errorType] || 0) + 1;
        
        // Count by component
        if (context.component) {
            this.stats.errorsByComponent[context.component] = 
                (this.stats.errorsByComponent[context.component] || 0) + 1;
        }
    }
    
    /**
     * Gets current user ID for error reporting.
     * 
     * @private
     * @method _getCurrentUserId
     * @returns {number|null} Current user ID
     */
    _getCurrentUserId() {
        try {
            // This would integrate with Odoo's user service
            // return odoo.session.uid;
            return null;
        } catch (error) {
            return null;
        }
    }
    
    /**
     * Gets error statistics for monitoring.
     * 
     * @method getStats
     * @returns {Object} Error statistics
     * 
     * @example
     * const stats = errorHandler.getStats();
     * console.log(`Total errors: ${stats.totalErrors}`);
     */
    getStats() {
        return { ...this.stats };
    }
    
    /**
     * Resets error statistics.
     * 
     * @method resetStats
     */
    resetStats() {
        this.stats = {
            totalErrors: 0,
            errorsByType: {},
            errorsByComponent: {},
            lastError: null
        };
    }
}

export default ErrorHandler;