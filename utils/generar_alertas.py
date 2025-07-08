from datetime import datetime
from dateutil.relativedelta import relativedelta
import click

from app import app, db


def generar_alertas():
    """Generate alerts for chronic clients missing their monthly purchase."""
    from app import Medicamento, ClienteCronico, Alerta, Venta

    with app.app_context():
        hoy = datetime.now().date()

        # limpia alertas viejas
        Alerta.query.delete()

        for cliente in ClienteCronico.query.all():
            expected_date = cliente.fecha_ultima_compra + relativedelta(months=1)
            dias_rest = (expected_date - hoy).days
            if dias_rest < 0 or dias_rest > 3:
                continue

            venta = Venta.query.filter_by(
                cliente_id=cliente.id,
                medicamento_id=cliente.medicamento_id,
                sucursal_id=cliente.sucursal_id,
                fecha=expected_date,
            ).first()
            if venta:
                continue

            med = Medicamento.query.get(cliente.medicamento_id)
            db.session.add(
                Alerta(
                    tipo="Cliente Crónico",
                    mensaje=f"{cliente.nombre} necesita {med.nombre} en {dias_rest} días.",
                    fecha_programada=datetime.now(),
                    sucursal_id=cliente.sucursal_id,
                    destinatario=cliente.nombre,
                )
            )

        db.session.commit()
        print("✅ Alertas generadas con regla de mes-pasado")


@click.command(help="Genera las alertas del sistema")
def cli():
    generar_alertas()


if __name__ == "__main__":
    cli()
