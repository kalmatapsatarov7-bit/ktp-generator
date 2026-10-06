import json
import os
import streamlit as st
from google import genai
from PIL import Image

# Настройка страницы
st.set_page_config(
    page_title="Учительская и ученическая платформа",
    page_icon="📖",
    layout="centered",
)

# Настройка ключа API и клиента Gemini
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not API_KEY:
  API_KEY = st.text_input("Google AI Studio API Key", type="password")

# Файл для постоянного кэширования планов на сервере
CACHE_FILE = "lesson_plans_cache.json"


def load_cache():
  if os.path.exists(CACHE_FILE):
    try:
      with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return {}
  return {}


def save_to_cache(key, plan_text):
  cache = load_cache()
  cache[key] = plan_text
  try:
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
      json.dump(cache, f, ensure_ascii=False, indent=4)
  except Exception as e:
    st.error(f"Ошибка сохранения в кэш: {e}")


# Выбор режима работы приложения через боковую панель или вкладки
st.title("📖 Образовательный помощник")

tab1, tab2 = st.tabs(
    ["📝 Генератор поурочных планов", "💡 Помощник по домашним заданиям"]
)

# ================= TAB 1: ПОУРОЧНЫЕ ПЛАНЫ (для учителя) =================
with tab1:
  st.header("Конструктор поурочных планов")
  st.markdown(
      "Создавайте подробные поурочные планы. Загружайте фото материалов или"
      " вводите тему вручную. Повторные запросы загружаются **мгновенно и без"
      " расхода лимитов**!"
  )

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
          key="l_grade",
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
          key="l_subject",
      )

    with col2:
      lessons_count = st.number_input(
          "Количество уроков в теме", min_value=1, max_value=30, value=5, key="l_count"
      )

    topic = st.text_input(
        "Тема урока или раздела (например: Имя существительное, Творчество"
        " Лермонтова)",
        key="l_topic",
    )

    uploaded_file = st.file_uploader(
        "📸 Загрузить фото учебника или методички (необязательно)",
        type=["jpg", "jpeg", "png"],
        key="l_file",
    )

    submitted = st.form_submit_button(
        "🚀 Сгенерировать поурочный план", use_container_width=True
    )

  if submitted:
    if not topic.strip() and not uploaded_file:
      st.warning("Пожалуйста, введите тему или загрузите изображение.")
    elif not API_KEY:
      st.error("Пожалуйста, укажите API-ключ Gemini.")
    else:
      photo_flag = "with_photo" if uploaded_file else "text_only"
      cache_key = (
          f"lesson_{grade}_{subject}_{lessons_count}_{topic.strip()}_{photo_flag}"
          .lower()
          .replace(" ", "_")
      )

      cache = load_cache()

      if cache_key in cache:
        st.success(
            "⚡ План найден в базе! Загружено мгновенно без запроса к нейросети."
        )
        st.markdown("---")
        st.markdown(cache[cache_key])
      else:
        with st.spinner("⏳ Генерация поурочного плана с помощью Gemini..."):
          try:
            client = genai.Client(api_key=API_KEY)
            prompt = (
                f"Ты — опытный школьный учитель высшей категории. Составь"
                f" детальный, профессиональный поурочный план по предмету"
                f" '{subject}' для {grade} по стандарту образования. Тема:"
                f" '{topic}'. Количество уроков: {lessons_count}. Для каждого"
                f" урока распиши: цель, этапы урока, объяснение материала и"
                f" задания. Напиши материал на русском языке."
            )

            contents = [prompt]
            if uploaded_file is not None:
              img = Image.open(uploaded_file)
              contents.append(img)
              prompt += " Используй также материалы с прикрепленного фото."
              contents[0] = prompt

            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=contents
            )
            plan_text = response.text

            save_to_cache(cache_key, plan_text)
            st.success("✅ План успешно сгенерирован и сохранен в базу!")
            st.markdown("---")
            st.markdown(plan_text)

          except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e):
              st.error(
                  "⚠️️ Превышен лимит запросов (ошибка 429). Подождите пару минут"
                  " или используйте план из кэша."
              )
            else:
              st.error(f"Произошла ошибка: {e}")

# ================= TAB 2: ПОМОЩНИК ПО ДОМАШНИМ ЗАДАНИЯМ (для учеников) =================
with tab2:
  st.header("💡 Объяснение домашнего задания")
  st.markdown(
      "Этот раздел предназначен для учеников. Сюда можно сфоткать сложное"
      " задание из учебника или написать вопрос, а система подробно и"
      " понятно объяснит правила, логику и шаг за шагом покажет, почему это"
      " решается именно так."
  )

  with st.form("hw_form"):
    hw_subject = st.selectbox(
        "Предмет",
        [
            "Русский язык",
            "Русская литература",
            "Человек и общество",
            "История",
            "Другой",
        ],
        key="hw_sub",
    )
    hw_question = st.text_area(
        "Напишите текст задания или свой вопрос:",
        placeholder=(
            "Например: Объясни, как отличить причастие от отглагольного"
            " прилагательного, или помоги разобрать предложение."
        ),
        key="hw_q",
    )
    hw_file = st.file_uploader(
        "📸 Прикрепите фото упражнения или задачи",
        type=["jpg", "jpeg", "png"],
        key="hw_f",
    )

    hw_submitted = st.form_submit_button(
        "🧠 Объяснить мне понятным языком", use_container_width=True
    )

  if hw_submitted:
    if not hw_question.strip() and not hw_file:
      st.warning(
          "Пожалуйста, напишите текст задания или прикрепите фотографию."
      )
    elif not API_KEY:
      st.error("Пожалуйста, укажите API-ключ Gemini.")
    else:
      with st.spinner("🤖 Думаю над объяснением..."):
        try:
          client = genai.Client(api_key=API_KEY)
          hw_prompt = (
              f"Ты — дружелюбный, терпеливый и мудрый учитель, который помогает"
              f" школьнику разобраться с домашним заданием по предмету"
              f" '{hw_subject}'. Объясни материал максимально понятно,"
              f" доступно, с примерами и пошаговым разбором. Не просто дай"
              f" готовый ответ, а объясни ученику **почему** и **как** это"
              f" работает, чтобы он понял суть."
          )

          contents = [hw_prompt]
          if hw_question.strip():
            contents.append(f"Задание/Вопрос ученика: {hw_question}")
          if hw_file is not None:
            hw_img = Image.open(hw_file)
            contents.append(hw_img)

          response = client.models.generate_content(
              model="gemini-2.5-flash", contents=contents
          )

          st.success("✅ Разбор готов!")
          st.markdown("---")
          st.markdown(response.text)

        except Exception as e:
          if "429" in str(e) or "ResourceExhausted" in str(e):
            st.error(
                "⚠️ Слишком много запросов к системе (ошибка 429). Пожалуйста,"
                " подождите минуту и попробуйте снова."
            )
          else:
            st.error(f"Произошла ошибка: {e}")
