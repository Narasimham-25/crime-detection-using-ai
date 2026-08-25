const express = require("express");
const router = express.Router();
const Case = require("../models/Case");
const PhysicalComplaint = require("../models/PhysicalComplaint");
const CyberComplaint = require("../models/CyberComplaint");
const { requireRole } = require("../middlewares/auth");

router.post("/", requireRole(["officer", "analyst", "admin"]), async (req, res) => {
    try {
        const pcase = new Case(req.body);
        await pcase.save();

        // If a case is successfully saved as Closed, try to find and remove/close the matching complaint
        if (req.body.status === "Closed") {
            const id = req.body.id;
            
            // Search Physical Complaints
            const physicals = await PhysicalComplaint.find();
            const matchPhys = physicals.find(c => c.complaint_id.endsWith(id) || c._id.toString().endsWith(id));
            if (matchPhys) {
                matchPhys.status = "Closed";
                await matchPhys.save();
            }

            // Search Cyber Complaints
            const cybers = await CyberComplaint.find();
            const matchCyber = cybers.find(c => c.complaint_id.endsWith(id) || c._id.toString().endsWith(id));
            if (matchCyber) {
                matchCyber.status = "Closed";
                await matchCyber.save();
            }
        }

        res.status(201).json(pcase);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Server error" });
    }
});

router.get("/", requireRole(["officer", "analyst", "admin"]), async (req, res) => {
    try {
        const cases = await Case.find().sort({ createdAt: -1 }).limit(100);
        res.json(cases);
    } catch (err) {
        res.status(500).json({ error: "Server error" });
    }
});

module.exports = router;
