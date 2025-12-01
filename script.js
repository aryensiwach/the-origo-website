// === CONSTELLATION ANIMATION ===
const canvas = document.getElementById('constellation-canvas');
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
    let gradient = ctx.createRadialGradient(canvas.width/2, canvas.height/2, 0, canvas.width/2, canvas.height/2, canvas.width);
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
                ctx.strokeStyle = `rgba(212, 163, 115, ${1 - distance/100})`;
                ctx.lineWidth = 0.5;
                ctx.moveTo(particlesArray[i].x, particlesArray[i].y);
                ctx.lineTo(particlesArray[j].x, particlesArray[j].y);
                ctx.stroke();
            }
        }
    }
    requestAnimationFrame(animate);
}

window.addEventListener('resize', function() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    init();
});

init();
animate();

// === MODAL LOGIC (Single, Couple, Join) ===
const singleModal = document.getElementById("singleModal");
const coupleModal = document.getElementById("coupleModal");
const joinModal = document.getElementById("joinModal");

const btnSingle = document.querySelector(".trigger-single");
const btnCouple = document.querySelector(".trigger-couple");
const btnJoinList = document.querySelectorAll(".trigger-join");

const closeSingle = document.querySelector(".close-single");
const closeCouple = document.querySelector(".close-couple");
const closeJoin = document.querySelector(".close-join");

if(btnSingle) btnSingle.addEventListener("click", (e) => { e.preventDefault(); singleModal.style.display = "flex"; });
if(btnCouple) btnCouple.addEventListener("click", (e) => { e.preventDefault(); coupleModal.style.display = "flex"; });

btnJoinList.forEach(btn => {
    btn.addEventListener("click", (e) => {
        e.preventDefault();
        // Close nav if open
        const navLinks = document.getElementById('navLinks');
        if(navLinks) navLinks.classList.remove('nav-active');
        joinModal.style.display = "flex";
    });
});

if(closeSingle) closeSingle.addEventListener("click", () => { singleModal.style.display = "none"; });
if(closeCouple) closeCouple.addEventListener("click", () => { coupleModal.style.display = "none"; });
if(closeJoin) closeJoin.addEventListener("click", () => { joinModal.style.display = "none"; });

window.addEventListener("click", (e) => {
    if (e.target == singleModal) singleModal.style.display = "none";
    if (e.target == coupleModal) coupleModal.style.display = "none";
    if (e.target == joinModal) joinModal.style.display = "none";
});

// === NAV SCROLL ===
const mainHeader = document.querySelector('.main-header');
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) mainHeader.classList.add('scrolled');
    else mainHeader.classList.remove('scrolled');
});

// === MOBILE MENU ===
const hamburger = document.getElementById('hamburgerBtn');
const navLinks = document.getElementById('navLinks');
const closeMenu = document.getElementById('closeMenuBtn');
if(hamburger) hamburger.addEventListener('click', () => navLinks.classList.add('nav-active'));
if(closeMenu) closeMenu.addEventListener('click', () => navLinks.classList.remove('nav-active'));
document.querySelectorAll('.nav-links a').forEach(link => link.addEventListener('click', () => navLinks.classList.remove('nav-active')));

// === POPUP & TIMER ===
const popup = document.getElementById('livePopup');
const popupText = document.getElementById('popupText');
const msg = ["Rahul from Delhi unlocked his Report", "Sneha from Mumbai found her Soulmate", "Amit from Pune checked Karmic Debt", "Riya from Bangalore joined the Beta", "Vikram found his Life Purpose"];
let i = 0;
setInterval(() => {
    if(popup && popupText) {
        popupText.innerHTML = msg[i]; i = (i+1)%msg.length;
        popup.classList.add('show');
        setTimeout(() => popup.classList.remove('show'), 5000);
    }
}, 25000);

const timerDisplay = document.getElementById('timer');
if(timerDisplay) {
    let t = 900;
    setInterval(() => {
        let m = Math.floor(t/60), s = t%60;
        timerDisplay.innerText = `${m}:${s<10?'0':''}${s}`;
        if(--t < 0) t = 900;
    }, 1000);
}