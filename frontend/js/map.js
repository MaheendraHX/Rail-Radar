/* ══════════════════════════════════════════════════
   RailRadar — Map Core
   FRONTEND-1's deliverable.
   
   - Leaflet map initialization
   - GeoJSON track rendering
   - Train marker system (create once, update in-place)
   - 2-second polling loop
   - GPU-accelerated translate3d markers
   - Inactive train path display
   ══════════════════════════════════════════════════ */

// ─── State ───
let map;
let trackLayer = null;
const markers = {};          // Map of trainNumber → L.Marker
let searchOverlayLine = null;
let searchOverlayDot = null;
let pollInterval = null;

// ─── Initialize Map ───
document.addEventListener('DOMContentLoaded', function () {
    map = L.map('map', {
        center: [12.5, 77.0],   // South India center
        zoom: 7,
        zoomControl: false,
        attributionControl: false
    });

    // CartoDB Dark Matter tile layer (free, no API key)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd'
    }).addTo(map);

    // Add station dots
    addStationDots(map);

    // Load tracks
    loadTracks();

    // Start polling
    startPolling();
});

// ─── Load & Render Track GeoJSON ───
function loadTracks() {
    fetch('/api/tracks')
        .then(function (res) { return res.json(); })
        .then(function (data) {
            trackLayer = L.geoJSON(data, {
                style: function () {
                    return {
                        color: '#666',
                        weight: 1.5,
                        opacity: 0.7,
                        lineCap: 'round',
                        lineJoin: 'round'
                    };
                }
            }).addTo(map);
        })
        .catch(function (err) {
            console.error('Failed to load tracks:', err);
        });
}

// ─── Polling Loop ───
function startPolling() {
    pollInterval = setInterval(fetchAndUpdateTrains, 2000);
    // Initial fetch
    fetchAndUpdateTrains();
}

function fetchAndUpdateTrains() {
    const speed = window.currentSpeed || 1;
    const url = '/api/live-trains?speed=' + speed;

    fetch(url)
        .then(function (res) { return res.json(); })
        .then(function (data) {
            // Hide connecting overlay
            const overlay = document.getElementById('connecting-overlay');
            if (overlay && !overlay.classList.contains('hidden')) {
                overlay.classList.add('hidden');
            }

            const trains = data.trains || [];
            const meta = data.meta || {};

            // Track which trains are in this response
            const activeTrainNumbers = new Set();

            trains.forEach(function (train) {
                activeTrainNumbers.add(train.trainNumber);
                updateOrCreateMarker(train);
            });

            // Remove markers for trains no longer active
            Object.keys(markers).forEach(function (tn) {
                if (!activeTrainNumbers.has(tn)) {
                    map.removeLayer(markers[tn]);
                    delete markers[tn];
                }
            });

            // Update meta display
            const countEl = document.getElementById('active-count');
            const timeEl = document.getElementById('server-time');
            if (countEl) {
                countEl.textContent = meta.activeTrains + ' trains active';
            }
            if (timeEl && meta.serverTime) {
                // Extract time portion
                const t = meta.serverTime.split('T')[1];
                if (t) {
                    timeEl.textContent = t.substring(0, 8);
                }
            }
        })
        .catch(function (err) {
            console.error('Poll failed:', err);
            // Show connecting overlay
            const overlay = document.getElementById('connecting-overlay');
            if (overlay) {
                overlay.classList.remove('hidden');
            }
        });
}

// ─── Create or Update Marker ───
function updateOrCreateMarker(train) {
    const tn = train.trainNumber;

    // Determine icon
    const icon = createTrainIcon(
        train.bearing,
        train.state,
        train.delayMinutes || 0,
        false  // aiPredicted — will be true if backend adds aiPredicted field
    );

    if (markers[tn]) {
        // UPDATE existing marker — GPU-accelerated via Leaflet
        markers[tn].setLatLng([train.lat, train.lng]);
        markers[tn].setIcon(icon);
    } else {
        // CREATE new marker
        const marker = L.marker([train.lat, train.lng], { icon: icon });

        // Popup with basic info
        marker.bindPopup(
            '<strong>' + train.trainName + '</strong><br>' +
            '#' + train.trainNumber + '<br>' +
            '<span style="color:' + (train.state === 'moving' ? '#00ff88' : '#ff4444') + '">' +
            (train.state === 'moving' ? '● Moving' : '● Dwelling') +
            '</span>'
        );

        // Click handler → open info panel
        marker.on('click', function () {
            if (typeof showTrainInfo === 'function') {
                showTrainInfo(train);
            }
        });

        marker.addTo(map);
        markers[tn] = marker;
    }
}

// ─── Inactive Train Path Display ───
// Called by FRONTEND-2's search feature

/**
 * Show a dashed polyline + dimmed origin dot for an inactive train's route.
 * @param {string} trainNumber
 * @param {Array} routeCoords - Array of [lat, lng] pairs
 */
function showInactiveTrainPath(trainNumber, routeCoords) {
    clearSearchOverlay();

    if (!routeCoords || routeCoords.length < 2) return;

    // Draw dashed line
    searchOverlayLine = L.polyline(routeCoords, {
        color: '#888',
        weight: 2,
        opacity: 0.4,
        dashArray: '8, 8'
    }).addTo(map);

    // Dimmed dot at origin
    searchOverlayDot = L.circleMarker(routeCoords[0], {
        radius: 5,
        fillColor: '#888',
        fillOpacity: 0.4,
        stroke: false
    }).addTo(map);

    // Fit map to the route
    map.fitBounds(searchOverlayLine.getBounds(), { padding: [40, 40] });
}

/**
 * Remove the search overlay (dashed line + origin dot).
 */
function clearSearchOverlay() {
    if (searchOverlayLine) {
        map.removeLayer(searchOverlayLine);
        searchOverlayLine = null;
    }
    if (searchOverlayDot) {
        map.removeLayer(searchOverlayDot);
        searchOverlayDot = null;
    }
}
