from odoo import models, api
from odoo.exceptions import UserError



class BaseModel(models.AbstractModel):
    _inherit = "base"

    @api.model
    def unlink(self):
        restricted_models = self.env.user.company_id.restricted_models.mapped("model")
        if (
            not self.env.user.has_group("scs_sale_management.group_delete_access")
            and self._name in restricted_models
        ):
            raise UserError(
                "You do not have permission to delete this record. Please contact an admin."
            )
        return super(BaseModel, self).unlink()
