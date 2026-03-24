from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AppointmentSlotWizard(models.TransientModel):
    _name = "appointment.slot.wizard"
    _description = "Choose Appointment Duration"

    appointment_id = fields.Many2one(
        "hospital.appointment",
        string="Appointment",
        required=True
    )
    doctor_id = fields.Many2one(
        "hospital.doctor",
        string="Doctor",
        required=True
    )
    date = fields.Date(
        string="Date",
        required=True
    )
    duration = fields.Selection([
        ('10', '10 Minutes - Quick Consultation'),
        ('20', '20 Minutes - Standard Consultation'),
        ('40', '40 Minutes - Detailed Consultation'),
    ], string="Appointment Duration", required=True, default='20')

    # Fee fields — read directly from doctor (no separate model needed)
    fee_10 = fields.Float(
        related='doctor_id.fee_10min',
        string="10 Min Fee (Rs.)",
        readonly=True
    )
    fee_20 = fields.Float(
        related='doctor_id.fee_20min',
        string="20 Min Fee (Rs.)",
        readonly=True
    )
    fee_40 = fields.Float(
        related='doctor_id.fee_40min',
        string="40 Min Fee (Rs.)",
        readonly=True
    )

    # Dynamically highlighted fee based on selected duration
    selected_fee = fields.Float(
        string="Your Selected Fee (Rs.)",
        compute="_compute_selected_fee",
        store=False
    )

    @api.depends('duration', 'fee_10', 'fee_20', 'fee_40')
    def _compute_selected_fee(self):
        for rec in self:
            rec.selected_fee = {
                '10': rec.fee_10,
                '20': rec.fee_20,
                '40': rec.fee_40,
            }.get(rec.duration or '20', 0.0)

    def action_show_slots(self):
        """Generate slots for selected duration and pass fee via context"""
        self.ensure_one()

        if not self.duration:
            raise ValidationError("Please select appointment duration!")

        duration_minutes = int(self.duration)
        fee = self.selected_fee

        slots = self.env['hospital.appointment.slot'].generate_slots_for_doctor(
            self.doctor_id.id,
            self.date,
            duration_minutes=duration_minutes
        )

        if not slots:
            raise ValidationError(
                f"No available {duration_minutes}-minute slots for "
                f"Dr. {self.doctor_id.name} on {self.date}!"
            )

        return {
            'type': 'ir.actions.act_window',
            'name': f'Available {duration_minutes}-Min Slots — Rs. {fee:,.0f}',
            'res_model': 'hospital.appointment.slot',
            'view_mode': 'kanban,tree',
            'domain': [('id', 'in', slots.ids)],
            'context': {
                'default_doctor_id': self.doctor_id.id,
                'default_date': self.date,
                'appointment_id': self.appointment_id.id,
                'selected_fee': fee,                   # ← passed to slot action
                'selected_duration': duration_minutes,
            },
            'target': 'new',
        }