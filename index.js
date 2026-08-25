require("dotenv").config();
const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const path = require("path");
const http = require("http");
const { Server } = require("socket.io");

const authRoutes = require("./routes/auth");
const complaintRoutes = require("./routes/complaints");
const watchRoutes = require("./routes/watch");
const statsRoutes = require("./routes/stats");
const searchRoutes = require("./routes/search");
const caseRoutes = require("./routes/cases");
const cyberRoutes = require("./routes/cyber");
const feedbackRoutes = require("./routes/feedback");
const cctvRoutes = require("./routes/cctv");
const sosRoutes = require("./routes/sos");
const healthRoutes = require("./routes/health");
const alertsRoutes = require("./routes/alerts");
const hotspotRoutes = require("./routes/hotspots");

const app = express();
app.use(cors());
app.use(express.json());

// Serve static uploads
app.use("/uploads", express.static(path.join(__dirname, "uploads")));

// Serve the frontend from the same process as the API.
const frontendPath = path.join(__dirname, "public");
app.use(express.static(frontendPath));

// Routes
app.use("/api/auth", authRoutes);
app.use("/api/complaints", complaintRoutes);
app.use("/api/watch", watchRoutes);
app.use("/api/stats", statsRoutes);
app.use("/api/search", searchRoutes);
app.use("/api/cases", caseRoutes);
app.use("/api/cyber", cyberRoutes);
app.use("/api/feedback", feedbackRoutes);
app.use("/api/cctv", cctvRoutes);
app.use("/api/sos", sosRoutes);
app.use("/api/health", healthRoutes);
app.use("/api/alerts", alertsRoutes);
app.use("/api/hotspots", hotspotRoutes);

app.get("/", (req, res) => {
  res.sendFile(path.join(frontendPath, "index.html"));
});

const PORT = process.env.PORT || 5001;

const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

app.set("socketio", io);

io.on("connection", (socket) => {
  console.log("Client connected to socket:", socket.id);
  
  socket.on("join", (room) => {
    socket.join(room);
    console.log(`Socket ${socket.id} joined room: ${room}`);
  });
  
  socket.on("disconnect", () => {
    console.log("Client disconnected:", socket.id);
  });
});

mongoose
  .connect(process.env.MONGO_URI || "mongodb://127.0.0.1:27017/crime_ai")
  .then(() => {
    console.log("Connected to MongoDB!");
    server.listen(PORT, () => console.log(`Node Server is running on port ${PORT}`));
  })
  .catch((err) => console.log("Failed to connect to MongoDB", err));

module.exports = app;
