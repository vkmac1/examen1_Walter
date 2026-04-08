import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for

load_dotenv()

app = Flask(__name__)


def preparar_database_url(database_url):
    parsed = urlparse(database_url)
    query = dict(parse_qsl(parsed.query))

    # Render suele requerir SSL cuando usamos la URL externa.
    if parsed.hostname and parsed.hostname.endswith("render.com"):
        query.setdefault("sslmode", "require")

    updated_query = urlencode(query)
    return urlunparse(parsed._replace(query=updated_query))


def conectar_db():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise OperationalError("DATABASE_URL no esta configurada.")

    return psycopg2.connect(preparar_database_url(database_url), connect_timeout=5)


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
    error = request.args.get("error")
    return render_template("index.html", mensaje=mensaje, error=error)


@app.route("/registrar", methods=["POST"])
def registrar():
    dni = request.form["dni"]
    nombre = request.form["nombre"]
    apellido = request.form["apellido"]
    direccion = request.form["direccion"]
    telefono = request.form["telefono"]

    try:
        crear_persona(dni, nombre, apellido, direccion, telefono)
        return redirect(url_for("index", mensaje="Registro exitoso"))
    except OperationalError:
        return redirect(
            url_for(
                "index",
                error="No se pudo conectar a la base de datos. Revisa tu DATABASE_URL en Render.",
            )
        )


@app.route("/administrar")
def administrar():
    try:
        registros = obtener_registros()
        return render_template("administrar.html", registros=registros, error=None)
    except OperationalError:
        return render_template(
            "administrar.html",
            registros=[],
            error="No se pudo consultar la base de datos. Verifica la conexion en Render.",
        )


@app.route("/eliminar/<dni>", methods=["POST"])
def eliminar_registro(dni):
    try:
        eliminar_persona_por_dni(dni)
        return redirect(url_for("administrar"))
    except OperationalError:
        return redirect(
            url_for(
                "administrar",
                error="No se pudo eliminar el registro porque la base de datos no responde.",
            )
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
