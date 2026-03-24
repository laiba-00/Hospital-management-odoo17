from odoo import http
from odoo.http import request
from datetime import datetime
import json


class HospitalAPI(http.Controller):
    def _json_response(self, data, status=200):
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')],
            status=status
        )


    # ── Login ────────────────────────────────────
    @http.route(
        '/api/auth/login',
        type='http',
        auth='none',
        methods=['POST'],
        csrf=False
    )
    def api_login(self, **kwargs):
        try:
            data = json.loads(
                request.httprequest.data.decode('utf-8')
            )
            email = data.get('email')
            password = data.get('password')

            uid = request.session.authenticate(
                request.db, email, password
            )

            if not uid:
                return self._json_response(
                    {'status': 'error',
                     'message': 'Invalid email or password'},
                    status=401
                )

            user = request.env(user=uid)[
                'res.users'
            ].browse(uid)

            patient = request.env(user=1)[
                'hospital.patient'
            ].search([
                ('email', '=', user.email)
            ], limit=1)

            return self._json_response({
                'status': 'success',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'patient_id': patient.id if patient else False
                }
            })

        except Exception as e:
            return self._json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    # ── Register ─────────────────────────────────
    @http.route(
        '/api/auth/register',
        type='http',
        auth='none',
        methods=['POST'],
        csrf=False
    )
    def api_register(self, **kwargs):
        try:
            data = json.loads(
                request.httprequest.data.decode('utf-8')
            )
            name = data.get('name')
            email = data.get('email')
            password = data.get('password')
            phone = data.get('phone', '')
            gender = data.get('gender', '')

            existing = request.env(user=1)[
                'res.users'
            ].search([
                ('login', '=', email)
            ], limit=1)

            if existing:
                return self._json_response(
                    {'status': 'error',
                     'message': 'Email already registered'},
                    status=400
                )

            request.env(user=1)['res.users'].create({
                'name': name,
                'login': email,
                'email': email,
                'password': password,
                'groups_id': [(6, 0, [
                    request.env.ref(
                        'base.group_portal'
                    ).id
                ])]
            })

            patient = request.env(user=1)[
                'hospital.patient'
            ].create({
                'name': name,
                'email': email,
                'phone': phone,
                'gender': gender,
            })

            return self._json_response({
                'status': 'success',
                'message': 'Account created successfully',
                'patient_id': patient.id
            })

        except Exception as e:
            return self._json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )


    # ── All Doctors ──────────────────────────────
    @http.route(
        '/api/doctors',
        type='http',
        auth='none',
        methods=['GET'],
        csrf=False
    )
    def api_get_doctors(self, **kwargs):
        try:
            doctors = request.env(user=1)[
                'hospital.doctor'
            ].search([])

            result = []
            for doctor in doctors:
                result.append({
                    'id': doctor.id,
                    'name': doctor.name,
                    'department': doctor.department,
                    'fee_10min': doctor.fee_10min,
                    'fee_20min': doctor.fee_20min,
                    'fee_40min': doctor.fee_40min,
                })

            return self._json_response({
                'status': 'success',
                'doctors': result
            })

        except Exception as e:
            return self._json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    # ── Single Doctor ────────────────────────────
    @http.route(
        '/api/doctors/<int:doctor_id>',
        type='http',
        auth='none',
        methods=['GET'],
        csrf=False
    )
    def api_get_doctor(self, doctor_id, **kwargs):
        try:
            doctor = request.env(user=1)[
                'hospital.doctor'
            ].browse(doctor_id)

            if not doctor.exists():
                return self._json_response(
                    {'status': 'error',
                     'message': 'Doctor not found'},
                    status=404
                )

            return self._json_response({
                'status': 'success',
                'doctor': {
                    'id': doctor.id,
                    'name': doctor.name,
                    'department': doctor.department,
                    'fee_10min': doctor.fee_10min,
                    'fee_20min': doctor.fee_20min,
                    'fee_40min': doctor.fee_40min,
                }
            })

        except Exception as e:
            return self._json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    # ── Doctor Schedule ──────────────────────────
    @http.route(
        '/api/doctors/<int:doctor_id>/schedule',
        type='http',
        auth='none',
        methods=['GET'],
        csrf=False
    )
    def api_get_doctor_schedule(self,
                                doctor_id, **kwargs):
        try:
            schedules = request.env(user=1)[
                'hospital.doctor.schedule'
            ].search([
                ('doctor_id', '=', doctor_id),
                ('is_available', '=', True)
            ])

            result = []
            for s in schedules:
                result.append({
                    'id': s.id,
                    'weekday': s.weekday,
                    'start_time': s.start_time,
                    'end_time': s.end_time,
                    'slot_duration': s.slot_duration,
                    'time_display': s.time_display,
                })

            return self._json_response({
                'status': 'success',
                'schedule': result
            })

        except Exception as e:
            return self._json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    @http.route(
        '/api/slots',
        type='http',
        auth='none',
        methods=['GET'],
        csrf=False
    )
    def api_get_slots(self, **kwargs):
        try:
            # Validation pehle
            doctor_id = kwargs.get('doctor_id')
            date = kwargs.get('date')
            duration = kwargs.get('duration', '20')

            if not doctor_id:
                return self._json_response(
                    {'status': 'error',
                     'message': 'doctor_id is required'},
                    status=400
                )
            if not date:
                return self._json_response(
                    {'status': 'error',
                     'message': 'date is required'},
                    status=400
                )

            doctor_id = int(doctor_id)
            duration = int(duration)

            date_obj = datetime.strptime(date, '%Y-%m-%d')
            weekday = date_obj.strftime('%A').lower()

            schedule = request.env(user=1)[
                'hospital.doctor.schedule'
            ].search([
                ('doctor_id', '=', doctor_id),
                ('weekday', '=', weekday),
                ('is_available', '=', True)
            ], limit=1)

            if not schedule:
                return self._json_response({
                    'status': 'success',
                    'slots': [],
                    'message': 'Doctor not available on this day'
                })

            booked = request.env(user=1)[
                'hospital.appointment'
            ].search([
                ('doctor_id', '=', doctor_id),
                ('date_appointment', '=', date),
                ('state', '!=', 'cancelled')
            ])
            booked_times = [b.slot_start_time for b in booked]

            slots = []
            current = schedule.start_time
            dur_hours = duration / 60

            while current + dur_hours <= schedule.end_time:
                if current not in booked_times:
                    h = int(current)
                    m = int((current - h) * 60)
                    end = current + dur_hours
                    eh = int(end)
                    em = int((end - eh) * 60)
                    slots.append({
                        'start': current,
                        'end': end,
                        'label': f"{h:02d}:{m:02d} - {eh:02d}:{em:02d}"
                    })
                current += dur_hours

            return self._json_response({
                'status': 'success',
                'slots': slots
            })

        except Exception as e:
            return self._json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    # ════════════════════════════════════════════
    # APPOINTMENTS APIs
    # ════════════════════════════════════════════

    # ── My Appointments ──────────────────────────
    @http.route(
        '/api/appointments',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False
    )
    def api_get_appointments(self, **kwargs):
        try:
            partner = request.env.user.partner_id
            appointments = request.env[
                'hospital.appointment'
            ].sudo().search([
                ('patient_id.email', '=', partner.email)
            ], order='date_appointment desc')

            result = []
            for apt in appointments:
                result.append({
                    'id': apt.id,
                    'reference': apt.reference,
                    'doctor': apt.doctor_id.name,
                    'department': apt.department,
                    'date': str(apt.date_appointment),
                    'slot_time': apt.slot_time or '',
                    'duration': apt.appointment_duration,
                    'fee': apt.consultation_fee,
                    'state': apt.state,
                    'note': apt.note or '',
                })

            return self._json_response({
                'status': 'success',
                'appointments': result
            })

        except Exception as e:
            return self._json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    # ── Book Appointment ─────────────────────────
    @http.route(
        '/api/appointments/book',
        type='http',
        auth='none',
        methods=['POST'],
        csrf=False
    )
    def api_book_appointment(self, **kwargs):
        try:
            data = json.loads(
                request.httprequest.data.decode('utf-8')
            )

            patient_email = data.get('patient_email')
            doctor_id = int(data.get('doctor_id'))
            date_appointment = datetime.strptime(
                data.get('date'), '%Y-%m-%d'
            ).date()
            slot_start = float(data.get('slot_start'))
            slot_end = float(data.get('slot_end'))
            fee = float(data.get('fee'))

            patient = request.env(user=1)[
                'hospital.patient'
            ].search([
                ('email', '=', patient_email)
            ], limit=1)

            if not patient:
                return self._json_response(
                    {'status': 'error',
                     'message': 'Patient not found'},
                    status=404
                )

            appointment = request.env(user=1)[
                'hospital.appointment'
            ].create({
                'patient_id': patient.id,
                'doctor_id': doctor_id,
                'date_appointment': date_appointment,
                'slot_start_time': slot_start,
                'slot_end_time': slot_end,
                'consultation_fee': fee,
                'state': 'draft',
            })

            return self._json_response({
                'status': 'success',
                'message': 'Appointment booked',
                'appointment': {
                    'id': appointment.id,
                    'reference': appointment.reference,
                    'date': str(appointment.date_appointment),
                    'slot_time': appointment.slot_time,
                    'fee': appointment.consultation_fee,
                    'state': appointment.state,
                }
            })

        except Exception as e:
            return self._json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    # ── Single Appointment ───────────────────────
    @http.route(
        '/api/appointments/<int:appointment_id>',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False
    )
    def api_get_appointment(self, appointment_id, **kwargs):
        try:
            partner = request.env.user.partner_id
            appointment = request.env[
                'hospital.appointment'
            ].sudo().search([
                ('id', '=', appointment_id),
                ('patient_id.email', '=', partner.email)
            ], limit=1)

            if not appointment:
                return self._json_response(
                    {'status': 'error',
                     'message': 'Not found'},
                    status=404
                )

            return self._json_response({
                'status': 'success',
                'appointment': {
                    'id': appointment.id,
                    'reference': appointment.reference,
                    'doctor': appointment.doctor_id.name,
                    'department': appointment.department,
                    'date': str(appointment.date_appointment),
                    'slot_time': appointment.slot_time or '',
                    'duration': appointment.appointment_duration,
                    'fee': appointment.consultation_fee,
                    'state': appointment.state,
                    'note': appointment.note or '',
                }
            })

        except Exception as e:
            return self._json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    # ════════════════════════════════════════════
    # PATIENT APIs
    # ════════════════════════════════════════════

    # ── Patient Profile ──────────────────────────
    @http.route(
        '/api/patient/profile',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False
    )
    def api_get_patient_profile(self, **kwargs):
        try:
            partner = request.env.user.partner_id
            patient = request.env[
                'hospital.patient'
            ].sudo().search([
                ('email', '=', partner.email)
            ], limit=1)

            if not patient:
                return self._json_response(
                    {'status': 'error',
                     'message': 'Patient not found'},
                    status=404
                )

            return self._json_response({
                'status': 'success',
                'patient': {
                    'id': patient.id,
                    'name': patient.name,
                    'email': patient.email,
                    'phone': patient.phone or '',
                    'gender': patient.gender or '',
                    'date_of_birth': str(
                        patient.date_of_birth
                    ) if patient.date_of_birth else '',
                }
            })

        except Exception as e:
            return self._json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    # ── Update Patient ───────────────────────────
    @http.route(
        '/api/patient/update',
        type='http',
        auth='user',
        methods=['POST'],
        csrf=False
    )
    def api_update_patient(self, **kwargs):
        try:
            data = json.loads(
                request.httprequest.data.decode('utf-8')
            )
            partner = request.env.user.partner_id
            patient = request.env[
                'hospital.patient'
            ].sudo().search([
                ('email', '=', partner.email)
            ], limit=1)

            if not patient:
                return self._json_response(
                    {'status': 'error',
                     'message': 'Patient not found'},
                    status=404
                )

            update_vals = {}
            if data.get('name'):
                update_vals['name'] = data['name']
            if data.get('phone'):
                update_vals['phone'] = data['phone']
            if data.get('gender'):
                update_vals['gender'] = data['gender']
            if data.get('date_of_birth'):
                update_vals['date_of_birth'] = \
                    datetime.strptime(
                        data['date_of_birth'],
                        '%Y-%m-%d'
                    ).date()

            patient.sudo().write(update_vals)

            return self._json_response({
                'status': 'success',
                'message': 'Profile updated successfully'
            })

        except Exception as e:
            return self._json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )
