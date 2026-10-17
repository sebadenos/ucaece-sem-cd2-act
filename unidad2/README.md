# Auditoría de equidad en contratación — Unidad 2, Seminario de Ciencia de Datos II

Componente práctico (consignas 7 a 11) del Análisis de Caso Individual. Verifica de forma
cuantitativa y reproducible el tipo de sesgo de género documentado en el sistema de
reclutamiento de Amazon (Dastin, 2018), lo mitiga con Fairlearn y lo explica con SHAP.

- **Alumno:** Sebastián Losinno
- **Caso analizado:** sistema de reclutamiento automatizado de Amazon (caso b)
- **Código:** carpeta [`unidad2/`](unidad2/) · **Resultados completos:** [`unidad2/evidencias.md`](unidad2/evidencias.md)

## Dataset utilizado

- **Nombre:** 70k+ Job Applicants Data (Human Resource) — Kaggle
  (https://www.kaggle.com/datasets/ayushtankha/70k-job-applicants-data-human-resource)
- **Contenido:** 73.462 postulantes a puestos de tecnología con variables de perfil
  (edad, nivel educativo, años de experiencia, país, salario previo, cantidad de tecnologías
  que manejan, etc.).
- **Columna objetivo:** `Employed` (1 = contratado, 0 = no contratado).
- **Preparación (ETL):** `unidad2/preparar_dataset.py` descarta el índice exportado
  (`Unnamed: 0`) y `HaveWorkedWith` (texto libre casi único por fila; su información ya está
  resumida en `ComputerSkills`). El pipeline toma una muestra aleatoria de 10.000 filas
  (semilla 42) y separa 70 % train / 30 % test.
- El CSV **no se versiona** (carpeta `data/` excluida en `.gitignore`).

## Atributo sensible

`Gender` (Man / Woman / NonBinary). Composición del dataset limpio: Man 93,3 %, Woman 4,8 %,
NonBinary 1,9 %. Tasa real de contratación: Man 0,541, Woman 0,449, NonBinary 0,533.

## Métricas de equidad (conjunto de test)

Modelo: regresión logística. Mitigación: `ambos` (ExponentiatedGradient y
ThresholdOptimizer) con restricción `demographic_parity`.

| Escenario | Exactitud | Demographic parity diff. | Equalized odds diff. |
|---|---|---|---|
| Modelo base (sin mitigar) | 0.788 | 0.195 | 0.159 |
| ExponentiatedGradient | 0.788 | 0.068 | 0.093 |
| ThresholdOptimizer | 0.791 | 0.091 | 0.109 |

Tasa de selección del modelo base: Man 0.529 · Woman 0.472 · NonBinary 0.333
(*demographic parity ratio* = 0.630, por debajo del umbral de 0.80).

Corrida complementaria con `FAIRNESS_CONSTRAINT=equalized_odds`: ExponentiatedGradient
llega a una EOD de 0.052 (exactitud 0.783) y ThresholdOptimizer a 0.129 (exactitud 0.776).

**Lectura breve:** el modelo base favorece al grupo masculino mayoritario y la desventaja
crece cuanto menos representado está el grupo. Con las mujeres reproduce la brecha que ya
existe en los datos reales, y con las personas no binarias la amplifica (8,1 puntos reales
frente a 19,6 predichos). ExponentiatedGradient fue la técnica más
efectiva: redujo la DPD un 65 % sin perder exactitud. Ninguna configuración minimiza las dos
métricas a la vez, y SHAP muestra que, para las mujeres, la brecha no se explica por la
variable de género sino por otras variables que actúan como proxies. Detalle completo en
[`unidad2/evidencias.md`](unidad2/evidencias.md).

## Cómo ejecutarlo

1. Abrir el repositorio en GitHub Codespaces: **Code → Codespaces → "..." → New with options**
   → configuración `unidad2-seminario-cd2`.
2. Descargar `stackoverflow_full.csv` de Kaggle y copiarlo a `unidad2/data/`.
3. En la terminal (parada en `unidad2/`):

   ```bash
   python preparar_dataset.py
   cp .env.example .env
   ```

4. Completar `.env`:

   ```env
   DATASET_PATH=data/job_applicants_limpio.csv
   TARGET_COLUMN=Employed
   SENSITIVE_ATTRIBUTE=Gender
   POSITIVE_LABEL=1
   MITIGATION_METHOD=ambos
   FAIRNESS_CONSTRAINT=demographic_parity
   ```

5. Ejecutar:

   ```bash
   python -m src.main
   ```

   Genera `evidencias.md` y los gráficos de `outputs/`.
