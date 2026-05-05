from flask import Flask, render_template, request, redirect, session, url_for, abort
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_secreta"

FECHA_INICIO = datetime(2026, 4, 1)
FECHA_FIN = datetime(2026, 6, 30)
MAX_NOTAS = 3

usuarios = {
    "profe1": "1234",
    "admin": "admin"
}

estudiantes = {
    "1": {"nombre": "Leonardo Leonesco", "notas": []},
    "2": {"nombre": "Adrian SantaCruz", "notas": []}
}

def usuario_logueado():
    return "usuario" in session

def estado_plazo():
    ahora = datetime.now()
    if ahora < FECHA_INICIO:
        return "no_iniciado"
    elif FECHA_INICIO <= ahora <= FECHA_FIN:
        return "activo"
    else:
        return "finalizado"

def calcular_promedio(codigo):
    notas = estudiantes[codigo]["notas"]
    if not notas:
        return 0
    valores = []
    for n in notas:
        if n["valor"] == "NSP":
            valores.append(0)
        else:
            valores.append(float(n["valor"]))
    return sum(valores) / len(valores)

@app.before_request
def proteger_rutas():
    rutas_protegidas = ["/menu", "/registrar", "/historial", "/editar", "/eliminar"]
    if any(request.path.startswith(r) for r in rutas_protegidas):
        if not usuario_logueado():
            return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()
        if user in usuarios and usuarios[user] == password:
            session["usuario"] = user
            return redirect(url_for("menu"))
        else:
            error = "Credenciales incorrectas"
    return render_template("login.html", error=error)

@app.route("/menu")
def menu():
    return render_template(
        "menu.html",
        estudiantes=estudiantes,
        fecha_inicio=FECHA_INICIO.strftime("%d/%m/%Y"),
        fecha_fin=FECHA_FIN.strftime("%d/%m/%Y"),
        estado=estado_plazo()
    )

@app.route("/registrar", methods=["POST"])
def registrar_nota():
    if estado_plazo() != "activo":
        return "Fuera del periodo de registro"

    codigo = request.form.get("codigo", "").strip()
    nota = request.form.get("nota", "").strip().upper()

    if codigo not in estudiantes:
        return "Estudiante no existe"

    estudiante = estudiantes[codigo]

    if len(estudiante["notas"]) >= MAX_NOTAS:
        return "Máximo de 3 notas alcanzado"

    if nota == "NSP":
        estudiante["notas"].append({"valor": "NSP"})
        return redirect(url_for("menu"))

    try:
        nota_valor = float(nota)
        if nota_valor < 0 or nota_valor > 20:
            return "Nota fuera de rango (0-20)"
        estudiante["notas"].append({"valor": nota_valor})
    except:
        return "Ingrese un número o NSP"

    return redirect(url_for("menu"))

@app.route("/historial/<codigo>")
def historial(codigo):
    if codigo not in estudiantes:
        return "Estudiante no existe"
    estudiante = estudiantes[codigo]
    promedio = calcular_promedio(codigo)
    estado = "Aprobado" if promedio >= 11 else "Desaprobado"
    return render_template(
        "historial.html",
        estudiante=estudiante,
        codigo=codigo,
        promedio=round(promedio, 2),
        estado=estado
    )

@app.route("/editar/<codigo>/<int:index>", methods=["GET", "POST"])
def editar_nota(codigo, index):
    if codigo not in estudiantes:
        return "Estudiante no existe"

    notas = estudiantes[codigo]["notas"]

    if index < 0 or index >= len(notas):
        return "Índice inválido"

    if request.method == "POST":
        nueva = request.form.get("nota", "").strip().upper()

        if nueva == "NSP":
            notas[index] = {"valor": "NSP"}
        else:
            try:
                nueva_valor = float(nueva)
                if nueva_valor < 0 or nueva_valor > 20:
                    return "Fuera de rango"
                notas[index] = {"valor": nueva_valor}
            except:
                return "Valor inválido"

        return redirect(url_for("historial", codigo=codigo))

    return render_template(
        "editar.html",
        codigo=codigo,
        index=index,
        nota=notas[index]["valor"]
    )

@app.route("/eliminar/<codigo>/<int:index>")
def eliminar_nota(codigo, index):
    if codigo not in estudiantes:
        return "Estudiante no existe"

    notas = estudiantes[codigo]["notas"]

    if index < 0 or index >= len(notas):
        return "Índice inválido"

    notas.pop(index)

    return redirect(url_for("historial", codigo=codigo))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
