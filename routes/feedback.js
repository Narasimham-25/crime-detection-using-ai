const express = require("express");
const router = express.Router();
const Feedback = require("../models/Feedback");
const { authMiddleware, requireRole } = require("../middlewares/auth");

router.post("/", authMiddleware, async (req, res) => {
    try {
        const feedback = new Feedback({ text: req.body.text, user: req.user ? req.user.id : null });
        await feedback.save();
        res.status(201).json(feedback);
    } catch (err) {
        res.status(500).json({ error: "Server error" });
    }
});

router.get("/", requireRole(["officer", "analyst", "admin"]), async (req, res) => {
    try {
        const fb = await Feedback.find().sort({ createdAt: -1 }).limit(100);
        res.json(fb);
    } catch (err) {
        res.status(500).json({ error: "Server error" });
    }
});

module.exports = router;
