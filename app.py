from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3
import pandas as pd

app = Flask(__name__)
DB_FILE = "credenza.db"

# DATABASE
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS credenza 
                 (codice TEXT, nome TEXT, categoria TEXT DEFAULT 'Altro',
                  quantita INTEGER DEFAULT 0, prezzo REAL DEFAULT 0, 
                  scadenza TEXT, data_inserimento TEXT,
                  PRIMARY KEY (codice, nome))''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_spesa 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, categoria TEXT DEFAULT 'Altro',
                  quantita INTEGER DEFAULT 1, prezzo REAL DEFAULT 0,
                  data_inserimento TEXT, completato INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

CATEGORIE = ['Altro', 'Latte/Uova', 'Carne/Pesce', 'Frutta/Verdura', 'Pane/Pasta', 'Conserve', 'Bevande', 'Dolci/Snack']

def get_dati_credenza():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM credenza ORDER BY data_inserimento DESC", conn)
    conn.close()
    if df.empty:
        return {"items": [], "stats": {"totale_items": 0, "totale_quantita": 0, "valore_totale": 0}}
    stats = {
        "totale_items": len(df),
        "totale_quantita": int(df['quantita'].sum()),
        "valore_totale": round((df['prezzo'] * df['quantita']).sum(), 2)
    }
    return {"items": df.to_dict('records'), "stats": stats}

def get_lista_spesa():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM lista_spesa ORDER BY data_inserimento DESC", conn)
    conn.close()
    if df.empty:
        return {"items": [], "stats": {"totale_items": 0, "totale_da_completare": 0, "valore_da_completare": 0}}
    stats = {
        "totale_items": len(df),
        "totale_da_completare": len(df[df['completato'] == 0]),
        "valore_da_completare": round((df[df['completato'] == 0]['prezzo'] * df[df['completato'] == 0]['quantita']).sum(), 2)
    }
    return {"items": df.to_dict('records'), "stats": stats}

# FUNZIONI
def aggiungi_credenza(codice, nome, categoria, quantita, prezzo, scadenza):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO credenza VALUES (?,?,?,?,?,?,?)''',
              (codice or "N/A", nome, categoria or "Altro", int(quantita), float(prezzo or 0), 
               scadenza or "N/D", datetime.now().strftime("%d/%m/%Y %H:%M")))
    conn.commit()
    conn.close()

def aggiungi_lista(nome, categoria, quantita, prezzo):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO lista_spesa (nome, categoria, quantita, prezzo, data_inserimento)
                 VALUES (?,?,?,?,?)''', (nome, categoria or "Altro", int(quantita), float(prezzo or 0),
               datetime.now().strftime("%d/%m/%Y %H:%M")))
    conn.commit()
    conn.close()

def rimuovi_credenza(nome):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM credenza WHERE nome=?", (nome,))
    conn.commit()
    conn.close()

def rimuovi_lista(id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM lista_spesa WHERE id=?", (id,))
    conn.commit()
    conn.close()

def completa_lista(id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE lista_spesa SET completato=1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

def svuota_credenza():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM credenza")
    conn.commit()
    conn.close()

def svuota_lista():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM lista_spesa")
    conn.commit()
    conn.close()

init_db()

HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>🍕 CRENZA PRO v8.0</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, Arial, sans-serif; background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); min-height: 100vh; padding: 15px; }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 20px; font-size: 2.2em; }
        .stats { background: rgba(255,255,255,0.95); border-radius: 20px; padding: 20px; margin-bottom: 25px; display: flex; justify-content: space-around; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .stat-number { font-size: 2em; font-weight: bold; color: #2563eb; }
        .stat-label { color: #64748b; font-size: 0.85em; margin-top: 5px; text-align: center; }
        .tab-buttons { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab-btn { flex: 1; padding: 15px; font-size: 16px; font-weight: bold; border: none; border-radius: 12px; cursor: pointer; }
        .tab-active { background: #2563eb; color: white; }
        .card { background: rgba(255,255,255,0.95); border-radius: 20px; padding: 25px; margin-bottom: 20px; box-shadow: 0 12px 30px rgba(0,0,0,0.2); }
        input, select { width: 100%; padding: 16px; font-size: 16px; border: 2px solid #e2e8f0; border-radius: 12px; margin-bottom: 15px; }
        input:focus, select:focus { border-color: #2563eb; outline: none; }
        .btn { padding: 16px; font-size: 16px; font-weight: bold; border: none; border-radius: 12px; cursor: pointer; margin: 5px; }
        .btn-primary { background: #10b981; color: white; width: 100%; }
        .btn-danger { background: #ef4444; color: white; width: 100%; }
        .btn-warning { background: #f59e0b; color: white; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.2); }
        .input-group { display: flex; gap: 10px; margin-bottom: 15px; }
        .input-group input, .input-group select { flex: 1; margin-bottom: 0; }
        .lista { max-height: 300px; overflow-y: auto; }
        .item { display: flex; justify-content: space-between; align-items: center; padding: 15px; margin: 8px 0; border-radius: 12px; }
        .item-completato { background: #f0fdf4; border-left: 4px solid #84cc16; opacity: 0.7; text-decoration: line-through; }
        .item-pendente { background: #fef3c7; border-left: 4px solid #f59e0b; }
        .item-nome { font-weight: bold; font-size: 1.1em; }
        .item-dettagli { color: #64748b; font-size: 0.9em; }
        .btn-small { padding: 8px 12px; font-size: 14px; width: auto; }
        .status { padding: 15px; border-radius: 12px; margin: 10px 0; text-align: center; font-weight: bold; font-size: 1.1em; display: none; }
        .status-success { background: rgba(16,185,129,0.2); color: #166534; border: 2px solid #10b981; display: block; }
        @media (max-width: 480px) { .stats, .tab-buttons, .input-group { flex-direction: column; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍕 CRENZA PRO v8.0 + 🛒 LISTA SPESA</h1>
        <div class="tab-buttons">
            <button class="tab-btn tab-active" onclick="showTab('credenza')">🍕 Credenza</button>
            <button class="tab-btn" onclick="showTab('lista')">🛒 Lista</button>
        </div>
        <div class="stats" id="stats-credenza" style="display:flex;">
            <div><div class="stat-number" id="totale_items">0</div><div>Prodotti</div></div>
            <div><div class="stat-number" id="totale_quantita">0</div><div>Qtà</div></div>
            <div><div class="stat-number" id="valore_totale">€0</div><div>Valore</div></div>
        </div>
        <div class="stats" id="stats-lista" style="display:none;">
            <div><div class="stat-number" id="lista_totale_items">0</div><div>Totale</div></div>
            <div><div class="stat-number" id="lista_da_completare">0</div><div>Da fare</div></div>
            <div><div class="stat-number" id="lista_valore_da_completare">€0</div><div>Da spendere</div></div>
        </div>
        <div id="tab-credenza" style="display:block;">
            <div class="card">
                <h3>➕ Credenza</h3>
                <input type="text" id="codice" placeholder="Codice EAN">
                <input type="text" id="nome_credenza" placeholder="Nome prodotto">
                <select id="categoria_credenza">
                    ''' + ''.join([f'<option value="{c}">{c}</option>' for c in CATGORIE]) + '''
                </select>
                <div class="input-group">
                    <input type="number" id="quantita_credenza" value="1" min="1">
                    <input type="number" id="prezzo_credenza" step="0.01" value="0">
                </div>
                <input type="date" id="scadenza_credenza">
                <div style="display:flex;gap:10px">
                    <button class="btn btn-primary" onclick="aggiungiCredenza()">➕ AGGIUNGI</button>
                    <button class="btn btn-warning" onclick="clearCredenza()">🧹 PULISCI</button>
                </div>
            </div>
            <div class="card">
                <h3>Lista Credenza (<span id="lista_count_credenza">0</span>)</h3>
                <div class="lista" id="lista_credenza"></div>
                <button class="btn btn-danger" onclick="svuotaCredenza()">🗑️ SVUOTA</button>
            </div>
        </div>
        <div id="tab-lista" style="display:none;">
            <div class="card">
                <h3>🛒 Lista Spesa</h3>
                <input type="text" id="nome_lista" placeholder="Prodotto da comprare">
                <select id="categoria_lista">
                    ''' + ''.join([f'<option value="{c}">{c}</option>' for c in CATGORIE]) + '''
                </select>
                <div class="input-group">
                    <input type="number" id="quantita_lista" value="1" min="1">
                    <input type="number" id="prezzo_lista" step="0.01" value="0">
                </div>
                <div style="display:flex;gap:10px">
                    <button class="btn btn-primary" onclick="aggiungiLista()">➕ LISTA</button>
                    <button class="btn btn-warning" onclick="clearLista()">🧹 PULISCI</button>
                </div>
            </div>
            <div class="card">
                <h3>Lista Spesa (<span id="lista_count_lista">0</span>)</h3>
                <div class="lista" id="lista_spesa"></div>
                <button class="btn btn-danger" onclick="svuotaLista()">🗑️ SVUOTA</button>
            </div>
        </div>
        <div class="status" id="status"></div>
    </div>
    <script>
        let currentTab = "credenza";
        
        function showStatus(msg, tipo = "success") {
            const status = document.getElementById("status");
            status.textContent = msg;
            status.className = `status status-${tipo}`;
            status.style.display = "block";
            setTimeout(() => status.style.display = "none", 2000);
        }
        
        function showTab(tab) {
            currentTab = tab;
            document.getElementById("tab-credenza").style.display = tab === "credenza" ? "block" : "none";
            document.getElementById("tab-lista").style.display = tab === "lista" ? "block" : "none";
            document.getElementById("stats-credenza").style.display = tab === "credenza" ? "flex" : "none";
            document.getElementById("stats-lista").style.display = tab === "lista" ? "flex" : "none";
            document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("tab-active"));
            event.target.classList.add("tab-active");
            if (tab === "credenza") aggiornaCredenza();
            else aggiornaLista();
        }
        
        function clearCredenza() {
            document.getElementById("codice").value = "";
            document.getElementById("nome_credenza").value = "";
            document.getElementById("quantita_credenza").value = "1";
            document.getElementById("prezzo_credenza").value = "0";
            document.getElementById("scadenza_credenza").value = "";
            document.getElementById("nome_credenza").focus();
        }
        
        function clearLista() {
            document.getElementById("nome_lista").value = "";
            document.getElementById("quantita_lista").value = "1";
            document.getElementById("prezzo_lista").value = "0";
            document.getElementById("nome_lista").focus();
        }
        
        function aggiungiCredenza() {
            const dati = {
                azione: "aggiungi_credenza",
                codice: document.getElementById("codice").value,
                nome: document.getElementById("nome_credenza").value.trim(),
                categoria: document.getElementById("categoria_credenza").value,
                quantita: parseInt(document.getElementById("quantita_credenza").value),
                prezzo: parseFloat(document.getElementById("prezzo_credenza").value),
                scadenza: document.getElementById("scadenza_credenza").value
            };
            if (!dati.nome) return showStatus("❌ Nome obbligatorio!", "error");
            fetch("/", {method: "POST", headers:{"Content-Type": "application/json"}, body: JSON.stringify(dati)})
            .then(() => {
                clearCredenza();
                showStatus("✅ Aggiunto alla credenza!");
                aggiornaCredenza();
            });
        }
        
        function aggiungiLista() {
            const dati = {
                azione: "aggiungi_lista",
                nome: document.getElementById("nome_lista").value.trim(),
                categoria: document.getElementById("categoria_lista").value,
                quantita: parseInt(document.getElementById("quantita_lista").value),
                prezzo: parseFloat(document.getElementById("prezzo_lista").value)
            };
            if (!dati.nome) return showStatus("❌ Nome obbligatorio!", "error");
            fetch("/", {method: "POST", headers:{"Content-Type": "application/json"}, body: JSON.stringify(dati)})
            .then(() => {
                clearLista();
                showStatus("✅ Aggiunto alla lista!");
                aggiornaLista();
            });
        }
        
        function aggiornaCredenza() {
            fetch("/dati_credenza").then(r => r.json()).then(data => {
                document.getElementById("totale_items").textContent = data.stats.totale_items;
                document.getElementById("totale_quantita").textContent = data.stats.totale_quantita;
                document.getElementById("valore_totale").textContent = "€" + data.stats.valore_totale.toFixed(2);
                document.getElementById("lista_count_credenza").textContent = data.items.length;
                document.getElementById("lista_credenza").innerHTML = data.items.map(item => 
                    `<div class="item">
                        <div>
                            <div class="item-nome">${item.nome} <small style="color:#2563eb">${item.categoria}</small></div>
                            <div class="item-dettagli">Q:${item.quantita} €${(item.prezzo*item.quantita).toFixed(2)} ${item.scadenza}</div>
                        </div>
                        <button class="btn btn-warning btn-small" onclick="rimuoviCredenza('${item.nome.replace(/'/g,"\\\\'")}')">🗑️</button>
                    </div>`).reverse().join("");
            });
        }
        
        function aggiornaLista() {
            fetch("/dati_lista").then(r => r.json()).then(data => {
                document.getElementById("lista_totale_items").textContent = data.stats.totale_items;
                document.getElementById("lista_da_completare").textContent = data.stats.totale_da_completare;
                document.getElementById("lista_valore_da_completare").textContent = "€" + data.stats.valore_da_completare.toFixed(2);
                document.getElementById("lista_count_lista").textContent = data.items.length;
                document.getElementById("lista_spesa").innerHTML = data.items.map(item => 
                    `<div class="item ${item.completato ? 'item-completato' : 'item-pendente'}">
                        <div>
                            <div class="item-nome">${item.nome} <small style="color:#2563eb">${item.categoria}</small></div>
                            <div class="item-dettagli">Q:${item.quantita} €${(item.prezzo*item.quantita).toFixed(2)}</div>
                        </div>
                        <div>
                            ${!item.completato ? `<button class="btn btn-success btn-small" onclick="completaLista(${item.id})">✅</button>` : ''}
                            <button class="btn btn-warning btn-small" onclick="rimuoviLista(${item.id})">🗑️</button>
                        </div>
                    </div>`).reverse().join("");
            });
        }
        
        function rimuoviCredenza(nome) {
            if(confirm("Rimuovere?")) {
                fetch("/", {method: "POST", headers:{"Content-Type": "application/json"}, 
                    body: JSON.stringify({azione: "rimuovi_credenza", nome})})
                .then(() => {showStatus("Rimosso!"); aggiornaCredenza();});
            }
        }
        
        function rimuoviLista(id) {
            if(confirm("Rimuovere?")) {
                fetch("/", {method: "POST", headers:{"Content-Type": "application/json"}, 
                    body: JSON.stringify({azione: "rimuovi_lista", id})})
                .then(() => {showStatus("Rimosso!"); aggiornaLista();});
            }
        }
        
        function completaLista(id) {
            fetch("/", {method: "POST", headers:{"Content-Type": "application/json"}, 
                body: JSON.stringify({azione: "completa_lista", id})})
            .then(() => {showStatus("Completato!"); aggiornaLista();});
        }
        
        function svuotaCredenza() {
            if(confirm("SVUOTARE TUTTO?")) {
                fetch("/", {method: "POST", headers:{"Content-Type": "application/json"}, 
                    body: JSON.stringify({azione: "cancella_credenza"})})
                .then(() => {showStatus("Svuotata!"); aggiornaCredenza();});
            }
        }
        
        function svuotaLista() {
            if(confirm("SVUOTARE LISTA?")) {
                fetch("/", {method: "POST", headers:{"Content-Type": "application/json"}, 
                    body: JSON.stringify({azione: "cancella_lista"})})
                .then(() => {showStatus("Lista svuotata!"); aggiornaLista();});
            }
        }
        
        document.addEventListener("DOMContentLoaded", function() {
            document.getElementById("scadenza_credenza").valueAsDate = new Date();
            document.getElementById("nome_credenza").focus();
            aggiornaCredenza();
            setInterval(() => currentTab === "credenza" ? aggiornaCredenza() : aggiornaLista(), 3000);
        });
    </script>
</body>
</html>'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        data = request.get_json()
        azione = data.get('azione')
        if azione == 'aggiungi_credenza':
            aggiungi_credenza(data.get('codice'), data.get('nome'), data.get('categoria'), data.get('quantita'), data.get('prezzo'), data.get('scadenza'))
        elif azione == 'aggiungi_lista':
            aggiungi_lista(data.get('nome'), data.get('categoria'), data.get('quantita'), data.get('prezzo'))
        elif azione == 'rimuovi_credenza':
            rimuovi_credenza(data.get('nome'))
        elif azione == 'rimuovi_lista':
            rimuovi_lista(data.get('id'))
        elif azione == 'completa_lista':
            completa_lista(data.get('id'))
        elif azione == 'cancella_credenza':
            svuota_credenza()
        elif azione == 'cancella_lista':
            svuota_lista()
        return jsonify({'status': 'ok'})
    return HTML

@app.route('/dati_credenza')
def dati_credenza():
    return jsonify(get_dati_credenza())

@app.route('/dati_lista')
def dati_lista():
    return jsonify(get_lista_spesa())

if __name__ == '__main__':
    print("🚀 CRENZA PRO v8.0 AVVIATA!")
    print("📱 Apri: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
