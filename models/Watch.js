const mongoose = require("mongoose");

const watchSchema = new mongoose.Schema({
  user_id: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
  user_name: { type: String, default: "System" },
  name: { type: String, required: true },
  area: { type: String, required: true },
  plan: { type: String, required: true },
  time: { type: Date, default: Date.now }
});

module.exports = mongoose.model("Watch", watchSchema);
