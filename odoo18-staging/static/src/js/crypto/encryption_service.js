/** @odoo-module **/

/**
 * @fileoverview Secure encryption service for Rebar Shop
 * 
 * This module provides secure encryption and decryption capabilities using
 * Web Crypto API with AES-GCM authenticated encryption. All operations
 * use cryptographically secure random IVs and proper error handling.
 * 
 * Compatible with Odoo 18 module system.
 * 
 * @author Rebar Shop Development Team
 * @version 18.0.1.0.0
 * @since 1.0.0
 * 
 * @requires crypto Web Crypto API
 * 
 * @example
 * import { EncryptionService } from './crypto/encryption_service';
 * 
 * const service = new EncryptionService();
 * const key = await service.generateKey();
 * const encrypted = await service.encrypt(data, key);
 * const decrypted = await service.decrypt(encrypted, key);
 */

/**
 * Custom error class for cryptographic operations.
 * 
 * @class CryptographicError
 * @extends Error
 */
export class CryptographicError extends Error {
    /**
     * Creates a new CryptographicError.
     * 
     * @constructor
     * @param {string} message - Error message
     * @param {string} operation - Operation that failed
     * @param {Error} [cause] - Original error cause
     */
    constructor(message, operation, cause) {
        super(message);
        this.name = 'CryptographicError';
        this.operation = operation;
        this.cause = cause;
        this.timestamp = new Date().toISOString();
    }
}

/**
 * Service class for handling cryptographic operations with AES-GCM encryption.
 * 
 * Provides secure encryption and decryption using authenticated encryption
 * with automatic IV generation and proper error handling. All operations
 * are designed to prevent common cryptographic vulnerabilities.
 * 
 * @class EncryptionService
 * @since 18.0.1.0.0
 * 
 * @example
 * const encryptionService = new EncryptionService();
 * 
 * // Generate a key
 * const key = await encryptionService.generateKey();
 * 
 * // Encrypt data
 * const result = await encryptionService.encrypt('sensitive data', key);
 * 
 * // Decrypt data
 * const original = await encryptionService.decrypt(result, key);
 */
export class EncryptionService {
    /**
     * Creates a new EncryptionService instance.
     * 
     * @constructor
     * @param {Object} [options={}] - Configuration options
     * @param {string} [options.algorithm='AES-GCM'] - Encryption algorithm to use
     * @param {number} [options.keyLength=256] - Key length in bits (128, 192, or 256)
     * @param {number} [options.ivLength=12] - IV length in bytes (12 for GCM)
     * 
     * @throws {CryptographicError} When invalid options are provided
     * 
     * @example
     * // Use default settings
     * const service = new EncryptionService();
     * 
     * // Custom configuration
     * const service = new EncryptionService({
     *     algorithm: 'AES-GCM',
     *     keyLength: 256,
     *     ivLength: 12
     * });
     */
    constructor(options = {}) {
        /**
         * Service configuration options
         * @private
         * @type {Object}
         */
        this.options = {
            algorithm: 'AES-GCM',
            keyLength: 256,
            ivLength: 12,
            ...options
        };
        
        // Validate configuration
        this._validateOptions();
    }
    
    /**
     * Encrypts data using AES-GCM authenticated encryption.
     * 
     * Generates a cryptographically secure random IV for each encryption
     * operation and returns both the encrypted data and IV. The IV is
     * required for decryption and should be stored alongside the ciphertext.
     * 
     * @async
     * @method encrypt
     * @param {string|ArrayBuffer|Uint8Array} data - Data to encrypt
     * @param {CryptoKey} key - Encryption key (must support 'encrypt' operation)
     * @returns {Promise<EncryptionResult>} Encryption result with ciphertext and IV
     * 
     * @throws {CryptographicError} When input parameters are invalid or encryption fails
     * 
     * @example
     * const key = await service.generateKey();
     * const result = await service.encrypt('Hello, World!', key);
     * 
     * console.log(result.encrypted); // ArrayBuffer with encrypted data
     * console.log(result.iv);        // Uint8Array with random IV
     * 
     * @example
     * // Encrypt binary data
     * const binaryData = new Uint8Array([1, 2, 3, 4, 5]);
     * const result = await service.encrypt(binaryData, key);
     */
    async encrypt(data, key) {
        try {
            // Validate inputs
            const validatedData = this._validateEncryptionInput(data, key);
            
            // Generate cryptographically secure random IV
            const iv = this._generateSecureIV();
            
            // Perform encryption with authentication
            const encrypted = await crypto.subtle.encrypt(
                {
                    name: this.options.algorithm,
                    iv: iv
                },
                key,
                validatedData
            );
            
            return {
                encrypted,
                iv,
                algorithm: this.options.algorithm,
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            throw new CryptographicError(
                'Encryption operation failed',
                'encrypt',
                error
            );
        }
    }
    
    /**
     * Decrypts data that was encrypted with the encrypt method.
     * 
     * Uses the provided IV and key to decrypt AES-GCM encrypted data.
     * The IV must be the same one used during encryption. Authentication
     * is automatically verified as part of the GCM decryption process.
     * 
     * @async
     * @method decrypt
     * @param {EncryptionResult} encryptedData - Result from encrypt method
     * @param {CryptoKey} key - Decryption key (must support 'decrypt' operation)
     * @returns {Promise<ArrayBuffer>} Decrypted data as ArrayBuffer
     * 
     * @throws {CryptographicError} When decryption fails or authentication fails
     * 
     * @example
     * const decrypted = await service.decrypt(encryptionResult, key);
     * const text = new TextDecoder().decode(decrypted);
     * console.log(text); // 'Hello, World!'
     * 
     * @example
     * // Handle decryption errors
     * try {
     *     const decrypted = await service.decrypt(corruptedData, key);
     * } catch (error) {
     *     if (error instanceof CryptographicError) {
     *         console.error('Decryption failed:', error.message);
     *     }
     * }
     */
    async decrypt(encryptedData, key) {
        try {
            // Validate inputs
            this._validateDecryptionInput(encryptedData, key);
            
            // Perform decryption with authentication verification
            const decrypted = await crypto.subtle.decrypt(
                {
                    name: this.options.algorithm,
                    iv: encryptedData.iv
                },
                key,
                encryptedData.encrypted
            );
            
            return decrypted;
            
        } catch (error) {
            throw new CryptographicError(
                'Decryption operation failed - data may be corrupted or key incorrect',
                'decrypt',
                error
            );
        }
    }
    
    /**
     * Generates a new cryptographic key for encryption/decryption operations.
     * 
     * Creates a new AES key with the configured key length that can be used
     * for both encryption and decryption operations. The key is not extractable
     * for security purposes.
     * 
     * @async
     * @method generateKey
     * @returns {Promise<CryptoKey>} New cryptographic key
     * 
     * @throws {CryptographicError} When key generation fails
     * 
     * @example
     * const key = await service.generateKey();
     * // Use key for encryption/decryption operations
     */
    async generateKey() {
        try {
            return await crypto.subtle.generateKey(
                {
                    name: this.options.algorithm,
                    length: this.options.keyLength
                },
                false, // Not extractable for security
                ['encrypt', 'decrypt']
            );
        } catch (error) {
            throw new CryptographicError(
                'Key generation failed',
                'generateKey',
                error
            );
        }
    }
    
    /**
     * Imports a key from raw key material.
     * 
     * @async
     * @method importKey
     * @param {ArrayBuffer} keyData - Raw key material
     * @returns {Promise<CryptoKey>} Imported cryptographic key
     * 
     * @throws {CryptographicError} When key import fails
     */
    async importKey(keyData) {
        try {
            return await crypto.subtle.importKey(
                'raw',
                keyData,
                {
                    name: this.options.algorithm,
                    length: this.options.keyLength
                },
                false, // Not extractable for security
                ['encrypt', 'decrypt']
            );
        } catch (error) {
            throw new CryptographicError(
                'Key import failed',
                'importKey',
                error
            );
        }
    }
    
    /**
     * Generates a cryptographically secure random IV.
     * 
     * @private
     * @method _generateSecureIV
     * @returns {Uint8Array} Random IV of configured length
     */
    _generateSecureIV() {
        return crypto.getRandomValues(new Uint8Array(this.options.ivLength));
    }
    
    /**
     * Validates service configuration options.
     * 
     * @private
     * @method _validateOptions
     * @throws {CryptographicError} When configuration is invalid
     */
    _validateOptions() {
        const { algorithm, keyLength, ivLength } = this.options;
        
        // Validate algorithm
        const supportedAlgorithms = ['AES-GCM', 'AES-CBC'];
        if (!supportedAlgorithms.includes(algorithm)) {
            throw new CryptographicError(
                `Unsupported algorithm: ${algorithm}. Supported: ${supportedAlgorithms.join(', ')}`,
                'validateOptions'
            );
        }
        
        // Validate key length
        const supportedKeyLengths = [128, 192, 256];
        if (!supportedKeyLengths.includes(keyLength)) {
            throw new CryptographicError(
                `Unsupported key length: ${keyLength}. Supported: ${supportedKeyLengths.join(', ')}`,
                'validateOptions'
            );
        }
        
        // Validate IV length based on algorithm
        const expectedIvLength = algorithm === 'AES-GCM' ? 12 : 16;
        if (ivLength !== expectedIvLength) {
            throw new CryptographicError(
                `Invalid IV length for ${algorithm}: ${ivLength}. Expected: ${expectedIvLength}`,
                'validateOptions'
            );
        }
        
        // Prohibit ECB mode explicitly
        if (algorithm.includes('ECB')) {
            throw new CryptographicError(
                'ECB mode is not allowed due to security vulnerabilities',
                'validateOptions'
            );
        }
    }
    
    /**
     * Validates encryption input parameters.
     * 
     * @private
     * @method _validateEncryptionInput
     * @param {*} data - Data to validate
     * @param {*} key - Key to validate
     * @returns {ArrayBuffer} Validated data as ArrayBuffer
     * @throws {CryptographicError} When validation fails
     */
    _validateEncryptionInput(data, key) {
        // Validate key
        if (!key || !(key instanceof CryptoKey)) {
            throw new CryptographicError(
                'Invalid encryption key provided',
                'validateEncryptionInput'
            );
        }
        
        // Validate data
        if (data === null || data === undefined) {
            throw new CryptographicError(
                'Data to encrypt cannot be null or undefined',
                'validateEncryptionInput'
            );
        }
        
        // Convert data to ArrayBuffer
        let arrayBuffer;
        if (typeof data === 'string') {
            arrayBuffer = new TextEncoder().encode(data);
        } else if (data instanceof ArrayBuffer) {
            arrayBuffer = data;
        } else if (data instanceof Uint8Array) {
            arrayBuffer = data.buffer;
        } else {
            // Try to convert to string first
            try {
                const stringData = JSON.stringify(data);
                arrayBuffer = new TextEncoder().encode(stringData);
            } catch (error) {
                throw new CryptographicError(
                    'Data must be string, ArrayBuffer, or Uint8Array',
                    'validateEncryptionInput',
                    error
                );
            }
        }
        
        // Check data size limits (1MB max for performance)
        if (arrayBuffer.byteLength > 1024 * 1024) {
            throw new CryptographicError(
                'Data size exceeds maximum limit of 1MB',
                'validateEncryptionInput'
            );
        }
        
        return arrayBuffer;
    }
    
    /**
     * Validates decryption input parameters.
     * 
     * @private
     * @method _validateDecryptionInput
     * @param {*} encryptedData - Encrypted data to validate
     * @param {*} key - Key to validate
     * @throws {CryptographicError} When validation fails
     */
    _validateDecryptionInput(encryptedData, key) {
        // Validate key
        if (!key || !(key instanceof CryptoKey)) {
            throw new CryptographicError(
                'Invalid decryption key provided',
                'validateDecryptionInput'
            );
        }
        
        // Validate encrypted data structure
        if (!encryptedData || typeof encryptedData !== 'object') {
            throw new CryptographicError(
                'Invalid encrypted data structure',
                'validateDecryptionInput'
            );
        }
        
        // Validate required properties
        if (!encryptedData.encrypted || !encryptedData.iv) {
            throw new CryptographicError(
                'Encrypted data must contain both encrypted data and IV',
                'validateDecryptionInput'
            );
        }
        
        // Validate IV length
        if (!(encryptedData.iv instanceof Uint8Array) || 
            encryptedData.iv.length !== this.options.ivLength) {
            throw new CryptographicError(
                `Invalid IV length: expected ${this.options.ivLength} bytes`,
                'validateDecryptionInput'
            );
        }
        
        // Validate encrypted data
        if (!(encryptedData.encrypted instanceof ArrayBuffer)) {
            throw new CryptographicError(
                'Encrypted data must be an ArrayBuffer',
                'validateDecryptionInput'
            );
        }
    }
}

/**
 * Result object returned by encryption operations.
 * 
 * @typedef {Object} EncryptionResult
 * @property {ArrayBuffer} encrypted - The encrypted data
 * @property {Uint8Array} iv - The initialization vector used
 * @property {string} algorithm - The encryption algorithm used
 * @property {string} timestamp - ISO timestamp of encryption
 */

export default EncryptionService;