from flask import Flask, request, render_template_string
import sqlite3, os, json
from datetime import datetime

app = Flask(__name__)
DB_PATH = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', '/app/db/credenza.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS credenza 
                 (codice TEXT, nome TEXT, quantita INTEGER, prezzo REAL, 
                  scadenza TEXT, data_inserimento TEXT, 
                  PRIMARY KEY (codice, nome))''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_spesa 
                 (nome TEXT PRIMARY KEY, quantita INTEGER DEFAULT 1, 
                  data_inserimento TEXT)''')
    conn.commit()
    conn.close()

def get_credenza():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM credenza ORDER BY data_inserimento DESC")
    items = []
    totale = 0
    for row in c.fetchall():
        item = {
            'codice': row[0] or '', 'nome': row[1], 'quantita': row[2],
            'prezzo': row[3] or 0, 'scadenza': row[4] or '', 'data': row[5]
        }
        totale += item['prezzo'] * item['quantita']
        items.append(item)
    conn.close()
    return items, round(totale, 2)

def get_lista_spesa():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM lista_spesa ORDER BY data_inserimento DESC")
    items = []
    for row in c.fetchall():
        items.append({'nome': row[0], 'quantita': row[1], 'data': row[2]})
    conn.close()
    return items

def save_item(codice, nome, quantita, prezzo, scadenza):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO credenza 
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (codice, nome, quantita, prezzo, scadenza, 
               datetime.now().strftime('%d/%m/%Y %H:%M')))
    conn.commit()
    conn.close()

def delete_item(nome):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM credenza WHERE nome=?", (nome,))
    conn.commit()
    conn.close()

def clear_all(table):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()

def add_lista_spesa(nome, quantita):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO lista_spesa 
                 VALUES (?, ?, ?)''',
              (nome, quantita, datetime.now().strftime('%d/%m/%Y %H:%M')))
    conn.commit()
    conn.close()

def delete_lista_item(nome):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM lista_spesa WHERE nome=?", (nome,))
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🍕 CRENZA PRO + LISTA SPESA</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { 
            text-align: center; color: white; 
            font-size: clamp(1.8rem, 5vw, 3rem); 
            margin-bottom: 30px; text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        .tabs { 
            display: flex; background: rgba(255,255,255,0.95); 
            border-radius: 20px 20px 0 0; margin-bottom: 0; overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }
        .tab-btn { 
            flex: 1; padding: 20px; background: none; border: none; 
            font-size: 18px; font-weight: 600; cursor: pointer; 
            transition: all 0.3s ease;
        }
        .tab-btn.active { background: #667eea; color: white; }
        .tab-btn:hover { background: rgba(102,126,234,0.2); }
        
        .section { 
            background: rgba(255,255,255,0.95); 
            border-radius: 0 0 20px 20px; padding: 25px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2); display: none;
        }
        .section.active { display: block; }
        
        .stats { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 15px; margin-bottom: 30px;
        }
        .stat { 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            color: white; padding: 20px; border-radius: 15px; text-align: center;
        }
        .stat-value { font-size: 2rem; font-weight: bold; }
        
        .form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 15px; }
        input, button { 
            padding: 15px; border: 2px solid #e1e5e9; border-radius: 12px; 
            font-size: 16px; transition: all 0.3s ease;
        }
        input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.1); }
        button { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; border: none; cursor: pointer; font-weight: 600;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(102,126,234,0.4); }
        button.danger { background: linear-gradient(135deg, #ff6b6b, #ee5a52); }
        
        .table-container { 
            background: rgba(255,255,255,0.95); border-radius: 20px; 
            overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 18px 15px; text-align: left; border-bottom: 1px solid #e1e5e9; }
        th { background: #f8f9fa; font-weight: 600; color: #495057; }
        .qty-controls { display: flex; gap: 5px; }
        .qty-btn { width: 40px; height: 40px; border-radius: 8px; font-weight: bold; }
        .qty-plus { background: #28a745; }
        .qty-minus { background: #dc3545; }
        .delete-btn { background: #ff6b6b; padding: 10px 15px; }
        
        .totale { font-size: 1.5rem; font-weight: bold; color: #28a745; text-align: right; padding: 20px; background: #f8f9fa; }
        
        @media (max-width: 768px) {
            .form-row { grid-template-columns: 1fr; }
            table { font-size: 14px; }
            th, td { padding: 12px 8px; }
            .tabs { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍕 Credenza Pro + Lista Spesa</h1>
        
        <div class="tabs">
            <button class="tab-btn active" onclick="showTab('credenza')">🥫 Credenza</button>
            <button class="tab-btn" onclick="showTab('lista')">🛒 Lista Spesa</button>
        </div>

        <!-- SEZIONE CRENZA -->
        <div id="credenza" class="section active">
            <div class="stats">
                <div class="stat"><div class="stat-value" id="tot_items_c">0</div><div>Prodotti</div></div>
                <div class="stat"><div class="stat-value" id="tot_qta_c">0</div><div>Quantità</div></div>
                <div class="stat"><div class="stat-value" id="tot_valore_c">€0,00</div><div>Valore</div></div>
            </div>

            <div class="form-row">
                <input type="text" id="codice_c" placeholder="Codice">
                <input type="text" id="nome_c" placeholder="Nome prodotto" required>
                <input type="number" id="quantita_c" value="1" min="1">
                <input type="number" id="prezzo_c" placeholder="Prezzo €" step="0.01">
                <input type="date" id="scadenza_c">
                <button onclick="addCredenza()">➕ AGGIUNGI</button>
            </div>

            <div class="table-container">
                <table id="tabella_c">
                    <thead><tr><th>Codice</th><th>Prodotto</th><th>Q.tà</th><th>Prezzo</th><th>Scad.</th><th>Data</th><th></th></tr></thead>
                    <tbody id="tbody_c"></tbody>
                </table>
                <div class="totale" id="totale_c">€0,00</div>
            </div>
            <div style="text-align: center; margin-top: 20px;">
                <button class="danger" onclick="clearAll('credenza')" style="padding: 15px 30px;">🗑️ CANCELLA CRENZA</button>
            </div>
        </div>

        <!-- SEZIONE LISTA SPESA -->
        <div id="lista" class="section">
            <div class="stats">
                <div class="stat"><div class="stat-value" id="tot_items_l">0</div><div>Articoli</div></div>
            </div>

            <div class="form-row">
                <input type="text" id="nome_l" placeholder="Cosa comprare?" required>
                <input type="number" id="quantita_l" value="1" min="1">
                <button onclick="addLista()" style="grid-column: span 2;">➕ LISTA SPESA</button>
            </div>

            <div class="table-container">
                <table id="tabella_l">
                    <thead><tr><th>Articolo</th><th>Q.tà</th><th>Data</th><th></th></tr></thead>
                    <tbody id="tbody_l"></tbody>
                </table>
            </div>
            <div style="text-align: center; margin-top: 20px;">
                <button class="danger" onclick="clearAll('lista')" style="padding: 15px 30px;">🗑️ CANCELLA LISTA</button>
            </div>
        </div>
    </div>

    <script>
        let credenza = {{ credenza|tojson }};
        let listaSpesa = {{ lista|tojson }};
        
        function showTab(tab) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            event.target.classList.add('active');
            if (tab === 'credenza') updateCredenza();
            else updateLista();
        }
        
        function updateCredenza() {
            let tbody = document.getElementById('tbody_c');
            let tot_items = 0, tot_qta = 0, tot_val = 0;
            tbody.innerHTML = '';
            credenza.forEach((item, index) => {
                let row = tbody.insertRow();
                row.innerHTML = `
                    <td>${item.codice}</td>
                    <td>${item.nome}</td>
                    <td>
                        <div class="qty-controls">
                            <button class="qty-btn qty-minus" onclick="changeQty(${index}, -1)">−</button>
                            <span>${item.quantita}</span>
                            <button class="qty-btn qty-plus" onclick="changeQty(${index}, +1)">+</button>
                        </div>
                    </td>
                    <td>€${(item.prezzo * item.quantita).toFixed(2)}</td>
                    <td>${item.scadenza || ''}</td>
                    <td>${item.data}</td>
                    <td><button class="delete-btn" onclick="deleteCredenza(${index})">🗑️</button></td>
                `;
                tot_items++; tot_qta += item.quantita; tot_val += item.prezzo * item.quantita;
            });
            document.getElementById('tot_items_c').textContent = tot_items;
            document.getElementById('tot_qta_c').textContent = tot_qta;
            document.getElementById('tot_valore_c').textContent = '€' + tot_val.toFixed(2);
            document.getElementById('totale_c').textContent = '€' + tot_val.toFixed(2);
        }
        
        function addCredenza() {
            let data = {
                codice: document.getElementById('codice_c').value,
                nome: document.getElementById('nome_c').value,
                quantita: parseInt(document.getElementById('quantita_c').value),
                prezzo: parseFloat(document.getElementById('prezzo_c').value) || 0,
                scadenza: document.getElementById('scadenza_c').value
            };
            if (!data.nome || data.quantita < 1) return alert('Nome e quantità obbligatori!');
            
            fetch('/add_credenza', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)})
                .then(r => r.json()).then(d => {
                    credenza = d.credenza; updateCredenza();
                    document.getElementById('codice_c').value = document.getElementById('nome_c').value = 
                    document.getElementById('prezzo_c').value = document.getElementById('scadenza_c').value = '';
                    document.getElementById('quantita_c').value = '1';
                });
        }
        
        function changeQty(index, delta) {
            if (credenza[index].quantita + delta < 1) return;
            let item = credenza[index];
            item.quantita += delta;
            fetch('/update_credenza', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(item)})
                .then(r => r.json()).then(d => { credenza = d.credenza; updateCredenza(); });
        }
        
        function deleteCredenza(index) {
            if (confirm('Eliminare ' + credenza[index].nome + '?')) {
                fetch('/delete_credenza', {
                    method: 'POST', 
                    headers: {'Content-Type': 'application/json'}, 
                    body: JSON.stringify({nome: credenza[index].nome})
                }).then(r => r.json()).then(d => { credenza = d.credenza; updateCredenza(); });
            }
        }
        
        function updateLista() {
            let tbody = document.getElementById('tbody_l');
            tbody.innerHTML = '';
            let tot_items = listaSpesa.length;
            document.getElementById('tot_items_l').textContent = tot_items;
            
            listaSpesa.forEach((item, index) => {
                let row = tbody.insertRow();
                row.innerHTML = `
                    <td>${item.nome}</td>
                    <td>${item.quantita}</td>
                    <td>${item.data}</td>
                    <td><button class="delete-btn" onclick="deleteLista(${index})">✅ FATTO</button></td>
                `;
            });
        }
        
        function addLista() {
            let nome = document.getElementById('nome_l').value.trim();
            let quantita = parseInt(document.getElementById('quantita_l').value);
            if (!nome) return alert('Inserisci il nome dell\'articolo!');
            
            fetch('/add_lista', {
                method: 'POST', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify({nome, quantita})
            }).then(r => r.json()).then(d => {
                listaSpesa = d.lista; updateLista();
                document.getElementById('nome_l').value = '';
                document.getElementById('quantita_l').value = '1';
            });
        }
        
        function deleteLista(index) {
            fetch('/delete_lista', {
                method: 'POST', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify({nome: listaSpesa[index].nome})
            }).then(r => r.json()).then(d => {
                listaSpesa = d.lista; updateLista();
            });
        }
        
        function clearAll(table) {
            if (confirm(`Cancellare ${table === 'credenza' ? 'la credenza' : 'la lista spesa'}?`)) {
                fetch('/clear_all', {
                    method: 'POST', 
                    headers: {'Content-Type': 'application/json'}, 
                    body: JSON.stringify({table})
                }).then(r => r.json()).then(d => {
                    if (table === 'credenza') { credenza = []; updateCredenza(); }
                    else { listaSpesa = []; updateLista(); }
                });
            }
        }
        
        updateCredenza();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    credenza_data, _ = get_credenza()
    lista_data = get_lista_spesa()
    return render_template_string(HTML_TEMPLATE, credenza=credenza_data, lista=lista_data)

# ROTTE CRENZA (già esistenti)
@app.route('/add_credenza', methods=['POST'])
def add_item():
    data = request.json
    save_item(data['codice'], data['nome'], data['quantita'], data['prezzo'], data['scadenza'])
    items, _ = get_credenza()
    return {'credenza': items}

@app.route('/update_credenza', methods=['POST'])
def update_item():
    data = request.json
    save_item(data['codice'], data['nome'], data['quantita'], data['prezzo'], data['scadenza'])
    items, _ = get_credenza()
    return {'credenza': items}

@app.route('/delete_credenza', methods=['POST'])
def delete_item_route():
    data = request.json
    delete_item(data['nome'])
    items, _ = get_credenza()
    return {'credenza': items}

# NUOVE ROTTE LISTA SPESA
@app.route('/add_lista', methods=['POST'])
def add_lista_route():
    data = request.json
    add_lista_spesa(data['nome'], data['quantita'])
    return {'lista': get_lista_spesa()}

@app.route('/delete_lista', methods=['POST'])
def delete_lista_route():
    data = request.json
    delete_lista_item(data['nome'])
    return {'lista': get_lista_spesa()}

@app.route('/clear_all', methods=['POST'])
def clear_all_route():
    data = request.json
    clear_all(data['table'])
    if data['table'] == 'credenza': return {'credenza': []}
    else: return {'lista': []}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
