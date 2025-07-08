from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import click
from app import app, db


def generar_alertas():
    """Genera alertas según el estado actual de la base de datos."""
    """Genera alertas de clientes crónicos próximas a vencer."""
    from app import Medicamento, ClienteCronico, Alerta, Venta
    with app.app_context():
        hoy = datetime.now().date()

        # Limpiar alertas existentes
        Alerta.query.delete()

        # Clientes crónicos próximos a comprar según la venta del mes pasado
        for c in ClienteCronico.query.all():
            prox = c.fecha_ultima_compra + relativedelta(months=1)
            dias_rest = (prox - hoy).days
            if 0 <= dias_rest <= 3:
                # Verificar si ya existe una venta para esta fecha
                venta = (
                    Venta.query
                    .filter_by(medicamento_id=c.medicamento_id, sucursal_id=c.sucursal_id)
                    .filter(Venta.fecha == prox)
                    .first()
                )
                if venta:
                    continue

                med = Medicamento.query.get(c.medicamento_id)
                db.session.add(
                    Alerta(
                        tipo='Cliente Crónico',
                        mensaje=f'{c.nombre} necesita {med.nombre} en {dias_rest} días.',
                        fecha_programada=datetime.now(),
                        sucursal_id=c.sucursal_id,
                        destinatario=c.nombre,
                    )
                )

        db.session.commit()
        print('\u2705 Alertas generadas')


@click.command(help='Genera las alertas del sistema')
def cli():
    from app import app
    generar_alertas()


if __name__ == '__main__':
    cli()    
    