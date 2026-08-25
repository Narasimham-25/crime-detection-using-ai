const PhysicalComplaint = require("../models/PhysicalComplaint");
const CyberComplaint = require("../models/CyberComplaint");

// Simple stopwords list for keyword extraction
const STOPWORDS = new Set([
  "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "arent", "as", "at",
  "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "cant", "cannot", "could",
  "did", "didnt", "do", "does", "doesnt", "doing", "dont", "down", "during", "each", "few", "for", "from", "further",
  "had", "hadnt", "has", "hasnt", "have", "havent", "having", "he", "hed", "hell", "hes", "her", "here", "heres",
  "hers", "herself", "him", "himself", "his", "how", "hows", "i", "id", "ill", "im", "ive", "if", "in", "into",
  "is", "isnt", "it", "its", "itself", "lets", "me", "more", "most", "mustnt", "my", "myself", "no", "nor", "not",
  "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
  "same", "shant", "she", "shed", "shell", "shes", "should", "shouldnt", "so", "some", "such", "than", "that",
  "thats", "the", "their", "theirs", "them", "themselves", "then", "there", "theres", "these", "they", "theyd",
  "theyll", "theyre", "theyve", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
  "wasnt", "we", "wed", "well", "were", "weve", "werent", "what", "whats", "when", "whens", "where", "wheres",
  "which", "while", "who", "whos", "whom", "why", "whys", "with", "wont", "would", "wouldnt", "you", "youd",
  "youll", "youre", "youve", "your", "yours", "yourself", "yourselves"
]);

/**
 * Automatically classifies the crime based on the description text.
 */
function classifyCrime(description) {
  const desc = description.toLowerCase();
  
  const keywords = {
    "Cyber Crime": ["hack", "online", "phish", "email", "scam", "account", "fraud", "internet", "website", "cyber", "computer", "profile", "upi", "bank transfer", "crypto", "ransomware", "virus", "otp"],
    "Theft": ["steal", "theft", "stolen", "pocket", "wallet", "bag", "shoplift", "bicycle", "bike", "purse", "chain snatching"],
    "Robbery": ["rob", "robbery", "mugged", "gunpoint", "knife", "threat", "store robbery", "bank robbery", "heist", "looted"],
    "Assault": ["beat", "hit", "punch", "slap", "fight", "assault", "attack", "violence", "abused", "clash"],
    "Murder": ["kill", "murder", "dead", "shoot", "shot", "stab", "homicide", "corpse", "body", "murdered", "death"],
    "Domestic Violence": ["husband", "wife", "abuse", "beat wife", "domestic", "family violence", "dowry", "marital", "spouse"],
    "Missing Person": ["missing", "lost child", "not returned", "disappear", "ran away", "kidnap", "abducted"],
    "Road Accident": ["accident", "crash", "car", "bike", "hit and run", "collision", "truck", "road", "injured in crash"],
    "Drug Crime": ["drugs", "drug", "cocaine", "weed", "heroin", "dealer", "peddler", "sell drugs", "marijuana", "substance", "narcotics"]
  };

  for (const [category, words] of Object.entries(keywords)) {
    if (words.some(word => desc.includes(word))) {
      return category;
    }
  }
  
  return "Other";
}

/**
 * Automatically detects the severity level of a crime.
 */
function detectSeverity(description, category) {
  const desc = description.toLowerCase();
  const cat = category.toLowerCase();
  
  const criticalWords = ["murder", "kill", "shoot", "gun", "hostage", "stab", "homicide", "death", "rape", "critical", "bomb", "terror"];
  const highWords = ["assault", "rob", "robbery", "kidnap", "abducted", "domestic violence", "drugs", "trafficking", "accident", "injured"];
  
  if (criticalWords.some(w => desc.includes(w) || cat.includes(w))) {
    return "Critical";
  }
  
  if (highWords.some(w => desc.includes(w) || cat.includes(w))) {
    return "High";
  }
  
  if (cat.includes("cyber") || desc.includes("fraud") || desc.includes("scam") || desc.includes("theft") || desc.includes("steal")) {
    return "Medium";
  }
  
  return "Low";
}

/**
 * Suggests priority level.
 */
function suggestPriority(description, category) {
  return detectSeverity(description, category); // Can map 1:1 or logic extensions
}

/**
 * Extracts key terms from the description.
 */
function extractKeywords(description) {
  if (!description) return [];
  const words = description
    .toLowerCase()
    .replace(/[^\w\s]/g, "")
    .split(/\s+/);
  
  const uniqueKeywords = new Set();
  for (const w of words) {
    if (w.length > 3 && !STOPWORDS.has(w)) {
      uniqueKeywords.add(w);
    }
  }
  
  return Array.from(uniqueKeywords).slice(0, 10);
}

/**
 * Computes Jaccard Similarity of two token sets.
 */
function getSimilarity(text1, text2) {
  const set1 = new Set(text1.toLowerCase().split(/\s+/));
  const set2 = new Set(text2.toLowerCase().split(/\s+/));
  
  const intersection = new Set([...set1].filter(x => set2.has(x)));
  const union = new Set([...set1, ...set2]);
  
  return intersection.size / union.size;
}

/**
 * Haversine formula to compute distance in KM.
 */
function getDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371; // Radius of the Earth in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Detects duplicate complaints in the DB.
 */
async function detectDuplicate(description, category, latitude, longitude) {
  const isCyber = category.toLowerCase() === "cyber crime";
  const Model = isCyber ? CyberComplaint : PhysicalComplaint;
  
  // Fetch existing complaints of the same type/category
  const list = await Model.find({ status: { $ne: "Closed" } });
  
  for (const item of list) {
    // Check coordinate distance (within 2 km)
    const dist = getDistanceKm(latitude, longitude, item.latitude, item.longitude);
    if (dist <= 2.0) {
      // Check description similarity
      const similarity = getSimilarity(description, item.description);
      if (similarity >= 0.35) {
        return { isDuplicate: true, duplicateOf: item.complaint_id };
      }
    }
  }
  
  return { isDuplicate: false, duplicateOf: "" };
}

/**
 * Predicts hotspot zones dynamically based on complaints count in districts.
 */
async function predictHotspots() {
  const physicals = await PhysicalComplaint.find();
  const cybers = await CyberComplaint.find();
  
  const districts = {};
  
  const processItem = (item) => {
    const key = `${item.district}, ${item.state}`;
    if (!districts[key]) {
      districts[key] = {
        district: item.district,
        state: item.state,
        count: 0,
        crime_types: new Set(),
        latitude: item.latitude,
        longitude: item.longitude
      };
    }
    districts[key].count++;
    districts[key].crime_types.add(item.crime_type);
  };
  
  physicals.forEach(processItem);
  cybers.forEach(processItem);
  
  const hotspots = Object.values(districts)
    .map(d => ({
      ...d,
      crime_types: Array.from(d.crime_types)
    }))
    .sort((a, b) => b.count - a.count);
    
  return hotspots;
}

module.exports = {
  classifyCrime,
  detectSeverity,
  suggestPriority,
  extractKeywords,
  detectDuplicate,
  predictHotspots
};
