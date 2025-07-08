import pandas as pd
import pytest
from utils.importar_excel import importar_excel
from app import db, Proveedor, Medicamento, StockLocal


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


def test_importar_medicamentos_without_proveedor_id(tmp_path, client):
    xls_path = tmp_path / 'data.xlsx'
    meds = pd.DataFrame({'codigo': [1, 2], 'descripcion': ['A', 'B']})
    with pd.ExcelWriter(xls_path) as writer:
        meds.to_excel(writer, sheet_name='medicamentos', index=False)

    importar_excel(str(xls_path))

    with client.application.app_context():
        nombres = [m.nombre for m in db.session.query(Medicamento).all()]
        assert nombres == ['A', 'B']


def test_importar_stock_ignores_unnamed_columns(tmp_path, client):
    xls_path = tmp_path / 'data.xlsx'
    meds = pd.DataFrame({'codigo': [1], 'descripcion': ['Med']})
    stock = pd.DataFrame({
        'sucursal_id': [1],
        'codigo': [1],
        'existencias': [2],
        None: [None],
    })
    with pd.ExcelWriter(xls_path) as writer:
        meds.to_excel(writer, sheet_name='medicamentos', index=False)
        stock.to_excel(writer, sheet_name='stock', index=False)

    importar_excel(str(xls_path))

    with client.application.app_context():
        stocks = db.session.query(StockLocal).all()
        assert len(stocks) == 1
        assert stocks[0].existencias == 2


def test_importar_stock_numeric_codes(tmp_path, client):
    xls_path = tmp_path / 'data.xlsx'
    meds = pd.DataFrame({'codigo': [51004.0], 'descripcion': ['Med']})
    stock = pd.DataFrame({'sucursal_id': [1], 'codigo': [51004], 'existencias': [2]})
    with pd.ExcelWriter(xls_path) as writer:
        meds.to_excel(writer, sheet_name='medicamentos', index=False)
        stock.to_excel(writer, sheet_name='stock', index=False)

    importar_excel(str(xls_path))

    with client.application.app_context():
        rows = db.session.query(StockLocal).all()
        assert len(rows) == 1
        assert rows[0].existencias == 2