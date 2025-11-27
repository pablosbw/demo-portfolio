# Racional Challenge – Investment Portfolio Platform

Una plataforma completa de gestión de portafolios de inversión con frontend en React/Vite y backend en Django REST.

## Estructura del Proyecto

```
racional-challenge/
├── racional-app/          # Frontend - React + Vite
│   ├── src/
│   │   ├── components/    # Componentes reutilizables
│   │   ├── hooks/         # Custom hooks
│   │   ├── App.jsx
│   │   ├── firebase.js
│   │   └── style.cssv
│   ├── .env.local.template
│   └── package.json
│
├── racional-api/          # Backend - Django REST
│   ├── racional_api/
│   │   ├── models.py      # Modelos de BD
│   │   ├── views.py
│   │   └── urls.py
│   └── manage.py
│
└── README.md
```

## Características

### Frontend (racional-app)

- Visualización interactiva de portafolios en tiempo real
- Gráficos con Chart.js (Valor vs Invertido, % de Retorno)
- Integración con Firestore para datos en vivo

### Backend (racional-api)

- API REST con Django
- Modelos de negocio: User, Stock, Portfolio, Order, Transaction
- Soft delete para auditoría
- Gestión de órdenes de compra/venta
- Seguimiento de precios de acciones

## Instalación y Ejecución

### Frontend

```bash
cd racional-app
npm install
npm run dev
```

Abre `http://localhost:5173`

### Backend

```bash
cd racional-api
docker-compose up --build
```

API disponible en `http://localhost:8000`

Puedes testearla en `http://localhost:8000/api/docs`

## Configuración de Entorno

### Frontend (.env.local)

Copia `.env.local.template` y completa con tus credenciales Firebase:

```env
VITE_FIREBASE_API_KEY=tu_api_key
VITE_FIREBASE_AUTH_DOMAIN=tu_auth_domain
VITE_FIREBASE_DATABASE_URL=tu_database_url
VITE_FIREBASE_PROJECT_ID=tu_project_id
VITE_FIREBASE_STORAGE_BUCKET=tu_storage_bucket
VITE_FIREBASE_MESSAGING_SENDER_ID=tu_sender_id
VITE_FIREBASE_APP_ID=tu_app_id
```

### Backend

Copia el archivo `.env.template` y pegalo en la misma carpeta como `.env`

## Flujo de Datos

1. **Usuario** -> Frontend (React/Vite)
2. Frontend -> **Firestore** (datos de evolución de portafolio)
3. Frontend -> **Backend API** (órdenes, transacciones)
4. Backend -> **Base de Datos** (persistencia)

## Tecnologías

| Componente    | Tecnología                    |
| ------------- | ----------------------------- |
| Frontend      | React 18, Vite, Chart.js      |
| Backend       | Django, Django REST Framework |
| Base de Datos | PostgreSQL                    |
| Tiempo Real   | Firebase Firestore            |
| Estilos       | CSS Personalizado             |

## Modelos del Backend

### User

- Información personal (nombre, email, teléfono)
- Saldo disponible
- Soft delete habilitado

### Portfolio

- Nombre y descripción
- Nivel de riesgo (LOW, MEDIUM, HIGH)
- Componentes (stocks con pesos)

### Order

- Compra/Venta de stocks o portafolios
- Precio de ejecución
- Cantidad y fecha

### Transaction

- Depósitos y retiros
- Auditoría completa con soft delete

### Stock & StockPrice

- Información del activo
- Histórico de precios

## Componentes Frontend

- **App.jsx** – Contenedor principal
- **InvestmentEvolutionChart.jsx** – Orquestador de gráficos
- **PortfolioValueVsInvestedChart.jsx** – Gráfico de valor vs invertido
- **ReturnChart.jsx** – Gráfico de porcentaje de retorno
- **useInvestmentEvolution.js** – Hook para Firestore

## API Endpoints (Backend)

Está en más detalle en el readme de `racional-api`y en el swagger en `http://localhost:8000/api/docs`

```
POST   /api/users/               – Crear usuario
GET    /api/users/               – Listar usuarios
POST   /api/orders/              – Crear orden
GET    /api/portfolios/          – Listar portafolios
POST   /api/transactions/        – Registrar transacción
```

## Notas de Desarrollo

- **Soft Delete**: Todos los modelos mantienen auditoría con `is_deleted` y timestamps
- **TODO**: Implementar Wallet model para reemplazar campo `money` en User
- **TODO**: Agregar tabla Positions para tracking de holdings del usuario
- **TODO**: Cambiar StockPrice.value a DecimalField
