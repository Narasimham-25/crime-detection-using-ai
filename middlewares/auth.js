const jwt = require("jsonwebtoken");

function authMiddleware(req, res, next) {
    const authHeader = req.headers["authorization"];
    const token = authHeader && authHeader.split(" ")[1];
    if (!token) {
        req.user = null;
        return next(); // Let endpoints decide if auth is mandatory
    }
    
    jwt.verify(token, process.env.JWT_SECRET || "default_secret", (err, user) => {
        if (err) req.user = null;
        else req.user = user;
        next();
    });
}

function requireAuth(req, res, next) {
    authMiddleware(req, res, () => {
        if (!req.user) {
            return res.status(401).json({ error: "Unauthorized. Please log in first." });
        }
        next();
    });
}

function requireRole(roles) {
    return (req, res, next) => {
        authMiddleware(req, res, () => {
            if (!req.user) {
                return res.status(401).json({ error: "Unauthorized. Please log in first." });
            }
            if (!roles.includes(req.user.role)) {
                return res.status(403).json({ error: "Forbidden. Access restricted." });
            }
            next();
        });
    };
}

module.exports = { authMiddleware, requireAuth, requireRole };
