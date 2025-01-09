from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def check_quality(self):
        print ('I m gooooooooooooood')
        self.ensure_one()
        checkable_products = self.mapped('move_line_ids').mapped('product_id')
        checks = self.check_ids.filtered(lambda check: check.quality_state == 'none' and ((check.product_id in checkable_products and check.lot_id) or check.measure_on == 'operation'))
        if checks:
            return checks.action_open_quality_check_wizard()
        return False

    def _sanity_check(self, separate_pickings=True):
        """ Sanity check for `button_validate()`
            :param separate_pickings: Indicates if pickings should be checked independently for lot/serial numbers or not.
        """
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        pickings_without_moves = self.filtered(lambda p: not p.move_ids and not p.move_line_ids)
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        no_quantities_done_ids = set()
        pickings_without_quantities = self.env['stock.picking']
        for picking in self:
            if all(float_is_zero(move.quantity, precision_digits=precision_digits) for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))):
                pickings_without_quantities |= picking

        pickings_using_lots = self.filtered(lambda p: p.picking_type_id.use_create_lots or p.picking_type_id.use_existing_lots)
        if pickings_using_lots:
            lines_to_check = pickings_using_lots._get_lot_move_lines_for_sanity_check(no_quantities_done_ids, separate_pickings)
            for line in lines_to_check:
                if not line.lot_name and not line.lot_id:
                    pickings_without_lots |= line.picking_id
                    products_without_lots |= line.product_id

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_("You can’t validate an empty transfer. Please add some products to move before proceeding."))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                print ('yeeeeeeeeeeeeeeeees')
                not_transport_picking = pickings_without_lots.filtered(lambda r: r.location_dest_id.id != self.env.ref('stock_auto_nejma.stock_location_carrier').id and r.location_id.id != self.env.ref('stock_auto_nejma.stock_location_carrier').id)
                print (not_transport_picking)
                if not_transport_picking:
                    raise UserError(_('You need to supply a Lot/Serial number for products %s.', ', '.join(products_without_lots.mapped('display_name'))))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.', ', '.join(pickings_without_moves.mapped('name')))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.', ', '.join(pickings_without_lots.mapped('name')), ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())

    def _create_maintenance_requests(self, equipment):
        wks_templates = self.env['worksheet.template'].search([('res_model', '=', 'maintenance.request'), ('company_ids', 'in', equipment.company_id.id)])
        for wks_template in wks_templates.filtered(lambda w: w.name in ('Arrivée', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12')):
            '''recurring = 1
            repeat_unit = 'month'
            if wks_template.name == "MB VUL/VU Semestriel après 6 mois de l'arrivage":
                recurring = 6
                repeat_unit = 'month'
                request_date =
            #elif wks_template.name == "MB VUL/VU Trimestriel après 3 mois de l'arrivage":
            #    recurring = 3
            #    repeat_unit = 'month'
            elif wks_template.name == "MB VUL/VU Annuel après un mois de l'arrivage":
                recurring = 1
                repeat_unit = 'year'
                request_date ='''
            schedule_date = datetime.now().date()
            if wks_template.name == 'M1':
                schedule_date = datetime.now().date() + relativedelta(months=+1)
            if wks_template.name == 'M2':
                schedule_date = datetime.now().date() + relativedelta(months=+2)
            if wks_template.name == 'M3':
                schedule_date = datetime.now().date() + relativedelta(months=+3)
            if wks_template.name == 'M4':
                schedule_date = datetime.now().date() + relativedelta(months=+4)
            if wks_template.name == 'M5':
                schedule_date = datetime.now().date() + relativedelta(months=+5)
            if wks_template.name == 'M6':
                schedule_date = datetime.now().date() + relativedelta(months=+6)
            if wks_template.name == 'M7':
                schedule_date = datetime.now().date() + relativedelta(months=+7)
            if wks_template.name == 'M8':
                schedule_date = datetime.now().date() + relativedelta(months=+8)
            if wks_template.name == 'M9':
                schedule_date = datetime.now().date() + relativedelta(months=+9)
            if wks_template.name == 'M10':
                schedule_date = datetime.now().date() + relativedelta(months=+10)
            if wks_template.name == 'M11':
                schedule_date = datetime.now().date() + relativedelta(months=+11)
            if wks_template.name == 'M12':
                schedule_date = datetime.now().date() + relativedelta(months=+12)
            rqs_maintenance = self.env['maintenance.request'].create({
                'name': equipment.name + ' / ' + equipment.serial_no,
                'equipment_id': equipment.id,
                'worksheet_template_id': wks_template.id,
                'maintenance_type' : 'preventive',
                'schedule_date': schedule_date,
                'schedule_end_date': schedule_date,
                'duration': 24,
                'recurring_maintenance': True,
                'maintenance_team_id': self.env['maintenance.team'].search([('name', '!=', 'PDI')], limit=1).id,
                'repeat_interval': 1,
                'repeat_unit': 'year',
                'repeat_type': 'forever'
            })
            '''if wks_template.name == "MB VUL/VU Annuel  après 11 mois de l'arrivage":
                rqs_maintenance.request_date = rqs_maintenance.request_date + relativedelta(months=12)
                rqs_maintenance.repeat_interval = 1
                rqs_maintenance.repeat_unit = 'year'
            rqs_maintenance.schedule_date = rqs_maintenance.request_date'''

        return equipment

    def button_validate(self):
        for picking in self:
            print ("1")
            super(StockPicking, self).button_validate()
            print("2")
            if picking.origin:
                po = self.env['purchase.order'].search([('name', '=', picking.origin)], limit=1)
                if po:
                    po.write({
                        'state':  'recepted'
                    })
                    mail_template = self.env.ref('purchase_auto_nejma.autonejma_notified_recepted')
                    mail_template.send_mail(po.id, force_send=True)

                    for move in picking.move_ids_without_package.filtered(lambda m : m.lot_ids):
                        equipment = self.env['maintenance.equipment'].create({
                            'name': move.description_picking,
                            'serial_no': move.lot_ids[0].name,
                            'partner_id': picking.partner_id.id
                        })
                """if picking.location_id.id == self.env['stock.location'].search([('usage', '=', 'internal'), ('name', '=', 'Transport')], limit=1).id:
                    origin = picking.origin
                    po_names = origin.split(',')
                    pos = self.env['purchase.order'].search([('name', 'in', po_names)])
                    for po in pos.filtered(lambda p: p.state == 'dedouaned'):
                        po.state = 'deliver_to_carrier'"""

            if picking.location_dest_id.id == self.env.ref('stock_auto_nejma.stock_location_carrier').id:
                mail_template = self.env.ref('purchase_auto_nejma.autonejma_deliver_to_carrier')
                mail_template.send_mail(picking.id, force_send=True)

            if picking.location_id.id == self.env.ref('stock_auto_nejma.stock_location_carrier').id:
                for move in picking.move_line_ids.filtered(lambda l: l.lot_id):
                    equipment = self.env['maintenance.equipment'].search(
                        [('serial_no', '=', move.lot_id.name)], limit=1
                    )
                    if equipment:
                        picking._create_maintenance_requests(equipment)