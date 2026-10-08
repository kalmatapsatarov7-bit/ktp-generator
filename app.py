import streamlit as st
from google import genai
from PIL import Image
import time

# Настройка страницы
st.set_page_config(
    page_title="Помощник Учителя КР",
    page_icon="📚",
    layout="wide"
)

# Получаем API ключ из секретов Streamlit
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# Инициализация кэша в session_state
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_title" not in st.session_state:
    st.session_state.last_title = "Поурочный_план"

# Боковая панель (Левая колонка)
with st.sidebar:
    st.image("https://img.icons8.com/color/96/teacher.png", width=70)
    st.title("Настройки")
    
    st.markdown("---")
    
    # Рекламный блок слева
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
        "Инструмент создан для быстрой разработки поурочных планов и КТП по стандартам КР с гарантированным табличным оформлением каждого урока."
    )

# Основной контент
st.title("📚 Помощник Учителя КР")
st.markdown("Интерактивный образовательный помощник: поурочные планы и серии уроков с принудительным табличным выводом для каждого урока.")

# Выбор режима работы
work_mode = st.selectbox(
    "Выберите режим работы:",
    [
        "📝 Генератор Поурочного Плана (Один урок)",
        "📋 Генератор блоком (серия уроков по тексту)",
        "📸 Генератор поурочных планов по фото (серия уроков)",
        "🔍 Помощник ученика / Разбор ДЗ (Фото или Текст)"
    ]
)

st.markdown("---")

def generate_with_fallback(prompt_text, images=None):
    if not API_KEY:
        st.error("⚠️ Ошибка конфигурации: API-ключ не задан в секретах сервера.")
        return None
        
    client = genai.Client(api_key=API_KEY)
    
    contents = [prompt_text]
    if images:
        if isinstance(images, list):
            contents.extend(images)
        else:
            contents.append(images)
    
    # Увеличиваем максимальное количество токенов до 16384, чтобы модели хватало места на таблицы для всех уроков
    config = {
        "max_output_tokens": 16384,
        "temperature": 0.5,
    }

    available_models = []
    try:
        models_pager = client.models.list()
        for m in models_pager:
            if "flash" in m.name.lower() or "gemini" in m.name.lower():
                available_models.append(m.name)
    except Exception:
        pass

    if not available_models:
        available_models = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]

    last_error = ""
    
    for model_name in available_models:
        try:
            clean_model_name = model_name.replace("models/", "")
            response = client.models.generate_content(
                model=clean_model_name,
                contents=contents,
                config=config
            )
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
            continue
            
    st.error(f"⚠️ Ошибка запроса ко всем доступным моделям. Детали: {last_error}")
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

    competences = st.text_input(
        "Компетенции (ключевые и предметные):", 
        placeholder="Например: ПК-1, ПК-2, ОК-1 (или оставить пустым для автоподбора по стандарту КР)"
    )
    objectives = st.text_area("Цели обучения (если есть конкретные):", placeholder="Например: Понять образ главного героя, развивать навыки анализа текста...")
    
    if st.button("Сгенерировать поурочный план", type="primary"):
        if not subject or not lesson_topic:
            st.warning("⚠️ Пожалуйста, заполните предмет и тему урока.")
        else:
            with st.spinner("Создаю качественный поурочный план с табличной структурой..."):
                prompt = (
                    f"Ты — опытный методист и школьный учитель высшей категории в Кыргызстане. "
                    f"Составь подробный профессиональный поурочный план по предмету '{subject}' для {grade} класса. "
                    f"Длительность урока: {duration}. Тема урока: {lesson_topic}. "
                    f"Компетенции для этого урока: {competences if competences else 'Определи стандартные ключевые и предметные компетенции по стандарту КР'}. "
                    f"Цели обучения: {objectives if objectives else 'Стандартные по программе'}. "
                    f"СТРОГОЕ ТРЕБОВАНИЕ: Ход урока должен быть оформлен ИСКЛЮЧИТЕЛЬНО в виде полноценной Markdown-таблицы с четырьмя колонками: "
                    f"| Этап урока и время | Деятельность учителя | Деятельность ученика | Оценивание / Методические указания |. "
                    f"Не используй списки для хода урока, только таблицу!"
                )

            result_text = generate_with_fallback(prompt)
            if result_text:
                st.session_state.last_result = result_text
                st.session_state.last_title = f"Поурочный_план_{subject}_{lesson_topic}"
                st.success("План с таблицей готов и сохранен в памяти!")

# Режим 2: Блок уроков по тексту
elif work_mode == "📋 Генератор блоком (серия уроков по тексту)":
    st.subheader("📚 Генерация КТП / серии уроков по тексту")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        block_subject = st.text_input("Предмет:", placeholder="Например: Человек и общество")
        block_grade = st.selectbox("Класс:", ["5 класс", "6 класс", "7 класс", "8 класс", "9 класс", "10 класс", "11 класс"], key="b_grade")
    with col_b2:
        lessons_count = st.slider("Количество уроков в блоке:", min_value=5, max_value=30, value=16, step=1)
        
    section_name = st.text_input("Название раздела или темы четверти:", placeholder="Например: Раздел «Этика и мораль»")
    block_competences = st.text_input(
        "Базовые компетенции:", 
        placeholder="Например: Развитие социально-гражданских и предметных компетенций",
        key="b_comp"
    )
    
    if st.button("Сгенерировать блок уроков", type="primary"):
        if not block_subject or not section_name:
            st.warning("⚠️ Укажите предмет и название раздела.")
        else:
            with st.spinner(f"Разрабатываю КТП из {lessons_count} уроков с таблицами для каждого урока..."):
                prompt = (
                    f"Составь развернутый план-блок ровно из {lessons_count} последовательных уроков по предмету '{block_subject}' для {block_grade} "
                    f"по разделу: '{section_name}'. "
                    f"КРИТИЧЕСКИ ВАЖНОЕ ТРЕБОВАНИЕ: "
                    f"1. Никаких общих вводных списков компетенций в шапке документа! "
                    f"2. КАЖДЫЙ из ровно {lessons_count} уроков должен начинаться с индивидуального заголовка (например, «Урок № 1...»), своих целей и своих персональных компетенций. "
                    f"3. ДЛЯ КАЖДОГО ИЗ {lessons_count} УРОКОВ ОБЯЗАТЕЛЬНО нарисуй отдельную полноценную Markdown-таблицу хода урока со следующими колонками: "
                    f"| Этап урока и время | Деятельность учителя | Деятельность ученика | Оценивание |. "
                    f"Не пропускай таблицы ни для одного урока! Строго выдержи количество: ровно {lessons_count} уроков. Пиши на русском языке."
                )
                result_text = generate_with_fallback(prompt)
                if result_text:
                    st.session_state.last_result = result_text
                    st.session_state.last_title = f"КТП_{block_subject}_{section_name}"
                    st.success(f"Блок ровно из {lessons_count} уроков с таблицами успешно сгенерирован!")

# Режим 3: Генератор поурочных планов по фотографиям
elif work_mode == "📸 Генератор поурочных планов по фото (серия уроков)":
    st.subheader("📸 Создание серии поурочных планов по фотографиям")
    st.markdown("Загрузите фотографии страниц учебника — каждый урок получит персональные компетенции и собственную таблицу.")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        photo_subject = st.text_input("Предмет:", placeholder="Например: История Кыргызстана")
        photo_grade = st.selectbox("Класс:", ["5 класс", "6 класс", "7 класс", "8 класс", "9 класс", "10 класс", "11 класс"], key="p_grade")
    with col_p2:
        photo_lessons_count = st.slider("Количество уроков для генерации:", min_value=5, max_value=30, value=16, step=1, key="p_slider")

    photo_competences = st.text_input(
        "Компетенции (по стандарту КР):", 
        placeholder="Например: Информационная, коммуникативная, социально-мировоззренческая",
        key="p_comp"
    )
    uploaded_files = st.file_uploader("Прикрепите фото страниц учебника/программы", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if st.button("Сгенерировать планы по фото", type="primary"):
        if not uploaded_files:
            st.warning("⚠️ Пожалуйста, прикрепите хотя бы одну фотографию.")
        else:
            with st.spinner(f"Анализирую фото и формирую ровно {photo_lessons_count} уроков с таблицами для каждого..."):
                pil_images = [Image.open(f) for f in uploaded_files]
                prompt = (
                    f"Ты — опытный методист и школьный учитель в Кыргызстане. "
                    f"На основе прикрепленных фотографий страниц учебника или программы по предмету '{photo_subject}' для {photo_grade} "
                    f"составь серию ровно из {photo_lessons_count} поурочных планов, охватывающих материал на фото. "
                    f"КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ: "
                    f"1. Запрещено создавать общие списки компетенций в самом начале документа. "
                    f"2. КАЖДЫЙ из {photo_lessons_count} уроков должен содержать свои персональные цели и свои конкретные компетенции прямо под своим заголовком. "
                    f"3. ДЛЯ КАЖДОГО УРОКА ОБЯЗАТЕЛЬНО создай отдельную детализированную Markdown-таблицу хода урока (колонки: "
                    f"| Этап урока и время | Деятельность учителя | Деятельность ученика | Оценивание |). "
                    f"Никаких сокращений или списков вместо таблиц! Строго выдержи количество: ровно {photo_lessons_count}. Пиши на русском языке."
                )
                result_text = generate_with_fallback(prompt, images=pil_images)
                if result_text:
                    st.session_state.last_result = result_text
                    st.session_state.last_title = f"КТП_по_фото_{photo_subject}"
                    st.success(f"КТП из {photo_lessons_count} уроков с таблицами успешно создано!")

# Режим 4: Помощник ученика / Разбор по фото или тексту
else:
    st.subheader("🔍 Помощник Ученика / Разбор ДЗ")
    st.markdown("Сфотографируйте страницу с упражнением или введите текст задачи, чтобы получить понятный пошаговый разбор.")

    hw_subject = st.text_input("Предмет задания:", placeholder="Например: Алгебра, Русский язык, Физика")
    hw_question = st.text_area("Текст задания / Вопрос ученика:", placeholder="Напишите условие задачи или вопрос...")
    hw_file = st.file_uploader("Прикрепите фото упражнения или задачи", type=["jpg", "jpeg", "png"], key="hw_single")

    if st.button("Объяснить понятным языком", type="primary"):
        if not hw_question.strip() and not hw_file:
            st.warning("⚠️ Пожалуйста, напишите текст задания или прикрепите фотографию.")
        else:
            with st.spinner("Думаю над объяснением..."):
                hw_prompt = (
                    f"Ты — дружелюбный, терпеливый и мудрый учитель, который помогает "
                    f"школьнику разобраться с домашним заданием по предмету '{hw_subject}'. "
                    f"Объясни материал максимально понятно, доступно, с примерами и пошаговым разбором. "
                    f"Если применимо, используй небольшие таблицы для наглядности сравнений или формул."
                )
                
                img_obj = Image.open(hw_file) if hw_file else None
                if hw_question.strip():
                    hw_prompt += f"\n\nЗадание/Вопрос ученика: {hw_question}"
                
                result_text = generate_with_fallback(hw_prompt, images=img_obj)
                if result_text:
                    st.session_state.last_result = result_text
                    st.session_state.last_title = f"Разбор_ДЗ_{hw_subject}"
                    st.success("Разбор готов и сохранен в памяти!")

# Вывод сохраненного в кэше результата и кнопки скачивания
if st.session_state.last_result:
    st.markdown("---")
    st.subheader("📄 Последний сгенерированный материал:")
    
    st.download_button(
        label="📥 Скачать материалом в файл (.txt)",
        data=st.session_state.last_result,
        file_name=f"{st.session_state.last_title}.txt",
        mime="text/plain",
        type="primary"
    )
    
    st.markdown("---")
    st.markdown(st.session_state.last_result)

# Нижний рекламный баннер
st.markdown("---")
st.markdown(
    """
    <div style="border: 2px dashed #bbb; padding: 20px; border-radius: 10px; text-align: center; background-color: #fcfcfc; color: #666;">
        📢 <b>Рекламный блок внизу страницы</b> — Отлично подходит для размещения партнерских ссылок или баннера для монетизации проекта.
    </div>
    """,
    unsafe_allow_html=True
)
