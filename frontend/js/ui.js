/* ══════════════════════════════════════════════════
   RailRadar — UI (Info Panel, Admin Panel, Search)
   FRONTEND-2's deliverable.
   
   - Train info sidebar (slides in from right)
   - Admin delay control panel
   - AI Predict Delay button
   - Train search functionality
   ══════════════════════════════════════════════════ */

// ─── State ───
let allTrains = [];           // Full list from /api/trains
let selectedTrainNumber = null;

// ══════════════════════════════════════════════════
//  INITIALIZATION
// ══════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', function () {
    initInfoPanel();
    initAdminPanel();
    initSearch();
    loadTrainList();
});

// ══════════════════════════════════════════════════
//  INFO PANEL
// ══════════════════════════════════════════════════

function initInfoPanel() {
    var closeBtn = document.getElementById('info-panel-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function () {
            document.getElementById('info-panel').classList.add('hidden');
            selectedTrainNumber = null;
        });
    }
}

/**
 * Show train info in the sidebar panel.
 * Called by FRONTEND-1 when a marker is clicked.
 * @param {Object} train - Train position object from /api/live-trains
 */
function showTrainInfo(train) {
    selectedTrainNumber = train.trainNumber;

    var panel = document.getElementById('info-panel');
    panel.classList.remove('hidden');

    document.getElementById('info-train-name').textContent = train.trainName || 'Unknown Train';
    document.getElementById('info-train-number').textContent = '#' + train.trainNumber;

    // Status
    var statusDot = document.getElementById('info-status-dot');
    var statusText = document.getElementById('info-status-text');
    statusDot.className = 'status-indicator ' + train.state;
    statusText.textContent = train.state === 'moving' ? 'Moving' : 'Dwelling';

    // Speed
    document.getElementById('info-speed').textContent =
        train.state === 'moving' ? (train.speedKmh || 0) + ' km/h' : '0 km/h — Stopped';

    // Stations
    document.getElementById('info-current-station').textContent = train.currentStation || '—';
    document.getElementById('info-next-station').textContent = train.nextStation || '—';

    // ETA
    document.getElementById('info-eta').textContent = train.arrivalTime || '—';

    // Times
    document.getElementById('info-departure').textContent = train.departureTime || '—';
    document.getElementById('info-arrival').textContent = train.arrivalTime || '—';

    // Stops — count from schedule if available
    document.getElementById('info-stops').textContent = '—';

    // Delay
    var delayRow = document.getElementById('info-delay-row');
    var delayValue = document.getElementById('info-delay-value');
    if (train.delayMinutes && train.delayMinutes > 0) {
        delayRow.classList.remove('hidden');
        delayValue.textContent = train.delayMinutes + ' min';
    } else {
        delayRow.classList.add('hidden');
    }

    // Auto-update: re-fetch info for this train periodically
    // (handled by the main polling loop calling showTrainInfo again if panel is open)
}

// ══════════════════════════════════════════════════
//  ADMIN PANEL
// ══════════════════════════════════════════════════

function initAdminPanel() {
    var slider = document.getElementById('admin-delay-slider');
    var sliderValue = document.getElementById('admin-delay-value');
    var applyBtn = document.getElementById('admin-apply-btn');
    var resetBtn = document.getElementById('admin-reset-btn');
    var aiBtn = document.getElementById('admin-ai-btn');
    var trainSelect = document.getElementById('admin-train-select');

    // Slider live value
    if (slider) {
        slider.addEventListener('input', function () {
            sliderValue.textContent = slider.value;
        });
    }

    // Apply delay
    if (applyBtn) {
        applyBtn.addEventListener('click', function () {
            var trainNum = trainSelect.value;
            var delayMin = parseInt(slider.value, 10);

            if (!trainNum) {
                showAdminStatus('error', 'Please select a train first.');
                return;
            }

            fetch('/api/delay', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ train: trainNum, delay_minutes: delayMin })
            })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.success) {
                    showAdminStatus('success', '✓ ' + data.message);
                } else {
                    showAdminStatus('error', '✗ ' + (data.error || 'Unknown error'));
                }
            })
            .catch(function (err) {
                showAdminStatus('error', '✗ Connection failed.');
            });
        });
    }

    // Reset delay
    if (resetBtn) {
        resetBtn.addEventListener('click', function () {
            var trainNum = trainSelect.value;
            if (!trainNum) {
                showAdminStatus('error', 'Please select a train first.');
                return;
            }

            slider.value = 0;
            sliderValue.textContent = '0';

            fetch('/api/delay', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ train: trainNum, delay_minutes: 0 })
            })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.success) {
                    showAdminStatus('success', '✓ Delay cleared.');
                }
            })
            .catch(function () {
                showAdminStatus('error', '✗ Connection failed.');
            });
        });
    }

    // AI Predict
    if (aiBtn) {
        aiBtn.addEventListener('click', function () {
            var trainNum = trainSelect.value;
            if (!trainNum) {
                showAdminStatus('error', 'Please select a train first.');
                return;
            }

            aiBtn.disabled = true;
            showAdminStatus('loading', '🧠 Analyzing delay risk...');

            fetch('/api/predict-delay', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ trainNumber: trainNum })
            })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                aiBtn.disabled = false;

                if (!data.success) {
                    showAdminStatus('error', '✗ ' + (data.error || 'Prediction failed'));
                    return;
                }

                var pred = data.prediction;
                if (pred.will_delay) {
                    showAICard('delay', pred);
                } else {
                    showAICard('clear', pred);
                }
            })
            .catch(function () {
                aiBtn.disabled = false;
                showAdminStatus('error', '✗ Connection failed.');
            });
        });
    }
}

function loadTrainList() {
    fetch('/api/trains')
        .then(function (res) { return res.json(); })
        .then(function (data) {
            allTrains = data;
            var select = document.getElementById('admin-train-select');
            if (!select) return;

            data.forEach(function (train) {
                var option = document.createElement('option');
                option.value = train.trainNumber;
                option.textContent = train.trainNumber + ' — ' + train.trainName;
                select.appendChild(option);
            });
        })
        .catch(function (err) {
            console.error('Failed to load train list:', err);
        });
}

// ══════════════════════════════════════════════════
//  ADMIN STATUS DISPLAY
// ══════════════════════════════════════════════════

function showAdminStatus(type, message) {
    var el = document.getElementById('admin-status');
    if (!el) return;
    el.className = 'admin-status ' + type;
    el.textContent = message;
}

function showAICard(type, prediction) {
    var el = document.getElementById('admin-status');
    if (!el) return;

    el.className = 'admin-status';

    var card = document.createElement('div');
    card.className = 'ai-card ' + (type === 'delay' ? 'ai-card-delay' : 'ai-card-clear');

    if (type === 'delay') {
        card.innerHTML =
            '<div class="ai-card-title">🧠 AI Predicted Delay</div>' +
            '<div class="ai-card-detail" style="font-size:16px;font-weight:700;color:#ff4444;">' +
            prediction.predicted_delay_minutes + ' minutes</div>' +
            '<div class="ai-card-detail">Risk Score: ' + (prediction.risk_score * 100).toFixed(0) + '%</div>' +
            '<div class="ai-card-detail">Next Station: ' + (prediction.next_station || '—') + '</div>' +
            '<div class="ai-card-factors">' +
            prediction.risk_factors.map(function (f) {
                return '<span class="ai-factor-tag">' + f.replace(/_/g, ' ') + '</span>';
            }).join('') +
            '</div>';
    } else {
        card.innerHTML =
            '<div class="ai-card-title">✓ AI Prediction: All Clear</div>' +
            '<div class="ai-card-detail">Risk Score: ' + (prediction.risk_score * 100).toFixed(0) + '%</div>' +
            '<div class="ai-card-detail">Next Station: ' + (prediction.next_station || '—') + '</div>' +
            '<div class="ai-card-detail" style="color:var(--accent-green)">No delay expected.</div>';
    }

    el.innerHTML = '';
    el.appendChild(card);
}

// ══════════════════════════════════════════════════
//  SEARCH
// ══════════════════════════════════════════════════

function initSearch() {
    var input = document.getElementById('search-input');
    var results = document.getElementById('search-results');
    if (!input || !results) return;

    input.addEventListener('input', function () {
        var query = input.value.trim().toLowerCase();
        if (query.length < 1) {
            results.classList.add('hidden');
            results.innerHTML = '';
            return;
        }

        var matches = allTrains.filter(function (t) {
            return t.trainNumber.toLowerCase().includes(query) ||
                   t.trainName.toLowerCase().includes(query);
        }).slice(0, 8);

        if (matches.length === 0) {
            results.classList.add('hidden');
            return;
        }

        results.innerHTML = '';
        results.classList.remove('hidden');

        matches.forEach(function (t) {
            var item = document.createElement('div');
            item.className = 'search-result-item';
            item.innerHTML =
                '<span class="search-result-number">#' + t.trainNumber + '</span>' +
                '<span class="search-result-name">' + t.trainName + '</span>';

            item.addEventListener('click', function () {
                results.classList.add('hidden');
                input.value = '';

                // Check if train is currently active
                var speed = window.currentSpeed || 1;
                fetch('/api/live-trains?speed=' + speed + '&train=' + t.trainNumber)
                    .then(function (res) { return res.json(); })
                    .then(function (data) {
                        if (data.trains && data.trains.length > 0) {
                            // Active — zoom to it and show info
                            var train = data.trains[0];
                            map.setView([train.lat, train.lng], 10);
                            showTrainInfo(train);
                        } else {
                            // Inactive — fetch full route and show dashed path
                            fetch('/api/trains/' + t.trainNumber)
                                .then(function (res) { return res.json(); })
                                .then(function (detail) {
                                    var routeCoords = [];
                                    if (detail.trainRoute) {
                                        // We need station coordinates — use mock coords
                                        var stationMap = window.RailRadarStations || [];
                                        detail.trainRoute.forEach(function (stop) {
                                            var found = stationMap.find(function (s) {
                                                return s.code === stop.stationCode;
                                            });
                                            if (found) {
                                                routeCoords.push([found.lat, found.lon]);
                                            }
                                        });
                                    }
                                    if (routeCoords.length >= 2 && typeof showInactiveTrainPath === 'function') {
                                        showInactiveTrainPath(t.trainNumber, routeCoords);
                                    }
                                });
                        }
                    });
            });

            results.appendChild(item);
        });
    });

    // Close search results on outside click
    document.addEventListener('click', function (e) {
        if (!e.target.closest('#search-container')) {
            results.classList.add('hidden');
        }
    });
}
