from flask import Flask, request, render_template_string, jsonify
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
DB_FILE = "/tmp/credenza.db"  # Render usa /tmp

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS credenza 
                 (codice TEXT, nome TEXT, quantita INTEGER DEFAULT 0, 
                  prezzo REAL DEFAULT 0, scadenza TEXT, data_inserimento TEXT,
                  PRIMARY KEY (codice, nome))''')
    conn.commit()
    conn.close()

def get_dati():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM credenza ORDER BY data_inserimento DESC")
    rows = c.fetchall()
    conn.close()
    
    items = []
    totale_items, totale_quantita, valore_totale = 0, 0, 0
    
    for row in rows:
        item = {
            'codice': row[0] or "N/A", 'nome': row[1], 'quantita': row[2],
            'prezzo': row[3], 'scadenza': row[4] or "N/D", 'data_inserimento': row[5]
        }
        items.append(item)
        totale_items += 1
        totale_quantita += item['quantita']
        valore_totale += item['prezzo'] * item['quantita']
    
    return {
        "items": items, 
        "stats": {
            "totale_items": totale_items,
            "totale_quantita": totale_quantita,
            "valore_totale": round(valore_totale, 2)
        }
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

def rimuovi_item(nome):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM credenza WHERE nome=?", (nome,))
    conn.commit()
    conn.close()

def cancella_tutto():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM credenza")
    conn.commit()
    conn.close()

init_db()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🍕 CRENZA PRO WEB</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding
