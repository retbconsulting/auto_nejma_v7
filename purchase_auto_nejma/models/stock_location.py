from odoo import fields, models, api


class StockLocation(models.Model):
    _inherit = "stock.location"

    sla = fields.Integer(string="Lead time après PDI")
