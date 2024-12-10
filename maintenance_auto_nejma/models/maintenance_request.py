from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    schedule_date = fields.Date('Date prévue',
                                    help="Date the maintenance team plans the maintenance.  It should not differ much from the Request Date. ")
    schedule_end_date = fields.Date(string="Date de fin")
    type = fields.Selection([('pdi', 'PDI'),
                               ('others', 'Autres')], string="Type", default='others')
    repair_order_id = fields.Many2one(comodel_name='repair.order',
                                      string="Ordre de réparation")

    @api.model
    def create(self, vals):
        if vals.get('type') and vals.get('type') == 'pdi':
            if vals.get('maintenance_team_id') and vals.get('schedule_date'):
                current_team = self.env['maintenance.team'].sudo().browse(vals.get('maintenance_team_id'))
                schedule_date = vals.get('schedule_date')
                if len(self.env['maintenance.request'].sudo().search([('maintenance_team_id', '=', current_team.id),
                                                               ('schedule_date', '=',schedule_date),
                                                               ('type', '=', 'pdi')])) >= current_team.capacity:
                    raise ValidationError("La capacité de la journée est atteinte")
        return super(MaintenanceRequest, self).create(vals)

    def write(self, vals):
        if self.type == 'pdi':
            if self.maintenance_team_id and self.schedule_date and vals.get('schedule_date'):
                if len(self.env['maintenance.request'].sudo().search(
                        [('maintenance_team_id', '=', self.maintenance_team_id.id),
                         ('schedule_date', '=', vals.get('schedule_date')),
                         ('type', '=', 'pdi')])) >= self.maintenance_team_id.capacity:
                    raise ValidationError("La capacité de la journée est atteinte")
        res = super().write(vals)
        for record in self:
            if self.type == 'pdi':
                record.onchange_schedule_dates()
        return res

    @api.onchange('schedule_date')
    def onchange_schedule_dates(self):
        if self.type == 'pdi':
            #self.schedule_end_date = self.schedule_date
            if self.schedule_date:
                if self.schedule_date < datetime.now().date() + timedelta(days=2):
                    raise ValidationError("La date devra être supérieure à la date courante + 48h ")

    @api.onchange('equipment_id')
    def onchange_equipment_id(self):
        if self.type == 'pdi' and self.equipment_id:
            self.name = 'PDI : ' + self.equipment_id.display_name
