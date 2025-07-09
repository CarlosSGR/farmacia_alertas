from datetime import datetime

from app import db, Alerta, JustificacionNoVenta, MOTIVOS


def test_justificaciones_grouped_by_motivo(client):
    with client.application.app_context():
        a1 = Alerta(tipo='Tipo X', mensaje='A1', fecha_programada=datetime.now())
        a2 = Alerta(tipo='Tipo X', mensaje='A2', fecha_programada=datetime.now())
        db.session.add_all([a1, a2])
        db.session.commit()
        j1 = JustificacionNoVenta(alerta_id=a1.id, motivo=MOTIVOS[0])
        j2 = JustificacionNoVenta(alerta_id=a1.id, motivo=MOTIVOS[0])
        j3 = JustificacionNoVenta(alerta_id=a2.id, motivo=MOTIVOS[1])
        db.session.add_all([j1, j2, j3])
        db.session.commit()
        a1_id = a1.id
        a2_id = a2.id

    resp = client.get('/justificaciones')
    html = resp.data.decode()
    assert resp.status_code == 200
    assert f"{MOTIVOS[0]} (2)" in html
    assert f"{MOTIVOS[1]} (1)" in html
    assert f"Alerta ID: {a1_id}" in html
    assert f"Alerta ID: {a2_id}" in html