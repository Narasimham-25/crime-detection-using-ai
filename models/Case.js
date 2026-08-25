const mongoose = require("mongoose");
const caseSchema = new mongoose.Schema({
    id: String,
    officer: String,
    status: String,
    priority: String,
    notes: String
}, { timestamps: true });
module.exports = mongoose.model("Case", caseSchema);
