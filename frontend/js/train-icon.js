/* ══════════════════════════════════════════════════
   RailRadar — SVG Train Icon Utility
   FRONTEND-3's shared deliverable.
   
   Function: createTrainIcon(bearing, state, delayMinutes, aiPredicted)
   Returns:  Leaflet DivIcon
   
   Called by FRONTEND-1 on every 2-second poll.
   ══════════════════════════════════════════════════ */

/**
 * Create a Leaflet DivIcon with a rotated SVG train arrow.
 * 
 * @param {number} bearing       - Compass heading 0-360 degrees
 * @param {string} state         - "moving", "dwelling", or "inactive"
 * @param {number} delayMinutes  - Minutes of delay (default 0)
 * @param {boolean} aiPredicted  - Whether the delay was AI-predicted (default false)
 * @returns {L.DivIcon}
 */
function createTrainIcon(bearing, state, delayMinutes = 0, aiPredicted = false) {
    // Determine color based on state and delay
    let color;
    if (state === 'dwelling') {
        color = '#ff4444';
    } else if (aiPredicted && delayMinutes > 0) {
        color = '#9944ff';
    } else if (delayMinutes > 0) {
        color = '#4488ff';
    } else {
        color = '#00ff88';
    }

    // Determine glow color for drop-shadow
    let glowColor;
    if (state === 'dwelling') {
        glowColor = 'rgba(255, 68, 68, 0.6)';
    } else if (aiPredicted && delayMinutes > 0) {
        glowColor = 'rgba(153, 68, 255, 0.6)';
    } else if (delayMinutes > 0) {
        glowColor = 'rgba(68, 136, 255, 0.6)';
    } else {
        glowColor = 'rgba(0, 255, 136, 0.5)';
    }

    // Build SVG
    const aiTag = aiPredicted ? `
        <text x="12" y="4" text-anchor="middle" 
              font-size="5" font-weight="700" fill="#9944ff"
              font-family="sans-serif">AI</text>
    ` : '';

    const viewBoxHeight = aiPredicted ? 22 : 18;

    const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="${viewBoxHeight}" 
             viewBox="0 0 24 ${viewBoxHeight}">
            <g transform="rotate(${bearing}, 12, 12)">
                ${aiTag}
                <polygon points="12,2 18,16 12,13 6,16" 
                         fill="${color}" 
                         stroke="${color}" 
                         stroke-width="0.5"
                         stroke-linejoin="round"/>
            </g>
        </svg>
    `;

    const cssClass = 'train-icon' + (aiPredicted ? ' train-icon-ai' : '');

    return L.divIcon({
        html: svg,
        className: cssClass,
        iconSize: [24, viewBoxHeight],
        iconAnchor: [12, viewBoxHeight / 2],
        popupAnchor: [0, -viewBoxHeight / 2]
    });
}
