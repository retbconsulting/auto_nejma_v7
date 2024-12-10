from odoo import fields, models, api


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def send_notification(self):
        for rec in self:
            quants = self.env['stock.quant'].search([('id', 'in', self.env.context.get('active_ids', []))])
            mail_template = self.env.ref('purchase_auto_nejma.mail_notify_sinistre')

            mail_template.send_mail(rec.id, force_send=True)
            print ('Hello')
