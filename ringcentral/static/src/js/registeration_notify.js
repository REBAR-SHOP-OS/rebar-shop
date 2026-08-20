/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

export class RegisterEventNotify extends Component {
    static components = { Dropdown, DropdownItem };
    static template = "ringcentral.registerEventNotification";

    setup() {
        this.rpc = useService("rpc");
        this.user = useService("user");
        this.state = useState({});
        // No special props; using bus for updates
        onMounted(async () => {
            // Remove icon if user not allowed to use RingCentral
            const isRingCentralUser = await this.user.hasGroup("ringcentral.ringcentral_user");
            if (!isRingCentralUser) {
                this.el.remove();  // remove the systray icon from DOM
                return;
            }
            // Set initial status appearance based on login state
            if (!session.loggedin) {
                // Not logged in: show "Offline" status in red with crossed-out icon
                $('.status-content').text('RingCentral Offline');
                $('.ringcentral-notify').attr("style", "background-color:red !important;");
                $('.ringcentral-notify i').addClass('gly-rotate-45');
            }
            // Listen for registration status events from RingCentral panel
            this.env.bus.addEventListener("registration-notification", (ev) => {
                const status = ev.detail;
                if (status === "success") {
                    // Connected: show "Online" status
                    $('.ringcentral-notify i').removeClass('gly-rotate-45');
                    $('.status-content').text('RingCentral Online');
                    $('.ringcentral-notify').attr("style", "background-color:#56374e !important;");
                    this.env.bus.trigger("registration-buttons", { detail: "success" });
                } else if (status === "logout" || status === "failed") {
                    // Disconnected: show "Offline" status
                    $('.status-content').text('RingCentral Offline');
                    $('.ringcentral-notify').attr("style", "background-color:red !important;");
                    $('.ringcentral-notify i').addClass('gly-rotate-45');
                    this.env.bus.trigger("registration-buttons", { detail: "logout" });
                }
            });
        });
    }
}

// Register the systray item (phone status indicator)
export const RegisterNotification = { Component: RegisterEventNotify };
registry.category("systray").add("ringcentral.registerEventNotification", RegisterNotification, { sequence: 101 });
