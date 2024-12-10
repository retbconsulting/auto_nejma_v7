# Copyright 2022 Eezee-IT (<http://www.eezee-it.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "Custom purchase",
    "version": "17.0.0.0.0",
    "author": "Eezee-It",
    "website": "http://www.eezee-it.com",
    "category": "Eezee-It",
    "license": "LGPL-3",
    "depends": [
        "purchase",
        "documents",
        "delivery",
        "maintenance",
        "quality_control",
        "repair",
        "stock_auto_nejma"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_order_view.xml",
        "views/purchase_order_line_view.xml",
        "views/documents_view.xml",
        "views/stock_location_view.xml",
        "views/stock_picking_view.xml",
        "wizard/wiz_import_ot.xml",
        "wizard/quality_check_wizard_view.xml",
        "wizard/stock_quant_relocate_view.xml",
        "views/stock_quant_view.xml",
        "data/mail_template_data.xml",
        "data/res_partner_data.xml"
    ],
    "installable": True,
}
