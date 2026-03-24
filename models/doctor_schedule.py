from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HospitalDoctorSchedule(models.Model):
    _name = "hospital.doctor.schedule"
    _description = "Doctor Weekly Schedule"
    _rec_name = "doctor_id"
    _order = "doctor_id, weekday_number"

    doctor_id = fields.Many2one(
        "hospital.doctor",
        string="Doctor",
        required=True,
        ondelete="cascade"
    )

    weekday = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ], required=True, string="Day")

    weekday_number = fields.Integer(
        string="Day Number",
        compute="_compute_weekday_number",
        store=True
    )

    start_time = fields.Float(
        string="Start Time",
        required=True,
        help="Use 24-hour format: 9.0 = 9:00 AM, 14.5 = 2:30 PM"
    )

    end_time = fields.Float(
        string="End Time",
        required=True,
        help="Use 24-hour format: 17.0 = 5:00 PM, 20.5 = 8:30 PM"
    )

    slot_duration = fields.Integer(
        string="Slot Duration (Minutes)",
        default=20,
        required=True
    )

    is_available = fields.Boolean(
        string="Available",
        default=True,
        help="Uncheck to mark doctor as unavailable on this day"
    )

    time_display = fields.Char(
        string="Working Hours",
        compute="_compute_time_display"
    )

    @api.depends('weekday')
    def _compute_weekday_number(self):
        """Compute weekday number for sorting"""
        weekday_map = {
            'monday': 1,
            'tuesday': 2,
            'wednesday': 3,
            'thursday': 4,
            'friday': 5,
            'saturday': 6,
            'sunday': 7
        }
        for rec in self:
            rec.weekday_number = weekday_map.get(rec.weekday, 0)

    @api.depends('start_time', 'end_time')
    def _compute_time_display(self):
        """Display time in able format"""
        for rec in self:
            if rec.start_time and rec.end_time:
                start_h = int(rec.start_time)
                start_m = int((rec.start_time - start_h) * 60)
                end_h = int(rec.end_time)
                end_m = int((rec.end_time - end_h) * 60)

                # Convert to AM/PM
                start_period = "AM" if start_h < 12 else "PM"
                end_period = "AM" if end_h < 12 else "PM"

                start_h_12 = start_h if start_h <= 12 else start_h - 12
                end_h_12 = end_h if end_h <= 12 else end_h - 12

                if start_h_12 == 0:
                    start_h_12 = 12
                if end_h_12 == 0:
                    end_h_12 = 12

                rec.time_display = f"{start_h_12:02d}:{start_m:02d} {start_period} - {end_h_12:02d}:{end_m:02d} {end_period}"
            else:
                rec.time_display = ""

    _sql_constraints = [
        (
            'unique_doctor_day',
            'unique(doctor_id, weekday)',
            'Schedule already exists for this doctor on this day!'
        )
    ]

    @api.constrains('start_time', 'end_time')
    def _check_time(self):
        for rec in self:
            if rec.start_time >= rec.end_time:
                raise ValidationError("Start time must be before end time.")
            if rec.start_time < 0 or rec.start_time >= 24:
                raise ValidationError("Start time must be between 0 and 24 hours.")
            if rec.end_time < 0 or rec.end_time > 24:
                raise ValidationError("End time must be between 0 and 24 hours.")

    @api.constrains('slot_duration')
    def _check_slot_duration(self):
        for rec in self:
            if rec.slot_duration <= 0:
                raise ValidationError("Slot duration must be greater than 0.")
            if rec.slot_duration > 240:
                raise ValidationError("Slot duration cannot exceed 240 minutes (4 hours).")

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.doctor_id.name} - {rec.weekday.title()}"
            if not rec.is_available:
                name += " (Unavailable)"
            result.append((rec.id, name))
        return result