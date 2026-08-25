const mongoose = require("mongoose");

const sosSchema = new mongoose.Schema({
  location: { type: String, required: true },
  type: { type: String, default: "Emergency SOS via Button" },
  status: { type: String, default: "Active" },
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model("Sos", sosSchema);
