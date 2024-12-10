from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta


class MaintenanceTeam(models.Model):
    _inherit = "maintenance.team"

    capacity = fields.Integer('Capacité')
