from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime, timedelta
import re
import os

app = Flask(__name__, instance_relative_config=True)
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'farmacia.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ───────────────── MODELOS ──────────────────
class Proveedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    dia_pedido_fijo = db.Column(db.String(10), nullable=False)
    dias_entrega = db.Column(db.Integer, nullable=False)

class Medicamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'))
    proveedor = db.relationship('Proveedor', lazy='joined')

class Sucursal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

class StockLocal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicamento_id = db.Column(db.Integer, db.ForeignKey('medicamento.id'))
    sucursal_id = db.Column(db.Integer, db.ForeignKey('sucursal.id'))
    existencias = db.Column(db.Integer, nullable=False)

class ClienteCronico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    medicamento_id = db.Column(db.Integer, db.ForeignKey('medicamento.id'))
    sucursal_id = db.Column(db.Integer, db.ForeignKey('sucursal.id'))
    frecuencia_dias = db.Column(db.Integer, nullable=False)
    fecha_ultima_compra = db.Column(db.Date, nullable=False)

class Alerta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    mensaje = db.Column(db.String(255), nullable=False)
    fecha_programada = db.Column(db.DateTime, nullable=False)
    sucursal_id = db.Column(db.Integer, nullable=True)
    atendida = db.Column(db.Boolean, default=False)
    destinatario = db.Column(db.String(100))

class PedidoMarcado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'))
    fecha = db.Column(db.Date, nullable=False)

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicamento_id = db.Column(db.Integer, db.ForeignKey('medicamento.id'), nullable=False)
    sucursal_id = db.Column(db.Integer, db.ForeignKey('sucursal.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)

class JustificacionNoVenta(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    alerta_id = db.Column(db.Integer, db.ForeignKey('alerta.id'), nullable=False)
    motivo    = db.Column(db.String(100), nullable=False)
    fecha     = db.Column(db.DateTime, default=datetime.now)


MOTIVOS = [
    "Cliente no contestó",
    "Lo encontró más barato",
    "Ya no lo necesita",
    "Otro proveedor"
]

# ───────────────── VISTAS ──────────────────

@app.route('/')
def home():
    return redirect(url_for('panel_jefe'))

@app.route('/panel')
def panel_jefe():
    total_alertas = Alerta.query.filter_by(atendida=False).count()
    por_tipo = db.session.query(Alerta.tipo, db.func.count(Alerta.id)).filter_by(atendida=False).group_by(Alerta.tipo).all()
    total_justificaciones = JustificacionNoVenta.query.count()
    return render_template('panel_jefe.html', total_alertas=total_alertas, por_tipo=por_tipo, total_justificaciones=total_justificaciones)

@app.route('/alertas')
def ver_alertas():
    hoy = datetime.now()
    alertas = Alerta.query.filter(Alerta.fecha_programada <= hoy, Alerta.atendida == False).all()
    tipos = {}
    for a in alertas:
        tipos.setdefault(a.tipo, []).append(a)
    return render_template('alertas.html', tipos=tipos, motivos=MOTIVOS)

@app.route('/alertas/resolver/<int:alerta_id>', methods=['POST'])
def resolver_alerta(alerta_id):
    alerta = Alerta.query.get_or_404(alerta_id)
    alerta.atendida = True
    db.session.commit()
    return redirect(request.referrer or url_for('ver_alertas'))

def _render_alertas_sucursal(sucursal_id: int, template: str = "alertas_sucursal.html"):
    """Renderiza las alertas de una sucursal usando la plantilla indicada."""
    hoy = datetime.now()
    alertas = (
        Alerta.query
        .filter_by(sucursal_id=sucursal_id, atendida=False)
        .filter(Alerta.fecha_programada <= hoy)
        .all()
    )
    for a in alertas:
        if a.tipo == 'Cliente Cr\xf3nico':
            m = re.search(r"necesita\s+(.+?)\s+en\s+(\d+)\s+d", a.mensaje, re.IGNORECASE)
            if m:
                a.medicamento = m.group(1)
                a.dias_restantes = m.group(2)
            else:
                a.medicamento = ""
                a.dias_restantes = None
    return render_template(template, alertas=alertas, sucursal_id=sucursal_id, motivos=MOTIVOS)


@app.route('/alertas_sucursal/<int:sucursal_id>')
def alertas_sucursal(sucursal_id):
    return _render_alertas_sucursal(sucursal_id)

@app.route('/alertas_sucursal_matriz')
def alertas_sucursal_1():
    return _render_alertas_sucursal(1)

@app.route('/alertas_sucursal_ampliacion')
def alertas_sucursal_2():
    return _render_alertas_sucursal(2)

@app.route('/alertas_sucursal_civil')
def alertas_sucursal_3():
    return _render_alertas_sucursal(3)

@app.route('/alertas_sucursal_curva')
def alertas_sucursal_4():
    return _render_alertas_sucursal(4)

@app.route('/alertas_sucursal_ejercito')
def alertas_sucursal_5():
    return _render_alertas_sucursal(5)

@app.route('/alertas_sucursal_tampico')
def alertas_sucursal_6():
    return _render_alertas_sucursal(6)

@app.route('/marcar_alerta/<int:alerta_id>', methods=['POST'])
def marcar_alerta(alerta_id):
    alerta = Alerta.query.get_or_404(alerta_id)
    alerta.atendida = True
    db.session.commit()
    return redirect(request.referrer or url_for('alertas_sucursal', sucursal_id=alerta.sucursal_id or 0))

@app.route('/no_venta/<int:alerta_id>', methods=['POST'])
def no_venta(alerta_id):
    motivo = request.form.get('motivo')
    if motivo in MOTIVOS:
        justificacion = JustificacionNoVenta(alerta_id=alerta_id, motivo=motivo)
        alerta = Alerta.query.get_or_404(alerta_id)
        alerta.atendida = True
        db.session.add(justificacion)
        db.session.commit()
    return redirect(request.referrer or url_for('ver_alertas'))

@app.cli.command("migrar")
def migrar():
    # Ensure legacy tables that are no longer required are removed
    db.session.execute(text("DROP TABLE IF EXISTS en_transito"))
    db.create_all()
    print("✅ Tablas listas")

@app.cli.command('insertar_dummy')
def insertar_dummy():
    """Carga la base de datos con la información de ``data/dummy_data.xlsx``."""
    db.session.execute(text("DROP TABLE IF EXISTS en_transito"))
    db.drop_all()
    db.create_all()

    # Utilizar el script de importación existente para cargar todos los datos
    from utils.importar_excel import importar_excel
    try:
        importar_excel("data/dummy_data.xlsx")
    except Exception as exc:
        db.session.rollback()
        print(f"❌ Error al importar datos: {exc}")
        raise
    else:
        print('✅ Datos dummy insertados')

from utils.generar_alertas import generar_alertas

@app.cli.command('generar_alertas')
def generar_alertas_command():
    """CLI que delega la generación de alertas a utils/generar_alertas.py."""
    generar_alertas()


@app.route('/justificaciones')
def ver_justificaciones():
    registros = JustificacionNoVenta.query.all()
    return render_template('justificaciones.html', registros=registros)

@app.route('/contactos_hoy')
def contactos_hoy():
    """Muestra clientes a contactar basados en las alertas activas."""
    fecha = datetime.now().strftime('%d/%m/%Y')
    hoy = datetime.now()

    alertas = (
        Alerta.query
        .filter_by(tipo='Cliente Crónico', atendida=False)
        .filter(Alerta.fecha_programada <= hoy)
        .all()
    )

    clientes = {
        'Urgente': [],
        'Prioritario': [],
        'Rutinario': []
    }

    for alerta in alertas:
        dias = 0
        medicamento = ''
        m = re.search(r'necesita (.+?) en (\d+) d', alerta.mensaje)
        if m:
            medicamento = m.group(1)
            dias = int(m.group(2))

        if dias <= 0:
            categoria = 'Urgente'
        elif dias <= 2:
            categoria = 'Prioritario'
        else:
            categoria = 'Rutinario'

        suc = Sucursal.query.get(alerta.sucursal_id)
        clientes[categoria].append({
            'nombre': alerta.destinatario or 'Cliente',
            'telefono': 'N/A',
            'direccion': suc.nombre if suc else 'Desconocido',
            'tipo': medicamento or 'Medicamento',
            'mensaje': alerta.mensaje
        })

    resumen = {
        cat: len(lista) for cat, lista in clientes.items()
    }
    resumen['Potencial'] = f"${len(alertas) * 1000:,}".replace(',', ',')

    return render_template('contactos_hoy.html', fecha=fecha, resumen=resumen, clientes=clientes)


if __name__ == '__main__':
    app.run(debug=True)
