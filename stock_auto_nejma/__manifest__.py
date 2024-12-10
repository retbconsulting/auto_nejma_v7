# Copyright 2022 Eezee-IT (<http://www.eezee-it.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "Stock Auto Nejma",
    "version": "17.0.0.0.0",
    "author": "Eezee-It",
    "website": "http://www.eezee-it.com",
    "category": "Eezee-It",
    "license": "LGPL-3",
    "depends": [
        "stock",
        "purchase_stock",
        "core_auto_nejma",
        "delivery"
    ],
    "data": [
        'views/stock_picking_view.xml',
        'views/delivery_carrier_view.xml',
        'data/stock_data.xml'
    ],
    "installable": True,
}
