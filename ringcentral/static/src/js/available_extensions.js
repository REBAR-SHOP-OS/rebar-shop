/** @odoo-module **/

import { Component } from "@odoo/owl";


export class AvailableExtensions extends Component {
    static template = "ringcentral.available.extensions";

    render_available_extensions() {
        document.querySelector(".render_available_extensions").classList.add('d-none')
        document.querySelector(".available-extension-header").classList.add('d-none')
        document.querySelector(".fetching-header").classList.remove('d-none')
        this.props.widget.render_available_extensions()
        setTimeout(this.fetchingCalls, 2000)
    }

    fetchingCalls() {
        document.querySelector(".render_available_extensions").classList.remove('d-none')
        document.querySelector(".available-extension-header").classList.remove('d-none')
        document.querySelector(".fetching-header").classList.add('d-none')
    }
}

AvailableExtensions.props = {
    widget: { type: Object, optional: true },
    available_extensions: { type: Object, optional: true },
    slots: { optional: true },
};
