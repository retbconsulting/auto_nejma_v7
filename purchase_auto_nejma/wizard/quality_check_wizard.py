# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import ast

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class QualityCheckWizard(models.TransientModel):
    _inherit = 'quality.check.wizard'
    _description = "Wizard for Quality Check Pop Up"

    qty_failed = fields.Float(digits='Product Unit of Measure')

    def do_pass(self):
        '''if self.test_type == 'picture' and not self.picture:
            raise UserError(_('You must provide a picture before validating'))'''
        if self.test_type == 'picture' and not self.picture and self.current_check_id.point_id.measure_on == 'operation':
            raise UserError(_('Merci de joindre la CIN du chauffeur'))
        self.current_check_id.do_pass()
        return self.action_generate_next_window()

    def do_fail(self):
        if self.test_type == 'picture' and not self.picture:
            raise UserError(_('Merci de mettre une photo'))
        if self.measure_on == 'move_line' and \
                not (self.product_tracking == 'serial' and not self.potential_failure_location_ids):
            return self.show_failure_message()
        if self.failure_message or self.warning_message:
            self.current_check_id.do_fail()
            return self.show_failure_message()
        #self.create_repair()
        '''if self.current_check_id.picture:
            mail_template = self.env.ref('purchase_auto_nejma.mail_quality_failed')
            email_values = {
                'picture': self.current_check_id.picture
            }
            mail_template.send_mail(self.id, force_send=True)'''
        return self.confirm_fail()

    def create_repair(self):
        print ("Helllo", self.current_check_id)
        '''self.env['repair.order'].create({

        })'''

    def confirm_fail(self):
        self.current_check_id.do_fail()
        current_check = self.current_check_id
        if self.measure_on == 'move_line':
            self.current_check_id._move_line_to_failure_location(self.failure_location_id.id, self.qty_failed)
            picking_type = self.env['stock.picking.type'].search([('sequence_code', '=', 'RO')], limit=1)
            self.env['repair.order'].sudo().create({
                'product_id': current_check.product_id.id,
                'lot_id': current_check.lot_id.id,
                'product_qty': current_check.qty_line,
                'picking_type_id': picking_type.id,
                'company_id': picking_type.company_id.id,
                'picture': current_check.picture
            })
        return self.action_generate_next_window()