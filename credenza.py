from flask import Flask, request, render_template_string, jsonify
from datetime import datetime
import sqlite3
import pandas as pd
import re

app = Flask(__name__)
DB_FILE = "credenza.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS credenza 
                 (codice TEXT, nome TEXT, quantita INTEGER DEFAULT 0, 
                  prezzo REAL DEFAULT 0, scadenza TEXT, data_inserimento TEXT,
                  PRIMARY KEY (codice, nome))''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_spesa 
                 (nome TEXT PRIMARY KEY, quantita INTEGER DEFAULT 1, 
                  prezzo_unitario REAL DEFAULT 0, totale REAL DEFAULT 0,
                  data_aggiunta TEXT)''')
    conn.commit()
    conn.close()

def get_dati():
    conn = sqlite3.connect(DB_FILE)
    df_credenza = pd.read_sql_query("SELECT * FROM credenza ORDER BY data_inserimento DESC", conn)
    df_lista = pd.read_sql_query("SELECT * FROM lista_spesa ORDER BY data_aggiunta DESC", conn)
    conn.close()
    
    stats_credenza = {}
    if not df_credenza.empty:
        stats_credenza = {
            "totale_items": len(df_credenza),
            "totale_quantita": int(df_credenza['quantita'].sum()),
            "valore_totale": round((df_credenza['prezzo'] * df_credenza['quantita']).sum(), 2)
        }
    
    stats_lista = {}
    if not df_lista.empty:
        stats_lista = {
            "totale_items": len(df_lista),
            "totale_costo": round(df_lista['totale'].sum(), 2)
        }
    
    return {
        "credenza": {"items": df_credenza.to_dict('records'), "stats": stats_credenza},
        "lista_spesa": {"items": df_lista.to_dict('records'), "stats": stats_lista}
    }

def aggiungi_item(codice, nome, quantita, prezzo, scadenza):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO credenza 
                 (codice, nome, quantita, prezzo, scadenza, data_inserimento) 
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (codice or "N/A", nome, int(quantita), float(prezzo or 0), 
               scadenza or "N/D", datetime.now().strftime("%d/%m/%Y %H:%M")))
    conn.commit()
    conn.close()

def rimuovi_item(nome, tabella="credenza"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"DELETE FROM {tabella} WHERE nome=?", (nome,))
    conn.commit()
    conn.close()

def cancella_tutto(tabella="credenza"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"DELETE FROM {tabella}")
    conn.commit()
    conn.close()

def aggiungi_lista_spesa(nome, quantita, prezzo_unitario):
    totale = float(quantita) * float(prezzo_unitario or 0)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO lista_spesa 
                 (nome, quantita, prezzo_unitario, totale, data_aggiunta) 
                 VALUES (?, ?, ?, ?, ?)''',
              (nome, int(quantita), float(prezzo_unitario or 0), totale,
               datetime.now().strftime("%d/%m/%Y %H:%M")))
    conn.commit()
    conn.close()

init_db()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🍕 CRENZA PRO WEB v5.0 🛒 LISTA SPESA + TOTALE</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="mobile-web-app-capable" content="yes">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif; 
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            min-height: 100vh; padding: 15px;
        }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 20px; font-size: 2.2em; }
        
        .tab-buttons { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab-btn { flex: 1; padding: 15px; font-size: 16px; font-weight: bold; 
                  border: none; border-radius: 12px; cursor: pointer; }
        .tab-btn.active { background: rgba(255,255,255,0.9); color: #2563eb; }
        .tab-btn:not(.active) { background: rgba(255,255,255,0.3); color: white; }
        
        .stats { 
            background: rgba(255,255,255,0.95); border-radius: 20px; padding: 20px; 
            margin-bottom: 25px; display: flex; justify-content: space-around;
        }
        .stat-number { font-size: 2.2em; font-weight: bold; }
        .stat-label { color: #64748b; font-size: 0.9em; margin-top: 5px; }
        .credenza .stat-number { color: #10b981; }
        .lista .stat-number { color: #ef4444; }
        
        .card { 
            background: rgba(255,255,255,0.95); border-radius: 20px; padding: 25px; 
            margin-bottom: 20px; box-shadow: 0 12px 30px rgba(0,0,0,0.2);
            display: none;
        }
        .card.active { display: block; }
        input { 
            width: 100%; padding: 16px; font-size: 16px; border: 2px solid #e2e8f0; 
            border-radius: 12px; margin-bottom: 15px; font-family: inherit;
        }
        input:focus { border-color: #2563eb; outline: none; }
        
        .btn { 
            padding: 16px; font-size: 16px; font-weight: bold; border: none; 
            border-radius: 12px; cursor: pointer; margin-bottom: 10px; font-family: inherit;
        }
        .btn-primary { background: #10b981; color: white; width: 48%; }
        .btn-danger { background: #ef4444; color: white; width: 48%; }
        .btn-warning { background: #f59e0b; color: white; }
        .btn-success { background: #84cc16; color: white; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.2); }
        .btn-full { width: 100%; }
        .btn-group { display: flex; gap: 10px; }
        .btn-small { padding: 8px 12px; font-size: 14px; width: auto; }
        
        .input-group { display: flex; gap: 10px; margin-bottom: 15px; }
        .input-group input { flex: 1; }
        
        .lista { max-height: 400px; overflow-y: auto; }
        .item { 
            display: flex; justify-content: space-between; align-items: center;
            background: #f8fafc; padding: 15px; margin: 8px 0; 
            border-radius: 12px; border-left: 4px solid #2563eb;
        }
        .item-nome { font-weight: bold; font-size: 1.1em; }
        .item-dettagli { color: #64748b; font-size: 0.9em; }
        .item-totale { font-weight: bold; color: #ef4444; font-size: 1.2em; }
        
        .status { padding: 12px; border-radius: 12px; margin: 10px 0; text-align: center; font-weight: bold; }
        .status-success { background: rgba(16,185,129,0.2); color: #166534; }
        
        @media (max-width: 480px) {
            .stats, .tab-buttons, .btn-group, .input-group { flex-direction: column; gap: 10px; }
            .btn-primary, .btn-danger { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍕 CRENZA PRO WEB v5.0 🛒 LISTA SPESA + TOTALE</h1>
        
        <div class="tab-buttons">
            <button class="tab-btn active" onclick="switchTab('credenza')">🍕 Credenza</button>
            <button class="tab-btn" onclick="switchTab('lista')">🛒 Lista Spesa</button>
        </div>
        
        <!-- STATS DINAMICHE -->
        <div class="stats credenza-stats" id="stats-credenza">
            <div><div class="stat-number" id="credenza_items">0</div><div>Prodotti</div></div>
            <div><div class="stat-number" id="credenza_quantita">0</div><div>Quantità</div></div>
            <div><div class="stat-number" id="credenza_valore">€0</div><div>Valore</div></div>
        </div>
        <div class="stats lista-stats" id="stats-lista" style="display:none;">
            <div><div class="stat-number" id="lista_items">0</div><div>Prodotti</div></div>
            <div><div class="stat-number" id="lista_totale">€0</div><div>TOTALE SPESA</div></div>
            <div><div class="stat-number" id="lista_quantita">0</div><div>Quantità</div></div>
        </div>
        
        <!-- CRENZA -->
        <div class="card active" id="card-credenza">
            <h3>➕ Aggiungi alla Credenza</h3>
            <input type="text" id="codice" placeholder="🔍 Codice EAN (opzionale)">
            <input type="text" id="nome_credenza" placeholder="📦 Nome prodotto *obbligatorio">
            <div class="input-group">
                <input type="number" id="quantita_credenza" value="1" min="1" max="99" placeholder="Q.tà">
                <input type="number" id="prezzo_credenza" step="0.01" value="0.00" placeholder="€/unità">
            </div>
            <input type="date" id="scadenza">
            <div class="btn-group">
                <button class="btn btn-primary" onclick="aggiungiCredenza()">➕ Credenza</button>
                <button class="btn btn-success" onclick="aggiungiListaDaCredenza()">🛒 Lista Spesa</button>
            </div>
            <button class="btn btn-danger btn-full" onclick="cancellaTutto('credenza')">🗑️ Svuota Credenza</button>
            
            <h4 style="margin: 25px 0 15px 0;">📦 Prodotti in Credenza (<span id="lista_credenza_count">0</span>)</h4>
            <div class="lista" id="lista_credenza"></div>
        </div>
        
        <!-- LISTA SPESA -->
        <div class="card" id="card-lista">
            <h3>🛒 Aggiungi alla Lista Spesa</h3>
            <input type="text" id="nome_lista" placeholder="🛒 Nome prodotto *obbligatorio">
            <div class="input-group">
                <input type="number" id="quantita_lista" value="1" min="1" max="99" placeholder="Q.tà">
                <input type="number" id="prezzo_lista" step="0.01" value="0.00" placeholder="€/unità">
            </div>
            <div class="btn-group">
                <button class="btn btn-primary" onclick="aggiungiLista()">➕ Lista Spesa</button>
                <button class="btn btn-warning" onclick="spuntaLista()">✅ Spunta & Cancella</button>
            </div>
            <button class="btn btn-danger btn-full" onclick="cancellaTutto('lista_spesa')">🗑️ Svuota Lista</button>
            
            <h4 style="margin: 25px 0 15px 0;">🛒 Lista Spesa Attuale (<span id="lista_spesa_count">0</span>)</h4>
            <div class="lista" id="lista_spesa"></div>
        </div>
    </div>

    <script>
        let currentTab = 'credenza';
        
        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            document.querySelectorAll('.card').forEach(card => card.classList.remove('active'));
            document.getElementById(`card-${tab}`).classList.add('active');
            
            document.getElementById('stats-credenza').style.display = tab === 'credenza' ? 'flex' : 'none';
            document.getElementById('stats-lista').style.display = tab === 'lista' ? 'flex' : 'none';
        }
        
        function aggiornaUI() {
            fetch('/dati')
                .then(r => r.json())
                .then(data => {
                    // Credenza
                    const cred = data.credenza;
                    document.getElementById('credenza_items').textContent = cred.stats.totale_items || 0;
                    document.getElementById('credenza_quantita').textContent = cred.stats.totale_quantita || 0;
                    document.getElementById('credenza_valore').textContent = '€' + (cred.stats.valore_totale || 0).toFixed(2);
                    document.getElementById('lista_credenza_count').textContent = cred.items.length;
                    
                    document.getElementById('lista_credenza').innerHTML = cred.items.map(item => 
                        `<div class="item">
                            <div>
                                <div class="item-nome">${item.nome}</div>
                                <div class="item-dettagli">
                                    ${item.codice !== 'N/A' ? `Cod: ${item.codice} | ` : ''}
                                    Q.tà: ${item.quantita} | €${item.prezzo.toFixed(2)}/un | 
                                    ${item.scadenza !== 'N/D' ? `Scad: ${item.scadenza}` : 'Nessuna'}
                                </div>
                            </div>
                            <div>
                                <button class="btn btn-warning btn-small" onclick="rimuovi('${item.nome.replace(/'/g, "\\\\'")}', 'credenza')">➖</button>
                                <button class="btn btn-success btn-small" style="margin-left:5px;" onclick="aggiungiListaDaCredenza('${item.nome.replace(/'/g, "\\\\'")}')">🛒</button>
                            </div>
                        </div>`
                    ).reverse().join('');
                    
                    // Lista Spesa
                    const lista = data.lista_spesa;
                    document.getElementById('lista_items').textContent = lista.stats.totale_items || 0;
                    document.getElementById('lista_totale').textContent = '€' + (lista.stats.totale_costo || 0).toFixed(2);
                    document.getElementById('lista_quantita').textContent = lista.items.reduce((sum, item) => sum + item.quantita, 0);
                    document.getElementById('lista_spesa_count').textContent = lista.items.length;
                    
                    document.getElementById('lista_spesa').innerHTML = lista.items.map(item => 
                        `<div class="item">
                            <div>
                                <div class="item-nome">${item.nome}</div>
                                <div class="item-dettagli">
                                    Q.tà: ${item.quantita} | €${item.prezzo_unitario.toFixed(2)}/un
                                </div>
                            </div>
                            <div>
                                <span class="item-totale">€${item.totale.toFixed(2)}</span>
                                <button class="btn btn-warning btn-small" style="margin-left:10px;" onclick="rimuovi('${item.nome.replace(/'/g, "\\\\'")}', 'lista_spesa')">➖</button>
                            </div>
                        </div>`
                    ).reverse().join('');
                });
        }
        
        function aggiungiCredenza() {
            const codice = document.getElementById('codice').value;
            const nome = document.getElementById('nome_credenza').value.trim();
            const quantita = document.getElementById('quantita_credenza').value;
            const prezzo = document.getElementById('prezzo_credenza').value;
            const scadenza = document.getElementById('scadenza').value;
            
            if (!nome) return alert('❌ Nome obbligatorio!');
            
            fetch('/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    azione: 'aggiungi_credenza',
                    codice, nome, quantita, prezzo, scadenza
                })
            }).then(() => {
                resetFormCredenza();
                aggiornaUI();
            });
        }
        
        function aggiungiLista() {
            const nome = document.getElementById('nome_lista').value.trim();
            const quantita = document.getElementById('quantita_lista').value;
            const prezzo = document.getElementById('prezzo_lista').value;
            
            if (!nome) return alert('❌ Nome obbligatorio!');
            
            fetch('/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    azione: 'aggiungi_lista',
                    nome, quantita, prezzo_unitario: prezzo
                })
            }).then(() => {
                resetFormLista();
                aggiornaUI();
            });
        }
        
        function aggiungiListaDaCredenza(nome = null) {
            if (!nome) {
                nome = document.getElementById('nome_credenza').value.trim();
                if (!nome) return alert('❌ Seleziona un prodotto dalla credenza!');
            }
            
            fetch('/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    azione: 'da_credenza_a_lista',
                    nome
                })
            }).then(aggiornaUI);
        }
        
        function rimuovi(nome, tabella) {
            fetch('/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({azione: 'rimuovi', nome, tabella})
            }).then(aggiornaUI);
        }
        
        function spuntaLista() {
            if (confirm('✅ Spuntare e CANCELLARE tutta la lista spesa?')) {
                fetch('/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({azione: 'cancella_tutto', tabella: 'lista_spesa'})
                }).then(aggiornaUI);
            }
        }
        
        function cancellaTutto(tabella) {
            if (confirm(`🗑️ Svuotare ${tabella === 'credenza' ? 'Credenza' : 'Lista Spesa'}?`)) {
                fetch('/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({azione: 'cancella_tutto', tabella})
                }).then(aggiornaUI);
            }
        }
        
        function resetFormCredenza() {
            document.getElementById('codice').value = '';
            document.getElementById('nome_credenza').value = '';
            document.getElementById('prezzo_credenza').value = '0.00';
            document.getElementById('quantita_credenza').value = '1';
            document.getElementById('scadenza').value = '';
            document.getElementById('nome_credenza').focus();
        }
        
        function resetFormLista() {
            document.getElementById('nome_lista').value = '';
            document.getElementById('prezzo_lista').value = '0.00';
            document.getElementById('quantita_lista').value = '1';
            document.getElementById('nome_lista').focus();
        }
        
        // INIZIALIZZAZIONE
        document.getElementById('scadenza').valueAsDate = new Date();
        aggiornaUI();
        setInterval(aggiornaUI, 2000);
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        data = request.get_json()
        azione = data.get('azione')
        
        if azione == 'aggiungi_credenza':
            aggiungi_item(data.get('codice'), data.get('nome'), data.get('quantita'),
                         data.get('prezzo'), data.get('scadenza'))
        elif azione == 'aggiungi_lista':
            aggiungi_lista_spesa(data.get('nome'), data.get('quantita'), data.get('prezzo_unitario'))
        elif azione == 'da_credenza_a_lista':
            # Copia dalla credenza alla lista (1 unità)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT prezzo FROM credenza WHERE nome=?", (data.get('nome'),))
            result = c.fetchone()
            prezzo = result[0] if result else 0
            aggiungi_lista_spesa(data.get('nome'), 1, prezzo)
            conn.close()
        elif azione == 'rimuovi':
            rimuovi_item(data.get('nome'), data.get('tabella', 'credenza'))
        elif azione == 'cancella_tutto':
            cancella_tutto(data.get('tabella', 'credenza'))
        
        return jsonify({'status': 'ok'})
    
    return render_template_string(HTML)

@app.route('/dati')
def dati_json():
    return jsonify(get_dati())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
