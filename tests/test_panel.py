from datetime import datetime

from app import db, Alerta, JustificacionNoVenta

def test_panel_counts(client):
    with client.application.app_context():
        a1 = Alerta(tipo='Tipo A', mensaje='A1', fecha_programada=datetime.now())
        a2 = Alerta(tipo='Tipo A', mensaje='A2', fecha_programada=datetime.now())
        a3 = Alerta(tipo='Tipo B', mensaje='B1', fecha_programada=datetime.now())
        db.session.add_all([a1, a2, a3])
        db.session.commit()
        j = JustificacionNoVenta(alerta_id=a1.id, motivo='Cliente no contestó')
        db.session.add(j)
        db.session.commit()

    resp = client.get('/panel')
    html = resp.data.decode()
    assert resp.status_code == 200
    assert 'Alertas activas' in html
    assert '>3<' in html
    assert 'Justificaciones registradas' in html
    assert 'Tipo A' in html and 'badge bg-secondary">2<' in html
    assert 'Tipo B' in html and 'badge bg-secondary">1<' in html
