from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

users = {
    "admin": "password123"
}

state = {
    'Cashier': 'C001',
    'Registrar': 'R001'
}

login_html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PGPC Queue System — Login</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Oxanium:wght@400;600;700;800&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --navy:    #060d1f;
      --cyan:    #00d4ff;
      --amber:   #f5a623;
      --text:    #e2e8f0;
      --text2:   #8899aa;
      --glass-bg: rgba(13, 24, 48, 0.72);
      --glass-border: rgba(0, 212, 255, 0.15);
      --red:     #ff4f6d;
      --green:   #00e676;
    }

    body, html {
      height: 100%;
      font-family: 'DM Sans', sans-serif;
      background: var(--navy);
      color: var(--text);
      display: flex;
      justify-content: center;
      align-items: center;
      overflow: hidden;
    }

    .bg {
      position: fixed;
      inset: 0;
      z-index: 0;
      background: var(--navy);
      overflow: hidden;
    }
    .bg::before {
      content: '';
      position: absolute;
      width: 800px; height: 800px;
      top: -200px; left: -200px;
      background: radial-gradient(circle, rgba(0,212,255,0.07) 0%, transparent 65%);
      animation: drift1 18s ease-in-out infinite alternate;
    }
    .bg::after {
      content: '';
      position: absolute;
      width: 600px; height: 600px;
      bottom: -100px; right: -100px;
      background: radial-gradient(circle, rgba(245,166,35,0.06) 0%, transparent 65%);
      animation: drift2 22s ease-in-out infinite alternate;
    }
    .grid-lines {
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(rgba(0,212,255,0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,212,255,0.035) 1px, transparent 1px);
      background-size: 60px 60px;
    }

    @keyframes drift1 { from { transform: translate(0,0); } to { transform: translate(80px,60px); } }
    @keyframes drift2 { from { transform: translate(0,0); } to { transform: translate(-60px,-80px); } }

    .card {
      position: relative;
      z-index: 1;
      width: 400px;
      padding: 48px 40px;
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      box-shadow: 0 0 60px rgba(0,212,255,0.05), 0 32px 64px rgba(0,0,0,0.5);
      animation: fadeUp 0.6s cubic-bezier(0.16,1,0.3,1) both;
    }
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(24px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .logo-wrap {
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 32px;
      gap: 12px;
    }
    .logo-icon {
      width: 48px; height: 48px;
      border-radius: 14px;
      background: rgba(0,212,255,0.1);
      border: 1px solid rgba(0,212,255,0.3);
      display: flex; align-items: center; justify-content: center;
    }
    .logo-icon svg {
      width: 26px; height: 26px;
      stroke: var(--cyan);
      stroke-width: 1.8;
      fill: none;
    }
    .logo-text { display: flex; flex-direction: column; }
    .logo-title {
      font-family: 'Oxanium', sans-serif;
      font-weight: 800;
      font-size: 1.3rem;
      color: var(--text);
      line-height: 1;
      letter-spacing: 0.04em;
    }
    .logo-sub {
      font-size: 0.7rem;
      color: var(--cyan);
      letter-spacing: 0.12em;
      text-transform: uppercase;
      font-weight: 500;
      margin-top: 3px;
    }

    h2 {
      font-family: 'Oxanium', sans-serif;
      font-weight: 700;
      font-size: 1.05rem;
      color: var(--text2);
      text-align: center;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 10px;
    }

    .divider {
      width: 60px; height: 1px;
      background: linear-gradient(90deg, transparent, var(--cyan), transparent);
      margin: 0 auto 28px;
    }

    .field {
      margin-bottom: 18px;
    }
    .field label {
      display: block;
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--text2);
      margin-bottom: 8px;
    }
    .field input {
      width: 100%;
      padding: 13px 16px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 10px;
      color: var(--text);
      font-family: 'DM Sans', sans-serif;
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.3s ease, box-shadow 0.3s ease, background 0.3s ease;
    }
    .field input:focus {
      border-color: var(--cyan);
      background: rgba(0,212,255,0.04);
      box-shadow: 0 0 0 3px rgba(0,212,255,0.1);
    }
    .field input::placeholder { color: rgba(136,153,170,0.45); }

    .btn-login {
      width: 100%;
      padding: 14px 0;
      margin-top: 8px;
      background: linear-gradient(135deg, #00d4ff, #0099cc);
      border: none;
      border-radius: 10px;
      color: #060d1f;
      font-family: 'Oxanium', sans-serif;
      font-weight: 700;
      font-size: 1rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      cursor: pointer;
      position: relative;
      overflow: hidden;
      transition: transform 0.2s ease, box-shadow 0.3s ease;
      box-shadow: 0 4px 24px rgba(0,212,255,0.28);
    }
    .btn-login::before {
      content: '';
      position: absolute;
      top: 0; left: -100%;
      width: 100%; height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent);
      transition: left 0.45s ease;
    }
    .btn-login:hover::before { left: 100%; }
    .btn-login:hover { transform: translateY(-1px); box-shadow: 0 8px 32px rgba(0,212,255,0.38); }
    .btn-login:active { transform: translateY(0); }
    .btn-login:disabled { opacity: 0.55; cursor: not-allowed; }

    .message {
      margin-top: 16px;
      text-align: center;
      font-size: 0.875rem;
      font-weight: 500;
      min-height: 22px;
    }
    .message.error { color: var(--red); }
    .message.success { color: var(--green); }

    .clock {
      margin-top: 20px;
      text-align: center;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.73rem;
      color: var(--text2);
      letter-spacing: 0.04em;
      opacity: 0.55;
    }
  </style>
</head>
<body>
  <div class="bg"><div class="grid-lines"></div></div>

  <div class="card">
    <div class="logo-wrap">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24">
          <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/>
          <rect x="9" y="3" width="6" height="4" rx="1"/>
          <path d="M9 12h6M9 16h4"/>
        </svg>
      </div>
      <div class="logo-text">
        <span class="logo-title">PGPC</span>
        <span class="logo-sub">Queue System</span>
      </div>
    </div>

    <h2>Admin Access</h2>
    <div class="divider"></div>

    <div class="field">
      <label for="username">Username</label>
      <input id="username" type="text" placeholder="Enter username" autocomplete="username" />
    </div>
    <div class="field">
      <label for="password">Password</label>
      <input id="password" type="password" placeholder="Enter password" autocomplete="current-password" />
    </div>

    <button class="btn-login" id="loginBtn">Sign In</button>
    <div id="message" class="message"></div>
    <div id="currentTime" class="clock"></div>
  </div>

  <script>
    const loginBtn = document.getElementById('loginBtn');
    const message = document.getElementById('message');

    document.addEventListener('keydown', (e) => { if (e.key === 'Enter') loginBtn.click(); });

    loginBtn.addEventListener('click', async () => {
      message.textContent = '';
      message.className = 'message';
      const username = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value.trim();

      if (!username || !password) {
        message.textContent = 'Please enter both username and password.';
        message.classList.add('error');
        return;
      }

      loginBtn.disabled = true;
      loginBtn.textContent = 'Authenticating...';

      try {
        const response = await fetch('/api/login', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          credentials: 'include',
          body: JSON.stringify({username, password}),
        });
        const data = await response.json();

        if (response.ok) {
          message.textContent = 'Access granted. Redirecting...';
          message.classList.add('success');
          setTimeout(() => { window.location.href = '/admin'; }, 1200);
        } else {
          loginBtn.disabled = false;
          loginBtn.textContent = 'Sign In';
          message.textContent = data.error || 'Authentication failed.';
          message.classList.add('error');
        }
      } catch (e) {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Sign In';
        message.textContent = 'Connection error. Please try again.';
        message.classList.add('error');
      }
    });

    function showTime() {
      const now = new Date();
      document.getElementById('currentTime').textContent = now.toLocaleString('en-US', {
        weekday:'short', year:'numeric', month:'short', day:'numeric',
        hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:false
      });
    }
    showTime();
    setInterval(showTime, 1000);
  </script>
</body>
</html>
"""

admin_html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PGPC Queue System — Admin Panel</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Oxanium:wght@400;600;700;800&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --navy:    #060d1f;
      --navy2:   #0d1830;
      --cyan:    #00d4ff;
      --amber:   #f5a623;
      --text:    #e2e8f0;
      --text2:   #8899aa;
      --glass:   rgba(13,24,48,0.72);
      --glass-border: rgba(0,212,255,0.12);
      --red:     #ff4f6d;
      --green:   #00e676;
    }

    body, html {
      min-height: 100vh;
      font-family: 'DM Sans', sans-serif;
      background: var(--navy);
      color: var(--text);
      overflow-x: hidden;
    }

    .bg {
      position: fixed;
      inset: 0;
      z-index: 0;
      pointer-events: none;
    }
    .bg-blob1 {
      position: absolute;
      width: 900px; height: 900px;
      top: -300px; left: -200px;
      background: radial-gradient(circle, rgba(0,212,255,0.055) 0%, transparent 65%);
      animation: drift1 20s ease-in-out infinite alternate;
    }
    .bg-blob2 {
      position: absolute;
      width: 700px; height: 700px;
      bottom: -200px; right: -100px;
      background: radial-gradient(circle, rgba(245,166,35,0.05) 0%, transparent 65%);
      animation: drift2 25s ease-in-out infinite alternate;
    }
    .grid-lines {
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
      background-size: 60px 60px;
    }
    @keyframes drift1 { from { transform: translate(0,0); } to { transform: translate(60px,40px); } }
    @keyframes drift2 { from { transform: translate(0,0); } to { transform: translate(-40px,-60px); } }

    .layout {
      position: relative;
      z-index: 1;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* ── Header ── */
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 18px 32px;
      background: rgba(6,13,31,0.9);
      border-bottom: 1px solid var(--glass-border);
      backdrop-filter: blur(20px);
      position: sticky;
      top: 0;
      z-index: 10;
    }
    .header-left { display: flex; align-items: center; gap: 14px; }
    .logo-icon {
      width: 42px; height: 42px;
      border-radius: 12px;
      background: rgba(0,212,255,0.1);
      border: 1px solid rgba(0,212,255,0.25);
      display: flex; align-items: center; justify-content: center;
    }
    .logo-icon svg { width: 22px; height: 22px; stroke: var(--cyan); stroke-width: 1.8; fill: none; }
    .brand { display: flex; flex-direction: column; }
    .brand-title {
      font-family: 'Oxanium', sans-serif;
      font-weight: 800;
      font-size: 1.1rem;
      color: var(--text);
      letter-spacing: 0.04em;
      line-height: 1;
    }
    .brand-sub {
      font-size: 0.67rem;
      color: var(--cyan);
      letter-spacing: 0.13em;
      text-transform: uppercase;
      font-weight: 500;
      margin-top: 2px;
    }

    .header-center { text-align: center; }
    .header-title {
      font-family: 'Oxanium', sans-serif;
      font-weight: 700;
      font-size: 1rem;
      color: var(--text);
      letter-spacing: 0.07em;
      text-transform: uppercase;
    }
    #liveTime {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.74rem;
      color: var(--text2);
      margin-top: 3px;
    }

    .header-right { display: flex; align-items: center; gap: 10px; }
    .status-dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      background: var(--green);
      box-shadow: 0 0 8px rgba(0,230,118,0.7);
      animation: pulseDot 2s ease-in-out infinite;
    }
    @keyframes pulseDot {
      0%,100% { opacity:1; transform:scale(1); }
      50% { opacity:0.55; transform:scale(0.8); }
    }
    .status-label { font-size: 0.78rem; color: var(--green); font-weight: 500; }

    .btn-icon {
      display: flex; align-items: center; gap: 6px;
      padding: 9px 16px;
      border-radius: 9px;
      border: 1px solid rgba(255,255,255,0.1);
      background: rgba(255,255,255,0.04);
      color: var(--text2);
      font-family: 'DM Sans', sans-serif;
      font-size: 0.82rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .btn-icon:hover {
      border-color: rgba(255,79,109,0.45);
      background: rgba(255,79,109,0.07);
      color: var(--red);
    }
    .btn-icon svg { width: 16px; height: 16px; stroke: currentColor; stroke-width: 2; fill: none; }

    /* ── Main ── */
    main {
      flex: 1;
      padding: 36px 32px;
      max-width: 1200px;
      margin: 0 auto;
      width: 100%;
    }

    .section-label {
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--text2);
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .section-label::after {
      content: '';
      flex: 1;
      height: 1px;
      background: linear-gradient(90deg, var(--glass-border), transparent);
    }

    /* ── Office cards ── */
    .offices-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      margin-bottom: 32px;
    }

    .office-card {
      background: var(--glass);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      padding: 28px;
      backdrop-filter: blur(20px);
      transition: border-color 0.3s ease, box-shadow 0.3s ease;
      animation: fadeUp 0.5s cubic-bezier(0.16,1,0.3,1) both;
    }
    .office-card:hover {
      border-color: rgba(0,212,255,0.22);
      box-shadow: 0 8px 40px rgba(0,212,255,0.055);
    }
    @keyframes fadeUp {
      from { opacity:0; transform:translateY(16px); }
      to   { opacity:1; transform:translateY(0); }
    }
    .office-card:nth-child(1) { animation-delay:0.05s; }
    .office-card:nth-child(2) { animation-delay:0.12s; }
    .office-card:nth-child(3) { animation-delay:0.19s; }
    .office-card:nth-child(4) { animation-delay:0.26s; }

    .card-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      margin-bottom: 24px;
    }
    .office-name {
      font-family: 'Oxanium', sans-serif;
      font-weight: 700;
      font-size: 1.15rem;
      color: var(--text);
      letter-spacing: 0.04em;
    }
    .office-subtitle { font-size: 0.77rem; color: var(--text2); margin-top: 4px; }
    .office-badge {
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      background: rgba(0,230,118,0.1);
      border: 1px solid rgba(0,230,118,0.22);
      color: var(--green);
      white-space: nowrap;
    }

    .ticket-display {
      text-align: center;
      margin: 0 0 24px;
      padding: 22px 16px;
      background: rgba(0,0,0,0.22);
      border-radius: 14px;
      border: 1px solid rgba(0,212,255,0.08);
      position: relative;
      overflow: hidden;
    }
    .ticket-display::before {
      content: '';
      position: absolute;
      top: 0; left: 50%;
      transform: translateX(-50%);
      width: 70%; height: 1px;
      background: linear-gradient(90deg, transparent, rgba(0,212,255,0.4), transparent);
    }
    .ticket-label {
      font-size: 0.67rem;
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--text2);
      margin-bottom: 10px;
    }
    .ticket-number {
      font-family: 'JetBrains Mono', monospace;
      font-size: 3.6rem;
      font-weight: 700;
      color: var(--cyan);
      line-height: 1;
      text-shadow: 0 0 40px rgba(0,212,255,0.35);
      letter-spacing: 0.08em;
      transition: all 0.35s ease;
    }
    .ticket-number.updated {
      animation: ticketPop 0.45s cubic-bezier(0.34,1.56,0.64,1);
    }
    @keyframes ticketPop {
      0%   { transform:scale(0.82); opacity:0.3; }
      60%  { transform:scale(1.07); }
      100% { transform:scale(1);    opacity:1; }
    }

    .card-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .btn-action {
      padding: 12px 0;
      border: none;
      border-radius: 10px;
      font-family: 'DM Sans', sans-serif;
      font-weight: 600;
      font-size: 0.88rem;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      position: relative;
      overflow: hidden;
    }
    .btn-action svg { width: 15px; height: 15px; stroke: currentColor; stroke-width: 2; fill: none; flex-shrink:0; }
    .btn-action:active { transform: scale(0.97); }

    .btn-next {
      background: rgba(0,212,255,0.1);
      border: 1px solid rgba(0,212,255,0.28);
      color: var(--cyan);
    }
    .btn-next:hover {
      background: rgba(0,212,255,0.18);
      box-shadow: 0 4px 20px rgba(0,212,255,0.18);
    }

    .btn-recall {
      background: rgba(245,166,35,0.1);
      border: 1px solid rgba(245,166,35,0.25);
      color: var(--amber);
    }
    .btn-recall:hover {
      background: rgba(245,166,35,0.18);
      box-shadow: 0 4px 20px rgba(245,166,35,0.14);
    }

    /* ── Control panel ── */
    .control-panel {
      background: var(--glass);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      padding: 24px 28px;
      backdrop-filter: blur(20px);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
      animation: fadeUp 0.5s 0.3s cubic-bezier(0.16,1,0.3,1) both;
    }
    .panel-title {
      font-family: 'Oxanium', sans-serif;
      font-weight: 600;
      font-size: 0.95rem;
      color: var(--text);
    }
    .panel-desc { font-size: 0.78rem; color: var(--text2); margin-top: 3px; }

    .btn-danger {
      display: flex; align-items: center; gap: 8px;
      padding: 12px 22px;
      background: rgba(255,79,109,0.08);
      border: 1px solid rgba(255,79,109,0.22);
      border-radius: 10px;
      color: var(--red);
      font-family: 'DM Sans', sans-serif;
      font-weight: 600;
      font-size: 0.88rem;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }
    .btn-danger svg { width: 15px; height: 15px; stroke: currentColor; stroke-width: 2; fill: none; }
    .btn-danger:hover {
      background: rgba(255,79,109,0.16);
      box-shadow: 0 4px 20px rgba(255,79,109,0.14);
      border-color: rgba(255,79,109,0.45);
    }
    .btn-danger:active { transform: scale(0.97); }

    /* ── Status toast ── */
    #statusBar {
      position: fixed;
      bottom: 28px;
      left: 50%;
      transform: translateX(-50%) translateY(100px);
      background: rgba(10,20,42,0.96);
      border: 1px solid var(--glass-border);
      border-radius: 12px;
      padding: 12px 24px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.82rem;
      color: var(--cyan);
      backdrop-filter: blur(20px);
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
      z-index: 100;
      transition: transform 0.4s cubic-bezier(0.34,1.56,0.64,1), opacity 0.3s;
      white-space: nowrap;
      max-width: 90vw;
    }
    #statusBar.visible { transform: translateX(-50%) translateY(0); }
    #statusBar.error   { color: var(--red);   border-color: rgba(255,79,109,0.3); }
    #statusBar.warning { color: var(--amber);  border-color: rgba(245,166,35,0.3); }

    /* ── Responsive ── */
    @media (max-width: 720px) {
      header { padding: 14px 18px; }
      .header-center { display: none; }
      main { padding: 24px 16px; }
      .offices-grid { grid-template-columns: 1fr; }
      .ticket-number { font-size: 2.8rem; }
      .control-panel { flex-direction: column; align-items: flex-start; }
    }

    .sr-only { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); border:0; }
  </style>
</head>
<body>
<div class="bg">
  <div class="bg-blob1"></div>
  <div class="bg-blob2"></div>
  <div class="grid-lines"></div>
</div>

<div class="layout">
  <header>
    <div class="header-left">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24">
          <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/>
          <rect x="9" y="3" width="6" height="4" rx="1"/>
          <path d="M9 12h6M9 16h4"/>
        </svg>
      </div>
      <div class="brand">
        <span class="brand-title">PGPC</span>
        <span class="brand-sub">Queue System</span>
      </div>
    </div>

    <div class="header-center">
      <div class="header-title">Admin Panel</div>
      <div id="liveTime"></div>
    </div>

    <div class="header-right">
      <div class="status-dot" aria-hidden="true"></div>
      <span class="status-label">System Online</span>
      <button class="btn-icon" id="logoutBtn" aria-label="Logout">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
        Logout
      </button>
    </div>
  </header>

  <main>
    <div class="section-label">Active Queues</div>

    <div class="offices-grid" role="list">
      {%- for office in offices %}
      <div class="office-card" role="listitem">
        <div class="card-top">
          <div>
            <div class="office-name">{{ office }}</div>
            <div class="office-subtitle">Window 1 &nbsp;·&nbsp; Counter Operations</div>
          </div>
          <div class="office-badge">Active</div>
        </div>

        <div class="ticket-display" aria-label="{{ office }} current ticket">
          <div class="ticket-label">Now Serving</div>
          <div class="ticket-number" id="ticket-{{ office }}">{{ state.get(office, '----') }}</div>
        </div>

        <div class="card-actions">
          <button class="btn-action btn-next" data-office="{{ office }}" aria-label="Next ticket for {{ office }}">
            <svg viewBox="0 0 24 24" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>
            Next
          </button>
          <button class="btn-action btn-recall" data-office="{{ office }}" aria-label="Recall ticket for {{ office }}">
            <svg viewBox="0 0 24 24" aria-hidden="true"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.54"/></svg>
            Recall
          </button>
        </div>
      </div>
      {%- endfor %}
    </div>

    <div class="section-label">System Controls</div>

    <div class="control-panel">
      <div>
        <div class="panel-title">Reset All Counters</div>
        <div class="panel-desc">Clears all ticket numbers and restarts queue from zero</div>
      </div>
      <button class="btn-danger" id="resetBtn">
        <svg viewBox="0 0 24 24" aria-hidden="true"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.54"/></svg>
        Reset System
      </button>
    </div>
  </main>
</div>

<div id="statusBar" role="status" aria-live="polite"></div>

<script>
  const notificationSound = new Audio('ding-dong-81717.mp3');
  notificationSound.preload = 'auto';
  notificationSound.volume = 1.0;

  function playSound() {
    notificationSound.pause();
    notificationSound.currentTime = 0;
    notificationSound.play().catch(() => {});
  }

  let statusTimer = null;
  function showStatus(msg, type='') {
    const bar = document.getElementById('statusBar');
    bar.textContent = msg;
    bar.className = 'visible' + (type ? ' ' + type : '');
    clearTimeout(statusTimer);
    statusTimer = setTimeout(() => { bar.className = ''; }, 4000);
  }

  function updateUI(state) {
    Object.keys(state).forEach(office => {
      const el = document.getElementById('ticket-' + office);
      if (el && el.textContent !== state[office]) {
        el.textContent = state[office] || '----';
        el.classList.remove('updated');
        void el.offsetWidth;
        el.classList.add('updated');
      }
    });
  }

  async function sendAction(action, office=null) {
    const body = office ? { office } : {};
    try {
      const res = await fetch('/api/' + action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (data.success) {
        updateUI(data.state);
        showStatus(data.message, action === 'reset' ? 'warning' : '');
        if (action === 'next' && office) playSound();
      } else {
        showStatus('Error: ' + data.message, 'error');
      }
    } catch (e) {
      showStatus('Connection error.', 'error');
    }
  }

  document.querySelectorAll('.btn-next').forEach(btn => {
    btn.addEventListener('click', () => sendAction('next', btn.dataset.office));
  });
  document.querySelectorAll('.btn-recall').forEach(btn => {
    btn.addEventListener('click', () => sendAction('recall', btn.dataset.office));
  });
  document.getElementById('resetBtn').addEventListener('click', () => {
    if (confirm('Reset all counters? This cannot be undone.')) sendAction('reset');
  });
  document.getElementById('logoutBtn').addEventListener('click', () => {
    window.location.href = '/';
  });

  function showTime() {
    document.getElementById('liveTime').textContent = new Date().toLocaleString('en-US', {
      weekday:'short', month:'short', day:'numeric',
      hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:false
    });
  }
  showTime();
  setInterval(showTime, 1000);

  async function loadState() {
    try {
      const res = await fetch('/api/state');
      const data = await res.json();
      if (data.success) updateUI(data.state);
    } catch(e) {}
  }
  loadState();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(login_html_template)

@app.route('/admin')
def admin_panel():
    return render_template_string(admin_html_template, offices=list(state.keys()), state=state)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username in users and users[username] == password:
        return jsonify({"message": "Login successful!"}), 200
    else:
        return jsonify({"error": "Invalid username or password."}), 401

@app.route('/api/state')
def get_state():
    return jsonify(success=True, state=state)

@app.route('/api/next', methods=['POST'])
def next_ticket():
    data = request.get_json() or {}
    office = data.get('office')
    if office not in state:
        return jsonify(success=False, message='Invalid office')
    current_ticket = state[office]
    num = int(current_ticket[1:]) if current_ticket != '----' else 0
    num += 1
    state[office] = office[0].upper() + str(num).zfill(3)
    message = f"Now serving {state[office]} at {office} 1"
    return jsonify(success=True, message=message, state=state)

@app.route('/api/recall', methods=['POST'])
def recall_ticket():
    data = request.get_json() or {}
    office = data.get('office')
    if office not in state:
        return jsonify(success=False, message='Invalid office')
    current_ticket = state[office]
    if current_ticket == '----':
        message = f"No current ticket to recall at {office} 1"
    else:
        message = f"Recalling ticket {current_ticket} at {office} 1"
    return jsonify(success=True, message=message, state=state)

@app.route('/api/reset', methods=['POST'])
def reset_system():
    for office in state:
        state[office] = '----'
    return jsonify(success=True, message='All counters have been reset.', state=state)

if __name__ == '__main__':
    app.run(debug=True, port=5000)