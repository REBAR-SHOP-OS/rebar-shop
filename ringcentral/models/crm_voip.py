# See LICENSE file for full copyright and licensing details.

import base64
import logging
import re
import tempfile
from datetime import datetime

import requests

from odoo import _, api, fields, models, registry
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CrmPhonecallAbout(models.Model):
    _name = "crm.phonecall.about"
    _description = "CRM PhoneCall About"

    name = fields.Char("Reason of the call", required=True)


class CrmPhonecall(models.Model):
    _name = "crm.phonecall"
    _description = "CRM PhoneCall"
    _order = "id"

    @api.model
    def fetch_agents(self):
        if self.env.company and self.env.company.ringcentral_server:
            headers = {
                "accept": "application/json",
            }
            if self.env.user.ringcentral_access_token:
                headers["authorization"] = (
                    "Bearer " + self.env.user.ringcentral_access_token
                )

            # for the Presence Call
            response = requests.get(
                str(self.env.company.ringcentral_server)
                + "/restapi/v1.0/account/~/presence",
                headers=headers,
                timeout=10,
            )
            response = response.json()

            response_data = response.get("records")

            if (response_data):
                if response.get("errorCode"):
                    raise UserError(_("Please log in RingCentral."))

            if response.get("errorCode"):
                raise UserError(_("Please log in RingCentral."))

            res_partner = self.env["res.partner"]
            for record in response_data:

                partner_id = res_partner.search(
                    [
                        (
                            "extension_number",
                            "=",
                            record.get("extension").get("extensionNumber"),
                        )
                    ],
                    limit=1,
                )
                if not partner_id:
                    res_partner.create(
                        {
                            "extension_id": record.get("extension").get("id"),
                            "extension_number": record.get("extension").get(
                                "extensionNumber"
                            ),
                            "name": record.get("extension").get("extensionNumber"),
                        }
                    )

            # for the Phone number call
            response = requests.get(
                str(self.env.company.ringcentral_server)
                + "/restapi/v1.0/account/~/phone-number",
                headers=headers,
                timeout=10,
            )
            response = response.json()
            res_partner = self.env["res.partner"]
            for record in response_data:
                partner_id = res_partner.search(
                    [
                        "|",
                        (
                            "extension_number",
                            "=",
                            record.get("extension")
                            and record.get("extension").get("extensionNumber"),
                        ),
                        ("phone", "=", record.get("phoneNumber")),
                    ],
                    limit=1,
                )
                name = str(record.get("phoneNumber"))
                if record.get("extension") and record.get("extension").get(
                    "extensionNumber"
                ):
                    name += " - " + \
                        record.get("extension").get("extensionNumber")
                vals = {
                    "extension_id": record.get("extension")
                    and record.get("extension").get("id"),
                    "phone": record.get("phoneNumber"),
                    "ringcentral_id": record.get("id"),
                    "extension_number": record.get("extension")
                    and record.get("extension").get("extensionNumber")
                    or "",
                    "name": name,
                }
                if not partner_id:
                    res_partner.create(vals)
                    continue
                vals.pop("name")
                partner_id.write(vals)

    def add_note_control(self):
        pass

    def _valid_field_parameter(self, field, name):
        # allow tracking on models inheriting from 'crm.phonecall'
        return name == "tracking" or super()._valid_field_parameter(field, name)

    name = fields.Char("Call Summary", required=True)

    type = fields.Selection(
        [
            ("in_bound", "In Bound"),
            ("out_bound", "Out Bound"),
            ("message", "Message"),
            ("receive", "Receive"),
            ("sent", "Sent"),
        ],
    )
    ringcentral_message_id = fields.Char()
    ringcentral_call_url = fields.Char("Ringcentral Call Recording URL")
    ringcentral_call_id = fields.Char("Ringcentral Call Record  Id")
    tag_ids = fields.Many2many(
        "in.out.tagged.documented",
        "rel_tagged_documented",
        "tagged_documented_id",
        "phoncall_id",
        "Tag",
    )
    date = fields.Datetime()
    crm_phonecall_about_id = fields.Many2one(
        "crm.phonecall.about", "Phonecall about?")
    user_id = fields.Many2one("res.users", "Responsible")
    partner_id = fields.Many2one("res.partner", "Contact")
    company_id = fields.Many2one("res.company", "Company")
    description = fields.Text()
    duration = fields.Float(help="Duration in minutes and seconds.")
    partner_phone = fields.Char("Phone")
    partner_mobile = fields.Char("Mobile")
    priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High")], string="priority"
    )
    team_id = fields.Many2one(
        "crm.team",
        "Sales Team",
        index=True,
        help="Sales team to which Case belongs to.",
    )
    categ_id = fields.Many2one("crm.phonecall.category", "Category")
    in_queue = fields.Boolean("In Call Queue", default=True)
    sequence = fields.Integer(
        index=True,
        help="Gives the sequence order when displaying a list of Phonecalls.",
    )
    start_time = fields.Integer()
    state = fields.Selection(
        [
            ("pending", "Not Held"),
            ("cancel", "Cancelled"),
            ("open", "To Do"),
            ("done", "Held"),
        ],
        string="Status",
        readonly=True,
        tracking=True,
        help="The status is set to To Do, when a case is created.\n"
        "When the call is over, the status is set to Held.\n"
        "If the call is not applicable anymore,"
        "the status can be set to Cancelled.",
    )
    opportunity_id = fields.Many2one(
        "crm.lead", "Lead/Opportunity", ondelete="cascade", tracking=True
    )
    check_notification = fields.Boolean("Check notification")
    crm_call_activity_ids = fields.One2many(
        "crm.call.activity", "crm_phonecall_id", "Crm Call Activity"
    )
    is_recording = fields.Boolean(string="IS Recording")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "phonecall_attachment_rel",
        "phonecall_id",
        "attachment_id",
        string="SMS attachment",
    )

    @api.model
    def create_search_voip(self, vals):
        # ringcentral_call_ids = self.search(
        #     [("ringcentral_call_id", "=", vals.get("ringcentral_call_id"))]
        # )
        # ringcentral_call_ids.unlink()
        if vals.get('date'):
            self.create(vals)

    @api.model
    def get_duration(self, duration):
        if not duration:
            return 0
        seconds = duration / 1000
        duration = seconds / 60
        return round(duration, 2)

    @api.model
    def synch_data(self, record_list):
        db_registry = registry(self._cr.dbname)
        with db_registry.cursor() as _cr:
            for record in record_list:
                record_id = record.get("id")
                if record_id:
                    voip_ids = self.search([("ringcentral_call_id", "=", record_id)])
                    if not voip_ids:
                        recording = record.get("recording")
                        if recording:
                            user_id = self.env.user
                            company = user_id.company_id
                            url = (company.ringcentral_service_uri or "").split("/login/")[0]
                            
                            rec_type = "Auto" if recording.get("type") == "Automatic" else recording.get("type")
                            
                            str_url = ""
                            if url:
                                str_url = (
                                    f"{url}/mobile/media?cmd=downloadMessage&msgid={recording.get('id') or ''}"
                                    f"&useName=true&time=1554700788480&msgExt=&msgNum={record.get('from', {}).get('phoneNumber') or ''}"
                                    f"&msgDir={record.get('direction') or ''}&msgRecType={rec_type or ''}"
                                    f"&msgRecId={recording.get('id') or ''}&type=1&download=1&saveMsg=&file=.mp3"
                                )
                            
                        try:
                            duration = self.get_duration(record.get("durationMs"))
                            vals = {
                                "name": record.get("to", {}).get("phoneNumber") or record.get("to", {}).get("extensionNumber") or "No Number Found",
                                "partner_phone": record.get("from", {}).get("phoneNumber"),
                                "date": datetime.today(),
                                "description": record.get("reasonDescription"),
                                "duration": duration,
                                "ringcentral_call_id": record_id,
                            }
                            val = {
                                "name": record.get("action"),
                                "call_type": record.get("direction"),
                                "leg_type": record.get("legType"),
                                "from_number": record.get("from", {}).get("phoneNumber"),
                                "to_number": record.get("to", {}).get("phoneNumber"),
                            }
                            
                            direction = record.get("direction")
                            if direction:
                                vals["type"] = "in_bound" if direction == "Inbound" else "out_bound" if direction == "Outbound" else ""
                            
                            if recording and str_url:
                                vals.update({
                                    "ringcentral_call_url": str_url,
                                    "is_recording": True
                                })
                            
                            vals.update({"crm_call_activity_ids": [(0, 0, val)]})
                            self.create(vals)
                            _cr.commit()
                        except ValueError as e:
                            _logger.warning(f"Error processing record {record_id}: {e}")

    @api.model
    def get_service_uri(self):
        return self.env.user.company_id.ringcentral_service_uri

    @api.model
    def ac_search_read(self):
        rec_message = self.search([])
        rec_message_id = rec_message.mapped("ringcentral_message_id")
        return rec_message_id

    @api.model
    def create_message(self, list_type):
        user_id = self.env.user
        for rec_vals in list_type:
            rec_data = self.search(
                [("ringcentral_message_id", "=", rec_vals.get("id"))]
            )
            if not rec_data:
                try:
                    vals = {
                        "name": rec_vals.get("from").get("phoneNumber") or "",
                        "partner_phone": rec_vals.get("to")[0].get("phoneNumber") if rec_vals.get("to") else "",
                        "date": rec_vals.get("creationTime"),
                        "description": rec_vals.get("subject"),
                        "ringcentral_message_id": rec_vals.get("id"),
                    }
                    if rec_vals.get("direction") == "Outbound":
                        vals.update({"type": "sent"})
                    else:
                        vals.update({"type": "receive"})
                    attachment_list = []
                    for attachment in rec_vals.get("attachments"):
                        if attachment.get("type") == "MmsAttachment":
                            auth_str = "Bearer  " + user_id.ringcentral_access_token
                            headers = {
                                "accept": "application/json",
                                "authorization": auth_str,
                            }
                            response = requests.get(
                                attachment.get("uri"), headers=headers, timeout=10
                            )
                            path = tempfile.mktemp("." + "image.png")
                            file_path = open(path, "wb")
                            file_path.write(response.content)
                            file_path.close()
                            buf = base64.encodebytes(open(path, "rb").read())
                            attachment_list.append(
                                (
                                    0,
                                    0,
                                    {
                                        "name": attachment.get("fileName")
                                        or "image.png",
                                        "type": "binary",
                                        "datas": buf,
                                    },
                                )
                            )
                    if attachment_list:
                        vals.update({"attachment_ids": attachment_list})
                    self.create(vals)
                except ValueError:
                    _logger.warning("")

    @api.onchange("partner_id")
    def on_change_partner_id(self):
        self.ensure_one()
        if self.partner_id:
            self.partner_phone = self.partner_id.phone
            self.partner_mobile = self.partner_id.mobile

    @api.model
    def create(self, values):
        if values.get("date") and isinstance(values.get("date"), str):
            date = fields.datetime.strptime(
                values.get("date"), "%Y-%m-%dT%H:%M:%S.%fZ")
            values["date"] = date.strftime("%Y-%m-%d %H:%M:%S")

        if values.get("name") and values.get("type") == "receive":
            array = re.findall(r"[0-9]+", values.get("name"))
            name = ""
            for rec in array:
                name += rec
            if len(name) > 10:
                number = len(name) - 10
                name = name[number:]
            self._cr.execute(
                r"""SELECT id FROM  res_partner
                    where NULLIF(regexp_replace(phone, '\D','','g'), '')::numeric::text
                    ilike %s limit 1""",
                (str("%" + name + "%"),),
            )
            rec = self._cr.fetchall()
            partner_id = False
            if rec:
                partner_id = rec[0][0]
            if partner_id:
                values.update({"partner_id": partner_id})
        if values.get("partner_phone"):
            array = re.findall(r"[0-9]+", values.get("partner_phone"))
            phone_number = ""
            for rec in array:
                phone_number += rec
            if len(phone_number) > 10:
                number = len(phone_number) - 10
                phone_number = phone_number[number:]
            self._cr.execute(
                r"""SELECT id FROM  res_partner
                    where NULLIF(regexp_replace(phone, '\D','','g'), '')::numeric::text
                    ilike %s limit 1""",
                (str("%" + phone_number + "%"),),
            )
            rec = self._cr.fetchall()
            partner_id = False
            if rec:
                partner_id = rec[0][0]
            if partner_id:
                values.update({"partner_id": partner_id})
        if values.get("crm_phonecall_about_id") and values.get("partner_id"):
            project_ids = self.env["project.project"].search(
                [
                    (
                        "phonecall_about_id",
                        "=",
                        int(values.get("crm_phonecall_about_id")),
                    )
                ],
                limit=1,
            )
            if project_ids:
                project = self.env["project.project"].browse(project_ids[0])
                partner = self.env["res.partner"].browse(
                    int(values.get("partner_id")))
                task_vals = {
                    "name": str(project.phonecall_about_id.name)
                    + ": "
                    + str(partner.name),
                    "project_id": project.id,
                    "description": values.get("description") or "",
                    "user_id": self._uid,
                    "partner_id": partner.id,
                }
                self.env["project.task"].create(task_vals)
        return super(CrmPhonecall, self).create(values)

    def write(self, values):
        if values.get("partner_phone"):
            array = re.findall(r"[0-9]+", values.get("partner_phone"))
            phone_number = ""
            for rec in array:
                phone_number += rec
            if len(phone_number) > 10:
                number = len(phone_number) - 10
                phone_number = phone_number[number:]
            self._cr.execute(
                r"""SELECT id FROM  res_partner
                    where NULLIF(regexp_replace(phone, '\D','','g'), '')::numeric::text
                    ilike %s limit 1""",
                (str("%" + phone_number + "%"),),
            )
            rec = self._cr.fetchall()
            partner_id = False
            if rec:
                partner_id = rec[0][0]
            if partner_id:
                values.update({"partner_id": partner_id})
        return super(CrmPhonecall, self).write(values)

    @api.model
    def get_partner_name(self, number):
        array = re.findall(r"[0-9]+", number)
        phone_number = ""
        for rec in array:
            phone_number += rec
        if len(phone_number) > 10:
            number = len(phone_number) - 10
            phone_number = phone_number[number:]
        self._cr.execute(
            r"""SELECT id FROM  res_partner
                where NULLIF(regexp_replace(phone, '\D','','g'), '')::numeric::text
                ilike %s""",
            (str("%" + phone_number + "%"),),
        )
        rec = self._cr.fetchall()
        rec_li = []
        if rec:
            for rec_id in rec:
                rec_li.append(rec_id[0])
        rec = self.env["res.partner"].search_read(
            [("id", "in", rec_li)], ["name", "phone", "child_ids"]
        )
        return rec


class CrmCallActivity(models.Model):
    _name = "crm.call.activity"
    _description = "CRM Call Activity"

    name = fields.Char("Reason")
    type = fields.Selection(
        [("in_bound", "In Bound"), ("out_bound", "Out Bound")])
    call_type = fields.Char()
    leg_type = fields.Char()
    from_number = fields.Char("From number")
    to_number = fields.Char("To number")
    act_date = fields.Datetime("Activity Date")
    from_user = fields.Many2one("res.users", "Transfer From")
    to_user = fields.Many2one("res.users", "Transfer To")
    crm_phonecall_id = fields.Many2one("crm.phonecall", "Phonecall")


class InOutTaggedDocumented(models.Model):
    _name = "in.out.tagged.documented"
    _description = "In Out Tag"

    name = fields.Char()


class CrmLead(models.Model):
    _inherit = "crm.lead"
    in_call_center_queue = fields.Boolean(
        "Is in the Call Queue", compute="_compute_is_call_center"
    )

    def _compute_is_call_center(self):
        phonecall = self.env["crm.phonecall"].search(
            [
                ("in_queue", "=", True),
                ("state", "!=", "done"),
                ("user_id", "=", self.env.user[0].id),
            ]
        )
        if phonecall:
            self.in_call_center_queue = True
        else:
            self.in_call_center_queue = False


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _compute_get_phone_count(self):
        for partner in self:
            partner.phone_count = len(partner.ph_log_ids)

    ph_log_ids = fields.One2many(
        "crm.phonecall",
        "partner_id",
        "Phonecall Log",
        domain=["|", ("type", "=", "in_bound"), ("type", "=", "out_bound")],
    )
    msg_log_ids = fields.One2many(
        "crm.phonecall",
        "partner_id",
        "Message Log",
        domain=["|", ("type", "=", "sent"), ("type", "=", "receive")],
    )
    phone_count = fields.Integer(
        compute="_compute_get_phone_count", string="Phones")

    def create_call_in_queue(self, number):
        phonecall = self.env["crm.phonecall"].create(
            {
                "name": "Call for " + self.name,
                "duration": 0,
                "user_id": self.env.user[0].id,
                "partner_id": self.id,
                "state": "open",
                "partner_phone": number,
                "in_queue": True,
                "type": "out_bound",
            }
        )
        return phonecall.id


class CrmPhonecallCategory(models.Model):
    _name = "crm.phonecall.category"
    _description = "Category of phone call"

    name = fields.Char(required=True, translate=True)
    team_id = fields.Many2one("crm.team", "Sales Team")


class IrAttachment(models.Model):

    _inherit = "ir.attachment"

    def downlaod_file(self):
        for doc_id in self:
            return {
                "type": "ir.actions.act_url",
                "url": "web/content/%s?download=true&filename=%s"
                % (doc_id.id, doc_id.name),
                "target": "new",
            }
