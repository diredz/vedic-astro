#!/usr/bin/env python3
"""
🪐 Jyotish GUI — Flask web interface for the Vedic Astrology CLI
Run: python gui.py   → opens at http://localhost:5050
"""
import sys, os, re, subprocess, json, threading, requests, io
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

app = Flask(__name__)

ANSI_RE = re.compile(r'\x1b\[[0-9;]*[mGKHF]|\x1b\][^\x07]*\x07|\x1b[@-Z\\-_]|\[[\x30-\x3f]*[\x20-\x2f]*[\x40-\x7e]')

def strip_ansi(text: str) -> str:
    return ANSI_RE.sub('', text)

def run_cmd(args: list[str], env_override: dict = None) -> str:
    env = os.environ.copy()
    env["TERM"] = "dumb"
    env["NO_COLOR"] = "1"
    env["FORCE_COLOR"] = "0"
    if env_override:
        env.update(env_override)
    try:
        result = subprocess.run(
            [sys.executable, "main.py"] + args,
            cwd=str(BASE_DIR),
            capture_output=True, text=True, env=env, timeout=180
        )
        out = strip_ansi(result.stdout + result.stderr)
        return out.strip()
    except subprocess.TimeoutExpired:
        return "⏱ Command timed out (180s). LLM may still be processing."
    except Exception as e:
        return f"Error: {e}"

def get_ollama_models() -> list[str]:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        data = r.json()
        return [m["name"] for m in data.get("models", [])]
    except:
        return ["qwen2.5:7b", "llama3.1:8b", "mistral:7b"]

def get_profiles() -> list[dict]:
    try:
        from data.db import list_profiles, init_db
        init_db()
        rows = list_profiles()
        return [{"name": r[0], "city": r[1] or "", "dob": r[2]} for r in rows]
    except Exception as e:
        return []


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🪐 Jyotish</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Crimson+Pro:ital,wght@0,300;0,400;1,300&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#060a12;--bg2:#0c1220;--bg3:#111a2e;
  --gold:#c8a84b;--gold2:#f0d080;--gold3:#8a6d28;
  --text:#d4c9b0;--text2:#8a7e6a;--text3:#4a4030;
  --accent:#4a9eff;--purple:#8b5cf6;--green:#34d399;--red:#f87171;
  --border:rgba(200,168,75,0.15);--border2:rgba(200,168,75,0.3);
  --radius:8px;--font-head:'Cinzel',serif;--font-body:'Crimson Pro',serif;
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--font-body);font-size:16px;overflow:hidden}

/* Layout */
.layout{display:grid;grid-template-columns:280px 1fr;grid-template-rows:56px 1fr;height:100vh}
.topbar{grid-column:1/-1;display:flex;align-items:center;padding:0 20px;gap:16px;
  background:var(--bg2);border-bottom:1px solid var(--border);
  font-family:var(--font-head);letter-spacing:.08em}
.topbar .logo{font-size:18px;color:var(--gold2);font-weight:700;display:flex;align-items:center;gap:8px}
.topbar .subtitle{font-size:11px;color:var(--text2);font-family:var(--font-body);font-weight:300;letter-spacing:.04em}
.model-wrap{margin-left:auto;display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text2)}
.model-wrap select{background:var(--bg3);border:1px solid var(--border2);color:var(--gold);
  padding:4px 10px;border-radius:var(--radius);font-size:13px;font-family:var(--font-body);cursor:pointer}
.model-wrap select:focus{outline:none;border-color:var(--gold)}
.use-llm{display:flex;align-items:center;gap:6px;cursor:pointer;font-size:13px;color:var(--text2)}
.use-llm input{accent-color:var(--gold);width:14px;height:14px;cursor:pointer}

/* Sidebar */
.sidebar{background:var(--bg2);border-right:1px solid var(--border);overflow-y:auto;display:flex;flex-direction:column}
.sidebar-section{padding:14px 16px;border-bottom:1px solid var(--border)}
.sidebar-title{font-family:var(--font-head);font-size:10px;letter-spacing:.15em;color:var(--gold3);
  text-transform:uppercase;margin-bottom:10px}
.profile-card{padding:8px 10px;border-radius:var(--radius);cursor:pointer;
  border:1px solid transparent;transition:.15s;margin-bottom:4px;display:flex;align-items:center;gap:8px}
.profile-card:hover{background:var(--bg3);border-color:var(--border)}
.profile-card.active{background:rgba(200,168,75,.08);border-color:var(--border2)}
.profile-card .name{font-size:15px;color:var(--text);font-weight:400}
.profile-card .meta{font-size:11px;color:var(--text2)}
.profile-avatar{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,var(--bg3),var(--bg));
  border:1px solid var(--border2);display:flex;align-items:center;justify-content:center;
  font-size:13px;flex-shrink:0;color:var(--gold)}
.no-profiles{font-size:13px;color:var(--text3);font-style:italic;padding:4px 0}

/* Add profile form */
.form-field{margin-bottom:8px}
.form-field label{display:block;font-size:11px;color:var(--text2);margin-bottom:3px;letter-spacing:.04em}
.form-field input,.form-field select{width:100%;background:var(--bg);border:1px solid var(--border2);
  color:var(--text);padding:6px 8px;border-radius:var(--radius);font-size:13px;font-family:var(--font-body)}
.form-field input:focus,.form-field select:focus{outline:none;border-color:var(--gold)}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.btn{padding:7px 14px;border-radius:var(--radius);border:none;cursor:pointer;
  font-family:var(--font-head);font-size:11px;letter-spacing:.08em;transition:.15s;font-weight:600}
.btn-gold{background:linear-gradient(135deg,var(--gold3),var(--gold));color:#0a0a0a}
.btn-gold:hover{background:linear-gradient(135deg,var(--gold),var(--gold2));transform:translateY(-1px)}
.btn-outline{background:transparent;border:1px solid var(--border2);color:var(--gold)}
.btn-outline:hover{border-color:var(--gold);background:rgba(200,168,75,.06)}
.btn:disabled{opacity:.4;cursor:not-allowed;transform:none}

/* Main panel */
.main{display:flex;flex-direction:column;overflow:hidden}
.commands-bar{padding:14px 20px;border-bottom:1px solid var(--border);
  display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.cmd-btn{padding:8px 18px;border-radius:var(--radius);border:1px solid var(--border2);
  background:var(--bg2);color:var(--text);cursor:pointer;font-family:var(--font-head);
  font-size:11px;letter-spacing:.1em;transition:.15s;position:relative}
.cmd-btn:hover{border-color:var(--gold);color:var(--gold);background:rgba(200,168,75,.05)}
.cmd-btn.active-cmd{border-color:var(--gold);color:var(--gold2);background:rgba(200,168,75,.1)}
.cmd-btn.running{opacity:.6;cursor:not-allowed}
.cmd-icon{margin-right:5px}

/* Match selector */
.match-row{display:flex;align-items:center;gap:8px;padding:8px 20px;
  border-bottom:1px solid var(--border);background:rgba(139,92,246,.04)}
.match-row label{font-size:12px;color:var(--text2);font-family:var(--font-head);letter-spacing:.06em}
.match-row select{background:var(--bg3);border:1px solid var(--border2);color:var(--gold);
  padding:4px 8px;border-radius:var(--radius);font-size:13px;font-family:var(--font-body)}
.match-row.hidden{display:none}

/* Output */
.output-area{flex:1;overflow:hidden;display:flex;flex-direction:column}
.output-header{padding:8px 20px;display:flex;align-items:center;justify-content:space-between;
  border-bottom:1px solid var(--border);background:var(--bg2)}
.output-label{font-family:var(--font-head);font-size:10px;letter-spacing:.15em;color:var(--text2);text-transform:uppercase}
.output-actions{display:flex;gap:8px}
.output-scroll{flex:1;overflow-y:auto;padding:16px 20px;font-family:'Courier New',monospace;
  font-size:13px;line-height:1.7;white-space:pre-wrap;word-break:break-word;color:#b8d4a8}
.output-scroll::-webkit-scrollbar{width:4px}
.output-scroll::-webkit-scrollbar-track{background:transparent}
.output-scroll::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}
.output-placeholder{color:var(--text3);font-family:var(--font-body);font-style:italic;font-size:15px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:8px;text-align:center}
.output-placeholder .big{font-size:36px}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid var(--border2);
  border-top-color:var(--gold);border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle;margin-right:6px}
@keyframes spin{to{transform:rotate(360deg)}}
.status-bar{padding:4px 20px;background:var(--bg2);border-top:1px solid var(--border);
  font-size:11px;color:var(--text3);font-family:var(--font-head);letter-spacing:.06em;display:flex;gap:16px}
.status-dot{width:6px;height:6px;border-radius:50%;background:var(--text3);display:inline-block;margin-right:4px}
.status-dot.ok{background:var(--green)}
.status-dot.err{background:var(--red)}

/* Stars bg */
.stars{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;opacity:.3}
.layout{position:relative;z-index:1}

/* Scroll */
.sidebar::-webkit-scrollbar{width:3px}
.sidebar::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}

/* Toggle add form */
.collapsible{overflow:hidden;max-height:0;transition:max-height .3s ease}
.collapsible.open{max-height:600px}

/* Tag pills */
.tag{display:inline-block;padding:1px 7px;border-radius:20px;font-size:10px;
  font-family:var(--font-head);letter-spacing:.06em;margin-left:4px}
.tag-gold{background:rgba(200,168,75,.15);color:var(--gold);border:1px solid var(--gold3)}
</style>
</head>
<body>

<canvas class="stars" id="stars"></canvas>

<div class="layout">
  <!-- Topbar -->
  <div class="topbar">
    <div class="logo">
      <span>🪐</span>
      <span>JYOTISH</span>
    </div>
    <div class="subtitle">Vedic Astrology Engine · Local</div>
    <div class="model-wrap">
      <span>Model</span>
      <select id="modelSelect" onchange="setModel(this.value)">
        <option value="loading">Loading…</option>
      </select>
      <label class="use-llm">
        <input type="checkbox" id="useLLM" checked>
        Use LLM
      </label>
    </div>
  </div>

  <!-- Sidebar -->
  <div class="sidebar">
    <!-- Profiles list -->
    <div class="sidebar-section">
      <div class="sidebar-title">Profiles</div>
      <div id="profileList"><div class="no-profiles">No profiles yet</div></div>
    </div>

    <!-- Add profile -->
    <div class="sidebar-section">
      <div style="display:flex;justify-content:space-between;align-items:center;cursor:pointer"
           onclick="toggleAddForm()" id="addToggle">
        <div class="sidebar-title" style="margin:0">Add Profile</div>
        <span id="addArrow" style="color:var(--gold);font-size:12px">▶</span>
      </div>
      <div class="collapsible" id="addForm">
        <div style="height:10px"></div>
        <div class="form-field">
          <label>Name</label>
          <input type="text" id="f_name" placeholder="Diwakar">
        </div>
        <div class="form-row">
          <div class="form-field">
            <label>Date of Birth</label>
            <input type="date" id="f_dob">
          </div>
          <div class="form-field">
            <label>Time (24h)</label>
            <input type="time" id="f_tob" placeholder="06:30">
          </div>
        </div>
        <div class="form-field">
          <label>City</label>
          <input type="text" id="f_city" placeholder="Hyderabad">
        </div>
        <div class="form-row">
          <div class="form-field">
            <label>Latitude</label>
            <input type="number" id="f_lat" step="0.01" placeholder="17.38">
          </div>
          <div class="form-field">
            <label>Longitude</label>
            <input type="number" id="f_lon" step="0.01" placeholder="78.49">
          </div>
        </div>
        <div class="form-field">
          <label>Timezone</label>
          <input type="text" id="f_tz" value="Asia/Kolkata" placeholder="Asia/Kolkata">
        </div>
        <div style="margin-top:10px;display:flex;gap:6px">
          <button class="btn btn-gold" onclick="saveProfile()" style="flex:1">Save Profile</button>
        </div>
        <div id="addMsg" style="font-size:12px;margin-top:6px;min-height:16px"></div>
      </div>
    </div>

    <!-- Quick ref -->
    <div class="sidebar-section" style="flex:1">
      <div class="sidebar-title">Common Coordinates</div>
      <div style="font-size:11px;color:var(--text2);line-height:2">
        <div onclick="fillCoords(17.38,78.49,'Asia/Kolkata')" style="cursor:pointer;hover:color:var(--gold)">📍 Hyderabad 17.38, 78.49</div>
        <div onclick="fillCoords(19.08,72.88,'Asia/Kolkata')" style="cursor:pointer">📍 Mumbai 19.08, 72.88</div>
        <div onclick="fillCoords(28.63,77.22,'Asia/Kolkata')" style="cursor:pointer">📍 Delhi 28.63, 77.22</div>
        <div onclick="fillCoords(12.97,77.60,'Asia/Kolkata')" style="cursor:pointer">📍 Bangalore 12.97, 77.60</div>
        <div onclick="fillCoords(48.76,11.42,'Europe/Berlin')" style="cursor:pointer">📍 Ingolstadt 48.76, 11.42</div>
        <div onclick="fillCoords(48.13,11.58,'Europe/Berlin')" style="cursor:pointer">📍 Munich 48.13, 11.58</div>
      </div>
    </div>
  </div>

  <!-- Main -->
  <div class="main">
    <!-- Command buttons -->
    <div class="commands-bar">
      <button class="cmd-btn" id="cmd-chart"   onclick="runCmd('chart')"  title="Full birth chart with planetary positions">
        <span class="cmd-icon">🗺</span>KUNDALI
      </button>
      <button class="cmd-btn" id="cmd-dasha"   onclick="runCmd('dasha')"  title="Vimshottari Dasha timeline">
        <span class="cmd-icon">⏳</span>DASHA
      </button>
      <button class="cmd-btn" id="cmd-transit" onclick="runCmd('transit')" title="Current planetary transits">
        <span class="cmd-icon">🌙</span>TRANSIT
      </button>
      <button class="cmd-btn" id="cmd-yoga"    onclick="runCmd('yoga')"   title="Yoga and Dosha analysis">
        <span class="cmd-icon">☯</span>YOGA
      </button>
      <button class="cmd-btn" id="cmd-match"   onclick="runCmd('match')"  title="Kundali compatibility matching">
        <span class="cmd-icon">💑</span>MATCH
      </button>
      <button class="cmd-btn" id="cmd-western" onclick="runCmd('western')" title="Western tropical chart" style="border-color:rgba(100,180,255,0.4);color:#6ab4ff">
        <span class="cmd-icon">♈</span>WESTERN
      </button>
      <button class="cmd-btn" id="cmd-export" onclick="exportPDF()" title="Export full profile as PDF" style="margin-left:auto;border-color:rgba(200,168,75,0.4);color:var(--gold)">
        <span class="cmd-icon">📄</span>EXPORT PDF
      </button>
    </div>

    <!-- Match person 2 selector -->
    <div class="match-row hidden" id="matchRow">
      <label>MATCH WITH</label>
      <select id="matchPerson2">
        <option value="">— select second person —</option>
      </select>
      <button class="btn btn-gold" onclick="runMatchNow()" style="padding:5px 14px">Run Match</button>
    </div>

    <!-- Output area -->
    <div class="output-area">
      <div class="output-header">
        <div class="output-label" id="outputLabel">Output</div>
        <div class="output-actions">
          <button class="btn btn-outline" onclick="clearOutput()" style="padding:3px 10px;font-size:10px">Clear</button>
        </div>
      </div>
      <div class="output-scroll" id="outputBox">
        <div class="output-placeholder">
          <div class="big">🪐</div>
          <div>Select a profile, then run a command</div>
          <div style="font-size:13px;margin-top:4px">ग्रहों की स्थिति जानें</div>
        </div>
      </div>
    </div>

    <div class="status-bar">
      <span><span class="status-dot" id="ollamaDot"></span><span id="ollamaStatus">Checking Ollama…</span></span>
      <span id="activeProfile" style="color:var(--gold)"></span>
      <span id="runStatus"></span>
    </div>
  </div>
</div>

<script>
let selectedProfile = null;
let selectedModel = 'qwen2.5:7b';
let running = false;
let pendingCmd = null;

// ── Stars ──────────────────────────────────────────────────────────────────
(function(){
  const c = document.getElementById('stars');
  const ctx = c.getContext('2d');
  c.width = window.innerWidth; c.height = window.innerHeight;
  for(let i=0;i<120;i++){
    const x=Math.random()*c.width, y=Math.random()*c.height;
    const r=Math.random()*1.2;
    ctx.beginPath(); ctx.arc(x,y,r,0,Math.PI*2);
    ctx.fillStyle=`rgba(255,255,220,${Math.random()*0.6+0.1})`; ctx.fill();
  }
})();

// ── Init ───────────────────────────────────────────────────────────────────
async function init(){
  await loadProfiles();
  await loadModels();
  checkOllama();
}

async function loadProfiles(){
  const r = await fetch('/api/profiles');
  const data = await r.json();
  renderProfiles(data.profiles);
}

function renderProfiles(profiles){
  const el = document.getElementById('profileList');
  const sel2 = document.getElementById('matchPerson2');
  sel2.innerHTML = '<option value="">— select second person —</option>';
  if(!profiles.length){
    el.innerHTML = '<div class="no-profiles">No profiles yet</div>';
    return;
  }
  el.innerHTML = profiles.map(p => `
    <div class="profile-card ${p.name===selectedProfile?'active':''}"
         onclick="selectProfile('${p.name}')">
      <div class="profile-avatar">${p.name[0].toUpperCase()}</div>
      <div>
        <div class="name">${p.name}</div>
        <div class="meta">${p.city} · ${p.dob}</div>
      </div>
    </div>`).join('');
  profiles.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.name; opt.textContent = p.name;
    sel2.appendChild(opt);
  });
}

async function loadModels(){
  const r = await fetch('/api/models');
  const data = await r.json();
  const sel = document.getElementById('modelSelect');
  sel.innerHTML = data.models.map(m =>
    `<option value="${m}" ${m===selectedModel?'selected':''}>${m}</option>`
  ).join('');
  if(data.models.length) selectedModel = data.models[0];
}

async function checkOllama(){
  const r = await fetch('/api/ollama_status');
  const data = await r.json();
  document.getElementById('ollamaDot').className = 'status-dot ' + (data.ok?'ok':'err');
  document.getElementById('ollamaStatus').textContent = data.ok ? 'Ollama running' : 'Ollama offline';
}

function setModel(v){ selectedModel = v; }

function selectProfile(name){
  selectedProfile = name;
  document.querySelectorAll('.profile-card').forEach(c => {
    c.classList.toggle('active', c.querySelector('.name').textContent === name);
  });
  document.getElementById('activeProfile').textContent = '👤 ' + name;
}

// ── Commands ───────────────────────────────────────────────────────────────
function runCmd(cmd){
  if(cmd === 'match'){
    // Show/hide match row
    document.getElementById('matchRow').classList.remove('hidden');
    pendingCmd = 'match';
    highlightCmd(cmd);
    return;
  }
  document.getElementById('matchRow').classList.add('hidden');
  pendingCmd = null;
  if(!selectedProfile){ showMsg('Please select a profile first.', 'err'); return; }
  executeCmd(cmd, selectedProfile, null);
  highlightCmd(cmd);
}

function runMatchNow(){
  const p2 = document.getElementById('matchPerson2').value;
  if(!selectedProfile){ showMsg('Select primary profile.','err'); return; }
  if(!p2){ showMsg('Select second person.','err'); return; }
  if(selectedProfile === p2){ showMsg('Cannot match a profile with itself.','err'); return; }
  executeCmd('match', selectedProfile, p2);
}

// ── South Indian Chart ─────────────────────────────────────────────────────
// Fixed sign positions in 4x4 grid (sign 1=Aries ... 12=Pisces)
const SI_POSITIONS = {
  1:{r:0,c:1}, 2:{r:0,c:2}, 3:{r:0,c:3},
  4:{r:1,c:3}, 5:{r:2,c:3}, 6:{r:3,c:3},
  7:{r:3,c:2}, 8:{r:3,c:1}, 9:{r:3,c:0},
  10:{r:2,c:0},11:{r:1,c:0},12:{r:0,c:0}
};
const SIGN_NAMES = ['','Ari','Tau','Gem','Can','Leo','Vir','Lib','Sco','Sag','Cap','Aqu','Pis'];
const PLANET_COLORS = {
  Sun:'#f0a040',Moon:'#c0d8f8',Mars:'#f06060',Mercury:'#60d080',
  Jupiter:'#f0e060','Jupiter℞':'#f0e060',Venus:'#f080c0',Saturn:'#a080f0',
  'Saturn℞':'#a080f0',Rahu:'#808080','Rahu℞':'#909090',
  Ketu:'#b09060','Ketu℞':'#c0a070','Mercury℞':'#60d080','Mars℞':'#f06060',
  'Venus℞':'#f080c0','Sun℞':'#f0a040','Moon℞':'#c0d8f8'
};

function renderSIChart(data) {
  const S = 130; // cell size
  const W = S*4, H = S*4;
  const cx = W/2, cy = H/2;

  // Build sign→house map (house = (sign_num - lagna_sign_num) % 12 + 1)
  const lagna = data.lagna_sign_num;
  const sp = data.sign_planets;

  let cells = '';
  for(let sn=1; sn<=12; sn++){
    const {r,c} = SI_POSITIONS[sn];
    const x = c*S, y = r*S;
    const isLagna = sn === lagna;
    const house = ((sn - lagna + 12) % 12) + 1;
    const planets = sp[String(sn)] || [];

    // Cell background
    const fill = isLagna ? 'rgba(200,168,75,0.10)' : 'rgba(12,18,32,0.7)';
    const stroke = isLagna ? '#c8a84b' : 'rgba(200,168,75,0.25)';
    const sw = isLagna ? 1.5 : 0.5;

    cells += `<rect x="${x+1}" y="${y+1}" width="${S-2}" height="${S-2}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" rx="2"/>`;

    // Sign name (top-left, small)
    cells += `<text x="${x+6}" y="${y+14}" font-size="10" fill="rgba(200,168,75,0.5)" font-family="Cinzel,serif">${SIGN_NAMES[sn]}</text>`;

    // House number (top-right)
    cells += `<text x="${x+S-6}" y="${y+14}" font-size="10" fill="rgba(150,140,120,0.5)" font-family="Cinzel,serif" text-anchor="end">H${house}</text>`;

    // Lagna marker — diagonal line top-left corner
    if(isLagna){
      cells += `<line x1="${x+1}" y1="${y+1}" x2="${x+28}" y2="${y+1}" stroke="#c8a84b" stroke-width="1.5"/>`;
      cells += `<line x1="${x+1}" y1="${y+1}" x2="${x+1}" y2="${y+28}" stroke="#c8a84b" stroke-width="1.5"/>`;
      cells += `<text x="${x+S/2}" y="${y+S-8}" font-size="9" fill="#c8a84b" font-family="Cinzel,serif" text-anchor="middle" opacity="0.7">Lagna</text>`;
    }

    // Planet labels stacked
    const lineH = 14;
    const startY = y + 30;
    planets.forEach((pl, i) => {
      const pname = pl.replace('℞','');
      const color = PLANET_COLORS[pl] || PLANET_COLORS[pname] || '#d4c9b0';
      const retro = pl.includes('℞') ? ' ℞' : '';
      const ty = startY + i*lineH;
      if(ty < y+S-10){
        cells += `<text x="${x+S/2}" y="${ty}" font-size="11" fill="${color}" font-family="'Crimson Pro',serif" text-anchor="middle" font-weight="400">${pname}${retro}</text>`;
      }
    });
  }

  // Center box
  cells += `<rect x="${S}" y="${S}" width="${S*2}" height="${S*2}" fill="rgba(6,10,18,0.8)" stroke="rgba(200,168,75,0.15)" stroke-width="0.5"/>`;
  cells += `<text x="${cx}" y="${cy-28}" font-size="13" fill="#c8a84b" font-family="Cinzel,serif" text-anchor="middle" letter-spacing="2">KUNDALI</text>`;
  cells += `<text x="${cx}" y="${cy-8}" font-size="11" fill="#8a7e6a" font-family="'Crimson Pro',serif" text-anchor="middle">${data.lagna_sign} Lagna</text>`;
  cells += `<text x="${cx}" y="${cy+10}" font-size="10" fill="#6a6050" font-family="'Crimson Pro',serif" text-anchor="middle">Moon: ${data.moon_sign}</text>`;
  cells += `<text x="${cx}" y="${cy+26}" font-size="10" fill="#6a6050" font-family="'Crimson Pro',serif" text-anchor="middle">${data.moon_nakshatra}</text>`;
  cells += `<text x="${cx}" y="${cy+44}" font-size="10" fill="#6a6050" font-family="'Crimson Pro',serif" text-anchor="middle">Sun: ${data.sun_sign}</text>`;

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" style="width:100%;max-width:520px;display:block;margin:0 auto">
  <rect width="${W}" height="${H}" fill="#060a12" rx="4"/>
  ${cells}
</svg>`;
}

function renderPlanetTable(data){
  const HOUSE_NAMES = ['','Tanu','Dhana','Sahaja','Sukha','Putra','Shatru','Kalatra','Mrityu','Dharma','Karma','Labha','Vyaya'];
  let rows = Object.entries(data.planets).map(([pn, pd]) => {
    const color = PLANET_COLORS[pn] || PLANET_COLORS[pn+'℞'] || '#d4c9b0';
    const retro = pd.retrograde ? ' <span style="opacity:.6">℞</span>' : '';
    return `<tr>
      <td style="color:${color};font-weight:500">${pn}${retro}</td>
      <td>${pd.sign}</td>
      <td style="color:#8a7e6a">${pd.deg}°</td>
      <td>H${pd.house} <span style="color:#6a6050;font-size:11px">${HOUSE_NAMES[pd.house]}</span></td>
      <td style="color:#8a7e6a;font-size:12px">${pd.nakshatra} P${pd.pada}</td>
    </tr>`;
  }).join('');
  return `<table style="width:100%;border-collapse:collapse;font-family:'Crimson Pro',serif;font-size:14px;margin-top:12px">
    <thead><tr style="color:#c8a84b;font-family:Cinzel,serif;font-size:11px;letter-spacing:.08em;border-bottom:1px solid rgba(200,168,75,.2)">
      <th style="text-align:left;padding:4px 8px">Planet</th>
      <th style="text-align:left;padding:4px 8px">Sign</th>
      <th style="text-align:left;padding:4px 8px">Deg</th>
      <th style="text-align:left;padding:4px 8px">House</th>
      <th style="text-align:left;padding:4px 8px">Nakshatra</th>
    </tr></thead>
    <tbody style="color:#d4c9b0">${rows}</tbody>
  </table>`;
}

// ── Western Chart ──────────────────────────────────────────────────────────
const W_SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
                 'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'];
const W_SIGN_ABBR = ['Ari','Tau','Gem','Can','Leo','Vir','Lib','Sco','Sag','Cap','Aqu','Pis'];
const W_SIGN_SYMBOLS = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓'];
const W_ELEMENTS = ['Fire','Earth','Air','Water','Fire','Earth','Air','Water','Fire','Earth','Air','Water'];
const W_ELEM_COLORS = {Fire:'#e8784a',Earth:'#8b7355',Air:'#6ab4ff',Water:'#4a9eff'};
const W_PLANET_COLORS = {
  Sun:'#f0a040', Moon:'#a0c0e8', Mercury:'#50c070', Venus:'#e070b0',
  Mars:'#e05050', Jupiter:'#e8d050', Saturn:'#9070e0', Uranus:'#50d0d0',
  Neptune:'#6090ff', Pluto:'#c08050', Ascendant:'#ffffff', MC:'#ffd700',
};
const W_PLANET_SYMBOLS = {
  Sun:'☉', Moon:'☽', Mercury:'☿', Venus:'♀', Mars:'♂',
  Jupiter:'♃', Saturn:'♄', Uranus:'♅', Neptune:'♆', Pluto:'♇',
  Ascendant:'AC', MC:'MC',
};
const ASP_COLORS_W = {
  Conjunction:'#f0e060', Opposition:'#f06060', Trine:'#60d080',
  Square:'#f06060', Sextile:'#60b0ff', Quincunx:'#c080ff',
};

function renderWesternChart(wc) {
  const sz = 460, cx = sz/2, cy = sz/2;
  const R_OUTER = 210, R_SIGN = 185, R_HOUSE = 158, R_PLANET = 128, R_ASP = 90;

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${sz} ${sz}"
    style="width:100%;max-width:480px;display:block;margin:0 auto;background:#060a12;border-radius:8px">`;

  // Dark bg circle
  svg += `<circle cx="${cx}" cy="${cy}" r="${R_OUTER+4}" fill="#060a12"/>`;

  // Sign ring
  const asc_lon = wc.ascendant.lon;
  for(let i=0;i<12;i++){
    const start_deg = i*30;
    const mid_deg   = start_deg + 15;
    const sign_idx  = ((Math.floor(asc_lon/30) + i) % 12); // signs from ASC
    const elem      = W_ELEMENTS[sign_idx];
    const ecolor    = W_ELEM_COLORS[elem];

    // Segment arc background
    const a1 = (start_deg - 90) * Math.PI/180;
    const a2 = (start_deg + 30 - 90) * Math.PI/180;
    const x1 = cx + R_SIGN*Math.cos(a1), y1 = cy + R_SIGN*Math.sin(a1);
    const x2 = cx + R_OUTER*Math.cos(a1), y2 = cy + R_OUTER*Math.sin(a1);
    const x3 = cx + R_OUTER*Math.cos(a2), y3 = cy + R_OUTER*Math.sin(a2);
    const x4 = cx + R_SIGN*Math.cos(a2), y4 = cy + R_SIGN*Math.sin(a2);
    const fillA = i%2===0 ? ecolor+'22' : ecolor+'11';
    svg += `<path d="M${x1},${y1} L${x2},${y2} A${R_OUTER},${R_OUTER} 0 0,1 ${x3},${y3} L${x4},${y4} A${R_SIGN},${R_SIGN} 0 0,0 ${x1},${y1}" fill="${fillA}" stroke="${ecolor}33" stroke-width="0.5"/>`;

    // Sign symbol + abbr
    const am = (mid_deg - 90) * Math.PI/180;
    const tx = cx + (R_SIGN+14)*Math.cos(am);
    const ty = cy + (R_SIGN+14)*Math.sin(am);
    svg += `<text x="${tx}" y="${ty-5}" text-anchor="middle" font-size="11" fill="${ecolor}" font-family="serif">${W_SIGN_SYMBOLS[sign_idx]}</text>`;
    svg += `<text x="${tx}" y="${ty+7}" text-anchor="middle" font-size="7" fill="${ecolor}99" font-family="Helvetica,sans-serif">${W_SIGN_ABBR[sign_idx]}</text>`;

    // Divider lines
    svg += `<line x1="${cx+R_HOUSE*Math.cos(a1)}" y1="${cy+R_HOUSE*Math.sin(a1)}"
                  x2="${cx+R_OUTER*Math.cos(a1)}" y2="${cy+R_OUTER*Math.sin(a1)}"
                  stroke="#ffffff22" stroke-width="0.5"/>`;
  }

  // House cusps
  const house_labels = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'];
  for(let h=1;h<=12;h++){
    const cusp_lon = wc.house_cusps[h].lon;
    const angle_deg = cusp_lon - asc_lon;
    const a = (angle_deg - 90) * Math.PI/180;
    const x1 = cx + R_HOUSE*Math.cos(a), y1 = cy + R_HOUSE*Math.sin(a);
    const x2 = cx + R_ASP*Math.cos(a), y2 = cy + R_ASP*Math.sin(a);
    const isAngular = [1,4,7,10].includes(h);
    svg += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"
                  stroke="${isAngular?'#c8a84b88':'#ffffff22'}" stroke-width="${isAngular?1.2:0.4}"/>`;
    // House number
    const mid_a = (angle_deg + 15 - 90) * Math.PI/180;
    const lx = cx + (R_ASP+18)*Math.cos(mid_a);
    const ly = cy + (R_ASP+18)*Math.sin(mid_a);
    svg += `<text x="${lx}" y="${ly+3}" text-anchor="middle" font-size="8" fill="#ffffff55" font-family="Helvetica,sans-serif">${house_labels[h-1]}</text>`;
  }

  // Aspect lines
  const planet_positions = {};
  for(const [pname, pd] of Object.entries(wc.planets)){
    const angle_deg = pd.lon - asc_lon;
    const a = (angle_deg - 90) * Math.PI/180;
    planet_positions[pname] = {
      x: cx + R_PLANET*Math.cos(a),
      y: cy + R_PLANET*Math.sin(a),
    };
  }

  for(const asp of wc.aspects){
    if(!['Conjunction','Opposition','Trine','Square','Sextile'].includes(asp.aspect)) continue;
    if(asp.orb > 5) continue;
    const p1 = planet_positions[asp.planet1];
    const p2 = planet_positions[asp.planet2];
    if(!p1||!p2) continue;
    const col = ASP_COLORS_W[asp.aspect] || '#ffffff';
    const opacity = Math.max(0.15, 0.7 - asp.orb*0.1);
    svg += `<line x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}"
                  stroke="${col}" stroke-width="${asp.orb<2?1.2:0.6}" opacity="${opacity}"
                  stroke-dasharray="${asp.aspect==='Trine'||asp.aspect==='Sextile'?'':''}"/>`;
  }

  // Planet dots + labels
  for(const [pname, pd] of Object.entries(wc.planets)){
    const angle_deg = pd.lon - asc_lon;
    const a = (angle_deg - 90) * Math.PI/180;
    const px = cx + R_PLANET*Math.cos(a);
    const py = cy + R_PLANET*Math.sin(a);
    const pcol = W_PLANET_COLORS[pname] || '#ffffff';
    const sym  = W_PLANET_SYMBOLS[pname] || pname.slice(0,2);
    const isAngular = pname==='Ascendant'||pname==='MC';

    svg += `<circle cx="${px}" cy="${py}" r="${isAngular?5:4}" fill="${pcol}" opacity="0.9"/>`;

    // Label offset outward
    const lx = cx + (R_PLANET+18)*Math.cos(a);
    const ly = cy + (R_PLANET+18)*Math.sin(a);
    svg += `<text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="central"
                  font-size="${isAngular?9:10}" fill="${pcol}" font-family="serif" font-weight="bold">${sym}</text>`;
    if(!isAngular){
      const sx = cx + (R_PLANET+18)*Math.cos(a);
      const sy = cy + (R_PLANET+30)*Math.sin(a) + (Math.sin(a)>0?8:-8);
      svg += `<text x="${sx}" y="${sy}" text-anchor="middle" font-size="7" fill="${pcol}99"
                    font-family="Helvetica,sans-serif">${pd.deg}°${pd.retrograde?'℞':''}</text>`;
    }
  }

  // Center info
  svg += `<circle cx="${cx}" cy="${cy}" r="${R_ASP-2}" fill="#060a12" stroke="#c8a84b33" stroke-width="0.5"/>`;
  svg += `<text x="${cx}" y="${cy-22}" text-anchor="middle" font-size="11" fill="#c8a84b" font-family="Helvetica,sans-serif" font-weight="bold">WESTERN</text>`;
  svg += `<text x="${cx}" y="${cy-8}" text-anchor="middle" font-size="9" fill="#8a7e6a" font-family="Helvetica,sans-serif">${wc.rising_sign} Rising</text>`;
  svg += `<text x="${cx}" y="${cy+6}" text-anchor="middle" font-size="8.5" fill="#6a6050" font-family="Helvetica,sans-serif">☉ ${wc.sun_sign}</text>`;
  svg += `<text x="${cx}" y="${cy+19}" text-anchor="middle" font-size="8.5" fill="#6a6050" font-family="Helvetica,sans-serif">☽ ${wc.moon_sign}</text>`;

  svg += `</svg>`;
  return svg;
}

function renderWesternDetails(wc) {
  const HOUSE_NAMES_W = ['','Self','Values','Mind','Home','Creativity','Health',
                         'Relationships','Transformation','Philosophy','Career','Friends','Spirituality'];
  const ASP_SYM = {Conjunction:'☌',Opposition:'☍',Trine:'△',Square:'□',Sextile:'⚹',Quincunx:'⚻'};

  // Planet table
  let rows = '';
  for(const [pn, pd] of Object.entries(wc.planets)){
    if(pn==='Ascendant'||pn==='MC') continue;
    const col = W_PLANET_COLORS[pn]||'#d4c9b0';
    const dig = pd.dignity||'';
    const dc = dig==='Domicile'||dig==='Exaltation'?'#60d080':dig==='Detriment'||dig==='Fall'?'#f06060':'#8a7e6a';
    rows += `<tr>
      <td style="color:${col};font-weight:bold">${W_PLANET_SYMBOLS[pn]||''} ${pn}${pd.retrograde?' ℞':''}</td>
      <td>${pd.sign}</td><td style="color:#8a7e6a">${pd.deg}°</td>
      <td>H${pd.house||'-'} <span style="color:#6a6050;font-size:11px">${HOUSE_NAMES_W[pd.house||0]||''}</span></td>
      <td style="color:${dc};font-size:12px">${dig||'-'}</td>
      <td style="color:#6a6050;font-size:11px">${pd.element}</td>
    </tr>`;
  }
  let table = `<table style="width:100%;border-collapse:collapse;font-family:'Crimson Pro',serif;font-size:14px;margin-top:8px">
    <thead><tr style="color:#6ab4ff;font-family:Cinzel,serif;font-size:10px;letter-spacing:.08em;border-bottom:1px solid rgba(100,180,255,.2)">
      <th style="text-align:left;padding:3px 6px">Planet</th><th>Sign</th><th>Deg</th><th>House</th><th>Dignity</th><th>Element</th>
    </tr></thead><tbody style="color:#d4c9b0">${rows}</tbody></table>`;

  // Aspects
  const major_asps = wc.aspects.filter(a=>['Conjunction','Opposition','Trine','Square','Sextile'].includes(a.aspect)&&a.orb<5);
  let asp_rows = major_asps.slice(0,12).map(a=>{
    const col = ASP_COLORS_W[a.aspect]||'#fff';
    return `<tr><td style="color:#d4c9b0">${a.planet1}</td>
      <td style="color:${col};text-align:center">${ASP_SYM[a.aspect]||''} ${a.aspect}</td>
      <td style="color:#d4c9b0">${a.planet2}</td>
      <td style="color:#8a7e6a;text-align:center">${a.orb}°</td></tr>`;
  }).join('');
  let asp_table = asp_rows ? `<table style="width:100%;border-collapse:collapse;font-family:'Crimson Pro',serif;font-size:13px;margin-top:12px">
    <thead><tr style="color:#6ab4ff;font-family:Cinzel,serif;font-size:10px;border-bottom:1px solid rgba(100,180,255,.15)">
      <th style="text-align:left;padding:3px 6px">Planet</th><th>Aspect</th><th>Planet</th><th>Orb</th></tr></thead>
    <tbody>${asp_rows}</tbody></table>` : '';

  // Patterns
  let pat_html = '';
  if(wc.patterns.length){
    pat_html = `<div style="margin-top:12px;padding:10px;border:1px solid rgba(100,180,255,.2);border-radius:6px;background:rgba(100,180,255,.03)">
      <div style="font-family:Cinzel,serif;font-size:10px;color:#6ab4ff;letter-spacing:.1em;margin-bottom:8px">CHART PATTERNS</div>
      ${wc.patterns.map(p=>`
        <div style="margin-bottom:8px">
          <span style="color:#f0e060;font-weight:bold;font-family:Cinzel,serif;font-size:11px">${p.name}</span>
          <span style="color:#8a7e6a;font-size:12px"> — ${p.planets.join(', ')}</span>
          <div style="color:#6a6050;font-size:12px;margin-top:2px">${p.description}</div>
        </div>`).join('')}
    </div>`;
  }

  // Balance
  const eb = wc.element_balance; const mb = wc.modality_balance;
  const bal_html = `<div style="margin-top:10px;display:flex;gap:16px;font-size:12px;color:#8a7e6a;font-family:Cinzel,serif;letter-spacing:.04em">
    <span>🔥${eb.Fire} 🌍${eb.Earth} 💨${eb.Air} 💧${eb.Water}</span>
    <span>Cardinal:${mb.Cardinal} Fixed:${mb.Fixed} Mutable:${mb.Mutable}</span>
  </div>`;

  return table + asp_table + pat_html + bal_html;
}

async function executeCmd(cmd, person1, person2){
  if(running) return;
  running = true;

  const useLLM = document.getElementById('useLLM').checked;
  const model  = document.getElementById('modelSelect').value;

  // For WESTERN: render circular chart + details, then optionally LLM
  if(cmd === 'western'){
    document.getElementById('outputLabel').textContent = 'WESTERN · ' + person1;
    setOutput('<span class="spinner"></span>Computing Western tropical chart…');
    try {
      const r = await fetch('/api/western_data/' + encodeURIComponent(person1));
      const data = await r.json();
      if(!data.ok){ setOutput('Error: '+data.error); running=false; document.querySelectorAll('.cmd-btn').forEach(b=>b.classList.remove('running')); return; }
      const wc = data.chart;
      const chartSVG = renderWesternChart(wc);
      const details  = renderWesternDetails(wc);
      let html = `<div style="padding:4px 0">${chartSVG}</div><div style="padding:0 4px">${details}</div>`;

      if(useLLM){
        html += `<div style="margin-top:12px;padding:8px 12px;border:1px solid rgba(100,180,255,.2);border-radius:6px">
          <span class="spinner"></span><span style="color:#6ab4ff;font-family:Cinzel,serif;font-size:10px">Fetching Western LLM reading…</span></div>`;
        setOutput(html);
        const lr = await fetch('/api/western_llm/'+encodeURIComponent(person1), {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({model, mode:'western'})
        });
        const ld = await lr.json();
        html += `<div style="margin-top:12px;padding:12px;border:1px solid rgba(100,180,255,.2);border-radius:6px;background:rgba(100,180,255,.03)">
          <div style="font-family:Cinzel,serif;font-size:10px;color:#6ab4ff;letter-spacing:.1em;margin-bottom:8px">♈ WESTERN READING</div>
          <div style="font-family:'Crimson Pro',serif;font-size:14px;line-height:1.7;color:#d4c9b0;white-space:pre-wrap">${ld.text||ld.error}</div>
        </div>
        <div style="margin-top:10px;padding:12px;border:1px solid rgba(200,100,255,.2);border-radius:6px;background:rgba(200,100,255,.03)">
          <div style="font-family:Cinzel,serif;font-size:10px;color:#c080ff;letter-spacing:.1em;margin-bottom:6px">⚡ FETCHING VEDIC vs WESTERN COMPARISON…</div>
          <span class="spinner"></span>
        </div>`;
        setOutput(html);
        const cr = await fetch('/api/western_llm/'+encodeURIComponent(person1), {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({model, mode:'compare'})
        });
        const cd = await cr.json();
        // Replace last panel
        const base = html.split('<div style="margin-top:10px;padding:12px;border:1px solid rgba(200,100,255,.2)')[0];
        html = base + `<div style="margin-top:10px;padding:12px;border:1px solid rgba(200,100,255,.2);border-radius:6px;background:rgba(200,100,255,.03)">
          <div style="font-family:Cinzel,serif;font-size:10px;color:#c080ff;letter-spacing:.1em;margin-bottom:8px">⚡ VEDIC vs WESTERN SYNTHESIS</div>
          <div style="font-family:'Crimson Pro',serif;font-size:14px;line-height:1.7;color:#d4c9b0;white-space:pre-wrap">${cd.text||cd.error}</div>
        </div>`;
      }
      setOutput(html);
    } catch(e){ setOutput('Error: '+e.message); }
    running=false;
    document.querySelectorAll('.cmd-btn').forEach(b=>b.classList.remove('running'));
    document.getElementById('runStatus').textContent='✓ done';
    setTimeout(()=>document.getElementById('runStatus').textContent='',3000);
    return;
  }

  if(cmd === 'chart'){
    document.getElementById('outputLabel').textContent = 'KUNDALI · ' + person1;
    setOutput('<span class="spinner"></span>Computing chart…');
    try {
      const r = await fetch('/api/chart_data/' + encodeURIComponent(person1));
      const data = await r.json();
      if(data.ok){
        const chartSVG = renderSIChart(data);
        const table = renderPlanetTable(data);
        let html = `<div style="padding:4px 0">${chartSVG}</div><div style="padding:0 4px">${table}</div>`;
        if(useLLM){
          html += `<div style="margin-top:16px;padding:10px;border:1px solid rgba(200,168,75,.15);border-radius:6px">
            <span class="spinner"></span><span style="color:#8a7e6a;font-family:Cinzel,serif;font-size:11px">Fetching LLM reading…</span>
          </div>`;
          setOutput(html);
          // Now get LLM reading via CLI
          const cr = await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({args:['chart',person1,'--llm'],model})});
          const cd = await cr.json();
          // Extract just the LLM panel from output
          const llmText = cd.output.replace(/.*Jyotish Reading.*/s,'').trim() || cd.output;
          html = `<div style="padding:4px 0">${chartSVG}</div><div style="padding:0 4px">${table}</div>
            <div style="margin-top:16px;padding:12px;border:1px solid rgba(200,168,75,.2);border-radius:6px;background:rgba(200,168,75,.03)">
              <div style="font-family:Cinzel,serif;font-size:10px;color:#c8a84b;letter-spacing:.1em;margin-bottom:8px">📿 JYOTISH READING</div>
              <div style="font-family:'Crimson Pro',serif;font-size:14px;line-height:1.7;color:#d4c9b0;white-space:pre-wrap">${cd.output}</div>
            </div>`;
        }
        setOutput(html);
      } else {
        setOutput('Error: ' + data.error);
      }
    } catch(e){ setOutput('Error: '+e.message); }
    running = false;
    document.querySelectorAll('.cmd-btn').forEach(b => b.classList.remove('running'));
    document.getElementById('runStatus').textContent = '✓ done';
    setTimeout(()=>document.getElementById('runStatus').textContent='',3000);
    return;
  }

  // Build args
  let args = [cmd, person1];
  if(cmd === 'match' && person2) args.push(person2);
  if(useLLM && cmd !== 'list') args.push('--llm');

  // UI
  document.getElementById('outputLabel').textContent = cmd.toUpperCase() + ' · ' + person1 + (person2?' × '+person2:'');
  setOutput('<span class="spinner"></span>Running ' + cmd.toUpperCase() + '…\n\nModel: ' + model + (useLLM?' (LLM enabled)':' (no LLM)'));
  document.getElementById('runStatus').textContent = '⏳ running…';
  document.querySelectorAll('.cmd-btn').forEach(b => b.classList.add('running'));

  try {
    const r = await fetch('/api/run', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({args, model})
    });
    const data = await r.json();
    setOutput(data.output || '(no output)');
    document.getElementById('runStatus').textContent = '✓ done';
  } catch(e) {
    setOutput('Error: ' + e.message);
    document.getElementById('runStatus').textContent = '✗ error';
  } finally {
    running = false;
    document.querySelectorAll('.cmd-btn').forEach(b => b.classList.remove('running'));
    setTimeout(()=> document.getElementById('runStatus').textContent = '', 3000);
  }
}

function setOutput(html){
  const box = document.getElementById('outputBox');
  box.textContent = '';
  box.innerHTML = html;
  box.scrollTop = box.scrollHeight;
}

function clearOutput(){
  document.getElementById('outputBox').innerHTML = `
    <div class="output-placeholder">
      <div class="big">🪐</div>
      <div>Select a profile, then run a command</div>
      <div style="font-size:13px;margin-top:4px">ग्रहों की स्थिति जानें</div>
    </div>`;
  document.getElementById('outputLabel').textContent = 'Output';
}

function highlightCmd(cmd){
  document.querySelectorAll('.cmd-btn').forEach(b => b.classList.remove('active-cmd'));
  document.getElementById('cmd-'+cmd)?.classList.add('active-cmd');
}

// ── Add profile ────────────────────────────────────────────────────────────
async function saveProfile(){
  const name = document.getElementById('f_name').value.trim();
  const dob  = document.getElementById('f_dob').value;
  const tob  = document.getElementById('f_tob').value;
  const city = document.getElementById('f_city').value.trim();
  const lat  = document.getElementById('f_lat').value;
  const lon  = document.getElementById('f_lon').value;
  const tz   = document.getElementById('f_tz').value.trim();
  const msg  = document.getElementById('addMsg');

  if(!name||!dob||!tob||!lat||!lon){ msg.style.color='var(--red)'; msg.textContent='Fill all required fields.'; return; }

  const r = await fetch('/api/profile', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name,dob,tob,city,lat:parseFloat(lat),lon:parseFloat(lon),tz})
  });
  const data = await r.json();
  if(data.ok){
    msg.style.color='var(--green)'; msg.textContent='✓ Profile saved!';
    await loadProfiles();
    selectProfile(name);
    setTimeout(()=>{ msg.textContent=''; toggleAddForm(false); },1500);
  } else {
    msg.style.color='var(--red)'; msg.textContent='Error: '+data.error;
  }
}

let addOpen = false;
function toggleAddForm(forceClose){
  addOpen = forceClose===false ? false : !addOpen;
  document.getElementById('addForm').classList.toggle('open', addOpen);
  document.getElementById('addArrow').textContent = addOpen ? '▼' : '▶';
}

function fillCoords(lat, lon, tz){
  document.getElementById('f_lat').value = lat;
  document.getElementById('f_lon').value = lon;
  document.getElementById('f_tz').value = tz;
}

async function exportPDF(){
  if(!selectedProfile){ showMsg('Please select a profile first.', 'err'); return; }
  if(running){ showMsg('Please wait for the current command to finish.', 'err'); return; }

  const btn  = document.getElementById('cmd-export');
  const model = document.getElementById('modelSelect').value;
  btn.classList.add('running');
  btn.innerHTML = '<span class="spinner"></span>EXPORTING…';
  document.getElementById('outputLabel').textContent = '📄 Full PDF Export · ' + selectedProfile;

  const steps = [
    '🗺  Computing birth chart…',
    '📿  Running Kundali LLM reading…',
    '⏳  Running Dasha prediction…',
    '🌙  Running Transit prediction…',
    '☯  Running Yoga & Dosha reading…',
    '📄  Assembling PDF…',
  ];
  let step = 0;
  function tick(){
    if(step < steps.length)
      setOutput(steps.slice(0, step+1).map((s,i)=> (i<step?'✓ ':'<span class="spinner"></span>') + s).join('\n\n'));
    step++;
  }
  tick();
  const ticker = setInterval(tick, 8000); // rough pacing

  try {
    const resp = await fetch(`/api/export_pdf/${encodeURIComponent(selectedProfile)}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ model }),
    });

    clearInterval(ticker);

    if(!resp.ok){
      let err = 'Server error';
      try { const j = await resp.json(); err = j.error || err; } catch{}
      setOutput('❌ PDF Error: ' + err);
      return;
    }

    const blob = await resp.blob();
    const fname = `kundali_${selectedProfile.toLowerCase().replace(/\s+/g,'_')}.pdf`;
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = fname;
    a.click();

    setOutput(
      '✓ Kundali chart + planet table\n' +
      '✓ Dasha timeline (25 years)\n' +
      '✓ Yogas & Doshas analysis\n' +
      '✓ Today\'s transit summary\n' +
      '✓ Kundali reading (LLM)\n' +
      '✓ Dasha prediction (LLM)\n' +
      '✓ Transit guidance (LLM)\n' +
      '✓ Yoga interpretation (LLM)\n\n' +
      `📄 Downloaded: ${fname}`
    );
  } catch(e){
    clearInterval(ticker);
    setOutput('Error: ' + e.message);
  } finally {
    btn.classList.remove('running');
    btn.innerHTML = '<span class="cmd-icon">📄</span>EXPORT PDF';
  }
}

function showMsg(text, type){
  const box = document.getElementById('outputBox');
  box.innerHTML = `<div style="color:var(--${type==='err'?'red':'green'});padding:20px;font-family:var(--font-body)">${text}</div>`;
}

init();
</script>
</body>
</html>
"""

# ── API routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/profiles")
def api_profiles():
    return jsonify({"profiles": get_profiles()})


@app.route("/api/profile", methods=["POST"])
def api_save_profile():
    try:
        d = request.json
        from data.db import save_profile
        save_profile(d["name"], d["dob"], d["tob"],
                     d["lat"], d["lon"], d["tz"], d.get("city",""))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/models")
def api_models():
    return jsonify({"models": get_ollama_models()})


@app.route("/api/ollama_status")
def api_ollama_status():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        return jsonify({"ok": r.status_code == 200})
    except:
        return jsonify({"ok": False})


@app.route("/api/run", methods=["POST"])
def api_run():
    d = request.json
    args  = d.get("args", [])
    model = d.get("model", "qwen2.5:7b")
    env   = {"JYOTISH_MODEL": model}
    output = run_cmd(args, env_override=env)
    return jsonify({"output": output})


@app.route("/api/chart_data/<profile_name>")
def api_chart_data(profile_name):
    try:
        from data.db import load_profile
        from core.kundali import build_kundali
        from datetime import datetime
        p = load_profile(profile_name)
        if not p:
            return jsonify({"ok": False, "error": "Profile not found"})
        dob = datetime.strptime(f"{p['dob']} {p['tob']}", "%Y-%m-%d %H:%M")
        k = build_kundali(p["name"], dob, p["lat"], p["lon"], p["tz"])
        # Build planet-per-sign mapping
        sign_planets = {i: [] for i in range(1, 13)}
        for pname, pdata in k["planets"].items():
            label = pname
            if pdata.get("retrograde"): label += "℞"
            sign_planets[pdata["sign_num"]].append(label)
        return jsonify({
            "ok": True,
            "lagna_sign_num": k["lagna"]["sign_num"],
            "lagna_sign": k["lagna"]["sign"],
            "moon_sign": k["moon_sign"],
            "moon_nakshatra": k["moon_nakshatra"],
            "sun_sign": k["sun_sign"],
            "sign_planets": {str(k2): v for k2, v in sign_planets.items()},
            "planets": {
                pn: {
                    "sign": pd["sign"],
                    "sign_num": pd["sign_num"],
                    "deg": pd["deg"],
                    "nakshatra": pd["nakshatra"],
                    "pada": pd["pada"],
                    "house": pd["house"],
                    "retrograde": pd["retrograde"],
                }
                for pn, pd in k["planets"].items()
            }
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/export_pdf/<profile_name>", methods=["POST"])
def api_export_pdf(profile_name):
    try:
        from data.db import load_profile
        from core.kundali import build_kundali
        from core.dasha import get_dasha_periods, get_current_dasha
        from core.yogas import analyze_all
        from core.transits import get_today_transits, get_moon_transit
        from export_pdf import build_pdf
        from datetime import datetime

        p = load_profile(profile_name)
        if not p:
            return jsonify({"ok": False, "error": "Profile not found"}), 404

        dob = datetime.strptime(f"{p['dob']} {p['tob']}", "%Y-%m-%d %H:%M")
        k   = build_kundali(p["name"], dob, p["lat"], p["lon"], p["tz"])

        moon_lon = k["planets"]["Moon"]["lon"]
        periods  = get_dasha_periods(dob, moon_lon, years_ahead=25)
        current  = get_current_dasha(periods)
        yogas    = analyze_all(k)
        transits = get_today_transits(k, days=1)
        moon_t   = get_moon_transit(k)

        model = (request.json or {}).get("model", "qwen2.5:7b")

        # Run all 4 LLM predictions
        def llm(args):
            return run_cmd(args, env_override={"JYOTISH_MODEL": model})

        predictions = {
            "chart":   llm(["chart",   profile_name, "--llm"]),
            "dasha":   llm(["dasha",   profile_name, "--llm"]),
            "transit": llm(["transit", profile_name, "--llm"]),
            "yoga":    llm(["yoga",    profile_name, "--llm"]),
        }

        pdf_bytes = build_pdf(k, periods, current, yogas, transits, moon_t, predictions)

        fname = f"kundali_{profile_name.lower().replace(' ','_')}.pdf"
        from flask import send_file
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=fname,
        )
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/debug/<profile_name>")
def api_debug(profile_name):
    """Returns all intermediate astrological values for comparison with reference software."""
    try:
        import swisseph as swe
        from data.db import load_profile
        from core.kundali import build_kundali
        from datetime import datetime
        import pytz

        p = load_profile(profile_name)
        if not p:
            return jsonify({"ok": False, "error": "Profile not found"})

        dob = datetime.strptime(f"{p['dob']} {p['tob']}", "%Y-%m-%d %H:%M")
        tz  = pytz.timezone(p["tz"])
        local_dt = tz.localize(dob)
        utc_dt   = local_dt.astimezone(pytz.utc).replace(tzinfo=None)

        jd   = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                          utc_dt.hour + utc_dt.minute/60 + utc_dt.second/3600)
        ayan = swe.get_ayanamsa_ut(jd)

        _, ascmc_trop = swe.houses_ex(jd, p["lat"], p["lon"], b'P')
        asc_tropical  = ascmc_trop[0]
        asc_sidereal  = (asc_tropical - ayan) % 360

        SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
                 'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
        NAKS  = ['Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra',
                 'Punarvasu','Pushya','Ashlesha','Magha','Purva Phalguni','Uttara Phalguni',
                 'Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
                 'Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishta',
                 'Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati']

        nak_idx  = int(asc_sidereal / (360/27))
        nak_pada = int((asc_sidereal % (360/27)) / (360/108)) + 1

        # Planet raw positions
        planet_ids = {"Sun":0,"Moon":1,"Mercury":2,"Venus":3,"Mars":4,"Jupiter":5,"Saturn":6}
        planets_debug = {}
        for name, pid in planet_ids.items():
            pos, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
            lon = pos[0] % 360
            planets_debug[name] = {
                "sidereal_lon": round(lon, 4),
                "sign": SIGNS[int(lon//30)],
                "deg_in_sign": round(lon % 30, 4),
            }

        return jsonify({
            "ok": True,
            "profile": {
                "name": p["name"],
                "dob_local": f"{p['dob']} {p['tob']} {p['tz']}",
                "dob_utc": utc_dt.strftime("%Y-%m-%d %H:%M UTC"),
            },
            "ephemeris": {
                "julian_day": round(jd, 6),
                "lahiri_ayanamsa": round(ayan, 4),
                "asc_tropical": round(asc_tropical, 4),
                "asc_sidereal": round(asc_sidereal, 4),
                "lagna_sign": SIGNS[int(asc_sidereal//30)],
                "lagna_deg": round(asc_sidereal % 30, 4),
                "lagna_nakshatra": NAKS[nak_idx],
                "lagna_pada": nak_pada,
            },
            "planets": planets_debug,
            "compare_with_astrovision": (
                "Verify: lagna_sign, lagna_deg, and planet signs above should match Astro-Vision exactly. "
                "If lagna_sign matches but planets are off, report which planet. "
                "If lagna_sign is still wrong, share your exact birth date so we can cross-check the UTC conversion."
            )
        })
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()})


@app.route("/api/western_data/<profile_name>")
def api_western_data(profile_name):
    try:
        from data.db import load_profile
        from core.western import get_western_chart
        from datetime import datetime
        p = load_profile(profile_name)
        if not p:
            return jsonify({"ok": False, "error": "Profile not found"})
        dob = datetime.strptime(f"{p['dob']} {p['tob']}", "%Y-%m-%d %H:%M")
        wc  = get_western_chart(dob, p["lat"], p["lon"], p["tz"])
        return jsonify({"ok": True, "chart": wc})
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()})


@app.route("/api/western_llm/<profile_name>", methods=["POST"])
def api_western_llm(profile_name):
    try:
        from data.db import load_profile
        from core.western import get_western_chart
        from llm.western_interpreter import interpret_western_chart, interpret_comparison
        from datetime import datetime
        import os

        p = load_profile(profile_name)
        if not p:
            return jsonify({"ok": False, "error": "Profile not found"})

        d     = request.json or {}
        model = d.get("model", "qwen2.5:7b")
        mode  = d.get("mode", "western")  # "western" or "compare"

        os.environ["JYOTISH_MODEL"] = model
        dob = datetime.strptime(f"{p['dob']} {p['tob']}", "%Y-%m-%d %H:%M")
        wc  = get_western_chart(dob, p["lat"], p["lon"], p["tz"])

        if mode == "compare":
            from core.kundali import build_kundali
            k = build_kundali(p["name"], dob, p["lat"], p["lon"], p["tz"])
            text = interpret_comparison(p["name"], k, wc)
        else:
            text = interpret_western_chart(p["name"], wc)

        return jsonify({"ok": True, "text": text})
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()})


if __name__ == "__main__":
    import webbrowser, threading
    port = 5050
    print(f"\n🪐 Jyotish GUI starting at http://localhost:{port}\n")
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(host="127.0.0.1", port=port, debug=False)
