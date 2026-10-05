// ============================================================
// PATIENT FEATURE CATALOG
// ============================================================
//
// Имена code должны ТОЧНО совпадать
// с api.schemas.request.PatientFeatures.
//
// unit сейчас используется только интерфейсом.
// Backend получает числовое значение feature.
// ============================================================


export const groups = [
  {
    key: "cbc",
    name: "Общий анализ крови",
    description:
      "Основные показатели крови и эритроцитарные индексы",

    codes: [
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
    ],
  },

  {
    key: "iron",
    name: "Обмен железа",
    description:
      "Показатели запасов железа, транспорта и насыщения трансферрина",

    codes: [
      "ferritin",
      "serum_iron",
      "transferrin",
      "TIBC",
      "UIBC",
      "TSAT",
      "sTfR",
      "Ret_He",
    ],
  },

  {
    key: "vitamins",
    name: "Витамины B12, B9 и B6",
    description:
      "Лабораторные показатели витаминного статуса",

    codes: [
      "vitamin_B12",
      "active_B12",
      "MMA",
      "homocysteine",
      "folate",
      "vitamin_B6",
    ],
  },

  {
    key: "copper",
    name: "Обмен меди",
    description:
      "Медь и церулоплазмин",

    codes: [
      "copper",
      "ceruloplasmin",
    ],
  },

  {
    key: "inflammation",
    name: "Воспаление",
    description:
      "Показатели воспалительного процесса",

    codes: [
      "CRP",
      "ESR",
    ],
  },

  {
    key: "renal-thyroid",
    name: "Почки, щитовидная железа и общий профиль",
    description:
      "Дополнительные показатели, влияющие на интерпретацию анализа",

    codes: [
      "creatinine",
      "eGFR",
      "TSH",
      "albumin",
    ],
  },

  {
    key: "hemolysis",
    name: "Маркеры гемолиза",
    description:
      "Дополнительные показатели разрушения эритроцитов",

    codes: [
      "LDH",
      "indirect_bilirubin",
      "haptoglobin",
    ],
  },
];


// ============================================================
// LABS
// ============================================================


export const labs = {
  // ----------------------------------------------------------
  // CBC
  // ----------------------------------------------------------

  hemoglobin: {
    label: "Гемоглобин",
    unit: "г/л",
    required: true,
  },

  RBC: {
    label: "Эритроциты",
    unit: "10¹²/л",
  },

  hematocrit: {
    label: "Гематокрит",
    unit: "%",
  },

  MCV: {
    label: "MCV · средний объём эритроцита",
    unit: "фл",
  },

  MCH: {
    label: "MCH · среднее содержание Hb",
    unit: "пг",
  },

  MCHC: {
    label: "MCHC · средняя концентрация Hb",
    unit: "г/л",
  },

  RDW: {
    label: "RDW · ширина распределения эритроцитов",
    unit: "%",
  },

  platelets: {
    label: "Тромбоциты",
    unit: "10⁹/л",
  },

  WBC: {
    label: "Лейкоциты",
    unit: "10⁹/л",
  },

  reticulocytes: {
    label: "Ретикулоциты",
    unit: "%",
  },


  // ----------------------------------------------------------
  // IRON
  // ----------------------------------------------------------

  ferritin: {
    label: "Ферритин",
    unit: "нг/мл",
  },

  serum_iron: {
    label: "Сывороточное железо",
    unit: "мкмоль/л",
  },

  transferrin: {
    label: "Трансферрин",
    unit: "г/л",
  },

  TIBC: {
    label: "ОЖСС / TIBC",
    unit: "мкмоль/л",
  },

  UIBC: {
    label: "НЖСС / UIBC",
    unit: "мкмоль/л",
  },

  TSAT: {
    label: "Насыщение трансферрина / TSAT",
    unit: "%",
  },

  sTfR: {
    label: "Растворимый рецептор трансферрина / sTfR",
    unit: "",
  },

  Ret_He: {
    label: "Гемоглобин ретикулоцитов / Ret-He",
    unit: "пг",
  },


  // ----------------------------------------------------------
  // VITAMINS
  // ----------------------------------------------------------

  vitamin_B12: {
    label: "Витамин B12",
    unit: "пг/мл",
  },

  active_B12: {
    label: "Активный B12",
    unit: "",
  },

  MMA: {
    label: "Метилмалоновая кислота / MMA",
    unit: "",
  },

  homocysteine: {
    label: "Гомоцистеин",
    unit: "мкмоль/л",
  },

  folate: {
    label: "Фолаты",
    unit: "нг/мл",
  },

  vitamin_B6: {
    label: "Витамин B6",
    unit: "",
  },


  // ----------------------------------------------------------
  // COPPER
  // ----------------------------------------------------------

  copper: {
    label: "Медь",
    unit: "",
  },

  ceruloplasmin: {
    label: "Церулоплазмин",
    unit: "",
  },


  // ----------------------------------------------------------
  // INFLAMMATION
  // ----------------------------------------------------------

  CRP: {
    label: "C-реактивный белок / CRP",
    unit: "мг/л",
  },

  ESR: {
    label: "СОЭ / ESR",
    unit: "мм/ч",
  },


  // ----------------------------------------------------------
  // RENAL / THYROID / GENERAL
  // ----------------------------------------------------------

  creatinine: {
    label: "Креатинин",
    unit: "мкмоль/л",
  },

  eGFR: {
    label: "Расчётная СКФ / eGFR",
    unit: "мл/мин/1,73 м²",
  },

  TSH: {
    label: "ТТГ / TSH",
    unit: "мМЕ/л",
  },

  albumin: {
    label: "Альбумин",
    unit: "г/л",
  },


  // ----------------------------------------------------------
  // HEMOLYSIS
  // ----------------------------------------------------------

  LDH: {
    label: "ЛДГ / LDH",
    unit: "Ед/л",
  },

  indirect_bilirubin: {
    label: "Непрямой билирубин",
    unit: "мкмоль/л",
  },

  haptoglobin: {
    label: "Гаптоглобин",
    unit: "",
  },
};


// ============================================================
// MODEL TARGET LABELS
// ============================================================


export const conditions = {
  iron_deficiency:
    "Дефицит железа",

  B12_deficiency:
    "Дефицит витамина B12",

  folate_deficiency:
    "Дефицит фолатов",

  B6_deficiency:
    "Дефицит витамина B6",

  copper_deficiency:
    "Дефицит меди",

  inflammation_anemia:
    "Анемия воспаления",
};


// ============================================================
// HELPERS
// ============================================================


export const labCodes =
  Object.keys(
    labs,
  );


export const requiredLabCodes =
  labCodes.filter(
    (
      code,
    ) =>
      labs[
        code
      ].required,
  );