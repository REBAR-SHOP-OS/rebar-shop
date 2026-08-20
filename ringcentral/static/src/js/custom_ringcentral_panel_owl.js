/** @odoo-module **/

import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { loadJS } from "@web/core/assets";
import { RingcentralPanelView } from "./panel_view_ringcentral";  // Owl component for the RingCentral panel

export const RingCentralService = {
    dependencies: ["rpc", "user"],
    async start(env, { rpc, user }) {
        session.loggedin = false;

        const isRingCentralUser = await user.hasGroup("ringcentral.ringcentral_user");
        if (!isRingCentralUser) return;

        const data = await rpc("/ringcentral_credentials", {
            company_id: session.user_companies.current_company,
            uid: session.uid,
        });

        if (!(data.ringcentral_server && data.ringcentral_app_key && data.ringcentral_app_secret &&
              data.ringcentral_redirect_uri && data.ringcentral_app_host && data.ringcentral_app_port)) {
            return;
        }

        await loadJS("/ringcentral/static/src/lib/promise.js");
        await loadJS("/ringcentral/static/src/lib/fetch.js");
        await loadJS("/ringcentral/static/src/lib/axios.js");
        await loadJS("/ringcentral/static/src/lib/sip.js");
        await loadJS("/ringcentral/static/src/lib/pubnub.js");
        await loadJS("/ringcentral/static/src/lib/ringcentral.js");
        await loadJS("/ringcentral/static/src/lib/ringcentral-web-phone.js");
        await loadJS("/ringcentral/static/src/lib/jquery.slidemenu.js");

        const container = document.createElement("div");
        document.body.appendChild(container);

        const panelComp = new RingcentralPanelView(env, { rcData: data });
        await panelComp.mount(container);

        $("#ring_central_panel_container").removeClass("d-none").on("click", () => {
            $("#ringcentral_menu").slideToggle("slow", "linear");
        });

        $("#ringcentral_menu").slidemenu();
        return panelComp;
    },
};

registry.category("services").add("ringcentralPanel", RingCentralService);