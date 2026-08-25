const express = require("express");
const router = express.Router();
const PhysicalComplaint = require("../models/PhysicalComplaint");
const CyberComplaint = require("../models/CyberComplaint");

router.get("/", async (req, res) => {
    try {
        const q = req.query.q || "";
        const limit = parseInt(req.query.limit) || 20;

        // Search physical complaints
        const physicals = await PhysicalComplaint.find({
            $or: [
                { crime_type: { $regex: q, $options: "i" } },
                { district: { $regex: q, $options: "i" } },
                { description: { $regex: q, $options: "i" } }
            ]
        }).limit(limit);

        // Search cyber complaints
        const cybers = await CyberComplaint.find({
            $or: [
                { crime_type: { $regex: q, $options: "i" } },
                { district: { $regex: q, $options: "i" } },
                { description: { $regex: q, $options: "i" } }
            ]
        }).limit(limit);

        const rows = [
            ...physicals.map(p => ({
                source: "Physical Complaint",
                id: p.complaint_id,
                title: p.crime_type || "Unknown",
                district: p.district || "Unknown",
                status: p.status || "New",
                time: new Date(p.created_date).toLocaleString()
            })),
            ...cybers.map(c => ({
                source: "Cyber Complaint",
                id: c.complaint_id,
                title: c.crime_type || "Cyber Crime",
                district: c.district || "Unknown",
                status: c.status || "New",
                time: new Date(c.created_date).toLocaleString()
            }))
        ].slice(0, limit);

        res.json({ rows });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Server error" });
    }
});

module.exports = router;
