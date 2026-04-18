from flask import Flask, render_template_string, jsonify, request, session, redirect
import logging
import datetime

DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>GEMINI TITAN V27 | Control Center</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root { --bg: #060912; --card: #0b0e14; --primary: #00f5ff; --secondary: #9e00ff; --text: #f8fafc; --text-dim: #94a3b8; --success: #00ff7f; --danger: #ff0055; --border: rgba(255,255,255,0.08); }
        * { box-sizing: border-box; margin:0; padding:0; }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .header { display: flex; justify-content: space-between; align-items: center; padding: 15px 30px; background: rgba(11,14,20,0.9); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100 }
        .container { max-width: 1400px; margin: 20px auto; padding: 0 15px; }
        .grid { display: grid; grid-template-columns: 320px 1fr 320px; gap: 20px; }
        @media (max-width: 1100px) { .grid { grid-template-columns: 1fr; } }
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 20px; margin-bottom: 20px; position: relative; }
        .card-title { font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-dim); margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }
        .pnl-big { font-size: 2.5rem; font-weight: 900; text-align: center; margin: 10px 0; }
        .green { color: var(--success); }
        .red { color: var(--danger); }
        .btn { width: 100%; padding: 14px; border-radius: 12px; border: none; font-weight: 800; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 10px; font-size: 0.85rem; transition: 0.2s; }
        .btn:active { transform: scale(0.96); }
        .btn-primary { background: linear-gradient(45deg, var(--secondary), var(--primary)); color: #fff; }
        .btn-danger { background: var(--danger); color: #fff; }
        .btn-outline { background: rgba(255,255,255,0.03); border: 1px solid var(--border); color: var(--text); }
        .sym-item { display: flex; justify-content: space-between; padding: 12px; border-radius: 10px; cursor: pointer; margin-bottom: 5px; border: 1px solid transparent; transition: 0.2s; }
        .sym-item.active { background: rgba(0, 245, 255, 0.1); border-color: rgba(0, 245, 255, 0.3); }
        .sig-item { padding: 15px; border-radius: 12px; background: rgba(255,255,255,0.02); border: 1px solid var(--border); margin-bottom: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <div style="font-weight:900; font-size:1.4rem; color:var(--primary); display:flex; align-items:center; gap:10px">
            <i class="fas fa-bolt"></i> GEMINI TITAN V27
        </div>
        <div style="display:flex; gap:30px; align-items:center">
            <div id="clock" style="font-weight:800; font-family:monospace; font-size:1.2rem; color:var(--primary)">--:--:--</div>
            <div style="display:flex; align-items:center; gap:10px; background:rgba(0,0,0,0.3); padding:8px 15px; border-radius:30px; border:1px solid var(--border)">
                <span id="mt5-led" style="width:8px; height:8px; border-radius:50%; background:#444"></span>
                <span id="mt5-status" style="font-size:0.65rem; font-weight:800; color:var(--text-dim)">WAITING...</span>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="grid">
            <div class="col">
                <div class="card">
                    <div class="card-title">Account Terminal</div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:15px">
                        <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:10px">
                            <div style="font-size:0.6rem; color:var(--text-dim)">Balance</div><b id="acc-bal">$0.00</b>
                        </div>
                        <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:10px">
                            <div style="font-size:0.6rem; color:var(--text-dim)">Equity</div><b id="acc-eq">$0.00</b>
                        </div>
                    </div>
                    <div id="acc-pnl" class="pnl-big">$0.00</div>
                    <button class="btn btn-danger" onclick="doAction('panic')">PANIC CLOSE ALL</button>
                </div>
                <div class="card"><div class="card-title">Market Symbols</div><div id="sym-list"></div></div>
            </div>
            <div class="col">
                <div class="card" style="min-height:550px">
                    <div class="card-title">Live SMC Signals</div>
                    <div id="signals-container"></div>
                </div>
                <div class="card" id="ai-report-card" style="display:none">
                    <div class="card-title">AI Analysis Report</div>
                    <div id="ai-report-content" style="font-size:0.8rem; line-height:1.4; color:var(--text-dim)"></div>
                </div>
            </div>
            <div class="col">
                <div class="card">
                    <div class="card-title">AI Intelligence</div>
                    <button class="btn btn-primary" onclick="reqAI('technical')">📊 Texnik Tahlil</button>
                    <button class="btn btn-primary" onclick="reqAI('fundamental')">🌐 Fundamental</button>
                    <button class="btn btn-primary" onclick="reqAI('scalping')" style="background: #3a0ca3">⚡ Scalping AI</button>
                    <button class="btn btn-outline" onclick="reqAI('risk')">⚖️ Risk Status</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // IMMUTABLE ENGINE - RUNS INDEPENDENTLY
        var selectedSym = "XAU/USD";

        function updateClock() {
            var el = document.getElementById("clock");
            if (el) {
                var d = new Date();
                var h = d.getHours(), m = d.getMinutes(), s = d.getSeconds();
                el.innerHTML = (h < 10 ? "0" + h : h) + ":" + (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
            }
        }

        function syncData() {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/api/symbols_data?v=" + new Date().getTime(), true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    try {
                        var d = JSON.parse(xhr.responseText);
                        var t = d.terminal || {connected: false};
                        
                        var connEl = document.getElementById("mt5-led");
                        var statusEl = document.getElementById("mt5-status");
                        
                        if (t.connected) {
                            connEl.style.background = "#00ff7f";
                            statusEl.innerHTML = "MT5: CONNECTED";
                        } else {
                            connEl.style.background = "#ffaa00";
                            statusEl.innerHTML = "WATCHER MODE: ACTIVE";
                        }

                        document.getElementById("acc-bal").innerHTML = t.balance ? "$" + t.balance.toFixed(2) : "NO-API";
                        document.getElementById("acc-eq").innerHTML = t.equity ? "$" + t.equity.toFixed(2) : "NO-API";
                        
                        var p = t.pnl || 0;
                        var pnlEl = document.getElementById("acc-pnl");
                        if (t.balance) {
                            pnlEl.innerHTML = (p >= 0 ? "+" : "") + p.toFixed(2) + "$";
                            pnlEl.className = "pnl-big " + (p >= 0 ? "green" : "red");
                        } else {
                            pnlEl.innerHTML = "DATA ONLY";
                            pnlEl.className = "pnl-big";
                            pnlEl.style.color = "var(--primary)";
                        }

                        if(d.symbols) {
                            var h = "";
                            for(var s in d.symbols) {
                                var active = (s === selectedSym ? "active" : "");
                                h += '<div class="sym-item ' + active + '" onclick="window.selectSym(\''+s+'\')">' +
                                     '<b>'+s+'</b> <span>'+d.symbols[s].price+'</span></div>';
                            }
                            document.getElementById("sym-list").innerHTML = h;
                        }

                        if(d.signals) {
                            var sigH = "";
                            for(var i=d.signals.length-1; i>=0; i--) {
                                var sig = d.signals[i];
                                sigH += '<div class="sig-item"><b>'+sig.symbol+'</b>: '+(sig.direction.toUpperCase())+' @ '+sig.entry+'</div>';
                            }
                            document.getElementById("signals-container").innerHTML = sigH;
                        }

                        if(d.last_ai_report) {
                            var aiCard = document.getElementById("ai-report-card");
                            var aiContent = document.getElementById("ai-report-content");
                            if (aiCard && aiContent) {
                                aiCard.style.display = "block";
                                aiContent.innerHTML = d.last_ai_report.replace(/\n/g, '<br>');
                            }
                        }
                    } catch(e) {}
                }
            };
            xhr.send();
        }

        window.selectSym = function(s) { selectedSym = s; syncData(); };
        window.reqAI = function(type) {
            var x = new XMLHttpRequest(); x.open("POST", "/api/request_ai", true);
            x.setRequestHeader("Content-Type", "application/json");
            x.onreadystatechange = function() {
                if (x.readyState === 4 && x.status === 200) {
                    alert("AI so'rovi qabul qilindi! Tahlil Telegram va Dashboard'da ko'rinadi.");
                }
            };
            x.send(JSON.stringify({type: type, symbol: selectedSym}));
        };
        window.doAction = function(a) { if(confirm("Confirm?")) { var x=new XMLHttpRequest(); x.open("POST","/api/"+a,true); x.send(); } };

        // INITIALIZE IMMEDIATELY
        updateClock();
        setInterval(updateClock, 1000);
        syncData();
        setInterval(syncData, 5000);
    </script>
</body>
</html>"""

def create_app(bot_state: dict, config: dict, lock):
    app = Flask(__name__)
    app.secret_key = "gemini_terminal_ultra_v27"
    pwd = config.get('web', {}).get('password', 'gemini2024')

    @app.route('/login', methods=['GET','POST'])
    def login():
        if request.method == 'POST':
            if request.form.get('password') == pwd:
                session['logged'] = True
                return redirect('/')
        return '<html><body style="background:#060912;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh"><form method="POST"><h2>GEMINI LOGIN</h2><input type="password" name="password" style="padding:10px"><button type="submit">ENTER</button></form></body></html>'

    @app.route('/')
    def index():
        if not session.get('logged'): return redirect('/login')
        return render_template_string(DASHBOARD_HTML)

    @app.route('/api/symbols_data')
    def sd():
        if not session.get('logged'): return jsonify({'err':'unauth'})

        # PythonAnywhere jonli sinxronizatsiyasi (Fayldan o'qish)
        import os, json
        try:
            if os.path.exists('data/bot_state.json'):
                with open('data/bot_state.json', 'r') as f:
                    bot_state.update(json.load(f))
        except: pass

        symbols_list = bot_state.get('symbols', {})
        terminal = bot_state.get('terminal', {})
        signals = bot_state.get('signals_log', [])
        last_ai = bot_state.get('last_ai_report', '')
        
        syms_ui = {}
        for s, d in symbols_list.items():
            price = d.get('price')
            price_str = f"{price:.5g}" if price is not None else "0.000"
            syms_ui[s] = {'price': price_str, 'change': d.get('change', 0)}
        
        return jsonify({
            'symbols': syms_ui, 
            'terminal': terminal, 
            'signals': signals,
            'last_ai_report': last_ai
        })

    @app.route('/api/request_ai', methods=['POST'])
    def rai():
        if not session.get('logged'): return jsonify({'err':'unauth'})
        data = request.json
        with lock:
            bot_state['ai_requests'].append({'type': data.get('type', 'technical'), 'symbol': data.get('symbol', 'XAU/USD')})
        return jsonify({'ok':True})

    @app.route('/api/panic', methods=['POST'])
    def panic():
        if not session.get('logged'): return jsonify({'err':'unauth'})
        with lock: bot_state['panic_request'] = True
        return jsonify({'ok':True})

    return app
