/** @odoo-module */

import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { Component, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CallDialog extends Component {
    
    static props = [
        'title',
        'size',
        'modal',
        'table_data',
        'partner_exits',
        'caller_number',
        'from_number',
        'type',
        'to_number',
        'call',
        'session',
        'agent_options',
        'contentClass',
        'position',
        'openWindow',
        "close",
    ]
    
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.rpc = useService("rpc");
        this.orm = useService("orm");
        this.isProcess = false;
        this.state = useState({})

        onMounted(async () => {
            var self = this
            this.state.phonecall_about = await this.orm.call('crm.phonecall.about', 'search_read', [[], ["name"]]);

            this.props.session.on("bye", async function () {
                console.log("Bye")
                self.props.close()
            })
            this.props.session.on("replaced", function () {
                self.props.close()
            });
            this.props.session.mediaHandler.on("iceConnection", function () {
                console.log("Event: ICE: iceConnection");
            });
            this.props.session.mediaHandler.on("iceConnectionChecking", function () {
                console.log("Event: ICE: iceConnectionChecking");
            });
            this.props.session.mediaHandler.on("iceConnectionConnected", function () {
                console.log("Event: ICE: iceConnectionConnected");
            });
            this.props.session.mediaHandler.on("iceConnectionCompleted", function () {
                console.log("Event: ICE: iceConnectionCompleted");
            });
            this.props.session.mediaHandler.on("iceConnectionFailed", function () {
                console.log("Event: ICE: iceConnectionFailed");
            });
            this.props.session.mediaHandler.on("iceConnectionDisconnected", function () {
                console.log("Event: ICE: iceConnectionDisconnected");
            });
            this.props.session.mediaHandler.on("iceConnectionClosed", function () {
                console.log("Event: ICE: iceConnectionClosed");
            });
            this.props.session.mediaHandler.on("iceGatheringComplete", function () {
                console.log("Event: ICE: iceGatheringComplete");
            });
            this.props.session.mediaHandler.on("iceGathering", function () {
                console.log("Event: ICE: iceGathering");
            });
            this.props.session.mediaHandler.on("iceCandidate", function () {
                console.log("Event: ICE: iceCandidate");
            });
            this.props.session.mediaHandler.on("userMedia", function () {
                console.log("Event: ICE: userMedia");
            });
            this.props.session.mediaHandler.on("userMediaRequest", function () {
                console.log("Event: ICE: userMediaRequest");
            });
            this.props.session.mediaHandler.on("userMediaFailed", function () {
                console.log("Event: ICE: userMediaFailed");
            });

            this.props.session.on("dtmf", function () {
                console.log("Event: DTMF");
            });
            this.props.session.on("muted", function () {
                console.log("Event: Muted");
            });
            this.props.session.on("unmuted", function () {
                console.log("Event: Unmuted");
            });
            this.props.session.on("connecting", function () {
                console.log("Event: Connecting");
            });

            this.props.session.on("cancel", function () {
                console.log("Event: Cancel");
                self.props.close();
            });
            this.props.session.on("refer", function () {
                console.log("Event: Refer");
                self.props.close();
            });
            this.props.session.on("failed", function () {
                console.log("Event: Failed");
                self.props.close()
            })
            this.props.session.on("accepted", function () {
                console.log("Event: Accepted");
            });
            this.props.session.on("progress", function () {
                console.log("Event: Progress");
            });
            this.props.session.on("rejected", function () {
                console.log("Event: Rejected");
                var description = document.querySelector("#description")
                var phonecallid = document.querySelector('select[name="phonecall_about"]')

                if (description && phonecallid) {
                    self.orm.call("crm.phonecall", 'create', [{
                        name: self.props.from_number,
                        type: self.props.type,
                        partner_phone: self.props.to_number,
                        date: new Date(),
                        description: description.value || '',
                        crm_phonecall_about_id: phonecallid.value || '',
                    },])
                }
                self.props.close()
            });

            var modal_outgoing_call = document.querySelector("#outgoingCall");
            var info = modal_outgoing_call.querySelector(".info");

            var session = this.props.session

            if (this.props.session) {
                var interval = setInterval(function () {
                    var time = session.startTime ? Math.round((Date.now() - session.startTime) / 1000) + "s"
                        : "Ringing";
                    info.innerHTML =
                        "time: " +
                        time +
                        "\n" +
                        "startTime: " +
                        JSON.stringify(session.startTime, null, 2) +
                        "\n";
                }, 1000);
            }

        })
    }

    closeDialog(ev) {
        if (this.props.close) {
            this.props.close();
        }
    }

    hangup(ev) {
        this.props.close()
        this.props.session.call_description = $('#description').val()
        this.props.session.phone_call_about = $('select[name="phonecall_about"]').val()
        this.props.session.terminate();
    }

    mute(ev) {
        this.props.session.mute();
        ev.view.document.querySelector('.mute').classList.add('d-none')
        ev.view.document.querySelector('.unmute').classList.remove('d-none')
    }
    unmute(ev) {
        this.props.session.unmute();
        ev.view.document.querySelector('.unmute').classList.add('d-none')
        ev.view.document.querySelector('.mute').classList.remove('d-none')
    }

    hold(ev) {
        try {
            this.props.session.hold();
            console.log("Holding");
        } catch (error) {
            console.error("Holding failed", error.stack || error);
        }
        ev.view.document.querySelector('.hold').classList.add('d-none')
        ev.view.document.querySelector('.unhold').classList.remove('d-none')
    }
    unhold(ev) {
        this.props.session.unhold()
            .then(function () {
                console.log("unHolding");
            }).catch(function (e) {
                console.error("unHolding failed", e.stack || e);
            });
        ev.view.document.querySelector('.unhold').classList.add('d-none')
        ev.view.document.querySelector('.hold').classList.remove('d-none')
    }

    startRecord(ev) {
        this.props.session.startRecord();
        this.notification.add(_t("Record started !"), { type: "success" });
        ev.view.document.querySelector(".startRecord").classList.add('d-none')
        ev.view.document.querySelector(".stopRecord").classList.remove('d-none')
    }
    stopRecord(ev) {
        this.props.session.stopRecord();
        this.notification.add(_t("Record stopped !"), { type: "success" });
        ev.view.document.querySelector(".stopRecord").classList.add('d-none')
        ev.view.document.querySelector(".startRecord").classList.remove('d-none')
    }

    park(ev) {
        this.props.session.park().then(function () {
            console.log("Parked");
        })
            .catch(function (e) {
                function close() {
                    clearInterval(interval);
                    dialog.close();
                }
                console.error("Park failed", e.stack || e);
            });
    }
    async transferForm(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var transferInput = ev.view.document.querySelector("input[name=transfer]");
        if (transferInput) {
            var destination = transferInput.value.trim();
            if (destination) {
                try {
                    await this.props.session.transfer(destination);
                    console.log("Transferred successfully");
                } catch (error) {
                    console.error("Transfer failed", error.stack || error);
                } finally {
                    transferInput.value = "";
                }
            } else {
                console.error("Destination is empty. Please provide a valid destination.");
            }
        } else {
            console.error("Transfer input not found in the form.");
        }
    }



    async activeAgentTransfer(ev) {
        ev.preventDefault()
        ev.stopPropagation()
        var available_agent_input = ev.view.document.querySelector("select[name=available_agents]");
        if (available_agent_input) {
            var destination = available_agent_input.value.trim()
            if (destination) {
                try {
                    await this.props.session.transfer(destination);
                    console.log("Transferred successfully");
                }
                catch (error) {
                    console.error("Agent Transfer Submit Failed", error.stack || error)
                }
                finally {
                    available_agent_input.value = "";
                }
            }
            else {
                console.log("Destination is Empty. Please provide a valid destination.")
            }
        } else {
            console.error("Agent Transfer input not found in the form.");
        }
    }
    async flipForm(ev) {
        ev.preventDefault()
        ev.stopPropagation()
        var flipFormInput = ev.view.document.querySelector("input[name=flip]");
        if (flipFormInput) {
            var destination = flipFormInput.value.trim()

            if (destination) {
                try {
                    await this.props.session.flip(destination);
                    console.log("Transferred successfully");
                }
                catch (error) {
                    console.error("Flip Form Submit Failed", error.stack || error)
                }
                finally {
                    flipFormInput.value = "";
                }
            }
            else {
                console.log("Destination is Empty. Please provide a valid destination.")
            }
        } else {
            console.error("FLipform input not found in the form.");
        }

    }
    async dtmfForm(ev) {
        ev.preventDefault()
        ev.stopPropagation()
        var dtmf_input = ev.view.document.querySelector("input[name=dtmf]");
        if (dtmf_input) {
            var destination = dtmf_input.value.trim()
            if (destination) {
                try {
                    await this.props.session.dtmf(destination);
                    console.log("Transferred dtmf successfully");
                }
                catch (error) {
                    console.error("dtmf Form Submit Failed", error.stack || error)
                }
                finally {
                    dtmf_input.value = "";
                }
            }
            else {
                console.log("Destination is Empty. Please provide a valid destination.")
            }
        } else {
            console.error("dtmf input not found in the form.");
        }
    }

    async createPartner(ev) {
        var new_contact_outgoing = await this.rpc('/create_new_contact', 'call', {
            caller_number: this.props.caller_number,
        })
        window.open(
            window.location.origin +
            "#id=" +
            parseInt(new_contact_outgoing) +
            "&action=" +
            this.props.call.contacts_action +
            "&model=res.partner&view_type=form",
            "_blank"
        );
    }

    Minimize() {
        var headerdialog = document.querySelector("#title_dialog").parentElement
        var outgoingCall = document.querySelector("#outgoingCall");
        outgoingCall.querySelector(".modal-footer").classList.add('d-none')
        outgoingCall.querySelector(".modal-body").classList.add('d-none')
        document.querySelector("#minimize").classList.add("d-none")
        document.querySelector("#maximize").classList.remove("d-none")
        headerdialog.setAttribute('style', ' background: #5b97d8;color: white; ');
    }

    maximize() {
        var headerdialog = document.querySelector("#title_dialog").parentElement
        var outgoingCall = document.querySelector("#outgoingCall");
        outgoingCall.querySelector(".modal-body").classList.remove('d-none')
        outgoingCall.querySelector(".modal-footer").classList.remove('d-none')
        document.querySelector("#maximize").classList.add("d-none")
        document.querySelector("#minimize").classList.remove("d-none")
        headerdialog.removeAttribute('style', 'background: #5b97d8;color: white; ');
    }
}
CallDialog.template = "ringcentral.outgoing_call";
CallDialog.components = { Dialog };