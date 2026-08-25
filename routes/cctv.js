const express = require("express");
const router = express.Router();
const Cctv = require("../models/Cctv");

router.post("/", async (req, res) => {
    try {
        const feed = new Cctv({ url: req.body.url });
        await feed.save();
        res.status(201).json(feed);
    } catch (err) {
        res.status(500).json({ error: "Server error" });
    }
});

router.get("/", async (req, res) => {
    try {
        const feeds = await Cctv.find().sort({ createdAt: -1 }).limit(50);
        res.json(feeds);
    } catch (err) {
        res.status(500).json({ error: "Server error" });
    }
});

router.delete("/:id", async (req, res) => {
    try {
        const deleted = await Cctv.findByIdAndDelete(req.params.id);
        if (!deleted) return res.status(404).json({ error: "Not found" });
        res.json({ message: "Feed removed" });
    } catch (err) {
        res.status(500).json({ error: "Server error" });
    }
});

module.exports = router;
