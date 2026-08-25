const mongoose = require("mongoose");
const feedbackSchema = new mongoose.Schema({
    text: String,
    user: { type: mongoose.Schema.Types.ObjectId, ref: 'User' }
}, { timestamps: true });
module.exports = mongoose.model("Feedback", feedbackSchema);
