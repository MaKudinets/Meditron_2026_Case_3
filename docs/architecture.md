# Architecture — Meditron 2026 Case 3

## 1. Назначение

Документ описывает архитектуру проекта **Meditron 2026 Case 3**: backend API, ML-инференс, экспертный движок, ноутбуки исследований, артефакты моделей, контейнеризацию и схему развёртывания.

Основная цель системы — предоставить сервис для получения ML-предсказаний и экспертных объяснений в медицинском домене, с возможностью внешней валидации и воспроизводимого пайплайна исследований.

---

## 2. Высокоуровневая архитектура

```text
┌─────────────────────┐        HTTP        ┌──────────────────────────────┐
│      Frontend       │  ───────────────>  │      Backend API             │
│ Vite / React / Nginx│ <───────────────   │      api/main.py             │
└─────────────────────┘                    │      FastAPI + Uvicorn       │
                                           └──────────────┬───────────────┘
                                                          │
                         ┌────────────────────────────────┼────────────────────────────────┐
                         │                                │                                │
                         v                                v                                v
              ┌────────────────────┐           ┌────────────────────┐           ┌────────────────────┐
              │   ML Inference     │           │   Expert System    │           │   SQLite Storage   │
              │ ml/inference/      │           │ expert/engine.py   │           │ meditron.db        │
              └────────────────────┘           └────────────────────┘           └────────────────────┘
                         ^
                         │
              ┌──────────────────────────────────────────────┐
              │        Artifacts / Notebooks                 │
              │  ml/artifacts/                               │
              │  notebooks/artifacts/baselines               │
              │  notebooks/artifacts/hierarchical            │
              └──────────────────────────────────────────────┘
```

---

## 3. Структура репозитория

```text
Meditron_2026_Case_3/
├── api/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── init_db.py
│   │   └── models.py
│   ├── resources/
│   │   ├── __init__.py
│   │   └── lab_groups.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── doctor_imports.py
│   │   ├── doctor_patients.py
│   │   ├── doctor_screenings.py
│   │   ├── health.py
│   │   ├── history.py
│   │   ├── imports.py
│   │   ├── metadata.py
│   │   ├── screenings.py
│   │   └── trends.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── common.py
│   │   ├── doctor_imports.py
│   │   ├── doctor_patients.py
│   │   ├── doctor_screenings.py
│   │   ├── history.py
│   │   ├── imports.py
│   │   ├── request.py
│   │   ├── response.py
│   │   └── trends.py
│   ├── security/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── passwords.py
│   │   └── tokens.py
│   └── main.py
├── ml/
│   ├── artifacts/
│   │   ├── class_mapping.json
│   │   └── feature_list.json
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── ensemble.py
│   │   ├── loader.py
│   │   └── predictor.py
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── features.py
│   │   ├── medical_features.py
│   │   └── validator.py
│   └── training/
│       ├── __init__.py
│       ├── calibration.py
│       ├── evaluate.py
│       ├── train_catboost.py
│       └── train_l1.py
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
- `ml/artifacts/`

---

## 4. Компоненты системы

### 4.1 Backend API (модуль `api/`)

Модуль `api/` реализует слой взаимодействия с клиентом и внутренней логикой приложения. Он разделён на следующие подпакеты:

- **`api/main.py`** — точка входа приложения FastAPI. Инициализация приложения, подключение роутеров, настройка CORS и middleware.
- **`api/routes/`** — HTTP-эндпоинты, сгруппированные по доменным областям:
  - `auth.py` — аутентификация и авторизация;
  - `doctor_imports.py`, `doctor_patients.py`, `doctor_screenings.py` — функциональность для врачей;
  - `health.py` — проверка работоспособности сервиса;
  - `history.py` — история приёмов/анализов;
  - `imports.py` — импорт данных;
  - `metadata.py` — метаданные системы;
  - `screenings.py` — скрининги;
  - `trends.py` — тренды и динамика показателей.
- **`api/schemas/`** — Pydantic-схемы для валидации входящих запросов и формирования ответов:
  - `auth.py`, `common.py`, `request.py`, `response.py`;
  - схемы для врачей и импортов: `doctor_imports.py`, `doctor_patients.py`, `doctor_screenings.py`;
  - схемы для истории, импортов и трендов: `history.py`, `imports.py`, `trends.py`.
- **`api/database/`** — работа с базой данных:
  - `database.py` — подключение и сессия SQLAlchemy;
  - `init_db.py` — инициализация схемы БД;
  - `models.py` — ORM-модели.
- **`api/security/`** — безопасность:
  - `auth.py` — логика аутентификации;
  - `passwords.py` — хэширование и проверка паролей;
  - `tokens.py` — генерация и валидация JWT-токенов.
- **`api/resources/`** — статические справочники и вспомогательные данные:
  - `lab_groups.py` — группы лабораторных показателей.

### 4.2 ML-модуль (модуль `ml/`)

Модуль `ml/` содержит всю логику машинного обучения: от препроцессинга и обучения до инференса и ансамблирования.

- **`ml/artifacts/`** — сериализованные артефакты, необходимые для инференса:
  - `class_mapping.json` — соответствие классов и их идентификаторов;
  - `feature_list.json` — список признаков, ожидаемых моделью.
- **`ml/inference/`** — логика инференса:
  - `loader.py` — загрузка моделей и артефактов;
  - `ensemble.py` — логика ансамблирования предсказаний;
  - `predictor.py` — основной модуль получения предсказаний.
- **`ml/preprocessing/`** — предобработка данных:
  - `features.py` — общая инженерия признаков;
  - `medical_features.py` — специфические медицинские признаки;
  - `validator.py` — валидация входных данных.
- **`ml/training/`** — обучение и оценка моделей:
  - `train_catboost.py` — обучение модели CatBoost;
  - `train_l1.py` — обучение модели первого уровня (L1);
  - `calibration.py` — калибровка вероятностей;
  - `evaluate.py` — расчёт метрик качества.

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
3. `api/main.py` принимает запрос, валидирует его через схемы в `api/schemas/`.
4. Роутер из `api/routes/` обрабатывает запрос и при необходимости обращается к `api/database/` или `api/security/`.
5. API вызывает `ml/inference/predictor.py`.
6. Predictor использует `ml/inference/loader.py` для загрузки моделей и артефактов из `ml/artifacts/`, а также `ml/inference/ensemble.py` для агрегации.
7. Предобработка входных данных выполняется через `ml/preprocessing/features.py` и `ml/preprocessing/validator.py`.
8. Predictor возвращает ML-предсказание.
9. API передаёт результат в `expert/engine.py`.
10. Expert engine применяет правила, калибровку и формирует объяснение.
11. API сохраняет необходимые данные в SQLite.
12. API возвращает frontend структурированный ответ: предсказание + объяснение + метаданные.

---

## 6. Артефакты и модели

### 6.1 ML-артефакты

Путь: `ml/artifacts/`

Содержит:
- `class_mapping.json` — маппинг классов;
- `feature_list.json` — перечень признаков.

### 6.2 Baseline-артефакты

Путь: `Meditron_2026_Case_3/notebooks/artifacts/baselines/`

Содержит результаты baseline-подхода:
- обученные модели;
- метрики;
- промежуточные датасеты;
- параметры предобработки;
- файлы для сравнения.

### 6.3 Hierarchical-артефакты

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

Файл `README_MIGRATION.md` предназначен для описания миграционных шагов, изменений структуры проекта, переноса артефактов и обновления окружения.

---

## 12. Расширение и поддержка

Возможные направления развития:

- добавление новых ML-моделей в `ml/training/` и `ml/inference/`;
- расширение правил в `expert/engine.py`;
- подключение PostgreSQL вместо SQLite;
- выделение inference-сервиса в отдельный контейнер;
- добавление CI/CD для сборки и валидации артефактов;
- автоматизация external validation через DVC/MLflow;
- версионирование моделей и датасетов;
- расширение API-схем и роутеров в соответствии с новыми бизнес-требованиями.

---

## 13. Краткое резюме

**Meditron 2026 Case 3** — это контейнеризованная система из frontend, модульного FastAPI backend, ML-модуля, экспертного движка и SQLite-хранилища. Backend API разделён на слои: маршруты (`routes`), схемы (`schemas`), база данных (`database`), безопасность (`security`) и справочники (`resources`). ML-модуль включает артефакты, инференс, препроцессинг и обучение. Исследовательская часть построена на ноутбуках и артефактах `baselines` и `hierarchical`. Развёртывание выполняется через Docker Compose, что обеспечивает воспроизводимость и удобный запуск backend и frontend.
