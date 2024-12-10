# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta


class Route(models.Model):
    _name = 'au.route'
    _description = 'Route'
    _rec_name = 'trajet'

    #name = fields.Char(string='Name')
    destination_id = fields.Many2one('stock.location', string='Destination')
    source_id = fields.Many2one('stock.location', string='Position')
    trajet = fields.Char(string='Trajet', compute='_compute_trajet', store=True)
    sla = fields.Float(string='SLA')
    active = fields.Boolean(default=True)

    @api.depends('destination_id.name', 'source_id.name')
    def _compute_trajet(self):
        for record in self:
            if record.destination_id.name and record.source_id.name:
                record.trajet = f"{record.destination_id.name} / {record.source_id.name}"
            else:
                record.trajet = False


'''class Destination(models.Model):
    _name = 'au.destination'
    _description = 'Destination'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    route_ids = fields.One2many('au.route', 'destination_id', string='Routes')
    active = fields.Boolean(default=True)'''


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    route_id = fields.Many2one('au.route', string='Route', compute='_compute_route', store=True)
    route_sla = fields.Float(string='SLA', related='route_id.sla', store=True)
    
    @api.depends('location_id', 'location_dest_id')
    def _compute_route(self):
        for picking in self:
            print ('I want to work')
            if picking.location_id and picking.location_dest_id:
                route = self.env['au.route'].search([('source_id', '=', picking.location_id.id), ('destination_id', '=', picking.location_dest_id.id)], limit=1)
                print ('Route', route)
                if route:
                    picking.route_id = route.id

    @api.onchange('route_id','location_id','location_dest_id')
    def _onchange_route_id(self):
        """Update scheduled_date based on route's SLA (in days) when route is changed"""
        if self.route_id and self.route_id.sla:
            current_date = fields.Datetime.now()
            sla_days = self.route_id.sla
            self.scheduled_date = current_date + timedelta(days=sla_days)

    @api.model
    def create(self, vals):
        """Override create to set scheduled_date based on route's SLA"""
        if vals.get('route_id'):
            route = self.env['au.route'].browse(vals['route_id'])
            if route and route.sla:
                current_date = fields.Datetime.now()
                sla_days = route.sla
                vals['scheduled_date'] = current_date + timedelta(days=sla_days)
        return super(StockPicking, self).create(vals)

    def write(self, vals):
        """Override write to update scheduled_date when route is changed"""
        if vals.get('route_id'):
            route = self.env['au.route'].browse(vals['route_id'])
            if route and route.sla:
                current_date = fields.Datetime.now()
                sla_days = route.sla
                vals['scheduled_date'] = current_date + timedelta(days=sla_days)
        return super(StockPicking, self).write(vals)


