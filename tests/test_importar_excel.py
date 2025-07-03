import pandas as pd
import pytest
from utils.importar_excel import importar_excel
from app import db, Proveedor


def test_importar_excel_raises_on_missing_dias_entrega(tmp_path, client):
    xls_path = tmp_path / 'data.xlsx'
    df = pd.DataFrame({
        'nombre': ['Prov1', 'Prov2'],
        'dia_pedido_fijo': ['Lunes', 'Martes'],
        'dias_entrega': [3, None]
    })
    with pd.ExcelWriter(xls_path) as writer:
        df.to_excel(writer, sheet_name='proveedores', index=False)

    with pytest.raises(Exception):
        importar_excel(str(xls_path))

    with client.application.app_context():
        db.session.rollback()
        nombres = [p.nombre for p in Proveedor.query.all()]
        assert nombres == []