localStorage.removeItem('crimeApiBase');

function switchTab(tabStr) {
    // Buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`tab-${tabStr}`).classList.add('active');
    
    // Forms
    document.querySelectorAll('.auth-form').forEach(form => form.classList.remove('active'));
    const formToShow = document.getElementById(`form-${tabStr}`);
    
    // Slight reset animation capability
    formToShow.style.animation = 'none';
    formToShow.offsetHeight; /* trigger reflow */
    formToShow.style.animation = null; 
    formToShow.classList.add('active');
}

async function handleAuth(e) {
    e.preventDefault();
    
    // Determine context (login vs register)
    const formId = e.target.closest('.auth-form').id;
    const isRegistering = formId === 'form-register';
    
    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Authenticating...</span>';
    btn.style.opacity = '0.8';
    btn.disabled = true;

    // Gather input values
    const email = document.getElementById(isRegistering ? 'reg-email' : 'login-email').value.trim();
    const password = document.getElementById(isRegistering ? 'reg-password' : 'login-password').value;
    
    const payload = { email, password };
    const apiBase = '/api';
    let endpoint = `${apiBase}/auth/login`;

    if (isRegistering) {
        endpoint = `${apiBase}/auth/register`;
        payload.name = document.getElementById('reg-name').value.trim();
        payload.role = document.getElementById('reg-role').value;
    }

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            let errorMsg = data.error || 'Authentication failed';
            
            // Try to parse nested error messages typical of python backends returning stringified JSON
            try {
                const parsed = JSON.parse(data.error);
                errorMsg = parsed.error || parsed.msg || errorMsg;
            } catch (e) {}

            alert(errorMsg);
            
            // Reset button
            btn.innerHTML = originalText;
            btn.style.opacity = '1';
            btn.disabled = false;
            return;
        }

        // On success, save the token and the user's name to localStorage
        localStorage.setItem('crimeToken', data.token);
        localStorage.setItem('crimeUser', data.name || payload.name || 'Citizen');
        localStorage.setItem('crimeRole', data.role || payload.role || 'citizen');

        // Redirect to main dashboard
        window.location.href = 'hotspot_report.html';

    } catch (err) {
        alert("Failed to connect to backend server. Is it running?");
        btn.innerHTML = originalText;
        btn.style.opacity = '1';
        btn.disabled = false;
    }
}
