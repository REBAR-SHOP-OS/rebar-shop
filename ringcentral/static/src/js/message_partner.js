/** @odoo-module **/

import { Component, useRef, useState, onMounted } from "@odoo/owl";
import { MessageChatBoxDialogchatbox } from "../js/message_chatbox"
import { useService } from "@web/core/utils/hooks";

export class MessagePartner extends Component {

    static template = "ringcentral.messages_partner";

    setup() {
        this.state = useState({});
        this.dialogService = useService("dialog");
    }

    onChatBoxClick() {
        this.dialogService.add(MessageChatBoxDialogchatbox, {
            title: "Message",
        });
    }
}

MessagePartner.props = {
    all_messages: { optional: true },
    openChatBox: { optional: true },
    slots: { optional: true },
}
