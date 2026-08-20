/** @odoo-module **/


import { Component, useRef, useState, onMounted } from "@odoo/owl";

export class Contacts extends Component {

    static template = "ringcentral.contacts";

    setup() {
        this.rootRef = useRef("root");
        this.state = useState({
            portalloggedin: true
        })
    }

    show_partner_details(ev, partnerId) {
        this.show_contacts = document.querySelector('#show_contacts')
        this.contact_data = document.querySelector('.contact_data')
        this.show_contacts.classList.add('d-none')
        this.contact_data.classList.remove('d-none')
        this.state.partner_data = partnerId
    }

    backtoMain() {
        this.show_contacts.classList.remove('d-none')
        this.contact_data.classList.add('d-none')
    }
}
Contacts.props = {
    partners_list: { optional: true },
    input_value: { optional: true },
    onClickDial: { optional: true },
    onSearchContact: { optional: true },
    partners_customer: { optional: true },
    partners_suppliers: { optional: true },
    slots: { optional: true }
}