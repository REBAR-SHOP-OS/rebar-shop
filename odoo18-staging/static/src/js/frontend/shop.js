/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { EncryptionService } from "../crypto/encryption_service";
import { InputValidator } from "../validation/input_validator";
import { ErrorHandler } from "../utils/error_handler";

/**
 * @fileoverview Frontend shop component for Rebar Shop
 * 
 * This module provides the public-facing shop interface with enhanced
 * security features and modern JavaScript patterns for Odoo 18.
 * 
 * @author Rebar Shop Development Team
 * @version 18.0.1.0.0
 * @since 1.0.0
 */

export class RebarShopFrontend extends Component {
    static template = "rebar_shop_staging.ShopTemplate";
    static props = {
        context: { type: Object, optional: true },
        products: { type: Array, optional: true },
    };

    setup() {
        // Odoo 18 frontend services
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.router = useService("router");

        // Component state
        this.state = useState({
            products: this.props.products || [],
            categories: [],
            cart: [],
            loading: false,
            searchTerm: "",
            selectedCategory: null,
            currentPage: 1,
            totalPages: 1,
            isLoggedIn: false,
        });

        // Initialize services
        this.encryptionService = new EncryptionService();
        this.inputValidator = new InputValidator();
        this.errorHandler = new ErrorHandler();

        // Lifecycle hooks
        onWillStart(this.onWillStart);
        onMounted(this.onMounted);
    }

    async onWillStart() {
        try {
            this.state.loading = true;
            await Promise.all([
                this._loadProducts(),
                this._loadCategories(),
                this._checkLoginStatus()
            ]);
        } catch (error) {
            this.errorHandler.handle(error, {
                component: 'RebarShopFrontend',
                method: 'onWillStart'
            });
        } finally {
            this.state.loading = false;
        }
    }

    onMounted() {
        this._setupEventListeners();
        this._initializeUI();
    }

    async _loadProducts() {
        try {
            const domain = [['website_published', '=', true]];
            
            if (this.state.searchTerm) {
                domain.push(['name', 'ilike', this.state.searchTerm]);
            }
            
            if (this.state.selectedCategory) {
                domain.push(['public_categ_ids', 'in', [this.state.selectedCategory]]);
            }

            const result = await this.rpc('/shop/products', {
                domain: domain,
                page: this.state.currentPage,
                limit: 12
            });

            this.state.products = result.products;
            this.state.totalPages = result.total_pages;
        } catch (error) {
            this.errorHandler.handle(error, {
                component: 'RebarShopFrontend',
                method: '_loadProducts'
            });
        }
    }

    async _loadCategories() {
        try {
            const categories = await this.rpc('/shop/categories', {});
            this.state.categories = categories;
        } catch (error) {
            this.errorHandler.handle(error, {
                component: 'RebarShopFrontend',
                method: '_loadCategories'
            });
        }
    }

    async _checkLoginStatus() {
        try {
            const result = await this.rpc('/web/session/get_session_info', {});
            this.state.isLoggedIn = result.uid && result.uid !== false;
        } catch (error) {
            this.state.isLoggedIn = false;
        }
    }

    onSearchProducts = this._debounce(async (event) => {
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
                    'Invalid search term',
                    { type: 'warning' }
                );
                return;
            }
            
            this.state.searchTerm = validatedInput.value;
            this.state.currentPage = 1;
            await this._loadProducts();
            
        } catch (error) {
            this.errorHandler.handle(error, {
                component: 'RebarShopFrontend',
                method: 'onSearchProducts'
            });
        }
    }, 300);

    async onCategoryChange(categoryId) {
        try {
            this.state.selectedCategory = categoryId;
            this.state.currentPage = 1;
            await this._loadProducts();
        } catch (error) {
            this.errorHandler.handle(error, {
                component: 'RebarShopFrontend',
                method: 'onCategoryChange'
            });
        }
    }

    async onAddToCart(productId, quantity = 1) {
        try {
            if (!this.state.isLoggedIn) {
                this.notification.add(
                    'Please log in to add items to cart',
                    { type: 'warning' }
                );
                return;
            }

            const validatedData = this.inputValidator.validate({
                productId: productId,
                quantity: quantity
            }, {
                productId: { type: 'integer', min: 1, required: true },
                quantity: { type: 'integer', min: 1, max: 1000, required: true }
            });

            await this.rpc('/shop/cart/add', {
                product_id: validatedData.productId,
                quantity: validatedData.quantity
            });

            this.notification.add(
                'Product added to cart successfully!',
                { type: 'success' }
            );

        } catch (error) {
            this.errorHandler.handle(error, {
                component: 'RebarShopFrontend',
                method: 'onAddToCart',
                productId: productId
            });
        }
    }

    _setupEventListeners() {
        // Handle browser navigation
        window.addEventListener('popstate', this._handlePopState.bind(this));
    }

    _initializeUI() {
        // Initialize any UI components
    }

    _handlePopState(event) {
        // Handle browser back/forward navigation
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
        window.removeEventListener('popstate', this._handlePopState);
    }
}

// Register component for frontend use
registry.category("public_components").add("rebar_shop_frontend", RebarShopFrontend);

export default RebarShopFrontend;