from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        for picking in self:
            super(StockPicking, self).button_validate()
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
