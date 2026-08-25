// Use global fetch

async function test() {
  try {
    // Register or login
    const loginRes = await fetch("http://127.0.0.1:5001/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "nani26@gmail.com", password: "password123" }) // Wait, what is nani26's password?
    });
    
    console.log("Login status:", loginRes.status);
    const loginData = await loginRes.json();
    console.log("Login response:", loginData);
    
    if (!loginRes.ok) return;
    
    const token = loginData.token;
    
    // Submit complaint
    const payload = {
      category: "Theft",
      district: "Vadodara",
      desc: "test description with nani26 token",
      anonymous: false
    };
    
    const compRes = await fetch("http://127.0.0.1:5001/api/complaints", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    
    console.log("Complaint status:", compRes.status);
    const compData = await compRes.json();
    console.log("Complaint response:", compData);
    
  } catch (err) {
    console.error(err);
  }
}

test();
