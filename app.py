import io
import time
import streamlit as st
from docx import Document
import google.generativeai as genai
from PIL import Image

# Настройка страницы Streamlit
st.set_page_config(
    page_title="Генератор поурочных планов", page_icon="📚", layout="centered"
)

# Заголовок приложения
st.title("📚 Генератор поурочных планов (20 уроков)")
st.write(
    "Создавайте комплекс из 20 подробных поурочных планов по теме или по фотографии материалов за пару секунд."
)

# Настройка API ключа (берётся из секрета Streamlit или вводится вручную)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Введите Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning(
        "Пожалуйста, укажите Gemini API Key в настройках secrets или в сайдбаре."
    )

# Выбор модели (используем gemini-1.5-flash)
model_name = "gemini-1.5-flash"

# Блок ввода данных
st.subheader("1. Исходные данные для генерации")
input_option = st.radio(
    "Выберите способ ввода темы:",
    ["Текстовый ввод темы / КТП", "Загрузить фото (страница КТП / учебника)"],
)

uploaded_image = None
text_prompt = ""

if input_option == "Текстовый ввод темы / КТП":
    text_prompt = st.text_area(
        "Введите тему, предмет и класс (например: Русский язык, 7 класс, тема: Имя существительное):",
        placeholder="Укажите предмет, класс и основные разделы темы...",
    )
else:
    uploaded_file = st.file_uploader(
        "Загрузите фото (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"]
    )
    if uploaded_file is not None:
        uploaded_image = Image.open(uploaded_file)
        st.image(
            uploaded_image,
            caption="Загруженное изображение",
            use_container_width=True,
        )
    extra_notes = st.text_input(
        "Дополнительные пожелания к урокам (необязательно):",
        placeholder="Например, сделать упор на практические упражнения...",
    )


# Функция генерации документов через Gemini с обработкой лимитов
def generate_20_lessons(prompt_content, image_obj=None):
    # Настраиваем генерацию с увеличенным лимитом токенов для 20 уроков
    generation_config = {
        "temperature": 0.7,
        "max_output_tokens": 8192,
    }

    model = genai.GenerativeModel(
        model_name=model_name, generation_config=generation_config
    )

    base_instruction = (
        "Ты — опытный методист и учитель. Твоя задача — составить ровно 20 подробных, "
        "качественных поурочных планов по стандартам образования. "
        "Для каждого из 20 уроков распиши: Номер и тему урока, цель, основные этапы урока, "
        "краткое содержание материала и домашнее задание. "
        "Структурируй текст четко, используя заголовки для каждого урока (Урок 1, Урок 2 и т.д.)."
    )

    if image_obj:
        contents = [
            base_instruction,
            image_obj,
            "Используй информацию с этого изображения для составления 20 поурочных планов.",
        ]
        if prompt_content:
            contents.append(f"Дополнительные пожелания: {prompt_content}")
    else:
        contents = f"{base_instruction}\n\nЗапрос/Тема: {prompt_content}"

    # Попытка генерации с обработкой ошибок API (включая 429 rate limit)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(contents)
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "ResourceExhausted" in error_str:
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
            raise e
    return None


# Функция создания Word-файла в памяти
def create_docx(text_content):
    doc = Document()
    doc.add_heading("Комплект поурочных планов (20 уроков)", 0)# Разбиваем текст на абзацы и добавляем в документ
    for line in text_content.split("\n"):
        if line.strip().startswith("Урок") or line.strip().startswith("#"):
            doc.add_heading(line.strip("# "), level=2)
        elif line.strip():
            doc.add_paragraph(line)

    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream


# Кнопка запуска генерации
st.markdown("---")
if st.button("🚀 Сгенерировать 20 поурочных планов", type="primary"):
    if not api_key:
        st.error("Пожалуйста, укажите API-ключ!")
    elif input_option == "Текстовый ввод темы / КТП" and not text_prompt.strip():
        st.warning("Пожалуйста, введите тему урока или КТП.")
    elif (
        input_option == "Загрузить фото (страница КТП / учебника)"
        and uploaded_image is None
    ):
        st.warning("Пожалуйста, загрузите изображение.")
    else:
        with st.spinner(
            "⏳ Идет генерация 20 подробных уроков. Это может занять полминуты..."
        ):
            try:
                result_text = generate_20_lessons(
                    text_prompt if input_option == "Текстовый ввод темы / КТП" else extra_notes,
                    uploaded_image,
                )

                if result_text:
                    st.success("✅ Все 20 поурочных планов успешно готовы!")

                    # Сохраняем в сессию, чтобы результат не пропадал
                    st.session_state["generated_lessons"] = result_text
                else:
                    st.error(
                        "Не удалось получить ответ от модели. Попробуйте еще раз."
                    )
            except Exception as e:
                st.error(
Сервер временно перегружен или превышен лимит запросов (ошибка API). Подождите минуту и нажмите кнопку снова.
                )

# Вывод результатов и кнопки скачивания, если они есть в памяти
if "generated_lessons" in st.session_state:
    st.subheader("📖 Результат генерации:")
    st.markdown(st.session_state["generated_lessons"])

    # Создаем файл для скачивания
    docx_file = create_docx(st.session_state["generated_lessons"])

    st.download_button(
        label="📥 Скачать поурочные планы в формате Word (.docx)",
        data=docx_file,
        file_name="20_Lessons_Plan.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
