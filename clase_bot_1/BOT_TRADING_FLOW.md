# Bot de Trading - Documentación de Flujo

Este documento describe el flujo de operación de un bot de trading que opera en el mercado de futuros.

## Índice
- [Descripción General](#descripción-general)
- [Diagrama de Flujo](#diagrama-de-flujo)
- [Componentes Principales](#componentes-principales)
- [Detalles de Implementación](#detalles-de-implementación)

## Descripción General
El bot está diseñado para ejecutar operaciones de trading de manera automatizada, gestionando órdenes y monitoreando su estado en tiempo real.

## Diagrama de Flujo

### 1. Inicialización y Configuración
```mermaid
graph TD
    A[Inicio del Bot] --> B[Crear Cliente PyRofex]
    B --> C{¿Descargar Instrumentos?}
    C -->|Sí| D[Obtener y Guardar Instrumentos en DB]
    C -->|No| E[Continuar]
    D --> E
    E --> F[Inicializar SQLite]
```

### 2. Verificación de Operaciones Pendientes
```mermaid
graph TD
    A[Consultar DB] --> B[Obtener Lista TODO]
    B --> C{¿Hay Pendientes?}
    C -->|Sí| D[Obtener Instrumentos de SQL]
    C -->|No| E[Esperar 10 minutos]
    D --> F[Obtener Data de Símbolos]
    F --> G[Obtener Precios de Mercado]
```

### 3. Procesamiento de Órdenes
```mermaid
graph TD
    A[Para cada Pendiente] --> B[Calcular Montos a Operar]
    B --> C[Generar Órdenes]
    C --> D[Para cada Orden]
    D --> E[Enviar Orden Límite]
    E --> F[Guardar en DB]
    F --> G[Consultar Estado]
```

### 4. Monitoreo y Actualización
```mermaid
graph TD
    A[Monitorear Órdenes] --> B{¿Todas Finalizadas?}
    B -->|No| C[Consultar Estados]
    C --> D[Actualizar DB]
    D --> E[Esperar 10 segundos]
    E --> B
    B -->|Sí| F[Marcar como Completado]
```

## Componentes Principales

### 1. Gestión de Instrumentos
- Sistema de descarga y actualización de instrumentos disponibles
- Almacenamiento en base de datos SQLite
- Actualización periódica de información

### 2. Gestión de Órdenes
- Procesamiento de órdenes pendientes
- Cálculo de montos y precios
- Envío de órdenes límite
- Sistema de monitoreo de estados

### 3. Persistencia de Datos
Utiliza SQLite para almacenar:
- Lista de instrumentos
- Órdenes activas
- Estados de operaciones
- Histórico de transacciones

### 4. Control de Flujo
- Ciclo principal de ejecución cada 10 minutos
- Monitoreo continuo de órdenes pendientes
- Actualización en tiempo real de estados
- Sistema de manejo de errores

## Detalles de Implementación

### Dependencias Principales
```python
from clase_primary.clase_pyrofex import PyRofexClient
import fx_sqlite
import functions
import pyRofex
```

### Funciones Clave
1. **run_bot()**
   - Función principal que inicia el ciclo del bot
   - Gestiona la lógica principal de operación

2. **Gestión de Base de Datos**
   - `main_sqlite()`: Inicialización de la base de datos
   - `create_connection()`: Conexión a SQLite
   - Funciones de consulta y actualización

3. **Procesamiento de Órdenes**
   - Cálculo de montos
   - Envío de órdenes
   - Monitoreo de estados

### Ciclo de Operación
1. Inicialización del sistema
2. Verificación de pendientes
3. Procesamiento de órdenes
4. Monitoreo continuo
5. Actualización de estados
6. Espera y reinicio del ciclo

## Consideraciones de Uso
- Asegurarse de tener todas las dependencias instaladas
- Configurar correctamente las credenciales de acceso
- Monitorear los logs del sistema
- Realizar pruebas en ambiente de desarrollo antes de producción