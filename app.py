from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///farmacia.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ───────────────── MODELOS ──────────────────
class Proveedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    dia_pedido_fijo = db.Column(db.String(10), nullable=False)  # Lunes‑Domingo
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
    sucursal_id = db.Column(db.Integer, nullable=True)  # NULL = global
    atendida = db.Column(db.Boolean, default=False)

class PedidoMarcado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'))
    fecha = db.Column(db.Date, nullable=False)

# ───────────────── VISTAS ──────────────────
@app.route('/alertas')
def ver_alertas():
    hoy = datetime.now()
    alertas = Alerta.query.filter(Alerta.fecha_programada <= hoy, Alerta.atendida == False).all()
    # Agrupar por tipo para panel admin
    tipos = {}
    for a in alertas:
        tipos.setdefault(a.tipo, []).append(a)
    return render_template('alertas.html', tipos=tipos)

@app.route('/alertas/resolver/<int:alerta_id>', methods=['POST'])
def resolver_alerta(alerta_id):
    alerta = Alerta.query.get_or_404(alerta_id)
    alerta.atendida = True
    db.session.commit()
    return redirect(request.referrer or url_for('ver_alertas'))

@app.route('/alertas_sucursal/<int:sucursal_id>')
def alertas_sucursal(sucursal_id):
    hoy = datetime.now()
    alertas = Alerta.query.filter_by(sucursal_id=sucursal_id, atendida=False).filter(Alerta.fecha_programada<=hoy).all()
    return render_template('alertas_sucursal.html', alertas=alertas, sucursal_id=sucursal_id)

# Ruta para que sucursal marque su alerta
@app.route('/marcar_alerta/<int:alerta_id>', methods=['POST'])
def marcar_alerta(alerta_id):
    alerta = Alerta.query.get_or_404(alerta_id)
    alerta.atendida = True
    db.session.commit()
    return redirect(request.referrer or url_for('alertas_sucursal', sucursal_id=alerta.sucursal_id or 0))

# ──────────────── CLI: dummy + alertas ───────────────
@app.cli.command('insertar_dummy')
def insertar_dummy():
    db.drop_all()
    db.create_all()

    prov = Proveedor(nombre='LEVIC', dia_pedido_fijo='Martes', dias_entrega=3)
    suc1 = Sucursal(nombre='Matriz')
    suc2 = Sucursal(nombre='Sucursal Norte')
    med = Medicamento(nombre='Trayenta', proveedor=prov)

    db.session.add_all([prov, suc1, suc2, med])
    db.session.commit()

    db.session.add_all([
        StockLocal(medicamento_id=med.id, sucursal_id=suc1.id, existencias=2),
        StockLocal(medicamento_id=med.id, sucursal_id=suc2.id, existencias=1)
    ])

    hoy = datetime.now().date()
    db.session.add_all([
        ClienteCronico(nombre='Juan Pérez', medicamento_id=med.id, sucursal_id=suc1.id, frecuencia_dias=30, fecha_ultima_compra=hoy - timedelta(days=27)),
        ClienteCronico(nombre='Ana Gómez', medicamento_id=med.id, sucursal_id=suc2.id, frecuencia_dias=30, fecha_ultima_compra=hoy - timedelta(days=28))
    ])
    db.session.commit()
    print('✅ Datos dummy insertados')

@app.cli.command('generar_alertas')
def generar_alertas():
    hoy = datetime.now()
    dias_semana = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']

    # Limpiamos alertas anteriores
    Alerta.query.delete()

    # 1) Clientes crónicos
    for c in ClienteCronico.query.all():
        prox = c.fecha_ultima_compra + timedelta(days=c.frecuencia_dias)
        dias_rest = (prox - hoy.date()).days
        if dias_rest <= 3:
            med = Medicamento.query.get(c.medicamento_id)
            stock = StockLocal.query.filter_by(medicamento_id=med.id, sucursal_id=c.sucursal_id).first()
            prov = med.proveedor

            db.session.add(Alerta(tipo='Cliente Crónico', mensaje=f'{c.nombre} necesita {med.nombre} en {dias_rest} días.', fecha_programada=hoy, sucursal_id=c.sucursal_id))

            if not stock or stock.existencias < 1:
                db.session.add(Alerta(tipo='Stock Bajo', mensaje=f'Stock insuficiente para {c.nombre} ({med.nombre}) en sucursal {c.sucursal_id}.', fecha_programada=hoy, sucursal_id=c.sucursal_id))

            dia_actual = hoy.weekday()
            dia_pedido = dias_semana.index(prov.dia_pedido_fijo)
            dias_hasta_pedido = (dia_pedido - dia_actual) % 7
            if dias_rest < dias_hasta_pedido + prov.dias_entrega:
                db.session.add(Alerta(tipo='Riesgo Entrega', mensaje=f'No alcanza a llegar {med.nombre} para {c.nombre} (falta {dias_rest} días).', fecha_programada=hoy, sucursal_id=c.sucursal_id))

    # 2) Pedido no marcado
    for prov in Proveedor.query.all():
        if dias_semana[hoy.weekday()] == prov.dia_pedido_fijo:
            marcado = PedidoMarcado.query.filter_by(proveedor_id=prov.id, fecha=hoy.date()).first()
            if not marcado:
                db.session.add(Alerta(tipo='Pedido No Marcado', mensaje=f'Hoy es día de pedido para {prov.nombre} y no se ha marcado como completado.', fecha_programada=hoy))

    db.session.commit()
    print('✅ Alertas generadas')

# ────────────────── MAIN ──────────────────
if __name__ == '__main__':
    app.run(debug=True)
