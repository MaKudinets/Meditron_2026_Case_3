# Meditron API Contract

Полный контракт взаимодействия frontend и backend: маршруты, доступ, запросы,
ответы, импорт файлов, история, динамика показателей и PDF.

- Дата сверки: **5 октября 2026 года**.
- Репозиторий: [MaKudinets/Meditron_2026_Case_3](https://github.com/MaKudinets/Meditron_2026_Case_3).
- Проверенная ветка: **develop**.
- Проверенный коммит: `c1af6e1869b9298b6766ad7c82ae491d885f86ce`.
- Версия FastAPI-приложения: **0.1.0**; префикс основных маршрутов: **/api/v1**.
- Текущий ML bundle: `meditron_frozen_inference_bundle`, версия `1.0`, 37 признаков, 6 целевых веток.

Документ описывает код указанного коммита. В проверенном `main` находится пустой
каркас, поэтому перенос этого контракта в `main` должен сопровождать перенос
рабочего backend. Числа в примерах форматов не являются медицинскими рекомендациями.
Полный пример ответа в разделе 6 взят из `data/demo/expected/patient_example_result.json`.

## Содержание

1. [Общие правила](#1-общие-правила)
2. [Все маршруты](#2-все-маршруты)
3. [Системные маршруты](#3-системные-маршруты)
4. [Авторизация](#4-авторизация)
5. [Входные признаки](#5-входные-признаки)
6. [Скрининг и его результат](#6-скрининг-и-его-результат)
7. [Импорт пациента](#7-импорт-пациента)
8. [История пациента](#8-история-пациента)
9. [Работа врача](#9-работа-врача)
10. [Динамика и референсы](#10-динамика-и-референсы)
11. [PDF](#11-pdf)
12. [Ошибки и неполные данные](#12-ошибки-и-неполные-данные)
13. [Интеграция frontend](#13-интеграция-frontend)
14. [Ограничения текущего контракта](#14-ограничения-текущего-контракта)
15. [Полный справочник схем](#15-полный-справочник-схем)
16. [Поддержка актуальности](#16-поддержка-актуальности)

## 1. Общие правила

### 1.1. Адреса и форматы

| Назначение | Значение |
| --- | --- |
| Backend локально | `http://127.0.0.1:8000` или `http://localhost:8000` |
| Frontend через Docker Compose | `http://localhost:3000` |
| Frontend через Vite | обычно `http://localhost:5173` |
| Swagger UI | `/docs` |
| ReDoc | `/redoc` |
| OpenAPI JSON | `/openapi.json` |
| Обычные тела запросов/ответов | `application/json` |
| Загрузка файла | `multipart/form-data`, поле `file` |
| Успешное скачивание отчёта | `application/pdf`, бинарное тело |

`VITE_API_URL` содержит адрес backend без `/api/v1`; пути в конфигурации frontend
уже включают этот префикс. `/` и `/health` расположены вне `/api/v1`.
Не добавлять завершающий `/` к маршрутам, у которых его нет в таблице.

### 1.2. Типы, пропуски и идентификаторы

- JSON-ключи чувствительны к регистру: `TIBC`, `vitamin_B12`, `RBC`.
- Числовые признаки отправлять JSON-числами, с точкой как десятичным разделителем.
  Pydantic может приводить некоторые значения к числу, но frontend не должен
  рассчитывать на эту особенность.
- Необязательные признаки можно не отправлять либо передавать `null`.
  Перед inference `null` удаляются; пропуск не означает нулевое или нормальное значение.
- `sex` и `hemoglobin` обязательны и не могут быть `null`.
- Пустая строка не заменяет `null`. Не отправлять `NaN`, бесконечности и отрицательные анализы.
- Даты сериализуются как ISO 8601. В SQLite сохранённые даты могут возвращаться
  без смещения часового пояса; frontend должен учитывать, что backend использует UTC.
- `screening_id` — идентификатор результата; у новых результатов `uuid4().hex`.
  `patient_id` полного ответа — внешний ID публичного запроса либо внутренний ID
  профиля при сохранённом скрининге. `patient_code` — код пациента в кабинете врача.
  Эти три значения не взаимозаменяемы.
- Модели запросов скрининга и авторизации запрещают лишние поля (`extra="forbid"`).
  Вложенная `ImportedLabMetadata` использует стандартное поведение Pydantic:
  неизвестные поля игнорируются. Не считать это разрешением переименовывать поля.

### 1.3. Доступ

Защищённые запросы используют заголовок:

```http
Authorization: Bearer <access_token>
```

Токен — непрозрачная случайная строка, а не JWT. Сервер проверяет сессию в БД.
Публичный скрининг не требует токена и не сохраняет историю. Авторизованный
скрининг пациента и пакетный скрининг врача сохраняют результаты.

## 2. Все маршруты

В таблице: «публичный» — без токена; «сессия» — любой вошедший пользователь;
«пациент»/«врач» — сессия с соответствующей ролью. Указан код успешного ответа.

| Метод | Путь | Доступ | Успех | Тело запроса → ответ |
| --- | --- | --- | --- | --- |
| GET | `/` | публичный | 200 | — → объект состояния сервиса |
| GET | `/health` | публичный | 200 | — → health-объект |
| GET | `/api/v1/meta/features` | публичный | 200 | — → контракт признаков |
| GET | `/api/v1/meta/model` | публичный | 200 | — → сведения о bundle |
| POST | `/api/v1/auth/register` | публичный | 201 | RegisterRequest → RegisterResponse |
| POST | `/api/v1/auth/verify-email` | публичный | 200 | VerifyEmailRequest → MessageResponse |
| POST | `/api/v1/auth/resend-verification` | публичный | 200 | ResendVerificationRequest → MessageResponse |
| POST | `/api/v1/auth/login` | публичный | 200 | LoginRequest → LoginResponse |
| GET | `/api/v1/auth/me` | сессия | 200 | — → UserResponse |
| POST | `/api/v1/auth/logout` | сессия | 200 | без тела → MessageResponse |
| POST | `/api/v1/auth/forgot-password` | публичный | 200 | ForgotPasswordRequest → MessageResponse |
| POST | `/api/v1/auth/reset-password` | публичный | 200 | ResetPasswordRequest → MessageResponse |
| POST | `/api/v1/screenings` | публичный | 200 | ScreeningRequest → ScreeningResponse |
| POST | `/api/v1/me/imports/lab-file` | пациент | 200 | multipart file → FileImportResponse |
| POST | `/api/v1/me/screenings` | пациент | 201 | MeScreeningRequest → ScreeningResponse |
| GET | `/api/v1/me/screenings` | пациент | 200 | — → ScreeningHistoryResponse |
| GET | `/api/v1/me/screenings/{screening_id}` | пациент | 200 | — → ScreeningResponse |
| DELETE | `/api/v1/me/screenings/{screening_id}` | пациент | 200 | — → DeleteScreeningResponse |
| GET | `/api/v1/me/screenings/{screening_id}/report.pdf` | пациент | 200 | — → PDF |
| GET | `/api/v1/me/trends` | пациент | 200 | — → TrendsResponse |
| POST | `/api/v1/doctor/imports/lab-file` | врач | 200 | multipart file → DoctorBulkImportResponse |
| POST | `/api/v1/doctor/screenings/bulk` | врач | 200 | DoctorBulkScreeningRequest → DoctorBulkScreeningResponse |
| GET | `/api/v1/doctor/patients` | врач | 200 | — → DoctorPatientListResponse |
| GET | `/api/v1/doctor/patients/{patient_code}/screenings` | врач | 200 | — → ScreeningHistoryResponse |
| GET | `/api/v1/doctor/patients/{patient_code}/screenings/{screening_id}` | врач | 200 | — → ScreeningResponse |
| GET | `/api/v1/doctor/patients/{patient_code}/trends` | врач | 200 | — → TrendsResponse |
| GET | `/api/v1/doctor/patients/{patient_code}/screenings/{screening_id}/report.pdf` | врач | 200 | — → PDF |

Всего 27 прикладных маршрутов. Автоматические `/docs`, `/redoc`, `/openapi.json`
в это число не входят. Query-параметры пагинации, фильтров и сортировки в текущих
маршрутах не объявлены.

## 3. Системные маршруты

`GET /`:

```json
{"service":"Meditron API","status":"running","docs":"/docs"}
```

`GET /health` проверяет загрузку ML bundle и доступность expert engine:

```json
{"status":"ok","api":"ok","ml_bundle_loaded":true,"expert_engine_available":true,"bundle_version":"1.0"}
```

При недоступности одного из компонентов возвращается HTTP 200 с `status="degraded"`.
`bundle_version` может быть `null`. HTTP 200 этого маршрута сам по себе не доказывает
готовность inference; health не проверяет SMTP и работоспособность БД.

`GET /api/v1/meta/features` возвращает `n_features`, `features`, `numeric_features`,
`categorical_features`, `targets` из `artifacts/inference_bundle/feature_contract.json`.
Список содержит 37 признаков, из них `sex` — единственный категориальный.

`GET /api/v1/meta/model` возвращает `bundle_name`, `bundle_version`, `purpose`,
`n_features`, `targets`, `architecture`. Значения берутся из manifest.
Эти маршруты не возвращают лабораторные единицы и референсные интервалы;
не использовать их как лабораторный справочник.

## 4. Авторизация

### 4.1. Регистрация, подтверждение почты и вход

`POST /api/v1/auth/register`, HTTP 201:

```json
{"email":"patient@example.com","password":"DemoPass123!","role":"patient"}
```

`role`: только `patient` или `doctor`; пароль регистрации — 8–128 символов.
Email проверяется как `EmailStr` и нормализуется сервисом.

```json
{"user":{"id":"user-example","email":"patient@example.com","role":"patient","is_email_verified":false},"message":"Registration successful. Email verification is required.","email_sent":true}
```

Регистрация не возвращает токен входа. При сбое отправки письма пользователь
остаётся зарегистрированным, ответ — 201 с `email_sent=false`. Занятый email — 409.

`POST /api/v1/auth/verify-email`: `{"token":"<токен из ссылки подтверждения>"}`;
токен 20–512 символов. Успех:
`{"message":"Email successfully verified."}`; неверный/истёкший токен — 400.
Срок подтверждения email в коде — 24 часа.

`POST /api/v1/auth/resend-verification`: `{"email":"patient@example.com"}`.
Ответ одинаков для отсутствующего аккаунта и аккаунта, требующего подтверждения:

```json
{"message":"If the account exists and requires verification, a verification message has been sent."}
```

`POST /api/v1/auth/login`: `{"email":"patient@example.com","password":"DemoPass123!"}`.
Для входа схема допускает пароль длиной 1–128 символов. Ответ:

```json
{"access_token":"<непрозрачный токен сессии>","token_type":"bearer","expires_at":"2026-10-12T09:00:00Z","user":{"id":"user-example","email":"patient@example.com","role":"patient","is_email_verified":true}}
```

Неверные credentials — 401 `Invalid email or password`; неподтверждённая почта —
403 `Email verification is required`. Срок сессии по умолчанию 168 часов,
настраивается `SESSION_TTL_HOURS`; ориентироваться на `expires_at` конкретного ответа.

### 4.2. Сессия и сброс пароля

- `GET /api/v1/auth/me` → `UserResponse` текущей сессии.
- `POST /api/v1/auth/logout` без тела отзывает текущую сессию →
  `{"message":"Successfully logged out."}`.
- `POST /api/v1/auth/forgot-password`, тело `{"email":"patient@example.com"}` →
  `{"message":"If an account with this email exists, password reset instructions have been sent."}`.
  Этот ответ не доказывает существование аккаунта или доставку письма.
- `POST /api/v1/auth/reset-password`, тело
  `{"token":"<токен сброса>","new_password":"NewDemoPass123!"}` →
  `{"message":"Password successfully changed."}`.
  Токен 20–512 символов, новый пароль 8–128; неверный/истёкший токен — 400.
  Срок сброса по умолчанию 30 минут, переменная `PASSWORD_RESET_TTL_MINUTES`.

В `.env.example` установлен `EMAIL_MODE=console`: для локального demo ссылки
следует получать из серверного вывода. Это не реальная SMTP-доставка.
Refresh-token endpoint в текущем API отсутствует.

## 5. Входные признаки

`PatientFeatures` совпадает по именам с frozen feature contract.
В модели API обязательны только `sex` и `hemoglobin`; все остальные поля
необязательны, по умолчанию `null`. Все лабораторные числа должны быть ≥ 0,
возраст — от 0 до 120. Дополнительных верхних границ для лабораторных полей
Pydantic-схема не задаёт.

Таблица ниже воспроизводит единицы и fallback-референсы **из текущего backend-каталога**.
Это описание реализации, а не универсальные нормы: каталог, например, не выбирает
референс гемоглобина по полу/возрасту. «Не задано» означает отсутствие единицы
в каталоге. Схема JSON не проверяет единицы и не конвертирует значения по `lab_metadata`;
перед inference значения должны соответствовать шкале, на которой обучена модель.
При незаданной единице сверить шкалу с командой ML, не придумывать её по имени анализа.

| JSON key | Название | Тип / обязательность | Единица каталога | Fallback-референс |
| --- | --- | --- | --- | --- |
| `age_years` | Возраст | number или null; необязательно | годы | не задан |
| `sex` | Пол | string F/M; обязательно | — | не задан |
| `hemoglobin` | Гемоглобин | number; обязательно | г/л | 120–150 |
| `RBC` | Эритроциты | number или null; необязательно | 10¹²/л | не задан |
| `hematocrit` | Гематокрит | number или null; необязательно | % | не задан |
| `MCV` | MCV | number или null; необязательно | фл | 80–100 |
| `MCH` | MCH | number или null; необязательно | пг | 27–34 |
| `MCHC` | MCHC | number или null; необязательно | г/л | не задан |
| `RDW` | RDW | number или null; необязательно | % | не задан |
| `platelets` | Тромбоциты | number или null; необязательно | 10⁹/л | не задан |
| `WBC` | Лейкоциты | number или null; необязательно | 10⁹/л | не задан |
| `reticulocytes` | Ретикулоциты | number или null; необязательно | % | не задан |
| `ferritin` | Ферритин | number или null; необязательно | нг/мл | 15–150 |
| `serum_iron` | Железо | number или null; необязательно | мкмоль/л | 9–30 |
| `transferrin` | Трансферрин | number или null; необязательно | г/л | не задан |
| `TIBC` | ОЖСС | number или null; необязательно | мкмоль/л | 45–72 |
| `UIBC` | НЖСС | number или null; необязательно | мкмоль/л | не задан |
| `TSAT` | Насыщение трансферрина | number или null; необязательно | % | 20–45 |
| `sTfR` | Растворимый рецептор трансферрина | number или null; необязательно | не задано | не задан |
| `Ret_He` | Ret-He | number или null; необязательно | пг | не задан |
| `vitamin_B12` | Витамин B12 | number или null; необязательно | пг/мл | не задан |
| `active_B12` | Активный B12 | number или null; необязательно | не задано | не задан |
| `MMA` | Метилмалоновая кислота | number или null; необязательно | не задано | не задан |
| `homocysteine` | Гомоцистеин | number или null; необязательно | мкмоль/л | не задан |
| `folate` | Фолат | number или null; необязательно | нг/мл | не задан |
| `vitamin_B6` | Витамин B6 | number или null; необязательно | не задано | не задан |
| `copper` | Медь | number или null; необязательно | не задано | не задан |
| `ceruloplasmin` | Церулоплазмин | number или null; необязательно | не задано | не задан |
| `CRP` | С-реактивный белок | number или null; необязательно | мг/л | не задан |
| `ESR` | СОЭ | number или null; необязательно | мм/ч | не задан |
| `creatinine` | Креатинин | number или null; необязательно | мкмоль/л | не задан |
| `eGFR` | СКФ | number или null; необязательно | мл/мин/1,73 м² | не задан |
| `TSH` | ТТГ | number или null; необязательно | мМЕ/л | не задан |
| `albumin` | Альбумин | number или null; необязательно | г/л | не задан |
| `LDH` | ЛДГ | number или null; необязательно | Ед/л | не задан |
| `indirect_bilirubin` | Непрямой билирубин | number или null; необязательно | мкмоль/л | не задан |
| `haptoglobin` | Гаптоглобин | number или null; необязательно | не задано | не задан |

## 6. Скрининг и его результат

### 6.1. Публичный скрининг

`POST /api/v1/screenings`, HTTP 200. Запускает pipeline, но не сохраняет результат
в БД. `patient_id` необязателен и не поступает в модель.

```json
{"patient_id":"DEMO-P001","features":{"age_years":35,"sex":"F","hemoglobin":108,"ferritin":7.2,"MCV":74,"TIBC":82,"TSAT":9.5}}
```

Не отправлять в этот маршрут `lab_metadata` или `source_filename`: они отсутствуют
в `ScreeningRequest`, поэтому запрос будет отклонён с 422.

### 6.2. Скрининг авторизованного пациента

`POST /api/v1/me/screenings`, Bearer с ролью `patient`, HTTP 201.
Выполняет pipeline и сохраняет скрининг и лабораторные значения в историю.
ID пациента определяется сессией; поле `patient_id` в запросе отсутствует.

```json
{
  "features": {
    "age_years": 35,
    "sex": "F",
    "hemoglobin": 108,
    "ferritin": 7.2
  },
  "lab_metadata": {
    "hemoglobin": {
      "unit": "г/л",
      "reference_low": 120,
      "reference_high": 150,
      "reference_text": "120–150"
    },
    "ferritin": {
      "unit": "нг/мл",
      "reference_low": 15,
      "reference_high": 150,
      "reference_text": "15–150"
    }
  },
  "source_filename": "patient_example.csv"
}
```

`lab_metadata` по умолчанию `{}`; `source_filename` — `null` либо строка до 255
символов. Непустой `source_filename` задаёт `source_type="file"`, иначе `"manual"`.
Метаданные для ключей, которых нет в непустых `features`, не сохраняются.
`lab_metadata` не передаётся в ML и не влияет на модельную вероятность.

### 6.3. Полный ответ ScreeningResponse

Оба маршрута возвращают одну схему. Ниже сохранённый demo-ответ из репозитория,
без подмены вероятностей и имён полей. Его `patient_id` относится к публичному demo;
в авторизованном маршруте это будет внутренний ID профиля.

```json
{
  "screening_id": "f1e2ab1916da4557bd93801c23a1a23a",
  "patient_id": "DEMO-P001",
  "prediction": {
    "anemia": true,
    "anemia_class": "iron_deficiency_anemia",
    "deficiency_cause": "iron_deficiency"
  },
  "confidence": {
    "basis": "weakest_positive_branch",
    "limiting_target": "B6_deficiency",
    "certainty": 0.6502,
    "level": "moderate"
  },
  "deficiencies": {
    "iron_deficiency": {
      "probability": 1.0,
      "prediction": true,
      "threshold": 0.4100000000000002,
      "rule_score": 0.95,
      "rule_state": "supports",
      "confidence": {
        "selected_state": "positive",
        "certainty": 1.0,
        "level": "high"
      }
    },
    "B12_deficiency": {
      "probability": 0.0001,
      "prediction": false,
      "threshold": 0.2600000000000001,
      "rule_score": 0.5,
      "rule_state": "unknown",
      "confidence": {
        "selected_state": "negative",
        "certainty": 0.9999,
        "level": "high"
      }
    },
    "folate_deficiency": {
      "probability": 0.0007,
      "prediction": false,
      "threshold": 0.4500000000000003,
      "rule_score": 0.1,
      "rule_state": "against",
      "confidence": {
        "selected_state": "negative",
        "certainty": 0.9993,
        "level": "high"
      }
    },
    "B6_deficiency": {
      "probability": 0.6502,
      "prediction": true,
      "threshold": 0.4500000000000003,
      "rule_score": 0.5,
      "rule_state": "unknown",
      "confidence": {
        "selected_state": "positive",
        "certainty": 0.6502,
        "level": "moderate"
      }
    },
    "copper_deficiency": {
      "probability": 0.0009,
      "prediction": false,
      "threshold": 0.18,
      "rule_score": 0.5,
      "rule_state": "unknown",
      "confidence": {
        "selected_state": "negative",
        "certainty": 0.9991,
        "level": "high"
      }
    },
    "inflammation_anemia": {
      "probability": 0.0002,
      "prediction": false,
      "threshold": 0.3800000000000002,
      "rule_score": 0.3,
      "rule_state": "unknown",
      "confidence": {
        "selected_state": "negative",
        "certainty": 0.9998,
        "level": "high"
      }
    }
  },
  "data_quality": {
    "coverage": 1.0,
    "used_features": [
      "age_years",
      "sex",
      "hemoglobin",
      "RBC",
      "hematocrit",
      "MCV",
      "MCH",
      "MCHC",
      "RDW",
      "platelets",
      "WBC",
      "reticulocytes",
      "ferritin",
      "serum_iron",
      "transferrin",
      "TIBC",
      "UIBC",
      "TSAT",
      "sTfR",
      "Ret_He",
      "vitamin_B12",
      "active_B12",
      "MMA",
      "homocysteine",
      "folate",
      "vitamin_B6",
      "copper",
      "ceruloplasmin",
      "CRP",
      "ESR",
      "creatinine",
      "eGFR",
      "TSH",
      "albumin",
      "LDH",
      "indirect_bilirubin",
      "haptoglobin"
    ],
    "missing_features": [],
    "warnings": []
  },
  "evidence": [
    {
      "target": "anemia",
      "feature": "hemoglobin",
      "value": 108.0,
      "criterion": "< 120.0 g/L",
      "direction": "supports",
      "strength": "hard deterministic",
      "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2"
    },
    {
      "target": "iron_deficiency",
      "feature": "Ret_He",
      "value": 26.8,
      "criterion": "< 30.6 pg",
      "direction": "supports",
      "strength": "strong diagnostic evidence",
      "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2"
    },
    {
      "target": "iron_deficiency",
      "feature": "ferritin",
      "value": 7.2,
      "criterion": "< 11.0 ng/mL",
      "direction": "supports",
      "strength": "strong evidence within iron profile",
      "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2"
    },
    {
      "target": "iron_deficiency",
      "feature": "serum_iron",
      "value": 7.8,
      "criterion": "< 10.7 umol/L",
      "direction": "supports",
      "strength": "moderate/supporting",
      "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2"
    },
    {
      "target": "iron_deficiency",
      "feature": "TSAT",
      "value": 9.5,
      "criterion": "< 17.8 %",
      "direction": "supports",
      "strength": "moderate/supporting",
      "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2"
    },
    {
      "target": "iron_deficiency",
      "feature": "TIBC",
      "value": 82.0,
      "criterion": "> 78.0 umol/L",
      "direction": "supports",
      "strength": "moderate/supporting",
      "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2"
    },
    {
      "target": "B12_deficiency",
      "feature": "vitamin_B12",
      "value": 310.0,
      "criterion": "< 140.0 pg/mL",
      "direction": "unknown",
      "strength": "insufficient to exclude functional deficiency",
      "source_url": "https://cr.minzdrav.gov.ru/preview-cr/536_3"
    },
    {
      "target": "folate_deficiency",
      "feature": "folate",
      "value": 8.9,
      "criterion": "< 4.0 strong; 4.0–8.0 borderline",
      "direction": "against",
      "strength": "supporting negative evidence",
      "source_url": "https://cr.minzdrav.gov.ru/preview-cr/540_3"
    }
  ],
  "conflicts": [],
  "recommended_next_tests": [],
  "model": {
    "bundle_name": "meditron_frozen_inference_bundle",
    "bundle_version": "1.0"
  },
  "disclaimer": "Предварительная оценка по доступным данным. Результат является системой поддержки принятия решений, не является самостоятельным клиническим диагнозом и требует интерпретации врачом. Отсутствующие лабораторные показатели могут ограничивать проверку альтернативных диагностических гипотез."
}
```

### 6.4. Значение блоков ответа

| Блок | Как использовать |
| --- | --- |
| `prediction` | Итоговая скрининговая категория, флаг анемии и предполагаемая причина |
| `confidence` | Уверенность в выбранном результате; не уровень риска заболевания |
| `deficiencies` | Объект с шестью ветками: вероятности, бинарные решения, рабочие пороги, экспертная оценка |
| `data_quality` | Полнота входа, использованные/отсутствующие признаки и предупреждения |
| `evidence` | Структурированные признаки экспертного слоя и источники критериев |
| `conflicts` | Расхождения ML и правил; показывать отдельно, не скрывать за общим итогом |
| `recommended_next_tests` | Рекомендованные уточняющие исследования с целью и причиной |
| `model` | Имя и версия bundle для воспроизводимости |
| `disclaimer` | Ограничения скрининга; отображать пользователю |

Ветки `deficiencies`:

| Ключ | Подпись интерфейса |
| --- | --- |
| `iron_deficiency` | Дефицит железа |
| `B12_deficiency` | Дефицит витамина B12 |
| `folate_deficiency` | Дефицит фолатов |
| `B6_deficiency` | Дефицит витамина B6 |
| `copper_deficiency` | Дефицит меди |
| `inflammation_anemia` | Анемия воспаления |

`prediction` ветки рассчитывается по неокруглённой вероятности и порогу из frozen
bundle. Для UI использовать готовый boolean; вероятность API округлена до четырёх
знаков и возле порога может давать иной результат при повторном сравнении.
Экспертный слой добавляет `rule_score`, `rule_state`, evidence и конфликты;
он не заменяет модельное бинарное решение в данном API.

`rule_state`: `supports` — поддерживает гипотезу; `against` — против;
`unknown` — недостаточно определённости. `rule_score` не является второй
модельной вероятностью и не обозначает лабораторную норму.

### 6.5. Уверенность и итоговые классы

`confidence.level` берётся из `certainty`, а не напрямую из риска дефицита:

| certainty до округления | level |
| --- | --- |
| ≥ 0.85 | `high` |
| ≥ 0.65 и < 0.85 | `moderate` |
| < 0.65 | `low` |

У ветки уверенность равна `p` для положительного решения и `1−p` для отрицательного.
Вложенная `confidence` ветки сейчас содержит `selected_state` (`positive/negative`),
`certainty`, `level`, хотя Pydantic типизирует этот блок как свободный словарь.
Общая уверенность: минимум уверенности среди положительных веток
(`basis="weakest_positive_branch"`); если все отрицательны — `1−max(p)`
(`basis="all_binary_branches_negative"`). `limiting_target` обозначает ограничивающую ветку.
Это вычисленная мера уверенности, не клиническая гарантия и не оценка полноты данных.

Текущие значения `prediction.anemia_class` и соответствующей `deficiency_cause`:

| anemia_class | deficiency_cause |
| --- | --- |
| `iron_deficiency_anemia` | `iron_deficiency` |
| `latent_deficiency` | `iron_deficiency` |
| `B12_deficiency_anemia` | `B12_deficiency` |
| `B12_deficiency_no_anemia` | `B12_deficiency` |
| `folate_deficiency_anemia` | `folate_deficiency` |
| `folate_deficiency_no_anemia` | `folate_deficiency` |
| `B6_deficiency` | `B6_deficiency` |
| `copper_deficiency` | `copper_deficiency` |
| `inflammation_anemia` | `inflammation` |
| `mixed_deficiency` | `iron_B12`, `iron_folate` или `B12_folate` |
| `anemia_other` | `undetermined` |
| `no_anemia_no_deficiency` | `none` |

Эти поля в Pydantic объявлены строками, а не enum. Frontend должен иметь fallback
для незнакомого значения. Все ветки нужно показывать отдельно: итоговая категория
не перечисляет автоматически все положительные решения.

## 7. Импорт пациента

`POST /api/v1/me/imports/lab-file`, роль `patient`.
В `FormData` добавить поле `file`. Не устанавливать `Content-Type` вручную:
браузер должен добавить multipart boundary.

Поддерживаются `.csv`, `.xlsx`, `.pdf` с текстовым слоем. Изображения, DICOM,
MIC и OCR сканов этим маршрутом не поддерживаются. Расширение определяется по
имени файла. Максимальный размер — **5 × 1024 × 1024 байт**; ровно лимит допустим.

Загрузка только распознаёт данные и возвращает preview, **ML не запускает**.
Ответ импорта имеет свободный словарь `features`, поэтому после preview ещё
необходимо проверить форму перед отправкой типизированного скрининга.

Пример длинного CSV:

```csv
Показатель,Значение,Ед.,Референс
Пол,F,,
Возраст,35,,
Гемоглобин,108,г/л,120-150
Ферритин,7.2,нг/мл,15-150
```

Пример широкого CSV:

```csv
age_years,sex,hemoglobin,ferritin,MCV,TIBC,TSAT
35,F,108,7.2,74,82,9.5
```

Парсер пробует UTF-8 BOM, UTF-8, Windows-1251, Latin-1 и разделители запятая,
точка с запятой, TAB. XLSX читается через openpyxl. В широком пациентском файле
используется только первая строка; если строк несколько, добавляется предупреждение.
Для длинного формата распознаются колонки показателя, значения, единицы и референса;
названия могут иметь поддерживаемые русские/английские алиасы.

Пример формы ответа (сокращённый набор анализов):

```json
{
  "filename": "patient_example.csv",
  "format": "csv",
  "features": {
    "age_years": 35,
    "sex": "F",
    "hemoglobin": 108,
    "ferritin": 7.2
  },
  "metadata": {
    "hemoglobin": {
      "unit": "г/л",
      "reference_low": 120,
      "reference_high": 150,
      "reference_text": "120-150"
    },
    "ferritin": {
      "unit": "нг/мл",
      "reference_low": 15,
      "reference_high": 150,
      "reference_text": "15-150"
    }
  },
  "recognized_count": 4,
  "unrecognized": [],
  "warnings": []
}
```

`recognized_count` — количество распознанных признаков, включая пол/возраст,
а не только анализов. `unrecognized` содержит `{name, value}` для неизвестных
элементов. `warnings` нужно показывать пользователю. Отсутствие пола или гемоглобина
добавляет предупреждение, но само по себе не превращает успешный preview в ошибку.

При подтверждении формы перенести `preview.features` в `features`,
**`preview.metadata` в `lab_metadata`**, а `preview.filename` в `source_filename`
запроса `/api/v1/me/screenings`. Имена `metadata` и `lab_metadata` относятся к разным
схемам и не должны смешиваться.

## 8. История пациента

### 8.1. Список

`GET /api/v1/me/screenings`, роль `patient`:

```json
{"items":[{"screening_id":"screening-example","created_at":"2026-10-05T09:00:00","prediction":{"anemia":true,"anemia_class":"iron_deficiency_anemia","deficiency_cause":"iron_deficiency"},"coverage":0.10810810810810811,"source_type":"file","bundle_version":"1.0"}],"total":1}
```

Пустая история — `{"items":[],"total":0}`. Элемент списка — сводка;
`deficiencies`, evidence и лабораторные значения в нём отсутствуют.

### 8.2. Просмотр и удаление

- `GET /api/v1/me/screenings/{screening_id}` возвращает сохранённый `ScreeningResponse`.
  ML повторно не запускается. Несуществующий/недоступный ID — 404.
- `DELETE /api/v1/me/screenings/{screening_id}` удаляет собственный скрининг
  и связанные лабораторные значения; возвращает HTTP 200, не 204:

```json
{"message":"Screening successfully deleted.","screening_id":"screening-example"}
```

Для этих маршрутов роль врача недопустима — 403. Отсутствующий профиль пациента — 404.

## 9. Работа врача

### 9.1. Предпросмотр файла

`POST /api/v1/doctor/imports/lab-file`, роль `doctor`, multipart `file`.
Поддерживаются только CSV/XLSX, одна строка — один пациент, лимит
**10 × 1024 × 1024 байт**. PDF в bulk preview не поддерживается.

```csv
patient_code,age_years,sex,hemoglobin,ferritin,MCV
P001,35,F,108,7.2,74
P002,46,M,144,72,89
```

Алиасы колонки кода включают `patient_code`, `patient_id`, `external_code`,
`код пациента`. Код не является признаком модели.

```json
{"filename":"doctor_batch_example.csv","format":"csv","total_rows":2,"recognized_patients":2,"patients":[{"row_number":2,"patient_code":"P001","features":{"age_years":35,"sex":"F","hemoglobin":108,"ferritin":7.2,"MCV":74},"missing_required":[],"warnings":[]},{"row_number":3,"patient_code":"P002","features":{"age_years":46,"sex":"M","hemoglobin":144,"ferritin":72,"MCV":89},"missing_required":[],"warnings":[]}],"warnings":[]}
```

`row_number` начинается с 2 (первая строка — заголовок).
`recognized_patients` считает строки, где распознан хотя бы один признак,
а не строки, полностью готовые к скринингу. `missing_required` — список отсутствующих
`sex/hemoglobin`. Нет кода пациента — `patient_code=null` и предупреждение.
Неизвестные колонки врачебный парсер пропускает. Preview не создаёт скрининги
и не возвращает лабораторные метаданные по каждой строке.

### 9.2. Подтверждение и пакетный скрининг

`POST /api/v1/doctor/screenings/bulk`, JSON, роль `doctor`.
Отправлять исправленные и подтверждённые данные, а не повторно файл:

```json
{"source_filename":"doctor_batch_example.csv","patients":[{"patient_code":"P001","features":{"age_years":35,"sex":"F","hemoglobin":108,"ferritin":7.2},"lab_metadata":{"ferritin":{"unit":"нг/мл","reference_low":15,"reference_high":150}}},{"patient_code":"P002","features":{"age_years":46,"sex":"M","hemoglobin":144},"lab_metadata":{}}]}
```

`patients`: от 1 до **200** элементов. `patient_code`: 1–100 символов;
`source_filename`: необязательная строка до 255; `lab_metadata`: по умолчанию `{}`.
Не использовать пробельные коды; код сервис обрезает по краям.
Одинаковый код у разных врачей соответствует разным внутренним профилям.
Учётная запись пациента для добавленного врачом профиля не требуется.

Пример частичного успеха, HTTP 200:

```json
{"total":2,"succeeded":1,"failed":1,"results":[{"patient_code":"P001","status":"success","screening_id":"screening-example","prediction":{"anemia":true,"anemia_class":"iron_deficiency_anemia","deficiency_cause":"iron_deficiency"},"coverage":0.10810810810810811,"error":null},{"patient_code":"P002","status":"error","screening_id":null,"prediction":null,"coverage":null,"error":"Screening could not be completed"}]}
```

Ответ bulk — сводка, а не список полных `ScreeningResponse`.
Результаты идут в порядке входных пациентов. `total = succeeded + failed`.
Runtime-ошибка одного пациента не останавливает остальные; проверять `status`
каждого элемента даже при HTTP 200. Успешные скрининги сохраняются независимо.
Профиль и связь врача могут быть созданы до ошибки ML.

Если хотя бы один элемент нарушает Pydantic-схему (например, нет гемоглобина),
весь запрос получает 422 до начала цикла; это не построчная runtime-ошибка.
Preview может содержать больше 200 строк: его парсер не ограничивает число строк,
но каждый подтверждённый запрос bulk обязан соблюдать лимит.

### 9.3. Пациенты, история и результат

`GET /api/v1/doctor/patients`:

```json
{"items":[{"patient_code":"P001","screening_count":2,"last_screening_at":"2026-10-05T09:00:00"}],"total":1}
```

Пустой список: `items=[]`, `total=0`. `last_screening_at` может быть `null`.

- `GET /api/v1/doctor/patients/{patient_code}/screenings` → `ScreeningHistoryResponse`.
- `GET /api/v1/doctor/patients/{patient_code}/screenings/{screening_id}` → `ScreeningResponse`.
- `GET /api/v1/doctor/patients/{patient_code}/trends` → `TrendsResponse`.

Врач получает доступ только к связанному с ним профилю. Нет доступного пациента —
404 `Patient not found`; нет доступного скрининга — 404 `Screening not found`.
Вставлять код в URL через `encodeURIComponent`; для демо удобны простые коды `P001`.
Маршрута удаления врачебного скрининга в проверенном коде нет.

## 10. Динамика и референсы

### 10.1. Данные графиков

`GET /api/v1/me/trends` для пациента и врачебный `/patients/{patient_code}/trends`
работают с сохранёнными `LabValue`; inference не запускается.

```json
{"groups":[{"key":"iron","label":"Обмен железа","series":[{"feature":"ferritin","label":"Ферритин","unit":"нг/мл","reference_low":15,"reference_high":150,"points":[{"screening_id":"screening-example","date":"2026-10-05T09:00:00","value":7.2,"reference_low":15,"reference_high":150,"reference_source":"lab_file"}]}]}]}
```

Точки идут по времени создания скрининга по возрастанию, а не по дате взятия анализа:
отдельное поле даты исследования в запросе сейчас отсутствует.
Пустые группы и серии не включаются, отсутствие данных → `{"groups":[]}`.
Пол и возраст в `LabValue`/графики не сохраняются. Графиков истории вероятностей
дефицитов этот ответ не содержит.

Группы: `cbc`, `iron`, `vitamins`, `copper`, `inflammation`, `renal_thyroid`, `hemolysis`.
Если ненулевые единицы или границы у точек различаются, соответствующее поле серии
становится `null`; сами границы сохраняются в точках. Агрегация игнорирует `null`,
поэтому одинаковая граница части точек может быть показана на уровне серии,
даже если у остальных точек её нет.

Для постоянных линий использовать `series.reference_low/reference_high`,
когда они заданы. Для меняющихся интервалов учитывать границы каждой точки.
Не преобразовывать отсутствующую границу в 0. Если единицы серии неизвестны или
различались, сравнение требует отдельной проверки; автоматической конвертации нет.

### 10.2. Сохранение метаданных и источник нормы

`ImportedLabMetadata`:

```json
{"unit":"нг/мл","reference_low":15,"reference_high":150,"reference_text":"15–150"}
```

Все четыре поля необязательны и допускают `null`. Имена `reference_min`,
`reference_max` и поле лабораторного `status` в этой схеме отсутствуют.
Проверки `reference_low <= reference_high` в текущей схеме нет:
на этапе preview нужно проверять корректность распознанного диапазона.

При сохранении:

1. Непустая единица из запроса имеет приоритет; иначе берётся единица backend-каталога.
2. Если передана хотя бы одна числовая граница, используются только переданные
   границы. Каталог не дополняет отсутствующую вторую границу.
3. Если есть непустой `reference_text`, но нет распознанных числовых границ,
   обе границы остаются `null`; каталог не подменяет нераспознанный интервал.
4. Если лабораторного референса нет, берутся доступные границы каталога.
5. Если нет ни референса, ни каталожных границ, значения остаются `null`.

Источник в `TrendPoint.reference_source`: `lab_file`, `manual`, `internal_catalog`
либо `null`; тип поля строковый, поэтому frontend должен иметь fallback.
Признак источника лабораторного референса зависит от `source_type` сохранения,
а не от проверки подлинности файла. Поле `reference_text` принимается на вход,
но не возвращается в трендах и не хранится как отдельное поле `LabValue`.

`ScreeningResponse` не содержит `features`, `lab_metadata` или таблицу
`lab_interpretation`. Для текущего экрана анализов frontend хранит введённые/импортированные
данные, для истории графиков использует trends, для PDF — серверные `LabValue`.
Если интерфейсу нужен статус «ниже/в пределах/выше референса», это отдельная
визуальная классификация по доступным границам, а не возвращённый модельный риск.

## 11. PDF

Маршруты:

- Пациент: `GET /api/v1/me/screenings/{screening_id}/report.pdf`.
- Врач: `GET /api/v1/doctor/patients/{patient_code}/screenings/{screening_id}/report.pdf`.

Оба требуют Bearer-токен и доступ к сохранённому скринингу. Сервер строит отчёт
из сохранённого результата и `LabValue`, модель повторно не запускается.
Несохранённый результат публичного `/api/v1/screenings` не доступен через эти маршруты.

Успех: бинарное тело, `Content-Type: application/pdf`,
`Content-Disposition: attachment; filename="..."`.
Имя пациента: `meditron_screening_{screening_id}.pdf`;
имя врача: `meditron_{patient_code}_{screening_id}.pdf`.

Frontend должен скачать через `fetch` с Authorization и читать `response.blob()`.
При ошибке сначала проверять `response.ok`: ошибка приходит как HTTP-ответ,
а не как PDF. Открытие ссылки в новой вкладке не добавляет Bearer-токен автоматически.
В CORS не настроен `expose_headers` для `Content-Disposition`, поэтому при запросе
на другой origin frontend может не прочитать имя из этого заголовка; допустимо
создать локальное имя по известному `screening_id`.

Таблица PDF берёт `value`, `unit`, `reference_low/reference_high` из БД;
при отсутствии единицы/референса показывает прочерк. Каталожный fallback
срабатывает при сохранении, а не через frontend. Старые записи могут требовать
`scripts/backfill_lab_metadata.py`, если они были сохранены до этого механизма.
Ошибка формирования отчёта — 500 `Could not generate PDF report`.

## 12. Ошибки и неполные данные

### 12.1. Формат ошибок

Обычная `HTTPException`:

```json
{"detail":"Authentication required"}
```

Ошибка валидации FastAPI/Pydantic, HTTP 422 (представительный пример):

```json
{"detail":[{"type":"missing","loc":["body","features","hemoglobin"],"msg":"Field required","input":{"sex":"F"}}]}
```

Конкретный состав `type/msg/input/ctx` зависит от ошибки и версии библиотек.
`loc` указывает путь до поля; frontend обрабатывает и строковый `detail`, и массив.
Не предполагается единый envelope `error.code`, `request_id` или верхнеуровневый
`status` для всех ответов.

| HTTP | Когда встречается | Реакция интерфейса |
| --- | --- | --- |
| 400 | Ошибка разбора файла; неверный токен подтверждения/сброса; ValueError публичного скрининга | Показать detail и дать исправить ввод |
| 401 | Нет, истёк или отозван токен; неправильные данные входа | Для защищённого запроса очистить локальную сессию и предложить вход |
| 403 | Неверная роль либо почта не подтверждена при входе | Сообщить причину и направить в подходящий сценарий |
| 404 | Нет доступного профиля/пациента/скрининга | Показать отсутствие записи, обновить список |
| 409 | Конфликт регистрации | Показать сообщение, предложить вход или восстановление |
| 413 | Файл превышает 5 MiB пациента или 10 MiB врача | Предложить файл меньшего размера |
| 415 | Неподдерживаемое расширение файла | Показать разрешённые форматы |
| 422 | Запрос не соответствует Pydantic-схеме | Подсветить поля по loc; bulk не запущен |
| 500 | Ошибка модели/артефактов, БД, pipeline или PDF | Показать сбой сервиса; не обещать успешное сохранение |

Пустой загруженный файл — 400 `Uploaded file is empty`.
Отсутствующий multipart-параметр `file` — 422.
Авторизация проверяется зависимостью, поэтому при отсутствии сессии можно получить
401 раньше проверки содержимого файла или роли.

Публичный скрининг явно переводит ValueError в 400 и ошибки pipeline в 500.
В сохранённом пациентском маршруте нет такой же обёртки: необработанные исключения
могут дать стандартный HTTP 500 без JSON `detail`. Это текущая особенность реализации;
frontend обязан иметь fallback для не-JSON ответа.

### 12.2. Недостаточно данных

В текущем API **нет** ответа `status="insufficient_data"` и отдельного маршрута
для этого состояния.

- Нет `sex` или `hemoglobin` / передан `null` / неверный тип → обычно 422 на уровне схемы.
- Необязательные поля отсутствуют → скрининг может выполниться успешно.
- `coverage = количество непустых признаков из контракта / 37`, включая пол и возраст.
- В `run_screening` задан ориентир 0.70, но `allow_low_coverage=True`:
  ниже ориентира добавляется warning, запрос автоматически не отклоняется.
- Только пол и гемоглобин дают полноту `2/37 ≈ 0.0541`, а не достаточность
  клинической проверки всех гипотез.

Экран «Недостаточно данных» может быть решением UX по отсутствующим обязательным
полям, `data_quality.missing_features/warnings` и согласованным ограничениям.
Не приписывать backend отдельный статус и не принимать 0.70 за медицинский
порог достоверности. Неопределённая/неполная оценка не должна отображаться как норма.

## 13. Интеграция frontend

### 13.1. Настройки

Для обращения к настоящему backend:

```dotenv
VITE_API_URL=http://localhost:8000
VITE_USE_MOCKS=false
VITE_REQUEST_FORMAT=features
```

При отсутствии точного значения `VITE_USE_MOCKS=false` текущая конфигурация включает
demo-режим. `VITE_*` в сборке Vite задаются при build; Docker Compose уже передаёт
эти значения как build args. Изменение требует новой сборки frontend.

CORS backend разрешает `localhost` и `127.0.0.1` с портами 3000 и 5173;
`allow_credentials=True`, все методы/заголовки разрешены. Для нового домена
нужно изменить список origins. Cookies авторизации текущий контракт не использует.

Токен клиент сейчас хранит в памяти и `sessionStorage` под ключом
`meditron_access_token`. Сетевой timeout frontend — 30 секунд; это клиентская
настройка, не SLA сервера. Bulk работает синхронно и может выполняться дольше.

### 13.2. Запрос скрининга и загрузка файла

```js
const base = "http://localhost:8000";
const token = sessionStorage.getItem("meditron_access_token");

async function readJson(response) {
  const text = await response.text();
  let data;
  try { data = JSON.parse(text); } catch { data = null; }
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail
      : Array.isArray(detail) ? detail.map(x => `${x.loc.join(".")}: ${x.msg}`).join("; ")
      : `Ошибка API: HTTP ${response.status}`;
    throw new Error(message);
  }
  if (!data) throw new Error("API вернул ответ без JSON");
  return data;
}

const form = new FormData();
form.append("file", selectedFile); // selectedFile — File из input
const preview = await readJson(await fetch(`${base}/api/v1/me/imports/lab-file`, {
  method: "POST", headers: { Authorization: `Bearer ${token}` }, body: form,
}));
// Показать preview, исправить/дополнить его, дождаться подтверждения формы.
const result = await readJson(await fetch(`${base}/api/v1/me/screenings`, {
  method: "POST",
  headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  body: JSON.stringify({
    features: confirmedFeatures,
    lab_metadata: preview.metadata,
    source_filename: preview.filename,
  }),
}));
```

`selectedFile` и `confirmedFeatures` здесь поступают из интерфейса.
Не запускать второй запрос автоматически сразу после импорта без проверки формы.

### 13.3. Вывод результата и отчёт

- Для карточки ветки читать `result.deficiencies[target]`, а не `results[]`.
- Вероятность отображать как `probability × 100%`, полноту — `coverage × 100%`.
- Отдельно отображать `confidence.level`, `prediction`, `rule_state` и конфликты.
- Не вводить собственные границы 0.30/0.70 как якобы серверные `risk_level`:
  это поле в API отсутствует; рабочий `threshold` индивидуален для ветки.
- `screening_id` использовать для истории и PDF; `created_at` брать из истории,
  поскольку полный `ScreeningResponse` не содержит времени создания.
- Сохранить метаданные импорта для подтверждения и таблицы текущих анализов.
- При выводе строк сервера в DOM использовать `textContent` либо экранирование.

```js
const response = await fetch(
  `${base}/api/v1/me/screenings/${encodeURIComponent(result.screening_id)}/report.pdf`,
  { headers: { Authorization: `Bearer ${token}` } },
);
if (!response.ok) await readJson(response);
const url = URL.createObjectURL(await response.blob());
const link = document.createElement("a");
link.href = url;
link.download = `meditron_screening_${result.screening_id}.pdf`;
link.click();
setTimeout(() => URL.revokeObjectURL(url), 1000);
```

## 14. Ограничения текущего контракта

Этот раздел фиксирует выявленные границы реализации, чтобы документация не
обещала того, что ещё не возвращается клиенту.

1. `ScreeningResponse` не содержит `lab_interpretation`, `risk_level`, `request_id`,
   время создания, исходные анализы или лабораторный `status`.
2. `expert/explanations.py` формирует `clinical_messages`, `mandatory_review`,
   `clinical_priority`, `review_targets`, `data_limitations`, `hypothesis_completeness`,
   `incomplete_hypotheses`, `fired_rules`; `run_screening` не включает их в полный
   API-ответ. Дополнительные поля веток `assessment_status`, `assessment_complete`,
   `available_key_markers`, `missing_key_markers`, `requires_review` отбрасываются
   моделью `DeficiencyResult`. Frontend не может рассчитывать на получение этих полей.
3. Контракт имеет 37 числовых/демографических признаков; API не принимает анкету,
   текст симптомов, изображения, DICOM/MIC или `vitamin_d`. PDF здесь — способ
   извлечения лабораторных чисел, не отдельный вход изображения в модель.
4. Автоматических преобразований единиц, клинической проверки всех диапазонов,
   idempotency key, пагинации, фоновых jobs и refresh-token в маршрутах нет.
5. Повторный POST после timeout может создать второй скрининг, даже если первый
   уже завершился. Перед повтором сохранённого запроса проверить историю.
6. Право регистрации роли `doctor` задаётся самим запросом; дополнительная
   проверка профессионального статуса врача кодом маршрутов не предусмотрена.
7. Каталожные референсы — fallback текущего проекта. Это не персонализированный
   лабораторный диапазон и не диагностический порог expert system.
8. Публичный скрининг не сохраняется; отсутствие токена в нём не является ошибкой.
   Пациентская история и врачебные профили — разные сценарии доступа.

## 15. Полный справочник схем

Таблицы ниже составлены по `api/schemas/*.py` указанного коммита.
«Обязательно» обозначает отсутствие default в схеме, а не клиническую достаточность.
В обозначениях Python `float` соответствует JSON number, `str` — string,
`datetime` — строке ISO 8601, `list` — массиву, `dict` — объекту,
`None` — JSON null. `Literal` перечисляет разрешённые значения.
`UserRole = Literal['patient', 'doctor']`,
`ConfidenceLevel = Literal['high', 'moderate', 'low']`.

### RegisterRequest

Источник: `api/schemas/auth.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `email` | `EmailStr` | да | — |
| `password` | `str` | да | min_length=8; max_length=128 |
| `role` | `UserRole` | да | — |

### UserResponse

Источник: `api/schemas/auth.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `id` | `str` | да | — |
| `email` | `EmailStr` | да | — |
| `role` | `UserRole` | да | — |
| `is_email_verified` | `bool` | да | — |

### RegisterResponse

Источник: `api/schemas/auth.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `user` | `UserResponse` | да | — |
| `message` | `str` | да | — |
| `email_sent` | `bool` | нет | default=True |

### VerifyEmailRequest

Источник: `api/schemas/auth.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `token` | `str` | да | min_length=20; max_length=512 |

### ResendVerificationRequest

Источник: `api/schemas/auth.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `email` | `EmailStr` | да | — |

### MessageResponse

Источник: `api/schemas/auth.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `message` | `str` | да | — |

### LoginRequest

Источник: `api/schemas/auth.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `email` | `EmailStr` | да | — |
| `password` | `str` | да | min_length=1; max_length=128 |

### LoginResponse

Источник: `api/schemas/auth.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `access_token` | `str` | да | — |
| `token_type` | `Literal['bearer']` | нет | default='bearer' |
| `expires_at` | `datetime` | да | — |
| `user` | `UserResponse` | да | — |

### ForgotPasswordRequest

Источник: `api/schemas/auth.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `email` | `EmailStr` | да | — |

### ResetPasswordRequest

Источник: `api/schemas/auth.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `token` | `str` | да | min_length=20; max_length=512 |
| `new_password` | `str` | да | min_length=8; max_length=128 |

### Confidence

Источник: `api/schemas/common.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `basis` | `str \| None` | нет | default=None |
| `limiting_target` | `str \| None` | нет | default=None |
| `certainty` | `float` | да | ge=0.0; le=1.0 |
| `level` | `ConfidenceLevel` | да | — |

### DataQuality

Источник: `api/schemas/common.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `coverage` | `float` | да | ge=0.0; le=1.0 |
| `used_features` | `list[str]` | нет | default_factory=list |
| `missing_features` | `list[str]` | нет | default_factory=list |
| `warnings` | `list[str]` | нет | default_factory=list |

### DoctorPatientPreview

Источник: `api/schemas/doctor_imports.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `row_number` | `int` | да | — |
| `patient_code` | `str \| None` | нет | default=None |
| `features` | `dict[str, float \| str]` | нет | default_factory=dict |
| `missing_required` | `list[str]` | нет | default_factory=list |
| `warnings` | `list[str]` | нет | default_factory=list |

### DoctorBulkImportResponse

Источник: `api/schemas/doctor_imports.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `filename` | `str` | да | — |
| `format` | `str` | да | — |
| `total_rows` | `int` | да | — |
| `recognized_patients` | `int` | да | — |
| `patients` | `list[DoctorPatientPreview]` | нет | default_factory=list |
| `warnings` | `list[str]` | нет | default_factory=list |

### DoctorPatientListItem

Источник: `api/schemas/doctor_patients.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `patient_code` | `str` | да | — |
| `screening_count` | `int` | да | ge=0 |
| `last_screening_at` | `datetime \| None` | нет | default=None |

### DoctorPatientListResponse

Источник: `api/schemas/doctor_patients.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `items` | `list[DoctorPatientListItem]` | нет | default_factory=list |
| `total` | `int` | да | ge=0 |

### DoctorBulkScreeningPatient

Источник: `api/schemas/doctor_screenings.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `patient_code` | `str` | да | min_length=1; max_length=100 |
| `features` | `PatientFeatures` | да | — |
| `lab_metadata` | `dict[str, ImportedLabMetadata]` | нет | default_factory=dict |

### DoctorBulkScreeningRequest

Источник: `api/schemas/doctor_screenings.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `source_filename` | `str \| None` | нет | default=None; max_length=255 |
| `patients` | `list[DoctorBulkScreeningPatient]` | да | min_length=1; max_length=200 |

### DoctorBulkScreeningResultItem

Источник: `api/schemas/doctor_screenings.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `patient_code` | `str` | да | — |
| `status` | `Literal['success', 'error']` | да | — |
| `screening_id` | `str \| None` | нет | default=None |
| `prediction` | `PredictionSummary \| None` | нет | default=None |
| `coverage` | `float \| None` | нет | default=None; ge=0.0; le=1.0 |
| `error` | `str \| None` | нет | default=None |

### DoctorBulkScreeningResponse

Источник: `api/schemas/doctor_screenings.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `total` | `int` | да | — |
| `succeeded` | `int` | да | — |
| `failed` | `int` | да | — |
| `results` | `list[DoctorBulkScreeningResultItem]` | нет | default_factory=list |

### MeScreeningRequest

Источник: `api/schemas/history.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `features` | `PatientFeatures` | да | — |
| `lab_metadata` | `dict[str, ImportedLabMetadata]` | нет | default_factory=dict |
| `source_filename` | `str \| None` | нет | default=None; max_length=255 |

### ScreeningHistoryItem

Источник: `api/schemas/history.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `screening_id` | `str` | да | — |
| `created_at` | `datetime` | да | — |
| `prediction` | `PredictionSummary` | да | — |
| `coverage` | `float \| None` | нет | default=None; ge=0.0; le=1.0 |
| `source_type` | `str` | да | — |
| `bundle_version` | `str \| None` | нет | default=None |

### ScreeningHistoryResponse

Источник: `api/schemas/history.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `items` | `list[ScreeningHistoryItem]` | да | — |
| `total` | `int` | да | — |

### DeleteScreeningResponse

Источник: `api/schemas/history.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `message` | `str` | да | — |
| `screening_id` | `str` | да | — |

### ImportedLabMetadata

Источник: `api/schemas/imports.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `unit` | `str \| None` | нет | default=None |
| `reference_low` | `float \| None` | нет | default=None |
| `reference_high` | `float \| None` | нет | default=None |
| `reference_text` | `str \| None` | нет | default=None |

### UnrecognizedItem

Источник: `api/schemas/imports.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `name` | `str` | да | — |
| `value` | `Any \| None` | нет | default=None |

### FileImportResponse

Источник: `api/schemas/imports.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `filename` | `str` | да | — |
| `format` | `str` | да | — |
| `features` | `dict[str, float \| str]` | нет | default_factory=dict |
| `metadata` | `dict[str, ImportedLabMetadata]` | нет | default_factory=dict |
| `recognized_count` | `int` | да | — |
| `unrecognized` | `list[UnrecognizedItem]` | нет | default_factory=list |
| `warnings` | `list[str]` | нет | default_factory=list |

### ScreeningRequest

Источник: `api/schemas/request.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `patient_id` | `str \| None` | нет | default=None |
| `features` | `PatientFeatures` | да | — |

### PredictionSummary

Источник: `api/schemas/response.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `anemia` | `bool` | да | — |
| `anemia_class` | `str` | да | — |
| `deficiency_cause` | `str` | да | — |

### DeficiencyResult

Источник: `api/schemas/response.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `probability` | `float` | да | ge=0.0; le=1.0 |
| `prediction` | `bool` | да | — |
| `threshold` | `float` | да | ge=0.0; le=1.0 |
| `rule_score` | `float \| None` | нет | default=None; ge=0.0; le=1.0 |
| `rule_state` | `Literal['supports', 'against', 'unknown'] \| None` | нет | default=None |
| `confidence` | `dict[str, Any] \| None` | нет | default=None |

### EvidenceItem

Источник: `api/schemas/response.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `target` | `str` | да | — |
| `feature` | `str` | да | — |
| `value` | `float` | да | — |
| `criterion` | `str` | да | — |
| `direction` | `Literal['supports', 'against', 'unknown']` | да | — |
| `strength` | `str` | да | — |
| `source_url` | `str \| None` | нет | default=None |

### ConflictItem

Источник: `api/schemas/response.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `target` | `str` | да | — |
| `type` | `str` | да | — |
| `severity` | `str` | да | — |
| `ensemble_probability` | `float` | да | ge=0.0; le=1.0 |
| `rule_score` | `float` | да | ge=0.0; le=1.0 |
| `rule_state` | `str` | да | — |
| `message` | `str` | да | — |

### RecommendedTest

Источник: `api/schemas/response.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `test` | `str` | да | — |
| `target` | `str` | да | — |
| `reason` | `str` | да | — |

### ModelInfo

Источник: `api/schemas/response.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `bundle_name` | `str \| None` | нет | default=None |
| `bundle_version` | `str \| None` | нет | default=None |

### ScreeningResponse

Источник: `api/schemas/response.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `screening_id` | `str` | да | — |
| `patient_id` | `str \| None` | нет | default=None |
| `prediction` | `PredictionSummary` | да | — |
| `confidence` | `Confidence` | да | — |
| `deficiencies` | `dict[str, DeficiencyResult]` | да | — |
| `data_quality` | `DataQuality` | да | — |
| `evidence` | `list[EvidenceItem]` | нет | default_factory=list |
| `conflicts` | `list[ConflictItem]` | нет | default_factory=list |
| `recommended_next_tests` | `list[RecommendedTest]` | нет | default_factory=list |
| `model` | `ModelInfo` | да | — |
| `disclaimer` | `str` | да | — |

### TrendPoint

Источник: `api/schemas/trends.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `screening_id` | `str` | да | — |
| `date` | `datetime` | да | — |
| `value` | `float` | да | — |
| `reference_low` | `float \| None` | нет | default=None |
| `reference_high` | `float \| None` | нет | default=None |
| `reference_source` | `str \| None` | нет | default=None |

### TrendSeries

Источник: `api/schemas/trends.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `feature` | `str` | да | — |
| `label` | `str` | да | — |
| `unit` | `str \| None` | нет | default=None |
| `reference_low` | `float \| None` | нет | default=None |
| `reference_high` | `float \| None` | нет | default=None |
| `points` | `list[TrendPoint]` | нет | default_factory=list |

### TrendGroup

Источник: `api/schemas/trends.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `key` | `str` | да | — |
| `label` | `str` | да | — |
| `series` | `list[TrendSeries]` | нет | default_factory=list |

### TrendsResponse

Источник: `api/schemas/trends.py`.

| Поле | Тип | Обязательно | Default / ограничения |
| --- | --- | --- | --- |
| `groups` | `list[TrendGroup]` | нет | default_factory=list |

## 16. Поддержка актуальности

Источники, по которым сверяется контракт:

- `api/main.py`, `api/routes/` — реальная регистрация маршрутов, доступ и HTTP-коды.
- `api/schemas/` — имена, типы, обязательность и ограничения JSON-полей.
- `api/services/screening_service.py` — окончательный набор полей pipeline.
- `api/services/file_parser_service.py`, `doctor_file_parser_service.py`,
  `pdf_lab_parser_service.py` — фактические форматы импорта.
- `api/services/history_service.py`, `doctor_screening_service.py`,
  `trends_service.py`, `report_service.py` — сохранение, доступ, нормы, графики, PDF.
- `api/resources/lab_catalog.py`, `lab_groups.py` — единицы, fallback и группы.
- `artifacts/inference_bundle/feature_contract.json`, `manifest.json`,
  `ml/inference/predictor.py`, `expert/knowledge_base.py` — признаки и семантика результата.
- `frontend/src/config.js`, `frontend/src/api/` — используемые frontend пути и payload.
- `tests/test_api.py`, `test_auth.py`, `test_history.py`, `test_file_import.py`,
  `test_lab_metadata_catalog.py` — существующие проверки поведения.
- `data/demo/` — воспроизводимые демонстрационные входы и ожидаемые результаты.

При изменении backend обновлять схему, обработчик, этот контракт и frontend
согласованно. После изменения сверять `/openapi.json` и проверять сценарии:
регистрация/вход; ручной скрининг; preview → подтверждение; история/удаление;
bulk с частичной runtime-ошибкой; графики с референсами; PDF; 401/403/422.

В ответах сохранять медицинский дисклеймер. Результат сервиса — предварительная
скрининговая оценка и поддержка принятия решений, а не установленный диагноз.
