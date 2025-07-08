from datetime import datetime, timedelta
import click
from app import app, db


def generar_alertas():
    """Genera alertas según el estado actual de la base de datos."""
    """Genera alertas de clientes crónicos próximas a vencer."""
    from app import Medicamento, ClienteCronico, Alerta
    with app.app_context():
        hoy = datetime.now()

        # Limpiar alertas existentes
        Alerta.query.delete()

        # Clientes crónicos próximos a comprar
        for c in ClienteCronico.query.all():
            prox = c.fecha_ultima_compra + timedelta(days=c.frecuencia_dias)
            dias_rest = (prox - hoy.date()).days
            if 0 <= dias_rest <= 3:
                med = Medicamento.query.get(c.medicamento_id)
                

                db.session.add(Alerta(
                    tipo='Cliente Crónico',
                    mensaje=f'{c.nombre} necesita {med.nombre} en {dias_rest} días.',
                    fecha_programada=hoy,
                    sucursal_id=c.sucursal_id,
                    destinatario=c.nombre
                ))

        db.session.commit()
        print('\u2705 Alertas generadas')


@click.command(help='Genera las alertas del sistema')
def cli():
    from app import app
    generar_alertas()


if __name__ == '__main__':
    cli()    
    