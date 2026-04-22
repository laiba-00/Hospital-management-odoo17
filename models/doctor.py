from odoo import fields, models, api


class HospitalDoctor(models.Model):
    _name = "hospital.doctor"
    _description = "Doctor"

    name = fields.Char(string="Doctor Name", required=True)
    department = fields.Char(string="Department")

    fee_10min = fields.Float(
        string="10 Min Fee (Rs.)",
        digits=(10, 2),
        default=0.0,
        help="Fee for a 10-minute quick consultation"
    )
    fee_20min = fields.Float(
        string="20 Min Fee (Rs.)",
        digits=(10, 2),
        default=0.0,
        help="Fee for a 20-minute standard consultation"
    )
    fee_40min = fields.Float(
        string="40 Min Fee (Rs.)",
        digits=(10, 2),
        default=0.0,
        help="Fee for a 40-minute detailed examination"
    )

    # Schedule days link
    schedule_ids = fields.One2many(
        'hospital.doctor.schedule',
        'doctor_id',
        string="Schedules"
    )

    # Available days computed
    available_days = fields.Char(
        string="Available Days",
        compute="_compute_available_days",
    )

    @api.depends('schedule_ids', 'schedule_ids.is_available', 'schedule_ids.weekday')
    def _compute_available_days(self):
        for rec in self:
            days = rec.schedule_ids.filtered(
                lambda s: s.is_available
            ).mapped('weekday')
            day_labels = {
                'monday': 'Mon', 'tuesday': 'Tue',
                'wednesday': 'Wed', 'thursday': 'Thu',
                'friday': 'Fri', 'saturday': 'Sat',
                'sunday': 'Sun'
            }
            rec.available_days = ', '.join(
                day_labels.get(d, d) for d in days
            ) if days else 'No Schedule'

    def get_fee_for_duration(self, duration_minutes):
        self.ensure_one()
        return {
            10: self.fee_10min,
            20: self.fee_20min,
            40: self.fee_40min,
        }.get(int(duration_minutes), 0.0)