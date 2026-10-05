# Architecture — Meditron 2026 Case 3

## 1. Назначение

Документ описывает архитектуру проекта **Meditron 2026 Case 3**: backend API, ML-инференс, экспертный движок, ноутбуки исследований, артефакты моделей, контейнеризацию и схему развёртывания.

Основная цель системы — предоставить сервис для получения ML-предсказаний и экспертных объяснений в медицинском домене, с возможностью внешней валидации и воспроизводимого пайплайна исследований.

---

## 2. Высокоуровневая архитектура

```text
┌─────────────────────┐        HTTP        ┌──────────────────────────────┐
│      Frontend       │  ───────────────>  │      Backend API             │
│  Vite / React / Nginx│ <───────────────  │      api/main.py             │
└─────────────────────┘                    │      FastAPI + Uvicorn       │
                                           └──────────────┬───────────────┘
                                                          │
                         ┌────────────────────────────────┼────────────────────────────────┐
                         │                                │                                │
                         v                                v                                v
              ┌────────────────────┐           ┌────────────────────┐           ┌────────────────────┐
              │   ML Inference     │           │   Expert System    │           │   SQLite Storage   │
              │ predictor.py       │           │ engine.py          │           │ meditron.db        │
              └────────────────────┘           └────────────────────┘           └────────────────────┘
                         ^
                         │
              ┌──────────────────────────────────────────────┐
              │        Artifacts / Notebooks                 │
              │  notebooks/artifacts/baselines               │
              │  notebooks/artifacts/hierarchical            │
              └──────────────────────────────────────────────┘
```

---

## 3. Структура репозитория

```text
Meditron_2026_Case_3/
├── api/
│   └── main.py
├── ml/
│   └── inference/
│       └── predictor.py
├── expert/
│   └── engine.py
├── notebooks/
│   ├── artifacts/
│   │   ├── baselines/
│   │   └── hierarchical/
│   ├── 01_eda_feature_selection.ipynb
│   ├── 02_model_baselines.ipynb
│   ├── 03_hierarchical_model.ipynb
│   ├── 04_rules_calibration_ensemble.ipynb
│   ├── 05_expert_system_explanations.ipynb
│   ├── 06_external_validation.ipynb
│   ├── 06_external_validation_part1.ipynb
│   ├── 06_external_validation_part2_build_inference_bundle.ipynb
│   ├── 06_external_validation_part3_nhanes_preparation.ipynb
│   ├── 06_external_validation_part4_frozen_inference.ipynb
│   ├── 06_external_validation_part5_final_report.ipynb
│   ├── 07_expert_system.ipynb
│   ├── clinical_hypotheses_full.ipynb
│   ├── expert_system_explanations.ipynb
│   ├── preprocessing_with_explanations.ipynb
│   └── rules_calibration_ensemble.ipynb
├── frontend/
│   └── Dockerfile
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
└── README_MIGRATION.md
```

Ключевые пути артефактов:

- `Meditron_2026_Case_3/notebooks/artifacts/baselines/`
- `notebooks/artifacts/hierarchical/`

---

## 4. Компоненты системы

### 4.1 Backend API

- Точка входа: `api/main.py`
- Фреймворк: FastAPI
- ASGI-сервер: Uvicorn
- Порт: `8000`
- Назначение:
  - приём запросов от frontend;
  - валидация входных данных;
  - вызов ML-инференса;
  - вызов экспертного движка;
  - сохранение/чтение данных из SQLite;
  - возврат предсказаний и объяснений.

### 4.2 ML Inference

- Модуль: `ml/inference/predictor.py`
- Назначение:
  - загрузка обученных моделей и артефактов;
  - предобработка входных признаков;
  - получение предсказаний;
  - поддержка baseline- и hierarchical-моделей;
  - подготовка данных для экспертного слоя.

### 4.3 Expert System

- Модуль: `expert/engine.py`
- Назначение:
  - применение клинических и логических правил;
  - калибровка и интерпретация предсказаний;
  - формирование объяснений;
  - объединение ML-результатов с экспертными выводами.

### 4.4 Frontend

- Сборка: Vite
- Раздача: Nginx
- Контейнер: `meditron_frontend`
- Порт: `3000:80`
- Параметры сборки:
  - `VITE_API_URL=http://localhost:8000`
  - `VITE_USE_MOCKS=false`
  - `VITE_REQUEST_FORMAT=features`

### 4.5 Хранилище

- Тип: SQLite
- Файл: `/app/data_runtime/meditron.db`
- Volume: `meditron_db`
- Подключение через `DATABASE_URL=sqlite:////app/data_runtime/meditron.db`

### 4.6 Ноутбуки и исследования

Ноутбуки формируют воспроизводимый исследовательский пайплайн: от EDA и baseline-моделей до иерархической модели, экспертных правил, калибровки, ансамблирования и внешней валидации.

---

## 5. Поток данных

1. Пользователь отправляет запрос через frontend.
2. Frontend обращается к backend API по `VITE_API_URL`.
3. `api/main.py` принимает запрос и валидирует признаки.
4. API вызывает `ml/inference/predictor.py`.
5. Predictor загружает нужные артефакты из `notebooks/artifacts/baselines/` или `notebooks/artifacts/hierarchical/`.
6. Predictor возвращает ML-предсказание.
7. API передаёт результат в `expert/engine.py`.
8. Expert engine применяет правила, калибровку и формирует объяснение.
9. API сохраняет необходимые данные в SQLite.
10. API возвращает frontend структурированный ответ: предсказание + объяснение + метаданные.

---

## 6. Артефакты и модели

### 6.1 Baseline-артефакты

Путь: `Meditron_2026_Case_3/notebooks/artifacts/baselines/`

Содержит результаты baseline-подхода:
- обученные модели;
- метрики;
- промежуточные датасеты;
- параметры предобработки;
- файлы для сравнения.

### 6.2 Hierarchical-артефакты

Путь: `notebooks/artifacts/hierarchical/`

Содержит результаты иерархического моделирования:
- модели верхнего и нижнего уровня;
- калиброванные вероятности;
- правила перехода между уровнями;
- метрики качества;
- артефакты для инференса.

---

## 7. Ноутбуки и пайплайн

| Ноутбук | Назначение |
|---|---|
| `01_eda_feature_selection.ipynb` | EDA и отбор признаков |
| `02_model_baselines.ipynb` | Базовые модели и сравнение |
| `03_hierarchical_model.ipynb` | Иерархическая модель |
| `04_rules_calibration_ensemble.ipynb` | Правила, калибровка, ансамбль |
| `05_expert_system_explanations.ipynb` | Объяснения экспертной системы |
| `06_external_validation.ipynb` | Внешняя валидация |
| `06_external_validation_part1.ipynb` | Внешняя валидация, часть 1 |
| `06_external_validation_part2_build_inference_bundle.ipynb` | Сборка inference bundle |
| `06_external_validation_part3_nhanes_preparation.ipynb` | Подготовка NHANES |
| `06_external_validation_part4_frozen_inference.ipynb` | Frozen inference |
| `06_external_validation_part5_final_report.ipynb` | Финальный отчёт |
| `07_expert_system.ipynb` | Экспертная система |
| `clinical_hypotheses_full.ipynb` | Клинические гипотезы |
| `expert_system_explanations.ipynb` | Объяснения экспертной системы |
| `preprocessing_with_explanations.ipynb` | Препроцессинг с объяснениями |
| `rules_calibration_ensemble.ipynb` | Калибровка правил и ансамбль |

---

## 8. Контейнеризация и запуск

### 8.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.2 docker-compose.yml

```yaml
services:

  backend:
    build:
      context: .
      dockerfile: Dockerfile

    container_name: meditron_backend

    ports:
      - "8000:8000"

    env_file:
      - .env

    environment:
      DATABASE_URL: sqlite:////app/data_runtime/meditron.db

    volumes:
      - meditron_db:/app/data_runtime

    restart: unless-stopped


  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_URL: http://localhost:8000
        VITE_USE_MOCKS: "false"
        VITE_REQUEST_FORMAT: features

    container_name: meditron_frontend

    ports:
      - "3000:80"

    depends_on:
      - backend

    restart: unless-stopped


volumes:
  meditron_db:
```

### 8.3 Переменные окружения

| Переменная | Назначение | Пример |
|---|---|---|
| `DATABASE_URL` | Подключение к SQLite | `sqlite:////app/data_runtime/meditron.db` |
| `VITE_API_URL` | URL backend API для frontend | `http://localhost:8000` |
| `VITE_USE_MOCKS` | Использование mock-данных | `false` |
| `VITE_REQUEST_FORMAT` | Формат запроса | `features` |

---

## 9. Запуск

### Локальная разработка

```bash
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Docker Compose

```bash
docker compose up --build
```

После запуска:

- backend: `http://localhost:8000`
- frontend: `http://localhost:3000`

---

## 10. Внешняя валидация

Внешняя валидация реализована через серию ноутбуков `06_external_validation_*`:

- подготовка данных;
- сборка inference bundle;
- подготовка NHANES;
- frozen inference;
- финальный отчёт.

Это позволяет проверить устойчивость модели на внешнем наборе данных и зафиксировать воспроизводимый протокол оценки.

---

## 11. Миграция

Файл `README_MIGRATION.md` предназначен для описания миграционных шагов, изменений структуры проекта, переноса артефактов и обновления окружения. В предоставленном фрагменте содержимое файла не приведено.

---

## 12. Расширение и поддержка

Возможные направления развития:

- добавление новых ML-моделей в `ml/inference/predictor.py`;
- расширение правил в `expert/engine.py`;
- подключение PostgreSQL вместо SQLite;
- выделение inference-сервиса в отдельный контейнер;
- добавление CI/CD для сборки и валидации артефактов;
- автоматизация external validation через DVC/MLflow;
- версионирование моделей и датасетов.

---

## 13. Краткое резюме

**Meditron 2026 Case 3** — это контейнеризованная система из frontend, FastAPI backend, ML-инференса, экспертного движка и SQLite-хранилища. Исследовательская часть построена на ноутбуках и артефактах `baselines` и `hierarchical`. Развёртывание выполняется через Docker Compose, что обеспечивает воспроизводимость и удобный запуск backend и frontend.
