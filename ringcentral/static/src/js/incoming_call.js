/** @odoo-module **/

import { Component, useChildSubEnv } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";


Dialog.props = {
    ...Dialog.props,
    closeOnClick: { optional: true },
    secondaryClick: { optional: true },
};

export class IncomingCall extends Component {
    static components = { Dialog }
    static props = ['close', 'from_number', 'from_name', 'title', 'table_list', 'session', 'contacts', 'call', 'incoming_call_number', 'username', 'data', 'partner_exists', 'contacts_action', 'call_from_number_list', 'openWindow'];
    static template = "ringcentral.incoming_call";
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.acceptOptions = {
            media: {
                render: {
                    remote: document.querySelector("#remoteVideo"),
                    local: document.querySelector("#localVideo"),
                },
            },
        };
    }
    async decline() {
        this.props.session.rejected();
        this.props.close()
    }

    async answer() {
        try {
            await this.props.session.accept(this.acceptOptions);
            var to_name = "";
            var from_name = "";
            for (var i = 0; i < this.props.contacts.length; i++) {
                if (
                    (this.props.contacts[i].phone &&
                        this.props.contacts[i].phone.indexOf(
                            this.props.incoming_call_number
                        ) > -1) ||
                    (this.props.contacts[i].mobile &&
                        this.props.contacts[i].mobile.indexOf(
                            this.props.incoming_call_number
                        ) > -1)
                ) {
                    from_name = this.props.contacts[i].name;
                    break;
                }
            }
            this.props.call.onAccepted(
                this.props.session,
                this.props.incoming_call_number,
                this.props.username,
                "in_bound",
                from_name,
                this.props.incoming_call_number,
                this.props.data
            );
        } catch (e) {
            console.error("Error in answer function:", e);
        }
        this.props.close()
    }

    async createPartner(e) {
        var new_contact = await this.rpc('/create_new_contact', {
            caller_number: this.props.incoming_call_number,
            caller_name: this.props.from_number
        })
        window.open(
            window.location.origin +
            "#id=" +
            parseInt(new_contact) +
            "&action=" +
            this.props.contacts_action +
            "&model=res.partner&view_type=form",
            "_blank"
        );
    }

    async forwardForm(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var forward_to = ev.view.document.querySelector("input[name=forward]").value
        if (forward_to) {
            this.props.session.forward(forward_to,
                this.acceptOptions
            ).catch(function (e) {
                console.log("Forward failed", e.stack || e);
            });
        }
    }

}

