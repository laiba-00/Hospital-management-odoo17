🏥 Hospital Management System — Odoo 17

A complete Hospital Management ERP module built 
from scratch in Odoo 17 using Python and XML.

📋 Overview
This module provides a full-featured hospital 
management system including patient registration, 
doctor management, appointment booking, online 
patient portal, and REST APIs for mobile 
app integration.

✨ Features
👤 Patient Management
•	Patient registration and records
•	Date of birth, gender, phone, email
•	Patient tags for categorization
•	Complete medical history tracking

👨‍⚕️ Doctor Management
•	Doctor profiles with departments
•	Consultation fee structure
•	10 minute — Quick Check-up
•	20 minute — Standard Consultation
•	40 minute — Detailed Examination
•	Weekly schedule management

📅 Appointment System
•	Create and manage appointments
•	Time slot selection — 10/20/40 minutes
•	Auto fee calculation based on slot duration
•	Status workflow:
•	Draft → Confirmed → In Consultation → Done
•	Cancel option available
•	Duplicate appointment prevention
•	Past date validation

🌐 Online Patient Portal
•	Patient self-registration
•	Secure login system
•	Online appointment booking
•	Doctor selection with fee display
•	Available slot selection
•	Appointment history dashboard
•	Appointment detail view

📱 REST APIs
•	Complete API suite for mobile integration
•	Auth APIs — Login, Register
•	Doctors API — List, Detail, Schedule
•	Slots API — Available slots by doctor/date
•	Appointments API — List, Book, Detail
•	Patient API — Profile, Update

📊 Reports & Analytics
•	PDF Appointment Slip — QWeb
•	Calendar View — appointments by date
•	Graph View — fee analysis by doctor
•	Pivot View — appointments by status
⚙️ Automation
•	Email notifications on confirmation
•	Cron job — Auto cancel past appointments
•	Sequence — Auto reference number generation

🛠️ Tech Stack

Backend    : Python , Odoo 17 ORM
Frontend   : XML, QWeb, JavaScript
Database   : PostgreSQL
API        : REST API, JSON
Security   : CSRF, Portal Auth

📁 Module Structure
om_hospital/
├── controllers/
│   ├── __init__.py
│   ├── portal.py          # Website/Portal routes
│   └── api.py             # REST API endpoints
├── data/
│   ├── sequence.xml       # Reference sequence
│   ├── cron.xml           # Scheduled actions
│   └── email_templates.xml
├── models/
│   ├── __init__.py
│   ├── appointment.py
│   ├── doctor.py
│   ├── doctor_schedule.py
│   └── patient.py
├── report/
│   ├── appointment_slip_template.xml
│   └── appointment_report_action.xml
├── security/
│   └── ir.model.access.csv
├── static/
│   └── src/
│       └── js/
│           └── hospital_booking.js
├── views/
│   ├── appointment_view.xml
│   ├── doctors.xml
│   ├── doctor_schedule_views.xml
│   ├── patient_view.xml
│   ├── portal_templates.xml
│   └── menu.xml
├── wizards/
│   ├── appointment_slot_wizard.py
│   └── appointment_slot_wizard_view.xml
├── __init__.py
└── __manifest__.py

 


