/* ══════════════════════════════════════════════════
   RailRadar — Controls
   FRONTEND-3's deliverable.
   
   Speed controls (1x, 10x, 60x, 100x)
   ══════════════════════════════════════════════════ */

// ─── Global speed variable ───
// FRONTEND-1's polling loop reads this and passes it as ?speed=N
window.currentSpeed = 1;

const SPEED_DESCRIPTIONS = {
    1:   'Real-time',
    10:  '10× speed',
    60:  '1 min/sec',
    100: '~2 min journey'
};

document.addEventListener('DOMContentLoaded', function () {
    const buttons = document.querySelectorAll('.speed-btn');
    const statusLabel = document.getElementById('speed-status');

    buttons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            // Remove active from all
            buttons.forEach(function (b) { b.classList.remove('active'); });
            // Activate clicked
            btn.classList.add('active');

            const speed = parseInt(btn.getAttribute('data-speed'), 10);
            window.currentSpeed = speed;

            if (statusLabel) {
                statusLabel.textContent = SPEED_DESCRIPTIONS[speed] || '';
            }
        });
    });
});
