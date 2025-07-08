from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import click
from app import app, db


def generar_alertas():
    from app import Medicamento, ClienteCronico, Alerta, Venta
    with app.app_context():
        hoy = datetime.now().date()
        ventana = [hoy + timedelta(days=i) for i in range(0, 4)]  # hoy + 3 días

        # limpia alertas viejas
        Alerta.query.delete()

        for dia_actual in ventana:
            dia_pasado = dia_actual - relativedelta(months=1)

            # Todas las ventas del mismo día del mes pasado
            ventas_pasadas = Venta.query.filter(Venta.fecha == dia_pasado).all()

            for v in ventas_pasadas:
                # ¿El mismo cliente ya compró el mismo día de este mes?
                ya_compro = Venta.query.filter_by(
                    cliente_id=v.cliente_id,
                    medicamento_id=v.medicamento_id,
                    sucursal_id=v.sucursal_id,
                    fecha=dia_actual
                ).first()

                if ya_compro:
                    continue  # no alertar, compra realizada

                cliente = ClienteCronico.query.get(v.cliente_id)
                med     = Medicamento.query.get(v.medicamento_id)
                dias_rest = (dia_actual - hoy).days

                db.session.add(Alerta(
                    tipo="Cliente Crónico",
                    mensaje=f"{cliente.nombre} compró {med.nombre} el {dia_pasado:%d/%m}. Faltan {dias_rest} días y aún no repite la compra.",
                    fecha_programada=datetime.now(),
                    sucursal_id=v.sucursal_id,
                    destinatario=cliente.nombre
                ))

        db.session.commit()
        print("✅ Alertas generadas con regla de mes-pasado")



@click.command(help='Genera las alertas del sistema')
def cli():
    from app import app
    generar_alertas()


if __name__ == '__main__':
    cli()    
    