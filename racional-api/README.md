# Racional Investment API

API de inversión que permite registrar depósitos / retiros, operar acciones y portafolios, editar información de usuarios y consultar el valor actual y los últimos movimientos de un usuario.

## Tech

- **Lenguaje / Framework:** Python 3 + Django 5 + Django REST Framework
- **DB:** PostgreSQL (vía Docker)
- **Docs:** Swagger / OpenAPI con `drf-spectacular`
- **Testing:** `pytest` + `pytest-django`

## Modelo de Datos (resumen)

> Todos los modelos heredan de `SoftDeleteModel`, que hace _soft delete_ usando `is_deleted` en vez de borrar filas.

### `User`

Información básica del usuario:

- `first_name`, `last_name`
- `phone_number`, `email` (único)
- `money`: saldo en efectivo (construido a medida que se efectuan `Transaction`, se puede utilizar como un valor de acceso más rápido).

### `Transaction`

Registra movimiento de dinero (no de activos):

- `user`: (FK a `User`)
- `transaction_type`: `DEPOSIT` o `WITHDRAW`
- `amount`: monto
- `execution_date`: fecha de ejecución

### `Stock`

Acción individual:

- `symbol`: string único (ej: `"AAPL"`)
- `name`: nombre de la acción

### `StockPrice`

- `stock`: FK de `Stock`.
- `value`: **precio actual** (float) usado para valorar posiciones
- `date`: timestamp asociado al último valor

### `Portfolio`

Plantilla de portafolio (no representa propiedad, sino una receta):

- `name`, `description`
- `risk`: `LOW`, `MEDIUM`, `HIGH`

### `PortfolioComponent`

Relación N–N entre `Portfolio` y `Stock` con peso:

- `portfolio`: FK a `Portfolio`
- `stock`: FK a `Stock`
- `weight`: peso relativo (Decimal).  
  Para cualquier portafolio válido, la suma de `weight` de sus componentes debe ser = 1.

### `Order`

Orden de compra / venta de activos:

- `user`: FK a `User`
- `asset_type`: `STOCK` o `PORTFOLIO`
- `side`: `BUY` o `SELL`
- `stock`: FK opcional (si `asset_type = STOCK`)
- `portfolio`: FK opcional (para trazar que ciertas órdenes de acciones provienen de la compra de un portafolio)
- `quantity`: cantidad (unidades)
- `execution_price`: precio unitario en el momento de la orden
- `execution_date`: fecha de ejecución

> **Fuente de verdad de las posiciones:**  
> Las posiciones reales de un usuario se derivan de `Order` (BUY – SELL por `Stock`).  
> Los `Portfolio` son solo plantillas usadas para descomponer inversiones en múltiples órdenes de acciones.

## Reglas de Negocio Principales

1. **Soft delete**

   - Todos los modelos heredan de `SoftDeleteModel`.
   - `delete()` marca `is_deleted = True` y conserva el registro.

2. **No se puede borrar un usuario con acciones**

   - En el endpoint de `DELETE /api/users/<id>/`, si el usuario tiene órdenes activas de `asset_type = STOCK`, se devuelve `400` con mensaje explicativo.

3. **Pesos de portafolio**

   - Al crear un `Portfolio` se valida que:
     - Tenga al menos un componente.
     - No existan `Stock` repetidos.
     - La suma de `weight` es `1`.

4. **Compra de portafolio por monto, no por cantidad**

   - El usuario envía un **monto a invertir** (`amount`) en un portafolio.
   - El monto se reparte según los pesos de los `PortfolioComponent`.
   - Para cada componente se crea una `Order` de tipo:
     - `asset_type = STOCK`
     - `side = BUY`
     - `stock = componente.stock`
     - `portfolio = portafolio` (para trazabilidad)
   - La cantidad comprada se calcula como `amount_asignado / Stock.value`.

5. **Valor total del portafolio de un usuario**

   - Se calcula sumando:
     - **Efectivo:** derivado de `Transaction` (`DEPOSIT − WITHDRAW - BUY ORDERS`).
     - **Posiciones en acciones:** para cada `Stock`, se agrega:
       - `qty` = $\sum$(BUY) − $\sum$(SELL)
       - `valor = qty * Stock.value` (usando `Decimal`).

6. **Últimos movimientos del usuario**
   - Se combinan `Transaction` y `Order` ordenados por fecha, en una sola lista cronológica:
     - Transacciones: `DEPOSIT` / `WITHDRAW`
     - Órdenes: `BUY` / `SELL` de `STOCK` o `PORTFOLIO`

## Endpoints Principales

> La lista completa y esquemas detallados están en Swagger:  
> **http://localhost:8000/api/docs** (requiere tener el contenedor corriendo).

Todos los endpoints se pueden ejecutar desde [aquí](http://localhost:8000/api/docs). Ya que OpenAPI, lo permite. Para esto hay que hacer click en el `Try it out` para cualquiera de los endpoints.

### Usuarios

- `GET /api/users/`  
  Lista de usuarios.

- `POST /api/users/`  
  Crea un usuario.

- `GET /api/users/<id>/`  
  Obtiene un usuario específico.

- `PUT/PATCH /api/users/<id>/`  
  Edita información personal del usuario (3. del enunciado).

- `DELETE /api/users/<id>/`  
  Soft delete del usuario.  
  ❗ **Restringido:** si el usuario tiene órdenes de acciones (`Order` con `asset_type = STOCK`), responde `400`.

### Depósitos / Retiros (`Transaction`)

- `GET /api/users/<user_id>/transactions/`  
  Lista transacciones de un usuario.

- `POST /api/users/<user_id>/transactions/`  
  Crea un depósito o retiro:

  ```json
  {
    "transaction_type": "DEPOSIT" | "WITHDRAW",
    "amount": 1000.00,
    "execution_date": "2025-11-28"
  }
  ```

### Órdenes de acciones (`Order` con `asset_type = STOCK`)

- `POST /api/orders/stocks/`
  Crea una orden de compra o venta de una acción concreta:

  ```json
  {
    "user_id": 1,
    "stock_id": 5,
    "side": "BUY" | "SELL",
    "quantity": 10,
    "execution_date": "2025-11-28"
  }
  ```

### Portafolios (`Portfolio` + `PortfolioComponent`)

- `POST /api/portfolios/`
  Crea un portafolio nuevo, seleccionando `Stock` por `symbol` y pesos:

  ```json
  {
    "name": "Portafolio Conservador",
    "description": "Enfoque de bajo riesgo",
    "risk": "LOW",
    "components": [
      { "symbol": "AAPL", "weight": 0.6 },
      { "symbol": "BND", "weight": 0.4 }
    ]
  }
  ```

  Valida que los pesos sumen 1 y que los símbolos existan.

- `GET /api/portfolios/<id>/`
  Lee metadata de un portafolio (y, según la implementación, su composición).

- `PUT/PATCH /api/portfolios/<id>/`
  **Edita solo la metadata del portafolio**

  - `name`
  - `description`
  - `risk`

  > La composición (acciones/pesos) no se modifica en este endpoint, para no afectar inversiones históricas, ya que se permiten ejecutar compras con `execution_data` arbitrarias.

### Invertir en un Portafolio (BUY only)

- `POST /api/orders/portfolios/invest/`
  Invierte un monto en un portafolio, descomponiéndolo automáticamente en órdenes de acciones:

  ```json
  {
    "user_id": 1,
    "portfolio_id": 3,
    "amount": 10000.0,
    "execution_date": "2025-11-28"
  }
  ```

  La respuesta incluye un resumen de las órdenes de acciones creadas.

> **Sell de portafolios**
> No se implementa venta de portafolios a nivel agregado.
> Las ventas se realizan a nivel de acción (`SELL` de `STOCK`).

### Valor total del portafolio de un usuario

- `GET /api/users/<user_id>/portfolio/total/`

Calcula:

- `cash`: efectivo (a partir de `Transaction` y `Order`)
- `stocks_total`: valor actual de todas las posiciones en acciones
- `portfolio_total = cash + stocks_total`
- detalle de posiciones por símbolo

### Últimos movimientos del usuario

- `GET /api/users/<user_id>/movements/`

Combina en una sola línea de tiempo:

- `Transaction` (DEPOSIT / WITHDRAW)
- `Order` (BUY / SELL de STOCK o PORTFOLIO)

Cada movimiento incluye:

- fecha
- tipo (`TRANSACTION` / `ORDER`)
- dirección (`DEPOSIT`/`WITHDRAW`/`BUY`/`SELL`)
- información del activo (si corresponde)
- monto aproximado de la operación

## Cómo ejecutar el proyecto

Asumiendo que ya tienes Docker y Docker Compose:

```bash
docker compose up --build
```

Una vez levantado:

- API base: `http://localhost:8000/api/`
- Swagger / OpenAPI: `http://localhost:8000/api/docs`

---

## Testing

Para ejecutar los tests:

```bash
docker compose exec racional_api pytest -vv --ds=project.settings
```

## Uso de IA

Según el enunciado se permite explícitamente el uso de herramientas de IA.
En este proyecto se utilizó IA para:

1. **Complementar diseño de BBDD**

   - Planificación de la base de datos y algunos refinamientos posteriores a modelos de datos
   - Pensar en implicancias de diseño (portafolio como plantilla vs. posiciones reales).

2. **Testing**

   - Sugerencias de casos de prueba para endpoints (valor del portafolio, últimos movimientos, validación de pesos).

3. **Copilot**
   - Auto completado de codigo

En general, utilizaba el output de IA como base para la posterior modificación. Con base código que había escrito.
