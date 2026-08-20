/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

export class AudioField extends Component {
    
    static props = { ...standardFieldProps };

    setup(){
        super.setup()
        this.props.value = this.props.record.data.ringcentral_call_url
    }
}
AudioField.template = "web.AudioField";

export const audioField = {
    component: AudioField,
    supportedTypes: ["char"],
};

registry.category("fields").add("audio_field", audioField);
