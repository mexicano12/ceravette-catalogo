import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from dotenv import load_dotenv # Importa esto
import psycopg2
import psycopg2.extras # <--- Asegúrate de importar esto


app = Flask(__name__)
# Carga las variables del archivo .env
load_dotenv()


# --- CONFIGURACIÓN DE BASE DE DATOS (NEON / POSTGRESQL) ---
DATABASE_URL = os.environ.get('DATABASE_URL')
app.secret_key = 'pedesinterra' 

def get_db_connection():
    # Nos conectamos
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    # ESTA LÍNEA ES LA CLAVE: le dice a psycopg2 que devuelva los datos como diccionarios
    conn.cursor_factory = psycopg2.extras.DictCursor
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Usamos SERIAL para el ID automático en PostgreSQL
    cur.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL,
            descripcion TEXT,
            imagen TEXT
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()
# --- SEGURIDAD ---
ADMIN_USER = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("123456")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS DE ACCESO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if user == ADMIN_USER and check_password_hash(ADMIN_PASSWORD_HASH, pwd):
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        return "Usuario o contraseña incorrectos", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

# --- RUTAS PRINCIPALES ---
@app.route('/')
def index():
    categoria_filtro = request.args.get('categoria')
    conn = get_db_connection()
    cur = conn.cursor()
    
    if categoria_filtro:
        cur.execute('SELECT * FROM productos WHERE categoria = %s', (categoria_filtro,))
    else:
        cur.execute('SELECT * FROM productos')
        
    productos = cur.fetchall() # En psycopg2, fetchall devuelve una lista de tuplas
    cur.close()
    conn.close()
    return render_template('index.html', productos=productos)

# --- PANEL ADMIN ---
CATEGORIAS_DISPONIBLES = [
    {"id": "xv_anos", "nombre": "XV Años"}, {"id": "comunion", "nombre": "Primera Comunión"},
    {"id": "bautizo", "nombre": "Bautizo"}, {"id": "boda", "nombre": "Boda"},
    {"id": "aniversario", "nombre": "Aniversario"}, {"id": "luctuoso", "nombre": "Aniversario Luctuoso"},
    {"id": "graduacion", "nombre": "Graduaciones"}, {"id": "san_valentin", "nombre": "San Valentín"},
    {"id": "navidad", "nombre": "Navidad"}, {"id": "halloween", "nombre": "Halloween"},
    {"id": "dia_madres", "nombre": "Día de las Madres"}, {"id": "jabones", "nombre": "Jabones de Glicerina"},
    {"id": "velas_sanacion", "nombre": "Velas de Sanación"}
]

@app.context_processor
def inject_categorias():
    return dict(categorias=CATEGORIAS_DISPONIBLES)

@app.route('/admin')
@login_required
def admin():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM productos')
    productos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', productos=productos)

@app.route('/admin/nuevo', methods=['POST'])
@login_required
def crear_producto():
    try:
        codigo = request.form.get('codigo', '').upper().strip()
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria')
        precio = float(request.form.get('precio', 0))
        descripcion = request.form.get('descripcion', '').strip()

        archivo = request.files.get('foto_molde')
        imagen_db = None
        if archivo:
            nombre_limpio = secure_filename(f"{codigo}.png")
            ruta_molde = os.path.join('static/productos', nombre_limpio)
            archivo.save(ruta_molde)
            imagen_db = f"/static/productos/{nombre_limpio}"

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO productos (codigo, nombre, categoria, precio, descripcion, imagen)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (codigo, nombre, categoria, precio, descripcion, imagen_db))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin'))
    except Exception as e:
        return f"Error: {e}", 500

# EL DECORADOR VA AQUÍ, SEPARADO EN UNA NUEVA LÍNEA:
@app.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    conn = get_db_connection()
    cur = conn.cursor() # ¡Necesitas crear el cursor!
    
    if request.method == 'POST':
        # Nota el uso de %s y que ahora es cur.execute
        cur.execute("""UPDATE productos SET nombre=%s, precio=%s, descripcion=%s, categoria=%s 
                       WHERE id=%s""", 
                     (request.form['nombre'], request.form['precio'], request.form['descripcion'], request.form['categoria'], id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin'))
    
    cur.execute("SELECT * FROM productos WHERE id = %s", (id,))
    producto = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('editar.html', producto=producto)

@app.route('/admin/eliminar/<int:id>')
@login_required
def eliminar_producto(id):
    conn = get_db_connection()
    cur = conn.cursor() # ¡Necesitas crear el cursor!
    cur.execute('DELETE FROM productos WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin'))
if __name__ == '__main__':
    # 1. Aseguramos que la base de datos se cree al arrancar
    init_db()
    
    # 2. Render nos da un puerto a través de una variable de entorno. 
    # Si no existe (como en tu PC), usamos el 5000 por defecto.
    port = int(os.environ.get("PORT", 5000))
    
    # 3. Quitamos el debug=True para producción y configuramos el host
    app.run(host='0.0.0.0', port=port, debug=False)