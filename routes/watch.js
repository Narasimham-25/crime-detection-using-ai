const express = require("express");
const router = express.Router();
const Watch = require("../models/Watch");
const { authMiddleware } = require("../middlewares/auth");

router.post("/", authMiddleware, async (req, res) => {
    try {
        const payload = req.body;
        
        const watch = new Watch({
            user_id: req.user ? req.user.id : null,
            user_name: req.user ? req.user.name : "System",  
            name: payload.name,
            area: payload.area,
            plan: payload.plan
        });
        
        await watch.save();
        res.status(201).json({
             name: watch.name,
             area: watch.area,
             plan: watch.plan,
             user_name: watch.user_name,
        });
    } catch (err) {
        console.error(err);
        if (err.name === 'ValidationError') {
            return res.status(400).json({ error: err.message });
        }
        res.status(500).json({ error: "Server error" });
    }
});

router.get("/", async (req, res) => {
    try {
        const watches = await Watch.find().sort({ time: -1 }).limit(20);
        res.status(200).json({
            rows: watches.map(w => ({
                name: w.name,
                area: w.area,
                plan: w.plan,
                user_name: w.user_name,
            }))
        });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Server error" });
    }
});

module.exports = router;
