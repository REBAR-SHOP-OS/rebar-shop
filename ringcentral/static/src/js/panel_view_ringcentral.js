/** @odoo-module **/

import { ActiveCall } from "../js/active_call";
import { AvailableExtensions } from "./available_extensions";
import { CallDialog } from "./outgoing_call"
import { Component, useState, onMounted, onWillRender} from "@odoo/owl";
import { CallLogsViews } from "../js/call_logs_views";
import { Contacts } from "../js/contact_render";
import { CallRingCentral } from "./phone_field"
const { DateTime } = luxon;
import { registry } from "@web/core/registry";
import { session } from '@web/session';
import { useService } from "@web/core/utils/hooks";
import { MissedCallLogsViews } from "./miss_logs_views";
import { MessagePartner } from "../js/message_partner";
import { _t } from "@web/core/l10n/translation";
import { IncomingCall } from '../js/incoming_call'
import { MessageChatBoxDialogchatbox } from '../js/message_chatbox'
import { loadJS } from "@web/core/assets";

export class RingcentralPanelView extends Component {
    static template = "ringcentral.PhonecallWidget";
    static props = {}
    static components = { MessageChatBoxDialogchatbox, CallLogsViews, MissedCallLogsViews, Contacts, CallDialog, ActiveCall, AvailableExtensions, MessagePartner, CallRingCentral };

    setup() {
        this.dialogService = useService("dialog");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.rpc = useService("rpc");
        this.orm = useService("orm");
        this.limit = 15;
        this.message_flag = false;
        this.a = 0;
        this.contacts = [];
        this.available_contacts = [];
        this.sdk = null;
        this.platform = null;
        this.webPhone = null;
        this.logLevel = 0;
        this.username = null;
        this.extension = null;
        this.appKey = null;
        this.rcsdk = null;
        this.sipInfo = null;
        this.loggedin = false;
        this.platform = null;
        this.phonecall_about_options = [];
        this.sipProvisionResponse = true;
        this.ContactResponse = true;
        this.ringcentral_server = null;
        this.ringcentral_app_key = null;
        this.ringcentral_app_secret = null;
        this.ringcentral_redirect_uri = null;
        this.ringcentral_app_host = null;
        this.ringcentral_app_port = null;
        this.partner_search_string = "";
        this.contacts_partner = {};
        this.access_token = localStorage.getItem("access_token") || null;
        this.refresh_token = localStorage.getItem("refresh_token") || null;
        this.partner = [];
        this.input_value = ''
        var nowDate = new Date();
        nowDate.setDate(nowDate.getDate() - 7);

        this.env.bus.addEventListener("fetch-active-calls", () => {
            this.render_active_calls()
        })

        this.env.bus.addEventListener("make-Call", (contact_number) => {
            if (contact_number.detail) {
                this.makeCall(contact_number.detail)
            }
            else {
                this.notification.add(_t("Phone number not Found !!."), {
                    type: "info",
                });
            }
        })
        this.dateBefore2days =
            nowDate.getFullYear() +
            "-" +
            (nowDate.getMonth() + 1) +
            "-" +
            nowDate.getDate() +
            "T00:00:00.000Z";

        this.state = useState({})

        onWillRender(async () => {
            loadJS("/ringcentral/static/src/lib/axios.js");
        })

        onMounted(async () => {
            session.loggedin = this.loggedin
            document.querySelector('.nav-tabs a').addEventListener('click', function (ev) {
                ev.preventDefault();
                $(ev.currentTarget).tab("show");
            });
            var data = await this.rpc("/ringcentral_credentials", {
                company_id: session.user_companies.current_company,
                uid: session.uid
            });
            if (
                data.ringcentral_server &&
                data.ringcentral_app_key &&
                data.ringcentral_app_secret &&
                data.ringcentral_redirect_uri &&
                data.ringcentral_app_host &&
                data.ringcentral_app_port) {
                this.ringcentral_server = data.ringcentral_server;
                this.ringcentral_app_key = data.ringcentral_app_key;
                this.ringcentral_app_secret = data.ringcentral_app_secret;
                this.ringcentral_redirect_uri = data.ringcentral_redirect_uri;
                this.ringcentral_app_host = data.ringcentral_app_host;
                this.ringcentral_app_port = data.ringcentral_app_port;
                this.ringcentral_service_uri = data.ringcentral_service_uri;
                this.ringcentral_base_url = data.ringcentral_base_url;
                this.contacts_action = data.contacts_action;
                this.menu_items = document.querySelectorAll('.menu_item_li')

                this.rcsdk = new RingCentral.SDK({
                    appKey: data.ringcentral_app_key,
                    appSecret: data.ringcentral_app_secret,
                    server: data.ringcentral_server,
                });
                this.platform = this.rcsdk.platform();
                if (this.access_token) {
                    this.orm.write("res.users", [session.uid], {
                        ringcentral_access_token: this.access_token,
                    });
                }
                if (this.access_token && this.platform._isAccessTokenValid()) {
                    this.state.portalloggedin = true;
                    document.querySelector(".fa-sign-in").classList.add("d-none");
                    document.querySelector(".fa-sign-out").classList.remove("d-none");
                    document.querySelector(".menu_sign_in_out_li").setAttribute("title", 'Sign Out');
                    document.querySelectorAll(".menu-panels").forEach(panel => panel.style.display = "block");
                    document.querySelector(".menu_sign_in_out_li").nextElementSibling.style.display = "block";
                    this.menu_items.forEach(menu => {
                        menu.classList.remove('d-none');
                    });
                    this.login(
                        data.ringcentral_server,
                        data.ringcentral_app_key,
                        data.ringcentral_app_secret,
                        data.ringcentral_redirect_uri,
                        data.ringcentral_app_host,
                        data.ringcentral_app_port
                    );

                }
                else {
                    this.state.portalloggedin = false;
                    document.querySelector(".fa-sign-in").classList.remove("d-none")
                    document.querySelector(".fa-sign-out").classList.add("d-none")
                    document.querySelector(".menu_sign_in_out_li").setAttribute("title", 'Sign In')
                    this.menu_items.forEach(menu => {
                        menu.classList.add('d-none')
                    });
                }
            }
            const partnerRecords = await this.orm.call('res.partner', 'get_search_read', [], session.context);
            const partnerList = [];
            document.querySelectorAll('.combobox').forEach(element => element.remove());

            const dialerPadInput = document.createElement('input');
            dialerPadInput.setAttribute('name', 'newInputName');
            dialerPadInput.setAttribute('id', 'dialerPad');
            dialerPadInput.setAttribute('class', 'form-control');
            document.querySelector('.ui-widget').appendChild(dialerPadInput);

            const messageRecipientInput = document.createElement('input');
            messageRecipientInput.setAttribute('name', 'messageto');
            messageRecipientInput.setAttribute('placeholder', 'Enter Number');
            messageRecipientInput.setAttribute('id', 'message_to');
            messageRecipientInput.setAttribute('class', 'form-control');
            document.querySelector('#compose_message_child_1 .form-group').appendChild(messageRecipientInput);

            partnerRecords.forEach(partner => {
                const partnerObj = {
                    id: partner[0],
                    name: partner[1],
                    phone: partner[2],
                    email: partner[3],
                    mobile: partner[4],
                    customerRank: partner[5],
                    supplierRank: partner[6],
                };

                partnerList.push(partnerObj);

                const optionText = partnerObj.phone ? `${partnerObj.name} <${partnerObj.phone}>` : `${partnerObj.name} <${partnerObj.mobile}>`;

                const optionForDialerPad = new Option(optionText, partnerObj.phone || partnerObj.mobile);
                dialerPadInput.appendChild(optionForDialerPad);

                const optionForMessageRecipient = new Option(optionText, partnerObj.phone || partnerObj.mobile);
                messageRecipientInput.appendChild(optionForMessageRecipient);

                if (!this.contacts_partner) {
                    this.contacts_partner = {};
                }
                this.contacts_partner[partnerObj.id] = partnerObj;
                this.partner_search_string += this.updatePartnerSearchString(partnerObj);
            });

            const dialerPadDropdown = document.createElement('div');
            dialerPadDropdown.classList.add('dropdown');
            document.querySelector('.ui-widget').appendChild(dialerPadDropdown);

            const messageRecipientDropdown = document.createElement('div');
            messageRecipientDropdown.classList.add('dropdown');
            document.querySelector('#compose_message_child_1 .form-group').appendChild(messageRecipientDropdown);

            const arrayOfInputs = [dialerPadInput, messageRecipientInput];

            arrayOfInputs.forEach((input, index) => {
                input.addEventListener('input', () => {
                    const inputValue = input.value.trim()?.toLowerCase();
                    const currentDropdown = index === 0 ? dialerPadDropdown : messageRecipientDropdown;

                    currentDropdown.innerHTML = '';

                    partnerList.forEach(partnerObj => {
                        const searchString = (partnerObj.phone || partnerObj.name)?.toLowerCase();

                        if (searchString && searchString.includes(inputValue)) {
                            currentDropdown.classList.remove('d-none');
                            createDropdownItem(currentDropdown, input, partnerObj);
                        }

                        const searchStringName = partnerObj.name?.toLowerCase();
                        if (searchStringName && searchStringName.includes(inputValue)) {
                            currentDropdown.classList.remove('d-none');
                            createDropdownItem(currentDropdown, input, partnerObj);
                        }

                        if (inputValue === '') {
                            currentDropdown.classList.add("d-none");
                        }
                    });
                });
            });

            function createDropdownItem(dropdown, inputElement, partnerObj) {
                var option = document.createElement('div');
                option.classList.add('dropdown-item');
                option.textContent = partnerObj.name + " <" + (partnerObj.phone || partnerObj.mobile) + ">";
                option.addEventListener('click', function () {
                    inputElement.value = (partnerObj.phone || partnerObj.mobile);
                    dropdown.innerHTML = '';
                });
                dropdown.appendChild(option);
            }
            this.contacts = partnerList
        });
    }

    updatePartnerSearchString(partner) {
        var str = partner.name;
        if (partner.phone) {
            str += "|" + partner?.phone?.split(" ").join("");
        }
        str = String(partner.id) + ":" + str.replace(":", "") + "\n";
        return str;
    }

    async login_auth() {
        this.logoutbutton = $(".login-auth")
        this.logoutbutton?.hide()
        this.logoutbutton?.attr('disabled', 'disabled')
        setTimeout(() => {
            this.logoutbutton?.show()
            this.logoutbutton?.removeAttr('disabled')
        }, 3000);
        var data = await this.rpc("/ringcentral_credentials", {
            company_id: session.user_companies.current_company,
            uid: session.uid
        });

        this.rcsdk = new RingCentral.SDK({
            appKey: data.ringcentral_app_key,
            appSecret: data.ringcentral_app_secret,
            server: data.ringcentral_server,
        });
        this.platform = this.rcsdk.platform();
        if (this.access_token) {
            this.orm.write("res.users", [session.uid], {
                ringcentral_access_token: this.access_token,
            });
        }
        if (document.querySelector(".fa-sign-in").classList.contains("d-none")) {
            if (this.state.registered) {
                document.querySelector(".fa-sign-out").classList.add("d-none")
                document.querySelector(".fa-sign-in").classList.remove("d-none")
                document.querySelector(".menu_sign_in_out_li").setAttribute("title", 'Sign In')
                document.querySelector(".menu-panels").setAttribute('style', 'display:none;')
                $(".menu-item menu_item_li").siblings().hide();
                this.menu_items.forEach(menu => {
                    menu.classList.add('d-none')
                });
                this.notification.add(_t("Logging you out.."), {
                    type: "info",
                });
                document.querySelector(".loading").classList.remove("d-none");
                this.platform.logout().then(() => {
                    setTimeout(() => {
                        document.querySelector(".fa-sign-out").classList.add("d-none")
                        document.querySelector(".fa-sign-in").classList.remove("d-none")
                        document.querySelector(".menu_sign_in_out_li").setAttribute("title", 'Sign In')
                        document.querySelector(".menu-panels").setAttribute('style', 'display:none;')
                        document.querySelector(".loading").classList.add("d-none");
                        self.webPhone = null;
                        $(".menu-item menu_item_li").siblings().hide();
                        this.env.bus.trigger("registration-notification", ('logout'));
                    }, 5000)
                })
            }
        }
        else if (this.access_token && this.platform._isAccessTokenValid()) {
            const login = await this.login(
                data.ringcentral_server,
                data.ringcentral_app_key,
                data.ringcentral_app_secret,
                data.ringcentral_redirect_uri,
                data.ringcentral_app_host,
                data.ringcentral_app_port
            )
            if (login) {
                this.do_recursive_alert();
            }
        }
        else {
            await this.open_auth_window(
                data.ringcentral_server,
                data.ringcentral_app_key,
                data.ringcentral_app_secret,
                data.ringcentral_redirect_uri,
                data.ringcentral_app_host,
                data.ringcentral_app_port,
            );
        }
    }

    async open_auth_window(server, appKey, appSecret, redirectUri, appHost, appPost) {
        var self = this;
        class OAuthCode {
            constructor(rcsdk, config) {
                self.config = config;
            }
            loginPopup() {
                var authUri = self.rcsdk.platform().authUrl({
                    redirectUri: self.config.RC_APP_REDIRECT_URL,
                });
                this.loginPopupUri(authUri, self.config.RC_APP_REDIRECT_URL);
            }
            loginPopupUri(authUri, redirectUri) {
                var win = window.open(
                    authUri,
                    "windowname1",
                    "width=800, height=600"
                );
                if (win.length > 0) {
                    location.reload(true)
                    win.close()
                }
                if (win.length == 0) {
                    var pollOAuth = window.setInterval(async () => {
                        try {
                            if (win.document) {
                                if (win.document.URL.indexOf("error") != -1) {
                                    window.clearInterval(pollOAuth);
                                    win.close();
                                }
                                else if (win.document.URL.indexOf(redirectUri) != -1) {
                                    window.clearInterval(pollOAuth);
                                    var qs = await self.rcsdk.platform().parseAuthRedirectUrl(win.document.URL);
                                    qs.redirectUri = redirectUri;
                                    win.close();
                                    if ("code" in qs) {
                                        document.querySelector(".loading").classList.remove("d-none");
                                        if (qs) {
                                            try {
                                                var headers = {
                                                    "Content-Type": "application/json",
                                                    Authorization: `Bearer ${self.access_token}`
                                                }
                                                var response = await self.platform.login(qs);
                                                if (response) {
                                                    var obj = JSON.parse(response.text());
                                                    self.loggedin = true;
                                                    self.accesstomenu = true
                                                    self.menu_items.forEach(menu => {
                                                        menu.classList.remove('d-none')
                                                    });
                                                    document.querySelectorAll(".menu-panels").forEach(panel => panel.style.display = "block");
                                                    document.querySelector(".menu_sign_in_out_li").nextElementSibling.style.display = "block";
                                                    document.querySelector(".fa-sign-in").classList.add("d-none");
                                                    document.querySelector(".fa-sign-out").classList.remove("d-none");
                                                    document.querySelector(".menu_sign_in_out_li").setAttribute("title", 'Sign Out');
                                                    localStorage.setItem("access_token", obj.access_token);
                                                    localStorage.setItem("refresh_token", obj.refresh_token);
                                                    self.access_token = obj.access_token;
                                                    self.refresh_token = obj.refresh_token;
                                                    if (self.access_token) {
                                                        await self.orm.call('res.users', 'write', [
                                                            session.uid,
                                                            {
                                                                ringcentral_access_token: self.access_token,
                                                            },
                                                        ]);
                                                    }
                                                    const res = await axios.get(`${self.ringcentral_server}/restapi/v1.0/account/~/extension/~`, {
                                                        headers: {
                                                            "Content-Type": "application/json",
                                                            Authorization: `Bearer ${self.access_token}`
                                                        }
                                                    });
                                                    self.extension = res.data;

                                                    var call_details = await axios.get(`${self.ringcentral_server}/restapi/v1.0/account/~/extension/~/caller-id`, {
                                                        headers: {
                                                            "Content-Type": "application/json",
                                                            Authorization: `Bearer ${self.access_token}`
                                                        }
                                                    });

                                                    call_details = call_details.data;
                                                    if (call_details.byFeature && call_details.byFeature[0] &&
                                                        call_details.byFeature[0].callerId && call_details.byFeature[0].callerId.phoneInfo.phoneNumber) {
                                                        self.message_number = call_details.byFeature[0].callerId.phoneInfo.phoneNumber;
                                                    } else {
                                                        self.message_number = null;
                                                    }
                                                    var account_details = await axios.get(`${self.ringcentral_server}/restapi/v1.0/account/~`, {
                                                        headers: {
                                                            "Content-Type": "application/json",
                                                            Authorization: `Bearer ${self.access_token}`
                                                        }
                                                    });

                                                    var account_json = account_details.data;
                                                    self.username = account_json.mainNumber;

                                                    var response_phoneNumber = await axios.get(`${self.ringcentral_server}/restapi/v1.0/account/~/extension/~/phone-number?usageType=DirectNumber`, {
                                                        headers: {
                                                            "Content-Type": "application/json",
                                                            Authorization: `Bearer ${self.access_token}`
                                                        }
                                                    });

                                                    var responseJson = response_phoneNumber.data;
                                                    self.message_number = responseJson.records && responseJson.records[0] &&
                                                        responseJson.records[0].phoneNumber;

                                                    var sipRes = await axios.post(`${self.ringcentral_server}/restapi/v1.0/client-info/sip-provision`, {
                                                        sipInfo: [
                                                            {
                                                                transport: "WSS",
                                                            },
                                                        ],
                                                    }, {
                                                        headers: {
                                                            "Content-Type": "application/json",
                                                            Authorization: `Bearer ${self.access_token}`
                                                        }
                                                    });

                                                    var sipData = sipRes.data;

                                                    if (self.loggedin) {
                                                        try {
                                                            self.register(sipData)
                                                        }
                                                        catch {
                                                            self.logoutbutton.show()
                                                            self.logoutbutton.removeAttr("disabled")
                                                            return false
                                                        }
                                                        finally {
                                                            setTimeout(() => {
                                                                document.querySelector(".loading").classList.add("d-none");
                                                                self.notification.add(_t("Logged-in successfully"), {
                                                                    type: "success",
                                                                });
                                                            }, 2000);
                                                            self.logoutbutton.show()
                                                            self.logoutbutton.removeAttr("disabled")
                                                        }
                                                    }
                                                }
                                            } catch (error) {
                                                console.error("Login failed:", error);
                                            }
                                        }
                                    }
                                    else {
                                        win.close();
                                        window.clearInterval(pollOAuth);
                                    }
                                }
                            }

                        } catch (e) {
                            if (e instanceof TypeError) {
                                win.close();
                                window.clearInterval(pollOAuth);
                            }
                        }
                    }, 100);
                }
            }
        }

        var oauth = new OAuthCode(self.rcsdk, {
            RC_APP_KEY: appKey,
            RC_APP_SECRET: appSecret,
            RC_APP_SERVER_URL: server,
            RC_APP_REDIRECT_URL: redirectUri,
            MY_APP_HOST: appHost,
            MY_APP_PORT: appPost,
        });
        oauth.loginPopup();

    }

    async login(self, server, appKey, appSecret, redirectUri, appHost, appPost) {
        try {
            var self = this;
            if (this.ContactResponse && this.access_token) {
                this.ContactResponse = false;
                const url = `${self.ringcentral_server}/restapi/v1.0/account/~/extension/~/address-book/contact`;
                const headers = {
                    'Authorization': `Bearer ${this.access_token || self.access_token}`
                };
                const account_details = await axios.get(url, { headers });
                if (account_details) {
                    this.ContactResponse = true;
                }
                for (const value of account_details.data.records) {

                    const all_res_users = await self.orm.call('res.partner', 'search', [[["ringcentral_id", "=", value.id]]], session.context)

                    if (all_res_users.length === 0) {
                        await this.orm.call('res.partner', 'create', [
                            {
                                ringcentral_id: value.id,
                                name: value.firstName,
                                phone: value.homePhone,
                            },
                        ], session.context)
                    }
                }

                if (!self.platform._isAccessTokenValid()) {
                    const res = await self.platform.refresh();
                    const obj = JSON.parse(res.text());

                    self.loggedin = true;
                    localStorage.setItem("access_token", obj.access_token);
                    localStorage.setItem("refresh_token", obj.refresh_token);
                    self.access_token = obj.access_token;
                    self.refresh_token = obj.refresh_token;

                    self.sub_login(
                        self,
                        server,
                        appKey,
                        appSecret,
                        redirectUri,
                        appHost,
                        appPost
                    );
                } else {
                    self.sub_login(
                        self,
                        server,
                        appKey,
                        appSecret,
                        redirectUri,
                        appHost,
                        appPost
                    );
                }
            }
        }
        catch (error) {
            const errorMessage = error.response?.data?.message || "An error occurred";
            this.notification.add(_t(errorMessage), { type: "warning" });
        }
    }

    async sub_login(self, server, appKey, appSecret, redirectUri, appHost, appPost) {
        try {
            var self = this;
            if (this.sipProvisionResponse) {
                this.sipProvisionResponse = false;
                const res = await axios.get(`${self.ringcentral_server}/restapi/v1.0/account/~/extension/~`, {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${this.access_token}`
                    }
                });
                self.loggedin = true;
                document.querySelectorAll(".menu-panels").forEach(panel => panel.style.display = "block");
                document.querySelector(".menu_sign_in_out_li").nextElementSibling.style.display = "block";
                self.extension = res.data;
                const sipProvisionRes = await axios.post(`${self.ringcentral_server}/restapi/v1.0/client-info/sip-provision`, {
                    sipInfo: [
                        {
                            transport: "WSS",
                        },
                    ],
                }, {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${this.access_token}`
                    }
                });
                this.data = sipProvisionRes.data;
                this.sipProvisionResponse = true;
                if (self.loggedin) {
                    self.register(this.data);
                }
            }
        }
        catch (error) {
            const errorMessage = error.response?.data?.message || "An error occurred";
            this.notification.add(_t(errorMessage), { type: "warning" });
        }
    }

    async register(data) {
        this.state.registered = true;
        var self = this;
        self.sipInfo = data.sipInfo[0] || data.sipInfo;
        self.webPhone = new RingCentral.WebPhone(data, {
            appKey: self.appKey,
            audioHelper: {
                enabled: true,
                incoming: "/ringcentral/static/src/audio/incoming.ogg",
                outgoing: "/ringcentral/static/src/audio/outgoing.ogg",
            },
            logLevel: parseInt(self.logLevel, 10),
        });

        self.webPhone.userAgent.on("invite", function (session) {
            self.onInvite(session);
        });
        self.webPhone.userAgent.on("connecting", function () {
            console.log("UA connecting");
        });
        self.webPhone.userAgent.on("connected", function () {
            console.log("UA Connected");
        });
        self.webPhone.userAgent.on("disconnected", function () {
            console.log("UA Disconnected");
        });
        self.webPhone.userAgent.on("registered",async () => {
            if (document.querySelector(".loading")){
                document.querySelector(".loading").classList.add("d-none");
                self.registered = true
                console.log("UA Registered");
                self.notification.add(_t("Registration Success."), {
                    type: "success",
                });
                var res = await self.platform.refresh();
                if (res){
                    var obj = JSON.parse(res.text());
                    self.loggedin = true;
                    localStorage.setItem("access_token", obj.access_token);
                    localStorage.setItem("refresh_token", obj.refresh_token);
                    self.access_token = obj.access_token;
                    self.refresh_token = obj.refresh_token;
                    console.log("Token Refreshed")
                }

                this.env.bus.trigger("registration-notification", ('success'));
            }
        });
        self.webPhone.userAgent.on("unregistered", function () {
            console.log("UA Unregistered");
        });
        self.webPhone.userAgent.on("registrationFailed", async () => {
            self.notification.add(_t("Registration failed, Please Login Again!"), {
                type: "warning",
            });
            this.env.bus.trigger("registration-notification", ('failed'));
            self.platform.logout().then(() => {
                location.reload(true)
            });
        });
        self.webPhone.userAgent.on("message", function () {
            console.log("UA Message", arguments);
        });

        const url = `${self.ringcentral_server}/restapi/v1.0/account/~`;
        const headers = {
            'Authorization': `Bearer ${self.access_token}`
        };
        const response = await axios.get(url, { headers });
        self.username = response.data.mainNumber;
        return self.webPhone;
    }

    async onInvite(session) {
        var self = this;
        var extension = false;
        var partner_exists = false;
        var data = {};
        var number = session.request?.headers?.From[0].raw;
        var incoming_call_number = "+".concat(number?.split("+")[1]?.split("@")[0]);
        if (session.request.from?.friendlyName?.indexOf("@") > -1) {
            var call_from_number_list =
                session.request?.from?.friendlyName?.split("@")[0];
        } else {
            var call_from_number_list = session.request?.from?.friendlyName;
        }
        if (session.request.to.friendlyName.indexOf("@") > -1) {
            var call_to_number_list = session.request?.to?.friendlyName?.split("@")[0];
        } else {
            var call_to_number_list = session.request?.to?.friendlyName;
        }
        var from_name = "";
        for (var i = 0; i < self.contacts.length; i++) {
            if (
                (self.contacts[i].phone &&
                    self.contacts[i].phone?.indexOf(call_from_number_list) > -1) ||
                (self.contacts[i].mobile &&
                    self.contacts[i].mobile?.indexOf(call_from_number_list) > -1)
            ) {
                from_name = self.contacts[i].name;
                break;
            }
        }
        let result = await self.orm.call('crm.phonecall', 'get_partner_name', [incoming_call_number])
        var data = result;

        var title = ""
        if (result[0]?.name) {
            title = "Call From: " + result[0]?.name
        }
        else {
            title = "Call From: " + incoming_call_number
        }
        this.dialogService.closeAll();
        this.dialogService.add(IncomingCall, {
            from_number: call_from_number_list,
            from_name: from_name,
            title: _t(title),
            table_list: result,
            session: session,
            contacts: this.contacts,
            call: self,
            incoming_call_number: incoming_call_number,
            username: self.username,
            data: data,
            partner_exists: partner_exists,
            contacts_action: self.contacts_action,
            call_from_number_list: call_from_number_list,
            openWindow: async (e) => {
                await this.openWindowLocation(e)
            },

        });
        session.on("rejected", function () {
        });
        session.on("terminated", function () {
        });
        session.on("cancel", function () {
        });
    }

    onAccepted(session, to_number, from_number, type, caller_name, caller_number, data) {
        var self = this;
        if (!self.platform._isAccessTokenValid()) {
            self.refreshAccessToken(session, to_number, from_number, type, caller_name, caller_number, data);
        } else {
            self.sub_onaccepted(session, to_number, from_number, type, caller_name, caller_number, data);
        }
    }
    async refreshAccessToken(session, to_number, from_number, type, caller_name, caller_number, data) {
        var self = this;
        var res = await self.platform.refresh();

        if (res) {
            var obj = JSON.parse(res.text());
            self.loggedin = true;
            localStorage.setItem("access_token", obj.access_token);
            localStorage.setItem("refresh_token", obj.refresh_token);
            self.access_token = obj.access_token;
            self.refresh_token = obj.refresh_token;

            self.sub_onaccepted(session, to_number, from_number, type, caller_name, caller_number);
        } else {
            this.notification.add(_t("Please Sign in."), {
                type: "warning",
            });
        }
    }

    async render_contacts() {
        try {
            const url = `${self.ringcentral_server}/restapi/v1.0/account/~/extension/~/address-book/contact`;
            const headers = {
                'Authorization': `Bearer ${this.access_token}`
            };
            const response = await axios.get(url, { headers });

            if (response?.data?.records) {
                const account_json = response.data;
                const partners = await this.orm.call('res.partner', 'ac_search_read', [account_json.records], session.context);

                const partners_customer = [];
                const partners_suppliers = [];
                const contacts = this.contacts.slice(0, this.limit);

                contacts.forEach(contact => {
                    if (contact.customerRank) {
                        partners_customer.push(contact);
                    }
                    if (contact.supplierRank) {
                        partners_suppliers.push(contact);
                    }
                    partners.push(contact);
                });

                this.state.partners_list = contacts;
                this.state.partners_customer = partners_customer;
                this.state.partners_suppliers = partners_suppliers;
            } else {
                this.state.partners_list = [];
                this.state.partners_customer = [];
                this.state.partners_suppliers = [];
            }
        } catch (error) {
            const errorMessage = error.response?.data?.message || "An error occurred";
            this.notification.add(_t(errorMessage), { type: "warning" });
        }
    }

    async render_available_extensions() {
        try {
            const url = `${self.ringcentral_server}/restapi/v1.0/account/~/presence`;
            const headers = {
                'Authorization': `Bearer ${this.access_token}`
            };
            const response = await axios.get(url, { headers });

            if (response?.data?.records?.length) {
                this.state.available_extensions = response.data.records;
                this.state.render_available_extensions = this;
            } else {
                this.state.available_extensions = [];
            }
        } catch (error) {
            const errorMessage = error.response?.data?.message || "An error occurred";
            this.notification.add(_t(errorMessage), { type: "warning" });
        }
    }

    async render_active_calls() {
        try {
            const url = self.ringcentral_server + "/restapi/v1.0/account/~/active-calls";

            const headers = {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.access_token}`
            };

            const response = await axios.get(url, { headers });

            if (response && response.data) {
                const active_calls = response.data;
                this.state.activecalls = active_calls;

                if (active_calls.records && active_calls.records.length) {
                    const active_calls_list = active_calls.records.filter(call =>
                        call.from && call.to
                    );

                    if (active_calls_list.length) {
                        this.state.active_calls_list = active_calls_list;
                        this.notification.add(_t("Fetched active calls !!"), { type: "success" });
                    }
                }
            }
        } catch (error) {
            const errorMessage = error.response?.data?.message || "An error occurred";
            this.notification.add(_t(errorMessage), { type: "warning" });
        }
    }

    contact_search(ev) {
        this.partners = [];
        let partners_customer = [];
        let partners_suppliers = [];
        let query_element = document.querySelector("#contact_search");
        var query = query_element.value;
        this.input_value = query;
        query = query.replace(
            /[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,
            "."
        );
        query = query.replace(/ /g, ".+");
        var re = RegExp("([0-9]+):.*?" + query, "gi");
        for (var i = 0; i < this.limit; i++) {
            var r = re.exec(this.partner_search_string);
            if (r) {
                var id = Number(r[1]);
                if (id > 0) {
                    if (this.contacts_partner[id].customer_rank) {
                        partners_customer.push(this.contacts[id]);
                    }
                    if (this.contacts_partner[id].supplier_rank) {
                        partners_suppliers.push(this.contacts[id]);
                    }
                    this.partners.push(this.contacts_partner[id]);
                }
            }
        }
        this.state.partners_list = this.removeRedundant(this.partners)
    }

    removeRedundant(partners) {
        let unique = [];
        partners.forEach(partner => {
            if (!unique.includes(partner)) {
                unique.push(partner)
            }
        });
        return unique
    }

    dialpad(e) {
        const appendedNumber = $(e.currentTarget).data("number");
        const dialerInput = document.querySelector("#dialerPad");
        dialerInput.value += _t(appendedNumber);
    }

    makeCallForm(event = false, pnumber = false) {
        var self = this;
        if (self.loggedin) {
            const dialled_number = document.querySelector("#dialerPad").value
            if (pnumber) {
                dialled_number = pnumber;
            }
            if (dialled_number !== undefined && dialled_number) {
                self.makeCall(self.filter_number(dialled_number));
            }
            else {
                this.notification.add(_t("Please Enter the Phone Number."), {
                    type: "warning",
                });
            }
        } else {
            this.notification.add(_t("You are not logged in in RingCentral. Please contact your Administrator.."), {
                type: "warning",
            });
        }
    }
    filter_number(phone_number) {
        if (phone_number) {
            if (phone_number.indexOf("<") > -1) {
                var start_pos = phone_number.indexOf("<") + 1;
                var pnumber = phone_number.substring(
                    start_pos,
                    phone_number.indexOf(">", start_pos)
                );
                var ph = pnumber.replace(/\s/g, "");
                return ph;
            }
            var pn = phone_number.replace(/\s/g, "");
            return pn;
        }
    }

    async load_callLog_on_dialpad(ev) {
        var self = this;
        if (!self.platform._isAccessTokenValid()) {
            var res = self.platform.refresh()
            var obj = JSON.parse(res);
            self.loggedin = true;
            localStorage.setItem("access_token", obj.access_token);
            localStorage.setItem("refresh_token", obj.refresh_token);
            self.access_token = obj.access_token;
            self.refresh_token = obj.refresh_token;
            var call_log_list = self.fetch_call_log_details(self)
            var all_calls = document.querySelector("#dial_all_calls");
            var menu_panels = document.querySelector(".menu-panels");
            var panel_body_height = all_calls.parentElement.parentElement.querySelector('.panel-body').style.height;
            var menu_panels_height = parseInt(menu_panels.style.height) || 0;
            var panel_body_height_numeric = parseInt(panel_body_height) || 0;
            var maxHeight = menu_panels_height - panel_body_height_numeric - 140;
            all_calls.setAttribute("style", `max-height: ${maxHeight}px; overflow: auto;`);
            var dial_missedcalls = document.querySelector("#dial_missed_calls");
            dial_missedcalls.setAttribute("style", `max-height: ${maxHeight}px; overflow: auto;`);
            var missed_calls = document.querySelector('#missed_calls')
            missed_calls.setAttribute("style", `max-height: ${maxHeight}px; overflow: auto;`);

        } else {
            var call_log_list = await self.fetch_call_log_details(self)
            self.state.record_length = call_log_list.length
            self.state.all_calls = call_log_list
            self.state.widget = self
            var all_calls = document.querySelector("#dial_all_calls");
            all_calls.setAttribute("style", 'overflow:auto;')
            var menu_panels = document.querySelector(".menu-panels");
            var panel_body_height = all_calls.parentElement.parentElement.querySelector('.panel-body').style.height;
            var menu_panels_height = parseInt(menu_panels.style.height) || 0;
            var panel_body_height_numeric = parseInt(panel_body_height) || 0;
            var maxHeight = menu_panels_height - panel_body_height_numeric - 140;
            all_calls.setAttribute("style", `max-height: ${maxHeight}px; overflow: auto;`);
            var dial_missedcalls = document.querySelector("#dial_missed_calls");
            dial_missedcalls.setAttribute("style", `max-height: ${maxHeight}px; overflow: auto;`);
            var missed_calls = document.querySelector('#missed_calls')
            missed_calls.setAttribute("style", `max-height: ${maxHeight}px; overflow: auto;`);
            var all_calls_2 = document.querySelector('#all_calls')
            all_calls_2.setAttribute("style", `max-height: ${maxHeight}px; overflow: auto;`);
        }
    }

    get_partner_name(number) {
        var self = this;
        var name = filter(self.contacts_partner, function (partner) {
            if (partner.phone == number || partner.mobile == number) {
                return partner.name;
            }
        });
        if (name) {
            return name.name;
        }
        return false;
    }

    async fetch_call_log_details(self) {
        try {
            var calls = []
            self.accountId = this.extension.account.id
            if (self.accountId) {
                var self = this;
                var d = new Date();
                d.setDate(d.getDate() - 7);
                const url = self.ringcentral_server + "/restapi/v1.0/account/~/extension/~/call-log"

                const headers = {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${self.access_token}`
                };
                const response = await axios.get(url, { headers });

                calls = response?.data.records;
                if (calls) {
                    for (var i = 0; i < self.contacts.length; i++) {
                        for (var j = 0; j < calls.length; j++) {
                            if (
                                self.contacts[i].phone == calls[j].to.phoneNumber ||
                                self.contacts[i].mobile == calls[j].to.phoneNumber
                            ) {
                                calls[j].to.name = self.capitalizeFirstLetter(
                                    self.contacts[i].name || self.contacts[i].phone
                                );
                            } else if (calls[j].to.name) {
                                calls[j].to.name = self.capitalizeFirstLetter(
                                    calls[j].to.name
                                );
                            }
                        }
                    }
                }
                return calls;
            }
            else {
                return calls
            }
        }
        catch (error) {
            const errorMessage = error.response?.data?.message || "An error occurred";
            this.notification.add(_t(errorMessage), { type: "warning" });
        }
        return calls
    }

    async load_sent_messages() {
        try {
            var self = this;
            const url = self.ringcentral_server + "/restapi/v1.0/account/~/extension/~/message-store?availability=Alive&dateFrom=" + self.dateBefore2days;

            const headers = {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${self.access_token}`
            };
            const msg_data = await axios.get(url, { headers });
            var messages = msg_data.data.records;
            self.messages = [];
            messages.forEach((message) => {
                var date = message.creationTime.split("T");
                var time = date[1].split(".");
                var datetime = date[0] + " " + time[0];
                message.datetime = datetime;
                self.messages.push(message.id);
            });
            var result = await self.orm.call('crm.phonecall', 'ac_search_read', [])

            var rec_list = [];
            messages.forEach(function (message) {
                var msg_id = message.id.toString();
                if (result.indexOf(msg_id) == -1) {
                    result.push(msg_id);
                    rec_list.push(message);
                }
            });

            if (rec_list.length > 0) {
                await self.orm.call('crm.phonecall', 'create_message', [rec_list])
            }

            messages.forEach(function (message) {
                self.contacts.forEach(function (contact) {
                    if (message.direction == "Outbound") {
                        message.to.forEach(function (to_phone_number) {
                            if (contact.phone == to_phone_number.phoneNumber || contact.mobile == to_phone_number.phoneNumber) {
                                to_phone_number.partner_name = self.capitalizeFirstLetter(contact.name || contact.phone);
                            }
                        });
                    } else if (message.direction == "Inbound") {
                        if (contact.phone == message.from.phoneNumber || contact.mobile == message.from.phoneNumber) {
                            message.from.partner_name = self.capitalizeFirstLetter(contact.name || contact.phone);
                        }
                    }
                });
            });

            var partner_list = [];
            var partner_message = [];
            messages.forEach((message) => {
                if (message.direction == "Inbound") {
                    if (partner_list.indexOf(message.from.phoneNumber) == -1) {
                        partner_list.push(message.from.phoneNumber);
                        partner_message.push({
                            id: message.id,
                            name: message.from.name || message.from.phoneNumber,
                            phoneNumber: message.from.phoneNumber,
                        });
                    }
                } else if (message.direction == "Outbound") {
                    message.to.forEach((to_phone_number) => {
                        if (partner_list.indexOf(to_phone_number.phoneNumber) == -1) {
                            partner_list.push(to_phone_number.phoneNumber);
                            partner_message.push({
                                id: message.id,
                                name: to_phone_number.partner_name || to_phone_number.phoneNumber,
                                phoneNumber: to_phone_number.phoneNumber,
                            });
                        }
                    });
                }
            });

            self.state.all_messages = partner_message
            function datetime_conversion(datetime) {
                var nowDate = new Date(datetime);
                var month = nowDate.getMonth() + 1;
                var seconds = nowDate.getSeconds();
                if (month < 10) {
                    month = "0" + month;
                }
                if (seconds < 10) {
                    seconds = "0" + seconds;
                }
                return self.format_datetime(
                    month +
                    "-" +
                    nowDate.getDate() +
                    "-" +
                    nowDate.getFullYear() +
                    " " +
                    nowDate.getHours() +
                    ":" +
                    nowDate.getMinutes() +
                    ":" +
                    seconds
                );
            }
            messages.reverse();
            self.state.messages = messages
            self.do_recursive_alert()


        } catch (error) {
            this.notification.add(_t(error.response.data.message), { type: "warning" });
        }

    }

    openChatBox(dialog_title, phoneNumber) {
        this.dialog_title = dialog_title
        if ($("#chatbox").length == 0) {
            this.dialogService.add(MessageChatBoxDialogchatbox, {
                widget: this,
                title: dialog_title,
                phoneNumber: phoneNumber,
                messages: this.state.messages,
            });
        }
    }
    async do_recursive_alert() {
        try {
            const msgData = await this.platform.get(
                "/restapi/v1.0/account/~/extension/~/message-store?availability=Alive&direction=Inbound"
            );

            const messages = msgData.json().records;
            const newMessages = [];

            for (const message of messages) {
                if (this.messages && this.messages.indexOf(message.id) === -1) {
                    newMessages.push(message);

                    Notification.requestPermission();
                    const msgStr = `Hi, New Message Received From ${message.from.phoneNumber}`;
                    new Notification(msgStr);

                    if (document.getElementById("messgae_contant")) {
                        const date = message.creationTime.split("T");
                        const time = date[1].split(".");
                        const datetime = date[0] + " " + time[0];
                        message.datetime = datetime;

                        if (message.direction === "Inbound" && message.from.phoneNumber === this.titlePopup) {
                            let divHtml =
                                "<div class='d-flex justify-content-start mb-4'>" +
                                "<div class='msg_cotainer_send'>" +
                                `${message.subject}<span class='msg_time'>${message.datetime}</span></div></div>`;

                            for (const attachment of message.attachments) {
                                if (attachment.type === "MmsAttachment") {
                                    const uri = `${attachment.uri}?access_token=${this.accessToken}`;
                                    divHtml +=
                                        `<div class='d-flex justify-content-start mb-4'><div class='msg_img_cotainer'>` +
                                        `<img src=${uri} class='img-responsive msg_img' style='width:30%; height:20%'/>` +
                                        `<span class='msg_time'>${message.datetime}</span></div></div>`;
                                }
                            }

                            document.getElementById("messgae_contant").insertAdjacentHTML("beforeend", divHtml);
                            this.messages.push(message.id);
                        } else if (message.direction === "Outbound") {
                            for (const toPhoneNumber of message.to) {
                                if (toPhoneNumber.phoneNumber === this.titlePopup) {
                                    let divHtml =
                                        "<div class='d-flex justify-content-end mb-4'>" +
                                        "<div class='msg_cotainer_send'>" +
                                        `${message.subject}<span class='msg_time_send'>${message.datetime}</span></div></div>`;

                                    for (const attachment of message.attachments) {
                                        if (attachment.type === "MmsAttachment") {
                                            const uri = `${attachment.uri}?access_token=${this.accessToken}`;
                                            divHtml +=
                                                `<div class='d-flex justify-content-end mb-4'><div class='msg_img_cotainer_send'>` +
                                                `<img src=${uri} class='img-responsive msg_img' style='width:30%; height:20%'/>` +
                                                `<span class='msg_time_send'>${message.datetime}</span></div></div>`;
                                        }
                                    }

                                    document.getElementById("messgae_contant").insertAdjacentHTML("beforeend", divHtml);
                                    this.messages.push(message.id);
                                }
                            }
                        }
                    }
                }
            }

            if (newMessages.length > 0) {
                await this.orm.call('crm.phonecall', 'create_message', [newMessages]);
            }
        } catch (error) {
            console.error('Error fetching or processing data:', error);
        }

        setTimeout(() => {
            this.do_recursive_alert();
        }, 10000);
    }

    capitalizeFirstLetter(string) {
        var name = string.trim().split(" ");
        var firstName = name.slice(0, -1).join(" ");
        var lastName = name.slice(-1).join(" ");
        return (
            firstName.charAt(0).toUpperCase() +
            firstName.slice(1)?.toLowerCase() +
            " " +
            (lastName.charAt(0).toUpperCase() + lastName.slice(1)?.toLowerCase())
        );
    }

    async send_msg(e, dialog_title) {
        var self = this;
        self.do_recursive_alert();

        if (!self.platform._isAccessTokenValid()) {
            self.refresh_token_request();
        }

        var msg_text = e.view.document.querySelector("#msg_text").value;
        var msg_to = e.view.document.querySelector("#message_to").value;
        if (!msg_to) {
            msg_to = dialog_title;
        }

        if (!self.message_number) {
            self.message_number = self.username;
        }

        var formData = new FormData();
        formData.append("from", self.message_number);
        formData.append("to", self.filter_number(msg_to));
        formData.append("text", msg_text);

        var fileInput = document.querySelector("#msg_image");
        var files = fileInput.files;
        var values_list = [];

        if (files.length > 0) {
            var filesArray = Array.from(files);
            filesArray.forEach((image, index) => {
                formData.append("attachment", image);
                var reader = new FileReader();
                reader.onload = function () {
                    var result = reader.result;
                    var data64 = result.split(",")[1];
                    var values = {
                        name: image.name,
                        type: "binary",
                        datas: data64,
                    };
                    values_list.push([0, 0, values]);
                };
                reader.readAsDataURL(image);
            });
        }

        if (self.loggedin) {
            if (!msg_to) {
                this.notification.add(_t("Error: Please Enter Number."), {
                    type: "warning",
                });
                return;
            }
            if (!msg_text) {
                this.notification.add(_t("Error: Please Enter Message."), {
                    type: "warning",
                });
                return;
            }

            if (msg_to && msg_text && formData) {
                try {
                    const url = self.ringcentral_server + "/restapi/v1.0/account/~/extension/~/sms";
                    const headers = {
                        'Authorization': `Bearer ${self.access_token}`
                    };

                    const response = await axios.post(url, formData, { headers });

                    const today = new Date();
                    const args = [{
                        name: self.username,
                        type: "sent",
                        partner_phone: self.filter_number(msg_to),
                        date: today,
                        description: msg_text,
                        attachment_ids: values_list,
                        ringcentral_message_id: response.data.id,
                    }];

                    await self.orm.call('crm.phonecall', 'create', args);

                    const msgText = e.view.document.querySelector("#msg_text");
                    const messageTo = e.view.document.querySelector("#message_to");
                    const msgImage = e.view.document.querySelector("#msg_image");

                    if (msgText) msgText.value = '';
                    if (messageTo) messageTo.value = '';
                    if (msgImage) msgImage.value = '';

                    this.notification.add(_t("Message Sent Successfully"), { type: "success" });

                } catch (error) {
                    this.notification.add(_t(error.response?.data?.message || "An error occurred"), { type: "warning" });
                }
            }
        } else {
            this.notification.add(_t("You are not logged in to RingCentral. Please contact your Administrator."), {
                type: "warning",
            });
        }
    }

    async send_popup_msg(e, dialog_title, fileInput) {
        console.log("e", e);
        var self = this;
        self.do_recursive_alert();

        if (!self.platform._isAccessTokenValid()) {
            self.refresh_token_request();
        }

        var msg_text = e.view.document.querySelector("#popup_input").value;
        var msg_to = e.view.document.querySelector("#message_to").value;
        if (!msg_to) {
            msg_to = dialog_title;
        }

        if (!self.message_number) {
            self.message_number = self.username;
        }

        var body = {
            from: { phoneNumber: self.message_number },
            to: [{ phoneNumber: self.filter_number(msg_to) }],
            text: msg_text
        };

        var formData = new FormData();
        formData.append("json", new Blob([JSON.stringify(body)], { type: "application/json" }));

        var fileInput = document.querySelector("#popup_file");
        var files = fileInput.files;

        var values_list = [];
        if (files.length > 0) {
            var filesArray = Array.from(files);
            filesArray.forEach((image, index) => {
                formData.append("attachment", image);
                var reader = new FileReader();
                reader.onload = function () {
                    var result = reader.result;
                    var data64 = result.split(",")[1];
                    var values = {
                        name: image.name,
                        type: "binary",
                        datas: data64,
                    };
                    values_list.push([0, 0, values]);
                };
                reader.readAsDataURL(image);
            });
        }

        if (self.loggedin) {
            if (msg_text && msg_to) {
                try {
                    const url = self.ringcentral_server + "/restapi/v1.0/account/~/extension/~/sms";
                    const headers = {
                        'Authorization': `Bearer ${self.access_token}`
                    };

                    const response = await axios.post(url, formData, { headers });

                    const today = new Date();
                    const args = [{
                        name: self.username,
                        type: "sent",
                        partner_phone: self.filter_number(msg_to),
                        date: today,
                        description: msg_text,
                        attachment_ids: values_list,
                        ringcentral_message_id: response.data.id,
                    }];

                    await self.orm.call('crm.phonecall', 'create', args);

                    response.datetime = today;
                    document.querySelector("#popup_input").value = '';
                    document.querySelector("#popup_file").value = '';
                    var divHtml =
                        "<div class='d-flex justify-content-end mb-4'>" +
                        "<div class='msg_cotainer_send'>" +
                        msg_text +
                        "<span class='msg_time_send'>" +
                        response.datetime +
                        "</span></div></div>";

                    if (response.data.attachments) {
                        response.data.attachments.forEach(attachment => {
                            if (attachment.type == "MmsAttachment") {
                                var uri = attachment.uri + "?access_token=" + self.access_token;
                                divHtml +=
                                    "<div class='d-flex justify-content-end mb-4'><div class='msg_img_cotainer_send'>" +
                                    "<img src=" + uri +
                                    " class='img-responsive msg_img' style='width:30%; height:20%'/>" +
                                    "<span class='msg_time_send'>" +
                                    response.datetime +
                                    "</span></div></div>";
                            }
                        });
                    }

                    self.messages.push(response.data.id);

                    var messgaeContant = document.querySelector("#messgae_contant");
                    if (messgaeContant) {
                        messgaeContant.insertAdjacentHTML("beforeend", divHtml);
                    }
                    this.notification.add(_t("Message Sent successfully"), { type: "success" });
                } catch (error) {
                    this.notification.add(_t(error.response?.data.message || "An error occurred"), { type: "warning" });
                }
            } else {
                this.notification.add(_t("Error: Please Enter Message."), { type: "warning" });
            }
        } else {
            this.notification.add(_t("You are not logged in to RingCentral. Please contact your Administrator."), { type: "warning" });
        }
    }


    dial_call_contact_detail(e, partner_data) {
        var self = this;
        if (!partner_data.phoneNumber) {
            partner_data.phoneNumber = e.target.dataset.phone_number
        }
        if (self.loggedin) {
            var dialled_number = partner_data.phone || partner_data.phoneNumber || partner_data.mobile
            if (dialled_number !== undefined && dialled_number) {
                self.makeCall(self.filter_number(dialled_number));
            } else {
                this.notification.add(_t("Please Enter the Phone Number."), {
                    type: "warning",
                });
            }
        } else {
            this.notification.add(_t("You are not logged in in RingCentral. Please contact your Administrator."), {
                type: "warning",
            });
        }
    }

    async listen_active_call(e, to_number) {
        var self = this;
        if (self.loggedin) {
            var data = await this.rpc("/find_extensionID", {
                phone_num: to_number,
            });
            if (data) {
                var ext_num = "*80" + data;
                self.makeCall(ext_num);
            } else {
                this.notification.add(_t("Sorry, can't find extension of this number!."), {
                    type: "info",
                });
            }
        } else {
            this.notification.add(_t("You are not logged in in RingCentral. Please contact your Administrator."), {
                type: "warning",
            });
        }
    }

    async makeCall(number) {
        var self = this;
        if (self.loggedin) {
            if (!self.message_number) {
                try {
                    const url = `${self.ringcentral_server}/restapi/v1.0/account/~/extension/~/phone-number?usageType=DirectNumber`;
                    const headers = {
                        'Authorization': `Bearer ${this.access_token}`
                    };
                    const response = await axios.get(url, { headers });

                    self.message_number = response.data.records && response.data.records[0] && response.data.records[0].phoneNumber;
                } catch (error) {
                    const errorMessage = error.response?.data?.message || "An error occurred";
                    this.notification.add(_t(errorMessage), { type: "warning" });
                    return;
                }
            }
            if (number == self.message_number) {
                this.notification.add(_t("Sorry! You cannot call your own number."), {
                    type: "info",
                });
            } else {
                var caller_name = number
                this.notification.add(_t("Calling: " + caller_name), {
                    type: "info",
                });
                var homeCountry =
                    self.extension &&
                        self.extension.regionalSettings &&
                        self.extension.regionalSettings.homeCountry
                        ? self.extension.regionalSettings.homeCountry.id
                        : null;
                if (self.webPhone) {
                    try {
                        var session = self.webPhone.userAgent.invite(number, {
                            media: {
                                render: {
                                    remote: document.getElementById("remoteVideo"),
                                    local: document.getElementById("localVideo"),
                                },
                            },
                            fromNumber: self.username,
                            homeCountryId: homeCountry,
                        });
                        var to_name = "";
                        for (var i = 0; i < self.contacts.length; i++) {
                            if (
                                (self.contacts[i].phone &&
                                    self.contacts[i].phone.indexOf(number) > -1) ||
                                (self.contacts[i].mobile &&
                                    self.contacts[i].mobile.indexOf(number) > -1)
                            ) {
                                to_name = self.contacts[i].name;
                                break;
                            }
                        }
                        self.onAccepted(
                            session,
                            number,
                            self.username,
                            "out_bound",
                            to_name,
                            number
                        );
                    } catch (error) {
                        console.error("Error making call:", error);
                        return;
                    }
                }
            }
        } else {
            this.notification.add(_t("You are not logged in to RingCentral."), {
                type: "warning",
            });
        }
    }

    openWindowLocation(e) {
        window.open(
            window.location.origin +
            "#id=" + e +
            "&action=" +
            self.contacts_action +
            "&model=res.partner&view_type=form",
            "_blank"
        );
    }
    async sub_onaccepted(
        session,
        to_number,
        from_number,
        type,
        caller_name,
        caller_number,
        data = {}) {
        let self = this;
        let partner_exists = false;
        var title = "Call In Progress with ";
        if (caller_name) {
            title += caller_name;
        }
        if (caller_number) {
            title += " [" + caller_number + "] ";
        }
        if (data && (!data.length || data.length < 1)) {
            partner_exists = true;
            var result = await self.orm.call('crm.phonecall', 'get_partner_name', [to_number]);

        }
        else {
            partner_exists = true;
            var result = data
        }
        var account_details = await self.platform.get("/restapi/v1.0/account/~/presence")
        var account_json = account_details.json();

        var available_extensions = [];
        for (
            var i = 0, len = account_json.records.length;
            i < len;
            i++
        ) {
            if (
                account_json.records[i].presenceStatus ==
                "Available"
            ) {
                available_extensions.push(account_json.records[i]);
            }
        }
        self.dialogService.closeAll();
        self.dialogService.add(CallDialog, {
            title: title,
            size: "md",
            modal: true,
            table_data: result,
            partner_exits: partner_exists,
            caller_number: caller_number,
            from_number: from_number,
            type: type,
            to_number: to_number,
            call: self,
            session: session,
            agent_options: available_extensions,
            contentClass: '',
            position: {
                my: "center",
                at: "center",
                of: window,
            },
            openWindow: async (e) => {
                await this.openWindowLocation(e)
            },
        })

        session.on("terminated", async function () {
            var results = await self.platform.get(
                "/restapi/v1.0/account/~/extension/~/call-log-sync?statusGroup=All&syncType=FSync&recordCount=1"
            )
            var record = results.json()
            var rec_li = [];

            record.records.forEach((result) => {
                if (
                    result &&
                    result.from &&
                    ((result.from.phoneNumber == to_number &&
                        result.result == "Accepted") ||
                        (result.to.phoneNumber == to_number &&
                            result.result == "Call connected"))
                ) {
                    var url = self.ringcentral_service_uri.split("/login/");
                    var duration = result.duration / 60;
                    var time = new Date().getTime();
                    var rec_type = "";
                    if (result.recording) {
                        if (result.recording.type == "Automatic") {
                            rec_type = "Auto";
                        } else {
                            rec_type = result.recording.type;
                        }

                        var str =
                            url[0] +
                            "/mobile/media?cmd=downloadMessage&msgid=" +
                            result.recording.id +
                            "&useName=true&time=" +
                            "1554700788480" +
                            "&msgExt=&msgNum=" +
                            result.from.phoneNumber +
                            "&msgDir=" +
                            result.direction +
                            "&msgRecType=" +
                            rec_type +
                            "&msgRecId=" +
                            result.recording.id +
                            "&type=1&download=1&saveMsg=&file=.mp3";
                    }
                    var data_li = [];
                    if (result.legs) {
                        result.legs.forEach(leg => {
                            var val = {
                                name: leg.action,
                                call_type: leg.direction,
                                leg_type: leg.legType,
                                from_number: leg.from.phoneNumber,
                                to_number: leg.to.phoneNumber,
                            };
                            data_li.push([0, 0, val]);
                        });
                    }
                    if (result.recording) {
                        self.orm.call('crm.phonecall', "create_search_voip", [{
                            name: from_number,
                            type: type,
                            partner_phone: to_number,
                            date: result.startTime,
                            description: session.call_description,
                            duration: duration,
                            crm_phonecall_about_id: parseInt(session.phone_call_about),
                            ringcentral_call_id: result.id,
                            ringcentral_call_url: str,
                            is_recording: true,
                            crm_call_activity_ids: data_li,
                        },])
                    } else {
                        self.orm.call('crm.phonecall', 'create_search_voip', [{
                            name: from_number,
                            type: type,
                            partner_phone: to_number,
                            date: result.startTime,
                            description: session.call_description,
                            duration: duration,
                            crm_phonecall_about_id: parseInt(session.phone_call_about),
                            ringcentral_call_id: result.id,
                            crm_call_activity_ids: data_li,
                        },])
                    }
                }
                console.log("Event: Terminated");
            })
        });


        session.on("replaced", function (newSession) {
            console.log(
                "Event: Replaced: old session",
                session,
                "has been replaced with",
                newSession
            );
            onAccepted(newSession);
        });


        session.on("bye", async function () {
            console.log("Event: Bye");
            var results = await axios.get(`${self.ringcentral_server}/restapi/v1.0/account/~/extension/~/call-log-sync?statusGroup=All&syncType=FSync&recordCount=3`, {
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${self.access_token}`
                }
            });
            var record = results.data;
            record.records.forEach(result => {
                if (result && result.from && ((result.from.phoneNumber == to_number && result.result == "Accepted") ||
                    (result.to.phoneNumber == to_number &&
                        result.result == "Call connected"))
                ) {
                    var url = self.ringcentral_service_uri.split("/login/");
                    var time = new Date().getTime();
                    var rec_type = "";
                    var str = "";
                    var data_li = [];
                    var duration = result.duration / 60;
                    if (result.legs) {

                        result.legs.forEach(leg => {
                            var val = {
                                name: leg.action,
                                call_type: leg.direction,
                                leg_type: leg.legType,
                                from_number: leg.from.phoneNumber,
                                to_number: leg.to.phoneNumber,
                            };
                            data_li.push([0, 0, val]);
                        });
                    }
                    if (result.recording) {
                        if (result.recording.type == "Automatic") {
                            rec_type = "Auto";
                        } else {
                            rec_type = result.recording.type;
                        }
                        var str =
                            url[0] +
                            "/mobile/media?cmd=downloadMessage&msgid=" +
                            result.recording.id +
                            "&useName=true&time=" +
                            "1554700788480" +
                            "&msgExt=&msgNum=" +
                            result.from.phoneNumber +
                            "&msgDir=" +
                            result.direction +
                            "&msgRecType=" +
                            rec_type +
                            "&msgRecId=" +
                            result.recording.id +
                            "&type=1&download=1&saveMsg=&file=.mp3";

                        self.orm.call('crm.phonecall', "create_search_voip", [{
                            name: from_number,
                            type: type,
                            partner_phone: to_number,
                            date: DateTime.utc(result.startTime),
                            description: session.call_description,
                            duration: duration,
                            crm_phonecall_about_id: parseInt(session.phone_call_about),
                            ringcentral_call_id: result.id,
                            ringcentral_call_url: str,
                            is_recording: true,
                            crm_call_activity_ids: data_li,
                        },])

                    } else {
                        self.orm.call('crm.phonecall', 'create_search_voip', [{
                            name: from_number,
                            type: type,
                            partner_phone: to_number,
                            date: DateTime.utc(result.startTime),
                            description: session.call_description,
                            duration: duration,
                            crm_phonecall_about_id: parseInt(session.phone_call_about),
                            ringcentral_call_id: result.id,
                            crm_call_activity_ids: data_li,
                        },])
                    }
                }
            });
        });
    }
}
registry.category("systray").add("RingcentralPanel", { Component: RingcentralPanelView }, { sequence: 25 });

