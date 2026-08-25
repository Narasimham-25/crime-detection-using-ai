const mongoose = require("mongoose");
const cyberSchema = new mongoose.Schema({
    type: String,
    contact: String,
    details: String,
    user: { type: mongoose.Schema.Types.ObjectId, ref: 'User' }
}, { timestamps: true });
module.exports = mongoose.model("Cyber", cyberSchema);
