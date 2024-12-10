from odoo import fields, models

class WorksheetTemplate(models.Model):
    _inherit = 'worksheet.template'

    product_categ = fields.Many2many(
        'product.category',
        string='Product Categories'
    )
