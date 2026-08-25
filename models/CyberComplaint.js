const mongoose = require("mongoose");

const cyberComplaintSchema = new mongoose.Schema({
  complaint_id: { type: String, required: true, unique: true },
  user_id: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: false },
  crime_type: { type: String, default: "Cyber Crime" },
  title: { type: String, required: true },
  description: { type: String, required: true },
  images_videos: [{ type: String }],
  latitude: { type: Number, required: false },
  longitude: { type: Number, required: false },
  address: { type: String, required: false, default: "Not Provided" },
  state: { type: String, required: false, default: "Not Provided" },
  district: { type: String, required: false, default: "Not Provided" },
  city: { type: String, required: false },
  pincode: { type: String, required: false },
  phone: { type: String, required: false, default: "Not Provided" },
  anonymous: { type: Boolean, default: false },
  ai_analysis: {
    severity: { type: String, default: "Low" },
    confidence: { type: Number, default: 0.5 },
    keywords: [{ type: String }],
    suggested_priority: { type: String, default: "Low" },
    is_duplicate: { type: Boolean, default: false },
    duplicate_of: { type: String, default: "" }
  },
  status: { type: String, default: "New" },
  is_advanced_cyber: { type: Boolean, default: false },
  created_date: { type: Date, default: Date.now }
}, {
  timestamps: { createdAt: "created_date", updatedAt: false }
});

module.exports = mongoose.model("CyberComplaint", cyberComplaintSchema);
