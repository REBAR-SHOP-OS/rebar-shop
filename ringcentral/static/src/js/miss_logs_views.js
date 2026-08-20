/** @odoo-module **/

import { Component } from "@odoo/owl";

export class MissedCallLogsViews extends Component {

    onClickDial(ev, call) {
        var call_from = call.from
        this.props.widget.dial_call_contact_detail(ev, call_from)
    }
}

MissedCallLogsViews.template = "ringcentral.miss_calllog";

MissedCallLogsViews.props = {
    widget: { type: Object, optional: true },
    all_calls: { type: Object, optional: true },
    record_length: { optional: true },
    slots: { type: Object, optional: true },
};
