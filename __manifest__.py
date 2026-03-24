{
    "name": "Hospital Management System",
    "author": "LM Solution",
    "License": "LGPL-3",
    "Version": "17.0.1.1",
    "depends": [
        "mail",
        "portal",
        "website",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        'data/cron.xml',
        'data/email_templates.xml',
        'report/appointment_slip_template.xml',
        'report/appointment_report_action.xml',
        "views/patient_view.xml",
        "views/patient_readonly_views.xml",
        "views/appointment_slot_views.xml",
        "views/appointment_slot_wizard_view.xml",
        "views/appointment_view.xml",
        "views/doctors.xml",
        "views/doctor_schedule_views.xml",
        "views/patient_tag_view.xml",
        "views/portal_template_view.xml",
        "views/menu.xml",
    ]
}
