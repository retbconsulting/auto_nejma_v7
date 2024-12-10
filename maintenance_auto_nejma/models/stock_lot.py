from odoo import fields, models, api
from dateutil.relativedelta import relativedelta

class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    lot_id = fields.Many2one(comodel_name='stock.lot', string="Lot/Numéro de série")
    location_id = fields.Many2one(related="lot_id.location_id", store=True)


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    location_id = fields.Many2one(related="equipment_id.location_id", store=True)


class StockLot(models.Model):
    _inherit = "stock.lot"

    @api.model_create_multi
    def create(self, vals_list):
        res = super(StockLot, self.with_context(mail_create_nosubscribe=True)).create(vals_list)
        for record in self:
            equipment = record._create_equipment(vals_list)
            #record._create_maintenance_requests(equipment)
            equipment.lot_id = record.id
        return res

    def _create_equipment(self, vals_list):
        equipment = self.env['maintenance.equipment'].create({
            'name': self.env['product.product'].browse(vals_list[0]['product_id']).name,
            'company_id': vals_list[0]['company_id'],
            'serial_no' : vals_list[0]['name']
        })
        return equipment

    def _create_maintenance_requests(self, equipment):
        wks_templates = self.env['worksheet.template'].search([('res_model', '=', 'maintenance.request'), ('company_ids', 'in', equipment.company_id.id)])
        for wks_template in wks_templates:
            recurring = 1
            repeat_unit = 'month'
            if wks_template.name == 'Semestriel':
                recurring = 6
                repeat_unit = 'month'
            elif wks_template.name == 'Trimestriel':
                recurring = 3
                repeat_unit = 'month'
            elif wks_template.name == 'Annuel':
                recurring = 1
                repeat_unit = 'year'

            rqs_maintenance = self.env['maintenance.request'].create({
                'name': equipment.name + ' / ' + equipment.serial_no,
                'equipment_id': equipment.id,
                'worksheet_template_id': wks_template.id,
                'maintenance_type' : 'preventive',
                'recurring_maintenance': True,
                'maintenance_team_id': self.env['maintenance.team'].search([('name', '=', equipment.company_id.name)], limit=1).id,
                'repeat_interval': recurring,
                'repeat_unit': repeat_unit,
                'repeat_type': 'forever'
            })
            if wks_template.name == 'Après 12 mois':
                rqs_maintenance.request_date = rqs_maintenance.request_date + relativedelta(months=12)
                rqs_maintenance.repeat_interval = 1
                rqs_maintenance.repeat_unit = 'year'
            rqs_maintenance.schedule_date = rqs_maintenance.request_date

        return equipment
