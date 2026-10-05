import { main, medicalNotice, page, back, faq } from "../components/index.js";
export function about() {
  main.innerHTML = page(
    `${back()}<div class="about"><div><div class="eyebrow">О сервисе</div><h1 style="margin-top:24px">Понять анализы.<br>Увидеть общую картину.</h1><p>Meditron — интерфейс для ИИ-скрининга латентных дефицитных состояний по числовым лабораторным показателям. При поддержке бэкендом можно добавить текстовое описание самочувствия.</p><p>Сервис отображает результат модели, значимые показатели и предупреждения о качестве данных. История и динамика помогают сравнивать обследования.</p><a class="btn" href="#/screening">Начать скрининг →</a></div><img src="assets/robot-about.webp" alt="Робот Meditron"></div>${medicalNotice()}<section class="section"><h2>Частые вопросы</h2><div class="faq" style="margin:0">${faq()}</div></section>`,
  );
}
