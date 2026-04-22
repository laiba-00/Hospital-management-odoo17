from odoo import fields, models, api
from odoo.exceptions import ValidationError


class HospitalAppointment(models.Model):
    _name = "hospital.appointment"
    _inherit = ["mail.thread"]
    _description = "Patient Appointment"
    _rec_name = "reference"

    reference = fields.Char(string="Reference", default="New")
    patient_id = fields.Many2one(
        "hospital.patient",
        string="Patient",
        required=True
    )
    date_appointment = fields.Date(string="Date", required=True)
    note = fields.Text(string="Note")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_consultation', 'In Consultation'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='draft', string="Status", tracking=True)

    date_of_birth = fields.Date(related="patient_id.date_of_birth", store=True)

    doctor_id = fields.Many2one(
        "hospital.doctor",
        string="Doctor",
        required=True,
    )
    department = fields.Char(
        string="Department",
        related="doctor_id.department",
        store=True,
        readonly=True
    )

    slot_start_time = fields.Float(
        string="Start Time",
        help="Format: 9.5 means 9:30 AM"
    )
    slot_end_time = fields.Float(
        string="End Time",
        help="Format: 10.0 means 10:00 AM"
    )
    appointment_duration = fields.Integer(
        string="Duration (Minutes)",
        compute="_compute_appointment_duration",
        store=True,
        help="Actual appointment duration in minutes"
    )
    slot_time = fields.Char(
        string="Appointment Time",
        compute="_compute_slot_time",
        store=True
    )
    consultation_fee = fields.Float(
        string="Consultation Fee (Rs.)",
        digits=(10, 2),
        tracking=True,
        help="Auto-calculated from doctor's fee schedule based on selected slot duration."
    )
    duration_selector = fields.Many2one(
        'hospital.doctor',
        string="Slot Selector",
        store=False,
        compute="_compute_duration_selector",
    )

    @api.depends('doctor_id')
    def _compute_duration_selector(self):
        for rec in self:
            rec.duration_selector = rec.doctor_id

    # ─── Computed Fields ──────────────────────────────────────────────────────

    @api.depends('slot_start_time', 'slot_end_time')
    def _compute_slot_time(self):
        for rec in self:
            if rec.slot_start_time and rec.slot_end_time:
                start_h = int(rec.slot_start_time)
                start_m = int((rec.slot_start_time - start_h) * 60)
                end_h = int(rec.slot_end_time)
                end_m = int((rec.slot_end_time - end_h) * 60)
                rec.slot_time = f"{start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"
            else:
                rec.slot_time = False

    @api.depends('slot_start_time', 'slot_end_time')
    def _compute_appointment_duration(self):
        for rec in self:
            if rec.slot_start_time and rec.slot_end_time:
                rec.appointment_duration = int(
                    (rec.slot_end_time - rec.slot_start_time) * 60
                )
            else:
                rec.appointment_duration = 0

    # ─── Onchange ─────────────────────────────────────────────────────────────

    @api.onchange('doctor_id', 'date_appointment')
    def _onchange_clear_slot(self):
        if self.slot_start_time or self.slot_end_time:
            self.slot_start_time = False
            self.slot_end_time = False
            self.consultation_fee = 0.0

    # ─── Actions ──────────────────────────────────────────────────────────────

    def action_confirm(self):
        for rec in self:
            if not rec.slot_start_time:
                raise ValidationError("Please select a time slot before confirming!")
            rec.state = "confirmed"
            template = self.env.ref('om_hospital.email_template_appointment_confirm')
            if template and rec.patient_id.email:
                template.send_mail(rec.id, force_send=True)

    def action_start_consultation(self):
        for rec in self:
            rec.state = "in_consultation"

    def action_done(self):
        for rec in self:
            rec.state = "done"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancelled"

    # ─── ORM Overrides ────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['reference'] = self.env['ir.sequence'].next_by_code('hospital.appointment')
        return super().create(vals_list)

    def write(self, vals):
        if any(key in vals for key in ['slot_start_time', 'slot_end_time']):
            for rec in self:
                if rec.state != 'draft':
                    raise ValidationError(
                        "Cannot change appointment time after confirmation! "
                        "Please cancel and create a new appointment."
                    )
        return super().write(vals)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.reference}] {rec.patient_id.display_name}"

    # ─── Constraints ──────────────────────────────────────────────────────────

    @api.constrains('doctor_id', 'date_appointment', 'slot_start_time', 'state')
    def _check_slot_availability(self):
        for rec in self:
            if rec.slot_start_time and rec.state != 'cancelled':
                existing = self.search([
                    ('doctor_id', '=', rec.doctor_id.id),
                    ('date_appointment', '=', rec.date_appointment),
                    ('slot_start_time', '=', rec.slot_start_time),
                    ('state', '!=', 'cancelled'),
                    ('id', '!=', rec.id)
                ])
                if existing:
                    raise ValidationError(
                        f"This time slot is already booked for {rec.doctor_id.name}!"
                    )

    def action_auto_cancel_appointments(self):
        today = fields.Date.today()
        past_appointments = self.search([
            ('state', '=', 'draft'),
            ('date_appointment', '<', today)
        ])
        if past_appointments:
            past_appointments.write({'state': 'cancelled'})

    @api.constrains('date_appointment')
    def _check_appointment_date(self):
        for rec in self:
            if rec.date_appointment < fields.Date.today():
                raise ValidationError(
                    "Appointment date cannot be in the past! "
                    "Please select today or a future date."
                )

    @api.onchange('date_appointment')
    def _onchange_date_appointment(self):
        if self.date_appointment and \
                self.date_appointment < fields.Date.today():
            return {
                'warning': {
                    'title': 'Invalid Date!',
                    'message': 'Please select today or future date!'
                }
            }

    # ─── OWL Slot Widget Methods ───────────────────────────────────────────────

    @api.model
    def get_doctor_fees(self, doctor_id):
        doctor = self.env['hospital.doctor'].browse(doctor_id)
        return {
            10: doctor.fee_10min,
            20: doctor.fee_20min,
            40: doctor.fee_40min,
        }

    @api.model
    def get_available_slots(self, appointment_id, doctor_id, date, duration_minutes):
        from odoo import fields as odoo_fields
        date_obj = odoo_fields.Date.from_string(date)
        weekday = date_obj.strftime('%A').lower()

        schedules = self.env['hospital.doctor.schedule'].search([
            ('doctor_id', '=', doctor_id),
            ('weekday', '=', weekday)
        ])

        if not schedules:
            return []

        duration_hours = duration_minutes / 60.0
        result = []

        for schedule in schedules:
            current = schedule.start_time
            while current < schedule.end_time:
                slot_end = current + duration_hours
                if slot_end > schedule.end_time:
                    break

                overlapping = self.env['hospital.appointment'].search([
                    ('doctor_id', '=', doctor_id),
                    ('date_appointment', '=', date),
                    ('slot_start_time', '<', slot_end),
                    ('slot_end_time', '>', current),
                    ('state', '!=', 'cancelled'),
                ])

                if appointment_id:
                    overlapping = overlapping.filtered(
                        lambda r: r.id != appointment_id
                    )

                start_h = int(current)
                start_m = int((current - start_h) * 60)
                end_h = int(slot_end)
                end_m = int((slot_end - end_h) * 60)

                result.append({
                    'start_time': current,
                    'end_time': slot_end,
                    'is_booked': bool(overlapping),
                    'time_display': f"{start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}",
                })

                current += duration_hours

        return result

    def save_slot_from_widget(self, start_time, end_time, fee):
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError("Cannot change slot after confirmation!")
        self.write({
            'slot_start_time': start_time,
            'slot_end_time': end_time,
            'consultation_fee': fee,
        })
        return True