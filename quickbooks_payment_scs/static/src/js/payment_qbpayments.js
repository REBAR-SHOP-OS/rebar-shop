/** @odoo-module **/
import paymentForm from "@payment/js/payment_form";
import {RPCError} from "@web/core/network/rpc_service";
import {_t} from "@web/core/l10n/translation";

paymentForm.include({

    async _processRedirectFlow(
        providerCode,
        paymentOptionId,
        paymentMethodCode,
        processingValues
    ) {
        if (providerCode !== "qbpayments") {
            this._super(...arguments);
            return;
        }
        return this.rpc("/payment/qbpayments/charge", {
            provider_id: processingValues.provider_id,
            reference: processingValues.reference,
            amount: processingValues.amount,
            currency_id: processingValues.currency_id,
            partner_id: processingValues.partner_id,
        })
            .then((paymentResponse) => {
                window.open(paymentResponse.Invoice.InvoiceLink, "_self");
                //            	window.location = '/payment/status';
            })
            .catch((error) => {
                if (error instanceof RPCError) {
                    this._displayErrorDialog(
                        _t("Payment processing failed"),
                        error.data.message
                    );
                    this._enableButton();
                } else {
                    return Promise.reject(error);
                }
            });
    },
});
