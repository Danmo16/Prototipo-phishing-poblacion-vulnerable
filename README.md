# Prototipo de simulación de phishing para identificación de población vulnerable

Proyecto académico desarrollado como Trabajo Profesional de Ingeniería de Sistemas. Este repositorio contiene un prototipo modular para ejecutar simulaciones controladas de phishing por correo electrónico, registrar eventos de interacción y analizar los datos generados mediante estadística descriptiva, regresión logística, XGBoost, GLMM y un componente NLP basado en DistilBERT.

---

## 1. Qué se puede reproducir con este repositorio

A partir de una instalación limpia es posible:

1. levantar PostgreSQL, Redis, API, tracker, worker y dashboard;
2. crear un usuario administrador;
3. autenticarse mediante JWT desde Swagger;
4. crear segmentos, plantillas, targets y campañas;
5. lanzar una campaña mediante Celery y Redis;
6. probar el envío en modo outbox o SMTP controlado;
7. registrar eventos `delivered`, `opened`, `clicked` y `reported`;
8. exportar datasets observados;
9. generar datos sintéticos y construir un dataset combinado;
10. entrenar regresión logística, XGBoost, GLMM y DistilBERT;
11. visualizar resultados en Streamlit;
12. generar reportes HTML/PDF;
13. validar la capa analítica mediante un dataset de prueba incluido en el repositorio;
14. reproducir los escenarios sintéticos controlados utilizados para comprobar la capacidad analítica del prototipo.

---

## 2. Arquitectura resumida

|        Componente      |                Tecnología                  |                       Función                  |
|------------------------|--------------------------------------------|------------------------------------------------|
| API                    | FastAPI / Uvicorn                          | Autenticación y administración de recursos     |
| Base de datos          | PostgreSQL                                 | Persistencia principal                         |
| ORM y migraciones      | SQLAlchemy / Alembic                       | Acceso y evolución del esquema                 |
| Broker                 | Redis                                      | Cola de tareas                                 |
| Worker                 | Celery                                     | Procesamiento asíncrono de campañas            |
| Tracker                | FastAPI                                    | Registro de apertura, clic y reporte por `uid` |
| Correo                 | Jinja2 / SMTP / outbox                     | Renderizado y entrega controlada               |
| Dashboard              | Streamlit                                  | Consulta operativa y analítica                 |
| Analítica estructurada | pandas, scikit-learn, XGBoost, statsmodels | ETL, descripción y modelado                    |
| NLP                    | PyTorch / Hugging Face Transformers        | DistilBERT                                     |
| Despliegue             | Docker / Docker Compose                    | Ejecución coordinada                           |

Flujo general:

```text
Administrador
    |
    v
FastAPI ----> PostgreSQL
    |
    v
 Redis ----> Celery Worker ----> SMTP / Outbox
                                  |
                                  v
                                Email
                                  |
                                  v
                               Tracker
                                  |
                                  v
                                Events
                                  |
                                  v
                         Pipeline analítico
                                  |
                                  v
                     Modelos + Dashboard + Reportes
```

---

## 3. Requisitos

### Software mínimo

- Git
- Python 3.11
- Docker Desktop o Docker Engine + Docker Compose v2
- Navegador web moderno

### Opcional para entrenamiento acelerado

- GPU NVIDIA compatible con CUDA
- Drivers NVIDIA y una instalación de PyTorch con soporte CUDA

La ejecución académica documentada utilizó Windows 10, Python 3.11 y una NVIDIA GeForce RTX 5070 Ti. El entrenamiento también puede realizarse en CPU, aunque será más lento.

---

## 4. Clonar el proyecto

El desarrollo completo se encuentra en la rama `master`.

```powershell
git clone -b master --single-branch https://github.com/Danmo16/Prototipo-phishing-poblacion-vulnerable.git
cd Prototipo-phishing-poblacion-vulnerable
```

---

## 5. Preparar el entorno Python

En Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r Infra/requirements.txt
```

Si la carpeta de infraestructura fue normalizada a minúsculas, use:

```powershell
pip install -r infra/requirements.txt
```

Para verificar el entorno:

```powershell
python --version
pip --version
```

Para comprobar CUDA:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

---

## 6. Configuración de variables de entorno

Copie el archivo de ejemplo:

```powershell
Copy-Item .env.example .env
```

Revise los valores antes de ejecutar el proyecto.

### Recomendación para pruebas reproducibles

Use inicialmente el modo outbox para no enviar correo real:

```dotenv
DELIVERY_MODE=outbox
OUTBOX_DIR=data/outbox
```

Para una prueba SMTP, configure únicamente una cuenta propia/controlada.

### Seguridad

- No publique contraseñas, tokens ni secretos reales.
- `.env` debe estar excluido por `.gitignore`.
- `docker-compose.yml` debe referenciar variables de entorno y no contener credenciales reales.
- Si alguna credencial fue publicada previamente, debe rotarse antes de distribuir el repositorio.

---

## 7. Levantar la infraestructura

La forma recomendada es Docker Compose:

```powershell
docker compose up --build -d
```

Verifique los servicios:

```powershell
docker compose ps
```

Servicios esperados:

- PostgreSQL
- Redis
- migraciones Alembic
- API
- tracker
- worker
- dashboard

Logs útiles:

```powershell
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f tracker
docker compose logs -f dashboard
```

URLs principales:

| Servicio | URL |
|---|---|
| Swagger / OpenAPI | `http://127.0.0.1:8000/docs` |
| Tracker / landing | `http://127.0.0.1:8001/landing` |
| Dashboard | `http://127.0.0.1:8501` |

Para detener:

```powershell
docker compose down
```

---

## 8. Ejecución manual de servicios

Si se desea ejecutar fuera de Docker, mantenga PostgreSQL y Redis activos y abra terminales separadas.

API:

```powershell
uvicorn apps.api.main:app --reload
```

Tracker:

```powershell
uvicorn apps.tracker.main:app --reload --port 8001 --reload-dir apps/tracker
```

Worker en Windows:

```powershell
celery -A apps.worker.celery_app.celery_app worker --loglevel=info --pool=solo
```

Dashboard:

```powershell
streamlit run apps/dashboard/app.py
```

---

## 9. Crear un usuario administrador

Con la base de datos disponible:

```powershell
python -m scripts.create_admin_user --username admin --email admin@example.com --password CambiarEstaClave --full-name "Administrador"
```

Use una contraseña local de prueba que no reutilice en otros servicios.

---

## 10. Probar la herramienta: campaña completa

Abra Swagger:

```text
http://127.0.0.1:8000/docs
```

### 10.1 Autenticación

Ejecute:

```text
POST /auth/login
```

Luego use el botón **Authorize** de Swagger para registrar el token Bearer.

### 10.2 Crear un segmento

```text
POST /segments
```

Ejemplo:

```json
{
  "age_bracket": "25-34",
  "gender": "F",
  "education": "Universitaria"
}
```

Guarde el `id` retornado.

### 10.3 Crear una plantilla

```text
POST /templates
```

Ejemplo conceptual:

```json
{
  "channel": "email",
  "name": "Plantilla académica",
  "subject": "Notificación académica para {{ name }}",
  "description": "Plantilla de validación controlada",
  "html_body": "<html><body><p>Simulación académica.</p><a href='{{ landing_url }}'>Abrir</a><img src='{{ tracking_dot }}' width='1' height='1' /></body></html>",
  "signals": {
    "urgencia": 0,
    "autoridad": 1,
    "recompensa": 0,
    "personalizacion": 1
  },
  "version": 1
}
```

### 10.4 Crear un target

```text
POST /targets
```

Use únicamente una cuenta propia o una dirección sintética:

```json
{
  "segment_id": 1,
  "recipient": "usuario-controlado@example.com",
  "meta": {
    "source": "self_test"
  }
}
```

### 10.5 Crear una campaña

```text
POST /campaigns
```

Ejemplo:

```json
{
  "channel": "email",
  "template_id": 1,
  "segment_id": 1
}
```

### 10.6 Lanzar la campaña

```text
POST /campaigns/{campaign_id}/launch
```

El resultado debe indicar que la campaña fue encolada y retornar un `task_id`.

En los logs del worker debe observarse la recepción y ejecución de la tarea.

### 10.7 Verificar entrega

Con `DELIVERY_MODE=outbox`, revise:

```text
data/outbox/
```

Con SMTP controlado, verifique únicamente la cuenta configurada por el evaluador.

### 10.8 Verificar tracking

El correo utiliza un `uid`. Los enlaces tienen una estructura similar a:

```text
http://127.0.0.1:8001/r?uid=<UID>
http://127.0.0.1:8001/open.gif?uid=<UID>
http://127.0.0.1:8001/report?uid=<UID>
```

El tracker resuelve internamente la campaña, target y plantilla a partir del `uid` y los eventos persistidos.

---

## 11. Exportar los datos de las campañas

Después de ejecutar pruebas operativas:

```powershell
python -m scripts.export_dataset
```

Se genera un dataset observado versionado en `data/exports/`.

Ejemplo de patrón:

```text
analytic_dataset_observed_<contexto>_<AAAAMMDD_HHMMSS>.csv
```

La nomenclatura versionada evita que una nueva ejecución sobrescriba un archivo previo.

---

# 12. Validación de la parte analítica con datos incluidos en el repositorio

Para que la capa analítica pueda probarse **sin crear campañas ni depender de una base de datos previamente poblada**, el repositorio debe incluir el archivo:

```text
data/samples/analytic_validation_dataset.csv
```

Este archivo es un conjunto **100 % sintético**, no contiene datos personales y está construido con semilla `42`.

Características del dataset de validación:

- 600 registros;
- 8 plantillas sintéticas;
- 5 segmentos sintéticos;
- 15 registros por combinación plantilla-segmento;
- variable objetivo `clicked_flag`;
- señales `signal_urgency`, `signal_authority`, `signal_reward` y `signal_personalization`;
- variables demográficas `age_bracket`, `gender` y `education`;
- patrón deliberado: mayor probabilidad de apertura cuando existe personalización.

Con semilla 42, la validación descriptiva de referencia es aproximadamente:

```text
Apertura con personalización    : 49.78 %
Apertura sin personalización    : 24.80 %
Diferencia                      : +24.98 puntos porcentuales
```

Este patrón es artificial y sirve únicamente para comprobar que el pipeline puede recuperar una diferencia conocida.

---

## 13. Validar el modelo baseline con el dataset incluido

```powershell
python -m scripts.train_baseline_model --dataset data/samples/analytic_validation_dataset.csv --output-prefix baseline_validation
```

Los artefactos se generan en:

```text
data/models/
```

con un timestamp común, por ejemplo:

```text
baseline_validation_20260905_130000_metrics.json
baseline_validation_20260905_130000_predictions.csv
baseline_validation_20260905_130000_coefficients.csv
baseline_validation_20260905_130000_calibration.csv
baseline_validation_20260905_130000_model.joblib
baseline_validation_20260905_130000_split.csv
```

---

## 14. Validar XGBoost con el dataset incluido

CPU, recomendado para un evaluador sin GPU:

```powershell
python -m scripts.train_xgboost_model --dataset data/samples/analytic_validation_dataset.csv --output-prefix xgboost_validation --device cpu
```

Con GPU CUDA:

```powershell
python -m scripts.train_xgboost_model --dataset data/samples/analytic_validation_dataset.csv --output-prefix xgboost_validation --device cuda
```

Los resultados incluyen métricas, predicciones, calibración, lift, modelo e importancias de variables.

---

## 15. Validar GLMM con el dataset incluido

```powershell
python -m scripts.train_glmm_model --dataset data/samples/analytic_validation_dataset.csv --output-prefix glmm_validation --random-effect segment_id --method vb
```

Se generan métricas, efectos fijos, componentes de varianza, predicciones y resumen del ajuste.

---

## 16. Usar el dataset de validación en el dashboard

El dashboard localiza automáticamente los datasets combinados versionados dentro de `data/exports/`.

Para probar la interfaz con el dataset incluido, copie el archivo de validación a `data/exports/` con un nombre compatible:

```powershell
Copy-Item data/samples/analytic_validation_dataset.csv data/exports/analytic_dataset_combined_validation_20260905_000000.csv
```

Luego ejecute:

```powershell
streamlit run apps/dashboard/app.py
```

En la barra lateral seleccione:

```text
Fuente del dataset analítico -> Combinado
```

El dashboard permitirá revisar:

- resumen general;
- dataset seleccionado;
- tasas de apertura y clic;
- resumen por campañas;
- resumen demográfico;
- comparación por señales;
- artefactos de baseline;
- XGBoost;
- GLMM;
- NLP cuando existan artefactos compatibles.

Las descargas generadas por el dashboard usan nombres versionados que incorporan contexto y timestamp.

---

## 17. Generar nuevamente el dataset sintético general

El dataset principal usado en la experimentación también puede regenerarse:

```powershell
python -m scripts.generate_synthetic_dataset
```

Después puede integrarse con los datos observados:

```powershell
python -m scripts.merge_observed_and_synthetic
```

El combinado resultante se almacena con nombre versionado en `data/exports/`.

---

## 18. Reproducir los cuatro escenarios sintéticos controlados

Además del dataset de validación incluido, el repositorio contiene un generador de escenarios con patrones conocidos.

### Control

```powershell
python -m scripts.generate_synthetic_scenarios --scenario control --seed 42 --targets-per-cell 15
```

### Personalización

```powershell
python -m scripts.generate_synthetic_scenarios --scenario personalization --seed 42 --targets-per-cell 15
```

### Segmento

```powershell
python -m scripts.generate_synthetic_scenarios --scenario segment --seed 42 --targets-per-cell 15
```

### Interacción señal-segmento

```powershell
python -m scripts.generate_synthetic_scenarios --scenario interaction --seed 42 --targets-per-cell 15
```

Luego ejecute:

```powershell
python -m scripts.analyze_synthetic_scenarios
```

Se genera:

```text
synthetic_scenario_validation_summary_<timestamp>.csv
```

Resultados de referencia con semilla 42:

| Escenario | Grupo A | Grupo B | Diferencia |
|---|---:|---:|---:|
| Control | 31.56 % | 33.33 % | -1.78 pp |
| Personalización | 49.78 % | 24.80 % | +24.98 pp |
| Segmento | 13.33 % | 4.79 % | +8.54 pp |
| Interacción | 28.89 pp | 12.78 pp | +16.11 pp |

Los valores no representan comportamiento humano real; corresponden a patrones introducidos de manera programática para validar que la capa analítica puede detectarlos.

---

## 19. Validación NLP

Primero genere o utilice un dataset NLP:

```powershell
python -m scripts.export_nlp_dataset
```

Después ejecute:

```powershell
python -m scripts.train_nlp_model --output-prefix nlp_distilbert_gpu --epochs 4 --batch-size 16 --max-length 192
```

Si existe CUDA, PyTorch utilizará la GPU. El script localiza automáticamente el `nlp_dataset_*.csv` versionado más reciente cuando no se proporciona `--dataset`.

---

## 20. Generar reportes analíticos

HTML:

```powershell
python -m scripts.generate_analytic_html_report
```

PDF:

```powershell
python -m scripts.generate_analytic_pdf_report
```

Los reportes se almacenan versionados dentro de `data/reports/`.

---

## 21. Convención de versionado de artefactos

Los artefactos utilizan marcas temporales con formato:

```text
AAAAMMDD_HHMMSS
```

Ejemplo:

```text
20260905_132500
```

Esto permite conservar ejecuciones históricas y evita sobrescrituras.

Ejemplos:

```text
analytic_dataset_combined_20260905_132500.csv
baseline_logreg_combined_20260905_133000_metrics.json
xgboost_combined_20260905_133500_predictions.csv
analytic_report_20260905_134000.html
```

Todos los archivos generados por un mismo entrenamiento comparten el mismo identificador temporal.

---

## 22. Criterios para considerar una prueba exitosa

### Operativo

- Swagger responde en `:8000/docs`.
- Un usuario administrador puede autenticarse.
- Se pueden crear segmento, plantilla, target y campaña.
- El lanzamiento retorna un `task_id`.
- El worker procesa la tarea.
- El mensaje se genera en outbox o llega a la cuenta SMTP controlada.
- El tracker registra eventos a partir del `uid`.

### Analítico

- El dataset incluido puede ser leído sin errores.
- Baseline genera métricas y predicciones.
- XGBoost genera métricas e importancias.
- GLMM genera efectos fijos y predicciones.
- El dashboard muestra resultados y permite descargar CSV.
- Los cuatro escenarios sintéticos producen el resumen esperado.
- Los artefactos de una segunda ejecución no reemplazan los de la primera.

---

## 23. Solución de problemas frecuentes

### `ModuleNotFoundError`

Ejecute siempre los scripts desde la raíz del repositorio:

```powershell
python -m scripts.nombre_del_script
```

### Celery en Windows

Use:

```powershell
celery -A apps.worker.celery_app.celery_app worker --loglevel=info --pool=solo
```

### XGBoost sin CUDA

Use:

```powershell
--device cpu
```

### NLP muestra `Path(None)`

La versión final de `train_nlp_model.py` debe resolver el dataset automáticamente. No debe existir una asignación incondicional `Path(args.dataset)` fuera del bloque que comprueba si `args.dataset` es `None`.

### El dashboard no encuentra modelos

Verifique que exista un archivo con patrón:

```text
<prefijo>_<timestamp>_metrics.json
```

El dashboard obtiene la ejecución más reciente a partir del prefijo lógico configurado.

---

## 24. Estructura mínima recomendada para la entrega final

```text
/
|-- README.md
|-- .env.example
|-- docker-compose.yml
|-- Dockerfile
|-- apps/
|-- channels/
|-- core/
|-- data/
|   |-- samples/
|   |   `-- analytic_validation_dataset.csv
|   |-- exports/
|   |-- models/
|   `-- reports/
|-- db/
|-- docs/
|-- infra/
|-- ml/
`-- scripts/
```

---

## 25. Nota sobre reproducibilidad de resultados

Para una reproducción estricta se recomienda conservar:

- commit o tag del código;
- versión de Python;
- versiones de dependencias;
- semilla utilizada;
- dataset exacto;
- archivos `split.csv` cuando correspondan;
- métricas y predicciones con timestamp;
- logs de Docker/Celery;
- reportes generados.

Puede crear un tag asociado a la versión presentada en el trabajo de grado:

```powershell
git tag -a tesis-final-2026 -m "Versión reproducible del trabajo de grado"
git push origin tesis-final-2026
```

---

## 26. Alcance de los resultados

Los datasets de validación y los escenarios suministrados en este repositorio son sintéticos. Su propósito es permitir que un tercero pruebe la funcionalidad de la capa analítica sin necesidad de exponer personas reales a una simulación de phishing.

Los resultados permiten comprobar que el prototipo puede detectar, cuantificar y visualizar patrones presentes en los datos.
