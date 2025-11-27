# Racional Investment Evolution – Frontend Challenge

Este proyecto implementa una visualización interactiva en tiempo real de la evolución del portafolio de un usuario, utilizando **Firestore**, **React**, **Vite** y **Chart.js**.  
El objetivo es reproducir una experiencia tipo fintech, con foco en claridad, diseño y UX.

## Tecnologías utilizadas

- **React + Vite** – Frontend rápido y moderno.
- **Firebase Firestore** – Lectura en tiempo real del documento `investmentEvolutions/user1`.
- **Chart.js + react-chartjs-2** – Visualizaciones interactivas y personalizadas.

## Estructura del proyecto

```
src/
  components/
    InvestmentEvolutionChart.jsx
    PortfolioValueVsInvestedChart.jsx
    ReturnChart.jsx
  hooks/
    useInvestmentEvolution.js
  utils.js
  firebase.js
  App.jsx
  index.css
```

## Funcionalidad principal

### Escucha de Firestore en tiempo real

El frontend se conecta automáticamente a:

```
investmentEvolutions/user1
```

El documento contiene un array con la evolución diaria del portafolio:

```json
{
  "array": [
    {
      "dailyReturn": 0,
      "contributions": 1000000,
      "date": { "seconds": 1546311600, "nanoseconds": 0 },
      "portfolioIndex": 100,
      "portfolioValue": 1000000
    }
  ]
}
```

### Visualizaciones

**Gráfico 1 — Valor del portafolio vs Total invertido**  
**Gráfico 2 — porcentaje de retorno**

Incluyen:

- Tooltip con formatos `$X.XM`, `$Xk`, `%`
- Línea vertical punteada siguiendo al puntero
- Líneas suavizadas

## Instalación y ejecución

### 1. Instalar dependencias

```bash
npm install
```

### 2. Ejecutar entorno de desarrollo

```bash
npm run dev
```

### 3. Abrir en navegador

Generalmente:

```
http://localhost:5173
```

## Uso de I.A. en el desarrollo

- Comparación de librerías de gráficos y decisiones técnicas.
- Generación rápida de estructuras de componentes.
- Sugerencias de estilos, UX y diseño fintech.
