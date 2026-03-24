from odoo import fields, models, api


class HospitalDoctor(models.Model):
    _name = "hospital.doctor"
    _description = "Doctor"

    name = fields.Char(string="Doctor Name", required=True)
    department = fields.Char(string="Department")

    # Consultation Fees per duration
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
        help="Fee for a 40-minute detailed consultation"
    )

    def get_fee_for_duration(self, duration_minutes):
        """Return fee based on duration. Called from wizard."""
        self.ensure_one()
        return {
            10: self.fee_10min,
            20: self.fee_20min,
            40: self.fee_40min,
        }.get(int(duration_minutes), 0.0)