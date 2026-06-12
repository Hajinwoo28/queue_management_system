from flask import Flask, request, jsonify, render_template_string, session, redirect
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', 'pgpc_qms_secret_8472')

# ── Auth ──────────────────────────────────────────────────────────────────────
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password123")
USERS = {ADMIN_USERNAME: ADMIN_PASSWORD}

OPERATOR_CREDS = {
    'Cashier':   {'username': 'cashier',   'password': 'cashier123'},
    'Registrar': {'username': 'registrar', 'password': 'registrar123'},
}

# ── Application State ─────────────────────────────────────────────────────────
offices_data = {
    'Cashier':   {'current': 'C001', 'served': 0, 'prefix': 'C', 'priority': 0, 'recall_count': 0},
    'Registrar': {'current': 'R001', 'served': 0, 'prefix': 'R', 'priority': 0, 'recall_count': 0},
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

def recall_map():
    return {k: v.get('recall_count', 0) for k, v in offices_data.items()}

def next_ticket(office_name):
    od = offices_data.get(office_name)
    if not od:
        return '----'
    cur = od['current']
    prefix = od['prefix']
    if cur == '----':
        return prefix + '001'
    if cur.startswith('P'):
        try:
            return 'P' + str(int(cur[1:]) + 1).zfill(2)
        except:
            return prefix + '001'
    try:
        return prefix + str(int(cur[len(prefix):]) + 1).zfill(3)
    except:
        return prefix + '001'

OFFICE_SLUGS = {
    'cashier':   'Cashier',
    'registrar': 'Registrar',
}

# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>PGPC Queue System — Login</title>
  <link rel="icon" type="image/png" href="data:image/png;base64,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"/>
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
      <img src="data:image/png;base64,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" alt="PGPC Logo" style="width:68px;height:68px;border-radius:50%;object-fit:cover;"/>
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
      setTimeout(()=>{location.href=d.redirect||'/admin'},1000)}
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
  <link rel="icon" type="image/png" href="data:image/png;base64,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"/>
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
    .btn-monitor{background:rgba(122,138,176,.07);border:1px solid rgba(122,138,176,.22);color:var(--text2)}
    .btn-monitor:hover{background:rgba(201,162,39,.08);border-color:rgba(201,162,39,.28);color:var(--gold)}
    .btn-office{background:rgba(245,166,35,.08);border:1px solid rgba(245,166,35,.22);color:var(--amber)}
    .btn-office:hover{background:rgba(245,166,35,.18);border-color:rgba(245,166,35,.38);color:var(--amber)}
    .monitor-btns{display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end}
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
        <img src="data:image/png;base64,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" alt="PGPC Logo" style="width:38px;height:38px;border-radius:50%;object-fit:cover;"/>
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
        <span id="sndLbl">Voice</span>
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
            <div class="ctrl-row" style="align-items:flex-start">
              <div class="ctrl-info">
                <div class="ctrl-title">Monitor Displays</div>
                <div class="ctrl-desc">Per-office queue screens</div>
              </div>
              <div class="monitor-btns">
                {%- for office in offices %}
                <button class="btn-ctrl btn-monitor" onclick="window.open('/monitor/{{ office | lower | replace(' ', '-') }}','_blank')">
                  <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8m-4-4v4" stroke-linecap="round"/></svg>
                  {{ office }}
                </button>
                {%- endfor %}
              </div>
            </div>
            <div class="ctrl-row" style="align-items:flex-start">
              <div class="ctrl-info">
                <div class="ctrl-title">Operator Pages</div>
                <div class="ctrl-desc">Per-window staff controls</div>
              </div>
              <div class="monitor-btns">
                {%- for office in offices %}
                <button class="btn-ctrl btn-office" onclick="window.open('/{{ office | lower | replace(' ', '-') }}','_blank')">
                  <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6m-6 4h6m-6 4h4" stroke-linecap="round"/></svg>
                  {{ office }}
                </button>
                {%- endfor %}
              </div>
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

  // ── Web Audio ding-dong chime (no MP3 file required) ─────────────────────────
  function playDing(){
    if(!soundOn)return;
    try{
      const ctx=new(window.AudioContext||window.webkitAudioContext)();
      function tone(freq,start,dur,vol){
        const osc=ctx.createOscillator(),g=ctx.createGain();
        osc.connect(g);g.connect(ctx.destination);
        osc.type='sine';osc.frequency.value=freq;
        g.gain.setValueAtTime(0,ctx.currentTime+start);
        g.gain.linearRampToValueAtTime(vol,ctx.currentTime+start+0.025);
        g.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+start+dur);
        osc.start(ctx.currentTime+start);
        osc.stop(ctx.currentTime+start+dur+0.05);
      }
      tone(880,0,1.4,0.55);    // ding — A5
      tone(659,0.42,1.6,0.50); // dong — E5
      setTimeout(()=>ctx.close(),2800);
    }catch(e){}
  }

  // ── Web Speech API voice announcement ────────────────────────────────────────
  function speak(text){
    if(!soundOn||!window.speechSynthesis)return;
    window.speechSynthesis.cancel();
    const utt=new SpeechSynthesisUtterance(text);
    utt.lang='en-US';utt.rate=0.88;utt.pitch=1.0;utt.volume=1.0;
    function doSpeak(){
      const voices=window.speechSynthesis.getVoices();
      const pick=voices.find(v=>/en.*(US|PH)/i.test(v.lang)&&/female|zira|samantha|karen|aria/i.test(v.name))
                ||voices.find(v=>/en/i.test(v.lang));
      if(pick)utt.voice=pick;
      window.speechSynthesis.speak(utt);
    }
    if(window.speechSynthesis.getVoices().length){doSpeak();}
    else{window.speechSynthesis.addEventListener('voiceschanged',doSpeak,{once:true});}
  }

  // Spell out ticket e.g. "C002" → "C 0 0 2" for clear TTS pronunciation
  function ticketForSpeech(t){
    return t?t.split('').join(' '):'';
  }
  function buildAnnouncement(action,office,ticket){
    const t=ticketForSpeech(ticket);
    if(action==='priority')return`Priority number ${t}. Please proceed to ${office}.`;
    if(action==='recall')return`Recalling for number ${t}. Please proceed to the ${office.toLowerCase()} office.`;
    return`Number ${t}. Please proceed to the ${office} window.`;
  }

  /* sound + voice toggle */
  document.getElementById('soundBtn').addEventListener('click',function(){
    soundOn=!soundOn;
    if(!soundOn&&window.speechSynthesis)window.speechSynthesis.cancel();
    this.classList.toggle('gold-on',soundOn);
    document.getElementById('sndLbl').textContent=soundOn?'Voice':'Muted';
    document.getElementById('sndIcon').innerHTML=soundOn
      ?'<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>'
      :'<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>';
    showToast(soundOn?'Voice announcements on':'Voice muted',soundOn?'success':'warning');
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

  function announceRecall(office){
    const el=document.getElementById('tnum-'+sid(office));
    const ticket=el?el.textContent.trim():'';
    if(!ticket||ticket==='----'||!soundOn)return;
    playDing();
    setTimeout(()=>speak(buildAnnouncement('recall',office,ticket)),680);
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
        if(action==='next'||action==='priority'){
          playDing();
          const ticket=office?d.state[office]:'';
          if(ticket&&ticket!=='----'){
            setTimeout(()=>speak(buildAnnouncement(action,office,ticket)),680);
          }
        }
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
  document.querySelectorAll('.btn-recall').forEach(b=>b.addEventListener('click',e=>{
    ripple(b,e);announceRecall(b.dataset.office);api('recall',b.dataset.office);
  }));
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
  <link rel="icon" type="image/png" href="data:image/png;base64,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"/>
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
        <img src="data:image/png;base64,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" alt="PGPC Logo" style="width:54px;height:54px;border-radius:50%;object-fit:cover;"/>
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

  function ticketForSpeech(t){return t?t.split('').join(' '):''}
  function buildAnnouncement(action,office,ticket){
    const t=ticketForSpeech(ticket);
    if(action==='priority')return`Priority number ${t}. Please proceed to ${office}.`;
    if(action==='recall')return`Recalling for number ${t}. Please proceed to the ${office.toLowerCase()} office.`;
    return`Number ${t}. Please proceed to the ${office} window.`;
  }
  function speak(text){
    if(!window.speechSynthesis)return;
    window.speechSynthesis.cancel();
    const utt=new SpeechSynthesisUtterance(text);
    utt.lang='en-US';utt.rate=0.88;utt.pitch=1.0;utt.volume=1.0;
    function doSpeak(){
      const voices=window.speechSynthesis.getVoices();
      const pick=voices.find(v=>/en.*(US|PH)/i.test(v.lang)&&/female|zira|samantha|karen|aria/i.test(v.name))
                ||voices.find(v=>/en/i.test(v.lang));
      if(pick)utt.voice=pick;
      window.speechSynthesis.speak(utt);
    }
    if(window.speechSynthesis.getVoices().length){doSpeak();}
    else{window.speechSynthesis.addEventListener('voiceschanged',doSpeak,{once:true});}
  }
  function playDing(){
    try{
      const ctx=new(window.AudioContext||window.webkitAudioContext)();
      function tone(freq,start,dur,vol){
        const osc=ctx.createOscillator(),g=ctx.createGain();
        osc.connect(g);g.connect(ctx.destination);
        osc.type='sine';osc.frequency.value=freq;
        g.gain.setValueAtTime(0,ctx.currentTime+start);
        g.gain.linearRampToValueAtTime(vol,ctx.currentTime+start+0.025);
        g.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+start+dur);
        osc.start(ctx.currentTime+start);
        osc.stop(ctx.currentTime+start+dur+0.05);
      }
      tone(880,0,1.4,0.55);tone(659,0.42,1.6,0.50);
      setTimeout(()=>ctx.close(),2800);
    }catch(e){}
  }

  let lastState={},lastRecall={};
  async function poll(){
    try{
      const r=await fetch('/api/state');const d=await r.json();
      if(!d.success)return;
      const recall=d.recall||{};
      Object.keys(d.state).forEach(name=>{
        const el=document.getElementById('dn-'+name.replace(/ /g,'_'));
        if(!el)return;
        const cur=d.state[name]||'----';
        const prev=lastState[name];
        if(el.textContent!==cur){
          el.textContent=cur;
          el.classList.remove('change');void el.offsetWidth;el.classList.add('change');
          if(cur&&cur!=='----'&&prev!==undefined){
            playDing();
            const action=cur.startsWith('P')?'priority':'next';
            setTimeout(()=>speak(buildAnnouncement(action,name,cur)),680);
          }
        }
        const rc=recall[name]||0;
        if(lastRecall[name]!==undefined&&rc>lastRecall[name]&&cur&&cur!=='----'){
          playDing();
          setTimeout(()=>speak(buildAnnouncement('recall',name,cur)),680);
        }
        lastRecall[name]=rc;
        lastState[name]=cur;
      });
    }catch{}
  }
  setInterval(poll,3000);
</script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
#  MONITOR SCREEN  (per-office, shows Now Serving + Next Queue)
# ══════════════════════════════════════════════════════════════════════════════
MONITOR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{{ office }} Monitor — PGPC Queue</title>
  <link rel="icon" type="image/png" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABCGlDQ1BJQ0MgUHJvZmlsZQAAeJxjYGA8wQAELAYMDLl5JUVB7k4KEZFRCuwPGBiBEAwSk4sLGHADoKpv1yBqL+viUYcLcKakFicD6Q9ArFIEtBxopAiQLZIOYWuA2EkQtg2IXV5SUAJkB4DYRSFBzkB2..."/>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Oxanium:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    :root{
      --navy:#030816;--royal:#0d1f5c;
      --gold:#c9a227;--gold-l:#f0c840;
      --text:#f0f4ff;--text2:#7a8ab0;--green:#00e676;
    }
    html,body{height:100%;background:var(--navy);color:var(--text);
      font-family:'Oxanium',sans-serif;overflow:hidden}
    .bg{position:fixed;inset:0;z-index:0;
      background:radial-gradient(ellipse at 15% 20%,rgba(13,31,92,.55) 0%,transparent 55%),
                 radial-gradient(ellipse at 85% 80%,rgba(201,162,39,.08) 0%,transparent 55%),
                 var(--navy)}
    .grid{position:fixed;inset:0;
      background-image:linear-gradient(rgba(201,162,39,.025) 1px,transparent 1px),
                       linear-gradient(90deg,rgba(201,162,39,.025) 1px,transparent 1px);
      background-size:80px 80px}
    .page{position:relative;z-index:1;height:100vh;display:flex;flex-direction:column}
    .m-hdr{display:flex;align-items:center;justify-content:space-between;
      padding:16px 36px;border-bottom:1px solid rgba(201,162,39,.18);
      background:rgba(3,8,22,.88);backdrop-filter:blur(12px)}
    .m-logo-area{display:flex;align-items:center;gap:14px}
    .m-emblem{width:52px;height:52px;border-radius:50%;
      border:1.5px solid rgba(201,162,39,.35);overflow:hidden;flex-shrink:0;
      box-shadow:0 0 18px rgba(201,162,39,.12)}
    .m-emblem img{width:100%;height:100%;object-fit:cover}
    .m-school{display:flex;flex-direction:column}
    .m-sname{font-family:'Cinzel',serif;font-weight:700;font-size:1.05rem;
      color:var(--gold-l);letter-spacing:.06em;line-height:1.2;
      text-shadow:0 0 16px rgba(201,162,39,.25)}
    .m-ssub{font-size:.6rem;color:var(--text2);letter-spacing:.18em;
      text-transform:uppercase;margin-top:3px}
    .m-office-badge{padding:9px 24px;border-radius:10px;
      background:rgba(201,162,39,.1);border:1px solid rgba(201,162,39,.3);
      font-family:'Oxanium',sans-serif;font-weight:800;font-size:1.05rem;
      color:var(--gold-l);letter-spacing:.1em;text-transform:uppercase;
      text-shadow:0 0 16px rgba(201,162,39,.3);
      box-shadow:0 0 28px rgba(201,162,39,.08)}
    .m-clock-area{text-align:right}
    #mDate{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:var(--gold);letter-spacing:.04em}
    #mTime{font-family:'JetBrains Mono',monospace;font-size:1.65rem;font-weight:700;
      color:var(--text);letter-spacing:.06em;margin-top:2px}
    .m-main{flex:1;display:flex;flex-direction:column;align-items:center;
      justify-content:center;padding:0 40px}
    .m-divider{width:min(680px,80%);height:1px;
      background:linear-gradient(90deg,transparent,rgba(201,162,39,.2),transparent);
      margin:0 auto}
    .m-serving{display:flex;flex-direction:column;align-items:center;
      width:100%;max-width:900px;padding:36px 0 32px;position:relative}
    .m-serving::before{content:'';position:absolute;top:-60px;left:50%;
      transform:translateX(-50%);width:560px;height:360px;
      background:radial-gradient(ellipse,rgba(201,162,39,.065) 0%,transparent 65%);
      pointer-events:none}
    .m-s-label{font-size:.78rem;font-weight:700;letter-spacing:.28em;
      text-transform:uppercase;color:var(--gold);margin-bottom:18px;
      display:flex;align-items:center;gap:12px}
    .m-s-label span{opacity:1}
    .m-s-label::before,.m-s-label::after{content:'';flex:0 0 56px;height:1px;
      background:linear-gradient(90deg,transparent,rgba(201,162,39,.45))}
    .m-s-label::after{background:linear-gradient(270deg,transparent,rgba(201,162,39,.45))}
    .m-serving-num{font-family:'JetBrains Mono',monospace;
      font-size:clamp(5.5rem,12vw,10rem);font-weight:700;
      color:var(--gold-l);line-height:1;letter-spacing:.06em;
      text-shadow:0 0 80px rgba(201,162,39,.6),0 0 160px rgba(201,162,39,.2),
                  0 0 240px rgba(201,162,39,.1);
      transition:all .3s}
    .m-serving-num.flip{animation:numFlip .55s cubic-bezier(.34,1.56,.64,1)}
    .m-hint{font-size:.78rem;color:var(--text2);margin-top:16px;
      letter-spacing:.1em;opacity:.65;display:flex;align-items:center;gap:7px}
    .live-dot{width:7px;height:7px;border-radius:50%;background:var(--green);
      flex-shrink:0;box-shadow:0 0 6px rgba(0,230,118,.7);
      animation:pDot 2s ease-in-out infinite}
    .m-next{display:flex;flex-direction:column;align-items:center;
      width:100%;max-width:900px;padding:26px 0 18px}
    .m-n-label{font-size:.7rem;font-weight:700;letter-spacing:.26em;
      text-transform:uppercase;color:var(--text2);margin-bottom:10px;
      display:flex;align-items:center;gap:10px}
    .m-n-label::before,.m-n-label::after{content:'';flex:0 0 40px;height:1px;
      background:linear-gradient(90deg,transparent,rgba(122,138,176,.3))}
    .m-n-label::after{background:linear-gradient(270deg,transparent,rgba(122,138,176,.3))}
    .m-next-num{font-family:'JetBrains Mono',monospace;
      font-size:clamp(2.8rem,6vw,5rem);font-weight:700;
      color:var(--text2);line-height:1;letter-spacing:.06em;
      text-shadow:0 0 32px rgba(122,138,176,.2);
      transition:all .3s;opacity:.7}
    .m-next-num.flip{animation:numFlip .55s cubic-bezier(.34,1.56,.64,1)}
    .m-next-hint{font-size:.68rem;color:var(--text2);margin-top:8px;
      letter-spacing:.1em;opacity:.4}
    @keyframes numFlip{
      0%{transform:scale(.6) translateY(-18px);opacity:0;filter:blur(5px)}
      65%{transform:scale(1.04);opacity:1;filter:blur(0)}
      100%{transform:scale(1);filter:blur(0)}}
    @keyframes pDot{0%,100%{opacity:1}50%{opacity:.35}}
    .m-footer{padding:8px 32px;border-top:1px solid rgba(201,162,39,.1);
      background:rgba(3,8,22,.9);display:flex;align-items:center;
      justify-content:space-between;font-size:.62rem;color:var(--text2);letter-spacing:.1em}
    .ticker-wrap{overflow:hidden;white-space:nowrap;flex:1;margin:0 22px}
    .ticker-text{display:inline-block;animation:ticker 28s linear infinite;
      color:rgba(201,162,39,.65);font-size:.66rem;letter-spacing:.1em}
    @keyframes ticker{from{transform:translateX(100vw)}to{transform:translateX(-100%)}}
  </style>
</head>
<body>
<div class="bg"><div class="grid"></div></div>
<div class="page">
  <div class="m-hdr">
    <div class="m-logo-area">
      <div class="m-emblem">
        <img src="data:image/png;base64,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" alt="PGPC Logo"/>
      </div>
      <div class="m-school">
        <span class="m-sname">Padre Garcia Polytechnic College</span>
        <span class="m-ssub">Queue Management System &nbsp;·&nbsp; Batangas, Philippines</span>
      </div>
    </div>
    <div class="m-office-badge">{{ office }} Window</div>
    <div class="m-clock-area">
      <div id="mDate"></div>
      <div id="mTime"></div>
    </div>
  </div>

  <div class="m-main">
    <div class="m-serving">
      <div class="m-s-label"><span>Now Serving</span></div>
      <div class="m-serving-num" id="mCurrent">{{ current }}</div>
      <div class="m-hint"><span class="live-dot"></span>Please proceed to the {{ office }} window</div>
    </div>
    <div class="m-divider"></div>
    <div class="m-next">
      <div class="m-n-label"><span>Next Queue</span></div>
      <div class="m-next-num" id="mNext">{{ next_num }}</div>
      <div class="m-next-hint">Please have your documents ready</div>
    </div>
  </div>

  <div class="m-footer">
    <span>PGPC &copy; 2024 &nbsp;&middot;&nbsp; {{ office }} Monitor</span>
    <div class="ticker-wrap">
      <span class="ticker-text">
        Welcome to Padre Garcia Polytechnic College &nbsp;&nbsp;&bull;&nbsp;&nbsp;
        Please wait for your number to be called &nbsp;&nbsp;&bull;&nbsp;&nbsp;
        {{ office }}: proceed to window when your number appears &nbsp;&nbsp;&bull;&nbsp;&nbsp;
        Please have your documents and requirements ready &nbsp;&nbsp;&bull;&nbsp;&nbsp;
        Thank you for your patience and cooperation &nbsp;&nbsp;&bull;&nbsp;&nbsp;
      </span>
    </div>
    <span id="mFootTime"></span>
  </div>
</div>
<script>
  const SLUG='{{ slug }}';
  function clock(){
    const n=new Date();
    document.getElementById('mDate').textContent=n.toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'});
    document.getElementById('mTime').textContent=n.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
    document.getElementById('mFootTime').textContent=n.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',hour12:true});
  }
  clock();setInterval(clock,1000);

  /* ── Web Speech (monitor) ──────────────────────────────────────────────── */
  function ticketForSpeech(t){return t?t.split('').join(' '):''}
  function buildAnnouncement(action,office,ticket){
    const t=ticketForSpeech(ticket);
    if(action==='priority')return`Priority number ${t}. Please proceed to ${office}.`;
    if(action==='recall')return`Recalling for number ${t}. Please proceed to the ${office.toLowerCase()} office.`;
    return`Number ${t}. Please proceed to the ${office} window.`;
  }
  function speak(text){
    if(!window.speechSynthesis)return;
    window.speechSynthesis.cancel();
    const utt=new SpeechSynthesisUtterance(text);
    utt.lang='en-US';utt.rate=0.88;utt.pitch=1.0;utt.volume=1.0;
    function doSpeak(){
      const voices=window.speechSynthesis.getVoices();
      const pick=voices.find(v=>/en.*(US|PH)/i.test(v.lang)&&/female|zira|samantha|karen|aria/i.test(v.name))
                ||voices.find(v=>/en/i.test(v.lang));
      if(pick)utt.voice=pick;
      window.speechSynthesis.speak(utt);
    }
    if(window.speechSynthesis.getVoices().length){doSpeak();}
    else{window.speechSynthesis.addEventListener('voiceschanged',doSpeak,{once:true});}
  }
  function playDing(){
    try{
      const ctx=new(window.AudioContext||window.webkitAudioContext)();
      function tone(freq,start,dur,vol){
        const osc=ctx.createOscillator(),g=ctx.createGain();
        osc.connect(g);g.connect(ctx.destination);
        osc.type='sine';osc.frequency.value=freq;
        g.gain.setValueAtTime(0,ctx.currentTime+start);
        g.gain.linearRampToValueAtTime(vol,ctx.currentTime+start+0.025);
        g.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+start+dur);
        osc.start(ctx.currentTime+start);
        osc.stop(ctx.currentTime+start+dur+0.05);
      }
      tone(880,0,1.4,0.55);
      tone(659,0.42,1.6,0.50);
      setTimeout(()=>ctx.close(),2800);
    }catch(e){}
  }

  /* ── Polling ──────────────────────────────────────────────────────────── */
  let lastRecallCount=-1;
  const OFFICE='{{ office }}';

  async function poll(){
    try{
      const r=await fetch('/api/monitor/'+SLUG);const d=await r.json();
      if(!d.success)return;
      const cEl=document.getElementById('mCurrent');
      const nEl=document.getElementById('mNext');

      /* ticket changed → announce new number */
      if(cEl.textContent!==d.current){
        cEl.textContent=d.current||'----';
        cEl.classList.remove('flip');void cEl.offsetWidth;cEl.classList.add('flip');
        if(d.current&&d.current!=='----'){
          playDing();
          const action=d.current.startsWith('P')?'priority':'next';
          setTimeout(()=>speak(buildAnnouncement(action,OFFICE,d.current)),680);
        }
      }
      if(nEl.textContent!==d.next){
        nEl.textContent=d.next||'----';
        nEl.classList.remove('flip');void nEl.offsetWidth;nEl.classList.add('flip');
      }

      /* recall_count changed → re-announce current ticket */
      const rc=d.recall_count||0;
      if(lastRecallCount===-1){
        /* first poll – just initialise, don't speak */
        lastRecallCount=rc;
      } else if(rc>lastRecallCount){
        lastRecallCount=rc;
        const cur=cEl.textContent;
        if(cur&&cur!=='----'){
          playDing();
          setTimeout(()=>speak(buildAnnouncement('recall',OFFICE,cur)),680);
        }
      }
    }catch{}
  }
  setInterval(poll,2000);
  poll(); /* run immediately on page load so we hear the current number */
</script>
</body>
</html>"""


OPERATOR_LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{{ office }} Login — PGPC Queue</title>
  <link rel="icon" type="image/png" href="data:image/png;base64,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"/>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Oxanium:wght@400;600;700;800&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    :root{
      --navy:#030816;--navy2:#060d1f;--royal:#1a3a8f;
      --gold:#c9a227;--gold-l:#f0c840;--gold-d:#8a6913;
      --gold-pale:rgba(201,162,39,.12);--gold-bd:rgba(201,162,39,.25);
      --glass:rgba(10,18,60,.78);--text:#f0f4ff;--text2:#7a8ab0;
      --red:#ff4f6d;--green:#00e676;
    }
    html,body{height:100%;background:var(--navy);color:var(--text);
      font-family:'DM Sans',sans-serif;display:flex;justify-content:center;
      align-items:center;overflow:hidden}
    .bg{position:fixed;inset:0;z-index:0;
      background:radial-gradient(ellipse at 20% 25%,rgba(26,58,143,.35) 0%,transparent 55%),
                 radial-gradient(ellipse at 80% 75%,rgba(201,162,39,.08) 0%,transparent 55%),
                 var(--navy)}
    .grid{position:absolute;inset:0;
      background-image:linear-gradient(rgba(201,162,39,.028) 1px,transparent 1px),
                       linear-gradient(90deg,rgba(201,162,39,.028) 1px,transparent 1px);
      background-size:64px 64px}
    canvas#ptx{position:fixed;inset:0;pointer-events:none;z-index:0}
    .card{position:relative;z-index:2;width:420px;padding:48px 44px;
      background:var(--glass);border:1px solid var(--gold-bd);border-radius:24px;
      backdrop-filter:blur(28px);-webkit-backdrop-filter:blur(28px);
      box-shadow:0 0 0 1px rgba(201,162,39,.06),0 0 80px rgba(201,162,39,.07),0 32px 80px rgba(0,0,0,.65);
      animation:cardIn .7s cubic-bezier(.16,1,.3,1) both}
    @keyframes cardIn{from{opacity:0;transform:translateY(32px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}
    .card::before,.card::after{content:'';position:absolute;width:22px;height:22px;border-color:var(--gold);border-style:solid;border-width:0}
    .card::before{top:14px;left:14px;border-top-width:2px;border-left-width:2px;border-radius:4px 0 0 0;opacity:.6}
    .card::after{bottom:14px;right:14px;border-bottom-width:2px;border-right-width:2px;border-radius:0 0 4px 0;opacity:.6}
    .emblem{display:flex;flex-direction:column;align-items:center;margin-bottom:30px;gap:10px}
    .emblem-ring{width:76px;height:76px;border-radius:50%;
      background:radial-gradient(circle,rgba(26,58,143,.5),rgba(201,162,39,.1));
      border:2px solid var(--gold-bd);display:flex;align-items:center;justify-content:center;
      position:relative;box-shadow:0 0 0 4px rgba(201,162,39,.06),0 0 32px rgba(201,162,39,.1);
      animation:ringPulse 4s ease-in-out infinite}
    @keyframes ringPulse{0%,100%{box-shadow:0 0 0 4px rgba(201,162,39,.06),0 0 32px rgba(201,162,39,.1)}
      50%{box-shadow:0 0 0 6px rgba(201,162,39,.1),0 0 48px rgba(201,162,39,.18)}}
    .emblem-ring::before{content:'';position:absolute;inset:5px;border-radius:50%;
      border:1px solid rgba(201,162,39,.18)}
    .emblem-ring img{width:52px;height:52px;border-radius:50%;object-fit:cover}
    .school-name{font-family:'Cinzel',serif;font-weight:700;font-size:1.05rem;
      color:var(--gold-l);letter-spacing:.1em;text-align:center;line-height:1.3;
      text-shadow:0 0 20px rgba(201,162,39,.3)}
    .school-tag{font-size:.6rem;font-weight:600;letter-spacing:.2em;text-transform:uppercase;
      color:var(--text2);text-align:center;margin-top:2px}
    .office-badge{display:inline-block;padding:4px 18px;border-radius:20px;margin:10px auto 0;
      background:rgba(201,162,39,.1);border:1px solid rgba(201,162,39,.3);
      font-family:'Oxanium',sans-serif;font-weight:800;font-size:.78rem;
      color:var(--gold-l);letter-spacing:.14em;text-transform:uppercase}
    .divider{width:80px;height:1px;
      background:linear-gradient(90deg,transparent,var(--gold),transparent);
      margin:20px auto;opacity:.4}
    .form-title{font-family:'Oxanium',sans-serif;font-weight:700;font-size:.8rem;
      letter-spacing:.15em;text-transform:uppercase;color:var(--text2);text-align:center;margin-bottom:20px}
    .field{margin-bottom:15px}
    .field label{display:block;font-size:.65rem;font-weight:600;letter-spacing:.12em;
      text-transform:uppercase;color:var(--text2);margin-bottom:7px}
    .field input{width:100%;padding:12px 16px;background:rgba(255,255,255,.04);
      border:1px solid rgba(201,162,39,.18);border-radius:10px;color:var(--text);
      font-family:'DM Sans',sans-serif;font-size:.92rem;outline:none;
      transition:border-color .3s,box-shadow .3s,background .3s}
    .field input:focus{border-color:var(--gold);background:rgba(201,162,39,.04);
      box-shadow:0 0 0 3px rgba(201,162,39,.14)}
    .field input::placeholder{color:rgba(122,138,176,.4)}
    .btn-login{width:100%;padding:13px 0;margin-top:10px;
      background:linear-gradient(135deg,#c9a227,#8a6913);
      border:none;border-radius:10px;color:#030816;
      font-family:'Oxanium',sans-serif;font-weight:800;font-size:.95rem;
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
    .message{margin-top:12px;text-align:center;font-size:.82rem;font-weight:500;min-height:18px}
    .message.error{color:var(--red)}.message.success{color:var(--green)}
    .footer-row{margin-top:20px;text-align:center;font-size:.66rem;color:var(--text2);opacity:.45}
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
      <img src="data:image/png;base64,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" alt="PGPC Logo"/>
    </div>
    <div class="school-name">Padre Garcia<br>Polytechnic College</div>
    <div class="school-tag">Queue Management System</div>
    <div class="office-badge">{{ office }}</div>
  </div>
  <div class="divider"></div>
  <div class="form-title">Operator Access</div>
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
  <div class="footer-row">
    <a href="/display" target="_blank">Queue Display</a> &nbsp;&middot;&nbsp;
    <a href="/">Admin Login</a> &nbsp;&middot;&nbsp; PGPC &copy; 2024
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
const OFFICE='{{ office }}';
const SLUG='{{ slug }}';
const loginBtn=document.getElementById('loginBtn'),msgEl=document.getElementById('msg');
function showMsg(t,cls){msgEl.textContent=t;msgEl.className='message '+cls}
document.addEventListener('keydown',e=>{if(e.key==='Enter')loginBtn.click()});
loginBtn.addEventListener('click',async()=>{
  const u=document.getElementById('usr').value.trim();
  const p=document.getElementById('pwd').value.trim();
  if(!u||!p){showMsg('Please fill in all fields.','error');return}
  loginBtn.disabled=true;loginBtn.textContent='Authenticating…';showMsg('','');
  try{
    const r=await fetch('/api/operator-login',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({office:OFFICE,username:u,password:p})});
    const d=await r.json();
    if(d.success){showMsg('Access granted. Redirecting…','success');
      setTimeout(()=>{location.href=d.redirect},900)}
    else{loginBtn.disabled=false;loginBtn.textContent='Sign In';
      showMsg(d.message||'Authentication failed.','error')}
  }catch{loginBtn.disabled=false;loginBtn.textContent='Sign In';showMsg('Connection error.','error')}
});
</script>
</body>
</html>
"""

OFFICE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{{ office }} — PGPC Queue</title>
  <link rel="icon" type="image/png" href="data:image/png;base64,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"/>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Oxanium:wght@400;600;700;800&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    :root{
      --navy:#030816;--navy2:#060d1f;--royal:#1a3a8f;
      --gold:#c9a227;--gold-l:#f0c840;--gold-d:#8a6913;
      --gold-pale:rgba(201,162,39,.12);--gold-bd:rgba(201,162,39,.25);
      --glass:rgba(10,18,60,.78);--text:#f0f4ff;--text2:#7a8ab0;
      --red:#ff4f6d;--green:#00e676;--amber:#f5a623;
    }
    html,body{min-height:100%;background:var(--navy);color:var(--text);font-family:\'DM Sans\',sans-serif}
    .bg{position:fixed;inset:0;z-index:0;
      background:radial-gradient(ellipse at 20% 15%,rgba(26,58,143,.45) 0%,transparent 55%),
                 radial-gradient(ellipse at 80% 85%,rgba(201,162,39,.07) 0%,transparent 55%),
                 var(--navy)}
    .grid{position:fixed;inset:0;
      background-image:linear-gradient(rgba(201,162,39,.022) 1px,transparent 1px),
                       linear-gradient(90deg,rgba(201,162,39,.022) 1px,transparent 1px);
      background-size:60px 60px}
    .layout{position:relative;z-index:1;min-height:100vh;display:flex;flex-direction:column}

    /* ── Header ── */
    header{display:flex;align-items:center;justify-content:space-between;
      padding:13px 26px;border-bottom:1px solid var(--gold-bd);
      background:rgba(3,8,22,.90);backdrop-filter:blur(16px);position:sticky;top:0;z-index:100}
    .h-left{display:flex;align-items:center;gap:11px}
    .h-emblem{width:36px;height:36px;border-radius:50%;border:1.5px solid rgba(201,162,39,.4);
      overflow:hidden;box-shadow:0 0 12px rgba(201,162,39,.1);flex-shrink:0}
    .h-emblem img{width:100%;height:100%;object-fit:cover}
    .h-brand{display:flex;flex-direction:column;line-height:1}
    .h-name{font-family:\'Cinzel\',serif;font-size:.82rem;font-weight:700;color:var(--gold-l);letter-spacing:.06em}
    .h-sub{font-size:.58rem;color:var(--text2);letter-spacing:.12em;margin-top:2px}
    .h-badge{padding:5px 15px;border-radius:8px;
      background:rgba(201,162,39,.1);border:1px solid rgba(201,162,39,.3);
      font-family:\'Oxanium\',sans-serif;font-weight:800;font-size:.8rem;
      color:var(--gold-l);letter-spacing:.14em;text-transform:uppercase}
    .h-right{display:flex;align-items:center;gap:7px}
    .btn-hdr{display:flex;align-items:center;gap:5px;padding:6px 12px;border-radius:8px;
      border:1px solid rgba(201,162,39,.2);background:rgba(201,162,39,.06);
      color:var(--text2);font-size:.72rem;font-weight:600;cursor:pointer;
      transition:all .2s;font-family:\'DM Sans\',sans-serif}
    .btn-hdr svg{width:13px;height:13px;stroke:currentColor;stroke-width:2;fill:none}
    .btn-hdr:hover,.btn-hdr.gold-on{background:rgba(201,162,39,.12);border-color:rgba(201,162,39,.35);color:var(--gold)}
    .online-dot{width:6px;height:6px;border-radius:50%;background:var(--green);
      box-shadow:0 0 5px rgba(0,230,118,.7);animation:pDot 2s ease-in-out infinite}
    @keyframes pDot{0%,100%{opacity:1}50%{opacity:.35}}

    /* ── Main grid ── */
    main{flex:1;padding:30px 26px;display:grid;
      grid-template-columns:1fr 300px;gap:22px;align-items:start;
      max-width:1100px;width:100%;margin:0 auto}

    /* ── Hero card ── */
    .hero{background:var(--glass);border:1px solid var(--gold-bd);
      border-radius:24px;backdrop-filter:blur(20px);
      padding:44px 32px 36px;display:flex;flex-direction:column;align-items:center;
      position:relative;overflow:hidden}
    .hero::before{content:\'\';position:absolute;top:-80px;left:50%;
      transform:translateX(-50%);width:500px;height:400px;
      background:radial-gradient(ellipse,rgba(201,162,39,.07) 0%,transparent 65%);
      pointer-events:none}
    .hero-lbl{font-size:.68rem;font-weight:700;letter-spacing:.28em;
      text-transform:uppercase;color:var(--gold);margin-bottom:22px;
      display:flex;align-items:center;gap:12px}
    .hero-lbl::before,.hero-lbl::after{content:\'\';flex:0 0 52px;height:1px;
      background:linear-gradient(90deg,transparent,rgba(201,162,39,.45))}
    .hero-lbl::after{background:linear-gradient(270deg,transparent,rgba(201,162,39,.45))}
    .hero-num{font-family:\'JetBrains Mono\',monospace;
      font-size:clamp(5rem,13vw,9.5rem);font-weight:700;
      color:var(--gold-l);line-height:1;letter-spacing:.06em;
      text-shadow:0 0 80px rgba(201,162,39,.55),0 0 160px rgba(201,162,39,.18);transition:all .3s}
    .hero-num.flip{animation:numFlip .55s cubic-bezier(.34,1.56,.64,1)}
    @keyframes numFlip{
      0%{transform:scale(.6) translateY(-18px);opacity:0;filter:blur(5px)}
      65%{transform:scale(1.04);opacity:1;filter:blur(0)}100%{transform:scale(1)}}
    .hero-type{margin-top:11px;font-size:.7rem;font-weight:600;
      padding:4px 16px;border-radius:20px;letter-spacing:.08em;
      background:rgba(201,162,39,.12);border:1px solid rgba(201,162,39,.22);color:var(--gold)}
    .hero-type.priority{background:rgba(245,166,35,.15);border-color:rgba(245,166,35,.3);color:var(--amber)}
    .hero-hint{font-size:.68rem;color:var(--text2);margin-top:10px;
      letter-spacing:.08em;opacity:.55;display:flex;align-items:center;gap:6px}
    .live-dot{width:6px;height:6px;border-radius:50%;background:var(--green);
      flex-shrink:0;box-shadow:0 0 5px rgba(0,230,118,.7);animation:pDot 2s ease-in-out infinite}

    /* ── Action buttons ── */
    .actions{display:flex;gap:11px;margin-top:34px;width:100%;justify-content:center;flex-wrap:wrap}
    .btn-act{display:flex;align-items:center;gap:7px;padding:14px 26px;border-radius:12px;
      font-family:\'DM Sans\',sans-serif;font-weight:700;font-size:.88rem;
      cursor:pointer;transition:all .28s;position:relative;overflow:hidden;letter-spacing:.02em}
    .btn-act svg{width:15px;height:15px;stroke:currentColor;stroke-width:2.2;fill:none}
    .ripple{position:absolute;border-radius:50%;background:rgba(255,255,255,.18);
      transform:scale(0);animation:rpl .6s linear;pointer-events:none}
    @keyframes rpl{to{transform:scale(4);opacity:0}}
    .btn-next{background:rgba(201,162,39,.12);border:1.5px solid rgba(201,162,39,.35);
      color:var(--gold-l);min-width:130px}
    .btn-next:hover{background:rgba(201,162,39,.22);box-shadow:0 4px 20px rgba(201,162,39,.18);transform:translateY(-1px)}
    .btn-recall{background:rgba(122,138,176,.08);border:1.5px solid rgba(122,138,176,.25);
      color:var(--text2);min-width:130px}
    .btn-recall:hover{background:rgba(122,138,176,.16);box-shadow:0 4px 16px rgba(122,138,176,.1);transform:translateY(-1px)}
    .btn-priority{background:rgba(245,166,35,.08);border:1.5px solid rgba(245,166,35,.22);
      color:var(--amber);min-width:170px}
    .btn-priority:hover{background:rgba(245,166,35,.16);box-shadow:0 4px 16px rgba(245,166,35,.12);transform:translateY(-1px)}

    /* ── Sidebar ── */
    .sidebar{display:flex;flex-direction:column;gap:14px}
    .panel{background:var(--glass);border:1px solid var(--gold-bd);
      border-radius:18px;backdrop-filter:blur(20px);overflow:hidden}
    .panel-hdr{padding:11px 15px;border-bottom:1px solid rgba(201,162,39,.1);
      display:flex;align-items:center;justify-content:space-between}
    .panel-title{font-family:\'Oxanium\',sans-serif;font-weight:700;font-size:.73rem;
      color:var(--text);letter-spacing:.08em;text-transform:uppercase}
    .p-badge{font-size:.6rem;font-weight:600;padding:2px 7px;border-radius:20px;
      background:rgba(201,162,39,.12);border:1px solid rgba(201,162,39,.2);color:var(--gold)}
    .stats-body{padding:14px 15px}
    .stat-row{display:flex;align-items:center;justify-content:space-between;
      padding:9px 0;border-bottom:1px solid rgba(255,255,255,.04)}
    .stat-row:last-child{border-bottom:none;padding-bottom:0}
    .stat-lbl{font-size:.73rem;color:var(--text2)}
    .stat-val{font-family:\'JetBrains Mono\',monospace;font-size:1.05rem;font-weight:700;color:var(--gold-l)}
    .stat-val.pop{animation:statPop .4s cubic-bezier(.34,1.56,.64,1)}
    @keyframes statPop{0%{transform:scale(.8)}60%{transform:scale(1.1)}100%{transform:scale(1)}}
    .h-list{max-height:290px;overflow-y:auto;padding:5px 0}
    .h-list::-webkit-scrollbar{width:3px}
    .h-list::-webkit-scrollbar-thumb{background:rgba(201,162,39,.2);border-radius:4px}
    .h-item{padding:7px 15px;display:flex;align-items:center;gap:8px;
      border-bottom:1px solid rgba(255,255,255,.03);animation:slideIn .3s ease}
    @keyframes slideIn{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)}}
    .h-icon{width:22px;height:22px;border-radius:6px;display:flex;
      align-items:center;justify-content:center;font-size:.68rem;flex-shrink:0}
    .ic-next{background:rgba(201,162,39,.15);color:var(--gold-l)}
    .ic-recall{background:rgba(122,138,176,.15);color:var(--text2)}
    .ic-priority{background:rgba(245,166,35,.15);color:var(--amber)}
    .ic-reset{background:rgba(255,79,109,.15);color:var(--red)}
    .h-text{flex:1;min-width:0}
    .h-ticket{font-family:\'JetBrains Mono\',monospace;font-size:.76rem;font-weight:700;color:var(--text)}
    .h-action{font-size:.62rem;color:var(--text2);margin-top:1px}
    .h-time{font-family:\'JetBrains Mono\',monospace;font-size:.58rem;color:var(--text2);opacity:.5;flex-shrink:0}
    .h-empty{padding:20px 15px;text-align:center;font-size:.72rem;color:var(--text2);opacity:.4}
    .btn-monitor{display:flex;align-items:center;justify-content:center;gap:7px;
      width:100%;padding:11px;border-radius:10px;
      background:rgba(122,138,176,.07);border:1px solid rgba(122,138,176,.2);
      color:var(--text2);font-family:\'DM Sans\',sans-serif;font-size:.76rem;font-weight:600;
      cursor:pointer;transition:all .2s;text-decoration:none}
    .btn-monitor svg{width:13px;height:13px;stroke:currentColor;stroke-width:2;fill:none}
    .btn-monitor:hover{background:rgba(201,162,39,.08);border-color:rgba(201,162,39,.28);color:var(--gold)}

    /* ── Toast ── */
    #toast{position:fixed;bottom:24px;left:50%;
      transform:translateX(-50%) translateY(120px);
      background:rgba(3,8,22,.97);border:1px solid var(--gold-bd);border-radius:14px;
      padding:10px 18px;display:flex;align-items:center;gap:8px;
      font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:var(--text);
      backdrop-filter:blur(20px);box-shadow:0 8px 40px rgba(0,0,0,.65);
      z-index:300;transition:transform .45s cubic-bezier(.34,1.56,.64,1),opacity .3s;
      opacity:0;white-space:nowrap;max-width:92vw}
    #toast.show{transform:translateX(-50%) translateY(0);opacity:1}
    #toast.success{border-color:rgba(0,230,118,.25);color:var(--green)}
    #toast.warning{border-color:rgba(245,166,35,.25);color:var(--amber)}
    #toast.error{border-color:rgba(255,79,109,.25);color:var(--red)}

    @media(max-width:720px){
      main{grid-template-columns:1fr;padding:18px 14px}
      .hero-num{font-size:5rem}
      .actions{flex-direction:column;align-items:stretch}
      .btn-act{justify-content:center}
    }
  </style>
</head>
<body>
<div class="bg"><div class="grid"></div></div>
<div class="layout">

  <header>
    <div class="h-left">
      <div class="h-emblem">
        <img src="data:image/png;base64,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" alt="PGPC"/>
      </div>
      <div class="h-brand">
        <span class="h-name">PGPC</span>
        <span class="h-sub">Queue System</span>
      </div>
    </div>
    <div class="h-badge">{{ office }}</div>
    <div class="h-right">
      <div style="display:flex;align-items:center;gap:5px;font-size:.68rem;color:var(--green);letter-spacing:.04em">
        <div class="online-dot"></div>Online
      </div>
      <button class="btn-hdr gold-on" id="soundBtn">
        <svg id="sndIcon" viewBox="0 0 24 24">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
          <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
        </svg>
        <span id="sndLbl">Voice</span>
      </button>
      <button class="btn-hdr" onclick="window.open(\'/monitor/{{ slug }}\',\'_blank\')">
        <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/>
          <path d="M8 21h8m-4-4v4" stroke-linecap="round"/></svg>
        Monitor
      </button>
      <button class="btn-hdr" onclick="location.href=\'/admin\'">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        Admin
      </button>
      <button class="btn-hdr" onclick="location.href='/{{ slug }}/logout'">
        <svg viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke-linecap="round"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
        Logout
      </button>
    </div>
  </header>

  <main>
    <!-- Hero: ticket display + action buttons -->
    <div class="hero">
      <div class="hero-lbl"><span>Now Serving</span></div>
      <div class="hero-num" id="curNum">{{ current }}</div>
      <div class="hero-type" id="curType">Regular</div>
      <div class="hero-hint">
        <div class="live-dot"></div>
        <span>{{ office }} window &nbsp;&middot;&nbsp; live</span>
      </div>
      <div class="actions">
        <button class="btn-act btn-next" id="btnNext">
          <svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>Next
        </button>
        <button class="btn-act btn-recall" id="btnRecall">
          <svg viewBox="0 0 24 24"><polyline points="1 4 1 10 7 10"/>
            <path d="M3.51 15a9 9 0 1 0 .49-3.54"/></svg>Recall
        </button>
        <button class="btn-act btn-priority" id="btnPriority">
          <svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          Priority Ticket
        </button>
      </div>
    </div>

    <!-- Sidebar -->
    <div class="sidebar">
      <!-- Stats -->
      <div class="panel">
        <div class="panel-hdr"><span class="panel-title">Today\'s Stats</span></div>
        <div class="stats-body">
          <div class="stat-row">
            <span class="stat-lbl">Served Today</span>
            <span class="stat-val" id="statServed">{{ served }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-lbl">Now Serving</span>
            <span class="stat-val" id="statCur" style="font-size:.85rem">{{ current }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-lbl">Next Up</span>
            <span class="stat-val" id="statNext" style="font-size:.85rem;color:var(--text2)">—</span>
          </div>
        </div>
      </div>

      <!-- Open monitor link -->
      <a class="btn-monitor" href="/monitor/{{ slug }}" target="_blank">
        <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/>
          <line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        Open {{ office }} Monitor Screen
      </a>

      <!-- Activity log (this office only) -->
      <div class="panel">
        <div class="panel-hdr">
          <span class="panel-title">Activity Log</span>
          <span class="p-badge" id="hCount">0</span>
        </div>
        <div class="h-list" id="hList"><div class="h-empty">No activity yet</div></div>
      </div>
    </div>
  </main>
</div>

<div id="toast" role="status" aria-live="polite">
  <span id="tIcon">✓</span><span id="tText"></span>
</div>

<script>
  const OFFICE=\'{{ office }}\';
  const SLUG=\'{{ slug }}\';
  let soundOn=true;

  /* ── Audio & Speech ─────────────────────────────────────────────────────── */
  function playDing(){
    if(!soundOn)return;
    try{
      const ctx=new(window.AudioContext||window.webkitAudioContext)();
      function tone(f,s,d,v){
        const o=ctx.createOscillator(),g=ctx.createGain();
        o.connect(g);g.connect(ctx.destination);o.type=\'sine\';o.frequency.value=f;
        g.gain.setValueAtTime(0,ctx.currentTime+s);
        g.gain.linearRampToValueAtTime(v,ctx.currentTime+s+0.025);
        g.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+s+d);
        o.start(ctx.currentTime+s);o.stop(ctx.currentTime+s+d+0.05);
      }
      tone(880,0,1.4,0.55);tone(659,0.42,1.6,0.50);
      setTimeout(()=>ctx.close(),2800);
    }catch(e){}
  }
  function speak(text){
    if(!soundOn||!window.speechSynthesis)return;
    window.speechSynthesis.cancel();
    const utt=new SpeechSynthesisUtterance(text);
    utt.lang=\'en-US\';utt.rate=0.88;utt.pitch=1.0;utt.volume=1.0;
    function doSpeak(){
      const voices=window.speechSynthesis.getVoices();
      const pick=voices.find(v=>/en.*(US|PH)/i.test(v.lang)&&/female|zira|samantha|karen|aria/i.test(v.name))
                ||voices.find(v=>/en/i.test(v.lang));
      if(pick)utt.voice=pick;
      window.speechSynthesis.speak(utt);
    }
    if(window.speechSynthesis.getVoices().length){doSpeak();}
    else{window.speechSynthesis.addEventListener(\'voiceschanged\',doSpeak,{once:true});}
  }
  function ticketForSpeech(t){return t?t.split(\'\').join(\' \'):'';}
  function buildAnnouncement(action,ticket){
    const t=ticketForSpeech(ticket);
    if(action===\'priority\')return`Priority number ${t}. Please proceed to the ${OFFICE} window.`;
    if(action===\'recall\')return`Recalling for number ${t}. Please proceed to the ${OFFICE.toLowerCase()} office.`;
    return`Number ${t}. Please proceed to the ${OFFICE} window.`;
  }

  /* ── Sound toggle ────────────────────────────────────────────────────────── */
  document.getElementById(\'soundBtn\').addEventListener(\'click\',function(){
    soundOn=!soundOn;
    if(!soundOn&&window.speechSynthesis)window.speechSynthesis.cancel();
    this.classList.toggle(\'gold-on\',soundOn);
    document.getElementById(\'sndLbl\').textContent=soundOn?\'Voice\':\'Muted\';
    document.getElementById(\'sndIcon\').innerHTML=soundOn
      ?\'<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>\'
      :\'<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>\'
    showToast(soundOn?\'Voice on\':\'Muted\',soundOn?\'success\':\'warning\');
  });

  /* ── Toast ───────────────────────────────────────────────────────────────── */
  let tTimer=null;
  function showToast(msg,type=\'\'){
    const icons={success:\'✓\',warning:\'⚠\',error:\'✕\'};
    const el=document.getElementById(\'toast\');
    document.getElementById(\'tIcon\').textContent=icons[type]||\' ℹ\';
    document.getElementById(\'tText\').textContent=msg;
    el.className=\'show\'+(type?\' \'+type:\'\');
    clearTimeout(tTimer);tTimer=setTimeout(()=>{el.className=\'\'},3800);
  }

  /* ── Ripple ──────────────────────────────────────────────────────────────── */
  function ripple(btn,e){
    const r=btn.getBoundingClientRect(),sp=document.createElement(\'span\');
    sp.className=\'ripple\';const s=Math.max(r.width,r.height);
    sp.style.cssText=`width:${s}px;height:${s}px;left:${e.clientX-r.left-s/2}px;top:${e.clientY-r.top-s/2}px`;
    btn.appendChild(sp);setTimeout(()=>sp.remove(),600);
  }

  /* ── UI helpers ──────────────────────────────────────────────────────────── */
  function setNum(num){
    const el=document.getElementById(\'curNum\');
    const te=document.getElementById(\'curType\');
    el.textContent=num||\' ----\';
    el.classList.remove(\'flip\');void el.offsetWidth;el.classList.add(\'flip\');
    document.getElementById(\'statCur\').textContent=num||\'----\';
    const isPri=num&&num.startsWith(\'P\');
    te.textContent=isPri?\'Priority\':\'Regular\';
    te.className=\'hero-type\'+(isPri?\' priority\':\'\');
  }
  function setServed(n){
    const el=document.getElementById(\'statServed\');
    if(el&&el.textContent!=n){el.textContent=n;el.classList.remove(\'pop\');void el.offsetWidth;el.classList.add(\'pop\')}
  }
  function setNext(n){
    const el=document.getElementById(\'statNext\');if(el)el.textContent=n||\'—\';
  }

  /* ── History (filtered to this office) ─────────────────────────────────── */
  function renderHistory(hist){
    const mine=hist.filter(h=>h.office===OFFICE);
    document.getElementById(\'hCount\').textContent=mine.length;
    const list=document.getElementById(\'hList\');
    if(!mine.length){list.innerHTML=\'<div class="h-empty">No activity yet</div>\';return}
    const ic={next:{c:\'ic-next\',s:\'→\'},recall:{c:\'ic-recall\',s:\'↺\'},priority:{c:\'ic-priority\',s:\'★\'},reset:{c:\'ic-reset\',s:\'⊘\'}};
    list.innerHTML=mine.slice(0,20).map(h=>{
      const i=ic[h.type]||{c:\'ic-next\',s:\'·\'};
      return`<div class="h-item"><div class="h-icon ${i.c}">${i.s}</div>
        <div class="h-text"><div class="h-ticket">${h.ticket}</div>
        <div class="h-action">${h.type}</div></div>
        <div class="h-time">${h.time}</div></div>`;
    }).join(\'\');
  }
  async function loadHistory(){
    try{const r=await fetch(\'/api/history\');const d=await r.json();if(d.success)renderHistory(d.history)}catch{}
  }

  function announceRecall(){
    const ticket=document.getElementById(\'curNum\').textContent.trim();
    if(!ticket||ticket===\'----\'||!soundOn)return;
    playDing();
    setTimeout(()=>speak(buildAnnouncement(\'recall\',ticket)),680);
  }

  /* ── API call ────────────────────────────────────────────────────────────── */
  async function api(action){
    try{
      const res=await fetch(\'/api/\'+action,{method:\'POST\',
        headers:{\'Content-Type\':\'application/json\'},
        body:JSON.stringify({office:OFFICE})});
      const d=await res.json();
      if(d.success){
        const ticket=d.state?d.state[OFFICE]:\'\';
        setNum(ticket);
        if(d.served)setServed(d.served[OFFICE]||0);
        showToast(d.message,\'success\');
        if(action===\'recall\'){
          lastRecallCount=d.recall_count||lastRecallCount;
        }else if(ticket&&ticket!==\'----\'){
          playDing();
          const ann=action===\'priority\'?\'priority\':\'next\';
          setTimeout(()=>speak(buildAnnouncement(ann,ticket)),680);
        }
        loadHistory();
      }else showToast(d.message||\'Error.\',\'error\');
    }catch{showToast(\'Connection error.\',\'error\')}
  }

  /* ── Polling ─────────────────────────────────────────────────────────────── */
  let lastRecallCount=-1;
  async function poll(){
    try{
      const r=await fetch(\'/api/monitor/\'+SLUG);const d=await r.json();
      if(!d.success)return;
      const cEl=document.getElementById(\'curNum\');
      if(cEl.textContent!==d.current)setNum(d.current);
      setNext(d.next);
      if(d.served!==undefined)setServed(d.served);
      const rc=d.recall_count||0;
      if(lastRecallCount===-1){lastRecallCount=rc;}
      else if(rc>lastRecallCount){
        lastRecallCount=rc;
        const cur=d.current;
        if(cur&&cur!==\'----\'){
          playDing();
          setTimeout(()=>speak(buildAnnouncement(\'recall\',cur)),680);
        }
      }
    }catch{}
  }
  setInterval(poll,2000);

  /* ── Button wiring ───────────────────────────────────────────────────────── */
  document.getElementById(\'btnNext\').addEventListener(\'click\',e=>{ripple(e.currentTarget,e);api(\'next\')});
  document.getElementById(\'btnRecall\').addEventListener(\'click\',e=>{ripple(e.currentTarget,e);announceRecall();api(\'recall\')});
  document.getElementById(\'btnPriority\').addEventListener(\'click\',e=>{ripple(e.currentTarget,e);api(\'priority\')});

  /* ── Init ────────────────────────────────────────────────────────────────── */
  (async()=>{
    try{
      const r=await fetch(\'/api/monitor/\'+SLUG);const d=await r.json();
      if(d.success){setNext(d.next);setServed(d.served);lastRecallCount=d.recall_count||0;}
    }catch{}
    loadHistory();
  })();
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

@app.route('/monitor/<slug>')
def monitor(slug):
    normalized = slug.lower().replace('-', ' ')
    office = next((k for k in offices_data if k.lower() == normalized), None)
    if not office:
        return f"<h2>Office not found: {slug}</h2>", 404
    od = offices_data[office]
    return render_template_string(MONITOR_HTML,
                                  office=office,
                                  slug=slug,
                                  current=od['current'],
                                  next_num=next_ticket(office))
@app.route('/cashier')
def cashier_page():
    if not session.get('op_cashier'):
        return redirect('/cashier/login')
    od = offices_data.get('Cashier', {})
    return render_template_string(OFFICE_HTML,
                                  office='Cashier', slug='cashier',
                                  current=od.get('current', '----'),
                                  served=od.get('served', 0))

@app.route('/registrar')
def registrar_page():
    if not session.get('op_registrar'):
        return redirect('/registrar/login')
    od = offices_data.get('Registrar', {})
    return render_template_string(OFFICE_HTML,
                                  office='Registrar', slug='registrar',
                                  current=od.get('current', '----'),
                                  served=od.get('served', 0))

@app.route('/cashier/login')
def cashier_login():
    if session.get('op_cashier'):
        return redirect('/cashier')
    return render_template_string(OPERATOR_LOGIN_HTML, office='Cashier', slug='cashier')

@app.route('/registrar/login')
def registrar_login():
    if session.get('op_registrar'):
        return redirect('/registrar')
    return render_template_string(OPERATOR_LOGIN_HTML, office='Registrar', slug='registrar')

@app.route('/cashier/logout')
def cashier_logout():
    session.pop('op_cashier', None)
    return redirect('/cashier/login')

@app.route('/registrar/logout')
def registrar_logout():
    session.pop('op_registrar', None)
    return redirect('/registrar/login')

@app.route('/api/operator-login', methods=['POST'])
def api_operator_login():
    data = request.get_json() or {}
    office   = data.get('office', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    creds = OPERATOR_CREDS.get(office)
    if not creds:
        return jsonify(success=False, message='Invalid office.'), 400
    if username == creds['username'] and password == creds['password']:
        slug = office.lower().replace(' ', '-')
        session['op_' + slug] = True
        return jsonify(success=True, redirect='/' + slug)
    return jsonify(success=False, message='Incorrect username or password.'), 401



@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u = data.get('username', '').strip()
    p = data.get('password', '').strip()
    # Admin credentials
    if u in USERS and USERS[u] == p:
        return jsonify(success=True, message='Login successful!', redirect='/admin')
    # Operator credentials
    for office, creds in OPERATOR_CREDS.items():
        if u == creds['username'] and p == creds['password']:
            slug = office.lower().replace(' ', '-')
            session['op_' + slug] = True
            return jsonify(success=True, message='Login successful!', redirect='/' + slug)
    return jsonify(success=False, message='Invalid credentials.'), 401

@app.route('/api/state')
def api_state():
    return jsonify(success=True, state=snapshot(), served=served_map(), recall=recall_map())

@app.route('/api/monitor/<slug>')
def api_monitor(slug):
    normalized = slug.lower().replace('-', ' ')
    office = next((k for k in offices_data if k.lower() == normalized), None)
    if not office:
        return jsonify(success=False, message='Office not found.'), 404
    od = offices_data[office]
    return jsonify(
        success=True,
        office=office,
        current=od['current'],
        next=next_ticket(office),
        served=od['served'],
        recall_count=od.get('recall_count', 0)
    )

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
    od['recall_count'] = od.get('recall_count', 0) + 1
    push_history('recall', office, od['current'])
    msg = (f"Recalling for number {od['current']}, please proceed to the {office.lower()} office."
           if od['current'] != '----'
           else f"No current ticket to recall at {office}.")
    return jsonify(success=True, message=msg, state=snapshot(), served=served_map(),
                   recall_count=od.get('recall_count', 0))

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
                          'prefix': prefix, 'priority': 0, 'recall_count': 0}
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