import json
import os
import streamlit as st
from google import genai

# Настройка страницы
st.set_page_config(
    page_title="Генератор КТП и планов уроков", page_icon="📚", layout="centered"
)

# Настройка ключа API и клиента Gemini
# (API-ключ можно настроить в Secrets Streamlit или ввести прямо в коде, если нужно)
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not API_KEY:
  st.warning(
      "⚠️ API-ключ Gemini не найден в настройках. Введите его ниже, чтобы"
      " генерация работала:"
  )
  API_KEY = st.text_input("Google AI Studio API Key", type="password")

# Файл для постоянного кэширования готовых планов на сервере
CACHE_FILE = "lesson_plans_cache.json"


def load_cache():
  """Загружает базу кэша из JSON-файла."""
  if os.path.exists(CACHE_FILE):
    try:
      with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return {}
  return {}


def save_to_cache(key, plan_text):
  """Сохраняет сгенерированный план в JSON-файл."""
  cache = load_cache()
  cache[key] = plan_text
  try:
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
      json.dump(cache, f, ensure_ascii=False, indent=4)
  except Exception as e:
    st.error(f"Ошибка сохранения в кэш: {e}")


# Интерфейс приложения
st.title("📚 Генератор КТП и поурочных планов")
st.markdown(
    "Создавайте учебные планы по стандартам образования. Уже готовые планы"
    " загружаются **мгновенно и без расхода лимитов**!"
)

# Форма ввода данных
with st.form("lesson_form"):
  col1, col2 = st.columns(2)
  with col1:
    grade = st.selectbox(
        "Класс",
        [
            "5 класс",
            "6 класс",
            "7 класс",
            "8 класс",
            "9 класс",
            "10 класс",
            "11 класс",
        ],
    )
    subject = st.selectbox(
        "Предмет",
        [
            "Русский язык",
            "Русская литература",
            "Человек и общество",
            "История",
            "Другой предмет",
        ],
    )

  with col2:
    plan_type = st.radio(
        "Тип документа", ["КТП (Календарно-тематический план)", "Поурочный план"]
    )
    lessons_count = st.number_input(
        "Количество уроков / часов", min_value=1, max_value=68, value=20
    )

  topic = st.text_input(
      "Тема или раздел (например: Имя существительное, Творчество Лермонтова)"
  )

  submitted = st.form_submit_button(
      "🚀 Сгенерировать / Найти в базе", use_container_width=True
  )

if submitted:
  if not topic.strip():
    st.warning("Пожалуйста, введите тему или раздел.")
  elif not API_KEY:
    st.error("Пожалуйста, укажите API-ключ Gemini.")
  else:
    # Создаем уникальный и стабильный ключ для этой комбинации параметров
    cache_key = (
        f"{grade}_{subject}_{plan_type}_{lessons_count}_{topic.strip()}"
        .lower()
        .replace(" ", "_")
    )

    cache = load_cache()

    # 1. ПЕРВЫЙ ДИСК-УРОВЕНЬ: Проверяем, есть ли готовый план в локальном кэше
    if cache_key in cache:
      st.success(
          "⚡ План найден в базе! Загружено мгновенно без запроса к нейросети."
      )
      st.markdown("---")
      st.markdown(cache[cache_key])
    else:
      # 2. Если в кэше нет — делаем запрос к Gemini API
      with st.spinner(
          "⏳ Идет генерация нового плана с помощью Gemini (это займет пару"
          " секунд)..."
      ):
        try:
          client = genai.Client(api_key=API_KEY)

          prompt = (
              f"Ты — опытный учитель высшей категории. Составь детальный"
              f" профессиональный {plan_type} по предмету '{subject}' для"
              f" {grade} по стандарту образования. Тема/раздел: '{topic}'. Объем:"
              f" рассчитано на {lessons_count} уроков. Структурируй материал"
              f" четко, с указанием тем каждого урока, целей обучения и"
              f" ожидаемых результатов. Напиши материал на русском языке."
          )

          # Используем актуальную модель flash
          response = client.models.generate_content(
              model="gemini-2.5-flash",
              contents=prompt,
          )

          plan_text = response.text

          # Сохраняем в кэш для всех будущих пользователей
          save_to_cache(cache_key, plan_text)

          st.success(
              "✅ План успешно сгенерирован и сохранен в общую базу сайта!"
          )
          st.markdown("---")
          st.markdown(plan_text)

        except Exception as e:
          err_str = str(e)
          if "429" in err_str or "ResourceExhausted" in err_str:
            st.error(
                "⚠️ Превышен лимит бесплатных запросов (ошибка 429). Подождите"
                " 1-2 минуты или попробуйте тему, которая уже есть в кэше."
            )
          else:
            st.error(f"Произошла ошибка при обращении к API: {e}")
