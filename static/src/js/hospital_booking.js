var selectedDuration = 0;
var selectedSlotStart = 0;
var selectedSlotEnd = 0;

function updateFees() {
    var select = document.getElementById('doctor_select');
    var option = select.options[select.selectedIndex];

    if (option.value) {
        document.getElementById('fee_10').innerText =
            'Rs. ' + option.dataset.fee10;
        document.getElementById('fee_20').innerText =
            'Rs. ' + option.dataset.fee20;
        document.getElementById('fee_40').innerText =
            'Rs. ' + option.dataset.fee40;
    }
    resetSlots();
}

function selectDuration(duration) {
    selectedDuration = duration;

    [10, 20, 40].forEach(function(d) {
        var card = document.getElementById('card_' + d);
        if (d === duration) {
            card.style.border = '2px solid #0d6efd';
            card.style.backgroundColor = '#e7f0ff';
        } else {
            card.style.border = '2px solid #dee2e6';
            card.style.backgroundColor = '';
        }
    });

    document.getElementById('duration_hidden').value = duration;
    loadSlots();
}

function loadSlots() {
    var doctorId = document.getElementById('doctor_select').value;
    var date = document.getElementById('date_input').value;

    if (!doctorId || !date || !selectedDuration) {
        return;
    }

    fetch('/hospital/get_slots', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'call',
            params: {
                doctor_id: doctorId,
                date: date,
                duration: selectedDuration
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        var result = data.result;
        var container = document.getElementById('slots_container');
        container.innerHTML = '';

        if (!result.slots || result.slots.length === 0) {
            container.innerHTML =
                '<div class="alert alert-warning">' +
                (result.message || 'No slots available') +
                '</div>';
        } else {
            result.slots.forEach(function(slot) {
                var btn = document.createElement('div');
                btn.className = 'col-md-3 mb-2';
                btn.innerHTML =
                    '<button type="button" ' +
                    'class="btn btn-outline-primary w-100 slot-btn" ' +
                    'onclick="selectSlot(' +
                    slot.start + ',' +
                    slot.end + ',\'' +
                    slot.label + '\')">' +
                    slot.label +
                    '</button>';
                container.appendChild(btn);
            });
        }

        document.getElementById('slots_section').style.display = 'block';
    });
}

function selectSlot(start, end, label) {
    selectedSlotStart = start;
    selectedSlotEnd = end;

    document.getElementById('slot_start').value = start;
    document.getElementById('slot_end').value = end;

    document.querySelectorAll('.slot-btn').forEach(function(btn) {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-outline-primary');
    });

    event.target.classList.remove('btn-outline-primary');
    event.target.classList.add('btn-primary');

    var select = document.getElementById('doctor_select');
    var option = select.options[select.selectedIndex];
    var fee = option.dataset['fee' + selectedDuration];

    document.getElementById('fee_hidden').value = fee;
    document.getElementById('fee_show').innerText = 'Rs. ' + fee;
    document.getElementById('fee_display').style.display = 'block';
    document.getElementById('submit_btn').style.display = 'block';
}

function resetSlots() {
    document.getElementById('slots_section').style.display = 'none';
    document.getElementById('fee_display').style.display = 'none';
    document.getElementById('submit_btn').style.display = 'none';
    document.getElementById('slots_container').innerHTML = '';
    selectedDuration = 0;
    selectedSlotStart = 0;
    selectedSlotEnd = 0;
}