import { main, medicalNotice, page, back } from "../components/index.js";

export function privacy() {
  main.innerHTML = page(
    `${back()}<div class="config privacy-page"><h1>Политика конфиденциальности</h1><p class="subtitle">Документ об обработке персональных данных в текущей версии Meditron.</p><section class="form-section"><h3>Ознакомление с политикой</h3><p>Полная версия политики открывается отдельным PDF-файлом. При регистрации пользователь подтверждает ознакомление с политикой и отдельно даёт согласие на обработку результатов лабораторных анализов и сведений о состоянии здоровья.</p><div class="actions"><a class="btn" href="/privacy-policy.pdf" target="_blank" rel="noopener">Открыть политику (PDF) ↗</a></div></section><section class="form-section"><h3>Важно для демонстрационной версии</h3><p>Документ содержит демонстрационные реквизиты организации. Перед реальной публикацией их необходимо заменить на сведения фактического оператора персональных данных.</p></section>${medicalNotice()}</div>`,
  );
}
