# incident-api

Backend REST API para el sistema de gestión de incidentes productivos.

## Stack

| Tecnología | Propósito |
|-----------|-----------|
| Python 3.12 | Lenguaje principal |
| Django 5.1 | Framework web |
| Django REST Framework | Construcción de API REST |
| SQL Server (mssql-django) | Persistencia de datos core (incidentes) |
| MongoDB (pymongo) | Persistencia de eventos/auditoría |
| Gunicorn | Servidor de producción |

### ¿Por qué Django y no .NET/Java?

Django + DRF es el framework que domino con mayor profundidad, lo que me permite
entregar código de mayor calidad en menor tiempo. La decisión prioriza:

- **Velocidad de entrega** sin sacrificar buenas prácticas.
- **ORM maduro** que se integra con SQL Server vía `mssql-django`.
- **Serializers de DRF** para validación robusta de entrada/salida.
- **Ecosistema Python** con `pymongo` y `requests` para las integraciones.

## Arquitectura
```
config/          → Configuración Django (settings, urls, wsgi)
incidents/
  models.py      → Modelo Incident (SQL Server, managed=False)
  serializers.py → Validación de entrada + formato de respuesta
  services.py    → Lógica de MongoDB + integración Service Catalog
  views.py       → 4 endpoints REST + health check
  urls.py        → Rutas de la app
tests/           → Tests unitarios y de integración
```

**Decisiones clave:**

- `managed = False` en el modelo porque la tabla la crea `init.sql`.
  Esto evita conflictos entre las migraciones de Django y el schema real.
- Capa `services.py` separada de los views para mantener la lógica
  de negocio (MongoDB, HTTP) desacoplada de la capa HTTP.
- Singleton para el cliente MongoDB para reutilizar conexiones.
- Manejo completo de errores en la integración con Service Catalog
  (404, timeout, connection error).

## Endpoints

### POST /incidents
Crea un nuevo incidente.
```bash
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Pago falla al confirmar",
    "description": "Error 500 intermitente",
    "severity": "HIGH",
    "serviceId": "payments-api"
  }'
```

### GET /incidents
Lista incidentes con filtros y paginación.
```bash
# Todos los incidentes
curl http://localhost:8000/incidents

# Con filtros
curl "http://localhost:8000/incidents?status=OPEN&severity=HIGH&page=1&pageSize=5"

# Búsqueda por título
curl "http://localhost:8000/incidents?q=pago"
```

### GET /incidents/{id}
Detalle del incidente con timeline de eventos.
```bash
curl http://localhost:8000/incidents/A1B2C3D4-E5F6-7890-ABCD-EF1234567890
```

### PATCH /incidents/{id}/status
Cambiar estado de un incidente.
```bash
curl -X PATCH http://localhost:8000/incidents/A1B2C3D4-E5F6-7890-ABCD-EF1234567890/status \
  -H "Content-Type: application/json" \
  -d '{"status": "RESOLVED"}'
```

### GET /health
Health check.
```bash
curl http://localhost:8000/health
```

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| SQL_SERVER_HOST | localhost | Host de SQL Server |
| SQL_SERVER_PORT | 1433 | Puerto de SQL Server |
| SQL_SERVER_DB | IncidentDB | Nombre de la base de datos |
| SQL_SERVER_USER | sa | Usuario de SQL Server |
| SQL_SERVER_PASSWORD | Incident@2026! | Contraseña de SQL Server |
| MONGODB_URI | mongodb://localhost:27017 | URI de conexión a MongoDB |
| MONGODB_DB | incident_events_db | Nombre de la BD en MongoDB |
| SERVICE_CATALOG_URL | http://localhost:3001 | URL del Service Catalog mock |
| DEBUG | 1 | Modo debug (0 en producción) |
| ALLOWED_HOSTS | * | Hosts permitidos |

## Cómo correr (desarrollo local)
```bash
# 1. Crear ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Correr tests
python manage.py test tests

# 4. Correr servidor de desarrollo
python manage.py runserver
```

## Cómo correr (Docker)
```bash
# Desde incident-infra/
docker compose up --build
```

## Tests
```bash
python manage.py test tests
```