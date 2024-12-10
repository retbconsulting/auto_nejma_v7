# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import ast

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RelocateStockQuant(models.TransientModel):
    _inherit = 'stock.quant.relocate'
    _description = 'Stock Quantity Relocation'

    def action_relocate_quants(self):
        self.ensure_one()
        '''lot_ids = self.quant_ids.lot_id
        product_ids = self.quant_ids.product_id'''

        for location in self.quant_ids.location_id:
            location_quants = self.quant_ids.filtered(lambda r: r.location_id == location)
            picking_pull = self.env['stock.picking'].create({
                'picking_type_id': self.env.ref('stock.picking_type_internal').id,
                'location_id': location.id,
                'location_dest_id': self.env.ref('stock_auto_nejma.stock_location_carrier').id,
                'state': 'draft',
                'origin': 'Transfert interne',
                'move_ids_without_package': [(0, 0, {
                    'name': quant.product_id.name,
                    'product_id': quant.product_id.id,
                    'product_uom_qty': 1,
                    'location_id': location.id,
                    'location_dest_id': self.env.ref('stock_auto_nejma.stock_location_carrier').id,
                }) for quant in location_quants]
            })
            picking_pull.action_confirm()
            '''for move in picking_pull.move_ids_without_package:
                move.lot_ids = [(6, 0, [self.env['stock.lot'].search([('name', '=', move.purchase_line_id.vin_number)], limit=1).id])]'''

            picking_push = self.env['stock.picking'].create({
                'picking_type_id': self.env.ref('stock.picking_type_internal').id,
                'location_id': self.env.ref('stock_auto_nejma.stock_location_carrier').id,
                'state': 'draft',
                'location_dest_id': self.dest_location_id.id,
                'origin': 'Transfert interne',
                'move_ids_without_package': [(0, 0, {
                    'name': quant.product_id.name,
                    'product_id': quant.product_id.id,
                    'product_uom_qty': 1,
                    'location_id': self.env.ref('stock_auto_nejma.stock_location_carrier').id,
                    'location_dest_id': self.dest_location_id.id,
                }) for quant in location_quants]
            })
            picking_push.action_confirm()
        self.quant_ids.write({
            'dest_location_id': self.dest_location_id.id
        })
        '''if not self.dest_location_id and not self.dest_package_id:
            return
        self.quant_ids.action_clear_inventory_quantity()

        if self.is_partial_package and not self.dest_package_id:
            quants_to_unpack = self.quant_ids.filtered(lambda q: not all(sub_q in self.quant_ids.ids for sub_q in q.package_id.quant_ids.ids))
            quants_to_unpack.move_quants(location_dest_id=self.dest_location_id, message=self.message, unpack=True)
            self.quant_ids -= quants_to_unpack
        self.quant_ids.move_quants(location_dest_id=self.dest_location_id, package_dest_id=self.dest_package_id, message=self.message)

        if self.env.context.get('default_lot_id', False) and len(lot_ids) == 1:
            return lot_ids.action_lot_open_quants()
        elif self.env.context.get('single_product', False) and len(product_ids) == 1:
            return product_ids.action_update_quantity_on_hand()
        return self.env['ir.actions.server']._for_xml_id(self.env.context.get('action_ref', 'stock.action_view_quants'))'''

