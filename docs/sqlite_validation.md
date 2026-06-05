# Validación de compatibilidad con SQLite

## Objetivo
Demostrar que el núcleo del prototipo puede operar también sobre SQLite en un entorno local de validación, manteniendo compatibilidad básica con:

- modelos del dominio,
- sesiones SQLAlchemy,
- migraciones Alembic,
- inserciones mínimas,
- lectura de entidades principales.

## Alcance
La validación SQLite se considera una validación de entorno local y no sustituye el uso principal de PostgreSQL para el despliegue del prototipo.

## Procedimiento

### 1. Preparar variables de entorno
Usar una configuración con:

```env
DATABASE_URL=sqlite:///./data/sqlite/phishing_sqlite.db