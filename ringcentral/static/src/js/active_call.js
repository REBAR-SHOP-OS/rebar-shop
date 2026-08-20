/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class ActiveCall extends Component {
    static template = "ringcentral.active.call";
    static props = {}
    setup() {
        this.notification = useService("notification");
    }
    render_active_calls() {
        this.notification.add(_t("Fetching active calls"), { type: "info" });
        document.querySelector(".active-call").classList.add('d-none')
        document.querySelector(".active-call-header").classList.add('d-none')
        document.querySelector(".fetching-header-active").classList.remove('d-none')
        this.env.bus.trigger("fetch-active-calls");
    }

    fetchingCalls() {
        document.querySelector(".active-call").classList.remove('d-none')
        document.querySelector(".active-call-header").classList.remove('d-none')
        document.querySelector(".fetching-header-active").classList.add('d-none')
    }
}

ActiveCall.props = {
    widget: { type: Object, optional: true },
    active_call_list: { type: Object, optional: true },
    slots: { optional: true },
    onClicklisten: { optional: true },
};
