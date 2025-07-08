from datetime import datetime, timedelta

from utils.generar_alertas import generar_alertas
from app import db, Medicamento, ClienteCronico, Alerta

def test_generar_alertas_cronicos(client):
    with client.application.app_context():
        med = Medicamento(nombre='Ibuprofeno')
        db.session.add(med)
        db.session.commit()

        c1 = ClienteCronico(
            nombre='Juan',
            medicamento_id=med.id,
            sucursal_id=1,
            frecuencia_dias=30,
            fecha_ultima_compra=datetime.now().date() - timedelta(days=28)
        )
        c2 = ClienteCronico(
            nombre='Ana',
            medicamento_id=med.id,
            sucursal_id=1,
            frecuencia_dias=30,
            fecha_ultima_compra=datetime.now().date() - timedelta(days=20)
        )
        db.session.add_all([c1, c2])
        db.session.commit()

        generar_alertas()

        alertas = Alerta.query.all()
        assert len(alertas) == 1
        assert alertas[0].tipo == 'Cliente Cr\xf3nico'
        assert 'Juan' in alertas[0].mensaje