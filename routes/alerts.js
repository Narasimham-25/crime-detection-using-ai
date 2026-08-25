const express = require("express");
const router = express.Router();
const Alert = require("../models/Alert");
const { authMiddleware } = require("../middlewares/auth");

router.get("/recent", authMiddleware, async (req, res) => {
    try {
        if (!req.user || !["officer", "analyst", "admin"].includes(req.user.role)) {
            return res.status(403).json({ error: "Forbidden. Not an officer or analyst." });
        }
        
        const sinceMs = parseInt(req.query.since || "0", 10);
        let query = {};
        if (sinceMs > 0) {
            query.createdAt = { $gt: new Date(sinceMs) };
        } else {
            // If opening for the first time, don't spam 100 historical alerts. Give last 5 mins or none.
            query.createdAt = { $gt: new Date(Date.now() - 5 * 60 * 1000) };
        }

        const alerts = await Alert.find(query).sort({ createdAt: 1 }).limit(50);
        
        res.status(200).json({ alerts });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Server error" });
    }
});

module.exports = router;
