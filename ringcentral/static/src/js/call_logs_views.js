/** @odoo-module **/

import { Component } from "@odoo/owl";

export class CallLogsViews extends Component {

    onClickCallDial(ev, call) {
        var call_from = call.from
        this.props.widget.dial_call_contact_detail(ev, call_from)
    }
}

CallLogsViews.template = "ringcentral.all_calllog";
CallLogsViews.props = {
    all_calls: { type: Object, optional: true },
    widget: { type: Object, optional: true },
    slots: { optional: true },
    record_length: { optional: true },
};
