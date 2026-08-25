const mongoose = require("mongoose");
const cctvSchema = new mongoose.Schema({
    url: String
}, { timestamps: true });
module.exports = mongoose.model("Cctv", cctvSchema);
