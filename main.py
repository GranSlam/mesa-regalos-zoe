from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
DB_NAME = "regalos.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regalos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            articulo TEXT NOT NULL,
            cupos_totales INTEGER NOT NULL,
            cupos_disponibles INTEGER NOT NULL,
            elegidos_por TEXT DEFAULT ''
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM regalos")
    if cursor.fetchone()[0] == 0:
        lista_inicial = [
            ("2 teteros pequeños antirreflujo", 1),
            ("2 teteros grandes", 1),
            ("1 esterilizador de teteros", 1),
            ("1 escurridor de teteros", 1),
            ("Baberos y cobertor", 1),
            ("Vasitos para almacenar leche materna", 1),
            ("Pañales etapa 3 X 30", 2),
            ("Pañales etapa 4 X 30", 2),
            ("Pañales etapa 5 X 30", 2),
            ("Toallitas de tela", 1),
            ("Toalla con capucha", 2),
            ("1 semanario", 1),
            ("Pijamas x 3", 2),
            ("Conjuntos cómodos", 1),
            ("Cobija liviana", 1),
            ("Cobija gruesa", 1),
            ("Juego de sabanas para la cuna", 1),
            ("Protector impermeable para colchón", 1),
            ("Muselinas para bebe", 1),
            ("Cargador fular", 2),
            ("Organizador de pañales", 1),
            ("Cesto de ropa sucia", 1),
            ("Canasta organizadora", 1),
            ("Luz nocturna para bebe", 1),
            ("Cepillo para lavar teteros", 1),
            ("Cambiador portátil", 1),
            ("Kit de cuidado (cepillo, corta uñas, aspirador nasal, etc.)", 1),
            ("Bodies manga corta", 1),
            ("Bodies manga larga", 1),
            ("Tina plegable para bebe", 1),
            ("Sleeping 3-6 meses", 1),
            ("Cojín de lactancia", 1)
        ]
        cursor.executemany("INSERT INTO regalos (articulo, cupos_totales, cupos_disponibles) VALUES (?, ?, ?)", [(r[0], r[1], r[1]) for r in lista_inicial])
        conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
def leer_regalos(request: Request, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM regalos")
    regalos = cursor.fetchall()
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "regalos": regalos})

@app.post("/reservar")
def reservar_regalo(id_regalo: int = Form(...), nombre: str = Form(...), db: sqlite3.Connection = Depends(get_db)):
    nombre = nombre.strip()
    if nombre:
        cursor = db.cursor()
        cursor.execute("SELECT cupos_disponibles, elegidos_por FROM regalos WHERE id = ?", (id_regalo,))
        regalo = cursor.fetchone()
        
        if regalo and regalo["cupos_disponibles"] > 0:
            nuevos_cupos = regalo["cupos_disponibles"] - 1
            elegidos_actuales = regalo["elegidos_por"]
            nuevos_elegidos = f"{elegidos_actuales}, {nombre}" if elegidos_actuales else nombre
            
            cursor.execute("UPDATE regalos SET cupos_disponibles = ?, elegidos_por = ? WHERE id = ?", (nuevos_cupos, nuevos_elegidos, id_regalo))
            db.commit()
            
    return RedirectResponse(url="/", status_code=303)