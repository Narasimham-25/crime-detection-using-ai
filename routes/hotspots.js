const express = require("express");
const router = express.Router();
const ai = require("../utils/ai");

// GET /api/hotspots
router.get("/", async (req, res) => {
    try {
        const hotspots = await ai.predictHotspots();
        
        // Format exactly how the frontend expects it:
        // Rank, state, district, mentions, crime_types, latitude, longitude, maps_url
        const formatted = hotspots.map((h, index) => ({
            rank: index + 1,
            state: h.state,
            district: h.district,
            mentions: h.count,
            crime_types: h.crime_types,
            latitude: h.latitude,
            longitude: h.longitude,
            maps_url: `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(h.district + ', ' + h.state + ', India')}`
        }));

        res.json({ hotspots: formatted });
    } catch (err) {
        console.error("Hotspots calculation error:", err);
        res.status(500).json({ error: "Server error calculating hotspots" });
    }
});

module.exports = router;
