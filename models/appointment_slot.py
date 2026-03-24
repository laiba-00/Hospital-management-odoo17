from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HospitalAppointmentSlot(models.TransientModel):
    _name = "hospital.appointment.slot"
    _description = "Appointment Slot (Transient)"
    _order = "date, start_time"

    doctor_id = fields.Many2one(
        "hospital.doctor",
        string="Doctor",
        required=True
    )
    date = fields.Date(
        string="Date",
        required=True
    )
    start_time = fields.Float(
        string="Start Time",
        required=True,
        help="Format: 9.5 means 9:30 AM"
    )
    end_time = fields.Float(
        string="End Time",
        required=True,
        help="Format: 10.0 means 10:00 AM"
    )
    is_booked = fields.Boolean(
        string="Booked",
        compute="_compute_is_booked",
        default=False
    )
    appointment_id = fields.Many2one(
        "hospital.appointment",
        string="Appointment",
        compute="_compute_is_booked"
    )
    time_display = fields.Char(
        string="Time",
        compute="_compute_time_display"
    )

    # ─── Computed Fields ──────────────────────────────────────────────────────

    @api.depends('start_time', 'end_time')
    def _compute_time_display(self):
        for rec in self:
            start_h = int(rec.start_time)
            start_m = int((rec.start_time - start_h) * 60)
            end_h = int(rec.end_time)
            end_m = int((rec.end_time - end_h) * 60)
            rec.time_display = f"{start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"

    @api.depends('doctor_id', 'date', 'start_time', 'end_time')
    def _compute_is_booked(self):
        """
        A slot is booked if any confirmed/draft appointment overlaps with it.
        Overlap: (apt_start < slot_end) AND (apt_end > slot_start)
        """
        for rec in self:
            if rec.doctor_id and rec.date and rec.start_time and rec.end_time:
                overlapping = self.env['hospital.appointment'].search([
                    ('doctor_id', '=', rec.doctor_id.id),
                    ('date_appointment', '=', rec.date),
                    ('slot_start_time', '<', rec.end_time),
                    ('slot_end_time', '>', rec.start_time),
                    ('state', '!=', 'cancelled'),
                ])
                rec.is_booked = bool(overlapping)
                rec.appointment_id = overlapping[0].id if overlapping else False
            else:
                rec.is_booked = False
                rec.appointment_id = False

    # ─── Name Get ─────────────────────────────────────────────────────────────

    def name_get(self):
        result = []
        for rec in self:
            start_h = int(rec.start_time)
            start_m = int((rec.start_time - start_h) * 60)
            end_h = int(rec.end_time)
            end_m = int((rec.end_time - end_h) * 60)
            name = f"{start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"
            result.append((rec.id, name))
        return result

    # ─── Slot Generation ──────────────────────────────────────────────────────

    @api.model
    def generate_slots_for_doctor(self, doctor_id, date, duration_minutes=None):
        """
        Dynamically generate time slots based on doctor's schedule.

        Args:
            doctor_id: ID of the doctor
            date: Appointment date (string or Date)
            duration_minutes: 10, 20, or 40. If None, uses schedule default.

        Returns:
            Recordset of transient slot records
        """
        date_obj = fields.Date.from_string(date)
        weekday = date_obj.strftime('%A').lower()

        schedules = self.env['hospital.doctor.schedule'].search([
            ('doctor_id', '=', doctor_id),
            ('weekday', '=', weekday)
        ])

        if not schedules:
            return self.browse()  # Empty recordset

        slot_records = self.browse()

        for schedule in schedules:
            start = schedule.start_time
            end = schedule.end_time

            duration = (duration_minutes / 60.0) if duration_minutes \
                else (schedule.slot_duration / 60.0)

            current = start
            while current < end:
                slot_end = current + duration
                if slot_end <= end:
                    slot = self.create({
                        'doctor_id': doctor_id,
                        'date': date,
                        'start_time': current,
                        'end_time': slot_end,
                    })
                    slot_records |= slot
                current += duration

        return slot_records

    # ─── Actions ──────────────────────────────────────────────────────────────

    def action_select_slot(self):
        """
        Select this slot from kanban view.
        Saves slot times AND consultation fee to the appointment.
        Fee comes from context set by the wizard.
        """
        self.ensure_one()

        if self.is_booked:
            raise ValidationError("This slot is already booked!")

        appointment_id = self.env.context.get('appointment_id')
        selected_fee = self.env.context.get('selected_fee', 0.0)  # ← from wizard

        if appointment_id:
            appointment = self.env['hospital.appointment'].browse(appointment_id)
            appointment.write({
                'slot_start_time': self.start_time,
                'slot_end_time': self.end_time,
                'consultation_fee': selected_fee,   # ← saved to appointment
            })
            return {'type': 'ir.actions.act_window_close'}

        return True

    def action_book_slot(self):
        """Book slot and open new appointment form"""
        self.ensure_one()

        if self.is_booked:
            raise ValidationError("This slot is already booked!")

        return {
            'type': 'ir.actions.act_window',
            'name': 'New Appointment',
            'res_model': 'hospital.appointment',
            'view_mode': 'form',
            'context': {
                'default_doctor_id': self.doctor_id.id,
                'default_date_appointment': self.date,
                'default_slot_start_time': self.start_time,
                'default_slot_end_time': self.end_time,
            },
            'target': 'current',
        }