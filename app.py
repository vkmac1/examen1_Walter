import os

import psycopg2
from psycopg2 import OperationalError
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)


def conectar_db():
    database_url = os.environ.get("postgresql://nubesdb_user:UFdc6R8x1xyn5pisLmY0RH5tgLdoPPNu@dpg-d7bbpohaae7s73c0jb5g-a/nubesdb")

    if database_url:
        return psycopg2.connect(database_url, connect_timeout=5)

    return psycopg2.connect(
        dbname=os.environ.get("nubesdb"),
        user=os.environ.get("nubesdb_user"),    
        password=os.environ.get("UFdc6R8x1xyn5pisLmY0RH5tgLdoPPNu"),
        host=os.environ.get("dpg-d7bbpohaae7s73c0jb5g-a.oregon-postgres.render.com"),
        port=os.environ.get("5432"),
        connect_timeout=5,
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
