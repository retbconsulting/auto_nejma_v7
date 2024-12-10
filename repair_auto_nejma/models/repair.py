from odoo import fields, models, api

class StockMove(models.Model):
    _inherit = "stock.move"

    repair_line_type = fields.Selection([
        ('add', 'Accessoire'),
        ('recycle', 'Réparation')
    ], 'Type', store=True, index=True)
    repair_estimation = fields.Float(string="Estimation")

class RepairOrder(models.Model):
    _inherit = "repair.order"

    @api.depends('move_ids', 'move_ids.repair_estimation')
    def _get_total_estimation(self):
        for repair in self:
            repair.total_estimation = sum(line.repair_estimation for line in repair.move_ids)

    def _get_deadlines(self):
        for repair in self:
            repair.deadline_declaration = 0
            repair.deadline_expertise = 0
            repair.deadline_open_tec = 0
            repair.delay_open_tec = 0
            repair.delay_receipt_quotation = 0
            repair.delay_remise_expert = 0
            repair.delay_acceptance = 0
            repair.delay_cancel_indispo = 0
            repair.delay_payment = 0

    total_estimation = fields.Float(string="Total", compute='_get_total_estimation', store=True)
    date_sinistre = fields.Date(string="Date de l'arrivage/sinistre")
    src_location_id = fields.Date(string="Lieu d'anomalie")
    expert_id = fields.Many2one(comodel_name="res.partner", string="Expert")
    w18_number = fields.Char(string="Numéro w18 si applicable")
    date_order = fields.Date(string="Date de réclamation")
    date_end = fields.Date(string="Date fin travaux")
    date_declaration_insurance = fields.Date(string="Date déclaration assurance")
    deadline_declaration = fields.Integer(string="Délai déclaration", compute='_get_deadlines')
    date_expertise = fields.Date(string="Date d'expertise")
    deadline_expertise = fields.Integer(string="Délai expertise", compute='_get_deadlines')
    date_ffi_logistique = fields.Date(string="Date dépôt FFI Logistique")
    date_open_tec = fields.Date(string="Date ouverture TEC")
    deadline_open_tec = fields.Integer(string="Délai d'ouverture TEC", compute='_get_deadlines')
    delay_open_tec = fields.Integer(string="Retard d'ouverture TEC", compute='_get_deadlines')
    tec = fields.Char(string="TEC")
    date_receipt_quotation = fields.Date(string="Date réception devis")
    delay_receipt_quotation = fields.Integer(string="Délai entre demande et réception devis", compute='_get_deadlines')
    date_send_quotation_expert = fields.Date(string="Date remise devis à l'expert")
    delay_remise_expert = fields.Integer(string="Délai de remise à l'expert", compute='_get_deadlines')
    date_accord = fields.Date(string="Date accord")
    delay_acceptance = fields.Integer(string="Délai acceptation", compute='_get_deadlines')
    date_return_to_sav = fields.Date(string="Date retour véhicule par SAV")
    date_cancel_indispo = fields.Date(string="Date annulation indisponibilité")
    delay_cancel_indispo = fields.Integer(string="Délai annulation indisponibilité", compute='_get_deadlines')
    date_remise_invoice_insurance = fields.Date(string="Date de remise facture par SAV")
    state_insurance = fields.Char(string="Statut dossier assurance")
    last_notif = fields.Date(string="Date dernière relance ")
    amount_reimbursed = fields.Float(string="Montant remboursé")
    date_payment = fields.Date(string="Date règlement")
    tva = fields.Float(string="TVA")
    vetuste = fields.Char(string="Vetusté")
    limit_bdg = fields.Float(string="Plafond BDG")
    franchise = fields.Char(string="Franchise")
    delay_payment = fields.Integer(string="Délai annulation indisponibilité", compute='_get_deadlines')
    picture = fields.Binary('Image', attachment=True)