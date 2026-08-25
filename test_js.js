
        const report = {"generated_at": "2026-03-17T12:26:51", "total_crime_articles": 9, "state_filter": "", "keywords": ["assault", "attack", "burglary", "crime", "homicide", "kidnap", "murder", "rape", "robbery", "shooting", "theft"], "top_hotspots": [{"rank": 1, "state": "Gujarat", "district": "Dang", "mentions": 1, "crime_types": ["attack", "shooting"], "latitude": 20.7881719, "longitude": 73.7092033, "maps_url": "https://www.google.com/maps/search/?api=1&query=Dang%2C+Gujarat%2C+India"}, {"rank": 2, "state": "Uttar Pradesh", "district": "Banda", "mentions": 1, "crime_types": ["attack", "shooting"], "latitude": 25.4438537, "longitude": 80.5595237, "maps_url": "https://www.google.com/maps/search/?api=1&query=Banda%2C+Uttar+Pradesh%2C+India"}, {"rank": 3, "state": "Tamil Nadu", "district": "Thoothukudi", "mentions": 1, "crime_types": ["murder"], "latitude": 8.8457035, "longitude": 77.9938178, "maps_url": "https://www.google.com/maps/search/?api=1&query=Thoothukudi%2C+Tamil+Nadu%2C+India"}, {"rank": 4, "state": "Himachal Pradesh", "district": "Una", "mentions": 1, "crime_types": ["attack"], "latitude": 31.5834642, "longitude": 76.2351452, "maps_url": "https://www.google.com/maps/search/?api=1&query=Una%2C+Himachal+Pradesh%2C+India"}, {"rank": 5, "state": "Gujarat", "district": "Anand", "mentions": 1, "crime_types": ["murder"], "latitude": 22.5586555, "longitude": 72.9627227, "maps_url": "https://www.google.com/maps/search/?api=1&query=Anand%2C+Gujarat%2C+India"}], "top_hotspot_police_info": "Police Station: Saputara Police Station | Address: Dang | Phone: N/A | Coordinates: 20.5792511, 73.7519774", "top_hotspot_center": {"district": "Dang", "state": "Gujarat", "latitude": 20.7881719, "longitude": 73.7092033, "maps_url": "https://www.google.com/maps/search/?api=1&query=20.7881719,73.7092033"}, "nearby_police_stations": [{"name": "Saputara Police Station", "address": "Dang", "phone": "", "website": "", "email": "", "latitude": 20.5792511, "longitude": 73.7519774, "maps_url": "https://www.google.com/maps/search/?api=1&query=20.5792511,73.7519774"}], "alerts": ["No critical alert in this cycle."], "category_breakdown": {"attack": 7, "murder": 2, "shooting": 1}, "incidents": [{"id": "INC-1-DANG", "district": "Dang", "state": "Gujarat", "crime_type": "attack", "severity": "Low", "time": "2026-03-17T10:26", "latitude": 20.7881719, "longitude": 73.7092033}, {"id": "INC-2-BANDA", "district": "Banda", "state": "Uttar Pradesh", "crime_type": "attack", "severity": "Low", "time": "2026-03-17T08:26", "latitude": 25.4438537, "longitude": 80.5595237}, {"id": "INC-3-THOOTHUKUDI", "district": "Thoothukudi", "state": "Tamil Nadu", "crime_type": "murder", "severity": "Low", "time": "2026-03-17T06:26", "latitude": 8.8457035, "longitude": 77.9938178}, {"id": "INC-4-UNA", "district": "Una", "state": "Himachal Pradesh", "crime_type": "attack", "severity": "Low", "time": "2026-03-17T04:26", "latitude": 31.5834642, "longitude": 76.2351452}, {"id": "INC-5-ANAND", "district": "Anand", "state": "Gujarat", "crime_type": "murder", "severity": "Low", "time": "2026-03-17T02:26", "latitude": 22.5586555, "longitude": 72.9627227}], "safety_tips": [{"title": "Cyber Safety", "content": "Never share OTPs, verify payment links, and enable 2FA on banking apps."}, {"title": "Home Security", "content": "Install door cameras, use motion lights, and keep emergency contacts visible."}, {"title": "Fraud Awareness", "content": "Do not trust urgent reward/loan calls; verify via official helplines first."}, {"title": "Women & Child Safety", "content": "Share live location with trusted contacts when travelling late hours."}], "emergency_contacts": [{"service": "Police Control Room", "phone": "112", "email": "controlroom@citypolice.gov"}, {"service": "Ambulance", "phone": "108", "email": ""}, {"service": "Fire", "phone": "101", "email": ""}, {"service": "Women Helpline", "phone": "1091", "email": ""}, {"service": "Cybercrime Helpline", "phone": "1930", "email": ""}], "portal": {"demo_pin": "4321", "control_room_number": "112", "control_room_email": "controlroom@citypolice.gov"}, "cyber_resources": {"citizen_steps": ["Immediately call 1930 for financial fraud freeze request.", "Report at cybercrime.gov.in with transaction IDs and screenshots.", "Do not delete chats, emails, or SMS evidence.", "Change passwords and enable 2-factor authentication on all accounts.", "Inform your bank and block compromised cards/wallets right away."], "police_playbook": ["Preserve chain of custody for digital evidence and device seizure logs.", "Correlate complaints with UPI IDs, mule accounts, and IP intelligence.", "Trigger rapid takedown workflow for phishing domains and fake apps.", "Issue legal preservation notices to platforms and ISPs.", "Escalate cross-state/cross-border cases to cyber coordination units."], "fraud_signals": ["Remote screen-share app installation requests.", "Urgent KYC update links from unknown senders.", "Payment request from fake customer-care/social media handles.", "Unexpected OTP/approval popups while on calls.", "Promises of instant loan/refund requiring advance fees."], "evidence_checklist": ["Transaction reference number / UTR", "Phone numbers, email IDs, social handles", "Wallet ID / UPI ID / account details", "Screenshots, call recordings, chat exports", "Device logs and approximate incident timeline"]}};
        const categoryLabels = ["attack", "murder", "shooting"];
        const categoryValues = [7, 2, 1];

        const tabs = document.querySelectorAll('.tab');
        const pages = document.querySelectorAll('.page');
        tabs.forEach(t => t.addEventListener('click', () => {
            tabs.forEach(x => x.classList.remove('active')); t.classList.add('active');
            pages.forEach(p => p.classList.remove('active'));
            document.getElementById(t.dataset.tab).classList.add('active');
            logAudit(`Open tab: ${t.dataset.tab}`, 'Citizen');
        }));

        function logAudit(action, actor) {
            const key = 'crimeAuditLogs';
            const logs = JSON.parse(localStorage.getItem(key) || '[]');
            logs.unshift({ action, actor, time: new Date().toLocaleString() });
            localStorage.setItem(key, JSON.stringify(logs.slice(0, 80)));
            renderAudit();
        }
        function renderAudit() {
            const logs = JSON.parse(localStorage.getItem('crimeAuditLogs') || '[]');
            document.getElementById('auditBody').innerHTML = logs.map(l => `<tr><td>${l.action}</td><td>${l.actor}</td><td>${l.time}</td></tr>`).join('');
        }

        function notifyUser(message) {
            if (!('Notification' in window)) return;
            if (Notification.permission === 'granted') new Notification('Crime Alert', { body: message });
            else if (Notification.permission !== 'denied') Notification.requestPermission();
        }
        document.getElementById('notifyBtn').addEventListener('click', () => { Notification.requestPermission(); logAudit('Enable notifications', 'Citizen'); });

        function toRad(x) { return x * Math.PI / 180; }
        function haversineKm(lat1, lon1, lat2, lon2) {
            const R = 6371, dLat = toRad(lat2-lat1), dLon = toRad(lon2-lon1);
            const a = Math.sin(dLat/2)**2 + Math.cos(toRad(lat1))*Math.cos(toRad(lat2))*Math.sin(dLon/2)**2;
            return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        }
        function findNearestStation(userLat, userLon) {
            let nearest = null;
            for (const s of report.nearby_police_stations || []) {
                if (typeof s.latitude !== 'number' || typeof s.longitude !== 'number') continue;
                const d = haversineKm(userLat, userLon, s.latitude, s.longitude);
                if (!nearest || d < nearest.distanceKm) nearest = { ...s, distanceKm: d };
            }
            return nearest;
        }

        const topHotspot = (report.top_hotspots || [])[0];
        if (report.alerts && report.alerts.length) notifyUser(report.alerts[0]);
        if (navigator.geolocation) {
            navigator.geolocation.watchPosition((pos) => {
                const userLat = pos.coords.latitude, userLon = pos.coords.longitude;
                document.getElementById('userLocation').textContent = `Your live location: ${userLat.toFixed(5)}, ${userLon.toFixed(5)}`;
                if (topHotspot && typeof topHotspot.latitude === 'number' && typeof topHotspot.longitude === 'number') {
                    const d = haversineKm(userLat, userLon, topHotspot.latitude, topHotspot.longitude);
                    document.getElementById('distanceToHotspot').textContent = `Distance to top hotspot (${topHotspot.district}): ${d.toFixed(2)} km`;
                    if (d <= 10) notifyUser(`Warning: You are within ${d.toFixed(1)} km of hotspot ${topHotspot.district}.`);
                }
                const nearest = findNearestStation(userLat, userLon);
                if (nearest) document.getElementById('nearestStationText').innerHTML = `Nearest station: <b>${nearest.name}</b> (${nearest.distanceKm.toFixed(2)} km) - <a target="_blank" href="${nearest.maps_url}">Navigate</a>`;
            }, () => { document.getElementById('userLocation').textContent = 'Location permission denied or unavailable.'; }, { enableHighAccuracy:true, maximumAge:10000, timeout:20000 });
        }

        async function drawChart() {
            const data = await getBackendJson('/api/stats');
            if (!data) return;
            const labels = data.categoryLabels || categoryLabels;
            const values = data.categoryValues || categoryValues;
            
            const c = document.getElementById('catChart'); if (!c) return; const x = c.getContext('2d');
            x.clearRect(0,0,c.width,c.height);
            const maxV = Math.max(1, ...(values.length ? values : [1]));
            const bw = Math.max(24, Math.floor((c.width - 40) / Math.max(1, values.length)) - 8);
            values.forEach((v,i) => {
                const h = Math.floor((v / maxV) * (c.height - 60));
                const bx = 24 + i*(bw+8), by = c.height - h - 24;
                x.fillStyle = '#22c55e'; x.fillRect(bx, by, bw, h);
                x.fillStyle = '#cbd5e1'; x.font = '12px sans-serif'; x.fillText(String(v), bx + 2, by - 4);
                x.fillStyle = '#93c5fd'; x.fillText(String(labels[i]).slice(0, 9), bx, c.height - 8);
            });
        }
        drawChart();

        function renderHeatmap() {
            const box = document.getElementById('heatmap');
            const t = document.getElementById('fType').value;
            const s = document.getElementById('fSeverity').value;
            box.innerHTML = '';
            const filtered = (report.incidents || []).filter(i => (t === 'All' || i.crime_type === t) && (s === 'All' || i.severity === s));
            filtered.forEach((inc, idx) => {
                const dot = document.createElement('div');
                dot.className = `dot ${inc.severity}`;
                const px = 10 + ((idx * 17) % 80);
                const py = 15 + ((idx * 29) % 70);
                dot.style.left = `${px}%`; dot.style.top = `${py}%`;
                dot.title = `${inc.id} | ${inc.crime_type} | ${inc.severity}`;
                box.appendChild(dot);
            });
        }
        const uniqueTypes = Array.from(new Set((report.incidents || []).map(i => i.crime_type)));
        const fType = document.getElementById('fType');
        uniqueTypes.forEach(type => { const o = document.createElement('option'); o.textContent = type; o.value = type; fType.appendChild(o); });
        document.getElementById('applyHeat').addEventListener('click', renderHeatmap);
        renderHeatmap();

        async function loadComplaints() {
            const res = await getBackendJson('/complaints');
            if (!res || !Array.isArray(res)) return;
            document.getElementById('complaintsBody').innerHTML = res.map(r => `<tr><td>${r._id?.slice(-6) || ''}</td><td>${r.category}</td><td>${r.district}</td><td>${r.ai_severity || 'Unknown'}</td><td>${r.anonymous ? 'Anonymous' : (r.user?.name || 'Unknown')}</td><td>${new Date(r.createdAt).toLocaleString()}</td></tr>`).join('');
        }
        document.getElementById('complaintForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                category: document.getElementById('cCategory').value,
                district: document.getElementById('cDistrict').value,
                desc: document.getElementById('cDesc').value,
                anonymous: document.getElementById('cAnon').checked
            };
            const res = await postBackendJson('/complaints', payload);
            if (res.error) { alert('Error: ' + res.error); return; }
            logAudit('Complaint submitted', document.getElementById('cAnon').checked ? 'Anonymous' : 'Citizen');
            loadComplaints();
            if (typeof drawChart === 'function') drawChart();
            alert('Complaint submitted to control room queue.');
            e.target.reset();
        });
        loadComplaints();

        document.getElementById('portalLogin').addEventListener('click', () => {
            const pin = document.getElementById('portalPin').value;
            if (pin === String(report.portal?.demo_pin || '4321')) {
                document.getElementById('portalArea').style.display = 'block';
                logAudit('Police portal login success', 'Police');
            } else {
                alert('Invalid PIN');
                logAudit('Police portal login failed', 'Unknown');
            }
        });
        async function loadCases() {
            const res = await getBackendJson('/cases');
            if (!res || !Array.isArray(res)) return;
            document.getElementById('casesBody').innerHTML = res.map(r => `<tr><td>${r.id || r._id.slice(-6)}</td><td>${r.officer}</td><td>${r.status}</td><td>${r.priority}</td><td>${new Date(r.createdAt).toLocaleString()}</td></tr>`).join('');
        }
        document.getElementById('caseForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = { id: caseId.value, officer: caseOfficer.value, status: caseStatus.value, priority: casePriority.value, notes: caseNotes.value };
            const res = await postBackendJson('/cases', payload);
            if (res.error) { alert('Error: ' + res.error); return; }
            logAudit('Case updated', 'Police');
            loadCases();
            e.target.reset();
        });
        loadCases();

        document.getElementById('importDb').addEventListener('click', () => {
            try {
                const parsed = JSON.parse(document.getElementById('dbImport').value || '{}');
                document.getElementById('dbPreview').textContent = JSON.stringify(parsed, null, 2).slice(0, 1500);
                logAudit('Imported police dataset', 'Police');
            } catch { alert('Invalid JSON'); }
        });

        async function loadWatch() {
            const res = await getBackendJson('/watch');
            if (!res || !Array.isArray(res)) return;
            document.getElementById('watchList').innerHTML = res.map(r => `<li><b>${r.name}</b> - ${r.area}: ${r.plan}</li>`).join('');
        }
        document.getElementById('watchForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = { name: document.getElementById('watchName').value, area: document.getElementById('watchArea').value, plan: document.getElementById('watchPlan').value };
            const res = await postBackendJson('/watch', payload);
            if (res.error) { alert('Error: ' + res.error); return; }
            logAudit('Neighborhood watch group created', 'Citizen');
            loadWatch();
            e.target.reset();
        });
        loadWatch();

        document.getElementById('saveFeedback').addEventListener('click', async () => {
            const payload = { text: feedbackText.value };
            const res = await postBackendJson('/feedback', payload);
            if (res.error) { alert('Error: ' + res.error); return; }
            logAudit('Feedback submitted', 'Citizen');
            feedbackText.value = '';
            alert('Feedback recorded.');
        });

        document.getElementById('cyberForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = { type: cyberType.value, contact: cyberContact.value, details: cyberDetails.value };
            const res = await postBackendJson('/cyber', payload);
            if (res.error) { alert('Error: ' + res.error); return; }
            logAudit('Cybercrime report submitted', 'Citizen');
            alert('Cybercrime report added to queue.');
            loadCyberReports();
            e.target.reset();
        });

        async function loadCyberReports() {
            const table = document.getElementById('cyberBody');
            if (!table) return;
            const res = await getBackendJson('/cyber');
            if (!res || !Array.isArray(res)) return;
            table.innerHTML = res.map(r => `<tr><td>${r.type || ''}</td><td>${r.contact || 'Anonymous'}</td><td>${new Date(r.createdAt).toLocaleString()}</td></tr>`).join('');
        }
        loadCyberReports();

        async function loadCctv() {
            const res = await getBackendJson('/cctv');
            if (!res || !Array.isArray(res)) return;
            document.getElementById('cctvList').innerHTML = res.map(f => `<li><a href="${f.url}" target="_blank">${f.url}</a> - Status: Monitored</li>`).join('');
        }
        document.getElementById('addCctv').addEventListener('click', async () => {
            const url = document.getElementById('cctvUrl').value.trim();
            if (!url) return;
            const res = await postBackendJson('/cctv', { url });
            if (res.error) { alert('Error: ' + res.error); return; }
            logAudit('CCTV feed linked', 'Police');
            document.getElementById('cctvUrl').value = '';
            loadCctv();
        });
        loadCctv();

        const highZones = (report.incidents || []).filter(i => i.severity === 'High').map(i => `${i.district} (${i.crime_type})`);
        document.getElementById('forecastText').textContent = highZones.length ? `Forecast: Elevated risk zone(s): ${highZones.join(', ')}. Increase patrol + CCTV checks.` : 'Forecast: Current trend stable; maintain regular patrolling and rapid-response units.';

        const texts = {
            en: { title: 'Crime Command Center', sub: 'Real-time public safety monitoring' },
            hi: { title: 'अपराध नियंत्रण केंद्र', sub: 'रीयल-टाइम सार्वजनिक सुरक्षा मॉनिटरिंग' },
            te: { title: 'నేర నియంత్రణ కేంద్రం', sub: 'రియల్-టైమ్ పబ్లిక్ సేఫ్టీ మానిటరింగ్' }
        };
        const themeSelect = document.getElementById('themeSelect');
        function applyTheme(theme) {
            const selected = ['midnight', 'royal', 'sunset', 'forest'].includes(theme) ? theme : 'midnight';
            document.body.setAttribute('data-theme', selected);
            localStorage.setItem('crimeTheme', selected);
            logAudit(`Theme changed: ${selected}`, 'Citizen');
        }
        const initialTheme = localStorage.getItem('crimeTheme') || 'midnight';
        themeSelect.value = initialTheme;
        applyTheme(initialTheme);
        themeSelect.addEventListener('change', (e) => applyTheme(e.target.value));
        document.getElementById('langSelect').addEventListener('change', (e) => {
            const t = texts[e.target.value] || texts.en;
            document.getElementById('titleText').textContent = t.title;
            document.getElementById('subtitleText').textContent = `Generated: ${report.generated_at} • ${t.sub}`;
            logAudit('Language switched', 'Citizen');
        });

        document.getElementById('speakBtn').addEventListener('click', () => {
            const msg = `Crime dashboard update. Total articles ${report.total_crime_articles}. Hotspots ${(report.top_hotspots || []).length}. Alerts ${(report.alerts || []).join('. ')}`;
            const utter = new SpeechSynthesisUtterance(msg);
            speechSynthesis.speak(utter);
            logAudit('Voice summary played', 'Citizen');
        });

        const API_BASE = localStorage.getItem('crimeApiBase') || 'http://127.0.0.1:5001/api';

        async function getBackendJson(path) {
            const token = localStorage.getItem('crimeToken');
            const headers = {};
            if (token) headers['Authorization'] = `Bearer ${token}`;
            try {
                const res = await fetch(`${API_BASE}${path}`, { headers });
                if (!res.ok) return null;
                return await res.json();
            } catch {
                return null;
            }
        }

        async function postBackendJson(path, payload, method="POST") {
            const token = localStorage.getItem('crimeToken');
            const headers = { 'Content-Type': 'application/json' };
            if (token) headers['Authorization'] = `Bearer ${token}`;
            try {
                const res = await fetch(`${API_BASE}${path}`, {
                    method,
                    headers,
                    body: JSON.stringify(payload)
                });
                if (!res.ok) return { error: await res.text() };
                return await res.json();
            } catch (e) {
                return { error: e.message };
            }
        }

        let isRegistering = false;
        document.getElementById('btnOpenLogin')?.addEventListener('click', () => {
             isRegistering = false;
             document.getElementById('modalTitle').textContent = 'Login';
             document.getElementById('grpName').style.display = 'none';
             document.getElementById('authName').required = false;
             document.getElementById('authModal').style.display = 'flex';
        });
        document.getElementById('btnOpenRegister')?.addEventListener('click', () => {
             isRegistering = true;
             document.getElementById('modalTitle').textContent = 'Register';
             document.getElementById('grpName').style.display = 'block';
             document.getElementById('authName').required = true;
             document.getElementById('authModal').style.display = 'flex';
        });
        document.getElementById('btnCloseModal')?.addEventListener('click', () => {
             document.getElementById('authModal').style.display = 'none';
        });
        document.getElementById('authForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btnSubmitAuth');
            btn.disabled = true; btn.textContent = 'Wait...';
            const email = document.getElementById('authEmail').value;
            const password = document.getElementById('authPassword').value;
            const err = document.getElementById('authError');
            err.textContent = '';
            
            let res;
            if (isRegistering) {
                const name = document.getElementById('authName').value;
                res = await postBackendJson('/auth/register', { name, email, password });
            } else {
                res = await postBackendJson('/auth/login', { email, password });
            }
            
            if (res.error) {
                try { const p = JSON.parse(res.error); err.textContent = p.error || p.msg || res.error; }
                catch { err.textContent = res.error; }
            } else {
                localStorage.setItem('crimeToken', res.token);
                // Handle different object structures between register / login endpoints if any
                localStorage.setItem('crimeUser', res.name || (res.user && res.user.name) || name || 'Citizen');
                document.getElementById('authModal').style.display = 'none';
                updateAuthUI();
            }
            btn.disabled = false; btn.textContent = isRegistering ? 'Register' : 'Login';
        });
        document.getElementById('btnLogout')?.addEventListener('click', () => {
            localStorage.removeItem('crimeToken');
            localStorage.removeItem('crimeUser');
            updateAuthUI();
        });
        function updateAuthUI() {
            const user = localStorage.getItem('crimeUser');
            // Select the main elements to hide when logged out
            const mainAppContainer = document.querySelector('.container');
            const landingPage = document.getElementById('landingPage');
            
            if (user) {
                // Show application when logged in
                document.getElementById('authControls').style.display = 'none';
                document.getElementById('userControls').style.display = 'flex';
                document.getElementById('lblUserName').textContent = user;
                
                if (mainAppContainer) mainAppContainer.style.display = 'block';
                if (landingPage) landingPage.style.display = 'none';
                document.getElementById('authModal').style.display = 'none';
                
                // Keep the internal layout displays active
                const kpiSection = document.querySelector('.kpis');
                const mainContent = document.querySelector('.content-layout');
                if (kpiSection) kpiSection.style.display = 'grid';
                if (mainContent) mainContent.style.display = 'flex';
            } else {
                // Hide ENTIRE application and show landing page when logged out
                document.getElementById('authControls').style.display = 'inline-block';
                document.getElementById('userControls').style.display = 'none';
                
                if (mainAppContainer) mainAppContainer.style.display = 'none';
                if (landingPage) landingPage.style.display = 'flex';
                
                // Allow the modal to be closed, don't force it open here
                document.getElementById('authModal').style.display = 'none';
                
                // Restore the modal close button
                const closeBtn = document.getElementById('btnCloseModal');
                if (closeBtn) closeBtn.style.display = 'block';
            }
        }
        
        document.getElementById('btnLandingLogin')?.addEventListener('click', () => {
             isRegistering = false;
             document.getElementById('modalTitle').textContent = 'Login';
             document.getElementById('grpName').style.display = 'none';
             document.getElementById('authName').required = false;
             const btnSubmit = document.getElementById('btnSubmitAuth');
             if(btnSubmit) btnSubmit.textContent = 'Login';
             document.getElementById('authModal').style.display = 'flex';
        });
        
        const openLandingRegister = () => {
             isRegistering = true;
             document.getElementById('modalTitle').textContent = 'Register';
             document.getElementById('grpName').style.display = 'block';
             document.getElementById('authName').required = true;
             const btnSubmit = document.getElementById('btnSubmitAuth');
             if(btnSubmit) btnSubmit.textContent = 'Register';
             document.getElementById('authModal').style.display = 'flex';
        };
        document.getElementById('btnLandingRegister')?.addEventListener('click', openLandingRegister);
        document.getElementById('btnHeroRegister')?.addEventListener('click', openLandingRegister);
        document.getElementById('btnGoogleLogin')?.addEventListener('click', () => {
            alert('Google Login requested! To enable real Google Login, set up OAuth credentials in the Google Cloud Console and implement backend verification.');
        });
        setTimeout(updateAuthUI, 100);

        async function refreshApiStatus() {
            const line = document.getElementById('apiStatusLine');
            const info = await getBackendJson('/health/details');
            if (!info) {
                line.textContent = 'API: offline or unreachable';
                line.classList.remove('status-live');
                line.classList.add('status-watch');
                return;
            }
            line.textContent = `API: live | Uptime: ${info.uptime_seconds || 0}s | Complaints: ${info.counts?.complaints || 0} | Cases: ${info.counts?.cases || 0}`;
            line.classList.remove('status-watch');
            line.classList.add('status-live');
        }

        function renderQuickSearchRows(rows) {
            const body = document.getElementById('quickSearchBody');
            if (!rows.length) {
                body.innerHTML = '<tr><td colspan="5" class="muted">No matches found.</td></tr>';
                return;
            }
            body.innerHTML = rows.map(r => `<tr><td>${r.source || ''}</td><td>${r.title || ''}</td><td>${r.district || ''}</td><td>${r.status || ''}</td><td>${r.time || ''}</td></tr>`).join('');
        }

        async function runQuickSearch() {
            const input = document.getElementById('quickSearchInput');
            const q = input.value.trim();
            if (!q) {
                renderQuickSearchRows([]);
                return;
            }
            const payload = await getBackendJson(`/search?q=${encodeURIComponent(q)}&limit=20`);
            if (!payload || !Array.isArray(payload.rows)) {
                renderQuickSearchRows([]);
                return;
            }
            renderQuickSearchRows(payload.rows);
        }

        document.getElementById('quickSearchBtn').addEventListener('click', runQuickSearch);
        document.getElementById('quickSearchInput').addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                runQuickSearch();
            }
        });

        refreshApiStatus();
        setInterval(refreshApiStatus, 20000);

        renderAudit();
    