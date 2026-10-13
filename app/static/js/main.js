/**
 * Elden Care - Client-side Interactive Logic
 * Features: Accessibility Toggles, Slot Dynamic Fetching, Image Previews, Modal Confirmations
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Accessibility Font Size Manager
    initAccessibilityControls();

    // 2. Dynamic Appointment Time Slot Loader
    initSlotPicker();

    // 3. Image Upload Preview
    initImagePreview();

    // 4. Confirmation Dialogs for Destructive Actions
    initConfirmDialogs();

    // 5. Auto dismiss flash alerts after 6 seconds
    initAlertDismiss();
});

function initAccessibilityControls() {
    const savedScale = localStorage.getItem('elden_font_scale');
    if (savedScale) {
        document.body.classList.remove('font-size-large', 'font-size-xlarge');
        if (savedScale === 'large') document.body.classList.add('font-size-large');
        if (savedScale === 'xlarge') document.body.classList.add('font-size-xlarge');
    }

    document.querySelectorAll('[data-font-scale]').forEach(btn => {
        btn.addEventListener('click', function () {
            const scale = this.getAttribute('data-font-scale');
            document.body.classList.remove('font-size-large', 'font-size-xlarge');
            if (scale === 'large') document.body.classList.add('font-size-large');
            if (scale === 'xlarge') document.body.classList.add('font-size-xlarge');
            localStorage.setItem('elden_font_scale', scale);
        });
    });
}

function initSlotPicker() {
    const dateInput = document.getElementById('appointment_date');
    const providerSelect = document.getElementById('provider_id');
    const slotsContainer = document.getElementById('slots-container');
    const timeSlotInput = document.getElementById('time_slot');

    if (!dateInput || !slotsContainer || !timeSlotInput) return;

    function fetchSlots() {
        const selectedDate = dateInput.value;
        if (!selectedDate) {
            slotsContainer.innerHTML = '<p class="text-muted small">Please select an appointment date first.</p>';
            return;
        }

        const providerId = providerSelect ? providerSelect.value : '';
        slotsContainer.innerHTML = '<div class="d-flex align-items-center gap-2 text-primary"><div class="spinner-border spinner-border-sm" role="status"></div><span>Checking available appointment slots...</span></div>';

        let url = `/api/appointments/available-slots?date=${encodeURIComponent(selectedDate)}`;
        if (providerId && providerId !== '0') {
            url += `&provider_id=${encodeURIComponent(providerId)}`;
        }

        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (data.success && data.data && data.data.length > 0) {
                    renderSlots(data.data);
                } else {
                    slotsContainer.innerHTML = '<div class="alert alert-warning py-2 small">No slots found for this date. Please pick another date.</div>';
                }
            })
            .catch(err => {
                console.error('Error fetching slots:', err);
                slotsContainer.innerHTML = '<div class="alert alert-danger py-2 small">Error loading slots. Please refresh and try again.</div>';
            });
    }

    function renderSlots(slots) {
        slotsContainer.innerHTML = '';
        let hasAvailable = false;

        slots.forEach(slot => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `slot-badge-btn ${slot.is_available ? '' : 'disabled'}`;
            btn.innerHTML = `<i class="bi bi-clock me-1"></i>${slot.display}`;

            if (slot.is_available) {
                hasAvailable = true;
                btn.addEventListener('click', function () {
                    document.querySelectorAll('.slot-badge-btn').forEach(b => b.classList.remove('selected'));
                    btn.classList.add('selected');
                    timeSlotInput.value = slot.start_time;
                });
            } else {
                btn.disabled = true;
                btn.title = "This slot is already booked";
            }

            slotsContainer.appendChild(btn);
        });

        if (!hasAvailable) {
            slotsContainer.innerHTML = '<div class="alert alert-info py-2 small">All slots on this date are currently fully booked. Please choose another date or caregiver.</div>';
        }
    }

    dateInput.addEventListener('change', fetchSlots);
    if (providerSelect) {
        providerSelect.addEventListener('change', fetchSlots);
    }

    // Trigger on initial page load if date is pre-filled
    if (dateInput.value) {
        fetchSlots();
    }
}

function initImagePreview() {
    const fileInputs = document.querySelectorAll('input[type="file"][data-preview-target]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function () {
            const targetId = this.getAttribute('data-preview-target');
            const targetImg = document.getElementById(targetId);
            if (!targetImg || !this.files || !this.files[0]) return;

            const reader = new FileReader();
            reader.onload = function (e) {
                targetImg.src = e.target.result;
            };
            reader.readAsDataURL(this.files[0]);
        });
    });
}

function initConfirmDialogs() {
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', function (e) {
            const msg = this.getAttribute('data-confirm') || "Are you sure you want to perform this action?";
            if (!confirm(msg)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

function initAlertDismiss() {
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(alert => {
            const bsAlert = bootstrap.Alert.getInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            } else {
                alert.classList.add('fade');
                setTimeout(() => alert.remove(), 500);
            }
        });
    }, 6000);
}
