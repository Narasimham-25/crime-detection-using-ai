const mongoose = require("mongoose");

const complaintSchema = new mongoose.Schema({
  user_id: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
  user_name: { type: String, default: "Anonymous" },
  phone: { type: String },
  category: { type: String, required: true },
  district: { type: String, required: true },
  desc: { type: String, required: true },
  anonymous: { type: Boolean, default: false },
  location: { type: String },
  status: { type: String, default: "New" },
  ai_severity: { type: String, default: "Low" },
  ai_confidence: { type: Number, default: 0.5 },
  time: { type: Date, default: Date.now },
});

module.exports = mongoose.model("Complaint", complaintSchema);
