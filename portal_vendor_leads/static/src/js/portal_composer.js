/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import portalComposer from "@portal/js/portal_composer";

var PortalComposer = portalComposer.PortalComposer;

/**
 * PortalComposer
 *
 * Extends Portal Composer to handle rating submission
 */
PortalComposer.include({
    events: Object.assign({}, PortalComposer.prototype.events, {
        'click .stars i': '_onClickStar',
        'input #taggingTextarea': 'onInputTextArea',
        'keydown #taggingTextarea': 'onKeyDownTextArea',
        'click .dropdown-item': 'onclickDropdownItem',
    }),

    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self.$textarea = $("#taggingTextarea");
            self.$dropdown = $("#tag-dropdown");
            self.$partner_ids_to_add = '';
            self.users = self.options.message_partner_ids ? { ...self.options.message_partner_ids } : {};
            self.selectedTags = [];
            self.itemss = [];
        });
    },

    showDropdown: function (filteredUsers = Object.entries(this.users)) {
        this.$dropdown.html(
            filteredUsers
                .map(([id, name]) => `<div class="dropdown-item" data-user-id="${id}" data-user-name="${name}">${name}</div>`)
                .join("")
        );
        this.$dropdown.removeClass("hidden");
    },

    hideDropdown: function () {
        this.$dropdown.addClass("hidden");
    },

    onclickDropdownItem: function (event) {
        const $item = $(event.currentTarget);
        const selectedUserId = $item.data("user-id");
        const selectedUserName = $item.data("user-name");

        if (selectedUserId && selectedUserName) {
            const value = this.$textarea.val();
            const beforeTag = value.substring(0, this.tagStartIndex);
            const afterTag = value.substring(this.$textarea[0].selectionStart);
            this.$textarea.val(`${beforeTag}@${selectedUserName} ${afterTag}`);
            this.selectedTags.push(parseInt(selectedUserId));
            this.itemss.push(parseInt(selectedUserId));
            this.isTagging = false;
            this.hideDropdown();
            this.$textarea.focus();
        }
    },

    onInputTextArea: function () {
        const value = this.$textarea.val();
        const cursorPos = this.$textarea[0].selectionStart;

        if (value[cursorPos - 1] === "@") {
            this.isTagging = true;
            this.tagStartIndex = cursorPos - 1;
            this.showDropdown();
        } else if (this.isTagging) {
            const currentTagText = value.substring(this.tagStartIndex + 1, cursorPos);
            const filteredUsers = Object.entries(this.users).filter(
                ([id, name]) =>
                    !this.selectedTags.includes(parseInt(id)) &&
                    name.toLowerCase().startsWith(currentTagText.toLowerCase())
            );
            if (filteredUsers.length > 0) {
                this.showDropdown(filteredUsers);
            } else {
                this.hideDropdown();
            }
        }

        this.updateSelectedTags(value);
    },

    onKeyDownTextArea: function (e) {
        const value = this.$textarea.val();
        const cursorPos = this.$textarea[0].selectionStart;

        if (e.key === "Backspace") {
            const beforeCursor = value.substring(0, cursorPos);
            const match = beforeCursor.match(/@(\w+)$/);

            if (match) {
                const username = match[1];
                const beforeTag = value.substring(0, beforeCursor.length - match[0].length);
                const afterTag = value.substring(cursorPos);

                this.$textarea.val(`${beforeTag}${afterTag}`);
                this.hideDropdown();
                this.isTagging = false;

                const userId = Object.keys(this.users).find(
                    (id) => this.users[id] === username
                );

                if (userId) {
                    const userIdIndex = this.itemss.indexOf(parseInt(userId));
                    if (userIdIndex !== -1) {
                        this.itemss.splice(userIdIndex, 1);
                    }
                }
            }
        }

        this.updateSelectedTags(this.$textarea.val());
    },

    updateSelectedTags: function (value) {
        const currentTags = (value.match(/@(\w+)/g) || []).map((tag) => tag.slice(1));
        const currentTagIds = Object.entries(this.options.message_partner_ids).reduce((acc, [id, name]) => {
            if (currentTags.includes(name)) {
                acc.push(parseInt(id));
            }
            return acc;
        }, []);

        this.selectedTags = currentTagIds;
        if (this.isTagging) {
            const filteredUsers = Object.entries(this.users).filter(
                ([id, name]) => !this.selectedTags.includes(parseInt(id))
            );
            this.showDropdown(filteredUsers);
        }
    },

    _prepareMessageData: function () {
        let data = {};
        if (this.options.res_model === 'crm.lead') {
            data = {
                lead_partners: this.itemss.length > 0 ? this.itemss.join(",") : "",
            };
        }
        return Object.assign(this._super(...arguments) || {}, data);
    },
});
