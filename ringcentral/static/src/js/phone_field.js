/** @odoo-module **/

import { session } from '@web/session';
import { useService } from "@web/core/utils/hooks";
import { PhoneField } from "@web/views/fields/phone/phone_field";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";


const { onWillStart, Component } = owl;

export class CallRingCentral extends Component {
    async setup() {
        this.action = useService("action");
        this.user = useService("user");
        this.title = _t("Ring Central Call");
        onWillStart(async () => {
            this.isRingCentralUser = await this.user.hasGroup(
                "ringcentral.ringcentral_user"
            );
        });
    }
    onClick(ev) {
        ev.preventDefault();
        const input = this.props.name
        const value_found = this.props.record._textValues.hasOwnProperty(input)
        if (input && value_found) {
            var contact_number = this.props.record._textValues[input]
        }
        if (session.ringcentralPanel && contact_number) {
            this.env.bus.trigger("make-Call", contact_number);
        }
    }
}
CallRingCentral.template = "ringcentral.CallRingCentral";

patch(PhoneField, {
    components: {
        ...PhoneField.components,
        CallRingCentral
    },
    defaultProps: {
        ...PhoneField.defaultProps,
        enableButton: true,

    },
    props: {
        ...PhoneField.props,
        enableButton: { type: Boolean, optional: true },
    },
    extractProps: ({ attrs }) => {
        return {
            enableButton: attrs.options.enable_sms,
            placeholder: attrs.placeholder,
        };
    },
});