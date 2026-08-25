const express = require("express");
const router = express.Router();
const Complaint = require("../models/Complaint");
const Case = require("../models/Case");

router.get("/details", async (req, res) => {
  try {
    const complaintsCount = await Complaint.countDocuments();
    const casesCount = await Case.countDocuments();
    
    res.json({
        ok: true,
        service: "crime-backend-node",
        uptime_seconds: Math.floor(process.uptime()),
        counts: {
            complaints: complaintsCount,
            cases: casesCount
        }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
