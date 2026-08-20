/** @odoo-module **/

import { Component, onMounted, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class MessageChatBoxDialogchatbox extends Component {

    setup() {
        this.orm = useService('orm')
        this.action = useService("action");
        this.notification = useService("notification");

        onMounted(async () => {
            const element = $("#scroll_messge");
            element.animate(
                {
                    scrollTop: element.prop("scrollHeight"),
                },
                600
            );
            this.content = document.querySelector(".modal-content");
            this.content_data = document.querySelector(".modal-body")
        });
    }
    onKeydownInput(ev) {
        switch (ev.key) {
            case "Enter":
                this.confirm(ev)
                break;
        }
    }
    async contactinfo(ev, title, PhoneNumber) {
        try {
            var domain = [
                "|",
                ["name", "ilike", title],
                ["phone", "ilike", PhoneNumber]
            ];
            const record = await this.orm.call("res.partner", 'search', [domain])

            if (record.length == 0) {
                var additional_values = {
                    'default_phone': PhoneNumber
                }
                this.action.doAction({
                    type: 'ir.actions.act_window',
                    name: _t('Contacts'),
                    res_model: 'res.partner',
                    views: [[false, "form"]],
                    context: additional_values,
                    target: "new"
                });
            }
            else {
                this.action.doAction({
                    type: 'ir.actions.act_window',
                    name: _t('Contacts'),
                    res_model: 'res.partner',
                    views: [[false, 'tree'], [false, 'form']],
                    domain: [
                        "|",
                        ["name", "ilike", title],
                        ["phone", "ilike", PhoneNumber]
                    ],
                });
            }
        }
        catch (error) {
            const errorMessage = "An error occurred";
            this.notification.add(_t(errorMessage), { type: "warning" });
        }
    }

    discardPopup() {
        this.props.close();
    }
    preventDrag(event) {
        event.preventDefault();
    }

    confirm(e) {
        var fileinput = document.querySelector("#popup_file")
        this.props.widget.send_popup_msg(e, this.props.phoneNumber,fileinput);
    }
    Minimize() {
        var headerdialog = document.querySelector("#title_dialog").parentElement
        document.querySelector("#minimize").classList.add("d-none")
        document.querySelector("#maximize").classList.remove("d-none")
        headerdialog.setAttribute('style', ' background: #5b97d8;color: white; ');
        this.content_data.classList?.add("modal-chabox-hide")
        $("#chatbox .modal-footer").hide()
    }

    maximize() {
        var headerdialog = document.querySelector("#title_dialog").parentElement
        document.querySelector("#maximize").classList.add("d-none")
        document.querySelector("#minimize").classList.remove("d-none")
        headerdialog.removeAttribute('style', 'background: #5b97d8;color: white; ');
        this.content_data.classList?.remove("modal-chabox-hide")
        $("#chatbox .modal-footer").show()
    }
}

MessageChatBoxDialogchatbox.template = "ringcentral.chatbox";
MessageChatBoxDialogchatbox.components = { Dialog };
MessageChatBoxDialogchatbox.props = {
    close: Function,
    widget: { type: Object },
    messages: { type: Object },
    title: { type: String },
    phoneNumber: { optional: true },
};
