const express = require("express");
const router = express.Router();
const { requireAuth } = require("../middlewares/auth");
const PhysicalComplaint = require("../models/PhysicalComplaint");
const CyberComplaint = require("../models/CyberComplaint");

// GET /api/stats
router.get("/", requireAuth, async (req, res) => {
    try {
        const role = req.user.role;
        let complaints = [];

        if (role === "citizen") {
            // Citizen gets their own statistics
            const physicals = await PhysicalComplaint.find({ user_id: req.user.id });
            const cybers = await CyberComplaint.find({ user_id: req.user.id });
            complaints = [...physicals, ...cybers];
        } else if (role === "officer") {
            // Law enforcement gets physical complaints statistics
            complaints = await PhysicalComplaint.find();
        } else if (role === "analyst") {
            // Analyst gets cyber complaints statistics
            complaints = await CyberComplaint.find();
        } else if (role === "admin") {
            // Admin gets stats for all complaints
            const physicals = await PhysicalComplaint.find();
            const cybers = await CyberComplaint.find();
            complaints = [...physicals, ...cybers];
        }

        const categories = {};
        const severityStats = { Critical: 0, High: 0, Medium: 0, Low: 0 };

        complaints.forEach(c => {
            const cat = c.crime_type || "Other";
            categories[cat] = (categories[cat] || 0) + 1;

            // Handle severity (could be nested inside ai_analysis for cyber)
            let sev = "Low";
            if (c.ai_analysis && c.ai_analysis.severity) {
                sev = c.ai_analysis.severity;
            } else if (c.crime_type) {
                // Approximate severity for physical
                const catLower = c.crime_type.toLowerCase();
                const descLower = (c.description || "").toLowerCase();
                if (["murder", "kill", "shoot", "stab"].some(w => catLower.includes(w) || descLower.includes(w))) {
                    sev = "Critical";
                } else if (["assault", "robbery", "kidnap", "domestic violence", "drug"].some(w => catLower.includes(w) || descLower.includes(w))) {
                    sev = "High";
                } else if (["theft", "accident", "fraud"].some(w => catLower.includes(w) || descLower.includes(w))) {
                    sev = "Medium";
                }
            }

            if (severityStats[sev] !== undefined) {
                severityStats[sev]++;
            }
        });

        // Convert to arrays for frontend Chart
        const categoryLabels = Object.keys(categories);
        const categoryValues = Object.values(categories);

        res.status(200).json({
            categoryLabels,
            categoryValues,
            severityStats,
            total: complaints.length
        });
    } catch (err) {
        console.error("Stats API Error:", err);
        res.status(500).json({ error: "Server error calculating stats" });
    }
});

module.exports = router;
