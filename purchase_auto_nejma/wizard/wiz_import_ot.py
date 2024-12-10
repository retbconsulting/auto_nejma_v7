from odoo import _, fields, models
from odoo.exceptions import ValidationError
import openpyxl
import xlrd


class WizImportOt(models.TransientModel):
    _name = "wiz.import.ot"

    file_id = fields.Binary(required=True)
    filename = fields.Char()

    def action_import_ot(self):
        for record in self:
            if not record.filename.endswith(('.xlsx', '.xls')):
                raise ValidationError(
                    _("Invalid file format. Only Excel files (.xlsx, .xls) are allowed."))
            try:
                wb = xlrd.open_workbook(filename=record.filename)
                sheet = wb.active

                data_start_row = 2

                for row in sheet.iter_rows(min_row=data_start_row):
                    data_dict = {}
                    cell_idx = 0

                    # Extract data from specific columns (adjust column indices as needed)
                    # Assuming VS8 No. and OT N (06.06.2024/...) are not relevant for import
                    """if cell_idx >= 3:  # Skip the first 2 columns (VS8 No. and OT N)
                        field_name = {
                            3: 'model',  # Assuming 'model' is a field in your Odoo model
                            4: 'type',  # Assuming 'type' is a field in your Odoo model
                            5: 'order_no',  # Assuming 'order_no' is a field in your Odoo model
                        }.get(cell_idx)
                        if field_name:
                            data_dict[field_name] = cell.value
                        cell_idx += 1

                    # Create a new record in the Odoo model with the extracted data
                    self.env['your.odoo.model.name'].create(data_dict)"""

                return {
                    'type': 'pop',
                    'title': 'Import Successful',
                    'message': 'Data imported successfully from the Excel file.',
                }

            except Exception as e:
                raise ValidationError(_(f"Error importing data: {e}"))
