from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ── Auth ──────────────────────────────────────────────────────────────────────
USERS = {"admin": "password123"}

# ── Application State ─────────────────────────────────────────────────────────
offices_data = {
    'Cashier':   {'current': 'C001', 'served': 0, 'prefix': 'C', 'priority': 0},
    'Registrar': {'current': 'R001', 'served': 0, 'prefix': 'R', 'priority': 0},
}
HISTORY = []

def push_history(action_type, office, ticket):
    HISTORY.insert(0, {
        'time': datetime.now().strftime('%H:%M:%S'),
        'type': action_type, 'office': office, 'ticket': ticket
    })
    while len(HISTORY) > 50: HISTORY.pop()

def snapshot():
    return {k: v['current'] for k, v in offices_data.items()}

def served_map():
    return {k: v['served'] for k, v in offices_data.items()}

# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>PGPC Queue System — Login</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Oxanium:wght@400;600;700;800&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    :root{
      --navy:#030816; --navy2:#060d1f; --royal:#1a3a8f;
      --gold:#c9a227; --gold-l:#f0c840; --gold-d:#8a6913;
      --gold-pale:rgba(201,162,39,.12); --gold-bd:rgba(201,162,39,.25);
      --glass:rgba(10,18,60,.78); --text:#f0f4ff; --text2:#7a8ab0;
      --red:#ff4f6d; --green:#00e676;
    }
    html,body{height:100%;background:var(--navy);color:var(--text);
      font-family:'DM Sans',sans-serif;display:flex;justify-content:center;
      align-items:center;overflow:hidden}
    /* Background */
    .bg{position:fixed;inset:0;z-index:0;
      background:radial-gradient(ellipse at 20% 25%,rgba(26,58,143,.35) 0%,transparent 55%),
                 radial-gradient(ellipse at 80% 75%,rgba(201,162,39,.08) 0%,transparent 55%),
                 var(--navy)}
    .grid{position:absolute;inset:0;
      background-image:linear-gradient(rgba(201,162,39,.028) 1px,transparent 1px),
                       linear-gradient(90deg,rgba(201,162,39,.028) 1px,transparent 1px);
      background-size:64px 64px}
    canvas#ptx{position:fixed;inset:0;pointer-events:none;z-index:0}
    /* Card */
    .card{position:relative;z-index:2;width:420px;padding:52px 44px;
      background:var(--glass);border:1px solid var(--gold-bd);border-radius:24px;
      backdrop-filter:blur(28px);-webkit-backdrop-filter:blur(28px);
      box-shadow:0 0 0 1px rgba(201,162,39,.06),0 0 80px rgba(201,162,39,.07),0 32px 80px rgba(0,0,0,.65);
      animation:cardIn .7s cubic-bezier(.16,1,.3,1) both}
    @keyframes cardIn{from{opacity:0;transform:translateY(32px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}
    /* Corner brackets */
    .card::before,.card::after{content:'';position:absolute;width:22px;height:22px;border-color:var(--gold);border-style:solid;border-width:0}
    .card::before{top:14px;left:14px;border-top-width:2px;border-left-width:2px;border-radius:4px 0 0 0;opacity:.6}
    .card::after{bottom:14px;right:14px;border-bottom-width:2px;border-right-width:2px;border-radius:0 0 4px 0;opacity:.6}
    /* Emblem */
    .emblem{display:flex;flex-direction:column;align-items:center;margin-bottom:36px;gap:10px}
    .emblem-ring{width:80px;height:80px;border-radius:50%;
      background:radial-gradient(circle,rgba(26,58,143,.5),rgba(201,162,39,.1));
      border:2px solid var(--gold-bd);display:flex;align-items:center;justify-content:center;
      position:relative;box-shadow:0 0 0 4px rgba(201,162,39,.06),0 0 32px rgba(201,162,39,.1);
      animation:ringPulse 4s ease-in-out infinite}
    @keyframes ringPulse{0%,100%{box-shadow:0 0 0 4px rgba(201,162,39,.06),0 0 32px rgba(201,162,39,.1)}
      50%{box-shadow:0 0 0 6px rgba(201,162,39,.1),0 0 48px rgba(201,162,39,.18)}}
    .emblem-ring::before{content:'';position:absolute;inset:5px;border-radius:50%;
      border:1px solid rgba(201,162,39,.18)}
    .emblem-ring svg{width:40px;height:40px}
    .school-name{font-family:'Cinzel',serif;font-weight:700;font-size:1.1rem;
      color:var(--gold-l);letter-spacing:.1em;text-align:center;line-height:1.3;
      text-shadow:0 0 20px rgba(201,162,39,.3)}
    .school-tag{font-size:.63rem;font-weight:600;letter-spacing:.2em;text-transform:uppercase;
      color:var(--text2);text-align:center;margin-top:2px}
    .divider{width:80px;height:1px;
      background:linear-gradient(90deg,transparent,var(--gold),transparent);
      margin:0 auto 28px;opacity:.4}
    .form-title{font-family:'Oxanium',sans-serif;font-weight:700;font-size:.82rem;
      letter-spacing:.15em;text-transform:uppercase;color:var(--text2);text-align:center;margin-bottom:22px}
    /* Fields */
    .field{margin-bottom:16px}
    .field label{display:block;font-size:.67rem;font-weight:600;letter-spacing:.12em;
      text-transform:uppercase;color:var(--text2);margin-bottom:8px}
    .field input{width:100%;padding:13px 16px;background:rgba(255,255,255,.04);
      border:1px solid rgba(201,162,39,.18);border-radius:10px;color:var(--text);
      font-family:'DM Sans',sans-serif;font-size:.95rem;outline:none;
      transition:border-color .3s,box-shadow .3s,background .3s}
    .field input:focus{border-color:var(--gold);background:rgba(201,162,39,.04);
      box-shadow:0 0 0 3px rgba(201,162,39,.14)}
    .field input::placeholder{color:rgba(122,138,176,.4)}
    /* Login button */
    .btn-login{width:100%;padding:14px 0;margin-top:10px;
      background:linear-gradient(135deg,#c9a227,#8a6913);
      border:none;border-radius:10px;color:#030816;
      font-family:'Oxanium',sans-serif;font-weight:800;font-size:.98rem;
      letter-spacing:.1em;text-transform:uppercase;cursor:pointer;
      position:relative;overflow:hidden;
      transition:transform .2s,box-shadow .3s;
      box-shadow:0 4px 24px rgba(201,162,39,.3)}
    .btn-login::before{content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;
      background:linear-gradient(90deg,transparent,rgba(255,255,255,.22),transparent);
      transition:left .5s ease}
    .btn-login:hover::before{left:100%}
    .btn-login:hover{transform:translateY(-2px);box-shadow:0 8px 36px rgba(201,162,39,.42)}
    .btn-login:active{transform:scale(.98)}
    .btn-login:disabled{opacity:.55;cursor:not-allowed;pointer-events:none}
    .message{margin-top:14px;text-align:center;font-size:.83rem;font-weight:500;min-height:20px}
    .message.error{color:var(--red)}.message.success{color:var(--green)}
    .clock{margin-top:20px;text-align:center;font-family:'JetBrains Mono',monospace;
      font-size:.72rem;color:var(--text2);opacity:.5;letter-spacing:.03em}
    .footer-row{margin-top:22px;text-align:center;font-size:.68rem;color:var(--text2);opacity:.45}
    .footer-row a{color:var(--gold);text-decoration:none;opacity:.7;transition:opacity .2s}
    .footer-row a:hover{opacity:1}
  </style>
</head>
<body>
<div class="bg"><div class="grid"></div></div>
<canvas id="ptx"></canvas>
<div class="card">
  <div class="emblem">
    <div class="emblem-ring">
      <svg viewBox="0 0 40 40" fill="none">
        <!-- Flame -->
        <path d="M20 3C18.5 7 16 8.5 17 12C18 15.5 20 16 20 16C20 16 22 15.5 23 12C24 8.5 21.5 7 20 3Z" fill="#f0c840" opacity=".95"/>
        <path d="M20 8C19 10.5 17.5 11.5 18.5 13.5C19.2 15 20 15.5 20 15.5C20 15.5 20.8 15 21.5 13.5C22.5 11.5 21 10.5 20 8Z" fill="#c9a227"/>
        <!-- Torch body -->
        <rect x="18.5" y="16" width="3" height="8" rx=".8" fill="#c9a227"/>
        <!-- Torch base -->
        <rect x="15" y="24" width="10" height="3" rx="1.5" fill="#a07b15"/>
        <!-- Bull horns -->
        <path d="M13 19C10 16 9 20 11.5 21" stroke="#c9a227" stroke-width="1.5" stroke-linecap="round"/>
        <path d="M27 19C30 16 31 20 28.5 21" stroke="#c9a227" stroke-width="1.5" stroke-linecap="round"/>
        <!-- Book -->
        <path d="M12 34C12 32 14.5 32 17 32H20H23C25.5 32 28 32 28 34" stroke="#c9a227" stroke-width="1.3" stroke-linecap="round"/>
        <line x1="20" y1="32" x2="20" y2="34" stroke="#a07b15" stroke-width="1.3"/>
        <!-- Laurel dots -->
        <circle cx="7" cy="24" r="1" fill="#c9a227" opacity=".5"/>
        <circle cx="33" cy="24" r="1" fill="#c9a227" opacity=".5"/>
      </svg>
    </div>
    <div class="school-name">Padre Garcia<br>Polytechnic College</div>
    <div class="school-tag">Queue Management System</div>
  </div>
  <div class="divider"></div>
  <div class="form-title">Admin Access</div>
  <div class="field">
    <label for="usr">Username</label>
    <input id="usr" type="text" placeholder="Enter username" autocomplete="username"/>
  </div>
  <div class="field">
    <label for="pwd">Password</label>
    <input id="pwd" type="password" placeholder="Enter password" autocomplete="current-password"/>
  </div>
  <button class="btn-login" id="loginBtn">Sign In</button>
  <div id="msg" class="message"></div>
  <div id="clk" class="clock"></div>
  <div class="footer-row">
    <a href="/display" target="_blank">Queue Display Screen</a> &nbsp;·&nbsp; PGPC &copy; 2024
  </div>
</div>
<script>
(function(){
  const c=document.getElementById('ptx'),ctx=c.getContext('2d');
  let W,H,pts=[];
  function resize(){W=c.width=innerWidth;H=c.height=innerHeight}
  resize();addEventListener('resize',resize);
  function mk(){return{x:Math.random()*W,y:H+10,r:Math.random()*1.4+.4,
    vy:-(Math.random()*.5+.2),vx:(Math.random()-.5)*.3,
    a:Math.random()*.4+.08,life:0,max:Math.random()*200+150}}
  for(let i=0;i<45;i++){const p=mk();p.y=Math.random()*H;p.life=Math.random()*p.max;pts.push(p)}
  function tick(){
    ctx.clearRect(0,0,W,H);
    pts.forEach((p,i)=>{
      p.x+=p.vx;p.y+=p.vy;p.life++;
      const f=Math.min(p.life/30,1)*Math.min((p.max-p.life)/30,1);
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle=`rgba(201,162,39,${p.a*f})`;ctx.fill();
      if(p.life>=p.max)pts[i]=mk();
    });
    requestAnimationFrame(tick);
  }
  tick();
})();

const loginBtn=document.getElementById('loginBtn'),msgEl=document.getElementById('msg');
function showMsg(t,cls){msgEl.textContent=t;msgEl.className='message '+cls}
document.addEventListener('keydown',e=>{if(e.key==='Enter')loginBtn.click()});
loginBtn.addEventListener('click',async()=>{
  const u=document.getElementById('usr').value.trim();
  const p=document.getElementById('pwd').value.trim();
  if(!u||!p){showMsg('Please fill in all fields.','error');return}
  loginBtn.disabled=true;loginBtn.textContent='Authenticating…';showMsg('','');
  try{
    const r=await fetch('/api/login',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({username:u,password:p})});
    const d=await r.json();
    if(r.ok){showMsg('Access granted. Redirecting…','success');
      setTimeout(()=>{location.href='/admin'},1000)}
    else{loginBtn.disabled=false;loginBtn.textContent='Sign In';
      showMsg(d.message||'Authentication failed.','error')}
  }catch{loginBtn.disabled=false;loginBtn.textContent='Sign In';showMsg('Connection error.','error')}
});
function tick(){document.getElementById('clk').textContent=
  new Date().toLocaleString('en-US',{weekday:'short',year:'numeric',month:'short',
    day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false})}
tick();setInterval(tick,1000);
</script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN PANEL
# ══════════════════════════════════════════════════════════════════════════════
ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>PGPC Queue System — Admin</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Oxanium:wght@400;600;700;800&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    :root{
      --navy:#030816; --navy2:#060d1f; --royal:#1a3a8f;
      --gold:#c9a227; --gold-l:#f0c840; --gold-d:#8a6913;
      --gold-pale:rgba(201,162,39,.1); --gold-bd:rgba(201,162,39,.22);
      --glass:rgba(8,16,54,.72); --text:#f0f4ff; --text2:#7a8ab0;
      --red:#ff4f6d; --green:#00e676; --amber:#f5a623;
    }
    html,body{min-height:100vh;background:var(--navy);color:var(--text);
      font-family:'DM Sans',sans-serif;overflow-x:hidden}
    .bg{position:fixed;inset:0;z-index:0;pointer-events:none;
      background:radial-gradient(ellipse at 8% 18%,rgba(26,58,143,.28) 0%,transparent 50%),
                 radial-gradient(ellipse at 92% 82%,rgba(201,162,39,.07) 0%,transparent 50%),
                 var(--navy)}
    .grid{position:absolute;inset:0;
      background-image:linear-gradient(rgba(201,162,39,.022) 1px,transparent 1px),
                       linear-gradient(90deg,rgba(201,162,39,.022) 1px,transparent 1px);
      background-size:60px 60px}
    .layout{position:relative;z-index:1;min-height:100vh;display:flex;flex-direction:column}
    /* ── Header ── */
    header{display:flex;align-items:center;justify-content:space-between;
      padding:14px 28px;background:rgba(3,8,22,.95);
      border-bottom:1px solid var(--gold-bd);backdrop-filter:blur(20px);
      position:sticky;top:0;z-index:100;gap:12px}
    .h-left{display:flex;align-items:center;gap:12px}
    .h-logo{width:44px;height:44px;border-radius:50%;
      background:radial-gradient(circle,rgba(26,58,143,.5),rgba(201,162,39,.08));
      border:1.5px solid var(--gold-bd);display:flex;align-items:center;justify-content:center;
      flex-shrink:0}
    .h-logo svg{width:26px;height:26px}
    .h-brand{display:flex;flex-direction:column}
    .h-name{font-family:'Cinzel',serif;font-weight:700;font-size:.95rem;
      color:var(--gold-l);letter-spacing:.07em;line-height:1}
    .h-sub{font-size:.62rem;color:var(--text2);letter-spacing:.16em;text-transform:uppercase;
      font-weight:500;margin-top:2px}
    .h-center{text-align:center}
    .h-title{font-family:'Oxanium',sans-serif;font-weight:700;font-size:.88rem;
      color:var(--text);letter-spacing:.1em;text-transform:uppercase}
    #liveTime{font-family:'JetBrains Mono',monospace;font-size:.7rem;color:var(--text2);margin-top:3px}
    .h-right{display:flex;align-items:center;gap:8px}
    .status-dot{width:8px;height:8px;border-radius:50%;background:var(--green);
      box-shadow:0 0 8px rgba(0,230,118,.7);animation:pDot 2s ease-in-out infinite;flex-shrink:0}
    @keyframes pDot{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.75)}}
    .status-lbl{font-size:.73rem;color:var(--green);font-weight:500}
    .btn-hdr{display:flex;align-items:center;gap:5px;padding:7px 13px;border-radius:8px;
      border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);
      color:var(--text2);font-family:'DM Sans',sans-serif;font-size:.78rem;font-weight:500;
      cursor:pointer;transition:all .25s;white-space:nowrap}
    .btn-hdr:hover{background:rgba(255,255,255,.08);color:var(--text)}
    .btn-hdr.gold-on{border-color:rgba(201,162,39,.3);color:var(--gold)}
    .btn-hdr.danger:hover{border-color:rgba(255,79,109,.4);background:rgba(255,79,109,.07);color:var(--red)}
    .btn-hdr svg{width:14px;height:14px;stroke:currentColor;stroke-width:2;fill:none;flex-shrink:0}
    /* ── Stats bar ── */
    .stats-bar{display:flex;gap:1px;background:rgba(201,162,39,.07);
      border-bottom:1px solid var(--gold-bd);overflow-x:auto}
    .stat-cell{flex:1;min-width:110px;padding:9px 18px;text-align:center;
      background:rgba(3,8,22,.55);border-right:1px solid rgba(201,162,39,.07)}
    .stat-cell:last-child{border-right:none}
    .stat-v{font-family:'JetBrains Mono',monospace;font-size:1.05rem;font-weight:700;
      color:var(--gold-l);transition:all .35s}
    .stat-v.pop{animation:sPop .45s cubic-bezier(.34,1.56,.64,1)}
    @keyframes sPop{0%{transform:scale(.75)}60%{transform:scale(1.18)}100%{transform:scale(1)}}
    .stat-lbl{font-size:.6rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
      color:var(--text2);margin-top:2px}
    /* ── Main ── */
    main{flex:1;padding:28px;max-width:1400px;margin:0 auto;width:100%}
    .sec-label{font-size:.64rem;font-weight:600;letter-spacing:.17em;text-transform:uppercase;
      color:var(--text2);margin-bottom:14px;display:flex;align-items:center;gap:10px}
    .sec-label::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,var(--gold-bd),transparent)}
    .main-grid{display:grid;grid-template-columns:1fr 350px;gap:22px;align-items:start}
    @media(max-width:950px){.main-grid{grid-template-columns:1fr}}
    /* ── Office cards ── */
    .offices-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
      gap:16px;margin-bottom:22px}
    .o-card{background:var(--glass);border:1px solid var(--gold-bd);border-radius:20px;
      padding:24px;backdrop-filter:blur(20px);
      transition:border-color .3s,box-shadow .3s,transform .3s;
      animation:fadeUp .5s cubic-bezier(.16,1,.3,1) both;position:relative;overflow:hidden}
    .o-card::after{content:'';position:absolute;top:-70px;right:-70px;
      width:200px;height:200px;
      background:radial-gradient(circle,rgba(201,162,39,.055) 0%,transparent 65%);
      pointer-events:none}
    .o-card:hover{border-color:rgba(201,162,39,.4);box-shadow:0 8px 40px rgba(201,162,39,.09);
      transform:translateY(-2px)}
    .o-card.pulse-card{animation:cPulse .7s ease}
    @keyframes cPulse{0%,100%{box-shadow:none}50%{box-shadow:0 0 0 4px rgba(201,162,39,.2),0 0 30px rgba(201,162,39,.18)}}
    @keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
    .o-card:nth-child(1){animation-delay:.05s}.o-card:nth-child(2){animation-delay:.12s}
    .o-card:nth-child(3){animation-delay:.19s}.o-card:nth-child(4){animation-delay:.26s}
    .c-top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:18px;gap:8px}
    .o-name{font-family:'Oxanium',sans-serif;font-weight:700;font-size:1.05rem;
      color:var(--text);letter-spacing:.04em}
    .o-sub{font-size:.71rem;color:var(--text2);margin-top:3px}
    .badge-on{padding:3px 10px;border-radius:20px;font-size:.62rem;font-weight:600;
      letter-spacing:.08em;text-transform:uppercase;background:rgba(0,230,118,.1);
      border:1px solid rgba(0,230,118,.22);color:var(--green);white-space:nowrap}
    /* Ticket display */
    .t-display{text-align:center;margin-bottom:18px;padding:18px 14px;
      background:rgba(0,0,0,.3);border-radius:14px;border:1px solid rgba(201,162,39,.1);
      position:relative;overflow:hidden}
    .t-display::before{content:'';position:absolute;top:0;left:50%;transform:translateX(-50%);
      width:60%;height:1px;background:linear-gradient(90deg,transparent,rgba(201,162,39,.5),transparent)}
    .t-lbl{font-size:.62rem;font-weight:600;letter-spacing:.16em;text-transform:uppercase;
      color:var(--text2);margin-bottom:8px}
    .t-num{font-family:'JetBrains Mono',monospace;font-size:3.2rem;font-weight:700;
      color:var(--gold-l);line-height:1;
      text-shadow:0 0 40px rgba(201,162,39,.45),0 0 80px rgba(201,162,39,.15);
      letter-spacing:.08em;display:block;transition:all .3s}
    .t-num.flip{animation:tFlip .55s cubic-bezier(.34,1.56,.64,1)}
    @keyframes tFlip{0%{transform:translateY(-22px) scale(.8);opacity:.2}
      60%{transform:translateY(4px) scale(1.07);opacity:1}100%{transform:translateY(0) scale(1)}}
    .t-type{font-size:.66rem;color:var(--text2);margin-top:5px;letter-spacing:.06em}
    .t-type.priority{color:var(--amber)}
    /* Action buttons */
    .c-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}
    .btn-full{grid-column:1/-1}
    .btn-act{padding:11px 0;border-radius:10px;font-family:'DM Sans',sans-serif;
      font-weight:600;font-size:.82rem;cursor:pointer;display:flex;align-items:center;
      justify-content:center;gap:6px;transition:all .25s;position:relative;overflow:hidden;
      border:1px solid transparent}
    .btn-act svg{width:13px;height:13px;stroke:currentColor;stroke-width:2.2;fill:none;flex-shrink:0}
    .btn-act:active{transform:scale(.96)}
    .ripple{position:absolute;border-radius:50%;transform:scale(0);
      animation:ripAnim .55s linear;background:rgba(255,255,255,.18);pointer-events:none}
    @keyframes ripAnim{to{transform:scale(5);opacity:0}}
    .btn-next{background:rgba(201,162,39,.1);border-color:rgba(201,162,39,.3);color:var(--gold-l)}
    .btn-next:hover{background:rgba(201,162,39,.2);box-shadow:0 4px 20px rgba(201,162,39,.2)}
    .btn-recall{background:rgba(122,138,176,.1);border-color:rgba(122,138,176,.22);color:var(--text2)}
    .btn-recall:hover{background:rgba(122,138,176,.18)}
    .btn-priority{background:rgba(245,166,35,.08);border-color:rgba(245,166,35,.22);color:var(--amber);font-size:.78rem}
    .btn-priority:hover{background:rgba(245,166,35,.16);box-shadow:0 4px 16px rgba(245,166,35,.12)}
    /* ── Sidebar ── */
    .sidebar{display:flex;flex-direction:column;gap:14px}
    .panel{background:var(--glass);border:1px solid var(--gold-bd);
      border-radius:18px;backdrop-filter:blur(20px);overflow:hidden}
    .panel-hdr{padding:13px 16px;border-bottom:1px solid rgba(201,162,39,.1);
      display:flex;align-items:center;justify-content:space-between}
    .panel-title{font-family:'Oxanium',sans-serif;font-weight:700;font-size:.78rem;
      color:var(--text);letter-spacing:.08em;text-transform:uppercase}
    .p-badge{font-size:.62rem;font-weight:600;padding:2px 8px;border-radius:20px;
      background:rgba(201,162,39,.12);border:1px solid rgba(201,162,39,.2);color:var(--gold)}
    /* History */
    .h-list{max-height:280px;overflow-y:auto;padding:6px 0}
    .h-list::-webkit-scrollbar{width:3px}
    .h-list::-webkit-scrollbar-thumb{background:rgba(201,162,39,.2);border-radius:4px}
    .h-item{padding:7px 16px;display:flex;align-items:center;gap:9px;
      border-bottom:1px solid rgba(255,255,255,.03);animation:slideIn .3s ease}
    @keyframes slideIn{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:translateX(0)}}
    .h-icon{width:24px;height:24px;border-radius:6px;display:flex;
      align-items:center;justify-content:center;font-size:.72rem;flex-shrink:0}
    .ic-next{background:rgba(201,162,39,.15);color:var(--gold-l)}
    .ic-recall{background:rgba(122,138,176,.15);color:var(--text2)}
    .ic-priority{background:rgba(245,166,35,.15);color:var(--amber)}
    .ic-reset{background:rgba(255,79,109,.15);color:var(--red)}
    .h-text{flex:1;min-width:0}
    .h-ticket{font-family:'JetBrains Mono',monospace;font-size:.8rem;font-weight:700;color:var(--text)}
    .h-office{font-size:.66rem;color:var(--text2);margin-top:1px}
    .h-time{font-family:'JetBrains Mono',monospace;font-size:.6rem;color:var(--text2);opacity:.55;flex-shrink:0}
    .h-empty{padding:22px 16px;text-align:center;font-size:.76rem;color:var(--text2);opacity:.45}
    /* Controls */
    .ctrl-body{padding:14px;display:flex;flex-direction:column;gap:9px}
    .ctrl-row{display:flex;align-items:center;justify-content:space-between;
      padding:11px 13px;background:rgba(0,0,0,.22);border-radius:12px;
      border:1px solid rgba(255,255,255,.04);gap:10px}
    .ctrl-info{flex:1;min-width:0}
    .ctrl-title{font-size:.8rem;font-weight:600;color:var(--text)}
    .ctrl-desc{font-size:.67rem;color:var(--text2);margin-top:2px}
    .btn-ctrl{padding:7px 12px;border-radius:8px;font-family:'DM Sans',sans-serif;
      font-size:.76rem;font-weight:600;cursor:pointer;transition:all .25s;white-space:nowrap;
      display:flex;align-items:center;gap:5px}
    .btn-ctrl svg{width:12px;height:12px;stroke:currentColor;stroke-width:2.2;fill:none}
    .btn-disp{background:rgba(201,162,39,.1);border:1px solid rgba(201,162,39,.25);color:var(--gold)}
    .btn-disp:hover{background:rgba(201,162,39,.2)}
    .btn-add{background:rgba(0,230,118,.08);border:1px solid rgba(0,230,118,.2);color:var(--green)}
    .btn-add:hover{background:rgba(0,230,118,.15)}
    .btn-danger{background:rgba(255,79,109,.08);border:1px solid rgba(255,79,109,.22);color:var(--red)}
    .btn-danger:hover{background:rgba(255,79,109,.18);box-shadow:0 4px 14px rgba(255,79,109,.12)}
    /* Add office form */
    .add-form{padding:10px 13px;background:rgba(0,0,0,.2);border-radius:12px;
      border:1px solid rgba(0,230,118,.18);display:none;flex-direction:column;gap:7px;
      animation:fadeUp .3s ease}
    .add-form.show{display:flex}
    .add-form input{padding:8px 11px;background:rgba(255,255,255,.05);
      border:1px solid rgba(201,162,39,.2);border-radius:8px;color:var(--text);
      font-family:'DM Sans',sans-serif;font-size:.84rem;outline:none;
      transition:border-color .25s}
    .add-form input:focus{border-color:var(--gold)}
    .add-btns{display:flex;gap:6px}
    .btn-cf{flex:1;padding:7px;background:rgba(0,230,118,.1);
      border:1px solid rgba(0,230,118,.22);border-radius:8px;
      color:var(--green);font-size:.77rem;font-weight:600;cursor:pointer;transition:all .2s}
    .btn-cf:hover{background:rgba(0,230,118,.2)}
    .btn-cx{padding:7px 12px;background:transparent;border:1px solid rgba(255,255,255,.1);
      border-radius:8px;color:var(--text2);font-size:.77rem;font-weight:600;
      cursor:pointer;transition:all .2s}
    .btn-cx:hover{background:rgba(255,255,255,.07)}
    /* ── Toast ── */
    #toast{position:fixed;bottom:26px;left:50%;
      transform:translateX(-50%) translateY(120px);
      background:rgba(3,8,22,.97);border:1px solid var(--gold-bd);border-radius:14px;
      padding:11px 20px;display:flex;align-items:center;gap:9px;
      font-family:'JetBrains Mono',monospace;font-size:.78rem;color:var(--text);
      backdrop-filter:blur(20px);box-shadow:0 8px 40px rgba(0,0,0,.65);
      z-index:300;transition:transform .45s cubic-bezier(.34,1.56,.64,1),opacity .3s;
      opacity:0;white-space:nowrap;max-width:90vw}
    #toast.show{transform:translateX(-50%) translateY(0);opacity:1}
    #toast.success{border-color:rgba(0,230,118,.25);color:var(--green)}
    #toast.warning{border-color:rgba(245,166,35,.25);color:var(--amber)}
    #toast.error{border-color:rgba(255,79,109,.25);color:var(--red)}
    .t-icon{font-size:.95rem;flex-shrink:0}
    /* ── Modal ── */
    .overlay{position:fixed;inset:0;background:rgba(3,8,22,.8);
      backdrop-filter:blur(7px);z-index:500;display:flex;align-items:center;
      justify-content:center;opacity:0;pointer-events:none;transition:opacity .3s}
    .overlay.show{opacity:1;pointer-events:all}
    .modal{background:var(--glass);border:1px solid var(--gold-bd);border-radius:22px;
      padding:36px 32px;width:360px;max-width:90vw;backdrop-filter:blur(28px);
      box-shadow:0 24px 80px rgba(0,0,0,.75);
      transform:translateY(32px) scale(.95);
      transition:transform .4s cubic-bezier(.16,1,.3,1);text-align:center}
    .overlay.show .modal{transform:translateY(0) scale(1)}
    .m-icon{width:56px;height:56px;border-radius:50%;
      background:rgba(255,79,109,.1);border:1.5px solid rgba(255,79,109,.3);
      display:flex;align-items:center;justify-content:center;margin:0 auto 18px}
    .m-icon svg{width:24px;height:24px;stroke:var(--red);stroke-width:2;fill:none}
    .m-title{font-family:'Oxanium',sans-serif;font-weight:700;font-size:1.05rem;
      color:var(--text);margin-bottom:9px}
    .m-desc{font-size:.83rem;color:var(--text2);line-height:1.55;margin-bottom:26px}
    .m-btns{display:flex;gap:10px}
    .btn-mx{flex:1;padding:12px;background:rgba(255,255,255,.05);
      border:1px solid rgba(255,255,255,.1);border-radius:10px;color:var(--text2);
      font-family:'DM Sans',sans-serif;font-weight:600;font-size:.86rem;
      cursor:pointer;transition:all .2s}
    .btn-mx:hover{background:rgba(255,255,255,.1);color:var(--text)}
    .btn-mc{flex:1;padding:12px;background:rgba(255,79,109,.1);
      border:1px solid rgba(255,79,109,.28);border-radius:10px;color:var(--red);
      font-family:'DM Sans',sans-serif;font-weight:600;font-size:.86rem;
      cursor:pointer;transition:all .2s}
    .btn-mc:hover{background:rgba(255,79,109,.22)}
    /* ── Responsive ── */
    @media(max-width:700px){
      header{padding:10px 14px}
      .h-center{display:none}
      .stats-bar{display:none}
      main{padding:18px 14px}
      .offices-grid{grid-template-columns:1fr}
      .t-num{font-size:2.6rem}
    }
  </style>
</head>
<body>
<div class="bg"><div class="grid"></div></div>
<div class="layout">
  <header>
    <div class="h-left">
      <div class="h-logo">
        <svg viewBox="0 0 26 26" fill="none">
          <path d="M13 2C12 5 10 6 11 9C12 12 13 12.5 13 12.5C13 12.5 14 12 15 9C16 6 14 5 13 2Z" fill="#f0c840" opacity=".95"/>
          <rect x="12" y="13" width="2" height="6" rx=".6" fill="#c9a227"/>
          <rect x="9.5" y="19" width="7" height="2.2" rx="1.1" fill="#a07b15"/>
          <path d="M8 15C6 13.5 5.5 16 7.5 16.5" stroke="#c9a227" stroke-width="1.3" stroke-linecap="round"/>
          <path d="M18 15C20 13.5 20.5 16 18.5 16.5" stroke="#c9a227" stroke-width="1.3" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="h-brand">
        <span class="h-name">PGPC</span>
        <span class="h-sub">Queue System</span>
      </div>
    </div>
    <div class="h-center">
      <div class="h-title">Admin Panel</div>
      <div id="liveTime"></div>
    </div>
    <div class="h-right">
      <div class="status-dot"></div>
      <span class="status-lbl">Online</span>
      <button class="btn-hdr gold-on" id="soundBtn">
        <svg id="sndIcon" viewBox="0 0 24 24"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        <span id="sndLbl">Sound</span>
      </button>
      <button class="btn-hdr" id="dispBtn">
        <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        Display
      </button>
      <button class="btn-hdr danger" id="logoutBtn">
        <svg viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
        Logout
      </button>
    </div>
  </header>

  <div class="stats-bar" id="statsBar"></div>

  <main>
    <div class="sec-label">Active Queues</div>
    <div class="main-grid">
      <div>
        <div class="offices-grid" id="officesGrid">
          {%- for office in offices %}
          <div class="o-card" id="card-{{ office | replace(' ','_') }}">
            <div class="c-top">
              <div>
                <div class="o-name">{{ office }}</div>
                <div class="o-sub">Window 1 &nbsp;·&nbsp; Counter Operations</div>
              </div>
              <div class="badge-on">Active</div>
            </div>
            <div class="t-display">
              <div class="t-lbl">Now Serving</div>
              <span class="t-num" id="tnum-{{ office | replace(' ','_') }}">{{ state.get(office,'----') }}</span>
              <div class="t-type" id="ttype-{{ office | replace(' ','_') }}">Regular</div>
            </div>
            <div class="c-actions">
              <button class="btn-act btn-next" data-office="{{ office }}">
                <svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>Next
              </button>
              <button class="btn-act btn-recall" data-office="{{ office }}">
                <svg viewBox="0 0 24 24"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.54"/></svg>Recall
              </button>
              <button class="btn-act btn-priority btn-full" data-office="{{ office }}">
                <svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                Priority Ticket
              </button>
            </div>
          </div>
          {%- endfor %}
        </div>
      </div>

      <!-- Sidebar -->
      <div class="sidebar">
        <div class="panel">
          <div class="panel-hdr">
            <span class="panel-title">Activity Log</span>
            <span class="p-badge" id="hCount">0</span>
          </div>
          <div class="h-list" id="hList"><div class="h-empty">No activity yet</div></div>
        </div>

        <div class="panel">
          <div class="panel-hdr"><span class="panel-title">System Controls</span></div>
          <div class="ctrl-body">
            <div class="ctrl-row">
              <div class="ctrl-info">
                <div class="ctrl-title">Queue Display Screen</div>
                <div class="ctrl-desc">Open public TV display</div>
              </div>
              <button class="btn-ctrl btn-disp" id="openDispBtn">
                <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="12" y1="17" x2="12" y2="21"/></svg>Open
              </button>
            </div>
            <div class="ctrl-row">
              <div class="ctrl-info">
                <div class="ctrl-title">Add Office / Counter</div>
                <div class="ctrl-desc">Create a new queue window</div>
              </div>
              <button class="btn-ctrl btn-add" id="addOffBtn">
                <svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>Add
              </button>
            </div>
            <div class="add-form" id="addForm">
              <input id="newOff" type="text" placeholder="e.g. Guidance Office" maxlength="30"/>
              <div class="add-btns">
                <button class="btn-cf" id="cfAdd">Create</button>
                <button class="btn-cx" id="cxAdd">Cancel</button>
              </div>
            </div>
            <div class="ctrl-row">
              <div class="ctrl-info">
                <div class="ctrl-title">Reset All Queues</div>
                <div class="ctrl-desc">Clear all ticket counters</div>
              </div>
              <button class="btn-ctrl btn-danger" id="resetBtn">
                <svg viewBox="0 0 24 24"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.54"/></svg>Reset
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</div>

<div id="toast" role="status" aria-live="polite">
  <span class="t-icon" id="tIcon">✓</span>
  <span id="tText"></span>
</div>

<div class="overlay" id="modal">
  <div class="modal">
    <div class="m-icon">
      <svg viewBox="0 0 24 24"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.54"/></svg>
    </div>
    <div class="m-title" id="mTitle">Confirm</div>
    <div class="m-desc" id="mDesc">Are you sure?</div>
    <div class="m-btns">
      <button class="btn-mx" id="mCancel">Cancel</button>
      <button class="btn-mc" id="mConfirm">Confirm</button>
    </div>
  </div>
</div>

<script>
  let soundOn=true,mCb=null;
  const sfx=new Audio('ding-dong-81717.mp3');sfx.preload='auto';sfx.volume=.9;
  function play(){if(!soundOn)return;sfx.pause();sfx.currentTime=0;sfx.play().catch(()=>{})}

  /* sound toggle */
  document.getElementById('soundBtn').addEventListener('click',function(){
    soundOn=!soundOn;
    this.classList.toggle('gold-on',soundOn);
    document.getElementById('sndLbl').textContent=soundOn?'Sound':'Muted';
    document.getElementById('sndIcon').innerHTML=soundOn
      ?'<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>'
      :'<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>';
    showToast(soundOn?'Sound enabled':'Sound muted',soundOn?'success':'warning');
  });

  /* toast */
  let tTimer=null;
  const icons={success:'✓',warning:'⚠',error:'✕','':'ℹ'};
  function showToast(msg,type=''){
    const el=document.getElementById('toast');
    document.getElementById('tIcon').textContent=icons[type]||'ℹ';
    document.getElementById('tText').textContent=msg;
    el.className='show'+(type?' '+type:'');
    clearTimeout(tTimer);tTimer=setTimeout(()=>{el.className=''},3800);
  }

  /* modal */
  function showModal(title,desc,cb){
    document.getElementById('mTitle').textContent=title;
    document.getElementById('mDesc').textContent=desc;
    mCb=cb;document.getElementById('modal').classList.add('show');
  }
  document.getElementById('mCancel').addEventListener('click',()=>{
    document.getElementById('modal').classList.remove('show');mCb=null;
  });
  document.getElementById('mConfirm').addEventListener('click',()=>{
    document.getElementById('modal').classList.remove('show');
    if(mCb){mCb();mCb=null;}
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape')document.getElementById('modal').classList.remove('show');});

  /* ripple */
  function ripple(btn,e){
    const r=btn.getBoundingClientRect(),sp=document.createElement('span');
    sp.className='ripple';const s=Math.max(r.width,r.height);
    sp.style.cssText=`width:${s}px;height:${s}px;left:${e.clientX-r.left-s/2}px;top:${e.clientY-r.top-s/2}px`;
    btn.appendChild(sp);setTimeout(()=>sp.remove(),600);
  }

  /* sid = safe id (replace spaces) */
  function sid(name){return name.replace(/ /g,'_')}

  /* UI update */
  function updateUI(state,served){
    Object.keys(state).forEach(office=>{
      const el=document.getElementById('tnum-'+sid(office));
      const te=document.getElementById('ttype-'+sid(office));
      if(!el)return;
      if(el.textContent!==state[office]){
        el.textContent=state[office]||'----';
        el.classList.remove('flip');void el.offsetWidth;el.classList.add('flip');
        const card=document.getElementById('card-'+sid(office));
        if(card){card.classList.remove('pulse-card');void card.offsetWidth;card.classList.add('pulse-card')}
        if(te){const isPri=state[office]&&state[office].startsWith('P');
          te.textContent=isPri?'Priority':'Regular';
          te.className='t-type'+(isPri?' priority':'');
        }
      }
    });
    if(served)updateStats(served);
  }

  /* stats */
  function buildStats(offices,served){
    const bar=document.getElementById('statsBar');bar.innerHTML='';
    let total=0;
    offices.forEach(n=>{
      const v=served[n]||0;total+=v;
      const d=document.createElement('div');d.className='stat-cell';
      d.innerHTML=`<div class="stat-v" id="sv-${sid(n)}">${v}</div><div class="stat-lbl">${n} Served</div>`;
      bar.appendChild(d);
    });
    const td=document.createElement('div');td.className='stat-cell';
    td.innerHTML=`<div class="stat-v" id="sv-TOTAL">${total}</div><div class="stat-lbl">Total Today</div>`;
    bar.appendChild(td);
  }
  function updateStats(served){
    let total=0;
    Object.keys(served).forEach(n=>{
      const v=served[n]||0;total+=v;
      const el=document.getElementById('sv-'+sid(n));
      if(el&&el.textContent!=v){el.textContent=v;el.classList.remove('pop');void el.offsetWidth;el.classList.add('pop')}
    });
    const tel=document.getElementById('sv-TOTAL');
    if(tel&&tel.textContent!=total){tel.textContent=total;tel.classList.remove('pop');void tel.offsetWidth;tel.classList.add('pop')}
  }

  /* history */
  function renderHistory(hist){
    const list=document.getElementById('hList');
    document.getElementById('hCount').textContent=hist.length;
    if(!hist.length){list.innerHTML='<div class="h-empty">No activity yet</div>';return}
    const ic={next:{c:'ic-next',s:'→'},recall:{c:'ic-recall',s:'↺'},priority:{c:'ic-priority',s:'★'},reset:{c:'ic-reset',s:'⊘'}};
    list.innerHTML=hist.slice(0,25).map(h=>{
      const i=ic[h.type]||{c:'ic-next',s:'·'};
      return`<div class="h-item"><div class="h-icon ${i.c}">${i.s}</div>
        <div class="h-text"><div class="h-ticket">${h.ticket}</div>
        <div class="h-office">${h.office} · ${h.type}</div></div>
        <div class="h-time">${h.time}</div></div>`;
    }).join('');
  }

  /* API */
  async function api(action,office=null,extra={}){
    const body=office?{office,...extra}:extra;
    try{
      const res=await fetch('/api/'+action,{method:'POST',
        headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const d=await res.json();
      if(d.success){
        updateUI(d.state,d.served);
        showToast(d.message,action==='reset'?'warning':'success');
        if(action==='next'||action==='priority')play();
        loadHistory();
      }else showToast(d.message||'Error.','error');
    }catch{showToast('Connection error.','error')}
  }
  async function loadHistory(){
    try{const r=await fetch('/api/history');const d=await r.json();if(d.success)renderHistory(d.history)}catch{}
  }
  async function loadState(){
    try{const r=await fetch('/api/state');const d=await r.json();if(d.success)updateUI(d.state,d.served)}catch{}
  }

  /* event wiring */
  document.querySelectorAll('.btn-next').forEach(b=>b.addEventListener('click',e=>{ripple(b,e);api('next',b.dataset.office)}));
  document.querySelectorAll('.btn-recall').forEach(b=>b.addEventListener('click',e=>{ripple(b,e);api('recall',b.dataset.office)}));
  document.querySelectorAll('.btn-priority').forEach(b=>b.addEventListener('click',e=>{ripple(b,e);api('priority',b.dataset.office)}));
  document.getElementById('resetBtn').addEventListener('click',()=>{
    showModal('Reset All Queues','Clear all ticket numbers and restart from zero? This cannot be undone.',()=>api('reset'));
  });
  document.getElementById('logoutBtn').addEventListener('click',()=>{location.href='/'});
  document.getElementById('dispBtn').addEventListener('click',()=>window.open('/display','_blank'));
  document.getElementById('openDispBtn').addEventListener('click',()=>window.open('/display','_blank'));

  /* add office */
  const addForm=document.getElementById('addForm'),newOff=document.getElementById('newOff');
  document.getElementById('addOffBtn').addEventListener('click',()=>{
    addForm.classList.toggle('show');if(addForm.classList.contains('show'))newOff.focus();
  });
  document.getElementById('cxAdd').addEventListener('click',()=>{addForm.classList.remove('show');newOff.value=''});
  document.getElementById('cfAdd').addEventListener('click',async()=>{
    const name=newOff.value.trim();
    if(!name){showToast('Enter an office name.','error');return}
    try{
      const r=await fetch('/api/add-office',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});
      const d=await r.json();
      if(d.success){showToast(d.message,'success');addForm.classList.remove('show');newOff.value='';setTimeout(()=>location.reload(),800)}
      else showToast(d.message||'Error.','error');
    }catch{showToast('Connection error.','error')}
  });
  newOff.addEventListener('keydown',e=>{
    if(e.key==='Enter')document.getElementById('cfAdd').click();
    if(e.key==='Escape')document.getElementById('cxAdd').click();
  });

  /* clock */
  function tick(){document.getElementById('liveTime').textContent=
    new Date().toLocaleString('en-US',{weekday:'short',month:'short',day:'numeric',
      hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false})}
  tick();setInterval(tick,1000);

  /* init */
  const initOffices=[{% for office in offices %}'{{ office }}'{% if not loop.last %},{% endif %}{% endfor %}];
  const initServed={{ served | tojson }};
  buildStats(initOffices,initServed);
  loadHistory();loadState();
</script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
#  DISPLAY SCREEN  (TV / public lobby)
# ══════════════════════════════════════════════════════════════════════════════
DISPLAY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>PGPC Queue Display</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Oxanium:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    :root{
      --navy:#030816; --royal:#0d1f5c;
      --gold:#c9a227; --gold-l:#f0c840;
      --text:#f0f4ff; --text2:#7a8ab0;
    }
    html,body{height:100%;background:var(--navy);color:var(--text);
      font-family:'Oxanium',sans-serif;overflow:hidden}
    .bg{position:fixed;inset:0;z-index:0;
      background:radial-gradient(ellipse at 12% 12%,rgba(13,31,92,.6) 0%,transparent 55%),
                 radial-gradient(ellipse at 88% 88%,rgba(201,162,39,.09) 0%,transparent 55%),
                 var(--navy)}
    .grid{position:fixed;inset:0;
      background-image:linear-gradient(rgba(201,162,39,.028) 1px,transparent 1px),
                       linear-gradient(90deg,rgba(201,162,39,.028) 1px,transparent 1px);
      background-size:80px 80px}
    .page{position:relative;z-index:1;height:100vh;display:flex;flex-direction:column}
    /* ── Header ── */
    .d-hdr{display:flex;align-items:center;justify-content:space-between;
      padding:18px 40px;border-bottom:1px solid rgba(201,162,39,.22);
      background:rgba(3,8,22,.85);backdrop-filter:blur(12px)}
    .d-logo{display:flex;align-items:center;gap:16px}
    .d-emblem{width:60px;height:60px;border-radius:50%;
      background:radial-gradient(circle,rgba(13,31,92,.7),rgba(201,162,39,.12));
      border:2px solid rgba(201,162,39,.38);display:flex;align-items:center;justify-content:center;
      box-shadow:0 0 0 4px rgba(201,162,39,.07),0 0 24px rgba(201,162,39,.1);
      animation:emblemGlow 4s ease-in-out infinite}
    @keyframes emblemGlow{0%,100%{box-shadow:0 0 0 4px rgba(201,162,39,.07),0 0 24px rgba(201,162,39,.1)}
      50%{box-shadow:0 0 0 6px rgba(201,162,39,.12),0 0 40px rgba(201,162,39,.2)}}
    .d-emblem svg{width:32px;height:32px}
    .d-school{display:flex;flex-direction:column}
    .d-sname{font-family:'Cinzel',serif;font-weight:700;font-size:1.25rem;
      color:var(--gold-l);letter-spacing:.08em;line-height:1;
      text-shadow:0 0 20px rgba(201,162,39,.3)}
    .d-ssub{font-size:.68rem;color:var(--text2);letter-spacing:.2em;text-transform:uppercase;margin-top:4px}
    .d-hdr-mid{text-align:center}
    .d-now-lbl{font-size:.72rem;letter-spacing:.22em;text-transform:uppercase;
      color:var(--gold);font-weight:600;margin-bottom:4px}
    .d-now-title{font-size:1.4rem;font-weight:800;color:var(--text);letter-spacing:.06em}
    .d-clock{text-align:right}
    #dDate{font-family:'JetBrains Mono',monospace;font-size:.82rem;color:var(--gold);letter-spacing:.04em}
    #dTime{font-family:'JetBrains Mono',monospace;font-size:1.9rem;font-weight:700;
      color:var(--text);letter-spacing:.06em;margin-top:2px}
    /* ── Queue grid ── */
    .q-grid{flex:1;display:grid;
      grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
      gap:1px;background:rgba(201,162,39,.07);overflow:hidden}
    .q-cell{display:flex;flex-direction:column;align-items:center;justify-content:center;
      padding:36px 28px;background:rgba(3,8,22,.93);text-align:center;
      position:relative;overflow:hidden}
    .q-cell::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
      background:linear-gradient(90deg,transparent,var(--gold),transparent);opacity:.45}
    .q-cell::after{content:'';position:absolute;top:-80px;left:50%;
      transform:translateX(-50%);width:320px;height:320px;
      background:radial-gradient(circle,rgba(201,162,39,.055) 0%,transparent 65%);pointer-events:none}
    .q-oname{font-size:1rem;font-weight:700;color:var(--text2);
      letter-spacing:.14em;text-transform:uppercase;margin-bottom:12px}
    .q-serving{font-size:.68rem;letter-spacing:.22em;text-transform:uppercase;
      color:var(--gold);margin-bottom:14px;font-weight:600}
    .q-num{font-family:'JetBrains Mono',monospace;
      font-size:clamp(4.5rem,9vw,7.5rem);font-weight:700;color:var(--gold-l);
      line-height:1;letter-spacing:.08em;
      text-shadow:0 0 60px rgba(201,162,39,.5),0 0 120px rgba(201,162,39,.2);
      transition:all .35s}
    .q-num.change{animation:bigFlip .65s cubic-bezier(.34,1.56,.64,1)}
    @keyframes bigFlip{
      0%{transform:scale(.65) translateY(-24px);opacity:0;filter:blur(4px)}
      60%{transform:scale(1.06);opacity:1;filter:blur(0)}100%{transform:scale(1)}}
    .q-hint{font-size:.72rem;color:var(--text2);margin-top:14px;letter-spacing:.08em}
    /* ── Footer ticker ── */
    .d-footer{padding:9px 36px;border-top:1px solid rgba(201,162,39,.14);
      background:rgba(3,8,22,.92);display:flex;align-items:center;
      justify-content:space-between;font-size:.64rem;color:var(--text2);letter-spacing:.1em}
    .ticker-wrap{overflow:hidden;white-space:nowrap;flex:1;margin:0 28px}
    .ticker-text{display:inline-block;animation:ticker 30s linear infinite;
      color:var(--gold);font-size:.68rem;letter-spacing:.1em}
    @keyframes ticker{from{transform:translateX(100vw)}to{transform:translateX(-100%)}}
  </style>
</head>
<body>
<div class="bg"><div class="grid"></div></div>
<div class="page">
  <div class="d-hdr">
    <div class="d-logo">
      <div class="d-emblem">
        <svg viewBox="0 0 32 32" fill="none">
          <path d="M16 2C15 5 13 6 14 9C15 12 16 12.5 16 12.5C16 12.5 17 12 18 9C19 6 17 5 16 2Z" fill="#f0c840" opacity=".95"/>
          <rect x="15" y="13" width="2" height="7" rx=".7" fill="#c9a227"/>
          <rect x="12" y="20" width="8" height="2.5" rx="1.2" fill="#a07b15"/>
          <path d="M9 16.5C7 15 6.5 17.5 8.5 18" stroke="#c9a227" stroke-width="1.3" stroke-linecap="round"/>
          <path d="M23 16.5C25 15 25.5 17.5 23.5 18" stroke="#c9a227" stroke-width="1.3" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="d-school">
        <span class="d-sname">Padre Garcia Polytechnic College</span>
        <span class="d-ssub">Queue Management System · Batangas, Philippines</span>
      </div>
    </div>
    <div class="d-hdr-mid">
      <div class="d-now-lbl">Queue Display</div>
      <div class="d-now-title">Now Serving</div>
    </div>
    <div class="d-clock">
      <div id="dDate"></div>
      <div id="dTime"></div>
    </div>
  </div>

  <div class="q-grid" id="qGrid">
    {%- for office in offices %}
    <div class="q-cell">
      <div class="q-oname">{{ office }}</div>
      <div class="q-serving">Now Serving</div>
      <div class="q-num" id="dn-{{ office | replace(' ','_') }}">{{ state.get(office,'----') }}</div>
      <div class="q-hint">Please proceed to {{ office }} window</div>
    </div>
    {%- endfor %}
  </div>

  <div class="d-footer">
    <span>PGPC &copy; 2024</span>
    <div class="ticker-wrap">
      <span class="ticker-text">
        Welcome to Padre Garcia Polytechnic College &nbsp;&nbsp;•&nbsp;&nbsp;
        Please wait for your number to be called &nbsp;&nbsp;•&nbsp;&nbsp;
        Proceed immediately to the designated window when your number appears &nbsp;&nbsp;•&nbsp;&nbsp;
        Thank you for your patience and cooperation &nbsp;&nbsp;•&nbsp;&nbsp;
        For inquiries, please approach the Information Desk &nbsp;&nbsp;•&nbsp;&nbsp;
      </span>
    </div>
    <span id="dFootTime"></span>
  </div>
</div>
<script>
  function clock(){
    const n=new Date();
    document.getElementById('dDate').textContent=n.toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'});
    document.getElementById('dTime').textContent=n.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
    document.getElementById('dFootTime').textContent=n.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',hour12:true});
  }
  clock();setInterval(clock,1000);
  async function poll(){
    try{
      const r=await fetch('/api/state');const d=await r.json();
      if(!d.success)return;
      Object.keys(d.state).forEach(name=>{
        const el=document.getElementById('dn-'+name.replace(/ /g,'_'));
        if(!el)return;
        if(el.textContent!==d.state[name]){
          el.textContent=d.state[name]||'----';
          el.classList.remove('change');void el.offsetWidth;el.classList.add('change');
        }
      });
    }catch{}
  }
  setInterval(poll,3000);
</script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    return render_template_string(LOGIN_HTML)

@app.route('/admin')
def admin():
    names = list(offices_data.keys())
    return render_template_string(ADMIN_HTML,
                                  offices=names,
                                  state=snapshot(),
                                  served=served_map())

@app.route('/display')
def display():
    names = list(offices_data.keys())
    return render_template_string(DISPLAY_HTML,
                                  offices=names,
                                  state=snapshot())

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u, p = data.get('username', ''), data.get('password', '')
    if u in USERS and USERS[u] == p:
        return jsonify(success=True, message='Login successful!')
    return jsonify(success=False, message='Invalid credentials.'), 401

@app.route('/api/state')
def api_state():
    return jsonify(success=True, state=snapshot(), served=served_map())

@app.route('/api/history')
def api_history():
    return jsonify(success=True, history=HISTORY[:25])

@app.route('/api/next', methods=['POST'])
def api_next():
    data = request.get_json() or {}
    office = data.get('office')
    if office not in offices_data:
        return jsonify(success=False, message='Invalid office.'), 400
    od = offices_data[office]
    cur = od['current']
    try:
        num = int(cur[1:]) if cur not in ('----',) and len(cur) > 1 and cur[1:].isdigit() else 0
    except:
        num = 0
    num += 1
    od['current'] = od['prefix'] + str(num).zfill(3)
    od['served'] += 1
    push_history('next', office, od['current'])
    return jsonify(success=True,
                   message=f"Now serving {od['current']} at {office}.",
                   state=snapshot(), served=served_map())

@app.route('/api/recall', methods=['POST'])
def api_recall():
    data = request.get_json() or {}
    office = data.get('office')
    if office not in offices_data:
        return jsonify(success=False, message='Invalid office.'), 400
    od = offices_data[office]
    push_history('recall', office, od['current'])
    msg = (f"Recalling {od['current']} at {office}."
           if od['current'] != '----'
           else f"No current ticket to recall at {office}.")
    return jsonify(success=True, message=msg, state=snapshot(), served=served_map())

@app.route('/api/priority', methods=['POST'])
def api_priority():
    data = request.get_json() or {}
    office = data.get('office')
    if office not in offices_data:
        return jsonify(success=False, message='Invalid office.'), 400
    od = offices_data[office]
    od['priority'] += 1
    ticket = 'P' + str(od['priority']).zfill(2)
    od['current'] = ticket
    od['served'] += 1
    push_history('priority', office, ticket)
    return jsonify(success=True,
                   message=f"Priority {ticket} now serving at {office}.",
                   state=snapshot(), served=served_map())

@app.route('/api/reset', methods=['POST'])
def api_reset():
    for od in offices_data.values():
        od['current'] = '----'
        od['priority'] = 0
    push_history('reset', 'ALL', '----')
    return jsonify(success=True,
                   message='All queues have been reset.',
                   state=snapshot(), served=served_map())

@app.route('/api/add-office', methods=['POST'])
def api_add_office():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name or name in offices_data:
        return jsonify(success=False, message='Invalid or duplicate office name.')
    prefix = name[0].upper()
    used = {v['prefix'] for v in offices_data.values()}
    if prefix in used:
        for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if ch not in used:
                prefix = ch
                break
    offices_data[name] = {'current': prefix + '001', 'served': 0,
                          'prefix': prefix, 'priority': 0}
    return jsonify(success=True,
                   message=f"Office '{name}' added successfully.",
                   state=snapshot(), served=served_map(),
                   offices=list(offices_data.keys()))

@app.route('/api/remove-office', methods=['POST'])
def api_remove_office():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if name not in offices_data:
        return jsonify(success=False, message='Office not found.')
    del offices_data[name]
    return jsonify(success=True,
                   message=f"Office '{name}' removed.",
                   state=snapshot(), served=served_map(),
                   offices=list(offices_data.keys()))

# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, port=5000)