/* ══════════════════════════════════════════════════
   RailRadar — Station Label Dots
   FRONTEND-3's deliverable.
   
   Adds small white dots for major junctions.
   ══════════════════════════════════════════════════ */

window.RailRadarStations = [
    { code: 'SBC',  name: 'KSR Bengaluru',   lat: 12.9767, lon: 77.5753 },
    { code: 'MAS',  name: 'Chennai Central',  lat: 13.0827, lon: 80.2707 },
    { code: 'ERS',  name: 'Ernakulam Jn',     lat: 9.9312,  lon: 76.2673 },
    { code: 'MAQ',  name: 'Mangaluru Central', lat: 12.8641, lon: 74.8370 },
    { code: 'TVC',  name: 'Thiruvananthapuram', lat: 8.4875, lon: 76.9491 },
    { code: 'CBE',  name: 'Coimbatore Jn',    lat: 11.0056, lon: 76.9715 },
    { code: 'CLT',  name: 'Kozhikode',        lat: 11.2588, lon: 75.7804 },
    { code: 'CAN',  name: 'Kannur',           lat: 11.8745, lon: 75.3704 },
    { code: 'SRR',  name: 'Shoranur Jn',      lat: 10.7663, lon: 75.9254 },
    { code: 'NCJ',  name: 'Nagercoil Jn',     lat: 8.1833,  lon: 77.4119 },
];

/**
 * Add station label dots to the Leaflet map.
 * @param {L.Map} map - The Leaflet map instance
 * @returns {L.Layer[]} Array of station markers
 */
function addStationDots(map) {
    const markers = [];

    window.RailRadarStations.forEach(function (station) {
        const marker = L.circleMarker([station.lat, station.lon], {
            radius: 3,
            fillColor: '#ffffff',
            fillOpacity: 0.5,
            stroke: false,
            interactive: true
        });

        marker.bindTooltip(station.code, {
            permanent: false,
            direction: 'top',
            className: 'station-tooltip'
        });

        marker.addTo(map);
        markers.push(marker);
    });

    return markers;
}
