# Farmacia Alertas

Pequeña aplicación de ejemplo para gestionar alertas de una farmacia. Las tablas se almacenan en `farmacia.db` utilizando SQLite y SQLAlchemy.

The SQLite database is stored in the `instance` directory so it is not
version controlled. When the app starts, it uses Flask's `instance_path`
to build the path to `farmacia.db`:

```python
app = Flask(__name__, instance_relative_config=True)
db_path = os.path.join(app.instance_path, 'farmacia.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
```

Make sure the `instance` folder exists and contains `farmacia.db` before
running the application.

## Instalación

Crea un entorno virtual y luego instala los paquetes listados en
`requirements.txt`:

```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

## Inicializar la base de datos

Antes de cargar información o generar alertas ejecuta la migración de la base de datos:

```bash
flask --app app migrar
```

## Importar datos desde Excel

El script `utils/importar_excel.py` lee un archivo de Excel con varias hojas y carga la información en la base de datos. Por defecto usa `data/dummy_data.xlsx`.

```bash
flask insertar_dummy
```

También puedes indicar un archivo diferente:

```bash
python utils/importar_excel.py --file path/a/datos.xlsx
```

Las hojas esperadas son `proveedores`, `sucursales`, `medicamentos`, `stock`, `clientes_cronicos` y `ventas`.

## Generar alertas

El módulo `utils/generar_alertas.py` contiene la lógica para construir las alertas de negocio. Ahora solamente se generan avisos de tipo **Cliente Crónico**, los cuales se crean cuando la siguiente compra prevista para un cliente está a 0–3 días de distancia.
Puedes ejecutarlo directamente:

```bash
python utils/generar_alertas.py
```

Dentro de la aplicación Flask también existe el comando equivalente:

```bash
flask --app app generar_alertas
```

Esto evaluará el estado actual de la base de datos y almacenará las alertas correspondientes.

## Running the Tests

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute the test suite with `pytest`:
   ```bash
   pytest
   ```

The tests use an in-memory SQLite database and do not modify the existing data files.


## Ejecutar la aplicación

Inicia el servidor de desarrollo con:

```bash
flask --app app run
```

## Para actualizar la base de datos constantemente

En un periodo determinado anteriormente ya sea diario semanal etc. Lo que debe hacerse es lo siguiente:

En la hoja de Excel dummy_data deberá ya sea registrarse o actualizarse en la hoja de clientes_cronicos el cliente a tratar. 
En caso de actualizar deberá actualizarse principalmente la fecha de la última compra MUY IMPORTANTE. (En caso de que sea necesario se deberá cambiar también el código de medicamento/frecuencia_dias/sucursal_id)

Una vez hecho deberá seguirse el proceso determinado anteriormente para 

1. Migrar
2. Insertar la tabla (Osea el excel)
3. Generar las alertas