# Code Review Checklist for Security & Technical Improvements

## Security-Focused Reviews (Issues #1, #2, #5, #6)

### Cryptographic Changes Checklist
- [ ] **No hardcoded IVs**: Verify all IVs are generated using `crypto.getRandomValues()`
- [ ] **No ECB mode**: Confirm no ECB encryption mode is used anywhere
- [ ] **Proper IV handling**: IV is prepended to ciphertext and extracted correctly
- [ ] **Key management**: Keys are handled securely and not logged
- [ ] **Error handling**: Cryptographic errors are handled without exposing sensitive info
- [ ] **Testing**: Comprehensive tests cover all crypto operations and edge cases

### Input Validation Checklist
- [ ] **All entry points validated**: Every user input has validation
- [ ] **Sanitization**: Input is properly sanitized for output context
- [ ] **Type checking**: Proper type validation is implemented
- [ ] **Boundary checks**: Length and size limits are enforced
- [ ] **SQL injection prevention**: Parameterized queries are used
- [ ] **XSS prevention**: Output is properly escaped

### Error Handling Checklist
- [ ] **No silent failures**: All errors are properly handled or logged
- [ ] **Consistent patterns**: Error handling follows established patterns
- [ ] **Security context**: No sensitive information in error messages
- [ ] **Logging**: Appropriate error logging without sensitive data
- [ ] **User experience**: User-friendly error messages for client-facing errors

## Code Quality Reviews (Issues #3, #4, #7, #8, #9)

### Refactoring Checklist
- [ ] **Single responsibility**: Each module has one clear purpose
- [ ] **File size**: No file exceeds 300 lines
- [ ] **Dependencies**: Clear import/export structure
- [ ] **Backward compatibility**: Existing functionality preserved
- [ ] **Documentation**: Refactored code is properly documented

### Modernization Checklist
- [ ] **No var declarations**: All variables use `const` or `let`
- [ ] **Arrow functions**: Appropriate use of arrow functions
- [ ] **Destructuring**: Object/array destructuring where beneficial
- [ ] **Template literals**: String interpolation uses template literals
- [ ] **Async/await**: Modern async patterns instead of callbacks
- [ ] **ES6+ features**: Appropriate use of modern JavaScript features

### Testing Checklist
- [ ] **Coverage**: 90%+ code coverage achieved
- [ ] **Unit tests**: All functions have unit tests
- [ ] **Integration tests**: Component interactions tested
- [ ] **Edge cases**: Boundary conditions and error scenarios tested
- [ ] **Performance**: No significant performance regression
- [ ] **CI integration**: Tests run automatically in pipeline

### Documentation Checklist
- [ ] **JSDoc comments**: All public functions documented
- [ ] **Module headers**: File-level documentation present
- [ ] **Examples**: Usage examples provided for complex functions
- [ ] **Type definitions**: Custom types documented
- [ ] **Generated docs**: Documentation builds without errors

### Linting Checklist
- [ ] **No linting errors**: Code passes all linting rules
- [ ] **Consistent style**: Code follows established style guide
- [ ] **Security rules**: Security-focused linting rules pass
- [ ] **Import organization**: Imports are properly organized
- [ ] **Pre-commit hooks**: Hooks prevent bad commits

## Python/Django Reviews (Issue #10)

### Auditlog Enhancement Checklist
- [ ] **Selective logging**: User-based logging configuration works
- [ ] **Read operations**: Read logging functions correctly when enabled
- [ ] **Bulk operations**: Bulk operations are properly logged
- [ ] **Performance**: No significant performance impact
- [ ] **Migration**: Existing data migrates correctly
- [ ] **Configuration**: New settings are properly documented
- [ ] **Backward compatibility**: Existing functionality preserved

## General Review Guidelines

### Before Merging
- [ ] **All acceptance criteria met**: Every requirement in issue is satisfied
- [ ] **Tests pass**: All automated tests pass
- [ ] **Security scan**: No new security vulnerabilities introduced
- [ ] **Performance**: No significant performance regression
- [ ] **Documentation updated**: Relevant docs reflect changes
- [ ] **Breaking changes**: Any breaking changes are documented

### Post-Merge Actions
- [ ] **Deploy to staging**: Changes deployed to staging environment
- [ ] **Manual testing**: Manual QA performed on staging
- [ ] **Monitoring**: Error rates and performance monitored
- [ ] **Documentation**: User-facing documentation updated if needed
- [ ] **Team notification**: Team notified of significant changes