const mongoose = require("mongoose");
const dotenv = require("dotenv");
const path = require("path");

dotenv.config({ path: path.join(__dirname, "../.env") });

const mongoURI = process.env.MONGO_URI || "mongodb://127.0.0.1:27017/crime_ai";

async function clearDatabase() {
  try {
    console.log("Connecting to MongoDB at:", mongoURI);
    await mongoose.connect(mongoURI);
    console.log("Connected successfully!");

    const collections = Object.keys(mongoose.connection.collections);
    for (const name of collections) {
      console.log(`Clearing collection: ${name}...`);
      await mongoose.connection.collections[name].deleteMany({});
    }

    console.log("\n✅ MongoDB Database cleared successfully!");
  } catch (error) {
    console.error("Error clearing database:", error);
  } finally {
    await mongoose.disconnect();
    process.exit(0);
  }
}

clearDatabase();
