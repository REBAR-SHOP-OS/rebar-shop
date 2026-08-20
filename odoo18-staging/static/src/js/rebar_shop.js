/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { EncryptionService } from "./crypto/encryption_service";
import { InputValidator } from "./validation/input_validator";
import { ErrorHandler } from "./utils/error_handler";

export class RebarShopComponent extends Component {
    static template = "rebar_shop_staging.RebarShopTemplate";
    static props = {
        context: { type: Object, optional: true },
        domain: { type: Array, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.user = useService("user");
        this.state = useState({
            products: [],
            loading: false,
            error: null,
            searchTerm: "",
            selectedCategory: null,
            cart: [],
            isAuthenticated: false,
        });
        this.encryptionService = new EncryptionService({
            algorithm: 'AES-GCM',
            keyLength: 256,
            ivLength: 12
        });
        this.inputValidator = new InputValidator();
        this.errorHandler = new ErrorHandler();
        // Bind debounced search handler as a method for use in templates
        this.onSearchProducts = this._debounce(this._onSearchProducts.bind(this), 300);
        onWillStart(this.onWillStart);
        onMounted(this.onMounted);
    }

    async onWillStart() {
        try {
            this.state.loading = true;
            await this._initializeEncryption();
            await this._loadProducts();
            this.state.isAuthenticated = await this._checkAuthentication();
        } catch (error) {
            this.errorHandler.handle(error, { 
                component: 'RebarShopComponent',
                method: 'onWillStart' 
            });
            this.state.error = 'Failed to initialize application';
        } finally {
            this.state.loading = false;
        }
    }

    onMounted() {
        this._setupEventListeners();
        this._initializeUI();
        this._startPeriodicRefresh();
    }

    async _loadProducts() {
        try {
            const searchParams = this.inputValidator.validate({
                search: this.state.searchTerm,
                category: this.state.selectedCategory,
                limit: 50
            }, {
                search: { 
                    type: 'string', 
                    maxLength: 100, 
                    pattern: /^[a-zA-Z0-9\s\-_]*$/ 
                },
                category: { 
                    type: 'string', 
                    enum: ['steel', 'concrete', 'tools', 'accessories'],
                    required: false 
                },
                limit: { 
                    type: 'integer', 
                    min: 1, 
                    max: 100 
                }
            });
            const domain = [['active', '=', true]];
            if (searchParams.search) {
                domain.push(['name', 'ilike', searchParams.search]);
            }
            if (searchParams.category) {
                domain.push(['category_id.code', '=', searchParams.category]);
            }
            const products = await this.orm.searchRead(
                'product.product',
                domain,
                ['id', 'name', 'list_price', 'image_128', 'description_sale', 'qty_available'],
                { limit: searchParams.limit }
            );
            const encryptedProducts = await Promise.all(
                products.map(product => this._encryptProductData(product))
            );
            this.state.products = encryptedProducts;
        } catch (error) {
            const handledError = this.errorHandler.handle(error, {
                component: 'RebarShopComponent',
                method: '_loadProducts',
                searchParams: { 
                    search: this.state.searchTerm,
                    category: this.state.selectedCategory 
                }
            });
            this.notification.add(
                'Failed to load products. Please try again.',
                { type: 'danger' }
            );
            throw handledError;
        }
    }

    async _encryptProductData(product) {
        try {
            const sensitiveFields = ['list_price', 'description_sale'];
            const encryptedProduct = { ...product };
            for (const field of sensitiveFields) {
                if (product[field]) {
                    const encrypted = await this.encryptionService.encrypt(
                        JSON.stringify(product[field]),
                        this.encryptionKey
                    );
                    encryptedProduct[`${field}_encrypted`] = encrypted;
                }
            }
            return encryptedProduct;
        } catch (error) {
            this.errorHandler.handle(error, {
                component: 'RebarShopComponent',
                method: '_encryptProductData',
                productId: product.id
            });
            return product;
        }
    }

    async _onSearchProducts(event) {
        try {
            const searchTerm = event.target.value;
            const validatedInput = this.inputValidator.validateField(
                searchTerm,
                { 
                    type: 'string', 
                    maxLength: 100, 
                    pattern: /^[a-zA-Z0-9\s\-_]*$/ 
                },
                'search'
            );
            if (validatedInput.errors.length > 0) {
                this.notification.add(
                    'Invalid search term. Please use only letters, numbers, spaces, hyphens, and underscores.',
                    { type: 'warning' }
                );
                return;
            }
            this.state.searchTerm = validatedInput.value;
            await this._loadProducts();
        } catch (error) {
            this.errorHandler.handle(error, {
                component: 'RebarShopComponent',
                method: 'onSearchProducts'
            });
        }
    }

    async onAddToCart(product, quantity = 1) {
        try {
            const validatedData = this.inputValidator.validate({
                productId: product.id,
                quantity: quantity
            }, {
                productId: { type: 'integer', min: 1, required: true },
                quantity: { type: 'integer', min: 1, max: 1000, required: true }
            });
            if (!this.state.isAuthenticated) {
                this.notification.add(
                    'Please log in to add items to cart.',
                    { type: 'warning' }
                );
                return;
            }
            await this.orm.call(
                'sale.order.line',
                'add_to_cart',
                [validatedData.productId, validatedData.quantity],
                { context: this.props.context }
            );
            const existingItem = this.state.cart.find(item => item.product_id === product.id);
            if (existingItem) {
                existingItem.quantity += validatedData.quantity;
            } else {
                this.state.cart.push({
                    product_id: product.id,
                    product_name: product.name,
                    quantity: validatedData.quantity,
                    price: product.list_price
                });
            }
            this.notification.add(
                `${product.name} added to cart successfully!`,
                { type: 'success' }
            );
        } catch (error) {
            const handledError = this.errorHandler.handle(error, {
                component: 'RebarShopComponent',
                method: 'onAddToCart',
                productId: product.id,
                quantity: quantity
            });
            this.notification.add(
                'Failed to add item to cart. Please try again.',
                { type: 'danger' }
            );
        }
    }

    async _initializeEncryption() {
        try {
            this.encryptionKey = await this.encryptionService.generateKey();
        } catch (error) {
            this.errorHandler.handle(error, {
                component: 'RebarShopComponent',
                method: '_initializeEncryption'
            });
            throw new Error('Failed to initialize encryption');
        }
    }

    async _checkAuthentication() {
        try {
            const userContext = this.user.context;
            return userContext.uid && userContext.uid !== false;
        } catch (error) {
            this.errorHandler.handle(error, {
                component: 'RebarShopComponent',
                method: '_checkAuthentication'
            });
            return false;
        }
    }

    _setupEventListeners() {
        window.addEventListener('popstate', this._handlePopState.bind(this));
        document.addEventListener('visibilitychange', this._handleVisibilityChange.bind(this));
    }

    _initializeUI() {}

    _startPeriodicRefresh() {
        this.refreshInterval = setInterval(() => {
            if (!document.hidden && this.state.isAuthenticated) {
                this._loadProducts().catch(error => {
                    this.errorHandler.handle(error, {
                        component: 'RebarShopComponent',
                        method: '_startPeriodicRefresh',
                        silent: true
                    });
                });
            }
        }, 5 * 60 * 1000); // 5 minutes
    }

    _handlePopState(event) {
        if (event.state && event.state.searchTerm !== undefined) {
            this.state.searchTerm = event.state.searchTerm;
            this._loadProducts();
        }
    }

    _handleVisibilityChange() {
        if (document.hidden) {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        } else {
            this._startPeriodicRefresh();
        }
    }

    _debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    willUnmount() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        window.removeEventListener('popstate', this._handlePopState);
        document.removeEventListener('visibilitychange', this._handleVisibilityChange);
    }
}
registry.category("actions").add("rebar_shop_staging.action", RebarShopComponent);
export default RebarShopComponent;
