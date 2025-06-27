import click
import pandas as pd
from pathlib import Path

from app import app, db, Proveedor, Medicamento, Sucursal, StockLocal, ClienteCronico, Venta


def importar_excel(path: str = "data/dummy_data.xlsx"):
    """Carga datos de un archivo Excel a la base de datos."""
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(file)

    with app.app_context():
        db.create_all()
        xls = pd.ExcelFile(file)

        if "proveedores" in xls.sheet_names:
            df = pd.read_excel(xls, "proveedores")
            for _, row in df.iterrows():
                db.session.add(Proveedor(
                    nombre=row["nombre"],
                    dia_pedido_fijo=row["dia_pedido_fijo"],
                    dias_entrega=int(row["dias_entrega"])
                ))

        if "sucursales" in xls.sheet_names:
            df = pd.read_excel(xls, "sucursales")
            for _, row in df.iterrows():
                db.session.add(Sucursal(nombre=row["nombre"]))

        if "medicamentos" in xls.sheet_names:
            df = pd.read_excel(xls, "medicamentos")
            for _, row in df.iterrows():
                db.session.add(Medicamento(
                    nombre=row["nombre"],
                    proveedor_id=int(row["proveedor_id"])
                ))

        if "stock" in xls.sheet_names:
            df = pd.read_excel(xls, "stock")
            for _, row in df.iterrows():
                db.session.add(StockLocal(
                    medicamento_id=int(row["medicamento_id"]),
                    sucursal_id=int(row["sucursal_id"]),
                    existencias=int(row["existencias"])
                ))

        if "clientes_cronicos" in xls.sheet_names:
            df = pd.read_excel(xls, "clientes_cronicos")
            for _, row in df.iterrows():
                fecha = pd.to_datetime(row["fecha_ultima_compra"]).date()
                db.session.add(ClienteCronico(
                    nombre=row["nombre"],
                    medicamento_id=int(row["medicamento_id"]),
                    sucursal_id=int(row["sucursal_id"]),
                    frecuencia_dias=int(row["frecuencia_dias"]),
                    fecha_ultima_compra=fecha
                ))

        if "ventas" in xls.sheet_names:
            df = pd.read_excel(xls, "ventas")
            for _, row in df.iterrows():
                fecha = pd.to_datetime(row["fecha"]).date()
                db.session.add(Venta(
                    medicamento_id=int(row["medicamento_id"]),
                    sucursal_id=int(row["sucursal_id"]),
                    fecha=fecha
                ))

        db.session.commit()
        print("\u2705 Datos importados")


@click.command(help="Importa datos desde un archivo Excel")
@click.option("--file", "path", default="data/dummy_data.xlsx", show_default=True,
              help="Ruta al archivo .xlsx")
def cli(path):
    importar_excel(path)


if __name__ == "__main__":
    cli()
    