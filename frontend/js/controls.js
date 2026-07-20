/* RailRadar speed controls. FRONTEND-1 reads window.currentSpeed per poll. */
(function () {
    'use strict';

    var SPEED_DESCRIPTIONS = {
        1: 'Real-time',
        10: '10× speed',
        60: '1 min/sec',
        100: '~2 min journey'
    };

    // Do not overwrite a speed selected before this script is re-initialized.
    window.currentSpeed = Number(window.currentSpeed) || 1;

    function setSpeed(speed, buttons, statusLabel) {
        if (!Object.prototype.hasOwnProperty.call(SPEED_DESCRIPTIONS, speed)) return;

        window.currentSpeed = speed;
        buttons.forEach(function (button) {
            var isActive = Number(button.dataset.speed) === speed;
            button.classList.toggle('active', isActive);
            button.setAttribute('aria-pressed', String(isActive));
        });

        if (statusLabel) statusLabel.textContent = SPEED_DESCRIPTIONS[speed];

        // Lets consumers refresh immediately without coupling this file to map.js.
        window.dispatchEvent(new CustomEvent('railradar:speedchange', {
            detail: { speed: speed }
        }));
    }

    function initSpeedControls() {
        var buttons = Array.prototype.slice.call(document.querySelectorAll('.speed-btn'));
        var statusLabel = document.getElementById('speed-status');
        if (!buttons.length) return;

        buttons.forEach(function (button) {
            button.type = 'button';
            button.setAttribute('aria-pressed', 'false');
            if (button.dataset.railradarBound === 'true') return;

            button.dataset.railradarBound = 'true';
            button.addEventListener('click', function () {
                setSpeed(Number(button.dataset.speed), buttons, statusLabel);
            });
        });

        setSpeed(window.currentSpeed, buttons, statusLabel);
    }

    window.initSpeedControls = initSpeedControls;
    document.addEventListener('DOMContentLoaded', initSpeedControls);
}());
