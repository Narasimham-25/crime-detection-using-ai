const express = require("express");
const router = express.Router();
const Case = require("../models/Case");
const PhysicalComplaint = require("../models/PhysicalComplaint");
const CyberComplaint = require("../models/CyberComplaint");
const Complaint = require("../models/Complaint");
const { requireRole } = require("../middlewares/auth");

router.post("/", requireRole(["officer", "analyst", "admin"]), async (req, res) => {
    try {
        const id = String(req.body.id || "").trim();
        let pcase;
        if (id) {
            pcase = await Case.findOne({ id });
            if (pcase) {
                pcase.officer = req.body.officer || pcase.officer;
                pcase.status = req.body.status || pcase.status;
                pcase.priority = req.body.priority || pcase.priority;
                pcase.notes = req.body.notes !== undefined ? req.body.notes : pcase.notes;
                await pcase.save();
                await Case.updateMany(
                    { id, _id: { $ne: pcase._id } },
                    { status: pcase.status, officer: pcase.officer, notes: pcase.notes }
                );
            } else {
                pcase = new Case(req.body);
                await pcase.save();
            }
        } else {
            pcase = new Case(req.body);
            await pcase.save();
        }

        // If a case is saved as Resolved, Closed, or Solved, update and remove the matching complaint
        const isResolved = ["Resolved", "Closed", "Solved", "resolved", "closed", "solved"].includes(String(req.body.status || "").trim());
        if (isResolved) {
            const id = String(req.body.id || "").trim();
            if (id) {
                // Search Physical Complaints
                const physicals = await PhysicalComplaint.find();
                const matchPhys = physicals.filter(c =>
                    (c.complaint_id && (c.complaint_id === id || c.complaint_id.endsWith(id))) ||
                    (c._id && (c._id.toString() === id || c._id.toString().endsWith(id)))
                );
                for (const p of matchPhys) {
                    p.status = req.body.status || "Resolved";
                    await p.save();
                }

                // Search Cyber Complaints
                const cybers = await CyberComplaint.find();
                const matchCyber = cybers.filter(c =>
                    (c.complaint_id && (c.complaint_id === id || c.complaint_id.endsWith(id))) ||
                    (c._id && (c._id.toString() === id || c._id.toString().endsWith(id)))
                );
                for (const c of matchCyber) {
                    c.status = req.body.status || "Resolved";
                    await c.save();
                }

                // Search Legacy Complaints
                try {
                    const legacy = await Complaint.find();
                    const matchLeg = legacy.filter(c =>
                        (c.complaint_id && (c.complaint_id === id || c.complaint_id.endsWith(id))) ||
                        (c.id && (c.id === id || c.id.endsWith(id))) ||
                        (c._id && (c._id.toString() === id || c._id.toString().endsWith(id)))
                    );
                    for (const l of matchLeg) {
                        l.status = req.body.status || "Resolved";
                        await l.save();
                    }
                } catch (legacyErr) {
                    console.warn("Legacy complaint sync skipped:", legacyErr.message);
                }
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
        const { status } = req.query;
        let query = {};
        if (status && status.toLowerCase() !== "all") {
            query.status = status;
        } else if (!status) {
            // Exclude resolved and closed cases by default
            query.status = { $nin: ["Resolved", "Closed", "Solved", "resolved", "closed", "solved"] };
        }
        const cases = await Case.find(query).sort({ createdAt: -1 }).limit(100);
        res.json(cases);
    } catch (err) {
        res.status(500).json({ error: "Server error" });
    }
});

module.exports = router;
