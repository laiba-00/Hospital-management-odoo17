/** @odoo-module **/

import { Component, useState, onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

export class HospitalDashboard extends Component {
    static template = "om_hospital.HospitalDashboard";

    setup() {
        this.orm = useService("orm");

        this.state = useState({
            activeTab: "overview",

            // Overview
            totalPatients: 0,
            totalDoctors: 0,
            todayAppointments: 0,
            pendingAppointments: 0,
            completedAppointments: 0,
            cancelledAppointments: 0,

            // Patients
            patientList: [],
            totalPatientCount: 0,

            // Appointments
            recentAppointments: [],
            appointmentFilter: "all",

            // Doctors
            doctorWorkload: [],

            // Departments
            departmentStats: [],
        });

        this.barChartRef = useRef("barChart");
        this.doughnutChartRef = useRef("doughnutChart");
        this.barChartInstance = null;
        this.doughnutChartInstance = null;

        onMounted(async () => {
            await this.loadTab("overview");
        });
    }

    // ─── TAB SWITCHING ─────────────────────────────────────────
    async switchTab(tab, filter = "all") {
        this.state.activeTab = tab;
        this.state.appointmentFilter = filter;
        await this.loadTab(tab, filter);
    }

    async loadTab(tab, filter = "all") {
        if (tab === "overview")     await this.loadOverview();
        if (tab === "patients")     await this.loadPatients();
        if (tab === "appointments") await this.loadAppointments(filter);
        if (tab === "doctors")      await this.loadDoctors();
        if (tab === "departments")  await this.loadDepartments();
    }

    // ─── OVERVIEW ──────────────────────────────────────────────
    async loadOverview() {
        this.state.totalPatients = await this.orm.searchCount("hospital.patient", []);
        this.state.totalDoctors  = await this.orm.searchCount("hospital.doctor", []);

        const today = new Date().toISOString().slice(0, 10);
        this.state.todayAppointments = await this.orm.searchCount("hospital.appointment", [
            ["date_appointment", "=", today],
        ]);
        this.state.pendingAppointments = await this.orm.searchCount("hospital.appointment", [
            ["state", "=", "draft"],
        ]);
        this.state.completedAppointments = await this.orm.searchCount("hospital.appointment", [
            ["state", "=", "done"],
        ]);
        this.state.cancelledAppointments = await this.orm.searchCount("hospital.appointment", [
            ["state", "=", "cancelled"],
        ]);

        setTimeout(() => {
            this.renderBarChart();
            this.renderDoughnutChart();
        }, 100);
    }

    async renderBarChart() {
        const labels = [];
        const counts = [];

        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().slice(0, 10);
            const label = date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
            labels.push(label);
            const count = await this.orm.searchCount("hospital.appointment", [
                ["date_appointment", "=", dateStr],
            ]);
            counts.push(count);
        }

        const canvas = this.barChartRef.el;
        if (!canvas) return;
        if (this.barChartInstance) this.barChartInstance.destroy();

        this.barChartInstance = new Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Appointments",
                    data: counts,
                    backgroundColor: "rgba(99, 102, 241, 0.7)",
                    borderColor: "rgba(99, 102, 241, 1)",
                    borderWidth: 2,
                    borderRadius: 8,
                }],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: "Appointments — Last 7 Days",
                        font: { size: 13, weight: "bold" },
                    },
                },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } },
                },
            },
        });
    }

    async renderDoughnutChart() {
        const statuses = ["draft", "confirmed", "in_consultation", "done", "cancelled"];
        const labels   = ["Draft", "Confirmed", "In Consultation", "Done", "Cancelled"];
        const colors   = ["#ffc107", "#6366f1", "#06b6d4", "#22c55e", "#ef4444"];
        const counts   = [];

        for (const status of statuses) {
            const count = await this.orm.searchCount("hospital.appointment", [
                ["state", "=", status],
            ]);
            counts.push(count);
        }

        const canvas = this.doughnutChartRef.el;
        if (!canvas) return;
        if (this.doughnutChartInstance) this.doughnutChartInstance.destroy();

        this.doughnutChartInstance = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels,
                datasets: [{
                    data: counts,
                    backgroundColor: colors,
                    borderWidth: 2,
                }],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: "bottom", labels: { font: { size: 11 } } },
                    title: {
                        display: true,
                        text: "Appointments by Status",
                        font: { size: 13, weight: "bold" },
                    },
                },
            },
        });
    }

    // ─── PATIENTS TAB ──────────────────────────────────────────
    async loadPatients() {
        this.state.totalPatientCount = await this.orm.searchCount("hospital.patient", []);
        const records = await this.orm.searchRead(
            "hospital.patient",
            [],
            ["name", "date_of_birth", "gender", "phone"],
            { limit: 10, order: "id desc" }
        );
        this.state.patientList = records;
    }

    // ─── APPOINTMENTS TAB ──────────────────────────────────────
    async loadAppointments(filter = "all") {
        let domain = [];

        if (filter === "today") {
            const today = new Date().toISOString().slice(0, 10);
            domain = [["date_appointment", "=", today]];
        } else if (filter === "draft") {
            domain = [["state", "=", "draft"]];
        } else if (filter === "done") {
            domain = [["state", "=", "done"]];
        } else if (filter === "cancelled") {
            domain = [["state", "=", "cancelled"]];
        }

        const records = await this.orm.searchRead(
            "hospital.appointment",
            domain,
            ["reference", "patient_id", "doctor_id", "date_appointment", "state", "consultation_fee"],
            { limit: 20, order: "date_appointment desc" }
        );
        this.state.recentAppointments = records;
    }

    // ─── DOCTORS TAB ───────────────────────────────────────────
    async loadDoctors() {
        const doctors = await this.orm.searchRead(
            "hospital.doctor",
            [],
            ["name", "department"],
            {}
        );

        const workload = [];
        for (const doc of doctors) {
            const total = await this.orm.searchCount("hospital.appointment", [
                ["doctor_id", "=", doc.id],
            ]);
            const done = await this.orm.searchCount("hospital.appointment", [
                ["doctor_id", "=", doc.id],
                ["state", "=", "done"],
            ]);
            workload.push({
                name: doc.name,
                department: doc.department || "—",
                total,
                done,
            });
        }

        workload.sort((a, b) => b.total - a.total);
        const max = workload[0]?.total || 1;
        this.state.doctorWorkload = workload.map(d => ({
            ...d,
            percent: Math.round((d.total / max) * 100),
        }));
    }

    // ─── DEPARTMENTS TAB ───────────────────────────────────────
    async loadDepartments() {
        const appointments = await this.orm.searchRead(
            "hospital.appointment",
            [],
            ["department", "state"],
            {}
        );

        const deptMap = {};
        for (const appt of appointments) {
            const dept = appt.department || "Unknown";
            if (!deptMap[dept]) {
                deptMap[dept] = { total: 0, done: 0, cancelled: 0, pending: 0 };
            }
            deptMap[dept].total++;
            if (appt.state === "done")      deptMap[dept].done++;
            if (appt.state === "cancelled") deptMap[dept].cancelled++;
            if (appt.state === "draft")     deptMap[dept].pending++;
        }

        this.state.departmentStats = Object.entries(deptMap).map(([name, stats]) => ({
            name, ...stats,
        })).sort((a, b) => b.total - a.total);
    }

    // ─── HELPERS ───────────────────────────────────────────────
    getStatusBadge(state) {
        const map = {
            draft:           "badge-draft",
            confirmed:       "badge-confirmed",
            in_consultation: "badge-consultation",
            done:            "badge-done",
            cancelled:       "badge-cancelled",
        };
        return map[state] || "badge-secondary";
    }

    getStatusLabel(state) {
        const map = {
            draft:           "Draft",
            confirmed:       "Confirmed",
            in_consultation: "In Consultation",
            done:            "Done",
            cancelled:       "Cancelled",
        };
        return map[state] || state;
    }

    formatFee(fee) {
        return fee ? `Rs. ${fee.toFixed(0)}` : "—";
    }
}

registry.category("actions").add("om_hospital.action_hospital_dashboard", HospitalDashboard);