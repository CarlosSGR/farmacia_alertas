import pandas as pd
from utils.importar_excel import importar_excel
from app import db, Proveedor

def test_importar_excel_skips_missing_dias_entrega(tmp_path, client):
    xls_path = tmp_path / 'data.xlsx'
    df = pd.DataFrame({
        'nombre': ['Prov1', 'Prov2'],
        'dia_pedido_fijo': ['Lunes', 'Martes'],
        'dias_entrega': [3, None]
    })
    with pd.ExcelWriter(xls_path) as writer:
        df.to_excel(writer, sheet_name='proveedores', index=False)

    importar_excel(str(xls_path))

    with client.application.app_context():
        nombres = [p.nombre for p in Proveedor.query.all()]
        assert nombres == ['Prov1']