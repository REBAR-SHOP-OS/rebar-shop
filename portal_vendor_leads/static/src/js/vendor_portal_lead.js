/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import publicWidget from "@web/legacy/js/public/public_widget";
import { parseDate, formatDate, serializeDate } from "@web/core/l10n/dates";
const { DateTime } = luxon;

publicWidget.registry.portalVendorLead = publicWidget.Widget.extend({
    selector: '#wrapwrap:has(.opp-stage-button)',
    events: {
        'click .opp-stage-button': '_onOppStageButtonClick',
        'click .edit_opp_confirm': '_onEditOppConfirm',
        'change .edit_opp_form .next_activity': '_onChangeNextActivity',
    },

    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {jQuery} $btn
     * @param {function} callback
     * @returns {Promise}
     */
    _buttonExec: function ($btn, callback) {
        // TODO remove once the automatic system which does this lands in master
        $btn.prop('disabled', true);
        return callback.call(this).catch(function (e) {
            $btn.prop('disabled', false);
            if (e instanceof Error) {
                return Promise.reject(e);
            }
        });
    },


    /**
     * @private
     * @param {}
     * @returns {Promise}
     */
    _changeOppStage: function (leadID, stageID) {
        return this.orm.write("crm.lead", [leadID], { stage_id: stageID }, {
            context: Object.assign({website_partner_assign: 1}),
        }).then(function () {
            window.location.reload();
        });
    },

    /**
     * @private
     * @returns {Promise}
     */
    _editOpportunity: function () {
        return this.orm.call("crm.lead", "update_vendor_lead_portal", [
            [parseInt($('.edit_opp_form .opportunity_id').val())],
            {
                date_deadline: this._parse_date($('.edit_opp_form .date_deadline').val()),
                expected_revenue: parseFloat($('.edit_opp_form .expected_revenue').val()),
                probability: parseFloat($('.edit_opp_form .probability').val()),
                activity_type_id: parseInt($('.edit_opp_form .next_activity').find(':selected').attr('data')),
                activity_summary: $('.edit_opp_form .activity_summary').val(),
                activity_date_deadline: this._parse_date($('.edit_opp_form .activity_date_deadline').val()),
                priority: $('input[name="PriorityRadioOptions"]:checked').val(),
                estimation_weight: parseFloat($('.edit_opp_form .estimation_weight').val()),
            },
        ]).then(function () {
            window.location.reload();
        });
    },


    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------


    /**
     * @private
     * @param {Event} ev
     */
    _onOppStageButtonClick: function (ev) {
        var $btn = $(ev.currentTarget);
        this._buttonExec(
            $btn,
            this._changeOppStage.bind(this, parseInt($btn.attr('opp')), parseInt($btn.attr('data')))
        );
    },


    /**
     * @private
     * @param {Event} ev
     */
    _onEditOppConfirm: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this._buttonExec($(ev.currentTarget), this._editOpportunity);
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onChangeNextActivity: function (ev) {
        var $selected = $('.edit_opp_form .next_activity').find(':selected');
        if ($selected.attr('activity_summary')) {
            $('.edit_opp_form .activity_summary').val($selected.attr('activity_summary'));
        }
        if ($selected.attr('delay_count')) {
            const value = +$selected.attr('delay_count');
            const unit = $selected.attr('delay_unit');
            const date = DateTime.now().plus({ [unit]: value});
            $('.edit_opp_form .activity_date_deadline').val( formatDate(date) );
        }
    },
    _parse_date: function (value) {
        var date = parseDate(value);
        if (!date.isValid || date.year < 1900) {
            return false;
        }
        return serializeDate(date);
    },
});
