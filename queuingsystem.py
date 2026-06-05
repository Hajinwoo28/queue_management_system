from flask import Flask, render_template_string, jsonify, request
import threading

app = Flask(__name__)
_lock = threading.Lock()

# ─────────────────────────────────────────────────────────────────────────────
# DEPARTMENT CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
DEPT_CFG = {
    'cashier': {
        'label':  'CASHIER',
        'prefix': 'C',
        'icon':   '💰',
        'accent': '#1E90FF',
        'glow':   'rgba(30,144,255,0.4)',
        'dark':   '#06111f',
        'mid':    '#0a1d38',
    },
    'registrar': {
        'label':  'REGISTRAR',
        'prefix': 'R',
        'icon':   '📋',
        'accent': '#00C875',
        'glow':   'rgba(0,200,117,0.4)',
        'dark':   '#05120a',
        'mid':    '#081e0e',
    },
    'accounting': {
        'label':  'ACCOUNTING',
        'prefix': 'A',
        'icon':   '🧾',
        'accent': '#FFB300',
        'glow':   'rgba(255,179,0,0.4)',
        'dark':   '#140e00',
        'mid':    '#1e1500',
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# RUNTIME QUEUE STATE
# ─────────────────────────────────────────────────────────────────────────────
queues = {
    k: {**v, 'now_serving': None, 'queue': [], 'counter': 0}
    for k, v in DEPT_CFG.items()
}


def peek_next(dept: str) -> str:
    q = queues[dept]['queue']
    return q[0] if q else '---'


def get_serving(dept: str) -> str:
    return queues[dept]['now_serving'] or '---'


# ─────────────────────────────────────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/status')
def api_all_status():
    with _lock:
        return jsonify({
            dept: {
                'label':       q['label'],
                'accent':      q['accent'],
                'now_serving': get_serving(dept),
                'next_queue':  peek_next(dept),
                'queue_count': len(q['queue']),
            }
            for dept, q in queues.items()
        })


@app.route('/api/status/<dept>')
def api_dept_status(dept):
    if dept not in queues:
        return jsonify(error='Department not found'), 404
    with _lock:
        q = queues[dept]
        return jsonify(
            label=q['label'],
            accent=q['accent'],
            now_serving=get_serving(dept),
            next_queue=peek_next(dept),
            queue_count=len(q['queue']),
        )


@app.route('/api/call_next/<dept>', methods=['POST'])
def api_call_next(dept):
    if dept not in queues:
        return jsonify(success=False, error='Department not found'), 404
    with _lock:
        q = queues[dept]
        if not q['queue']:
            return jsonify(success=False, msg='Queue is empty')
        q['now_serving'] = q['queue'].pop(0)
        return jsonify(
            success=True,
            now_serving=q['now_serving'],
            next_queue=peek_next(dept),
            queue_count=len(q['queue']),
        )


@app.route('/api/issue/<dept>', methods=['POST'])
def api_issue(dept):
    if dept not in queues:
        return jsonify(success=False, error='Department not found'), 404
    with _lock:
        q = queues[dept]
        q['counter'] += 1
        ticket = f"{q['prefix']}-{q['counter']:03d}"
        q['queue'].append(ticket)
        return jsonify(
            success=True,
            ticket=ticket,
            position=len(q['queue']),
            dept=q['label'],
        )


@app.route('/api/reset/<dept>', methods=['POST'])
def api_reset(dept):
    if dept not in queues:
        return jsonify(success=False, error='Department not found'), 404
    with _lock:
        q = queues[dept]
        q['queue'].clear()
        q['now_serving'] = None
        q['counter'] = 0
        return jsonify(success=True, msg=f"{q['label']} queue cleared")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/monitor/<dept>')
def monitor(dept):
    if dept not in queues:
        return (f'Department "{dept}" not found. '
                f'Valid: cashier, registrar, accounting'), 404
    d = queues[dept]
    return render_template_string(
        MONITOR_TMPL,
        dept=dept,
        label=d['label'],
        accent=d['accent'],
        glow=d['glow'],
        dark=d['dark'],
        mid=d['mid'],
    )


@app.route('/admin')
def admin():
    return render_template_string(ADMIN_TMPL)


@app.route('/')
def dispenser():
    return render_template_string(DISPENSER_TMPL)


# ─────────────────────────────────────────────────────────────────────────────
# ██████████████████████  MONITOR TEMPLATE  ███████████████████████████████████
# Full-screen queue display for each department
# ─────────────────────────────────────────────────────────────────────────────
MONITOR_TMPL = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<title>{{ label }} – Queue Monitor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;700&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --accent: {{ accent }};
  --glow:   {{ glow }};
  --dark:   {{ dark }};
  --mid:    {{ mid }};
}

html, body {
  width: 100%; height: 100%;
  background: var(--dark);
  color: #fff;
  font-family: 'Outfit', sans-serif;
  overflow: hidden;
  user-select: none;
}

body {
  display: grid;
  grid-template-rows: auto 1fr auto;
}

/* ── Radial ambient glow background ─── */
body::after {
  content: '';
  position: fixed;
  inset: 0;
  background:
    radial-gradient(ellipse 70% 50% at 50% 50%, var(--mid) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

/* ── Scanline overlay ──────────────── */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,0.05) 2px,
    rgba(0,0,0,0.05) 4px
  );
  pointer-events: none;
  z-index: 200;
}

/* ── Department Header ─────────────── */
.hdr {
  position: relative;
  z-index: 10;
  background: var(--accent);
  color: #000;
  text-align: center;
  padding: 22px 0 20px;
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(2rem, 5.5vw, 4.5rem);
  letter-spacing: 0.35em;
  font-weight: 400;
}

.hdr::after {
  content: '';
  position: absolute;
  inset: auto 0 0 0;
  height: 5px;
  background: rgba(0,0,0,0.25);
}

/* ── Main content area ─────────────── */
.body {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-rows: 1fr auto 1fr;
  place-items: center;
  padding: 40px 24px;
}

/* ── Section (label + number) ──────── */
.sec {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.sec-lbl {
  font-size: clamp(1rem, 2.8vw, 2rem);
  font-weight: 300;
  letter-spacing: 0.5em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.4);
}

/* ── NOW SERVING number ────────────── */
#now-num {
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(6rem, 24vw, 20rem);
  letter-spacing: 0.06em;
  line-height: 0.88;
  color: var(--accent);
  text-shadow:
    0 0 40px var(--glow),
    0 0 80px var(--glow),
    0 0 140px var(--glow);
  font-variant-numeric: tabular-nums;
}

#now-num.pop {
  animation: pop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes pop {
  0%   { transform: scale(0.72); opacity: 0.15; filter: blur(4px); }
  60%  { transform: scale(1.05); filter: blur(0); }
  100% { transform: scale(1);   opacity: 1; }
}

/* ── Divider ───────────────────────── */
.div {
  width: 65%;
  max-width: 520px;
  height: 1px;
  background: linear-gradient(90deg,
    transparent, var(--accent) 30%, var(--accent) 70%, transparent);
  opacity: 0.3;
  position: relative;
}

.div::before {
  content: '';
  position: absolute;
  top: -2px; left: 50%; transform: translateX(-50%);
  width: 8px; height: 5px;
  background: var(--accent);
  border-radius: 50%;
  opacity: 0.8;
}

/* ── NEXT QUEUE number ─────────────── */
#next-num {
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(3rem, 10vw, 8rem);
  letter-spacing: 0.08em;
  line-height: 1;
  color: rgba(255,255,255,0.45);
  font-variant-numeric: tabular-nums;
  transition: all 0.35s ease;
}

#next-num.shift {
  animation: shift 0.35s ease forwards;
}
@keyframes shift {
  0%   { transform: translateY(8px); opacity: 0.2; }
  100% { transform: none; opacity: 1; }
}

/* ── Footer status bar ─────────────── */
.ftr {
  position: relative;
  z-index: 10;
  background: rgba(0,0,0,0.3);
  border-top: 1px solid rgba(255,255,255,0.05);
  padding: 14px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: clamp(0.78rem, 1.4vw, 1rem);
  color: rgba(255,255,255,0.3);
  letter-spacing: 0.1em;
  backdrop-filter: blur(10px);
}

.live {
  display: flex;
  align-items: center;
  gap: 9px;
  font-weight: 600;
  text-transform: uppercase;
}

.dot {
  width: 9px; height: 9px;
  border-radius: 50%;
  background: var(--accent);
  animation: blink 2s ease-in-out infinite;
  box-shadow: 0 0 8px var(--glow);
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.2; box-shadow: none; }
}

.wait-badge {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  padding: 4px 16px;
  font-size: 0.9em;
}

.clock {
  font-variant-numeric: tabular-nums;
}
</style>
</head>
<body>

<!-- Department Header -->
<header class="hdr">{{ label }}</header>

<!-- Main Monitor Content -->
<main class="body">

  <!-- NOW SERVING -->
  <div class="sec">
    <span class="sec-lbl">Now Serving</span>
    <div id="now-num">---</div>
  </div>

  <!-- Separator -->
  <div class="div"></div>

  <!-- NEXT QUEUE -->
  <div class="sec">
    <span class="sec-lbl">Next Queue</span>
    <div id="next-num">---</div>
  </div>

</main>

<!-- Status Bar -->
<footer class="ftr">
  <span class="live"><span class="dot"></span>LIVE</span>
  <span class="clock" id="clk">—</span>
  <span class="wait-badge">Waiting:&nbsp;<strong id="wcount">0</strong></span>
</footer>

<script>
const DEPT = '{{ dept }}';
let lastNow = null;
let lastNext = null;

/* ── Clock ─────────────────────────────────────────────── */
function tick() {
  const n = new Date();
  document.getElementById('clk').textContent =
    n.toLocaleTimeString('en-PH', {
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
}
tick();
setInterval(tick, 1000);

/* ── Audio chime (2-tone) ──────────────────────────────── */
function chime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    [880, 1320].forEach((freq, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = freq;
      osc.type = 'sine';
      const t = ctx.currentTime + i * 0.18;
      gain.gain.setValueAtTime(0, t);
      gain.gain.linearRampToValueAtTime(0.28, t + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.65);
      osc.start(t);
      osc.stop(t + 0.65);
    });
  } catch (e) { /* graceful fail */ }
}

/* ── Poll server every 2 seconds ───────────────────────── */
async function poll() {
  try {
    const res = await fetch(`/api/status/${DEPT}`, { cache: 'no-store' });
    if (!res.ok) return;
    const d = await res.json();

    const ne = document.getElementById('now-num');
    const nx = document.getElementById('next-num');
    const wc = document.getElementById('wcount');

    /* NOW SERVING changed → pop animation + chime */
    if (d.now_serving !== lastNow) {
      ne.classList.remove('pop');
      void ne.offsetWidth; /* force reflow */
      ne.classList.add('pop');
      if (lastNow !== null) chime();
      lastNow = d.now_serving;
    }

    /* NEXT QUEUE changed → slide-up animation */
    if (d.next_queue !== lastNext) {
      nx.classList.remove('shift');
      void nx.offsetWidth;
      nx.classList.add('shift');
      lastNext = d.next_queue;
    }

    ne.textContent = d.now_serving;
    nx.textContent = d.next_queue;
    wc.textContent = d.queue_count;
  } catch (e) {
    /* silently retry on next interval */
  }
}

poll();
setInterval(poll, 2000);
</script>

</body>
</html>'''


# ─────────────────────────────────────────────────────────────────────────────
# █████████████████████  ADMIN TEMPLATE  ██████████████████████████████████████
# Staff control panel — call next, view queues, reset
# ─────────────────────────────────────────────────────────────────────────────
ADMIN_TMPL = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Queue Admin Panel</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700;900&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Outfit', sans-serif;
  background: #08081a;
  color: #fff;
  min-height: 100vh;
}

/* ── Navbar ─────────────────────────── */
nav {
  background: #0e0e22;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  padding: 15px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 14px;
  position: sticky;
  top: 0;
  z-index: 50;
  backdrop-filter: blur(12px);
}

.brand {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.55rem;
  letter-spacing: 0.2em;
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-dim { opacity: 0.35; }

.nav-links {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.nl {
  padding: 6px 15px;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border: 1px solid transparent;
  transition: all 0.2s;
}
.nl:hover { opacity: 0.75; transform: translateY(-1px); }

.nl-c { color: #1E90FF; border-color: rgba(30,144,255,0.3); background: rgba(30,144,255,0.08); }
.nl-r { color: #00C875; border-color: rgba(0,200,117,0.3); background: rgba(0,200,117,0.08); }
.nl-a { color: #FFB300; border-color: rgba(255,179,0,0.3);  background: rgba(255,179,0,0.08);  }
.nl-d { color: #aaa;    border-color: rgba(170,170,170,0.2); background: rgba(255,255,255,0.04); }

/* ── Main ───────────────────────────── */
.main { padding: 28px 28px 60px; }

.pg-hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
  flex-wrap: wrap;
  gap: 10px;
}

.pg-title {
  font-size: 0.72rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.28);
}

.refresh-note {
  font-size: 0.72rem;
  color: rgba(255,255,255,0.2);
  letter-spacing: 0.08em;
  display: flex;
  align-items: center;
  gap: 6px;
}
.rdot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #00C875;
  animation: blink2 2s ease-in-out infinite;
}
@keyframes blink2 { 0%,100%{opacity:1}50%{opacity:0.2} }

/* ── Cards Grid ─────────────────────── */
.cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
@media (max-width: 960px) { .cards { grid-template-columns: 1fr; } }

.card {
  background: #0e0e24;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.05);
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.25s;
}
.card:hover {
  border-color: rgba(255,255,255,0.1);
  box-shadow: 0 6px 32px rgba(0,0,0,0.45);
}

.card-hdr {
  padding: 16px 22px;
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.7rem;
  letter-spacing: 0.22em;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-body { padding: 22px; }

/* ── Stats ──────────────────────────── */
.stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 12px;
}

.stat {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: 10px;
  padding: 14px 12px;
  text-align: center;
}

.s-lbl {
  font-size: 0.63rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.32);
  margin-bottom: 7px;
}

.s-val {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 2.4rem;
  letter-spacing: 0.05em;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  transition: all 0.3s ease;
}

.wait-row {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: 8px;
  padding: 11px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
  font-size: 0.85rem;
  color: rgba(255,255,255,0.42);
}

.wait-row .wnum {
  font-weight: 700;
  font-size: 1.05rem;
  color: #fff;
}

/* ── Action Buttons ─────────────────── */
.btns { display: flex; gap: 9px; }

.btn {
  flex: 1;
  padding: 13px 10px;
  border: none;
  border-radius: 9px;
  font-family: 'Outfit', sans-serif;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.15s;
  outline: none;
}
.btn:hover { transform: translateY(-2px); filter: brightness(1.12); }
.btn:active { transform: translateY(0); filter: brightness(0.95); }

.btn-primary { color: #000; flex: 2; }

.btn-reset {
  background: rgba(255,60,60,0.07);
  border: 1px solid rgba(255,60,60,0.22);
  color: #ff5252;
}
.btn-reset:hover { background: rgba(255,60,60,0.15); }

/* ── Toast Notifications ───────────── */
#toasts {
  position: fixed;
  top: 20px; right: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 999;
  pointer-events: none;
}

.toast {
  background: #141430;
  border-left: 3px solid #00C875;
  border-radius: 9px;
  padding: 13px 20px;
  font-size: 0.88rem;
  max-width: 320px;
  animation: tin 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: auto;
  box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}
.toast.err  { border-left-color: #ff5252; }
.toast.out  { animation: tout 0.3s ease forwards; }

@keyframes tin  { from { transform: translateX(110%); opacity: 0; } to { transform: none; opacity: 1; } }
@keyframes tout { from { opacity: 1; } to { opacity: 0; transform: translateX(10%); } }

/* ── Footer ─────────────────────────── */
footer {
  text-align: center;
  padding: 20px;
  font-size: 0.72rem;
  color: rgba(255,255,255,0.16);
  letter-spacing: 0.15em;
  text-transform: uppercase;
}
</style>
</head>
<body>

<!-- Navbar -->
<nav>
  <div class="brand">
    <span>🎫</span>
    <span>Queue Management</span>
    <span class="brand-dim">System</span>
  </div>
  <div class="nav-links">
    <a href="/monitor/cashier"    class="nl nl-c" target="_blank">💰 Cashier Monitor</a>
    <a href="/monitor/registrar"  class="nl nl-r" target="_blank">📋 Registrar Monitor</a>
    <a href="/monitor/accounting" class="nl nl-a" target="_blank">🧾 Accounting Monitor</a>
    <a href="/"                   class="nl nl-d" target="_blank">🎟 Ticket Dispenser</a>
  </div>
</nav>

<!-- Main Content -->
<main class="main">
  <div class="pg-hdr">
    <div class="pg-title">Department Queue Control</div>
    <div class="refresh-note">
      <span class="rdot"></span>
      Live &mdash; updates every 2s
      &nbsp;&nbsp;|&nbsp;&nbsp;
      Last sync: <span id="ts">—</span>
    </div>
  </div>

  <div class="cards" id="cards"></div>
</main>

<footer>Queue Management System &nbsp;·&nbsp; Admin Panel</footer>

<div id="toasts"></div>

<script>
const CFG = {
  cashier:    { label: 'CASHIER',    icon: '💰', accent: '#1E90FF', bg: 'rgba(30,144,255,0.1)',  bdr: 'rgba(30,144,255,0.25)'  },
  registrar:  { label: 'REGISTRAR',  icon: '📋', accent: '#00C875', bg: 'rgba(0,200,117,0.1)',   bdr: 'rgba(0,200,117,0.25)'   },
  accounting: { label: 'ACCOUNTING', icon: '🧾', accent: '#FFB300', bg: 'rgba(255,179,0,0.1)',   bdr: 'rgba(255,179,0,0.25)'   },
};

/* ── Toast helper ──────────────────────────────────── */
function toast(msg, err = false) {
  const tc = document.getElementById('toasts');
  const t = document.createElement('div');
  t.className = 'toast' + (err ? ' err' : '');
  t.textContent = msg;
  tc.appendChild(t);
  setTimeout(() => {
    t.classList.add('out');
    setTimeout(() => t.remove(), 300);
  }, 3400);
}

/* ── API: Call next ticket ─────────────────────────── */
async function callNext(dept) {
  try {
    const res = await fetch(`/api/call_next/${dept}`, { method: 'POST' });
    const d = await res.json();
    if (d.success) {
      toast(`${CFG[dept].label}: Now Serving ${d.now_serving}`);
    } else {
      toast(`${CFG[dept].label}: ${d.msg || 'Queue is empty'}`, true);
    }
    refresh();
  } catch (e) {
    toast('Connection error', true);
  }
}

/* ── API: Reset queue ──────────────────────────────── */
async function resetQueue(dept) {
  if (!confirm(`Reset ${CFG[dept].label} queue?\nThis will clear all tickets and cannot be undone.`)) return;
  try {
    await fetch(`/api/reset/${dept}`, { method: 'POST' });
    toast(`${CFG[dept].label} queue has been reset`);
    refresh();
  } catch (e) {
    toast('Connection error', true);
  }
}

/* ── Build department cards ────────────────────────── */
function buildCards(data) {
  const container = document.getElementById('cards');
  container.innerHTML = '';

  Object.entries(CFG).forEach(([dept, cfg]) => {
    const info = data[dept] || {};
    const ns = info.now_serving || '---';
    const nq = info.next_queue  || '---';
    const wc = info.queue_count ?? 0;

    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <div class="card-hdr"
           style="background:${cfg.bg};color:${cfg.accent};border-bottom-color:${cfg.bdr}">
        <span>${cfg.icon}</span> ${cfg.label}
      </div>
      <div class="card-body">
        <div class="stats">
          <div class="stat">
            <div class="s-lbl">Now Serving</div>
            <div class="s-val" style="color:${cfg.accent}" id="ns-${dept}">${ns}</div>
          </div>
          <div class="stat">
            <div class="s-lbl">Next Queue</div>
            <div class="s-val" style="color:rgba(255,255,255,0.55)" id="nq-${dept}">${nq}</div>
          </div>
        </div>
        <div class="wait-row">
          <span>Currently Waiting</span>
          <span class="wnum" id="wc-${dept}">${wc} ticket${wc !== 1 ? 's' : ''}</span>
        </div>
        <div class="btns">
          <button class="btn btn-primary"
                  style="background:${cfg.accent}"
                  onclick="callNext('${dept}')">
            ▶&nbsp; Call Next
          </button>
          <button class="btn btn-reset" onclick="resetQueue('${dept}')">
            Reset
          </button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

/* ── Soft-update (no full rebuild) ─────────────────── */
function softUpdate(data) {
  /* Try to update in-place first to avoid flicker */
  const missing = Object.keys(CFG).some(dept =>
    !document.getElementById(`ns-${dept}`)
  );
  if (missing) { buildCards(data); return; }

  Object.entries(CFG).forEach(([dept]) => {
    const info = data[dept] || {};
    const ns = info.now_serving || '---';
    const nq = info.next_queue  || '---';
    const wc = info.queue_count ?? 0;

    document.getElementById(`ns-${dept}`).textContent = ns;
    document.getElementById(`nq-${dept}`).textContent = nq;
    document.getElementById(`wc-${dept}`).textContent = `${wc} ticket${wc !== 1 ? 's' : ''}`;
  });
}

/* ── Refresh from API ──────────────────────────────── */
let firstLoad = true;
async function refresh() {
  try {
    const res = await fetch('/api/status', { cache: 'no-store' });
    if (!res.ok) return;
    const data = await res.json();
    if (firstLoad) { buildCards(data); firstLoad = false; }
    else { softUpdate(data); }
    document.getElementById('ts').textContent =
      new Date().toLocaleTimeString('en-PH');
  } catch (e) {
    console.error('Refresh error:', e);
  }
}

refresh();
setInterval(refresh, 2000);
</script>

</body>
</html>'''


# ─────────────────────────────────────────────────────────────────────────────
# █████████████████████  DISPENSER TEMPLATE  ██████████████████████████████████
# Customer-facing kiosk to issue queue tickets
# ─────────────────────────────────────────────────────────────────────────────
DISPENSER_TMPL = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Queue Ticket System</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700;900&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Outfit', sans-serif;
  background: #08081a;
  color: #fff;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* ── Ambient background ─────────────── */
body::before {
  content: '';
  position: fixed; inset: 0;
  background:
    radial-gradient(ellipse 60% 40% at 20% 20%, rgba(30,144,255,0.06) 0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 80% 80%, rgba(0,200,117,0.05) 0%, transparent 60%);
  pointer-events: none;
}

/* ── Hero ───────────────────────────── */
.hero {
  text-align: center;
  padding: 56px 20px 36px;
  position: relative;
  z-index: 1;
}

.hero-icon { font-size: 3.5rem; margin-bottom: 14px; }

.hero-title {
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(2.5rem, 7vw, 5rem);
  letter-spacing: 0.25em;
  line-height: 1;
}

.hero-sub {
  margin-top: 10px;
  font-size: clamp(0.85rem, 2vw, 1rem);
  color: rgba(255,255,255,0.38);
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

/* ── Department Grid ─────────────────── */
.dept-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
  max-width: 860px;
  width: 100%;
  padding: 0 24px;
  position: relative;
  z-index: 1;
}
@media (max-width: 680px) { .dept-grid { grid-template-columns: 1fr; } }

/* ── Department Button ─────────────── */
.dept-btn {
  border: 2px solid transparent;
  border-radius: 18px;
  padding: 38px 22px 30px;
  cursor: pointer;
  font-family: 'Outfit', sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  transition: all 0.22s;
  position: relative;
  overflow: hidden;
}

.dept-btn::after {
  content: '';
  position: absolute; inset: 0;
  background: rgba(255,255,255,0);
  transition: background 0.2s;
  border-radius: inherit;
}
.dept-btn:hover { transform: translateY(-6px); box-shadow: 0 16px 48px rgba(0,0,0,0.5); }
.dept-btn:hover::after { background: rgba(255,255,255,0.06); }
.dept-btn:active { transform: translateY(-2px); }

.dept-btn:disabled {
  opacity: 0.5;
  cursor: wait;
  transform: none;
}

.dept-icon { font-size: 2.8rem; }

.dept-name {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 2rem;
  letter-spacing: 0.22em;
}

.dept-wait {
  font-size: 0.78rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.6;
  margin-top: 4px;
}

/* ── Ticket Modal ───────────────────── */
.modal-wrap {
  display: none;
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.78);
  backdrop-filter: blur(8px);
  z-index: 100;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-wrap.show { display: flex; }

.ticket-card {
  background: #0e0e26;
  border-radius: 20px;
  width: 100%;
  max-width: 420px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.07);
  animation: rise 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 24px 80px rgba(0,0,0,0.6);
}

@keyframes rise {
  from { transform: scale(0.78) translateY(24px); opacity: 0; }
  to   { transform: none; opacity: 1; }
}

/* Ticket header */
.t-hdr {
  padding: 20px 24px;
  text-align: center;
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.6rem;
  letter-spacing: 0.3em;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

/* Perforation separator */
.t-perf {
  height: 1px;
  background: repeating-linear-gradient(
    90deg, transparent, transparent 8px,
    rgba(255,255,255,0.14) 8px, rgba(255,255,255,0.14) 10px
  );
  margin: 0 -1px;
}

/* Ticket body */
.t-body {
  padding: 32px 24px 28px;
  text-align: center;
}

.t-dept {
  font-size: 0.72rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.38);
  margin-bottom: 8px;
}

.t-num {
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(4.5rem, 18vw, 7.5rem);
  letter-spacing: 0.1em;
  line-height: 1;
  margin-bottom: 16px;
}

.t-pos {
  font-size: 0.92rem;
  color: rgba(255,255,255,0.48);
}
.t-pos strong { color: #fff; }

/* Ticket footer */
.t-ftr {
  padding: 18px 22px;
  display: flex;
  gap: 10px;
  border-top: 1px solid rgba(255,255,255,0.05);
}

.t-btn {
  flex: 1;
  padding: 13px;
  border-radius: 9px;
  border: none;
  cursor: pointer;
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  font-size: 0.88rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  transition: all 0.15s;
}
.t-btn:hover { filter: brightness(1.1); transform: translateY(-1px); }
.t-btn:active { transform: none; }

.t-close {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  color: #fff;
}

.t-print { color: #000; }

/* ── Admin bar ──────────────────────── */
.admin-bar {
  margin-top: auto;
  padding: 40px 20px 24px;
  text-align: center;
  position: relative;
  z-index: 1;
}
.admin-bar a {
  color: rgba(255,255,255,0.18);
  text-decoration: none;
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  transition: color 0.2s;
}
.admin-bar a:hover { color: rgba(255,255,255,0.48); }
</style>
</head>
<body>

<!-- Hero -->
<div class="hero">
  <div class="hero-icon">🎫</div>
  <div class="hero-title">Queue Ticket System</div>
  <div class="hero-sub">Please select your department to receive a number</div>
</div>

<!-- Department Buttons -->
<div class="dept-grid">
  <button class="dept-btn" id="btn-cashier" onclick="getTicket('cashier')"
          style="background:rgba(30,144,255,0.1);border-color:rgba(30,144,255,0.35)">
    <span class="dept-icon">💰</span>
    <span class="dept-name" style="color:#1E90FF">Cashier</span>
    <span class="dept-wait" id="wait-cashier">Loading…</span>
  </button>

  <button class="dept-btn" id="btn-registrar" onclick="getTicket('registrar')"
          style="background:rgba(0,200,117,0.1);border-color:rgba(0,200,117,0.35)">
    <span class="dept-icon">📋</span>
    <span class="dept-name" style="color:#00C875">Registrar</span>
    <span class="dept-wait" id="wait-registrar">Loading…</span>
  </button>

  <button class="dept-btn" id="btn-accounting" onclick="getTicket('accounting')"
          style="background:rgba(255,179,0,0.1);border-color:rgba(255,179,0,0.35)">
    <span class="dept-icon">🧾</span>
    <span class="dept-name" style="color:#FFB300">Accounting</span>
    <span class="dept-wait" id="wait-accounting">Loading…</span>
  </button>
</div>

<!-- Ticket Modal -->
<div class="modal-wrap" id="modal">
  <div class="ticket-card" id="ticket-card">
    <div class="t-hdr" id="t-hdr">DEPARTMENT</div>
    <div class="t-perf"></div>
    <div class="t-body">
      <div class="t-dept" id="t-dept">DEPARTMENT</div>
      <div class="t-num"  id="t-num">---</div>
      <div class="t-pos"  id="t-pos">You are <strong>1st</strong> in queue</div>
    </div>
    <div class="t-ftr">
      <button class="t-btn t-close" onclick="closeModal()">✕ Close</button>
      <button class="t-btn t-print" id="t-print-btn" onclick="printTicket()">🖨 Print</button>
    </div>
  </div>
</div>

<!-- Admin link -->
<div class="admin-bar">
  <a href="/admin">Staff Admin Panel</a>
</div>

<script>
const ACCENT = {
  cashier:    '#1E90FF',
  registrar:  '#00C875',
  accounting: '#FFB300',
};

let currentTicket = null;

/* ── Ordinal suffix ─────────────────────────────────── */
function ord(n) {
  const s = ['th','st','nd','rd'], v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

/* ── Load queue wait counts ─────────────────────────── */
async function loadCounts() {
  try {
    const res = await fetch('/api/status', { cache: 'no-store' });
    const d = await res.json();
    Object.keys(ACCENT).forEach(dept => {
      const el = document.getElementById(`wait-${dept}`);
      if (el && d[dept]) {
        const n = d[dept].queue_count;
        el.textContent = n === 0 ? 'No wait' : `${n} waiting`;
      }
    });
  } catch (e) {}
}

loadCounts();
setInterval(loadCounts, 5000);

/* ── Issue ticket ───────────────────────────────────── */
async function getTicket(dept) {
  const btn = document.getElementById(`btn-${dept}`);
  btn.disabled = true;
  try {
    const res = await fetch(`/api/issue/${dept}`, { method: 'POST' });
    const d = await res.json();
    if (!d.success) { alert('Error issuing ticket. Please try again.'); return; }
    showTicket(dept, d);
    loadCounts();
  } catch (e) {
    alert('Connection error. Please try again.');
  } finally {
    btn.disabled = false;
  }
}

/* ── Show ticket modal ──────────────────────────────── */
function showTicket(dept, d) {
  const acc = ACCENT[dept];
  currentTicket = { ...d, dept, acc, time: new Date().toLocaleString('en-PH') };

  document.getElementById('t-hdr').textContent = d.dept;
  document.getElementById('t-hdr').style.background = acc + '20';
  document.getElementById('t-hdr').style.color = acc;
  document.getElementById('t-dept').textContent = d.dept + ' DEPARTMENT';
  document.getElementById('t-num').textContent = d.ticket;
  document.getElementById('t-num').style.color = acc;
  document.getElementById('t-pos').innerHTML =
    `You are <strong>${ord(d.position)}</strong> in queue`;
  document.getElementById('t-print-btn').style.background = acc;

  document.getElementById('modal').classList.add('show');
}

function closeModal() {
  document.getElementById('modal').classList.remove('show');
}

/* Close modal on backdrop click */
document.getElementById('modal').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

/* ── Print ticket ───────────────────────────────────── */
function printTicket() {
  if (!currentTicket) return;
  const t = currentTicket;
  const w = window.open('', '_blank', 'width=380,height=520');
  w.document.write(`
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Queue Ticket — ${t.ticket}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #fff; color: #000;
      padding: 40px 32px;
      text-align: center;
    }
    .lbl { font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: #666; }
    .num { font-size: 90px; font-weight: 900; color: ${t.acc}; margin: 16px 0 12px; line-height: 1; }
    hr   { border: none; border-top: 1px dashed #ccc; margin: 18px 0; }
    .sm  { font-size: 12px; color: #777; margin: 6px 0; letter-spacing: 1px; }
  </style>
</head>
<body>
  <div class="lbl">${t.dept} Department</div>
  <div class="lbl" style="margin-top:4px">Queue Number</div>
  <div class="num">${t.ticket}</div>
  <hr>
  <div class="sm">Position: ${ord(t.position)} in queue</div>
  <div class="sm">Issued: ${t.time}</div>
  <hr>
  <div class="sm">Please wait for your number to be called.</div>
  <div class="sm">Thank you for your patience.</div>
  <script>
    window.onload = function() {
      window.print();
      setTimeout(function() { window.close(); }, 1200);
    };
  <\/script>
</body>
</html>
  `);
  w.document.close();
}
</script>

</body>
</html>'''


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('\n  Queue Management System')
    print('  ─────────────────────────────────────────────')
    print('  Ticket Dispenser  → http://localhost:5000/')
    print('  Admin Panel       → http://localhost:5000/admin')
    print('  Cashier Monitor   → http://localhost:5000/monitor/cashier')
    print('  Registrar Monitor → http://localhost:5000/monitor/registrar')
    print('  Accounting Monitor→ http://localhost:5000/monitor/accounting')
    print('  ─────────────────────────────────────────────\n')
    app.run(debug=True, host='0.0.0.0', port=5000)