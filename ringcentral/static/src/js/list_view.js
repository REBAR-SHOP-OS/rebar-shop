/** @odoo-module **/
import { registry } from "@web/core/registry";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, useState } from "@odoo/owl";

export class RingcentralListController extends ListController {
    setup() {
        super.setup();
        this.action = useService("action");
        this.orm = useService("orm");
        this.user = useService("user");
        onWillStart(async () => {
            this.isRingCentralUser = await this.user.hasGroup(
                "ringcentral.ringcentral_user"
            );
        });
        this.state = useState({})
        this.state.active = false
        this.env.bus.addEventListener("registration-buttons", (status) => {
            if (status.detail == 'success') {
                this.state.active = true
            }
            if (status.detail == "logout"){
                this.state.active = false
                setTimeout(() => {
                    location.reload(true)
                }, 1000);
            }
        })

    }

    async onClickLogin() {
        const action = await this.orm.call("crm.phonecall", "get_service_uri", [], {});
        const loginUrl = action.split("/login/");
        this.action.doAction({
            type: "ir.actions.act_url",
            url: loginUrl[0],
        });
    }
    onClickSyncPhonecall() {
        this.action.doAction({
            type: "ir.actions.act_window",
            target: "new",
            res_model: "ringcentral.sync",
            views: [[false, "form"]],
        });
    }
    async onClickFetchAgents() {
        await this.orm.call("crm.phonecall", "fetch_agents", [], {});
    }
}

export const RingcentralListView = {
    ...listView,
    Controller: RingcentralListController,
    buttonTemplate: "ringcentral.ListView.Buttons",
};

registry.category("views").add("ringcentral_phonecall_tree", RingcentralListView);
