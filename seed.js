require("dotenv").config();
const mongoose = require("mongoose");
const Complaint = require("./models/Complaint");
const fs = require("fs");

const seedData = [
  {
    user_name: "Test User 1",
    phone: "9876543210",
    category: "Theft",
    district: "Thane",
    desc: "Sample theft complaint",
    ai_severity: "Medium",
    ai_confidence: 0.75
  },
  {
    user_name: "Test User 2",
    phone: "9123456789",
    category: "Assault",
    district: "Guntur",
    desc: "Sample assault complaint",
    ai_severity: "High",
    ai_confidence: 0.85
  },
  {
    user_name: "Test User 3",
    phone: "9012345678",
    category: "Fraud",
    district: "Mumbai",
    desc: "Sample fraud complaint",
    ai_severity: "Low",
    ai_confidence: 0.65
  },
  {
    user_name: "Test User 4",
    phone: "8765432109",
    category: "Theft",
    district: "Delhi",
    desc: "Another theft complaint",
    ai_severity: "Low",
    ai_confidence: 0.70
  },
  {
    user_name: "Test User 5",
    phone: "8654321098",
    category: "Assault",
    district: "Bangalore",
    desc: "Another assault complaint",
    ai_severity: "Medium",
    ai_confidence: 0.78
  }
];

mongoose.connect(process.env.MONGO_URI || "mongodb://localhost:27017/crime_db").then(async () => {
  console.log("Seeding database...");
  try {
    await Complaint.deleteMany({}); // Clear existing data
    const result = await Complaint.insertMany(seedData);
    console.log(`✓ Inserted ${result.length} complaints`);
    mongoose.connection.close();
    console.log("Database seeded successfully!");
  } catch (err) {
    console.error("Error seeding database:", err);
    mongoose.connection.close();
  }
});
