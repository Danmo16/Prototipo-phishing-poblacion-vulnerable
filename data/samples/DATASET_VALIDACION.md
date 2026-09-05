# Dataset de validación analítica

Archivo asociado:

```text
data/samples/analytic_validation_dataset.csv
```

## Propósito

Permitir que un evaluador pruebe la capa analítica del proyecto sin ejecutar campañas ni poblar previamente PostgreSQL.

El conjunto es completamente sintético y no contiene datos personales reales.

## Diseño

- Semilla: `42`
- Escenario: `personalization`
- Filas: `600`
- Plantillas: `8`
- Segmentos: `5`
- Targets por combinación plantilla-segmento: `15`
- Objetivo de clasificación: `clicked_flag`

Se introdujo deliberadamente una mayor probabilidad de apertura cuando la señal `signal_personalization` está presente:

```text
P(apertura | personalización) = 0.48
P(apertura | sin personalización) = 0.26
P(clic | apertura) = 0.18
```

Con semilla 42 se espera aproximadamente:

```text
Apertura con personalización = 49.78 %
Apertura sin personalización = 24.80 %
Diferencia = +24.98 puntos porcentuales
```

## Columnas principales

- `source`
- `scenario`
- `scenario_seed`
- `campaign_id`
- `template_id`
- `signal_urgency`
- `signal_authority`
- `signal_reward`
- `signal_personalization`
- `segment_id`
- `age_bracket`
- `gender`
- `education`
- `delivered`
- `opened_flag`
- `clicked_flag`
- `reported_flag`

## Prueba rápida

Baseline:

```powershell
python -m scripts.train_baseline_model --dataset data/samples/analytic_validation_dataset.csv --output-prefix baseline_validation
```

XGBoost CPU:

```powershell
python -m scripts.train_xgboost_model --dataset data/samples/analytic_validation_dataset.csv --output-prefix xgboost_validation --device cpu
```

GLMM:

```powershell
python -m scripts.train_glmm_model --dataset data/samples/analytic_validation_dataset.csv --output-prefix glmm_validation --random-effect segment_id --method vb
```

Para usarlo en Streamlit:

```powershell
Copy-Item data/samples/analytic_validation_dataset.csv data/exports/analytic_dataset_combined_validation_20260905_000000.csv
streamlit run apps/dashboard/app.py
```

Seleccione la fuente `Combinado` en el dashboard.

## Interpretación

Este dataset solo permite validar técnicamente el pipeline. El patrón de personalización fue introducido de forma artificial y no debe interpretarse como evidencia sobre el comportamiento real de una población.
