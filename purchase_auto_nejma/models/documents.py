from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
import io
import re
from datetime import datetime, timedelta
try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

class Documents(models.Model):
    _inherit = "documents.document"

    ot_already_created = fields.Boolean(compute='_ots_already_created', store=True)
    order_ids = fields.One2many(comodel_name='purchase.order', inverse_name='arrival_doc_id', string='OTs')
    vehicle_number = fields.Integer(string='# Véhicule', compute='_compute_vehicle_ots_number')
    ots_number = fields.Integer(string="# OT", compute='_compute_vehicle_ots_number')
    attachment_packing_list = fields.Binary(string='Liste de colisage')
    attachment_origin_certificate = fields.Binary(string="Certificat d'origine")
    attachment_bill_lading = fields.Binary(string='Bill of lading')
    attachment_receipt_bulletin = fields.Binary(string='CNM')
    attachment_other = fields.Binary(string='Autres')
    arrival_date = fields.Date(string="Date d'arrivage", required=True)
    missing_docs = fields.Char(compute='_get_missing_docs', store=True, string="Documents attachés")

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Le champ nom devra être unique!')
    ]

    @api.depends('attachment_packing_list', 'attachment_origin_certificate',
                 'attachment_bill_lading', 'attachment_receipt_bulletin',
                 'attachment_other')
    def _get_missing_docs(self):
        for doc in self:
            missing_docs = []
            if doc.attachment_packing_list:
                missing_docs.append('Liste de colisage')
            if doc.attachment_origin_certificate:
                missing_docs.append("Certificat d'origine")
            if doc.attachment_bill_lading:
                missing_docs.append('Bill of lading')
            if doc.attachment_receipt_bulletin:
                missing_docs.append('Bulletin de réception')
            if doc.attachment_other:
                missing_docs.append('Autres')
            doc.missing_docs = '('+str(len(missing_docs))+'/5) ' + ', '.join(missing_docs)

    @api.depends('order_ids', 'order_ids.order_line')
    def _compute_vehicle_ots_number(self):
        for doc in self:
            doc.ots_number = len(doc.order_ids)
            doc.vehicle_number = len(doc.order_ids.order_line)

    @api.depends('order_ids')
    def _ots_already_created(self):
        for doc in self:
            if len(doc.order_ids):
                doc.ot_already_created = True
            else:
                doc.ot_already_created = False

    def action_display_ot(self):
        result = self.env["ir.actions.actions"]._for_xml_id('purchase.purchase_rfq')
        result['domain'] = [('id', 'in', self.order_ids.ids)]
        return result

    def action_display_arrivage(self):
        result = self.env["ir.actions.actions"]._for_xml_id('purchase_auto_nejma.document_action_auto_nejma')
        res = self.env.ref('purchase_auto_nejma.document_view_form_auto_nejma', False)
        form_view = [(res and res.id or False, 'form')]
        result['views'] = form_view
        result['res_id'] = self.id
        result['domain'] = [('id', '=', self.id)]
        return result

    def action_generate_ot(self):
        for record in self:
            document_name = record.name
            record.name = document_name.replace('.xlsx', '')
            if not record.attachment_id:
                raise ValidationError(_("No attachment found for this purchase order."))

            try:
                mimetype = record.attachment_id.mimetype
                if not mimetype or not (mimetype.startswith(
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') or mimetype.startswith(
                        'application/vnd.ms-excel')):
                    raise ValidationError(
                        _("Format de fichier non pris en charge. Seuls les fichiers Excel sont supportés."))

                book = xlrd.open_workbook(file_contents=record.raw or b'')
                print(book)
                sheet_names = book.sheet_names()
                if 'OT' not in sheet_names:
                    raise ValidationError('Aucune feuille portant le nom OT.')
                for sheet in book.sheets():
                    self._read_xls_book(book,sheet)
            except FileNotFoundError:
                raise ValidationError('An unexpected error occurred. Please try again.')
            except xlrd.biffh.XLRDError:
                raise ValidationError('Only excel files are supported.')

    def _read_xls_book(self, book, sheet):
        if sheet.name == 'OT':
            PurchaseOrder = self.env['purchase.order']
            PurchaseOrderLine = self.env['purchase.order.line']
            rows = []
            pattern = "OT N°"
            transit_orders = []
            nrow = 0
            for rowx, row in enumerate(map(sheet.row, range(sheet.nrows)), 1):
                #values = []
                nrow += 1
                index = 0
                if re.search(pattern, str(row[2].value)):
                    cell_value = row[2].value
                    if transit_orders:
                        transit_orders[-1]['end_index'] = nrow - 2
                    #transit_orders.append(cell_value.replace(' :', ''))
                    transit_orders.append({'name' : cell_value,
                                           'start_index': nrow+2,
                                           'end_index': sheet.nrows+1})

            if transit_orders:
                transit_orders[-1]['end_index'] = transit_orders[-1]['end_index'] - 1
                for transit_order in transit_orders:
                    print (re.findall(r'\d{2}\.\d{2}\.\d{4}', transit_order['name']))
                    processing_deadline = datetime.strptime(re.findall(r'\d{2}\.\d{2}\.\d{4}', transit_order['name'])[0], "%d.%m.%Y")
                    order = PurchaseOrder.create({'partner_id': self.env.ref('purchase_auto_nejma.mb_partner').id,
                                          'partner_ref': transit_order['name'].replace(' :', ''),
                                            'type_ot': 'normal',
                                                  'processing_deadline':processing_deadline + timedelta(days=5),
                                          'incoterm_id': self.env['account.incoterms'].search([('code', '=', 'CFR')], limit=1).id,
                                          'picking_type_id': self.env.ref('stock.picking_type_in').id,
                                          'arrival_doc_id': self.id})
                    for row_idx in range(transit_order['start_index']-1, transit_order['end_index']):
                        row = sheet.row_values(row_idx)
                        #product = self.env['product.template'].search([('name', '=', row[2])], limit=1).product_variant_ids[0].id
                        product = self.env['product.template'].search([('name', '=', row[2])], limit=1)
                        if not product:
                            raise ValidationError(f"Le produit '{row[2]}' n'existe pas dans la base de données, merci de le créer.")
                        product_variant = product.product_variant_ids[0].id
                        
                        xyz = xlrd.xldate_as_tuple(row[13], book.datemode)
                        PurchaseOrderLine.create({'name': row[2],
                                                  'product_id': product_variant,
                                                  'vsb_number': int(row[1]),
                                                  'order_number': str(row[3]),
                                                  'vin_number': str(row[4]),
                                                  'engine_number': str(row[5]),
                                                  'bm': int(row[6]),
                                                  'length': int(row[7]),
                                                  'width': int(row[8]),
                                                  'height': int(row[9]),
                                                  'weight': int(row[10]),
                                                  'fuel': 'diesel' if row[11]=='Diesel' else 'essence-electrique',
                                                  'traking_number': str(row[12]),
                                                  #'date': xlrd.xldate_as_tuple(row[13], book.datemode),
                                                  'invoice_number': str(row[15]),
                                                  #'invoice_date': xlrd.xldate_as_tuple(row[16], book.datemode),
                                                  'order_id': order.id})

                    self.arrival_date = processing_deadline
            else:
                raise ValidationError("Aucune OT n'a été détecté dans le fichier.")


            print (transit_orders)
            #print(rows[0])
            return rows


