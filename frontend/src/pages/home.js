import { main, faq } from "../components/index.js";

const icon = (file, alt = "") =>
  `<img class="home-icon-img" src="assets/icons/${file}" alt="${alt}" aria-hidden="true">`;

export function home() {
  main.innerHTML = `
    <div class="home-page">
      <section class="home-hero">
        <div class="home-hero__inner">
          <div class="home-hero__copy">
            <h1 class="home-logo-word">Med<span>it</span>ron</h1>
            <h2>ИИ - скрининг латентных дефицитных состояний</h2>
            <p>Автоматическая интерпретация лабораторных данных и определение 12 итоговых классов анемии и связанных дефицитных состояний</p>
            <div class="home-hero__actions">
              <a class="btn" href="#/screening">Начать скрининг</a>
              <a class="btn secondary" href="#/how">Как это работает?</a>
            </div>
          </div>
          <img class="home-hero__robot" src="assets/robot-hero.webp" alt="Робот Meditron с цифровым планшетом">
        </div>
      </section>

      <section class="home-benefits home-shell-card" aria-label="Преимущества сервиса">
        <article>
          <div class="home-icon">${icon("flask-solid.svg")}</div>
          <div><h3>Лабораторные данные</h3><p>Вводите доступные показатели</p></div>
        </article>
        <article>
          <div class="home-icon home-icon--soft">${icon("robot-solid.svg")}</div>
          <div><h3>ИИ-анализ</h3><p>Модель оценивает риск дефицита</p></div>
        </article>
        <article>
          <div class="home-icon home-icon--soft">${icon("list-alt.svg")}</div>
          <div><h3>Понятный результат</h3><p>Получите персональные рекомендации</p></div>
        </article>
      </section>

      <section class="home-section">
        <h2 class="home-section__title">Почему это важно?</h2>
        <div class="home-why-grid">
          <article class="home-mini-card">
            <div class="home-icon">${icon("microscope-solid.svg")}</div>
            <div><h3>Раннее выявление</h3><p>Латентные дефициты часто не имеют явных симптомов</p></div>
          </article>
          <article class="home-mini-card">
            <div class="home-icon">${icon("chalkboard-teacher-solid.svg")}</div>
            <div><h3>Научный подход</h3><p>Основано на анализе лабораторных работ</p></div>
          </article>
          <article class="home-mini-card">
            <div class="home-icon">${icon("chart-pie-solid.svg")}</div>
            <div><h3>Профилактика</h3><p>Позволяет снизить риски для здоровья</p></div>
          </article>
        </div>
      </section>

      <section class="home-section home-how" id="how-section">
        <h2 class="home-section__title">Как это работает?</h2>
        <div class="home-how__card home-shell-card">
          <article class="home-how__step">
            <div class="home-icon home-icon--soft">${icon("flask-solid.svg")}</div>
            <h3>Введите данные</h3><p>Лабораторных анализов</p>
          </article>
          <span class="home-arrow" aria-hidden="true">→</span>
          <article class="home-how__step">
            <div class="home-icon home-icon--soft">${icon("robot-solid.svg")}</div>
            <h3>ИИ анализирует</h3><p>показатели</p>
          </article>
          <span class="home-arrow" aria-hidden="true">→</span>
          <article class="home-how__step">
            <div class="home-icon home-icon--soft">${icon("chart-pie-solid.svg")}</div>
            <h3>Получите оценку</h3><p>рисков</p>
          </article>
          <span class="home-arrow" aria-hidden="true">→</span>
          <article class="home-how__step">
            <div class="home-icon home-icon--soft">${icon("file-download-solid.svg")}</div>
            <h3>Скачайте результат</h3><p>и рекомендации</p>
          </article>
        </div>
      </section>

      <section class="home-about home-shell-card" id="about-home">
        <div class="home-about__copy">
          <h2>О сервисе</h2>
          <h3>Современные ИИ-технологии для заботы о вашем здоровье</h3>
          <p>Наш сервис использует машинное обучение для анализа лабораторных показателей и оценки риска латентных дефицитных состояний</p>
        </div>
        <img src="assets/robot-about.webp" alt="Медицинский робот Meditron" loading="lazy">

        <div class="home-about__features">
          <article>
            <div class="home-icon home-icon--light">${icon("robot-solid.svg")}</div>
            <h3>Гибридная ML-система</h3>
            <p>Автоматическая интерпретация данных</p>
          </article>
          <article>
            <div class="home-icon home-icon--light">${icon("space-shuttle-solid.svg")}</div>
            <h3>Быстрый результат</h3>
            <p>Анализ за несколько секунд</p>
          </article>
          <article>
            <div class="home-icon home-icon--light">${icon("microscope-solid.svg")}</div>
            <h3>Научная база</h3>
            <p>Основано на актуальных медицинских исследованиях</p>
          </article>
        </div>
      </section>

      <section class="home-faq home-shell-card">
        <h2>Часто задаваемые вопросы</h2>
        <div class="faq">${faq()}</div>
      </section>
    </div>
  `;
}
