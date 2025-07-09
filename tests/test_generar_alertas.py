from datetime import datetime

from dateutil.relativedelta import relativedelta

from utils.generar_alertas import generar_alertas
from app import db, Medicamento, ClienteCronico, Venta, Alerta


def test_generar_alertas_compara_mes_pasado(client):
    with client.application.app_context():
        med = Medicamento(nombre="Ibuprofeno")
        db.session.add(med)
        db.session.commit()

        fecha_prev = (datetime.now() - relativedelta(months=1)).date()

        c1 = ClienteCronico(
            nombre="Juan",
            medicamento_id=med.id,
            sucursal_id=1,
            frecuencia_dias=30,
            fecha_ultima_compra=fecha_prev,
        )

        c2 = ClienteCronico(
            nombre="Ana",
            medicamento_id=med.id,
            sucursal_id=1,
            frecuencia_dias=30,
            fecha_ultima_compra=fecha_prev,
        )

        db.session.add_all([c1, c2])
        db.session.commit()

        # Registrar la compra de Ana para la fecha esperada
        db.session.add(
            Venta(
                cliente_id=c2.id,
                medicamento_id=med.id,
                sucursal_id=1,
                fecha=datetime.now().date(),
            )
        )
        db.session.commit()

        generar_alertas()

        alertas = Alerta.query.all()
        assert len(alertas) == 1
        assert alertas[0].tipo == "Cliente Cr\xf3nico"
        assert "Juan" in alertas[0].mensaje
        assert "necesita" in alertas[0].mensaje
        