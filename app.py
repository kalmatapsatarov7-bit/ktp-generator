import streamlit as st
from google import genai
from PIL import Image

# Настройка страницы
st.set_page_config(
    page_title="Помощник Учителя КР",
    page_icon="📚",
    layout="wide"
)

# Получаем API ключ из секретов Streamlit (учителям вводить ничего не нужно!)
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# Боковая панель (Левая колонка)
with st.sidebar:
    st.image("https://img.icons8.com/color/96/teacher.png", width=70)
    st.title("Настройки")
    
    st.markdown("---")
    
    # Рекламный блок вместо API-ключа (как ты и просил)
    st.markdown("### 📢 Реклама")
    st.markdown(
        """
        <div style="border: 2px dashed #ccc; padding: 15px; border-radius: 10px; text-align: center; background-color: #f9f9f9; color: #555;">
            <b>Место для вашего баннера</b><br>
            Здесь может быть реклама учебных курсов, пособий или партнерских услуг.
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ О программе")
    st.markdown(
        "Инструмент создан для быстрой разработки поурочных планов по стандартам КР и качественного разбора сложных вопросов с учениками."
    )

# Основной контент
st.title("📚 Помощник Учителя")
st.markdown("Интерактивный образовательный помощник: поурочные планы, блоки уроков и разбор домашних заданий.")

# Выбор режима работы
work_mode = st.selectbox(
    "Выберите режим работы:",
    [
        "📝 Генератор Поурочного Плана (Один урок)",
        "📋 Генератор блоком (10-15 уроков на четверть)",
        "🔍 Помощник ученика / Разбор ДЗ (Фото или Текст)"
    ]
)

st.markdown("---")

# Список моделей для авто-резерва
MODELS_TO_TRY = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro-latest",
    "gemini-1.5-pro",
    "gemini-flash-latest"
]

def generate_with_fallback(prompt_text, image=None):
    if not API_KEY:
        st.error("⚠️ Ошибка конфигурации: API-ключ не задан в секретах сервера.")
        return None
    
    client = genai.Client(api_key=API_KEY)
    contents = [prompt_text]
    if image:
        contents.append(image)
        
    response = None
    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            if response and response.text:
                return response.text
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "ResourceExhausted" in err_str or "503" in err_str:
                continue
            else:
                continue
    return None

# Режим 1: Один поурочный план
if work_mode == "📝 Генератор Поурочного Плана (Один урок)":
    st.subheader("🗓️ Создание Поурочного Плана")
    
    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("Предмет:", placeholder="Например: Русский язык и литература")
        grade = st.selectbox("Класс:", ["5 класс", "6 класс", "7 класс", "8 класс", "9 класс", "10 класс", "11 класс"])
    with col2:
        duration = st.selectbox("Длительность урока:", ["45 минут", "90 минут (пара)"])
        lesson_topic = st.text_input("Тема урока:", placeholder="Например: И.С. Тургенев, рассказ «Муму»")

    objectives = st.text_area("Цели обучения (если есть конкретные):", placeholder="Например: Понять образ главного героя, развивать навыки анализа текста...")

    if st.button("Сгенерировать поурочный план", type="primary"):
        if not subject or not lesson_topic:
            st.warning("⚠️ Пожалуйста, заполните предмет и тему урока.")
        else:
            with st.spinner("Создаю качественный поурочный план по стандартам..."):
                prompt = (
                    f"Ты — опытный методист и школьный учитель в Кыргызстане. "
                    f"Составь подробный профессиональный поурочный план по предмету '{subject}' для {grade}. "
                    f"Длительность урока: {duration}. "
                    f"Тема урока: '{lesson_topic}'. "
                    f"Цели обучения: {objectives if objectives else 'Стандартные по программе'}. "
                    f"План должен включать: 1. Организационный момент, 2. Опрос домашнего задания / Актуализация знаний, "
                    f"3. Объяснение нового материала, 4. Закрепление (практические задания), 5. Рефлексия и домашнее задание. "
                    f"Пиши структурированно, понятно и профессионально на русском языке."
                )
                
                result_text = generate_with_fallback(prompt)
                if result_text:
                    st.success("План готов!")
                    st.markdown("---")
                    st.markdown(result_text)
                else:
                    st.error("Все модели перегружены. Попробуйте еще раз через минуту.")

# Режим 2: Блок уроков (10-15 штук)
elif work_mode == "📋 Генератор блоком (10-15 уроков на четверть)":
    st.subheader("📚 Генерация серии уроков (на четверть / раздел)")
    
    block_subject = st.text_input("Предмет:", placeholder="Например: Человек и общество")
    block_grade = st.selectbox("Класс:", ["7 класс", "8 класс", "9 класс"])
    section_name = st.text_input("Название раздела или темы четверти:", placeholder="Например: Раздел «Этика и мораль» (10-12 уроков)")
    
    if st.button("Сгенерировать блок уроков", type="primary"):
        if not block_subject or not section_name:
            st.warning("⚠️ Укажите предмет и название раздела.")
        else:
            with st.spinner("Разрабатываю календарно-тематический блок уроков..."):
                prompt = (
                    f"Составь развернутый план-блок из 10-12 последовательных уроков по предмету '{block_subject}' для {block_grade} "
                    f"по разделу: '{section_name}'. "
                    f"Для каждого урока укажи номер, тему урока, краткое содержание и тип активности учеников. "
                    f"Оформи всё четко и структурированно на русском языке."
                )
                result_text = generate_with_fallback(prompt)
                if result_text:
                    st.success("Блок уроков успешно сгенерирован!")
                    st.markdown("---")
                    st.markdown(result_text)
                else:
                    st.error("Сервер перегружен. Попробуйте еще раз.")

# Режим 3: Помощник ученика / Разбор по фото или тексту
else:
    st.subheader("🔍 Помощник Ученика / Разбор ДЗ")
    st.markdown("Сфотографируйте страницу с упражнением или введите текст задачи, чтобы получить понятный пошаговый разбор.")

    hw_subject = st.text_input("Предмет задания:", placeholder="Например: Алгебра, Русский язык, Физика")
    hw_question = st.text_area("Текст задания / Вопрос ученика:", placeholder="Напишите условие задачи или вопрос...")
    hw_file = st.file_uploader("Прикрепите фото упражнения или задачи", type=["jpg", "jpeg", "png"])

    if st.button("Объяснить понятным языком", type="primary"):
        if not hw_question.strip() and not hw_file:
            st.warning("⚠️ Пожалуйста, напишите текст задания или прикрепите фотографию.")
        else:
            with st.spinner("Думаю над объяснением..."):
                hw_prompt = (
                    f"Ты — дружелюбный, терпеливый и мудрый учитель, который помогает "
                    f"школьнику разобраться с домашним заданием по предмету '{hw_subject}'. "
                    f"Объясни материал максимально понятно, доступно, с примерами и пошаговым разбором. "
                    f"Не просто дай готовый ответ, а объясни ученику почему и как это работает, чтобы он понял суть."
                )
                
                img_obj = Image.open(hw_file) if hw_file else None
                if hw_question.strip():
                    hw_prompt += f"\n\nЗадание/Вопрос ученика: {hw_question}"
                
                result_text = generate_with_fallback(hw_prompt, image=img_obj)
                if result_text:
                    st.success("Разбор готов!")
                    st.markdown("---")
                    st.markdown(result_text)
                else:
                    st.error("Все модели перегружены. Попробуйте повторить запрос.")

# Нижний рекламный баннер (остался на месте, как ты просил)
st.markdown("---")
st.markdown(
    """
    <div style="border: 2px dashed #bbb; padding: 20px; border-radius: 10px; text-align: center; background-color: #fcfcfc; color: #666;">
        📢 <b>Рекламный блок внизу страницы</b> — Отлично подходит для размещения партнерских ссылок или баннера для монетизации проекта.
    </div>
    """,
    unsafe_allow_html=True
)
