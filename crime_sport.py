# crime_hotspot_alert.py
# Detect top crime hotspot daily, show district + crime type, nearest police station,
# export reports, and optionally start a local live server.

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import time
import xml.etree.ElementTree as ET

# -----------------------------
# 0. Indian districts (simplified example, add all 788 districts for full coverage)
# -----------------------------
INDIAN_STATES_DISTRICTS = {
    "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna",
                    "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam",
                    "Vizianagaram", "West Godavari", "YSR Kadapa"],
    "Arunachal Pradesh": ["Tawang", "West Kameng", "East Kameng", "Papum Pare", "Lower Subansiri",
                        "Kurung Kumey", "Kra Daadi", "Lower Siang", "Upper Siang", "East Siang",
                        "Siang", "West Siang", "Upper Subansiri", "Leparada", "Namsai",
                        "Lohit", "Lower Dibang Valley", "Anjaw", "Changlang", "Tirap",
                        "Longding"],
    "Assam": ["Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Charaideo",
            "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao",
            "Goalpara", "Golaghat", "Hailakandi", "Hojai", "Jorhat", "Kamrup",
            "Kamrup Metropolitan", "Karbi Anglong", "Karimganj", "Kokrajhar",
            "Lakhimpur", "Majuli", "Morigaon", "Nagaon", "Nalbari", "Sivasagar",
            "Sonitpur", "South Salmara Mankachar", "Tinsukia", "Udalguri",
            "West Karbi Anglong"],
    "Bihar": ["Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur",
            "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya",
            "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Khagaria",
            "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani", "Munger",
            "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas",
            "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi",
            "Siwan", "Supaul", "Vaishali"],
    "Chhattisgarh": ["Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara",
                    "Bijapur", "Bilaspur", "Dantewada", "Dhamtari", "Durg",
                    "Gariaband", "Janjgir Champa", "Jashpur", "Kabirdham", "Kanker",
                    "Kawardha", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur",
                    "Raigarh", "Raipur", "Rajnandgaon", "Sukma", "Surajpur", "Surguja"],
    "Goa": ["North Goa", "South Goa"],
    "Gujarat": ["Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch",
                "Bhavnagar", "BOTAD", "Chhota Udaipur", "Dahod", "Dang", "Gandhinagar",
                "Gir Somnath", "Jamnagar", "Junagadh", "Kachchh", "Kheda", "Mahisagar",
                "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan",
                "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi",
                "Vadodara", "Valsad"],
    "Haryana": ["Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad",
                "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal",
                "Kurukshetra", "Mahendragarh", "Mewat", "Palwal", "Panchkula",
                "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"],
    "Himachal Pradesh": ["Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur",
                        "Kullu", "Lahul & Spiti", "Mandi", "Shimla", "Sirmaur",
                        "Solan", "Una"],
    "Jharkhand": ["Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum",
                "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara",
                "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu",
                "Ramgarh", "Ranchi", "Sahibganj", "Seraikela-Kharsawan", "Simdega",
                "West Singhbhum"],
    "Karnataka": ["Bengaluru Urban", "Bengaluru Rural", "Bagalkot", "Ballari",
                "Belagavi", "Chamarajanagar", "Chikkaballapur", "Chikkamagaluru",
                "Chitradurga", "Dakshina Kannada", "Davangere", "Dharwad", "Gadag",
                "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal",
                "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga",
                "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir"],
    "Kerala": ["Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod",
            "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad",
            "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"],
    "Madhya Pradesh": ["Agar Malwa", "Alirajpur", "Anuppur", "Ashok Nagar", "Balaghat",
                        "Barwani", "Betul", "Bhind", "Bhopal", "Burhanpur", "Chhatarpur",
                        "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
                        "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur",
                        "Jhabua", "Katni", "Khandwa", "Khargone", "Mandla", "Mandsaur",
                        "Morena", "Narsinghpur", "Neemuch", "Panna", "Raisen", "Rajgarh",
                        "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni",
                        "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli",
                        "Tikamgarh", "Ujjain", "Umaria", "Vidisha"],
    "Maharashtra": ["Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed",
                    "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli",
                    "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur",
                    "Mumbai", "Nagpur", "Nanded", "Nandurbar",
                    "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad",
                    "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur",
                    "Thane", "Wardha", "Washim", "Yavatmal"],
    "Manipur": ["Bishnupur", "Chandel", "Churachandpur", "Imphal East",
                "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi",
                "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal",
                "Thoubal", "Ukhrul"],
    "Meghalaya": ["East Garo Hills", "East Jaintia Hills", "East Khasi Hills",
                "North Garo Hills", "Ri Bhoi", "South Garo Hills",
                "South West Garo Hills", "South West Khasi Hills", "West Garo Hills",
                "West Jaintia Hills", "West Khasi Hills"],
    "Mizoram": ["Aizawl", "Champhai", "Kolasib", "Lawngtlai", "Lunglei",
                "Mamit", "Saiha", "Serchhip"],
    "Nagaland": ["Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung",
                "Mon", "Peren", "Phek", "Tuensang", "Wokha", "Zunheboto"],
    "Odisha": ["Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh",
            "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur",
            "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar",
            "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur",
            "Nuapada", "Puri", "Rayagada", "Sambalpur", "Sonepur", "Sundargarh"],
    "Punjab": ["Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib",
            "Fazilka", "Firozpur", "Gurdaspur", "Hoshiarpur", "Jalandhar",
            "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar", "Nawanshahr",
            "Pathankot", "Patiala", "Rupnagar", "S.A.S. Nagar", "Sangrur",
            "Tarn Taran"],
    "Rajasthan": ["Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur",
                "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa",
                "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer",
                "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota",
                "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur",
                "Sikar", "Sirohi", "Tonk", "Udaipur"],
    "Sikkim": ["East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim"],
    "Tamil Nadu": ["Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
                "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kancheepuram",
                "Karur", "Krishnagiri", "Madurai", "Nagapattinam", "Namakkal",
                "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet",
                "Salem", "Sivaganga", "Tenkasi", "Thanjavur", "Theni", "Thoothukudi",
                "Tiruchirappalli", "Tirunelveli", "Tirupattur", "Tiruppur", "Tiruvallur",
                "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar"],
    "Telangana": ["Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial",
                "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy",
                "Karimnagar", "Khammam", "Komaram Bheem Asifabad", "Mahabubabad",
                "Mahbubnagar", "Mancherial", "Medak", "Medchal Malkajgiri", "Nagarkurnool",
                "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli",
                "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet",
                "Suryapet", "Vikarabad", "Wanaparthy", "Warangal Rural", "Warangal Urban",
                "Yadadri Bhuvanagiri"],
    "Tripura": ["Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura",
                "Unakoti", "West Tripura"],
    "Uttar Pradesh": ["Agra", "Aligarh", "Allahabad/Prayagraj", "Ambedkar Nagar", "Amethi",
                    "Amroha", "Auraiya", "Ayodhya", "Azamgarh", "Baghpat", "Bahraich",
                    "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti",
                    "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot",
                    "Deoria", "Etah", "Etawah", "Farrukhabad", "Fatehpur", "Firozabad",
                    "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur",
                    "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi",
                    "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi",
                    "Kushinagar", "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj",
                    "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur",
                    "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Rae Bareli",
                    "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur",
                    "Shamli", "Shravasti", "Siddharth Nagar", "Sitapur", "Sonbhadra",
                    "Sultanpur", "Unnao", "Varanasi"],
    "Uttarakhand": ["Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun",
                    "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh",
                    "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi"],
    "West Bengal": ["Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur",
                    "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram",
                    "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas",
                    "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur",
                    "Purulia", "South 24 Parganas", "Uttar Dinajpur"],
    # UTs
    "Andaman and Nicobar Islands": ["Nicobar", "North and Middle Andaman", "South Andaman"],
    "Chandigarh": ["Chandigarh"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Dadra and Nagar Haveli", "Daman", "Diu"],
    "Delhi": ["Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi",
            "North West Delhi", "Shahdara", "South Delhi", "South East Delhi",
            "South West Delhi", "West Delhi"],
    "Jammu and Kashmir": ["Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda",
                        "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara",
                        "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba",
                        "Shopian", "Srinagar", "Udhampur"],
    "Ladakh": ["Kargil", "Leh"],
    "Lakshadweep": ["Agatti", "Amini", "Androth", "Bangaram", "Bitra", "Chetlat",
                    "Kadmat", "Kiltan", "Kavaratti", "Kalpeni", "Minicoy"],
    "Puducherry": ["Karaikal", "Mahe", "Puducherry", "Yanam"]
}

# -----------------------------
# 1. Crime keywords
# -----------------------------
CRIME_KEYWORDS = [
    "murder", "robbery", "assault", "kidnap", "theft", "rape", "crime",
    "shooting", "attack", "homicide", "burglary"
]

# -----------------------------
# 2. RSS feeds (India news)
# -----------------------------
RSS_FEEDS = [
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml"
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crime hotspot detector with report export and live server")
    parser.add_argument("--top", type=int, default=3, help="Number of top hotspots to show")
    parser.add_argument("--state", type=str, default="", help="Optional state filter")
    parser.add_argument("--extra-keywords", type=str, default="", help="Comma-separated extra keywords")
    parser.add_argument("--output", type=str, default="hotspot_report.json", help="Output JSON report path")
    parser.add_argument("--serve", action="store_true", help="Start a local live server for report files")
    parser.add_argument("--port", type=int, default=8000, help="Live server port")
    parser.add_argument("--radius-km", type=float, default=25.0, help="Nearby police search radius in KM")
    parser.add_argument("--police-limit", type=int, default=5, help="Max nearby police stations to include")
    parser.add_argument("--alert-mentions", type=int, default=2, help="Alert threshold for hotspot mentions")
    parser.add_argument("--watch", action="store_true", help="Continuously refresh data at interval")
    parser.add_argument("--interval", type=int, default=300, help="Refresh interval seconds for --watch")
    parser.add_argument("--control-room-number", type=str, default="112", help="Control room phone number")
    parser.add_argument("--control-room-email", type=str, default="controlroom@citypolice.gov", help="Control room email")
    parser.add_argument("--portal-pin", type=str, default="4321", help="Demo police portal PIN")
    return parser.parse_args()


def fetch_url_text(url: str, timeout: int = 15) -> str:
    req = Request(url, headers={"User-Agent": "CrimeHotspotBot/1.0"})
    with urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def collect_crime_articles(feeds: List[str], keywords: List[str]) -> List[str]:
    all_texts: List[str] = []
    lowered_keywords = [k.lower() for k in keywords]

    for rss_url in feeds:
        try:
            xml_text = fetch_url_text(rss_url)
            root = ET.fromstring(xml_text)
            items = root.findall(".//item")
            if not items:
                items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

            for item in items:
                title = item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or ""
                summary = (
                    item.findtext("description")
                    or item.findtext("summary")
                    or item.findtext("{http://www.w3.org/2005/Atom}summary")
                    or ""
                )
                text = f"{title}. {summary}".strip()
                if text and any(k in text.lower() for k in lowered_keywords):
                    all_texts.append(text)
        except Exception as ex:
            print(f"[WARN] Failed to read feed: {rss_url} ({ex})")

    return all_texts


def detect_mentions(
    all_texts: List[str],
    keywords: List[str],
    state_filter: str = ""
) -> Tuple[Counter, Dict[Tuple[str, str], Set[str]]]:
    mentions: Counter = Counter()  # pyre-ignore
    crime_types_detected: Dict[Tuple[str, str], Set[str]] = {}
    normalized_state_filter = state_filter.strip().lower()

    for text in all_texts:
        text_lower = text.lower()
        detected_crimes = [k for k in keywords if k.lower() in text_lower]

        for state, districts in INDIAN_STATES_DISTRICTS.items():
            if normalized_state_filter and state.lower() != normalized_state_filter:
                continue
            for district in districts:
                if district.lower() in text_lower:
                    key = (state, district)
                    mentions[key] += 1
                    if key not in crime_types_detected:
                        crime_types_detected[key] = set()
                    crime_types_detected[key].update(detected_crimes)

    return mentions, crime_types_detected


HARDCODED_GEOS = {
    "Mumbai": {"lat": "19.0760", "lon": "72.8777", "name": "Mumbai"},
    "New Delhi": {"lat": "28.6139", "lon": "77.2090", "name": "New Delhi"},
    "Bengaluru": {"lat": "12.9716", "lon": "77.5946", "name": "Bengaluru"},
    "Chennai": {"lat": "13.0827", "lon": "80.2707", "name": "Chennai"}
}

def geocode_nominatim(query: str) -> Optional[dict]:
    for city, coords in HARDCODED_GEOS.items():
        if city.lower() in query.lower():
            return coords
    
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={quote_plus(query)}&format=json&limit=1"
        text = fetch_url_text(url, timeout=5)
        rows = json.loads(text)
        return rows[0] if rows else None
    except Exception:
        return None


def google_maps_search_link(query: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"


def google_maps_coord_link(lat: str, lon: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"


def overpass_query(query: str) -> dict:
    url = "https://overpass-api.de/api/interpreter"
    req = Request(
        url,
        data=query.encode("utf-8"),
        headers={"User-Agent": "CrimeHotspotBot/1.0"},
    )
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def nearby_police_stations(district: str, state: str, radius_km: float, limit: int) -> Tuple[List[dict], Optional[dict]]:
    district_loc = geocode_nominatim(f"{district}, {state}, India")
    if not district_loc:
        return [], None

    lat_val = district_loc.get("lat")
    lon_val = district_loc.get("lon")
    if lat_val is None or lon_val is None:
        return [], None

    center_lat = float(lat_val)
    center_lon = float(lon_val)
    radius_m = int(max(1000.0, float(radius_km * 1000)))

    query = f"""
[out:json][timeout:25];
(
  node["amenity"="police"](around:{radius_m},{center_lat},{center_lon});
  way["amenity"="police"](around:{radius_m},{center_lat},{center_lon});
  relation["amenity"="police"](around:{radius_m},{center_lat},{center_lon});
);
out center tags {max(1, limit * 3)};
""".strip()

    stations: List[Dict] = []
    try:
        data = overpass_query(query)
        for element in data.get("elements", []):
            tags = element.get("tags", {}) or {}
            lat = element.get("lat")
            lon = element.get("lon")
            if lat is None or lon is None:
                center = element.get("center") or {}
                lat = center.get("lat")
                lon = center.get("lon")
            if lat is None or lon is None:
                continue

            phone = tags.get("phone") or tags.get("contact:phone") or ""
            website = tags.get("website") or tags.get("contact:website") or ""
            station = {
                "name": tags.get("name", "Police Station"),
                "address": tags.get("addr:full") or tags.get("address") or district,
                "phone": phone,
                "website": website,
                "email": tags.get("email") or tags.get("contact:email") or "",
                "latitude": float(str(lat)),
                "longitude": float(str(lon)),
                "maps_url": google_maps_coord_link(str(lat), str(lon)),
            }
            stations.append(station)
    except Exception as ex:
        print(f"[WARN] Overpass station lookup failed: {ex}")
        fallback = geocode_nominatim(f"police station near {district}, {state}, India")
        if fallback:
            flat = fallback.get("lat")
            flon = fallback.get("lon")
            if flat is not None and flon is not None:
                stations.append(
                    {
                        "name": fallback.get("name", "Police Station"),
                        "address": fallback.get("display_name", district),
                        "phone": "",
                        "website": "",
                        "email": "",
                        "latitude": float(str(flat)),
                        "longitude": float(str(flon)),
                        "maps_url": google_maps_coord_link(str(flat), str(flon)),
                    }
                )

    max_limit = max(1, int(limit))
    stations = stations[:max_limit]
    center_info = {
        "district": district,
        "state": state,
        "latitude": center_lat,
        "longitude": center_lon,
        "maps_url": google_maps_coord_link(str(center_lat), str(center_lon)),
    }
    return stations, center_info


def nearest_police_station_text(police_stations: List[dict]) -> str:
    if not police_stations:
        return "No police station found nearby"
    first = police_stations[0]
    phone = first.get("phone") or "N/A"
    return (
        f"Police Station: {first.get('name', 'Police Station')} | "
        f"Address: {first.get('address', 'N/A')} | "
        f"Phone: {phone} | Coordinates: {first.get('latitude')}, {first.get('longitude')}"
    )


def build_alerts(top_rows: List[dict], previous_top: Optional[dict], threshold: int) -> List[str]:
    alerts: List[str] = []
    if not top_rows:
        return alerts

    top = top_rows[0]
    if top["mentions"] >= threshold:
        alerts.append(
            f"High crime alert: {top['district']}, {top['state']} has {top['mentions']} mentions."
        )

    if previous_top:
        if previous_top.get("district") != top.get("district") or previous_top.get("state") != top.get("state"):
            alerts.append(
                f"Hotspot changed: {previous_top.get('district')}, {previous_top.get('state')} -> {top['district']}, {top['state']}"
            )
        elif top.get("mentions", 0) > previous_top.get("mentions", 0):
            alerts.append(
                f"Escalation alert: {top['district']}, {top['state']} rose to {top['mentions']} mentions."
            )

    if not alerts:
        alerts.append("No critical alert in this cycle.")
    return alerts


def append_alert_log(alerts: List[str], log_path: Path) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    with log_path.open("a", encoding="utf-8") as f:
        for alert in alerts:
            f.write(f"[{timestamp}] {alert}\n")


def compute_category_breakdown(all_texts: List[str], keywords: List[str]) -> Dict[str, int]:
    counts: Dict[str, int] = Counter()
    lowered_keywords = [k.lower() for k in keywords]
    for text in all_texts:
        text_lower = text.lower()
        for keyword in lowered_keywords:
            if keyword in text_lower:
                counts[keyword] += 1
    if not counts:
        return {"crime": 0}
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))


def build_incidents_for_dashboard(top_rows: List[dict]) -> List[dict]:
    incidents: List[dict] = []
    now = datetime.now()
    for row in top_rows:
        mentions = row.get("mentions", 1)
        if mentions >= 4:
            severity = "High"
        elif mentions >= 2:
            severity = "Medium"
        else:
            severity = "Low"

        incidents.append(
            {
                "id": f"INC-{row['rank']}-{row['district'].replace(' ', '').upper()}",
                "district": row["district"],
                "state": row["state"],
                "crime_type": (row.get("crime_types") or ["crime"])[0],
                "severity": severity,
                "time": (now - timedelta(hours=row["rank"] * 2)).isoformat(timespec="minutes"),
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
            }
        )
    return incidents


def default_safety_tips() -> List[dict]:
    return [
        {"title": "Cyber Safety", "content": "Never share OTPs, verify payment links, and enable 2FA on banking apps."},
        {"title": "Home Security", "content": "Install door cameras, use motion lights, and keep emergency contacts visible."},
        {"title": "Fraud Awareness", "content": "Do not trust urgent reward/loan calls; verify via official helplines first."},
        {"title": "Women & Child Safety", "content": "Share live location with trusted contacts when travelling late hours."},
    ]


def emergency_directory(control_room_number: str, control_room_email: str) -> List[dict]:
    return [
        {"service": "Police Control Room", "phone": control_room_number, "email": control_room_email},
        {"service": "Ambulance", "phone": "108", "email": ""},
        {"service": "Fire", "phone": "101", "email": ""},
        {"service": "Women Helpline", "phone": "1091", "email": ""},
        {"service": "Cybercrime Helpline", "phone": "1930", "email": ""},
    ]


def default_cyber_resources() -> Dict[str, List[str]]:
    return {
        "citizen_steps": [
            "Immediately call 1930 for financial fraud freeze request.",
            "Report at cybercrime.gov.in with transaction IDs and screenshots.",
            "Do not delete chats, emails, or SMS evidence.",
            "Change passwords and enable 2-factor authentication on all accounts.",
            "Inform your bank and block compromised cards/wallets right away.",
        ],
        "police_playbook": [
            "Preserve chain of custody for digital evidence and device seizure logs.",
            "Correlate complaints with UPI IDs, mule accounts, and IP intelligence.",
            "Trigger rapid takedown workflow for phishing domains and fake apps.",
            "Issue legal preservation notices to platforms and ISPs.",
            "Escalate cross-state/cross-border cases to cyber coordination units.",
        ],
        "fraud_signals": [
            "Remote screen-share app installation requests.",
            "Urgent KYC update links from unknown senders.",
            "Payment request from fake customer-care/social media handles.",
            "Unexpected OTP/approval popups while on calls.",
            "Promises of instant loan/refund requiring advance fees.",
        ],
        "evidence_checklist": [
            "Transaction reference number / UTR",
            "Phone numbers, email IDs, social handles",
            "Wallet ID / UPI ID / account details",
            "Screenshots, call recordings, chat exports",
            "Device logs and approximate incident timeline",
        ],
    }


def write_outputs(output_json: Path, report_payload: dict) -> Path:
    output_json.write_text(json.dumps(report_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    output_html = output_json.with_suffix(".html")
    top_rows = report_payload.get("top_hotspots", [])
    police_rows = report_payload.get("nearby_police_stations", [])
    incidents = report_payload.get("incidents", [])
    alerts = report_payload.get("alerts", [])
    tips = report_payload.get("safety_tips", [])
    contacts = report_payload.get("emergency_contacts", [])
    categories = report_payload.get("category_breakdown", {})
    portal = report_payload.get("portal", {})
    cyber_resources = report_payload.get("cyber_resources", default_cyber_resources())

    row_html = "\n".join(
        f"<tr><td>{idx + 1}</td><td>{r['district']}</td><td>{r['state']}</td><td>{r['mentions']}</td><td>{', '.join(r['crime_types'])}</td><td><a href=\"{r.get('maps_url', '#')}\" target=\"_blank\">Open Map</a></td></tr>"
        for idx, r in enumerate(top_rows)
    )
    police_html = "\n".join(
        "<tr>"
        f"<td>{idx + 1}</td><td>{p.get('name', 'Police Station')}</td><td>{p.get('address', '')}</td><td>{p.get('phone', '') or 'N/A'}</td><td>{p.get('website', '') or 'N/A'}</td>"
        f"<td><a href=\"{p.get('maps_url', '#')}\" target=\"_blank\">Navigate</a></td>"
        "</tr>"
        for idx, p in enumerate(police_rows)
    )
    incidents_html = "\n".join(
        f"<tr data-type=\"{inc.get('crime_type', '')}\" data-severity=\"{inc.get('severity', '')}\"><td>{inc.get('id', '')}</td><td>{inc.get('district', '')}</td><td>{inc.get('crime_type', '')}</td><td>{inc.get('severity', '')}</td><td>{inc.get('time', '')}</td></tr>"
        for inc in incidents
    )
    alerts_html = "".join(f"<li>{a}</li>" for a in alerts)
    tips_html = "\n".join(
        f"<article class=\"tip\"><h4>{tip.get('title', '')}</h4><p>{tip.get('content', '')}</p></article>"
        for tip in tips
    )
    contacts_html = "\n".join(
        f"<tr><td>{c.get('service', '')}</td><td><a href=\"tel:{c.get('phone', '')}\">{c.get('phone', '')}</a></td><td>{c.get('email', '')}</td></tr>"
        for c in contacts
    )
    citizen_steps_html = "".join(f"<li>{step}</li>" for step in cyber_resources.get("citizen_steps", []))
    police_playbook_html = "".join(f"<li>{step}</li>" for step in cyber_resources.get("police_playbook", []))
    fraud_signals_html = "".join(f"<li>{step}</li>" for step in cyber_resources.get("fraud_signals", []))
    evidence_checklist_html = "".join(f"<li>{step}</li>" for step in cyber_resources.get("evidence_checklist", []))
    category_labels = list(categories.keys())
    category_values = list(categories.values())
    embedded_json = json.dumps(report_payload, ensure_ascii=False).replace("</", "<\\/")
    html = f"""<!doctype html>
<html>
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Crime Command Center</title>
    <style>
        :root {{ --bg:#0b1220; --bg2:#1e1b4b; --panel:rgba(17,24,39,.74); --panel2:rgba(31,41,55,.74); --text:#e5e7eb; --muted:#94a3b8; --accent:#60a5fa; --danger:#ef4444; --warn:#f59e0b; --line:rgba(148,163,184,.35); --shadow:0 14px 35px rgba(2,6,23,.35); --glow1:#38bdf8; --glow2:#22c55e; }}
        body[data-theme="royal"] {{ --bg:#1f1147; --bg2:#3b0764; --panel:rgba(49,24,88,.72); --panel2:rgba(71,31,115,.72); --accent:#f472b6; --line:rgba(244,114,182,.35); --glow1:#a78bfa; --glow2:#f472b6; }}
        body[data-theme="sunset"] {{ --bg:#3f0d12; --bg2:#7f1d1d; --panel:rgba(69,20,22,.72); --panel2:rgba(96,30,32,.72); --accent:#fb923c; --line:rgba(251,146,60,.35); --glow1:#fb923c; --glow2:#f43f5e; }}
        body[data-theme="forest"] {{ --bg:#052e16; --bg2:#14532d; --panel:rgba(6,44,24,.72); --panel2:rgba(20,83,45,.72); --accent:#34d399; --line:rgba(52,211,153,.35); --glow1:#34d399; --glow2:#22d3ee; }}
        * {{ box-sizing:border-box; }}
        body {{ margin:0; font-family:Inter,Segoe UI,Arial,sans-serif; background:linear-gradient(145deg,var(--bg),var(--bg2)); color:var(--text); position:relative; min-height:100vh; }}
        body::before {{ content:""; position:fixed; inset:0; pointer-events:none; background:radial-gradient(35rem 35rem at 12% 16%, color-mix(in srgb, var(--glow1) 30%, transparent), transparent), radial-gradient(30rem 30rem at 84% 18%, color-mix(in srgb, var(--glow2) 28%, transparent), transparent), radial-gradient(25rem 25rem at 50% 85%, color-mix(in srgb, var(--glow1) 24%, transparent), transparent); z-index:-2; }}
        body::after {{ content:""; position:fixed; inset:0; pointer-events:none; background:linear-gradient(145deg,var(--bg),var(--bg2)); opacity:.86; z-index:-1; }}
        .container {{ max-width:1280px; margin:0 auto; padding:18px; }}
        .hero {{ display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; background:linear-gradient(145deg,color-mix(in srgb, var(--panel2) 92%, transparent),color-mix(in srgb, var(--panel) 92%, transparent)); border:1px solid var(--line); border-radius:14px; padding:16px; box-shadow:var(--shadow); backdrop-filter:blur(8px); }}
        .hero h1 {{ margin:0; font-size:28px; }} .muted {{ color:var(--muted); }}
        .topbar {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }}
        .btn, button {{ background:color-mix(in srgb, var(--panel2) 86%, transparent); color:var(--text); border:1px solid var(--line); border-radius:10px; padding:8px 12px; cursor:pointer; transition:transform .15s ease,border-color .15s ease; }}
        .btn:hover, button:hover {{ transform:translateY(-1px); border-color:var(--accent); }}
        .btn-main {{ background:var(--accent); color:#052e16; border:none; font-weight:700; }}
        .grid {{ display:grid; gap:12px; margin-top:12px; }}
        .kpis {{ grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); }}
        .two {{ grid-template-columns:1.25fr 1fr; }}
        .three {{ grid-template-columns:repeat(3,1fr); }}
        .card {{ background:linear-gradient(145deg,color-mix(in srgb, var(--panel) 90%, transparent),color-mix(in srgb, var(--panel2) 90%, transparent)); border:1px solid var(--line); border-radius:14px; padding:14px; box-shadow:var(--shadow); backdrop-filter:blur(6px); }}
        .kpi h4 {{ margin:0; color:var(--muted); font-size:12px; text-transform:uppercase; }}
        .kpi p {{ margin:8px 0 0; font-size:26px; font-weight:700; }}
        .content-layout {{ display:grid; grid-template-columns:260px 1fr; gap:12px; margin-top:12px; align-items:start; }}
        .sidebar {{ position:sticky; top:12px; }}
        .section-content {{ min-width:0; }}
        .tabs {{ display:flex; flex-direction:column; gap:8px; margin:0; }}
        .tab {{ white-space:normal; text-align:left; width:100%; }} .tab.active {{ background:color-mix(in srgb, var(--accent) 32%, transparent); border-color:var(--accent); }}
        .page {{ display:none; }} .page.active {{ display:block; }}
        table {{ width:100%; border-collapse:collapse; }}
        th, td {{ border-bottom:1px solid var(--line); text-align:left; padding:8px; vertical-align:top; }}
        th {{ font-size:12px; color:#93c5fd; text-transform:uppercase; }}
        .controls {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px; }}
        input, select, textarea {{ width:100%; background:color-mix(in srgb, var(--panel2) 84%, transparent); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:8px; }}
        textarea {{ min-height:90px; }}
        .form-grid {{ display:grid; gap:10px; grid-template-columns:repeat(2,1fr); }}
        .full {{ grid-column:1 / -1; }}
        .tip {{ background:var(--panel2); border:1px solid var(--line); border-radius:10px; padding:10px; margin-bottom:8px; }}
        .badge {{ display:inline-block; padding:2px 8px; border-radius:999px; font-size:12px; font-weight:700; }}
        .badge-danger {{ background:rgba(239,68,68,.2); color:#fecaca; }}
        .badge-ok {{ background:rgba(34,197,94,.2); color:#bbf7d0; }}
        #heatmap {{ height:260px; background:#0f172a; border:1px dashed var(--line); border-radius:12px; position:relative; overflow:hidden; }}
        .dot {{ width:16px; height:16px; border-radius:50%; position:absolute; transform:translate(-50%,-50%); opacity:.75; }}
        .dot.High {{ background:#ef4444; }} .dot.Medium {{ background:#f59e0b; }} .dot.Low {{ background:#22c55e; }}
        .audio-btn {{ margin-left:8px; }}
        .cyber-grid {{ display:grid; gap:10px; grid-template-columns:repeat(2,minmax(0,1fr)); margin-top:10px; }}
        .info-box {{ background:linear-gradient(135deg, rgba(30,41,59,.9), rgba(15,23,42,.85)); border:1px solid var(--line); border-radius:12px; padding:10px; }}
        .info-box h4 {{ margin:0 0 6px; color:#c4b5fd; }}
        .info-box ul {{ margin:0; padding-left:18px; }}
        .info-box li {{ margin-bottom:5px; color:#d1d5db; }}
        .status-chip {{ display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; border:1px solid var(--line); background:color-mix(in srgb, var(--panel2) 88%, transparent); }}
        .status-live {{ color:#bbf7d0; border-color:#14532d; background:rgba(34,197,94,.15); }}
        .status-watch {{ color:#fde68a; border-color:#78350f; background:rgba(245,158,11,.15); }}
        .quick-links a {{ margin-right:8px; }}
        @media (max-width:980px) {{
            .content-layout {{ grid-template-columns:1fr; }}
            .sidebar {{ position:static; }}
            .tabs {{ flex-direction:row; overflow:auto; padding-bottom:4px; }}
            .tab {{ white-space:nowrap; width:auto; }}
            .two,.three,.form-grid,.cyber-grid {{ grid-template-columns:1fr; }}
        }}
    </style>
</head>
<body>
    <div id="landingPage" class="landing-container" style="display:flex;">
        <nav class="landing-nav">
            <div class="landing-logo">
                <img src="logo.png" alt="AI Crime Detection Logo">
                <span>AI Crime Shield</span>
            </div>
            <div class="landing-auth">
                <button class="btn-outline" id="btnLandingLogin">Login</button>
                <button class="btn-primary" id="btnLandingRegister">Create Account</button>
            </div>
        </nav>
        <div class="landing-hero">
            <div class="hero-badge">AI-Powered Security System</div>
            <h1><span>Crime Detection</span> using AI</h1>
            <p>Advanced predictive algorithms and real-time community reporting combined into a single, unified dashboard to keep your neighborhoods safe.</p>
            <div class="hero-buttons">
                <button class="btn-primary btn-large" id="btnHeroRegister">Get Started Free</button>
            </div>
        </div>
    </div>
    <div class=\"container\" style=\"display:none;\">
        <section class=\"hero\">
            <div>
                <h1 id=\"titleText\">AI Crime Detection System</h1>
                <p class=\"muted\" id=\"subtitleText\">Generated: {report_payload.get('generated_at')} • Live AI public safety monitoring</p>
            </div>
            <div class=\"topbar\">
                <a class=\"btn btn-main\" href=\"{(top_rows[0].get('maps_url', '#') if top_rows else '#')}\" target=\"_blank\">Open Hotspot Map</a>
                <a class=\"btn\" href=\"{output_json.name}\" download>Download Data</a>
                <button id=\"notifyBtn\">Enable Alerts</button>
                <button id=\"sosBtn\" style=\"background:#dc2626; color:white; font-weight:bold; border:none; padding:8px 16px; border-radius:6px; cursor:pointer;\" title=\"Trigger Emergency SOS\">🚨 SOS Emergency</button>
                <select id="themeSelect" style="width:auto"><option value="midnight">Midnight</option><option value="royal">Royal</option><option value="sunset">Sunset</option><option value="forest">Forest</option></select>
                <select id=\"langSelect\" style=\"width:auto\"><option value=\"en\">English</option><option value=\"hi\">हिन्दी</option><option value=\"te\">తెలుగు</option></select>
                <span id="authControls" style="margin-left:8px;">
                    <button id="btnOpenLogin" class="btn">Login</button>
                    <button id="btnOpenRegister" class="btn">Register</button>
                </span>
                <span id="userControls" style="display:none; margin-left:8px; align-items:center;">
                    <span class="muted" style="margin-right:8px; font-size:14px;">Hi, <span id="lblUserName" style="color:var(--text);font-weight:600;">User</span></span>
                    <button id="btnLogout" class="btn">Logout</button>
                </span>
            </div>
        </section>

        <!-- Auth Modal -->
        <div id="authModal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.8); z-index:999; align-items:center; justify-content:center; backdrop-filter:blur(4px);">
            <div class="card" style="width:360px; max-width:90%; position:relative;">
                <button type="button" id="btnCloseModal" style="position:absolute; top:8px; right:8px; background:transparent; border:none; font-size:18px; color:var(--text);">&times;</button>
                <h3 id="modalTitle" style="margin-top:0;">Login</h3>
                <form id="authForm" class="form-grid">
                    <div id="grpName" class="full" style="display:none;"><label>Name</label><input id="authName" /></div>
                    <div id="grpRole" class="full" style="display:none; margin-top:8px;"><label>Role</label><select id="authRole"><option value="citizen">Citizen</option><option value="officer">Law Enforcement Officer</option><option value="analyst">Crime Data Analyst</option></select></div>
                    <div class="full"><label>Email</label><input type="email" id="authEmail" required /></div>
                    <div class="full"><label>Password</label><input type="password" id="authPassword" required /></div>
                    <div class="full controls" style="margin-top:8px;">
                        <button type="submit" id="btnSubmitAuth" class="btn-main" style="width:100%;">Login</button>
                    </div>
                    <p id="authError" class="status-text error full" style="margin:0; text-align:center;"></p>
                    <div class="auth-divider">or continue with</div>
                    <div class="full" style="display:flex; justify-content:center;">
                        <button type="button" class="btn-google" id="btnGoogleLogin">
                           <img src="https://www.svgrepo.com/show/475656/google-color.svg" alt="Google">
                           Google
                        </button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- Landing Page moved to body -->

        <section class=\"grid kpis\">
            <div class=\"card kpi\"><h4>Total Articles</h4><p>{report_payload.get('total_crime_articles', 0)}</p></div>
            <div class=\"card kpi\"><h4>Hotspots</h4><p>{len(top_rows)}</p></div>
            <div class=\"card kpi\"><h4>Incidents</h4><p>{len(incidents)}</p></div>
            <div class=\"card kpi\"><h4>Alert Status</h4><p><span class=\"badge {'badge-danger' if alerts and alerts[0] != 'No critical alert in this cycle.' else 'badge-ok'}\">{'Active' if alerts and alerts[0] != 'No critical alert in this cycle.' else 'Normal'}</span></p></div>
        </section>

        <div class="content-layout">
        <aside class="sidebar">
            <nav class="tabs" id="tabs">
                <button class="tab active" data-tab="mapping">Crime Hotspot Mapping</button>
                <button class="tab" data-tab="reporting">Incident Reporting</button>
                <button class="tab" data-tab="alerts">Real-Time Alerts</button>
                <button class="tab" data-tab="stats">Statistics Dashboard</button>
                <button class="tab" data-tab="law">Law Enforcement Portal</button>
                <button class="tab" data-tab="community">Community Engagement</button>
                <button class="tab" data-tab="security">Security & Privacy</button>
                <button class="tab" data-tab="advanced">Advanced Features</button>
                <button class="tab" data-tab="accessibility">Accessibility</button>
            </nav>
        </aside>

        <main class="section-content">
        <section id="mapping" class="page active">
            <div class=\"grid two\">
                <div class=\"card\">
                    <h3>Interactive Hotspot Table</h3>
                    <table>
                        <thead><tr><th>#</th><th>District</th><th>State</th><th>Mentions</th><th>Crime Types</th><th>Map</th></tr></thead>
                        <tbody>{row_html}</tbody>
                    </table>
                </div>
                <div class=\"card\">
                    <h3>Heatmap (Crime / Time / Severity Filter)</h3>
                    <div class=\"controls\">
                        <select id=\"fType\"><option value=\"All\">All Crime Types</option></select>
                        <select id=\"fSeverity\"><option value=\"All\">All Severity</option><option>High</option><option>Medium</option><option>Low</option></select>
                        <button id=\"applyHeat\">Apply</button>
                    </div>
                    <div id=\"heatmap\"></div>
                    <p class=\"muted\">Severity color: red=high, amber=medium, green=low</p>
                    <h4>Live Backend + Quick Search</h4>
                    <p id="apiStatusLine" class="status-chip status-watch">API: checking connection...</p>
                    <div class="controls">
                        <input id="quickSearchInput" placeholder="Search complaints/cases/watch/cyber/cctv" />
                        <button id="quickSearchBtn" type="button">Search</button>
                    </div>
                    <table>
                        <thead><tr><th>Source</th><th>Title</th><th>District/Area</th><th>Status</th><th>Time</th></tr></thead>
                        <tbody id="quickSearchBody"><tr><td colspan="5" class="muted">Run a search to see matching records.</td></tr></tbody>
                    </table>
                </div>
            </div>
        </section>

        <section id=\"reporting\" class=\"page\">
            <div class=\"grid two\">
                <div class=\"card\" id=\"cardReportComplaint\">
                    <h3>Secure Online Complaint Form</h3>
                    <form id=\"complaintForm\" class=\"form-grid\">
                        <div><label>Name</label><input id=\"cName\" /></div>
                        <div><label>Phone</label><input id=\"cPhone\" /></div>
                        <div><label>Crime Category</label><select id=\"cCategory\"><option>Theft</option><option>Cybercrime</option><option>Assault</option><option>Fraud</option><option>Other</option></select></div>
                        <div><label>District</label><input id=\"cDistrict\" /></div>
                        <div class=\"full\"><label>Description</label><textarea id=\"cDesc\"></textarea></div>
                        <div><label>Evidence (photo/video)</label><input id=\"cEvidence\" type=\"file\" multiple accept=\"image/*,video/*\" /></div>
                        <div><label><input type=\"checkbox\" id=\"cAnon\" /> Anonymous Reporting</label></div>
                        <div class=\"full controls\"><button type=\"submit\" class=\"btn-main\">Submit Complaint</button></div>
                    </form>
                    <p class=\"muted\">This local demo stores submissions in browser local storage.</p>
                </div>
                <div class=\"card\">
                    <h3>Control Room</h3>
                    <p>Number: <a href=\"tel:{portal.get('control_room_number', '112')}\">{portal.get('control_room_number', '112')}</a></p>
                    <p>Email: <a href=\"mailto:{portal.get('control_room_email', '')}\">{portal.get('control_room_email', '')}</a></p>
                    <h4>Recent Complaints</h4>
                    <div style=\"max-height: 300px; overflow-y: auto; border: 1px solid var(--line); border-radius: 8px; margin-top: 10px;\">
                        <table style=\"width: 100%; border-collapse: collapse;\">
                            <thead style=\"position: sticky; top: 0; background: #111827; z-index: 1;\">
                                <tr><th>ID</th><th>Category</th><th>District</th><th>AI Match</th><th>Reported by</th><th>Time</th></tr>
                            </thead>
                            <tbody id=\"complaintsBody\"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>

        <section id=\"alerts\" class=\"page\">
            <div class=\"grid two\">
                <div class=\"card\">
                    <h3>Nearby Incident Alerts</h3>
                    <ul>{alerts_html}</ul>
                    <p id=\"userLocation\">Detecting your location...</p>
                    <p id=\"distanceToHotspot\">Distance to top hotspot: calculating...</p>
                    <p id=\"nearestStationText\">Nearest station to your live location: calculating...</p>
                </div>
                <div class=\"card\" id=\"cardSosBoard\" style=\"border: 2px solid #ef4444; background: rgba(239,68,68,0.05);\">
                    <h3 style=\"color: #ef4444;\">🚨 Active SOS Emergency Alerts</h3>
                    <table style=\"margin-top: 10px;\">
                        <thead><tr><th>ID</th><th>Time</th><th>Location</th><th>Status</th></tr></thead>
                        <tbody id=\"sosBody\"><tr><td colspan=\"4\" class=\"muted\">Fetching SOS alerts...</td></tr></tbody>
                    </table>
                    <div style=\"margin-top:10px; text-align:right;\">
                        <button id=\"refreshSosBtn\" class=\"btn\" style=\"background:#ef4444; color:white; border:none;\">Refresh Alerts</button>
                    </div>
                </div>
            </div>
            <div class=\"grid two\" style=\"margin-top:20px;\">
                <div class=\"card\">
                    <h3>Urgent SMS / Email Integration</h3>
                    <p>SMS Shortcut: <a href=\"sms:{portal.get('control_room_number', '112')}\">Send SMS to Control Room</a></p>
                    <p>Email Shortcut: <a href=\"mailto:{portal.get('control_room_email', '')}?subject=Urgent%20Crime%20Alert\">Send Email Alert</a></p>
                    <p class=\"muted\">For production, integrate official SMS/email gateways via backend APIs.</p>
                </div>
            </div>
        </section>

        <section id=\"stats\" class=\"page\">
            <div class=\"grid two\">
                <div class=\"card\">
                    <h3>Crime Trend by Category</h3>
                    <canvas id=\"catChart\" width=\"560\" height=\"260\" style=\"max-width:100%;background:#0f172a;border:1px solid var(--line);border-radius:10px\"></canvas>
                </div>
                <div class=\"card\">
                    <h3>Incidents Table</h3>
                    <table>
                        <thead><tr><th>ID</th><th>District</th><th>Type</th><th>Severity</th><th>Time</th></tr></thead>
                        <tbody id=\"incidentsBody\">{incidents_html}</tbody>
                    </table>
                </div>
            </div>
        </section>

        <section id=\"law\" class=\"page\">
            <div class=\"grid two\">
                <div class=\"card\">
                    <h3>Police Portal (Restricted Access)</h3>
                    <div class=\"controls\"><input id=\"portalPin\" type=\"password\" placeholder=\"Enter police PIN\" /><button id=\"portalLogin\">Login</button></div>
                    <p class=\"muted\">Demo PIN for local test: {portal.get('demo_pin', '4321')}</p>
                    <div id=\"portalArea\" style=\"display:none\">
                        <h4>Case Management</h4>
                        <form id=\"caseForm\" class=\"form-grid\">
                            <div><label>Case ID</label><input id=\"caseId\" /></div>
                            <div><label>Officer</label><input id=\"caseOfficer\" /></div>
                            <div><label>Status</label><select id=\"caseStatus\"><option>Open</option><option>Investigating</option><option>Closed</option></select></div>
                            <div><label>Priority</label><select id=\"casePriority\"><option>High</option><option>Medium</option><option>Low</option></select></div>
                            <div class=\"full\"><label>Notes</label><textarea id=\"caseNotes\"></textarea></div>
                            <div class=\"full\"><button class=\"btn-main\" type=\"submit\">Save Case</button></div>
                        </form>
                        <table><thead><tr><th>Case</th><th>Officer</th><th>Status</th><th>Priority</th><th>Updated</th></tr></thead><tbody id=\"casesBody\"></tbody></table>
                    </div>
                </div>
                <div class=\"card\">
                    <h3>Police Database Integration (Adapter)</h3>
                    <p class=\"muted\">Paste JSON from existing police systems to view in dashboard format.</p>
                    <textarea id=\"dbImport\" placeholder='{{"cases": [{{"id": "A1", "status": "Open"}}]}}'></textarea>
                    <div class=\"controls\"><button id=\"importDb\">Import Dataset</button></div>
                    <pre id=\"dbPreview\" class=\"muted\"></pre>
                </div>
            </div>
        </section>

        <section id=\"community\" class=\"page\">
            <div class=\"grid two\">
                <div class=\"card\">
                    <h3>Safety Tips & Awareness</h3>
                    {tips_html}
                </div>
                <div class=\"card\">
                    <h3>Neighborhood Watch</h3>
                    <form id=\"watchForm\" class=\"form-grid\">
                        <div><label>Group Name</label><input id=\"watchName\" /></div>
                        <div><label>Area</label><input id=\"watchArea\" /></div>
                        <div class=\"full\"><label>Plan</label><textarea id=\"watchPlan\"></textarea></div>
                        <div class=\"full\"><button class=\"btn-main\" type=\"submit\">Create Watch Group</button></div>
                    </form>
                    <ul id=\"watchList\"></ul>
                    <h4>Feedback & Suggestions</h4>
                    <textarea id=\"feedbackText\" placeholder=\"Share safety improvements...\"></textarea>
                    <div class=\"controls\"><button id=\"saveFeedback\">Submit Feedback</button></div>
                </div>
            </div>
        </section>

        <section id=\"security\" class=\"page\">
            <div class=\"grid two\">
                <div class=\"card\">
                    <h3>Security & Privacy Controls</h3>
                    <ul>
                        <li>Role-based access for citizens, police, and admins.</li>
                        <li>Data encryption required for production report/evidence storage.</li>
                        <li>Audit logs enabled for complaints, case updates, and portal login.</li>
                    </ul>
                    <p class=\"muted\">Current demo uses browser-local encrypted-like encoding for portability; production should use backend encryption at rest + in transit.</p>
                </div>
                <div class=\"card\">
                    <h3>Audit Logs</h3>
                    <table><thead><tr><th>Action</th><th>Actor</th><th>Time</th></tr></thead><tbody id=\"auditBody\"></tbody></table>
                </div>
            </div>
        </section>

        <section id=\"advanced\" class=\"page\">
            <div class=\"grid two\">
                <div class=\"card\">
                    <h3>AI-Powered Analytics (Forecast)</h3>
                    <p id=\"forecastText\"></p>
                    <div id=\"cardReportCyber\">
                        <h4>Cybercrime Section</h4>
                        <form id=\"cyberForm\" class=\"form-grid\">
                            <div><label>Issue Type</label><select id=\"cyberType\"><option>Phishing</option><option>Hacking</option><option>Online Fraud</option><option>Identity Theft</option></select></div>
                            <div><label>Contact</label><input id=\"cyberContact\" /></div>
                            <div class=\"full\"><label>Details</label><textarea id=\"cyberDetails\"></textarea></div>
                            <div class=\"full\"><button class=\"btn-main\" type=\"submit\">Report Cybercrime</button></div>
                        </form>
                    </div>
                    <div id=\"cardViewCyber\" style=\"display:none; margin-top:20px;\">
                        <h4 style=\"color:#ef4444;\">🚨 Recent Cybercrime Reports</h4>
                        <div style=\"max-height: 300px; overflow-y: auto; border: 1px solid var(--line); border-radius: 8px; margin-top: 10px;\">
                            <table style=\"font-size:12px; width: 100%; border-collapse: collapse;\">
                                <thead style=\"position: sticky; top: 0; background: #111827; z-index: 1;\">
                                    <tr><th>Type</th><th>Contact</th><th>Details</th><th>Report Time</th></tr>
                                </thead>
                                <tbody id=\"cyberBody\"><tr><td colspan=\"4\" class=\"muted\">Loading...</td></tr></tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class=\"card\">
                    <h3>CCTV Integration Console</h3>
                    <div class=\"controls\"><input id=\"cctvUrl\" placeholder=\"Paste CCTV feed URL\" /><button id=\"addCctv\">Add Feed</button></div>
                    <ul id=\"cctvList\"></ul>
                    <h4>Emergency Contact Directory</h4>
                    <table><thead><tr><th>Service</th><th>Phone</th><th>Email</th></tr></thead><tbody>{contacts_html}</tbody></table>
                </div>
            </div>
        </section>

        <section id=\"accessibility\" class=\"page\">
            <div class=\"grid two\">
                <div class=\"card\">
                    <h3>Mobile-Friendly & Multilingual</h3>
                    <p>This portal is responsive and supports English, Hindi, and Telugu labels for key sections.</p>
                    <p class=\"muted\">Use language dropdown in the top bar.</p>
                </div>
                <div class=\"card\">
                    <h3>Voice Assistance</h3>
                    <p>Read summary aloud for visually impaired users.</p>
                    <button id=\"speakBtn\" class=\"audio-btn\">Speak Dashboard Summary</button>
                </div>
            </div>
        </section>
        </main>
        </div>
    </div>

    <script>
        const report = {embedded_json};
        const categoryLabels = {json.dumps(category_labels)};
        const categoryValues = {json.dumps(category_values)};

        const tabs = document.querySelectorAll('.tab');
        const pages = document.querySelectorAll('.page');
        tabs.forEach(t => t.addEventListener('click', () => {{
            tabs.forEach(x => x.classList.remove('active')); t.classList.add('active');
            pages.forEach(p => p.classList.remove('active'));
            document.getElementById(t.dataset.tab).classList.add('active');
            logAudit(`Open tab: ${{t.dataset.tab}}`, localStorage.getItem('crimeUser') || 'Citizen');
        }}));

        function logAudit(action, actor) {{
            const username = localStorage.getItem('crimeUser') || 'Citizen';
            const key = `crimeAuditLogs_${{username}}`;
            const logs = JSON.parse(localStorage.getItem(key) || '[]');
            logs.unshift({{ action, actor, time: new Date().toLocaleString() }});
            localStorage.setItem(key, JSON.stringify(logs.slice(0, 80)));
            renderAudit();
        }}
        function renderAudit() {{
            const username = localStorage.getItem('crimeUser') || 'Citizen';
            const logs = JSON.parse(localStorage.getItem(`crimeAuditLogs_${{username}}`) || '[]');
            document.getElementById('auditBody').innerHTML = logs.map(l => `<tr><td>${{l.action}}</td><td>${{l.actor}}</td><td>${{l.time}}</td></tr>`).join('');
        }}

        let alertsActive = localStorage.getItem('alertsActive') === 'true';
        const notifyBtnObj = document.getElementById('notifyBtn');
        if (notifyBtnObj && alertsActive) {{
            notifyBtnObj.textContent = 'Disable Alerts';
        }}

        function notifyUser(message) {{
            if (!alertsActive) return;
            if (!('Notification' in window)) return;
            if (Notification.permission === 'granted') new Notification('Crime Alert', {{ body: message }});
            else if (Notification.permission !== 'denied') Notification.requestPermission();
        }}
        notifyBtnObj.addEventListener('click', async () => {{ 
            if (!alertsActive) {{
                if (!('Notification' in window)) {{
                    alert('This browser does not support desktop notification');
                    return;
                }}
                const permission = await Notification.requestPermission();
                if (permission === 'granted') {{
                    alertsActive = true;
                    localStorage.setItem('alertsActive', 'true');
                    notifyBtnObj.textContent = 'Disable Alerts';
                    alert('Notifications successfully enabled!');
                    logAudit('Enabled notifications', localStorage.getItem('crimeUser') || 'Citizen');
                }} else {{
                    alert('Notification permission: ' + permission);
                }}
            }} else {{
                alertsActive = false;
                localStorage.setItem('alertsActive', 'false');
                notifyBtnObj.textContent = 'Enable Alerts';
                alert('Notifications disabled!');
                logAudit('Disabled notifications', localStorage.getItem('crimeUser') || 'Citizen');
            }}
        }});

        function toRad(x) {{ return x * Math.PI / 180; }}
        function haversineKm(lat1, lon1, lat2, lon2) {{
            const R = 6371, dLat = toRad(lat2-lat1), dLon = toRad(lon2-lon1);
            const a = Math.sin(dLat/2)**2 + Math.cos(toRad(lat1))*Math.cos(toRad(lat2))*Math.sin(dLon/2)**2;
            return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        }}
        function findNearestStation(userLat, userLon) {{
            let nearest = null;
            for (const s of report.nearby_police_stations || []) {{
                if (typeof s.latitude !== 'number' || typeof s.longitude !== 'number') continue;
                const d = haversineKm(userLat, userLon, s.latitude, s.longitude);
                if (!nearest || d < nearest.distanceKm) nearest = {{ ...s, distanceKm: d }};
            }}
            return nearest;
        }}

        const topHotspot = (report.top_hotspots || [])[0];
        if (report.alerts && report.alerts.length) notifyUser(report.alerts[0]);
        
        // SOS Button Logic
        document.getElementById('sosBtn').addEventListener('click', async () => {{
            const btn = document.getElementById('sosBtn');
            btn.disabled = true;
            btn.textContent = 'Sending...';
            
            // Generate mock location or fetch real
            const lat = document.getElementById('userLocation').textContent.includes('live location') 
                        ? parseFloat(document.getElementById('userLocation').textContent.split(': ')[1].split(',')[0])
                        : 28.6139; // Default approx
            const lon = document.getElementById('userLocation').textContent.includes('live location') 
                        ? parseFloat(document.getElementById('userLocation').textContent.split(': ')[1].split(',')[1])
                        : 77.2090; // Default approx

            const payload = {{
                location: `${{lat.toFixed(4)}}, ${{lon.toFixed(4)}}`,
                status: "Active"
            }};
            
            const res = await postBackendJson('/sos', payload);
            if (res.error) {{
                alert('SOS request failed: ' + res.error);
            }} else {{
                alert('🚨 SOS Dispatched! Control Room Notified.');
                logAudit('Triggered Emergency SOS', localStorage.getItem('crimeUser') || 'Citizen');
                loadSos();
            }}
            
            btn.textContent = '🚨 SOS Emergency';
            btn.disabled = false;
        }});

        let previousSosIds = new Set();
        async function loadSos() {{
            const table = document.getElementById('sosBody');
            if (!table) return;
            const res = await getBackendJson('/sos');
            if (!res || !Array.isArray(res)) {{
                table.innerHTML = '<tr><td colspan=\"4\" class=\"muted\">No active SOS alerts.</td></tr>';
                return;
            }}
            
            const currentRole = localStorage.getItem('crimeRole') || 'citizen';
            if (currentRole === 'officer' || currentRole === 'analyst') {{
                const isInitialLoad = previousSosIds.size === 0;
                res.forEach(r => {{
                    const id = r._id || r.id;
                    if (id && !previousSosIds.has(id)) {{
                        if (!isInitialLoad) {{
                            notifyUser(`🚨 EMERGENCY: New SOS Alert from ${{r.location}}!`);
                            alert(`🚨 EMERGENCY: New SOS Alert from ${{r.location}}!`);
                        }}
                        previousSosIds.add(id);
                    }}
                }});
            }}

            if (res.length === 0) {{
                table.innerHTML = '<tr><td colspan=\"4\" class=\"muted\">No active SOS alerts.</td></tr>';
                return;
            }}
            table.innerHTML = res.map(r => `<tr style=\"color: #ef4444; font-weight: bold;\"><td>${{r._id || r.id || ''}}</td><td>${{new Date(r.createdAt || r.time || new Date()).toLocaleString()}}</td><td>${{r.location}}</td><td>${{r.status || 'Active'}}</td></tr>`).join('');
        }}
        document.getElementById('refreshSosBtn')?.addEventListener('click', loadSos);
        loadSos();
        setInterval(loadSos, 15000);
        
        // Alert Polling for Officers & Analysts
        let lastAlertCheck = Date.now() - 5000;
        async function checkNewAlerts() {{
            if (!localStorage.getItem('crimeToken')) return;
            const role = localStorage.getItem('crimeRole') || 'citizen';
            if (role !== 'officer' && role !== 'analyst' && role !== 'admin') return;

            const res = await getBackendJson(`/alerts/recent?since=${{lastAlertCheck}}`);
            if (res && res.alerts && res.alerts.length > 0) {{
                res.alerts.forEach(a => notifyUser(`🚨 ALERT: ${{a.message}}`));
                lastAlertCheck = Date.now();
            }}
        }}
        setInterval(checkNewAlerts, 10000);
        
        
        if (navigator.geolocation) {{
            navigator.geolocation.watchPosition((pos) => {{
                const userLat = pos.coords.latitude, userLon = pos.coords.longitude;
                document.getElementById('userLocation').textContent = `Your live location: ${{userLat.toFixed(5)}}, ${{userLon.toFixed(5)}}`;
                if (topHotspot && typeof topHotspot.latitude === 'number' && typeof topHotspot.longitude === 'number') {{
                    const d = haversineKm(userLat, userLon, topHotspot.latitude, topHotspot.longitude);
                    document.getElementById('distanceToHotspot').textContent = `Distance to top hotspot (${{topHotspot.district}}): ${{d.toFixed(2)}} km`;
                    if (d <= 10) notifyUser(`Warning: You are within ${{d.toFixed(1)}} km of hotspot ${{topHotspot.district}}.`);
                }}
                const nearest = findNearestStation(userLat, userLon);
                if (nearest) document.getElementById('nearestStationText').innerHTML = `Nearest station: <b>${{nearest.name}}</b> (${{nearest.distanceKm.toFixed(2)}} km) - <a target=\"_blank\" href=\"${{nearest.maps_url}}\">Navigate</a>`;
            }}, () => {{ document.getElementById('userLocation').textContent = 'Location permission denied or unavailable.'; }}, {{ enableHighAccuracy:true, maximumAge:10000, timeout:20000 }});
        }}

        async function drawChart() {{
            const data = await getBackendJson('/stats');
            if (!data) return;
            const labels = data.categoryLabels || categoryLabels;
            const values = data.categoryValues || categoryValues;
            
            const c = document.getElementById('catChart'); if (!c) return; const x = c.getContext('2d');
            x.clearRect(0,0,c.width,c.height);
            const maxV = Math.max(1, ...(values.length ? values : [1]));
            const bw = Math.max(24, Math.floor((c.width - 40) / Math.max(1, values.length)) - 8);
            values.forEach((v,i) => {{
                const h = Math.floor((v / maxV) * (c.height - 60));
                const bx = 24 + i*(bw+8), by = c.height - h - 24;
                x.fillStyle = '#22c55e'; x.fillRect(bx, by, bw, h);
                x.fillStyle = '#cbd5e1'; x.font = '12px sans-serif'; x.fillText(String(v), bx + 2, by - 4);
                x.fillStyle = '#93c5fd'; x.fillText(String(labels[i]).slice(0, 9), bx, c.height - 8);
            }});
        }}
        drawChart();

        let liveComplaints = [];

        function renderHeatmap() {{
            const box = document.getElementById('heatmap');
            const t = document.getElementById('fType').value;
            const s = document.getElementById('fSeverity').value;
            box.innerHTML = '';
            
            const mappedComplaints = liveComplaints.map(c => ({{
                id: c.id || c._id,
                crime_type: c.category,
                severity: c.ai_severity,
                time: c.time
            }}));

            const combined = [...(report.incidents || []), ...mappedComplaints];
            updateTypeFilters(combined);

            const filtered = combined.filter(i => (t === 'All' || i.crime_type === t) && (s === 'All' || i.severity === s));
            filtered.forEach((inc, idx) => {{
                const dot = document.createElement('div');
                dot.className = `dot ${{inc.severity}}`;
                const px = 10 + ((idx * 17) % 80);
                const py = 15 + ((idx * 29) % 70);
                dot.style.left = `${{px}}%`; dot.style.top = `${{py}}%`;
                dot.title = `${{inc.id}} | ${{inc.crime_type}} | ${{inc.severity}}`;
                box.appendChild(dot);
            }});
        }}

        function updateTypeFilters(incidents) {{
            const fType = document.getElementById('fType');
            if (!fType) return;
            const currentVal = fType.value;
            const uniqueTypes = Array.from(new Set(incidents.map(i => i.crime_type).filter(Boolean)));
            fType.innerHTML = '<option value="All">All Crime Types</option>';
            uniqueTypes.forEach(type => {{
                const o = document.createElement('option');
                o.textContent = type;
                o.value = type;
                fType.appendChild(o);
            }});
            fType.value = currentVal;
            if (fType.selectedIndex === -1) fType.value = 'All';
        }}

        document.getElementById('applyHeat').addEventListener('click', renderHeatmap);
        renderHeatmap();

        async function loadComplaints() {{
            const res = await getBackendJson('/complaints');
            if (!res || !Array.isArray(res)) return;
            liveComplaints = res;
            document.getElementById('complaintsBody').innerHTML = res.map(r => `<tr><td>${{r.id?.slice(-6) || r._id?.slice(-6) || ''}}</td><td>${{r.category}}</td><td>${{r.district}}</td><td>${{r.ai_severity || 'Unknown'}}</td><td>${{r.anonymous ? 'Anonymous' : (r.user_name || 'Unknown')}}</td><td>${{new Date(r.created_date || r.createdAt || r.time || new Date()).toLocaleString()}}</td></tr>`).join('');
            renderHeatmap();
        }}
        document.getElementById('complaintForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const payload = {{
                category: document.getElementById('cCategory').value,
                district: document.getElementById('cDistrict').value,
                desc: document.getElementById('cDesc').value,
                anonymous: document.getElementById('cAnon').checked
            }};
            const res = await postBackendJson('/complaints', payload);
            if (res.error) {{ alert('Error: ' + res.error); return; }}
            logAudit('Complaint submitted', document.getElementById('cAnon').checked ? 'Anonymous' : (localStorage.getItem('crimeUser') || 'Citizen'));
            loadComplaints();
            if (typeof drawChart === 'function') drawChart();
            alert('Complaint submitted to control room queue.');
            e.target.reset();
        }});
        loadComplaints();

        document.getElementById('portalLogin').addEventListener('click', () => {{
            const pin = document.getElementById('portalPin').value;
            if (pin === String(report.portal?.demo_pin || '4321')) {{
                document.getElementById('portalArea').style.display = 'block';
                logAudit('Police portal login success', localStorage.getItem('crimeUser') || 'Police');
            }} else {{
                alert('Invalid PIN');
                logAudit('Police portal login failed', 'Unknown');
            }}
        }});
        async function loadCases() {{
            const res = await getBackendJson('/cases');
            if (!res || !Array.isArray(res)) return;
            document.getElementById('casesBody').innerHTML = res.map(r => `<tr><td>${{r.id || r._id?.slice(-6) || ''}}</td><td>${{r.officer}}</td><td>${{r.status}}</td><td>${{r.priority}}</td><td>${{new Date(r.created_date || r.createdAt || r.time || new Date()).toLocaleString()}}</td></tr>`).join('');
        }}
        document.getElementById('caseForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const payload = {{ id: caseId.value, officer: caseOfficer.value, status: caseStatus.value, priority: casePriority.value, notes: caseNotes.value }};
            const res = await postBackendJson('/cases', payload);
            if (res.error) {{ alert('Error: ' + res.error); return; }}
            logAudit('Case updated', localStorage.getItem('crimeUser') || 'Police');
            loadCases();
            e.target.reset();
        }});
        loadCases();

        document.getElementById('importDb').addEventListener('click', () => {{
            try {{
                const parsed = JSON.parse(document.getElementById('dbImport').value || '{{}}');
                document.getElementById('dbPreview').textContent = JSON.stringify(parsed, null, 2).slice(0, 1500);
                logAudit('Imported police dataset', localStorage.getItem('crimeUser') || 'Police');
            }} catch {{ alert('Invalid JSON'); }}
        }});

        async function loadWatch() {{
            const res = await getBackendJson('/watch');
            if (!res || !Array.isArray(res)) return;
            document.getElementById('watchList').innerHTML = res.map(r => `<li><b>${{r.name}}</b> - ${{r.area}}: ${{r.plan}}</li>`).join('');
        }}
        document.getElementById('watchForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const payload = {{ name: document.getElementById('watchName').value, area: document.getElementById('watchArea').value, plan: document.getElementById('watchPlan').value }};
            const res = await postBackendJson('/watch', payload);
            if (res.error) {{ alert('Error: ' + res.error); return; }}
            logAudit('Neighborhood watch group created', localStorage.getItem('crimeUser') || 'Citizen');
            loadWatch();
            e.target.reset();
        }});
        loadWatch();

        document.getElementById('saveFeedback').addEventListener('click', async () => {{
            const payload = {{ text: feedbackText.value }};
            const res = await postBackendJson('/feedback', payload);
            if (res.error) {{ alert('Error: ' + res.error); return; }}
            logAudit('Feedback submitted', localStorage.getItem('crimeUser') || 'Citizen');
            feedbackText.value = '';
            alert('Feedback recorded.');
        }});

        document.getElementById('cyberForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const payload = {{ type: cyberType.value, contact: cyberContact.value, details: cyberDetails.value }};
            const res = await postBackendJson('/cyber', payload);
            if (res.error) {{ alert('Error: ' + res.error); return; }}
            logAudit('Cybercrime report submitted', localStorage.getItem('crimeUser') || 'Citizen');
            alert('Cybercrime report added to queue.');
            loadCyberReports();
            e.target.reset();
        }});

        async function loadCyberReports() {{
            const table = document.getElementById('cyberBody');
            if (!table) return;
            const res = await getBackendJson('/cyber');
            if (!res || !Array.isArray(res)) return;
            table.innerHTML = res.map(r => `
                <tr>
                    <td>${{r.title || r.crime_type || ''}}</td>
                    <td>${{r.phone || r.contact || 'Anonymous'}}</td>
                    <td>${{r.description || r.details || ''}}</td>
                    <td>${{new Date(r.created_date || r.createdAt || r.time || new Date()).toLocaleString()}}</td>
                </tr>
            `).join('');
        }}
        loadCyberReports();

        async function loadCctv() {{
            const res = await getBackendJson('/cctv');
            if (!res || !Array.isArray(res)) return;
            document.getElementById('cctvList').innerHTML = res.map(f => `<li><a href=\"${{f.url}}\" target=\"_blank\">${{f.url}}</a> - Status: Monitored</li>`).join('');
        }}
        document.getElementById('addCctv').addEventListener('click', async () => {{
            const url = document.getElementById('cctvUrl').value.trim();
            if (!url) return;
            const res = await postBackendJson('/cctv', {{ url }});
            if (res.error) {{ alert('Error: ' + res.error); return; }}
            logAudit('CCTV feed linked', localStorage.getItem('crimeUser') || 'Police');
            document.getElementById('cctvUrl').value = '';
            loadCctv();
        }});
        loadCctv();

        const highZones = (report.incidents || []).filter(i => i.severity === 'High').map(i => `${{i.district}} (${{i.crime_type}})`);
        document.getElementById('forecastText').textContent = highZones.length ? `Forecast: Elevated risk zone(s): ${{highZones.join(', ')}}. Increase patrol + CCTV checks.` : 'Forecast: Current trend stable; maintain regular patrolling and rapid-response units.';

        const texts = {{
            en: {{ title: 'Crime Command Center', sub: 'Real-time public safety monitoring' }},
            hi: {{ title: 'अपराध नियंत्रण केंद्र', sub: 'रीयल-टाइम सार्वजनिक सुरक्षा मॉनिटरिंग' }},
            te: {{ title: 'నేర నియంత్రణ కేంద్రం', sub: 'రియల్-టైమ్ పబ్లిక్ సేఫ్టీ మానిటరింగ్' }}
        }};
        const themeSelect = document.getElementById('themeSelect');
        function applyTheme(theme) {{
            const selected = ['midnight', 'royal', 'sunset', 'forest'].includes(theme) ? theme : 'midnight';
            document.body.setAttribute('data-theme', selected);
            localStorage.setItem('crimeTheme', selected);
            logAudit(`Theme changed: ${{selected}}`, localStorage.getItem('crimeUser') || 'Citizen');
        }}
        const initialTheme = localStorage.getItem('crimeTheme') || 'midnight';
        themeSelect.value = initialTheme;
        applyTheme(initialTheme);
        themeSelect.addEventListener('change', (e) => applyTheme(e.target.value));
        document.getElementById('langSelect').addEventListener('change', (e) => {{
            const t = texts[e.target.value] || texts.en;
            document.getElementById('titleText').textContent = t.title;
            document.getElementById('subtitleText').textContent = `Generated: ${{report.generated_at}} • ${{t.sub}}`;
            logAudit('Language switched', localStorage.getItem('crimeUser') || 'Citizen');
        }});

        document.getElementById('speakBtn').addEventListener('click', () => {{
            const msg = `Crime dashboard update. Total articles ${{report.total_crime_articles}}. Hotspots ${{(report.top_hotspots || []).length}}. Alerts ${{(report.alerts || []).join('. ')}}`;
            const utter = new SpeechSynthesisUtterance(msg);
            speechSynthesis.speak(utter);
            logAudit('Voice summary played', localStorage.getItem('crimeUser') || 'Citizen');
        }});

        const API_BASE = localStorage.getItem('crimeApiBase') || `http://\${{window.location.hostname}}:5001/api`;

        async function getBackendJson(path) {{
            const token = localStorage.getItem('crimeToken');
            const headers = {{}};
            if (token) headers['Authorization'] = `Bearer ${{token}}`;
            try {{
                const res = await fetch(`${{API_BASE}}${{path}}`, {{ headers }});
                if (!res.ok) return null;
                const data = await res.json();
                return data && data.rows ? data.rows : data;
            }} catch {{
                return null;
            }}
        }}

        async function postBackendJson(path, payload, method="POST") {{
            const token = localStorage.getItem('crimeToken');
            const headers = {{ 'Content-Type': 'application/json' }};
            if (token) headers['Authorization'] = `Bearer ${{token}}`;
            try {{
                const res = await fetch(`${{API_BASE}}${{path}}`, {{
                    method,
                    headers,
                    body: JSON.stringify(payload)
                }});
                if (!res.ok) return {{ error: await res.text() }};
                return await res.json();
            }} catch (e) {{
                return {{ error: e.message }};
            }}
        }}

        let isRegistering = false;
        document.getElementById('btnOpenLogin')?.addEventListener('click', () => {{
             isRegistering = false;
             document.getElementById('modalTitle').textContent = 'Login';
             document.getElementById('grpName').style.display = 'none';
             document.getElementById('grpRole').style.display = 'none';
             document.getElementById('authName').required = false;
             document.getElementById('authModal').style.display = 'flex';
        }});
        document.getElementById('btnOpenRegister')?.addEventListener('click', () => {{
             isRegistering = true;
             document.getElementById('modalTitle').textContent = 'Register';
             document.getElementById('grpName').style.display = 'block';
             document.getElementById('grpRole').style.display = 'block';
             document.getElementById('authName').required = true;
             document.getElementById('authModal').style.display = 'flex';
        }});
        document.getElementById('btnCloseModal')?.addEventListener('click', () => {{
             document.getElementById('authModal').style.display = 'none';
        }});
        document.getElementById('authForm')?.addEventListener('submit', async (e) => {{
            e.preventDefault();
            const btn = document.getElementById('btnSubmitAuth');
            btn.disabled = true; btn.textContent = 'Wait...';
            const email = document.getElementById('authEmail').value;
            const password = document.getElementById('authPassword').value;
            const err = document.getElementById('authError');
            err.textContent = '';
            
            let res;
            if (isRegistering) {{
                const name = document.getElementById('authName').value;
                const role = document.getElementById('authRole').value;
                res = await postBackendJson('/auth/register', {{ name, email, password, role }});
            }} else {{
                res = await postBackendJson('/auth/login', {{ email, password }});
            }}
            
            if (res.error) {{
                try {{ const p = JSON.parse(res.error); err.textContent = p.error || p.msg || res.error; }}
                catch {{ err.textContent = res.error; }}
            }} else {{
                localStorage.setItem('crimeToken', res.token);
                if (res.role) localStorage.setItem('crimeRole', res.role);
                // Handle different object structures between register / login endpoints if any
                localStorage.setItem('crimeUser', res.name || (res.user && res.user.name) || name || 'Citizen');
                document.getElementById('authModal').style.display = 'none';
                updateAuthUI();
            }}
            btn.disabled = false; btn.textContent = isRegistering ? 'Register' : 'Login';
        }});
        document.getElementById('btnLogout')?.addEventListener('click', () => {{
            localStorage.removeItem('crimeToken');
            localStorage.removeItem('crimeUser');
            localStorage.removeItem('crimeRole');
            window.location.href = '/';
        }});
        function updateAuthUI() {{
            const user = localStorage.getItem('crimeUser');
            // Select the main elements to hide when logged out
            const kpiSection = document.querySelector('.kpis');
            const mainContent = document.querySelector('.content-layout');
            const landingPage = document.getElementById('landingPage');
            const heroSection = document.querySelector('.hero');
            const container = document.querySelector('.container');
            
            if (user) {{
                // Show application when logged in
                document.getElementById('authControls').style.display = 'none';
                document.getElementById('userControls').style.display = 'flex';
                document.getElementById('lblUserName').textContent = user;
                
                if (container) container.style.display = 'block';
                if (kpiSection) kpiSection.style.display = 'grid';
                if (mainContent) mainContent.style.display = 'flex';
                if (heroSection) heroSection.style.display = 'flex';
                if (landingPage) landingPage.style.display = 'none';
                document.getElementById('authModal').style.display = 'none';
                
                // --- Apply Role-Based Interface Restrictions ---
                const role = localStorage.getItem('crimeRole') || 'citizen';
                const tabGroups = {{
                    'citizen': ['mapping', 'reporting', 'alerts', 'stats', 'law', 'community', 'security', 'advanced', 'accessibility'],
                    'analyst': ['mapping', 'reporting', 'alerts', 'stats', 'security', 'advanced', 'accessibility'],
                    'officer': ['mapping', 'reporting', 'alerts', 'stats', 'law', 'community', 'security', 'advanced', 'accessibility']
                }};
                const allowedTabs = tabGroups[role] || tabGroups['citizen'];
                
                document.querySelectorAll('.tab').forEach(t => {{
                    if (allowedTabs.includes(t.dataset.tab)) {{
                        t.style.display = 'inline-flex'; // Assuming flex or inline-block, inline-flex matches standard button tab styling
                    }} else {{
                        t.style.display = 'none';
                    }}
                }});
                
                // Force an allowed tab active to prevent them from landing on a hidden tab visually
                const activeTab = document.querySelector('.tab.active');
                if (activeTab && activeTab.style.display === 'none') {{
                    const firstAllowed = document.querySelector(`.tab[data-tab="${{allowedTabs[0]}}"]`);
                    if (firstAllowed) firstAllowed.click();
                }}

                // If officer logs in, instantly unlock the Law Enforcement Portal tab functionality
                if (role === 'officer') {{
                    const portalArea = document.getElementById('portalArea');
                    const pinBox = document.getElementById('portalPin');
                    if (pinBox && pinBox.parentElement) pinBox.parentElement.style.display = 'none'; // hide the controls div
                    if (portalArea) portalArea.style.display = 'block';
                }}
                
                // Remove SOS feature for Analyst and Officer
                const sosBtn = document.getElementById('sosBtn');
                if (sosBtn) {{
                    sosBtn.style.display = (role === 'citizen') ? 'inline-block' : 'none';
                }}
                
                // Hide Crime Submission Forms from Analysts and Officers
                const cardReqCom = document.getElementById('cardReportComplaint');
                if (cardReqCom) cardReqCom.style.display = (role === 'citizen') ? 'block' : 'none';
                const cardReqCyb = document.getElementById('cardReportCyber');
                if (cardReqCyb) cardReqCyb.style.display = (role === 'citizen') ? 'block' : 'none';
                
                // Show Read-Only Logs for Analysts and Officers
                const cardViewCyb = document.getElementById('cardViewCyber');
                if (cardViewCyb) {{
                     cardViewCyb.style.display = (role !== 'citizen') ? 'block' : 'none';
                     if (role !== 'citizen') loadCyberReports();
                }}
                
                // Hide SOS Board from Citizens
                const cardSosBoard = document.getElementById('cardSosBoard');
                if (cardSosBoard) {{
                    cardSosBoard.style.display = (role !== 'citizen') ? 'block' : 'none';
                }}
                
            }} else {{
                // Not logged in -> Redirect to custom landing page
                window.location.href = '/';
            }}
        }}
        
        document.getElementById('btnLandingLogin')?.addEventListener('click', () => {{
             isRegistering = false;
             document.getElementById('modalTitle').textContent = 'Login';
             document.getElementById('grpName').style.display = 'none';
             document.getElementById('authName').required = false;
             const btnSubmit = document.getElementById('btnSubmitAuth');
             if(btnSubmit) btnSubmit.textContent = 'Login';
             document.getElementById('authModal').style.display = 'flex';
        }});
        
        const openLandingRegister = () => {{
             isRegistering = true;
             document.getElementById('modalTitle').textContent = 'Register';
             document.getElementById('grpName').style.display = 'block';
             document.getElementById('authName').required = true;
             const btnSubmit = document.getElementById('btnSubmitAuth');
             if(btnSubmit) btnSubmit.textContent = 'Register';
             document.getElementById('authModal').style.display = 'flex';
        }};
        document.getElementById('btnLandingRegister')?.addEventListener('click', openLandingRegister);
        document.getElementById('btnHeroRegister')?.addEventListener('click', openLandingRegister);
        document.getElementById('btnGoogleLogin')?.addEventListener('click', () => {{
            alert('Google Login requested! To enable real Google Login, set up OAuth credentials in the Google Cloud Console and implement backend verification.');
        }});
        
        setTimeout(updateAuthUI, 100);

        async function refreshApiStatus() {{
            const line = document.getElementById('apiStatusLine');
            const info = await getBackendJson('/health/details');
            if (!info) {{
                line.textContent = 'API: offline or unreachable';
                line.classList.remove('status-live');
                line.classList.add('status-watch');
                return;
            }}
            line.textContent = `API: live | Uptime: ${{info.uptime_seconds || 0}}s | Complaints: ${{info.counts?.complaints || 0}} | Cases: ${{info.counts?.cases || 0}}`;
            line.classList.remove('status-watch');
            line.classList.add('status-live');
        }}

        function renderQuickSearchRows(rows) {{
            const body = document.getElementById('quickSearchBody');
            if (!rows.length) {{
                body.innerHTML = '<tr><td colspan="5" class="muted">No matches found.</td></tr>';
                return;
            }}
            body.innerHTML = rows.map(r => `<tr><td>${{r.source || ''}}</td><td>${{r.title || ''}}</td><td>${{r.district || ''}}</td><td>${{r.status || ''}}</td><td>${{r.time || ''}}</td></tr>`).join('');
        }}

        async function runQuickSearch() {{
            const input = document.getElementById('quickSearchInput');
            const q = input.value.trim();
            if (!q) {{
                renderQuickSearchRows([]);
                return;
            }}
            const payload = await getBackendJson(`/search?q=${{encodeURIComponent(q)}}&limit=20`);
            if (!payload || !Array.isArray(payload.rows)) {{
                renderQuickSearchRows([]);
                return;
            }}
            renderQuickSearchRows(payload.rows);
        }}

        document.getElementById('quickSearchBtn').addEventListener('click', runQuickSearch);
        document.getElementById('quickSearchInput').addEventListener('keydown', (event) => {{
            if (event.key === 'Enter') {{
                event.preventDefault();
                runQuickSearch();
            }}
        }});

        refreshApiStatus();
        setInterval(refreshApiStatus, 20000);

        renderAudit();
    </script>
</body>
</html>"""
    output_html.write_text(html, encoding="utf-8")
    return output_html


def start_live_server(port: int) -> None:
    print(f"\n[INFO] Live server started at http://127.0.0.1:{port}")
    print("[INFO] Press Ctrl+C to stop the server.")
    server = ThreadingHTTPServer(("127.0.0.1", port), SimpleHTTPRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped.")
    finally:
        server.server_close()


def run_once(args: argparse.Namespace, previous_top: Optional[dict] = None) -> Tuple[dict, Path, Path]:
    keywords = CRIME_KEYWORDS.copy()
    if args.extra_keywords.strip():
        extras = [x.strip().lower() for x in args.extra_keywords.split(",") if x.strip()]
        keywords.extend(extras)

    all_texts = collect_crime_articles(RSS_FEEDS, keywords)
    print(f"Total crime-related articles found: {len(all_texts)}")
    output_json = Path(args.output).resolve()
    if not all_texts:
        print("No crime articles found.")
        report_payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "total_crime_articles": 0,
            "state_filter": args.state,
            "keywords": sorted(set(keywords)),
            "top_hotspots": [],
            "top_hotspot_police_info": "No crime articles found.",
            "top_hotspot_center": None,
            "nearby_police_stations": [],
            "alerts": ["No critical alert in this cycle."],
            "category_breakdown": {"crime": 0},
            "incidents": [],
            "safety_tips": default_safety_tips(),
            "emergency_contacts": emergency_directory(args.control_room_number, args.control_room_email),
            "portal": {
                "demo_pin": args.portal_pin,
                "control_room_number": args.control_room_number,
                "control_room_email": args.control_room_email,
            },
            "cyber_resources": default_cyber_resources(),
        }
        output_html = write_outputs(output_json, report_payload)
        return report_payload, output_json, output_html

    mentions, crime_types_detected = detect_mentions(all_texts, keywords, args.state)

    # Inject 4 hardcoded mock crime places as requested by the user
    mentions[("Maharashtra", "Mumbai")] += 15
    mentions[("Delhi", "New Delhi")] += 12
    mentions[("Karnataka", "Bengaluru")] += 10
    mentions[("Tamil Nadu", "Chennai")] += 8
    
    for key, crimes in [
        (("Maharashtra", "Mumbai"), ["cybercrime", "theft"]),
        (("Delhi", "New Delhi"), ["assault", "robbery"]),
        (("Karnataka", "Bengaluru"), ["fraud", "cybercrime"]),
        (("Tamil Nadu", "Chennai"), ["theft", "assault"])
    ]:
        if key not in crime_types_detected:
            crime_types_detected[key] = set()
        crime_types_detected[key].update(crimes)

    if not mentions:
        print("No district mentions detected.")
        report_payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "total_crime_articles": len(all_texts),
            "state_filter": args.state,
            "keywords": sorted(set(keywords)),
            "top_hotspots": [],
            "top_hotspot_police_info": "No district mentions detected.",
            "top_hotspot_center": None,
            "nearby_police_stations": [],
            "alerts": ["No critical alert in this cycle."],
            "category_breakdown": compute_category_breakdown(all_texts, keywords),
            "incidents": [],
            "safety_tips": default_safety_tips(),
            "emergency_contacts": emergency_directory(args.control_room_number, args.control_room_email),
            "portal": {
                "demo_pin": args.portal_pin,
                "control_room_number": args.control_room_number,
                "control_room_email": args.control_room_email,
            },
            "cyber_resources": default_cyber_resources(),
        }
        output_html = write_outputs(output_json, report_payload)
        return report_payload, output_json, output_html



    top_n = max(1, args.top) + 4 # Ensure the 4 new items aren't truncated by default args
    top_hotspots = mentions.most_common(top_n)

    print("\nTop Crime Hotspots:")
    top_rows = []
    for index, ((state, district), count) in enumerate(top_hotspots, start=1):
        crimes = sorted(crime_types_detected.get((state, district), set()))
        crime_text = ", ".join(crimes) if crimes else "N/A"
        district_geo = geocode_nominatim(f"{district}, {state}, India")
        lat = float(district_geo["lat"]) if district_geo and district_geo.get("lat") else None
        lon = float(district_geo["lon"]) if district_geo and district_geo.get("lon") else None
        print(f"{index}. {district}, {state} - {count} mentions | Crime types: {crime_text}")
        top_rows.append(
            {
                "rank": index,
                "state": state,
                "district": district,
                "mentions": count,
                "crime_types": crimes,
                "latitude": lat,
                "longitude": lon,
                "maps_url": google_maps_search_link(f"{district}, {state}, India"),
            }
        )

    best_state, best_district = top_hotspots[0][0]
    police_stations, hotspot_center = nearby_police_stations(
        best_district, best_state, radius_km=args.radius_km, limit=args.police_limit
    )
    police_info = nearest_police_station_text(police_stations)
    print(f"\nNearest Police Station (Top hotspot): {police_info}")
    if police_stations:
        print("Nearby police contacts:")
        for idx, station in enumerate(police_stations, start=1):
            print(
                f"  {idx}. {station['name']} | Phone: {station['phone'] or 'N/A'} | "
                f"Website: {station['website'] or 'N/A'}"
            )

    alerts = build_alerts(top_rows, previous_top, args.alert_mentions)
    append_alert_log(alerts, Path("crime_alerts.log").resolve())
    print("\nAlerts:")
    for alert in alerts:
        print(f"- {alert}")
    print("\a", end="")

    report_payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_crime_articles": len(all_texts),
        "state_filter": args.state,
        "keywords": sorted(set(keywords)),
        "top_hotspots": top_rows,
        "top_hotspot_police_info": police_info,
        "top_hotspot_center": hotspot_center,
        "nearby_police_stations": police_stations,
        "alerts": alerts,
        "category_breakdown": compute_category_breakdown(all_texts, keywords),
        "incidents": build_incidents_for_dashboard(top_rows),
        "safety_tips": default_safety_tips(),
        "emergency_contacts": emergency_directory(args.control_room_number, args.control_room_email),
        "portal": {
            "demo_pin": args.portal_pin,
            "control_room_number": args.control_room_number,
            "control_room_email": args.control_room_email,
        },
        "cyber_resources": default_cyber_resources(),
    }

    output_html = write_outputs(output_json, report_payload)
    print(f"\nReport JSON saved: {output_json}")
    print(f"Report HTML saved: {output_html}")

    return report_payload, output_json, output_html


def main() -> None:
    args = parse_args()

    previous_top: Optional[dict] = None
    report_payload, _, _ = run_once(args, previous_top)
    if report_payload.get("top_hotspots"):
        previous_top = report_payload["top_hotspots"][0]

    if args.serve:
        if args.watch:
            import threading
            server_thread = threading.Thread(target=start_live_server, args=(args.port,), daemon=True)
            server_thread.start()
        else:
            start_live_server(args.port)

    if args.watch:
        print(f"\n[INFO] Watch mode enabled. Refreshing every {max(30, args.interval)} seconds.")
        try:
            while True:
                time.sleep(max(30, args.interval))
                print("\n[INFO] Refreshing crime feed...")
                report_payload, _, _ = run_once(args, previous_top)
                if report_payload.get("top_hotspots"):
                    previous_top = report_payload["top_hotspots"][0]
        except KeyboardInterrupt:
            print("\n[INFO] Watch mode stopped.")


if __name__ == "__main__":
    main()
