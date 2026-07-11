from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Toma la variable de entorno que configuramos en Render
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    if not DATABASE_URL:
        return
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regalos (
            id SERIAL PRIMARY KEY,
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
        cursor.executemany("INSERT INTO regalos (articulo, cupos_totales, cupos_disponibles) VALUES (%s, %s, %s)", [(r[0], r[1], r[1]) for r in lista_inicial])
        conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
def leer_regalos(request: Request, db = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM regalos ORDER BY id ASC")
    regalos = cursor.fetchall()
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "regalos": regalos})

@app.post("/reservar")
def reservar_regalo(id_regalo: int = Form(...), nombre: str = Form(...), db = Depends(get_db)):
    nombre = nombre.strip()
    if nombre:
        cursor = db.cursor()
        cursor.execute("SELECT cupos_disponibles, elegidos_por FROM regalos WHERE id = %s", (id_regalo,))
        regalo = cursor.fetchone()
        
        if regalo and regalo["cupos_disponibles"] > 0:
            nuevos_cupos = regalo["cupos_disponibles"] - 1
            elegidos_actuales = regalo["elegidos_por"]
            nuevos_elegidos = f"{elegidos_actuales}, {nombre}".strip(", ") if elegidos_actuales else nombre
            
            cursor.execute("UPDATE regalos SET cupos_disponibles = %s, elegidos_por = %s WHERE id = %s", (nuevos_cupos, nuevos_elegidos, id_regalo))
            db.commit()
            
    return RedirectResponse(url="/", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
def ver_resumen_admin(db = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, articulo, elegidos_por, cupos_disponibles, cupos_totales FROM regalos WHERE elegidos_por != ''")
    reservados = cursor.fetchall()
    
    html_content = "<h2 style='font-family:sans-serif;'>📋 Resumen de Regalos Apartados</h2><hr><br>"
    if not reservados:
        html_content += "<p style='font-family:sans-serif;'>Aún nadie ha apartado regalos.</p>"
    else:
        for r in reservados:
            html_content += f"<p style='font-family:sans-serif;'>🎁 <b>{r['articulo']}</b> (Disponibles: {r['cupos_disponibles']}/{r['cupos_totales']})<br>"
            html_content += f"👤 Apartado por: <b>{r['elegidos_por']}</b> "
            html_content += f"<a href='/liberar/{r['id']}' style='color:red; font-weight:bold; text-decoration:none;'>[Eliminar invitado]</a></p>"
            
    html_content += "<br><br><a href='/' style='font-family:sans-serif;'>⬅ Volver a la mesa</a>"
    return HTMLResponse(content=html_content)

@app.get("/liberar/{id_regalo}")
def liberar_regalo(id_regalo: int, db = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT cupos_totales FROM regalos WHERE id = %s", (id_regalo,))
    regalo = cursor.fetchone()
    
    if regalo:
        cursor.execute("UPDATE regalos SET cupos_disponibles = %s, elegidos_por = '' WHERE id = %s", (regalo["cupos_totales"], id_regalo))
        db.commit()
        
    return RedirectResponse(url="/admin", status_code=303)
