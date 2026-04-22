/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted, onWillUpdateProps } from "@odoo/owl";

class SlotSelectorWidget extends Component {
    static template = "om_hospital.SlotSelectorWidget";
    static props = {
        id: { optional: true },
        name: { optional: true },
        record: { type: Object },
        readonly: { type: Boolean, optional: true },
        required: { type: Boolean, optional: true },
        value: { optional: true },
        update: { optional: true },
        "*": true,
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            selectedDuration: null,
            slots: [],
            loading: false,
            fee10: 0,
            fee20: 0,
            fee40: 0,
            selectedFee: 0,
            selectedSlot: null,
        });

        onMounted(() => {
            setTimeout(async () => {
                const doctorId = this.props.record.data.doctor_id?.[0];
                if (doctorId) {
                    await this.loadFeesForDoctor(doctorId);
                }
            }, 800);
        });

        onWillUpdateProps(async (nextProps) => {
            const newDoctorId = nextProps.record.data.doctor_id?.[0];
            const currentDoctorId = this.props.record.data.doctor_id?.[0];
            if (newDoctorId && newDoctorId !== currentDoctorId) {
                await this.loadFeesForDoctor(newDoctorId);
            }
        });
    }

    get doctorId() {
        const doctor = this.props.record.data.doctor_id;
        return doctor ? doctor[0] : null;
    }

    get appointmentDate() {
        const date = this.props.record.data.date_appointment;
        if (!date) return null;
        if (typeof date === "string") return date;
        return date.toFormat ? date.toFormat("yyyy-MM-dd") : date.toString().slice(0, 10);
    }

    get appointmentId() {
        return this.props.record.resId;
    }

    get isLocked() {
        return this.props.record.data.state !== "draft";
    }

    get currentSlotTime() {
        return this.props.record.data.slot_time || "";
    }

    get durations() {
        return [
            { value: 10, label: "10 Min", desc: "Quick Check-up" },
            { value: 20, label: "20 Min", desc: "Standard" },
            { value: 40, label: "40 Min", desc: "Detailed" },
        ];
    }

    async loadFeesForDoctor(doctorId) {
        if (!doctorId) return;
        try {
            const result = await this.orm.read(
                "hospital.doctor",
                [doctorId],
                ["fee_10min", "fee_20min", "fee_40min"]
            );
            if (result && result[0]) {
                this.state.fee10 = result[0].fee_10min || 0;
                this.state.fee20 = result[0].fee_20min || 0;
                this.state.fee40 = result[0].fee_40min || 0;
            }
        } catch (e) {
            console.error("Fee load error:", e);
        }
    }

    getFeeForDuration(duration) {
        if (duration === 10) return this.state.fee10;
        if (duration === 20) return this.state.fee20;
        if (duration === 40) return this.state.fee40;
        return 0;
    }

    async onDurationChange(duration) {
        if (this.isLocked) return;

        if (!this.doctorId || !this.appointmentDate) {
            alert("Please select Doctor and Date first!");
            return;
        }

        // Fees reload karo agar abhi tak load nahi huin
        if (this.state.fee10 === 0 &&
            this.state.fee20 === 0 &&
            this.state.fee40 === 0) {
            await this.loadFeesForDoctor(this.doctorId);
        }

        this.state.selectedDuration = duration;
        this.state.selectedFee = this.getFeeForDuration(duration);
        this.state.loading = true;
        this.state.slots = [];
        this.state.selectedSlot = null;

        try {
            const response = await fetch('/hospital/get_slots', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        doctor_id: this.doctorId,
                        date: this.appointmentDate,
                        duration: duration,
                    }
                })
            });
            const data = await response.json();
            const result = data.result;

            if (result && result.slots && result.slots.length > 0) {
                this.state.slots = result.slots.map(slot => ({
                    start_time: slot.start,
                    end_time: slot.end,
                    time_display: slot.label,
                    is_booked: false,
                }));
            } else {
                this.state.slots = [];
            }
        } catch (e) {
            console.error("Slot load error:", e);
        }

        this.state.loading = false;
    }

    async onSlotSelect(slot) {
        if (slot.is_booked) return;

        this.state.selectedSlot = slot.start_time;

        // record.update — Odoo native way, discard properly kaam karega
        await this.props.record.update({
            slot_start_time: slot.start_time,
            slot_end_time: slot.end_time,
            consultation_fee: this.state.selectedFee,
        });
    }

    formatFee(amount) {
        if (!amount) return "—";
        return `Rs. ${parseInt(amount).toLocaleString()}`;
    }

    isDurationSelected(value) {
        return this.state.selectedDuration === value;
    }

    isSlotSelected(startTime) {
        return this.state.selectedSlot === startTime;
    }
}

registry.category("fields").add("slot_selector", {
    component: SlotSelectorWidget,
    supportedTypes: ["many2one"],
});