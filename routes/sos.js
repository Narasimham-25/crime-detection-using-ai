const express = require("express");
const router = express.Router();
const Sos = require("../models/Sos");
const Alert = require("../models/Alert");

router.post("/", async (req, res) => {
  try {
    const { location, type } = req.body;
    const newSos = new Sos({ location, type: type || "Emergency SOS via Button" });
    await newSos.save();
    
    // Broadcast as an active Alert so it pops up
    const alert = new Alert({ message: `CRITICAL SOS ACTIVATED at coordinates: ${location || 'Unknown'}`, type: "SOS" });
    await alert.save();
    
    res.status(201).json(newSos);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get("/", async (req, res) => {
  try {
    const sosAlerts = await Sos.find().sort({ createdAt: -1 }).limit(10);
    res.json(sosAlerts);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
