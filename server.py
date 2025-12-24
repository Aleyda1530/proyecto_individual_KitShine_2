# server.py
# Autora: Aleyda Quispe

from wsgiref.simple_server import make_server
from urllib.parse import unquote
import mysql.connector
import os

BASE_DIR = os.path.dirname(__file__)

def conectar_bd():
    try:
        # Configuración específica para Aiven Cloud
        return mysql.connector.connect(
            host="kit-shine-unsa-9bd1.i.aivencloud.com",
            port=24071,
            user="avnadmin",
            password="AVNS_0-Mm0V6wcez3L8DL953",
            database="defaultdb",
            ssl_disabled=False,
            # Aiven requiere SSL. ssl_verify_cert=False permite conectar sin el archivo .pem
            ssl_verify_cert=False 
        )
    except mysql.connector.Error as err:
        print(f"Error de conexión: {err}")
        return None

def app(environ, start_response):
    metodo = environ["REQUEST_METHOD"]
    path = unquote(environ["PATH_INFO"])

    # --- MÉTODO GET ---
    if metodo == "GET":
        if path == "/" or path == "":
            path = "/index.html"

        archivo = os.path.join(BASE_DIR, path.lstrip("/"))

        if os.path.isfile(archivo):
            extension = os.path.splitext(archivo)[1]
            content_type = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg"
            }.get(extension, "application/octet-stream")

            with open(archivo, "rb") as f:
                contenido = f.read()

            start_response("200 OK", [("Content-Type", content_type)])
            return [contenido]

        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"Archivo no encontrado"]

    # --- MÉTODO POST ---
    if metodo == "POST":
        try:
            size = int(environ.get("CONTENT_LENGTH", 0))
            datos_raw = environ["wsgi.input"].read(size).decode()
            # Unquote corrige los caracteres como '+' por espacios y '%40' por '@'
            params = {}
            for par in datos_raw.split("&"):
                if "=" in par:
                    k, v = par.split("=")
                    params[k] = unquote(v.replace("+", " "))
        except Exception as e:
            print(f"Error procesando datos: {e}")
            params = {}

        conn = conectar_bd()
        if conn and conn.is_connected():
            cursor = conn.cursor()
            try:
                if path == "/pedidos":
                    sql = """INSERT INTO pedidos 
                             (nombre, apellido, dni, direccion, correo, producto, pago, comentarios) 
                             VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
                    valores = (params.get("nombre"), params.get("apellido"), params.get("dni"), 
                               params.get("direccion"), params.get("correo"), params.get("producto"), 
                               params.get("pago"), params.get("comentarios"))
                    cursor.execute(sql, valores)

                elif path == "/opiniones":
                    sql = "INSERT INTO opiniones (nombre, apellido, correo, calificacion, comentario) VALUES (%s,%s,%s,%s,%s)"
                    valores = (params.get("nombre"), params.get("apellido"), params.get("correo"), 
                               params.get("calificacion"), params.get("comentario"))
                    cursor.execute(sql, valores)

                elif path == "/contacto":
                    sql = "INSERT INTO contactos (nombre, apellido, correo, tema, mensaje) VALUES (%s,%s,%s,%s,%s)"
                    valores = (params.get("nombre"), params.get("apellido"), params.get("correo"), 
                               params.get("tema"), params.get("mensaje"))
                    cursor.execute(sql, valores)

                conn.commit()
                mensaje = "Datos guardados correctamente en Aiven Cloud"
            except mysql.connector.Error as e:
                print(f"Error SQL: {e}")
                mensaje = "Error al guardar los datos"
            finally:
                cursor.close()
                conn.close()
        else:
            mensaje = "No se pudo conectar con la base de datos"

        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        html_res = f"""
        <html>
        <body style='text-align:center; margin-top:50px; font-family: sans-serif;'>
            <h2>{mensaje}</h2>
            <p><a href='/index.html'>Volver</a></p>
        </body>
        </html>
        """
        return [html_res.encode("utf-8")]

    start_response("405 Method Not Allowed", [("Content-Type", "text/plain")])
    return [b"Metodo no permitido"]

# CONFIGURACIÓN DEL SERVIDOR
if __name__ == "__main__":
    import os
    # Render asigna el puerto automáticamente mediante una variable de entorno
    port = int(os.environ.get("PORT", 8000))
    # Usamos 0.0.0.0 para que sea visible en la web
    server = make_server("0.0.0.0", port, app)
    print(f"Servidor iniciado en el puerto {port}...")
    server.serve_forever()