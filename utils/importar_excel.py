import click
import pandas as pd
from pathlib import Path

from app import app, db, Proveedor, Medicamento, Sucursal, StockLocal, ClienteCronico, Venta

def _norm_code(code):
    """Return a normalized string for a medication code."""
    if pd.isna(code):
        return None
    code_str = str(code).strip()
    if code_str.endswith('.0'):
        code_str = code_str[:-2]
    return code_str

def importar_excel(path: str = "data/dummy_data.xlsx"):
    """Carga datos de un archivo Excel a la base de datos."""
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(file)

    with app.app_context():
        db.create_all()
        xls = pd.ExcelFile(file)

        def _read(sheet: str):
            df = pd.read_excel(xls, sheet)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            return df

        if "proveedores" in xls.sheet_names:
            df = _read("proveedores")
            for _, row in df.iterrows():
                db.session.add(Proveedor(
                    nombre=row["nombre"],
                    dia_pedido_fijo=row["dia_pedido_fijo"],
                    dias_entrega=int(row["dias_entrega"])
                ))

        if "sucursales" in xls.sheet_names:
            df = _read("sucursales")
            for _, row in df.iterrows():
                db.session.add(Sucursal(nombre=row["nombre"]))

        meds_map = {}
        if "medicamentos" in xls.sheet_names:
            df = _read("medicamentos")
            for _, row in df.iterrows():
                prov = row.get("proveedor_id")
                med = Medicamento(
                    nombre=row.get("descripcion") or row.get("nombre"),
                    proveedor_id=int(prov) if prov is not None and not pd.isna(prov) else None
                )
                db.session.add(med)
                db.session.flush()  # asigna id sin esperar al commit
                meds_map[_norm_code(row["codigo"])] = med.id

        if "stock" in xls.sheet_names:
            df = _read("stock")
            for _, row in df.iterrows():
                code = _norm_code(row.get("codigo") or row.get("codigo_medicamento"))
                med_id = meds_map.get(code)
                suc_id = row.get("sucursal_id")
                if med_id is None or pd.isna(suc_id):
                    print(f"Fila de stock omitida: {row.to_dict()}")
                    continue
                db.session.add(StockLocal(
                    medicamento_id=int(med_id),
                    sucursal_id=int(suc_id),
                    existencias=int(row["existencias"])
                ))

        if "clientes_cronicos" in xls.sheet_names:
            df = _read("clientes_cronicos")
            for _, row in df.iterrows():
                code = _norm_code(row.get("codigo") or row.get("codigo_medicamento"))
                med_id = meds_map.get(code)
                suc_id = row.get("sucursal_id")
                if med_id is None or pd.isna(suc_id):
                    print(f"Fila cr\xf3nico omitida: {row.to_dict()}")
                    continue
                fecha = pd.to_datetime(row["fecha_ultima_compra"]).date()
                db.session.add(ClienteCronico(
                    nombre=row["nombre"],
                    medicamento_id=int(med_id),
                    sucursal_id=int(suc_id),
                    frecuencia_dias=int(row["frecuencia_dias"]),
                    fecha_ultima_compra=fecha
                ))

        if "ventas" in xls.sheet_names:
            df = _read("ventas")
            for _, row in df.iterrows():
                code = _norm_code(row.get("codigo") or row.get("codigo_medicamento"))
                med_id = meds_map.get(code)
                suc_id = row.get("sucursal_id")
                if med_id is None or pd.isna(suc_id):
                    print(f"Fila venta omitida: {row.to_dict()}")
                    continue
                fecha = pd.to_datetime(row["fecha"]).date()
                db.session.add(Venta(
                    medicamento_id=int(med_id),
                    sucursal_id=int(suc_id),
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