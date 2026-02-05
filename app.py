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

def clear_all():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM credenza")
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🍕 CRENZA PRO</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { 
            text-align: center; color: white; 
            font-size: clamp(1.8rem, 5vw, 3rem); 
            margin-bottom: 30px; text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        .stats { 
            background: rgba(255,255,255,0.95); 
            border-radius: 20px; padding: 20px; margin-bottom: 30px; 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .stat { text-align: center; }
        .stat-value { font-size: 2rem; font-weight: bold; color: #667eea; }
        .form-section { 
            background: rgba(255,255,255,0.95); border-radius: 20px; 
            padding: 25px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .form-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr auto auto; gap: 15px; margin-bottom: 15px; }
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
        .totale { font-size: 1.5rem; font-weight: bold; color: #28a745; text-align: right; padding: 20px; }
        @media (max-width: 768px) {
            .form-row { grid-template-columns: 1fr; }
            table { font-size: 14px; }
            th, td { padding: 12px 8px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍕 Gestione Credenza Pro</h1>
        
        <div class="stats">
            <div class="stat"><div class="stat-value" id="tot_items">0</div><div>Prodotti</div></div>
            <div class="stat"><div class="stat-value" id="tot_qta">0</div><div>Quantità</div></div>
            <div class="stat"><div class="stat-value" id="tot_valore">€0,00</div><div>Valore Totale</div></div>
        </div>

        <div class="form-section">
            <div class="form-row">
                <input type="text" id="codice" placeholder="Codice (es: 001)" maxlength="20">
                <input type="text" id="nome" placeholder="Nome prodotto" required>
                <input type="number" id="quantita" placeholder="Q.tà" min="1" value="1">
                <input type="number" id="prezzo" placeholder="Prezzo €" step="0.01" min="0">
                <input type="date" id="scadenza">
                <button onclick="addItem()">➕ AGGIUNGI</button>
            </div>
        </div>

        <div class="table-container">
            <table id="tabella">
                <thead>
                    <tr>
                        <th>Codice</th><th>Prodotto</th><th>Q.tà</th><th>Prezzo</th>
                        <th>Scadenza</th><th>Data</th><th></th>
                    </tr>
                </thead>
                <tbody id="tbody"></tbody>
            </table>
            <div class="totale" id="totale_finale">€0,00</div>
        </div>

        <div style="text-align: center; margin-top: 30px;">
            <button class="danger" onclick="clearAll()" style="padding: 15px 40px; font-size: 18px;">
                🗑️ CANCELLA TUTTO
            </button>
        </div>
    </div>

    <script>
        let items = {{ items|tojson }};
        
        function updateTable() {
            let tbody = document.getElementById('tbody');
            let tot_items = 0, tot_qta = 0, tot_val = 0;
            
            tbody.innerHTML = '';
            items.forEach((item, index) => {
                let row = tbody.insertRow();
                row.innerHTML = `
                    <td>${item.codice}</td>
                    <td>${item.nome}</td>
                    <td>
                        <div class="qty-controls">
                            <button class="qty-btn qty-minus" onclick="changeQty(${index}, -1)">−</button>
                            <span style="min-width: 30px; text-align: center;">${item.quantita}</span>
                            <button class="qty-btn qty-plus" onclick="changeQty(${index}, +1)">+</button>
                        </div>
                    </td>
                    <td>€${(item.prezzo * item.quantita).toFixed(2)}</td>
                    <td>${item.scadenza || ''}</td>
                    <td>${item.data}</td>
                    <td><button class="delete-btn" onclick="deleteItem(${index})">🗑️</button></td>
                `;
                tot_items++;
                tot_qta += item.quantita;
                tot_val += item.prezzo * item.quantita;
            });
            
            document.getElementById('tot_items').textContent = tot_items;
            document.getElementById('tot_qta').textContent = tot_qta;
            document.getElementById('tot_valore').textContent = '€' + tot_val.toFixed(2);
            document.getElementById('totale_finale').textContent = '€' + tot_val.toFixed(2);
        }
        
        function addItem() {
            let codice = document.getElementById('codice').value.trim();
            let nome = document.getElementById('nome').value.trim();
            let quantita = parseInt(document.getElementById('quantita').value);
            let prezzo = parseFloat(document.getElementById('prezzo').value) || 0;
            let scadenza = document.getElementById('scadenza').value;
            
            if (!nome || quantita < 1) return alert('Nome e quantità obbligatori!');
            
            fetch('/add', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({codice, nome, quantita, prezzo, scadenza})
            }).then(r => r.json()).then(data => {
                items = data.items;
                updateTable();
                document.getElementById('codice').value = '';
                document.getElementById('nome').value = '';
                document.getElementById('quantita').value = '1';
                document.getElementById('prezzo').value = '';
                document.getElementById('scadenza').value = '';
            });
        }
        
        function changeQty(index, delta) {
            if (items[index].quantita + delta < 1) return;
            items[index].quantita += delta;
            fetch('/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(items[index])
            }).then(r => r.json()).then(data => {
                items = data.items;
                updateTable();
            });
        }
        
        function deleteItem(index) {
            if (confirm('Eliminare ' + items[index].nome + '?')) {
                fetch('/delete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({nome: items[index].nome})
                }).then(r => r.json()).then(data => {
                    items = data.items;
                    updateTable();
                });
            }
        }
        
        function clearAll() {
            if (confirm('Cancellare TUTTA la credenza?')) {
                fetch('/clear').then(r => r.json()).then(data => {
                    items = [];
                    updateTable();
                });
            }
        }
        
        updateTable();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    items, totale = get_credenza()
    return render_template_string(HTML_TEMPLATE, items=items)

@app.route('/add', methods=['POST'])
def add_item():
    data = request.json
    save_item(data['codice'], data['nome'], data['quantita'], data['prezzo'], data['scadenza'])
    items, _ = get_credenza()
    return {'items': items}

@app.route('/update', methods=['POST'])
def update_item():
    data = request.json
    save_item(data['codice'], data['nome'], data['quantita'], data['prezzo'], data['scadenza'])
    items, _ = get_credenza()
    return {'items': items}

@app.route('/delete', methods=['POST'])
def delete_item_route():
    data = request.json
    delete_item(data['nome'])
    items, _ = get_credenza()
    return {'items': items}

@app.route('/clear', methods=['POST'])
def clear_all_route():
    clear_all()
    return {'items': []}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
