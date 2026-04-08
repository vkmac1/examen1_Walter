import os

import psycopg2
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)


def conectar_db():
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        return psycopg2.connect(database_url)

    return psycopg2.connect(
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT", "5432"),
    )


def crear_persona(dni, nombre, apellido, direccion, telefono):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO personas (dni, nombre, apellido, direccion, telefono)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (dni, nombre, apellido, direccion, telefono),
    )
    conn.commit()
    cursor.close()
    conn.close()


def obtener_registros():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, dni, nombre, apellido, direccion, telefono
        FROM personas
        ORDER BY apellido, nombre
        """
    )
    registros = cursor.fetchall()
    cursor.close()
    conn.close()
    return registros


def eliminar_persona_por_dni(dni):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM personas WHERE dni = %s", (dni,))
    conn.commit()
    cursor.close()
    conn.close()


@app.route("/")
def index():
    mensaje = request.args.get("mensaje")
    return render_template("index.html", mensaje=mensaje)


@app.route("/registrar", methods=["POST"])
def registrar():
    dni = request.form["dni"]
    nombre = request.form["nombre"]
    apellido = request.form["apellido"]
    direccion = request.form["direccion"]
    telefono = request.form["telefono"]

    crear_persona(dni, nombre, apellido, direccion, telefono)
    return redirect(url_for("index", mensaje="Registro exitoso"))


@app.route("/administrar")
def administrar():
    registros = obtener_registros()
    return render_template("administrar.html", registros=registros)


@app.route("/eliminar/<dni>", methods=["POST"])
def eliminar_registro(dni):
    eliminar_persona_por_dni(dni)
    return redirect(url_for("administrar"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
