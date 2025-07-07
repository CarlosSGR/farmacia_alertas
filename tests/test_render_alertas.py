from datetime import datetime

from app import db, Alerta, _render_alertas_sucursal


def test_render_alertas_parses_variations(client):
    with client.application.app_context():
        a1 = Alerta(
            tipo='Cliente Crónico',
            mensaje='JUAN NECESITA  Aspirina  en  3 dias',
            fecha_programada=datetime.now(),
            sucursal_id=1,
            destinatario='Juan'
        )
        a2 = Alerta(
            tipo='Cliente Crónico',
            mensaje='mensaje sin datos',
            fecha_programada=datetime.now(),
            sucursal_id=1,
            destinatario='Juan'
        )
        db.session.add_all([a1, a2])
        db.session.commit()

        _render_alertas_sucursal(1)

        assert a1.medicamento == 'Aspirina'
        assert a1.dias_restantes == '3'
        assert a2.medicamento == ''
        assert a2.dias_restantes is None