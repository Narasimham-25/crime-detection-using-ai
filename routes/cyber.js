const express = require("express");
const router = express.Router();
const CyberComplaint = require("../models/CyberComplaint");
const Alert = require("../models/Alert");
const { authMiddleware, requireAuth, requireRole } = require("../middlewares/auth");

// POST /api/cyber (Direct submission fallback/backup)
router.post("/", authMiddleware, async (req, res) => {
    try {
        const { title, details, contact, type, latitude, longitude, address, state, district } = req.body;
        
        const complaintId = `CMP-${Date.now()}`;
        const report = new CyberComplaint({
            complaint_id: complaintId,
            user_id: req.user ? req.user.id : null,
            crime_type: "Cyber Crime",
            title: title || type || "Cyber Incident",
            description: details || "No details provided",
            phone: contact || "Not Provided",
            anonymous: false,
            latitude: parseFloat(latitude) || 0.0,
            longitude: parseFloat(longitude) || 0.0,
            address: address || "Unknown",
            state: state || "Unknown",
            district: district || "Unknown",
            status: "New",
            is_advanced_cyber: true,
            ai_analysis: {
                severity: "Medium",
                confidence: 0.75,
                keywords: [type || "phishing"],
                suggested_priority: "Medium"
            }
        });
        await report.save();
        
        const alertMsg = `A new Cybercrime incident was reported: ${report.title}.`;
        const alert = new Alert({ message: alertMsg, type: "Cybercrime" });
        await alert.save();
        
        res.status(201).json(report);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Server error" });
    }
});

// GET /api/cyber
router.get("/", requireAuth, async (req, res) => {
    try {
        const role = req.user.role;
        
        if (role === "citizen") {
            // Citizens see only their own cyber complaints
            const reports = await CyberComplaint.find({ user_id: req.user.id }).sort({ created_date: -1 });
            return res.json(reports);
        }
        
        if (role === "analyst" || role === "admin" || role === "officer") {
            if (role === "officer") {
                // Officers should not see Cyber complaints as per instructions: "Only physical crimes should appear here (officers)"
                return res.status(403).json({ error: "Forbidden. Officer access restricted from Cyber complaints." });
            }
            
            // Analysts and Admins see all cyber complaints
            const reports = await CyberComplaint.find().sort({ created_date: -1 });
            return res.json(reports);
        }
        
        res.status(403).json({ error: "Forbidden. Access restricted." });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Server error" });
    }
});

module.exports = router;
