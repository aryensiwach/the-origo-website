// =========================================
//  1. CONSTELLATION ANIMATION
// =========================================
const canvas = document.getElementById('constellation-canvas');
if (canvas) {
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    let particlesArray;

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 0.1;
            this.speedX = (Math.random() * 0.5) - 0.25;
            this.speedY = (Math.random() * 0.5) - 0.25;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.x > canvas.width || this.x < 0) this.speedX = -this.speedX;
            if (this.y > canvas.height || this.y < 0) this.speedY = -this.speedY;
        }
        draw() {
            ctx.fillStyle = '#d4a373';
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function init() {
        particlesArray = [];
        let numberOfParticles = (canvas.width * canvas.height) / 9000;
        for (let i = 0; i < numberOfParticles; i++) {
            particlesArray.push(new Particle());
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        let gradient = ctx.createRadialGradient(canvas.width / 2, canvas.height / 2, 0, canvas.width / 2, canvas.height / 2, canvas.width);
        gradient.addColorStop(0, '#064e3b');
        gradient.addColorStop(1, '#022c22');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        for (let i = 0; i < particlesArray.length; i++) {
            particlesArray[i].update();
            particlesArray[i].draw();
            for (let j = i; j < particlesArray.length; j++) {
                const dx = particlesArray[i].x - particlesArray[j].x;
                const dy = particlesArray[i].y - particlesArray[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                if (distance < 100) {
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(212, 163, 115, ${1 - distance / 100})`;
                    ctx.lineWidth = 0.5;
                    ctx.moveTo(particlesArray[i].x, particlesArray[i].y);
                    ctx.lineTo(particlesArray[j].x, particlesArray[j].y);
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }

    window.addEventListener('resize', function () {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        init();
    });

    init();
    animate();
}

// =========================================
//  2. FIREBASE CONFIGURATION & AUTH LOGIC
// =========================================
const firebaseConfig = {
    apiKey: "AIzaSyCe0mBaCP3DpFGZ7-GKTlEQ9L8wCNXZ9kI",
    authDomain: "internhub-c469b.firebaseapp.com",
    projectId: "internhub-c469b",
    storageBucket: "internhub-c469b.firebasestorage.app",
    messagingSenderId: "332430290715",
    appId: "1:332430290715:web:d4c7725ebe94785d156dbe",
    measurementId: "G-8KR4E419DP"
};

let auth;
let provider;

window.addEventListener('load', function () {
    try {
        if (typeof firebase !== 'undefined' && !firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
        }

        if (typeof firebase !== 'undefined') {
            auth = firebase.auth();
            provider = new firebase.auth.GoogleAuthProvider();

            // AUTH LISTENER
            auth.onAuthStateChanged((user) => {
                if (user) {
                    console.log("Auth: User Logged In ->", user.displayName);
                    toggleAuthUI(true, user);
                } else {
                    console.log("Auth: User Logged Out");
                    toggleAuthUI(false, null);
                }
            });
        }
    } catch (error) {
        console.error("Firebase Init Error:", error);
    }
});

// =========================================
//  3. HAMBURGER & UI LOGIC
// =========================================
const hamburger = document.getElementById('hamburgerBtn');
const navLinks = document.getElementById('navLinks');
const closeMenuBtn = document.getElementById('closeMenuBtn');

function openMenu() {
    if (navLinks) navLinks.classList.add('active');
}

function closeMenu() {
    if (navLinks) navLinks.classList.remove('active');
}

if (hamburger) hamburger.addEventListener('click', openMenu);
if (closeMenuBtn) closeMenuBtn.addEventListener('click', closeMenu);

// Mobile Menu me link click hone pe band ho jaye
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', closeMenu);
});

// =========================================
//  4. AUTH UI TOGGLE (LOGIN BUTTON HIDE FIX)
// =========================================
function toggleAuthUI(isLoggedIn, user) {
    const deskAuth = document.getElementById('desktopAuthBtns');
    const deskUser = document.getElementById('desktopUserSection');
    
    const mobLoginBtn = document.getElementById('mobileLoginBtn');
    const mobUserSection = document.getElementById('mobileUserSection');

    if (isLoggedIn) {
        // --- DESKTOP ---
        if (deskAuth) deskAuth.style.display = 'none';
        if (deskUser) deskUser.style.display = 'flex';
        
        const firstName = user.displayName ? user.displayName.split(' ')[0] : 'Seeker';
        document.querySelectorAll('.desktopUserName').forEach(el => el.innerText = firstName);

        // --- MOBILE ---
        if (mobLoginBtn) mobLoginBtn.style.setProperty('display', 'none', 'important');
        
        if (mobUserSection) {
            mobUserSection.style.display = 'flex';
            mobUserSection.innerHTML = `
                <div style="border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 15px; margin-bottom: 10px;">
                    <h3 style="color: var(--gold); font-size: 1.5rem; margin-bottom: 5px;">
                        Namaste, ${firstName}
                    </h3>
                    <p style="color: #aaa; font-size: 0.8rem;">${user.email}</p>
                </div>

                <a href="#" onclick="openEditProfile(); closeMenu();" style="color: white; font-size: 1.1rem; display: flex; align-items: center; justify-content: flex-start; gap: 10px; text-decoration: none;">
                    <i class="fa-solid fa-pen-to-square" style="color: var(--gold);"></i> Edit Profile
                </a>

                <button onclick="logoutUser()" style="
                    margin-top: 15px;
                    background: rgba(255, 77, 77, 0.1);
                    border: 1px solid #ff4d4d;
                    color: #ff4d4d;
                    padding: 10px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 0.9rem;
                    display: flex; 
                    align-items: center; 
                    justify-content: center;
                    gap: 10px;
                    width: 100%;
                ">
                    Logout <i class="fa-solid fa-power-off"></i>
                </button>
            `;
        }

    } else {
        // --- LOGGED OUT ---
        if (deskAuth) deskAuth.style.display = 'block';
        if (deskUser) deskUser.style.display = 'none';

        if (mobLoginBtn) mobLoginBtn.style.display = 'block'; 
        if (mobUserSection) {
            mobUserSection.style.display = 'none';
            mobUserSection.innerHTML = ''; 
        }
    }
}

function logoutUser() {
    if (auth) {
        auth.signOut().then(() => {
            window.location.href = "/"; 
        });
    }
}

// =========================================
//  5. MODAL HANDLERS (FIXED)
// =========================================
const loginModal = document.getElementById('loginModal');
const onboardingModal = document.getElementById('onboardingModal');
const editProfileModal = document.getElementById('editProfileModal');
const selectionModal = document.getElementById('selectionModal'); // New Modal Reference

function closeModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.style.display = 'none';
}

function openLoginModal() {
    closeMenu();
    if (loginModal) loginModal.style.display = 'flex';
}

// --- FIX: OPEN SELECTION MODAL FIRST ---
function handleMainAction() {
    // Reveal My Truth button calls this
    if (selectionModal) {
        selectionModal.style.display = 'flex';
    } else {
        console.error("Selection Modal not found!");
    }
}

// --- NEW FUNCTION FOR SELECTION BUTTONS ---
function proceedAnalysis(mode) {
    closeModal('selectionModal');
    
    // Store mode temporarily
    sessionStorage.setItem('analysisMode', mode);

    const user = firebase.auth().currentUser;

    if (user) {
        // Logged In
        if (mode === 'guest') {
            window.location.href = "/dashboard?mode=guest";
        } else {
            // Self Mode: Check if profile exists, else onboarding
            checkUserProfile(user);
        }
    } else {
        // Not Logged In -> Show Login
        openLoginModal();
    }
}

// Helper to check profile
async function checkUserProfile(user) {
    try {
        const db = firebase.firestore();
        const doc = await db.collection('users').doc(user.uid).get();
        
        if (doc.exists) {
            window.location.href = "/dashboard";
        } else {
            // New User -> Open Onboarding
            if (onboardingModal) {
                onboardingModal.style.display = 'flex';
                document.getElementById('userUid').value = user.uid;
                document.getElementById('userEmail').value = user.email;
                document.getElementById('userName').value = user.displayName;
            }
        }
    } catch (e) {
        console.error("Profile Check Error:", e);
    }
}

// =========================================
//  6. EDIT PROFILE & ONBOARDING
// =========================================
async function openEditProfile() {
    const user = firebase.auth().currentUser;
    if (!user) { alert("Please login first."); return; }

    const modal = document.getElementById('editProfileModal');
    if (modal) modal.style.display = 'flex';

    if (document.getElementById("editName")) document.getElementById("editName").value = "Loading...";

    try {
        const db = firebase.firestore();
        const doc = await db.collection("users").doc(user.uid).get();
        
        if (doc.exists) {
            const rawData = doc.data();
            const data = rawData.profile || rawData; 

            if (document.getElementById("editName")) document.getElementById("editName").value = data.name || "";
            if (document.getElementById("editDob")) document.getElementById("editDob").value = data.dob || "";
            if (document.getElementById("editTime")) document.getElementById("editTime").value = data.tob || "";
            if (document.getElementById("editPlace")) document.getElementById("editPlace").value = data.pob || "";
            if (document.getElementById("editGender")) document.getElementById("editGender").value = data.gender || "male";
            if (document.getElementById("editStatus")) document.getElementById("editStatus").value = data.status || "single";
        } else {
            if (document.getElementById("editName")) document.getElementById("editName").value = user.displayName || "";
        }
    } catch (error) {
        console.error("Error fetching user data:", error);
    }
}

async function updateProfile(event) {
    event.preventDefault();
    const user = firebase.auth().currentUser;
    if (!user) return;
    
    const form = document.getElementById("editProfileForm");
    const submitBtn = form.querySelector('.btn-submit');
    const originalText = submitBtn.innerText;

    submitBtn.innerHTML = "Regenerating... <i class='fa-solid fa-spinner fa-spin'></i>";
    submitBtn.disabled = true;

    const formData = new FormData(form);
    formData.append("uid", user.uid);
    formData.append("email", user.email);

    try {
        const response = await fetch('/api/save_user_data', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.status === 'success') {
            alert("✅ Profile & Charts Updated!");
            closeModal("editProfileModal");
            location.reload(); 
        } else {
            alert("❌ Error: " + result.message);
        }
    } catch (error) {
        console.error("Error updating:", error);
    }
    submitBtn.innerHTML = originalText;
    submitBtn.disabled = false;
}

// --- GOOGLE LOGIN ---
const googleBtn = document.getElementById('googleLoginBtn');
if (googleBtn) {
    googleBtn.addEventListener('click', () => {
        auth.signInWithPopup(provider)
            .then(async (result) => {
                const user = result.user;
                closeModal('loginModal');
                
                // Login ke baad kya karna hai?
                // Check sessionStorage for pending action
                const mode = sessionStorage.getItem('analysisMode');
                
                if (mode === 'guest') {
                    window.location.href = "/dashboard?mode=guest";
                } else if (mode === 'self') {
                    checkUserProfile(user); // Will go to dashboard or onboarding
                } else {
                    // Default fallback
                    checkUserProfile(user);
                }
            })
            .catch((error) => console.error("Login Failed", error));
    });
}

// Onboarding Submit
async function submitOnboarding(event) {
    event.preventDefault();
    const form = document.getElementById('onboardingForm');
    const formData = new FormData(form);

    try {
        const response = await fetch('/api/save_user_data', { method: 'POST', body: formData });
        const result = await response.json();
        if (result.status === 'success') {
            closeModal('onboardingModal');
            window.location.href = "/dashboard";
        }
    } catch (e) { console.error(e); }
}

// Close Modals on Outside Click
window.addEventListener("click", (e) => {
    if (loginModal && e.target == loginModal) loginModal.style.display = "none";
    if (onboardingModal && e.target == onboardingModal) onboardingModal.style.display = "none";
    if (editProfileModal && e.target == editProfileModal) editProfileModal.style.display = "none";
    if (selectionModal && e.target == selectionModal) selectionModal.style.display = "none";
});