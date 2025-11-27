# Racional App – Frontend

Interfaz interactiva para visualizar la evolución del portafolio de inversiones en tiempo real.

## Características

- **Gráficos Interactivos** – Chart.js con tooltips personalizados
- **Tiempo Real** – Sincronización con Firestore
- **Diseño Responsivo** – 50% del ancho en desktop, adaptable en mobile
- **Formatos Personalizados** – Dinero ($), porcentajes (%)

## Estructura

```
src/
├── components/
│   ├── InvestmentEvolutionChart.jsx      # Orquestador de gráficos
│   ├── PortfolioValueVsInvestedChart.jsx # Gráfico 1
│   └── ReturnChart.jsx                   # Gráfico 2
├── hooks/
│   └── useInvestmentEvolution.js         # Listener de Firestore
├── App.jsx
├── firebase.js
├── style.css
└── main.jsx
```

## Instalación

```bash
npm install
npm run dev
```

## Variables de Entorno

Copia `.env.local.template` a `.env.local`:

```bash
cp .env.local.template .env.local
```

Completa con tus credenciales de Firebase:

```env
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_DATABASE_URL=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
```

## 📊 Datos de Firestore

La aplicación escucha en `investmentEvolutions/user1`:

```json
{
  "array": [
    {
      "date": { "seconds": 1546311600, "nanoseconds": 0 },
      "contributions": 1000000,
      "portfolioValue": 1050000,
      "dailyReturn": 50000,
      "portfolioIndex": 105
    }
  ]
}
```

## 📈 Gráficos

### Gráfico 1: Valor del Portafolio vs Total Invertido

- Línea azul: Valor del portafolio
- Línea naranja punteada: Total invertido
- Área sombreada para el portafolio

### Gráfico 2: Porcentaje de Retorno

- Línea verde: % de retorno calculado

## Estilos

Todos los estilos están en `style.css` con clases reutilizables:

- `.app-root` – Contenedor principal
- `.app-card` – Tarjeta central (50% ancho)
- `.chart-root` – Contenedor de gráficos
- `.chart-box` – Cada gráfico individual

## 🔧 Tecnologías

- **React 18** – UI library
- **Vite** – Build tool rápido
- **Chart.js** – Gráficos
- **Firebase** – Firestore para datos en vivo
