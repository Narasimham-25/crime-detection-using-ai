const express = require("express");
const router = express.Router();
const User = require("../models/User");
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");

// POST /api/auth/register
router.post("/register", async (req, res) => {
  try {
    const { name, email, password, role } = req.body;
    if (!name || !email || !password) return res.status(400).json({ error: "Missing fields" });

    const existingUser = await User.findOne({ email: email.toLowerCase() });
    if (existingUser) return res.status(400).json({ error: "Email already registered" });

    const hashedPassword = await bcrypt.hash(password, 10);
    const user = new User({
      name,
      email: email.toLowerCase(),
      password: hashedPassword,
      role: role || "citizen",
    });
    await user.save();

    const token = jwt.sign({ id: user._id, role: user.role }, process.env.JWT_SECRET || "default_secret", { expiresIn: "1d" });
    
    res.status(201).json({ id: user._id, name: user.name, email: user.email, role: user.role, token });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
});

// POST /api/auth/login
router.post("/login", async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email: email.toLowerCase() });
    console.log('Login Attempt -> User found: ', !!user);
    
    if (!user) return res.status(401).json({ error: "Invalid credentials" });

    const isMatch = await bcrypt.compare(password, user.password);
    console.log('Password hash match: ', isMatch);
    if (!isMatch) return res.status(401).json({ error: "Invalid credentials" });

    const token = jwt.sign({ id: user._id, role: user.role }, process.env.JWT_SECRET || "default_secret", { expiresIn: "1d" });
    res.status(200).json({ id: user._id, name: user.name, email: user.email, role: user.role, token });

  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
});

// POST /api/admin/login
router.post("/admin/login", async (req, res) => {
    // Simple mock admin for now to match exactly the previous Python logic functionality.
    const { pin } = req.body;
    if (pin === "4321") {
        const token = jwt.sign({ id: "mock-admin-id", role: "admin" }, process.env.JWT_SECRET || "default_secret", { expiresIn: "1d" });
        return res.status(200).json({ id: "ADMIN-1", name: "Control Room Admin", role: "admin", token });
    }
    return res.status(401).json({ error: "Invalid admin PIN" });
});

module.exports = router;
