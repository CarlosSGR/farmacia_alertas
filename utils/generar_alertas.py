from datetime import datetime, timedelta
import click

from app import app, db, Proveedor, Medicamento, StockLocal, ClienteCronico, PedidoMarcado, Alerta, Venta


def generar_alertas():
    """Genera alertas según el estado actual de la base de datos."""
    with app.app_context():
        hoy = datetime.now()
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

        # Limpiar alertas existentes
        Alerta.query.delete()

        # Clientes crónicos próximos a comprar
        for c in ClienteCronico.query.all():
            prox = c.fecha_ultima_compra + timedelta(days=c.frecuencia_dias)
            dias_rest = (prox - hoy.date()).days
            if dias_rest <= 3:
                med = Medicamento.query.get(c.medicamento_id)
                stock = StockLocal.query.filter_by(medicamento_id=med.id, sucursal_id=c.sucursal_id).first()
                prov = med.proveedor

                db.session.add(Alerta(
                    tipo='Cliente Crónico',
                    mensaje=f'{c.nombre} necesita {med.nombre} en {dias_rest} días.',
                    fecha_programada=hoy,
                    sucursal_id=c.sucursal_id
                ))

                if not stock or stock.existencias < 1:
                    db.session.add(Alerta(
                        tipo='Stock Bajo',
                        mensaje=f'Stock insuficiente para {c.nombre} ({med.nombre}) en sucursal {c.sucursal_id}.',
                        fecha_programada=hoy,
                        sucursal_id=c.sucursal_id
                    ))

                dia_actual = hoy.weekday()
                dia_pedido = dias_semana.index(prov.dia_pedido_fijo)
                dias_hasta_pedido = (dia_pedido - dia_actual) % 7
                if dias_rest < dias_hasta_pedido + prov.dias_entrega:
                    db.session.add(Alerta(
                        tipo='Riesgo Entrega',
                        mensaje=f'No alcanza a llegar {med.nombre} para {c.nombre} (falta {dias_rest} días).',
                        fecha_programada=hoy,
                        sucursal_id=c.sucursal_id
                    ))

        # Verificar pedidos no marcados
        for prov in Proveedor.query.all():
            if dias_semana[hoy.weekday()] == prov.dia_pedido_fijo:
                marcado = PedidoMarcado.query.filter_by(proveedor_id=prov.id, fecha=hoy.date()).first()
                if not marcado:
                    db.session.add(Alerta(
                        tipo='Pedido No Marcado',
                        mensaje=f'Hoy es día de pedido para {prov.nombre} y no se ha marcado como completado.',
                        fecha_programada=hoy
                    ))

        # Productos que no se venden hace más de 60 días
        sesenta_dias = datetime.now().date() - timedelta(days=60)
        ventas = db.session.query(
            Venta.medicamento_id,
            Venta.sucursal_id,
            db.func.max(Venta.fecha).label('ultima_venta')
        ).group_by(Venta.medicamento_id, Venta.sucursal_id).all()

        for venta in ventas:
            if venta.ultima_venta <= sesenta_dias:
                medicamento = Medicamento.query.get(venta.medicamento_id)
                alerta = Alerta(
                    tipo='Producto Emulado',
                    mensaje=f'{medicamento.nombre} no se ha vendido en más de 60 días en sucursal {venta.sucursal_id}.',
                    destinatario='administrador',
                    fecha_programada=datetime.now(),
                    sucursal_id=None
                )
                db.session.add(alerta)

        db.session.commit()
        print('\u2705 Alertas generadas')


@click.command(help='Genera las alertas del sistema')
def cli():
    generar_alertas()


if __name__ == '__main__':
    cli()    