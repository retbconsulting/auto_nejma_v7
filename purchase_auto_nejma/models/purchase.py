from odoo import fields, models, api, _, Command
from odoo.exceptions import AccessError, UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    vsb_number = fields.Char(string="VSB No.")
    order_number = fields.Char(string="ORDER NO.")
    vin_number = fields.Char(string="VIN N°")
    engine_number = fields.Char(string="ENGINE NUMBER")
    bm = fields.Char(string="BM")
    length = fields.Char(string="LENGTH")
    width = fields.Char(string="WIDTH")
    height = fields.Char(string="HEIGHT")
    weight = fields.Char(string="WEIGHT")
    fuel = fields.Selection([
        ('diesel', 'Diesel'),
        ('essence-electrique', 'Essence -Electrique')
    ], string='Carburant')
    traking_number = fields.Char(string="Tracking N°")
    date = fields.Date(string="Date")
    invoice_number = fields.Char(string="Invoice Number")
    invoice_date = fields.Date(string="Invoice Date")
    attachment_invoice = fields.Binary(string='Facture commerciale')
    location_id = fields.Many2one(string='Destination',
                                  comodel_name='stock.location',
                                  domain='[("usage", "=", "internal")]')
    src_location_id = fields.Many2one(string='Source',
                                        comodel_name='stock.location',
                                      compute='_compute_default_src_location')
    internal_picking_ids = fields.Many2many(comodel_name='stock.picking', string='Transferts')

    arrival_doc_id = fields.Many2one(comodel_name='documents.document', string='Arrivage',
                                     related='order_id.arrival_doc_id', store=True)
    delivered = fields.Boolean(string="Remis au transporteur", compute='_is_delivered', store=True, default=False)
    status = fields.Selection([('draft', 'En instance'),
                               ('confirmed', 'Confirmé')], string="Etat", default='draft')
    received = fields.Boolean(string='Reçu', default=True)

    @api.depends('internal_picking_ids', 'internal_picking_ids.state')
    def _is_delivered(self):
        for pol in self:
            if pol.internal_picking_ids:
                if any(pick.state == "done" for pick in pol.filtered(lambda l:l.received).internal_picking_ids):
                    pol.delivered = True

    def _compute_default_src_location(self):
        for record in self:
            record.src_location_id = self.env.ref('stock_auto_nejma.stock_location_port').id,

    def generate_internal_pickings(self):
        pols = self.env['purchase.order.line'].search([('id','in',self.env.context.get('active_ids', []))])

        if any(pol.internal_picking_ids for pol in pols):
            raise UserError("Certaines lignes ont déjà été transférées au transporteur.")

        if any(not pol.src_location_id for pol in pols):
            raise UserError(_("L'emplacement source n'est pas spécifié pour certaines lignes %s.",pols))

        if any(not pol.location_id for pol in pols):
            raise UserError("L'emplacement destination n'est pas spécifié pour certaines lignes.")

        if len(pols.location_id) > 1 or len(pols.src_location_id) > 1:
            raise UserError("Les emplacements source et destination doivent être identiques pour toutes les lignes.")

        missing_vins = []

        for pol in pols:
            if not self.env['stock.lot'].search([('name', '=', pol.vin_number)]):
                missing_vins.append(pol.vin_number)
        print(missing_vins)
        if missing_vins:
            missing_vins_msg = ', '.join(missing_vin for missing_vin in missing_vins)
            raise UserError(_('Les numéros de châssis %s n\'existent pas dans le système.', missing_vins_msg))

        picking_pull = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
            'location_id': self.env.ref('stock_auto_nejma.stock_location_port').id,
            'location_dest_id': self.env.ref('stock_auto_nejma.stock_location_carrier').id,
            'origin': ','.join(pol.partner_ref for pol in pols.mapped('order_id')),
            'move_ids_without_package': [ (0, 0, {
                    'name': pol.product_id.name,
                    'product_id': pol.product_id.id,
                    'product_uom_qty': 1.000,
                    'location_id': pol.src_location_id.id,
                    'location_dest_id': self.env.ref('stock_auto_nejma.stock_location_carrier').id,
                    'lot_ids': [(6, 0, [self.env['stock.lot'].search([('name', '=', pol.vin_number)], limit=1).id])]
                }) for pol in pols]
        })

        picking_push = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
            'location_id': self.env.ref('stock_auto_nejma.stock_location_carrier').id,
            'location_dest_id': pols[0].location_id.id,
            'origin': ','.join(pol.partner_ref for pol in pols.mapped('order_id')),
            'move_ids_without_package': [ (0, 0, {
                    'name': pol.product_id.name,
                    'product_id': pol.product_id.id,
                    'product_uom_qty': 1.000,
                    'location_id': self.env.ref('stock_auto_nejma.stock_location_carrier').id,
                    'location_dest_id': pol.location_id.id,
                    'lot_ids': [(6, 0, [self.env['stock.lot'].search([('name', '=', pol.vin_number)], limit=1).id])],
                    'date': fields.Datetime.now() + relativedelta(day=pols[0].location_id.sla)
                }) for pol in pols]
        })

        #picking_push.scheduled_date = picking_pull.scheduled_date + relativedelta(day=pols[0].location_id.sla)
        for pol in pols:
            pol.internal_picking_ids = [(6, 0, [picking_pull.id, picking_push.id])]
        self.status = 'confirmed'

    def action_display_invoice(self):
        result = self.env["ir.actions.actions"]._for_xml_id('account.action_move_in_invoice_type')
        res = self.env.ref('account.view_move_form', False)
        form_view = [(res and res.id or False, 'form')]
        result['views'] = form_view
        related_invoice = self.env['account.move'].search([('ref', '=', self.invoice_number)], limit=1)
        if not related_invoice:
            raise UserError(_("La facture avec la référence %s n'existe pas dans le système",self.invoice_number))
        result['res_id'] = related_invoice.id
        result['domain'] = [('id', '=', related_invoice.id)]
        return result
    
    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        self.ensure_one()
        values = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        if self.vin_number:
            lot_id = self.env['stock.lot'].create({
                'name': self.vin_number,
                'product_id': self.product_id.id,
            })
            values ['lot_ids'] = [(4, lot_id.id)]
        return values

    def _create_stock_moves(self, picking):
        values = []
        for line in self.filtered(lambda l: not l.display_type and l.received):
            print ('I m here', line)
            for val in line._prepare_stock_moves(picking):
                values.append(val)
            line.move_dest_ids.created_purchase_line_ids = [Command.clear()]

        return self.env['stock.move'].create(values)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = "Ordre de transit"

    state = fields.Selection([
        ('draft', 'Nouveau'),
        ('sent', 'Sent'),
        ('to approve', 'To Approve'),
        ('notified', 'Notifié'),
        ('bad', 'BAD'),
        ('payment_ticket', 'Ticket de paiement'),
        ('payment_received', 'Reçu de paiement'),
        ('purchase', 'Dédouané'),
        ('recepted', 'Réceptionné'),
        ('deliver_to_carrier', 'Remise au transporteur'),
        ('closed', 'Clôturé'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    arrival_doc_id = fields.Many2one(comodel_name='documents.document', string='Arrivage')
    type_ot = fields.Selection([
        ('normal', 'Normal'),
        ('premium', 'Premium')], string='Type de l\'ordre de transit')
    boat_name = fields.Many2one(string='Nom du bateau', comodel_name='delivery.carrier')
    goods_description = fields.Char(string='Désignation de la marchandise')
    other_information = fields.Selection([
        ('0', 'Mise à la consommation'),
        ('1', 'Régime économique'),
        ('2', 'Investissement d’envergure'),
        ('3', 'Franchise')], string='Renseignements patrticuliers')

    attachment_invoice = fields.Binary(string='Facture commerciale')
    attachment_payment = fields.Binary(string='Reçu de paiement')
    attachment_ml = fields.Binary(string='Main levée')
    attachment_bad = fields.Binary(string='BAD')
    vehicle_count = fields.Integer(string='# Véhicule', compute='_compute_vehicle_count')
    invoices_count = fields.Integer(string='# Factures', compute='_compute_vehicle_count')
    dispatched_count = fields.Char(string='# Remise TRS', compute='_compute_vehicle_count')
    processing_deadline = fields.Date(string='Echéance de traitement')
    delivered = fields.Boolean(string="Remis au transporteur", compute='_is_delivered', store=True, default=False)

    @api.depends('order_line', 'order_line.delivered')
    def _is_delivered(self):
        for po in self:
            if any(pol.delivered for pol in po.order_line) and po.state != 'deliver_to_carrier':
                po.state = 'deliver_to_carrier'
            if all(pol.delivered for pol in po.order_line):
                po.delivered = True

    @api.depends('order_line')
    def _compute_vehicle_count(self):
        for po in self:
            invoices_count = 0
            po.vehicle_count = len(po.order_line)
            for pol in po.order_line:
                if pol.attachment_invoice or self.env['account.move'].search([('ref', '=', pol.invoice_number)]):
                    invoices_count = invoices_count + 1
            po.invoices_count = invoices_count
            po.dispatched_count = str(len(po.order_line.filtered(lambda l: l.status == 'confirmed'))) + '/' + str(len(po.order_line))

    def action_view_vehicle(self):
        result = self.env["ir.actions.actions"]._for_xml_id('purchase_auto_nejma.action_purchase_order_line_view')
        result['domain'] = [('id', 'in', self.order_line.ids)]
        return result

    def action_notify_stage(self):
        for record in self:
            mail_template = self.env.ref('purchase_auto_nejma.transitaire_new_notified')
            mail_template.send_mail(record.id, force_send=True)
            record.state = 'notified'

    def action_to_send(self):
        for record in self:
            record.state = 'sent'

    def action_bad_stage(self):
        for record in self:
            if not record.attachment_bad:
                raise ValidationError("Merci de scanner et joindre le BAD")
            record.state = 'bad'

    def action_payment_ticket(self):
        for record in self:
            record.state = 'payment_ticket'
            mail_template = self.env.ref('purchase_auto_nejma.autonejma_recepted_ticket')
            mail_template.send_mail(record.id, force_send=True)


    def action_payment_received(self):
        for record in self:
            if not record.attachment_payment:
                raise ValidationError("Merci de scanner et joindre le ticket de paiement")
            record.state = 'payment_received'
            mail_template = self.env.ref('purchase_auto_nejma.transitaire_ticket_payed')
            mail_template.send_mail(record.id, force_send=True)

    '''def action_reception_stage(self):
        for record in self:
            if not record.attachment_ml:
                raise ValidationError("Merci de scanner et joindre le ticket de paiement")
            record.state = 'purchase'
            mail_template = self.env.ref('purchase_auto_nejma.autonejma_dedouaned')
            mail_template.send_mail(record.id, force_send=True)'''

    def action_deliver_to_carrier(self):
        for record in self:
            record.state = 'deliver_to_carrier'
            mail_template = self.env.ref('purchase_auto_nejma.autonejma_deliver_to_carrier')
            mail_template.send_mail(record.id, force_send=True)

    def action_closed(self):
        for record in self:
            record.state = 'closed'
            mail_template = self.env.ref('purchase_auto_nejma.autonejma_closed')
            mail_template.send_mail(record.id, force_send=True)

    def button_confirm(self):
        for order in self:
            if order.state != 'payment_received':
                print ('Hello')
                continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    @api.depends('partner_ref')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} ({record.partner_ref})"