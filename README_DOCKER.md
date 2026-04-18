# Dockerización del prototipo de phishing

## Archivos incluidos
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `.env.example`

## Servicios levantados
- `postgres`
- `redis`
- `migrate`
- `api`
- `tracker`
- `worker`
- `dashboard`

## Pasos
1. Copia estos archivos en la **raíz** de tu proyecto.
2. Verifica que tu `infra/requirements.txt` incluya al menos:
   - fastapi
   - uvicorn
   - sqlalchemy
   - alembic
   - celery
   - redis
   - pydantic-settings
   - jinja2
   - psycopg2-binary
   - pandas
   - streamlit
3. Si ya tienes `.env`, puedes dejarlo para desarrollo local. Docker Compose usa variables internas apuntando a `postgres` y `redis`.
4. Desde la raíz del proyecto ejecuta:

   ```bash
   docker compose up --build
   ```

## URLs
- API: http://localhost:8000/docs
- Tracker: http://localhost:8001/landing
- Dashboard: http://localhost:8501

## Notas importantes
- Se incluyó el servicio `migrate` para ejecutar `alembic upgrade head` antes de arrancar el resto.
- `TRACKER_BASE_URL` se dejó como `http://localhost:8001` para que los HTML del outbox se puedan abrir desde el navegador del host.
- El worker usa `--pool=solo`, porque en Windows `prefork` suele fallar con Celery.
- La carpeta del proyecto se monta como volumen (`.:/app`) para desarrollo con recarga en caliente.

## Comandos útiles
Detener:
```bash
docker compose down
```

Ver logs:
```bash
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f tracker
docker compose logs -f dashboard
```

Reiniciar solo un servicio:
```bash
docker compose up --build api
```
