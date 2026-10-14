const express = require("express");
const router = express.Router();
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const { authMiddleware, requireAuth } = require("../middlewares/auth");
const PhysicalComplaint = require("../models/PhysicalComplaint");
const CyberComplaint = require("../models/CyberComplaint");
const Alert = require("../models/Alert");
const ai = require("../utils/ai");

// Configure Multer for evidence upload
const uploadDir = path.join(__dirname, "../uploads");
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        cb(null, `${Date.now()}-${file.originalname}`);
    }
});

const upload = multer({
    storage,
    limits: { fileSize: 50 * 1024 * 1024 }, // 50MB limit
    fileFilter: (req, file, cb) => {
        const filetypes = /jpeg|jpg|png|gif|webp|mp4|mov|avi|mkv/i;
        const mimetype = filetypes.test(file.mimetype);
        const extname = filetypes.test(path.extname(file.originalname));
        if (mimetype && extname) {
            return cb(null, true);
        }
        cb(new Error("Error: Only images and videos are allowed!"));
    }
});

// POST /api/complaints
router.post("/", authMiddleware, upload.array("images_videos", 10), async (req, res) => {
    try {
        const {
            title,
            desc,
            category,
            phone,
            anonymous,
            latitude,
            longitude,
            address,
            state,
            district,
            city,
            pincode
        } = req.body;

        const isAnon = anonymous === "true" || anonymous === true;

        if (!req.user && !isAnon) {
            return res.status(401).json({ error: "Unauthorized. Please log in first." });
        }

        // Validate basic text fields
        if (!title || !desc || !category) {
            return res.status(400).json({ error: "Missing required fields (title, desc, category)." });
        }

        // Validate GPS coordinates (Optional fallback)
        let lat = parseFloat(latitude);
        let lon = parseFloat(longitude);
        if (isNaN(lat) || isNaN(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180 || (lat === 0 && lon === 0)) {
            lat = null;
            lon = null;
        }

        // Validate required address fields (Optional fallback)
        const finalAddress = address || "Not Provided";
        const finalState = state || "Not Provided";
        const finalDistrict = district || "Not Provided";

        // Map uploaded files to URLs
        const files = req.files || [];
        const fileUrls = files.map(file => `/uploads/${file.filename}`);

        // Run AI classification check
        const finalCategory = ai.classifyCrime(desc);
        // Use auto classification if user category is "Other", or check if it matches "Cyber Crime"
        const isCyber = category.toLowerCase() === "cyber crime" || finalCategory.toLowerCase() === "cyber crime";
        const matchedCategory = isCyber ? "Cyber Crime" : (category || finalCategory);

        // Run AI analysis details
        const severity = ai.detectSeverity(desc, matchedCategory);
        const priority = ai.suggestPriority(desc, matchedCategory);
        const keywords = ai.extractKeywords(desc);
        const complaintId = `CMP-${Date.now()}`;

        // Run duplicate checker
        const duplicateCheck = await ai.detectDuplicate(desc, matchedCategory, lat, lon);

        let savedComplaint;

        if (isCyber) {
            // Route to Cyber Complaints Collection
            const cyberObj = new CyberComplaint({
                complaint_id: complaintId,
                user_id: req.user ? req.user.id : null,
                crime_type: "Cyber Crime",
                title,
                description: desc,
                phone: phone || "Not Provided",
                anonymous: isAnon,
                images_videos: fileUrls,
                latitude: lat,
                longitude: lon,
                address: finalAddress,
                state: finalState,
                district: finalDistrict,
                city: city || "Unknown",
                pincode: pincode || "Unknown",
                status: "New",
                ai_analysis: {
                    severity,
                    confidence: 0.85,
                    keywords,
                    suggested_priority: priority,
                    is_duplicate: duplicateCheck.isDuplicate,
                    duplicate_of: duplicateCheck.duplicateOf
                }
            });
            savedComplaint = await cyberObj.save();
        } else {
            // Route to Physical Complaints Collection
            const physicalObj = new PhysicalComplaint({
                complaint_id: complaintId,
                user_id: req.user ? req.user.id : null,
                crime_type: matchedCategory,
                title,
                description: desc,
                phone: phone || "Not Provided",
                anonymous: isAnon,
                images_videos: fileUrls,
                latitude: lat,
                longitude: lon,
                address: finalAddress,
                state: finalState,
                district: finalDistrict,
                city: city || "Unknown",
                pincode: pincode || "Unknown",
                status: "New",
                ai_severity: severity,
                assigned_officer: "None"
            });
            savedComplaint = await physicalObj.save();
        }

        // Create notification alert
        const alertMsg = `New ${severity}-severity ${matchedCategory} complaint reported in ${finalDistrict}, ${finalState}.`;
        const alert = new Alert({ message: alertMsg, type: isCyber ? "Cybercrime" : "Complaint" });
        await alert.save();

        // Socket.io Real-Time Update Trigger
        if (req.app.get("socketio")) {
            const io = req.app.get("socketio");
            // Notify role-specific rooms
            if (isCyber) {
                io.to("analysts").emit("newCyberComplaint", savedComplaint);
                io.to("officers").emit("newPhysicalComplaint", savedComplaint);
            } else {
                io.to("officers").emit("newPhysicalComplaint", savedComplaint);
            }
            // If user logged in, notify them about their own submission success
            if (req.user) {
                io.to(req.user.id).emit("complaintStatusChanged", {
                    complaint_id: complaintId,
                    status: "New",
                    message: "Your complaint was received."
                });
            }
        }

        res.status(201).json({
            success: true,
            message: "Complaint submitted successfully.",
            data: savedComplaint
        });

    } catch (err) {
        console.error("Complaint Submission Error:", err);
        res.status(500).json({ error: "Server error during complaint submission." });
    }
});

// GET /api/complaints
router.get("/", requireAuth, async (req, res) => {
    try {
        const { state, district, city, crime_type, status } = req.query;
        const role = req.user.role;

        let query = {};

        if (role === "citizen") {
            // Citizens can only view their own complaints (physical + cyber)
            const physicals = await PhysicalComplaint.find({ user_id: req.user.id }).populate("user_id", "name").sort({ created_date: -1 });
            const cybers = await CyberComplaint.find({ user_id: req.user.id }).populate("user_id", "name").sort({ created_date: -1 });
            
            // Format to match dashboard UI expectations
            const merged = [
                ...physicals.map(p => ({
                    id: p.complaint_id,
                    _id: p._id,
                    category: p.crime_type,
                    district: p.district,
                    title: p.title,
                    desc: p.description,
                    phone: p.phone || "Not Provided",
                    reported_by: p.anonymous ? "Anonymous" : (p.user_id ? p.user_id.name : "Citizen"),
                    ai_severity: "N/A",
                    status: p.status,
                    assigned_officer: p.assigned_officer,
                    time: p.created_date,
                    latitude: p.latitude,
                    longitude: p.longitude,
                    address: p.address,
                    images_videos: p.images_videos
                })),
                ...cybers.map(c => ({
                    id: c.complaint_id,
                    _id: c._id,
                    category: c.crime_type,
                    district: c.district,
                    title: c.title,
                    desc: c.description,
                    phone: c.phone || "Not Provided",
                    reported_by: c.anonymous ? "Anonymous" : (c.user_id ? c.user_id.name : "Citizen"),
                    ai_severity: c.ai_analysis?.severity || "Low",
                    status: c.status,
                    assigned_officer: "N/A",
                    time: c.created_date,
                    latitude: c.latitude,
                    longitude: c.longitude,
                    address: c.address,
                    images_videos: c.images_videos
                }))
            ].sort((a, b) => new Date(b.time) - new Date(a.time));

            return res.status(200).json({ rows: merged });
        }

        if (role === "officer") {
            // Officers only view Physical complaints
            if (state) query.state = { $regex: state, $options: "i" };
            if (district) query.district = { $regex: district, $options: "i" };
            if (city) query.city = { $regex: city, $options: "i" };
            if (status) {
                query.status = status;
            } else {
                query.status = { $nin: ["Solved", "Resolved", "Closed", "solved", "resolved", "closed"] };
            }

            let physicalQuery = { ...query };
            if (crime_type) {
                physicalQuery.crime_type = { $regex: crime_type, $options: "i" };
            }

            const physicals = await PhysicalComplaint.find(physicalQuery).populate("user_id", "name").sort({ created_date: -1 }).limit(100);

            const rows = physicals.map(p => ({
                id: p.complaint_id,
                _id: p._id,
                category: p.crime_type,
                district: p.district,
                title: p.title,
                desc: p.description,
                phone: p.phone || "Not Provided",
                reported_by: p.anonymous ? "Anonymous" : (p.user_id ? p.user_id.name : "Citizen"),
                ai_severity: p.ai_severity || "Low",
                status: p.status,
                assigned_officer: p.assigned_officer,
                time: p.created_date,
                latitude: p.latitude,
                longitude: p.longitude,
                address: p.address,
                images_videos: p.images_videos
            }));
            
            return res.status(200).json({ rows });
        }

        if (role === "analyst") {
            // Analysts only view Cyber complaints
            if (state) query.state = { $regex: state, $options: "i" };
            if (district) query.district = { $regex: district, $options: "i" };
            if (city) query.city = { $regex: city, $options: "i" };
            if (status) query.status = status;

            let cyberQuery = { ...query };
            if (crime_type) {
                cyberQuery.crime_type = { $regex: crime_type, $options: "i" };
            }

            const cybers = await CyberComplaint.find(cyberQuery).populate("user_id", "name").sort({ created_date: -1 }).limit(100);

            const rows = cybers.map(c => ({
                id: c.complaint_id,
                _id: c._id,
                category: c.crime_type,
                district: c.district,
                title: c.title,
                desc: c.description,
                phone: c.phone || "Not Provided",
                reported_by: c.anonymous ? "Anonymous" : (c.user_id ? c.user_id.name : "Citizen"),
                ai_severity: c.ai_analysis?.severity || "Low",
                status: c.status,
                assigned_officer: "N/A",
                time: c.created_date,
                latitude: c.latitude,
                longitude: c.longitude,
                address: c.address,
                images_videos: c.images_videos,
                ai_analysis: c.ai_analysis
            }));
            
            return res.status(200).json({ rows });
        }

        if (role === "admin") {
            // Admin can see both
            const physicals = await PhysicalComplaint.find().populate("user_id", "name").sort({ created_date: -1 });
            const cybers = await CyberComplaint.find().populate("user_id", "name").sort({ created_date: -1 });
            
            const merged = [
                ...physicals.map(p => ({
                    id: p.complaint_id,
                    _id: p._id,
                    category: p.crime_type,
                    district: p.district,
                    title: p.title,
                    desc: p.description,
                    phone: p.phone || "Not Provided",
                    reported_by: p.anonymous ? "Anonymous" : (p.user_id ? p.user_id.name : "Citizen"),
                    status: p.status,
                    assigned_officer: p.assigned_officer,
                    time: p.created_date,
                    latitude: p.latitude,
                    longitude: p.longitude,
                    address: p.address
                })),
                ...cybers.map(c => ({
                    id: c.complaint_id,
                    _id: c._id,
                    category: c.crime_type,
                    district: c.district,
                    title: c.title,
                    desc: c.description,
                    phone: c.phone || "Not Provided",
                    reported_by: c.anonymous ? "Anonymous" : (c.user_id ? c.user_id.name : "Citizen"),
                    status: c.status,
                    assigned_officer: "N/A",
                    time: c.created_date,
                    latitude: c.latitude,
                    longitude: c.longitude,
                    address: c.address
                }))
            ].sort((a, b) => new Date(b.time) - new Date(a.time));

            return res.status(200).json({ rows: merged });
        }

        res.status(403).json({ error: "Access denied." });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Server error" });
    }
});

// POST /api/complaints/update-status
router.post("/update-status", requireAuth, async (req, res) => {
    try {
        const { id, status, remarks, assigned_officer } = req.body;
        const role = req.user.role;

        if (role !== "officer" && role !== "admin") {
            return res.status(403).json({ error: "Forbidden. Only law enforcement can update status." });
        }

        // Try physical first, then cyber
        let complaint = await PhysicalComplaint.findOne({ complaint_id: id });
        let isCyber = false;

        if (!complaint) {
            complaint = await CyberComplaint.findOne({ complaint_id: id });
            if (complaint) isCyber = true;
        }

        if (!complaint && id && /^[0-9a-fA-F]{24}$/.test(id)) {
            complaint = await PhysicalComplaint.findById(id);
            if (!complaint) {
                complaint = await CyberComplaint.findById(id);
                if (complaint) isCyber = true;
            }
        }

        if (!complaint) {
            return res.status(404).json({ error: "Complaint not found." });
        }

        complaint.status = status;
        if (remarks) complaint.description += `\n[Remark by Officer]: ${remarks}`;
        if (!isCyber && assigned_officer) {
            complaint.assigned_officer = assigned_officer;
        }

        await complaint.save();

        // Broadcast to citizen
        if (req.app.get("socketio")) {
            const io = req.app.get("socketio");
            const alertMsg = `Complaint ${id} status updated to: ${status}`;
            if (complaint.user_id) {
                io.to(complaint.user_id.toString()).emit("complaintStatusChanged", {
                    complaint_id: id,
                    status: status,
                    message: alertMsg
                });
            }
        }

        res.status(200).json({ success: true, data: complaint });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Server error" });
    }
});

module.exports = router;
