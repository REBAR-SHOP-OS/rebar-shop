/** @odoo-module **/

import { EncryptionService, CryptographicError } from "../src/js/crypto/encryption_service";

QUnit.module('EncryptionService Tests', function() {
    
    QUnit.test('should create EncryptionService with default options', function(assert) {
        const service = new EncryptionService();
        
        assert.ok(service instanceof EncryptionService, 'Service instance created');
        assert.equal(service.options.algorithm, 'AES-GCM', 'Default algorithm is AES-GCM');
        assert.equal(service.options.keyLength, 256, 'Default key length is 256');
        assert.equal(service.options.ivLength, 12, 'Default IV length is 12 for GCM');
    });
    
    QUnit.test('should reject ECB mode', function(assert) {
        assert.throws(
            () => new EncryptionService({ algorithm: 'AES-ECB' }),
            CryptographicError,
            'ECB mode should be rejected'
        );
    });
    
    QUnit.test('should generate cryptographic key', async function(assert) {
        const service = new EncryptionService();
        
        const key = await service.generateKey();
        
        assert.ok(key instanceof CryptoKey, 'Generated key is CryptoKey instance');
        assert.equal(key.algorithm.name, 'AES-GCM', 'Key algorithm is AES-GCM');
        assert.equal(key.algorithm.length, 256, 'Key length is 256 bits');
    });
    
    QUnit.test('should encrypt and decrypt data successfully', async function(assert) {
        const service = new EncryptionService();
        const key = await service.generateKey();
        const originalData = 'Hello, World!';
        
        const encrypted = await service.encrypt(originalData, key);
        const decrypted = await service.decrypt(encrypted, key);
        const decryptedText = new TextDecoder().decode(decrypted);
        
        assert.equal(decryptedText, originalData, 'Decrypted data matches original');
        assert.ok(encrypted.iv instanceof Uint8Array, 'IV is Uint8Array');
        assert.equal(encrypted.iv.length, 12, 'IV length is 12 bytes for GCM');
    });
    
    QUnit.test('should generate unique IVs', async function(assert) {
        const service = new EncryptionService();
        const key = await service.generateKey();
        const data = 'Test data';
        
        const encrypted1 = await service.encrypt(data, key);
        const encrypted2 = await service.encrypt(data, key);
        
        assert.notDeepEqual(encrypted1.iv, encrypted2.iv, 'IVs should be unique');
    });
    
    QUnit.test('should validate input parameters', async function(assert) {
        const service = new EncryptionService();
        const key = await service.generateKey();
        
        // Test invalid key
        await assert.rejects(
            service.encrypt('data', null),
            CryptographicError,
            'Should reject null key'
        );
        
        // Test invalid data
        await assert.rejects(
            service.encrypt(null, key),
            CryptographicError,
            'Should reject null data'
        );
    });
    
    QUnit.test('should handle large data encryption', async function(assert) {
        const service = new EncryptionService();
        const key = await service.generateKey();
        const largeData = 'x'.repeat(100000); // 100KB
        
        const encrypted = await service.encrypt(largeData, key);
        const decrypted = await service.decrypt(encrypted, key);
        const decryptedText = new TextDecoder().decode(decrypted);
        
        assert.equal(decryptedText, largeData, 'Large data encrypted/decrypted successfully');
    });
    
    QUnit.test('should fail decryption with wrong key', async function(assert) {
        const service = new EncryptionService();
        const key1 = await service.generateKey();
        const key2 = await service.generateKey();
        const data = 'Secret data';
        
        const encrypted = await service.encrypt(data, key1);
        
        await assert.rejects(
            service.decrypt(encrypted, key2),
            CryptographicError,
            'Should fail with wrong key'
        );
    });
    
    QUnit.test('should fail decryption with corrupted data', async function(assert) {
        const service = new EncryptionService();
        const key = await service.generateKey();
        const data = 'Test data';
        
        const encrypted = await service.encrypt(data, key);
        
        // Corrupt the encrypted data
        const corruptedData = new Uint8Array(encrypted.encrypted);
        corruptedData[0] = corruptedData[0] ^ 0xFF;
        
        const corruptedEncrypted = {
            ...encrypted,
            encrypted: corruptedData.buffer
        };
        
        await assert.rejects(
            service.decrypt(corruptedEncrypted, key),
            CryptographicError,
            'Should fail with corrupted data'
        );
    });
});