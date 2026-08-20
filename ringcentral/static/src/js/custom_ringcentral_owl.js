/** @odoo-module **/
import { session } from '@web/session';
import { RingcentralPanelView } from "./panel_view_ringcentral";
import { View } from "@web/views/view";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";


patch(View.prototype, {
    async setup() {
        super.setup();
        this.action = useService("action");
        this.orm = useService("orm");
        this.user = useService("user");
        this.rpc = useService("rpc");
        this.isRingCentralUser = await this.user.hasGroup(
            "ringcentral.ringcentral_user"
        );
    },
    async loadView(props) {
        const columns = super.loadView(...arguments);
        var self = this;
        var data = await this.rpc("/ringcentral_credentials", {
            company_id: session.user_companies.current_company,
            uid: session.uid,
        })
        this.isRingCentralUser = await this.user.hasGroup(
            "ringcentral.ringcentral_user"
        );
        if (this.isRingCentralUser && data.ringcentral_server &&
            data.ringcentral_app_key &&
            data.ringcentral_app_secret &&
            data.ringcentral_redirect_uri &&
            data.ringcentral_app_host &&
            data.ringcentral_app_port) {
                
            document.querySelector('#ring_central_panel_container')?.classList.remove('d-none')
            await this.set_ringcentral_sidebar();
            if (this.ringcentralPanel) {
                $("#ringcentral_menu").slidemenu();
                $("#ring_central_panel_container")
                    ?.on("click", function () {
                        $("#ringcentral_menu")
                            ?.slideToggle("slow", "linear");
                    });
            }
        }
        return columns
    },
    set_ringcentral_sidebar() {
        var self = this;
        $(".nav-tabs a").on("click", function (ev) {
            ev.preventDefault();
            $(ev.currentTarget).tab("show");
        });
        this.ringcentralPanel = new RingcentralPanelView(self)
        session.ringcentralPanel = this.ringcentralPanel
    },
});
