from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
import time

app = Flask(__name__)
CORS(app)

DB_HOST = os.getenv("DB_HOST", "mariadb-service")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "password")
DB_NAME = os.getenv("DB_NAME", "productos")

def get_connection():
    retries = 5
    while retries > 0:
        try:
            return mysql.connector.connect(
                host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
            )
        except mysql.connector.Error:
            retries -= 1
            time.sleep(2)
    raise Exception("No se pudo conectar a la base de datos")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/healthz", methods=["GET"])
def healthz():
    try:
        conn = get_connection()
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

@app.route("/productos", methods=["GET"])
def listar():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM producto")
    rows = c.fetchall()
    conn.close()
    productos = [{"id": r[0], "nombre": r[1], "descripcion": r[2], "precio": r[3], "stock": r[4]} for r in rows]
    return jsonify(productos)

@app.route("/productos/<int:id>", methods=["GET"])
def obtener(id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM producto WHERE id = %s", (id,))
    row = c.fetchone()
    conn.close()
    if row:
        producto = {"id": row[0], "nombre": row[1], "descripcion": row[2], "precio": row[3], "stock": row[4]}
        return jsonify(producto)
    return jsonify({"error": "Producto no encontrado"}), 404

@app.route("/productos", methods=["POST"])
def crear():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO producto (nombre, descripcion, precio, stock)
        VALUES (%s, %s, %s, %s)
    """, (data["nombre"], data["descripcion"], data["precio"], data["stock"]))
    conn.commit()
    product_id = c.lastrowid
    conn.close()
    return jsonify({"status": "ok", "id": product_id}), 201

@app.route("/productos/<int:id>", methods=["PUT"])
def actualizar(id):
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE producto 
        SET nombre = %s, descripcion = %s, precio = %s, stock = %s
        WHERE id = %s
    """, (data["nombre"], data["descripcion"], data["precio"], data["stock"], id))
    conn.commit()
    affected = c.rowcount
    conn.close()
    if affected > 0:
        return jsonify({"status": "ok", "updated": id})
    return jsonify({"error": "Producto no encontrado"}), 404

@app.route("/productos/<int:id>", methods=["DELETE"])
def eliminar(id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM producto WHERE id = %s", (id,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    if affected > 0:
        return jsonify({"status": "ok", "deleted": id})
    return jsonify({"error": "Producto no encontrado"}), 404

def init_db():
    time.sleep(10)
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS producto (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100),
            descripcion TEXT,
            precio FLOAT,
            stock INT
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)