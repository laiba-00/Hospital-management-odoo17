from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from datetime import datetime


class HospitalPortal(CustomerPortal):

    # ── Portal Home Count ────────────────────────
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'appointment_count' in counters:
            partner = request.env.user.partner_id
            appointment_count = request.env[
                'hospital.appointment'
            ].sudo().search_count([
                ('patient_id.email', '=', partner.email)
            ])
            values['appointment_count'] = appointment_count
        return values

    # ── My Appointments List ─────────────────────
    @http.route(
        '/my/appointments',
        type='http',
        auth='user',
        website=True
    )
    def portal_appointments(self, **kwargs):
        partner = request.env.user.partner_id
        appointments = request.env[
            'hospital.appointment'
        ].sudo().search([
            ('patient_id.email', '=', partner.email)
        ], order='date_appointment desc')

        return request.render(
            'om_hospital.portal_appointments_list',
            {'appointments': appointments}
        )

    # ── Appointment Detail ───────────────────────
    @http.route(
        '/my/appointments/<int:appointment_id>',
        type='http',
        auth='user',
        website=True
    )
    def portal_appointment_detail(self,
                                  appointment_id,
                                  **kwargs):
        partner = request.env.user.partner_id
        appointment = request.env[
            'hospital.appointment'
        ].sudo().search([
            ('id', '=', appointment_id),
            ('patient_id.email', '=', partner.email)
        ], limit=1)

        if not appointment:
            return request.not_found()

        return request.render(
            'om_hospital.portal_appointment_detail',
            {'appointment': appointment}
        )

    # ── Register Page ────────────────────────────
    @http.route(
        '/hospital/register',
        type='http',
        auth='public',
        website=True
    )
    def hospital_register(self, **kwargs):
        return request.render(
            'om_hospital.hospital_register_page',
            {}
        )

    # ── Register Submit ──────────────────────────
    @http.route(
        '/hospital/register/submit',
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        csrf=False
    )
    def hospital_register_submit(self, **kwargs):
        name = kwargs.get('name')
        email = kwargs.get('email')
        password = kwargs.get('password')

        # Check existing user
        existing_user = request.env[
            'res.users'
        ].sudo().search([
            ('login', '=', email)
        ], limit=1)

        if existing_user:
            return request.render(
                'om_hospital.hospital_register_page',
                {'error': 'Email already registered. Please login.'}
            )

        # Naya portal user banao
        user = request.env['res.users'].sudo().create({
            'name': name,
            'login': email,
            'email': email,
            'password': password,
            'groups_id': [(6, 0, [
                request.env.ref('base.group_portal').id
            ])]
        })

        # Patient record banao
        request.env['hospital.patient'].sudo().create({
            'name': name,
            'email': email,
        })

        # Auto login
        request.session.authenticate(
            request.db,
            email,
            password
        )

        # Website home pe redirect
        return request.redirect('/')

    # ── Login Page ───────────────────────────────
    @http.route(
        '/hospital/login',
        type='http',
        auth='public',
        website=True
    )
    def hospital_login(self, **kwargs):
        return request.render(
            'om_hospital.hospital_login_page',
            {}
        )

    # ── Login Submit ─────────────────────────────
    @http.route(
        '/hospital/login/submit',
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        csrf=False
    )
    def hospital_login_submit(self, **kwargs):
        email = kwargs.get('email')
        password = kwargs.get('password')

        uid = request.session.authenticate(
            request.db,
            email,
            password
        )

        if uid:
            return request.redirect('/home')
        else:
            return request.render(
                'om_hospital.hospital_login_page',
                {'error': 'Invalid email or password!'}
            )




    # ── Doctors List ─────────────────────────────
    @http.route(
        '/hospital/doctors',
        type='http',
        auth='public',
        website=True
    )
    def hospital_doctors(self, **kwargs):
        doctors = request.env[
            'hospital.doctor'
        ].sudo().search([])

        return request.render(
            'om_hospital.hospital_doctors_list',
            {'doctors': doctors}
        )

    # ── Book Appointment Page ────────────────────
    @http.route(
        '/hospital/book',
        type='http',
        auth='public',
        website=True
    )
    def hospital_book_appointment(self, **kwargs):
        doctors = request.env[
            'hospital.doctor'
        ].sudo().search([])

        return request.render(
            'om_hospital.hospital_book_appointment',
            {'doctors': doctors}
        )

    # ── Get Available Slots — AJAX ───────────────
    @http.route(
        '/hospital/get_slots',
        type='json',
        auth='public',
        website=True
    )
    def get_available_slots(self,
                            doctor_id,
                            date,
                            duration,
                            **kwargs):

        doctor = request.env[
            'hospital.doctor'
        ].sudo().browse(int(doctor_id))

        # Date ka weekday nikalo
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        weekday = date_obj.strftime('%A').lower()

        # Doctor ka schedule dhundo
        schedule = request.env[
            'hospital.doctor.schedule'
        ].sudo().search([
            ('doctor_id', '=', int(doctor_id)),
            ('weekday', '=', weekday),
            ('is_available', '=', True)
        ], limit=1)

        if not schedule:
            return {
                'slots': [],
                'message': 'Doctor not available on this day'
            }

        # Already booked slots
        booked = request.env[
            'hospital.appointment'
        ].sudo().search([
            ('doctor_id', '=', int(doctor_id)),
            ('date_appointment', '=', date),
            ('state', '!=', 'cancelled')
        ])
        booked_times = [b.slot_start_time for b in booked]

        # Available slots generate karo
        slots = []
        current = schedule.start_time
        dur_hours = int(duration) / 60

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

        return {'slots': slots}

    # ── Book Appointment Submit ──────────────────
    @http.route(
        '/hospital/book/submit',
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        csrf=False
    )

    def hospital_book_submit(self, **kwargs):
        doctor_id = int(kwargs.get('doctor_id'))
        date_appointment = kwargs.get('date_appointment')
        duration = int(kwargs.get('duration'))
        slot_start = float(kwargs.get('slot_start'))
        slot_end = float(kwargs.get('slot_end'))
        fee = float(kwargs.get('fee'))

        # Patient info
        patient_name = kwargs.get('patient_name')
        patient_email = kwargs.get('patient_email')
        patient_phone = kwargs.get('patient_phone')
        patient_gender = kwargs.get('patient_gender')
        patient_dob = kwargs.get('patient_dob') or False

        # Date string ko Date object mein convert karo
        if date_appointment:
            date_appointment = datetime.strptime(
                date_appointment, '%Y-%m-%d'
            ).date()

        if patient_dob:
            patient_dob = datetime.strptime(
                patient_dob, '%Y-%m-%d'
            ).date()

        # Patient dhundo ya banao
        patient = request.env[
            'hospital.patient'
        ].sudo().search([
            ('email', '=', patient_email)
        ], limit=1)

        if not patient:
            patient = request.env[
                'hospital.patient'
            ].sudo().create({
                'name': patient_name,
                'email': patient_email,
                'phone': patient_phone,
                'gender': patient_gender,
                'date_of_birth': patient_dob,
            })
        else:
            patient.sudo().write({
                'name': patient_name,
                'phone': patient_phone,
                'gender': patient_gender,
                'date_of_birth': patient_dob,
            })

        # Appointment banao
        appointment = request.env[
            'hospital.appointment'
        ].sudo().create({
            'patient_id': patient.id,
            'doctor_id': doctor_id,
            'date_appointment': date_appointment,
            'slot_start_time': slot_start,
            'slot_end_time': slot_end,
            'consultation_fee': fee,
            'state': 'draft',
        })

        return request.redirect('/my/appointments')


