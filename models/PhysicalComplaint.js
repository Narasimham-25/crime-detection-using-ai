const mongoose = require("mongoose");

const physicalComplaintSchema = new mongoose.Schema({
  complaint_id: { type: String, required: true, unique: true },
  user_id: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: false },
  crime_type: { type: String, required: true },
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
  status: { type: String, default: "New" },
  ai_severity: { type: String, default: "Low" },
  assigned_officer: { type: String, default: "None" },
  created_date: { type: Date, default: Date.now }
}, {
  timestamps: { createdAt: "created_date", updatedAt: false }
});

module.exports = mongoose.model("PhysicalComplaint", physicalComplaintSchema);
