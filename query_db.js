const mongoose = require("mongoose");
const User = require("./models/User");
const Complaint = require("./models/Complaint");
require("dotenv").config();

mongoose.connect(process.env.MONGO_URI || "mongodb://127.0.0.1:27017/crime_ai")
  .then(async () => {
    console.log("Connected to MongoDB!");
    
    const users = await User.find();
    console.log("\n--- USERS ---");
    users.forEach(u => console.log(`ID: ${u._id}, Name: ${u.name}, Email: ${u.email}, Role: ${u.role}`));
    
    const complaints = await Complaint.find().sort({ time: -1 }).limit(5);
    console.log("\n--- LATEST COMPLAINTS ---");
    complaints.forEach(c => console.log(`ID: ${c._id}, Category: ${c.category}, District: ${c.district}, User: ${c.user_name}, Status: ${c.status}`));
    
    mongoose.connection.close();
  })
  .catch(err => {
    console.error(err);
    process.exit(1);
  });
