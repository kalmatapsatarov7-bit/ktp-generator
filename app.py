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
        "Инструмент создан для быстрой разработки поурочных планов по стандартам КР и качественного разбора сложных вопросов с учениками."
    )

# Основной контент
st.title("📚 Помощник Учителя")
st.markdown("Интерактивный образовательный помощник: поурочные планы (по текстам и фото) с учетом компетенций, сохранением в кэш и выгрузкой в файл.")

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

# Актуальный список поддерживаемых моделей без устаревших суффиксов
MODELS_TO_TRY = [
    "gemini-2.5-flash",
    "gemini-3.8-flash",
]

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
    
    config = {
        "max_output_tokens": 8192,
        "temperature": 0.7,
    }

    # Список моделей для автоматического переключения при ошибках (503 перегрузка, 404 и т.д.)
    MODELS_TO_TRY = [
        "gemini-3.8-flash",
        "gemini-2.5-flash",
    ]

    last_error = ""
    
    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = str(e)
            continue  # Если модель перегружена или недоступна, молча пробуем следующую
            
    st.error(f"⚠️ Ошибка запроса ко всем моделям. Последняя ошибка: {last_error}")
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
                with st.spinner("Создаю качественный поурочный план с учетом компетенций по стандартам КР..."):
                    # Все строки ниже сдвинуты вправо (находятся внутри блока with)
                    lesson_lang = st.selectbox(
                        "Язык поурочного плана / Сабактын тили:",
                        ["Кыргызский (Кыргыз тилинде)", "Русский (На русском языке)"],
                        key="single_lesson_lang"
                    )

                    if lesson_lang.startswith("Кыргызский"):
                        lang_instruction = "Пиши строго на кыргызском языке (мамлекеттик тилде), используя профессиональную кыргызскую педагогическую терминологию."
                            structure_instruction = (
        "План терең, мазмундуу жана КР мамлекеттик стандарттарына так ылайык төмөнкүлөрдү камтууга тийиш: \n"
        "1. Сабактын темасы жана классы. \n"
        "2. Максаттары (окутуучу, өстүрүүчү, тарбиялык). \n"
        "3. Компетенттүүлүктөр (КК жана ПК КР стандарты боюнча). \n"
        "4. Сабактын жүрүшү СӨЗСҮЗ ТҮРДӨ төрт тилкеден турган Markdown-таблица түрүндө болсун: \n"
        "   | Бөлүк | Мазмуну жана көнүгүүлөр | Убакыт | Методикалык көрсөтмөлөр | \n"
        "   (кирүүчү, негизги жана жыйынтыктоочу бөлүктөргө мүнөттөрү менен бөл). \n"
        "5. Коопсуздук эрежелери жана керектүү жабдуулар. \n"
        "6. Үй тапшырмасы жана баалоо критерийлери."
    )

                    else:
                        lang_instruction = "Пиши строго на русском языке, используя профессиональную методическую терминологию."
                            structure_instruction = (
        "План должен быть глубоким, содержательным и оформленным строго по государственным стандартам КР, включая: \n"
        "1. Тему урока и класс. \n"
        "2. Цели урока (обучающая, развивающая, воспитательная). \n"
        "3. Компетенции (КК и ПК по стандарту КР). \n"
        "4. Ход урока ОБЯЗАТЕЛЬНО оформи в виде Markdown-таблицы с четырьмя колонками: \n"
        "   | Бөлүк | Мазмуну жана көнүгүүлөр | Убакыт | Методикалык көрсөтмөлөр | \n"
        "   (разбей на вводную, основную и заключительную части по минутам). \n"
        "5. Коопсуздук эрежелери (Правила безопасности) и необходимое оборудование. \n"
        "6. Дифференцированное домашнее задание и критерии оценивания."
    )


                    prompt = (
                        f"Ты — опытный методист, эксперт по разработке поурочных планов и школьный учитель высшей категории в Кыргызстане. "
                        f"Составь подробный профессиональный поурочный план по предмету '{subject}' для {grade} класса. "
                        f"Длительность урока: {duration}. Тема урока: {lesson_topic}. "
                        f"Компетенции: {competences if competences else 'Определи стандартные ключевые и предметные компетенции по стандарту КР'}. "
                        f"Цели обучения: {objectives if objectives else 'Стандартные по программе'}. "
                        f"{lang_instruction} "
                        f"Обязательно соблюдай государственные образовательные стандарты КР. "
                        f"{structure_instruction}"
                    )

                # Этот код возвращается на уровень выше (вне with, но внутри else)
                result_text = generate_with_fallback(prompt)
                if result_text:
                    st.session_state.last_result = result_text
                    st.session_state.last_title = f"Поурочный_план_{subject}_{lesson_topic}"
                    st.success("План с учетом компетенций готов и сохранен в памяти!")

                result_text = generate_with_fallback(prompt)
                if result_text:
                    st.session_state.last_result = result_text
                    st.session_state.last_title = f"Поурочный_план_{subject}_{lesson_topic}"
                    st.success("План с учетом компетенций готов и сохранен в памяти!")

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
        "Компетенции для блока уроков:", 
        placeholder="Например: Развитие социально-гражданских и предметных компетенций",
        key="b_comp"
    )
    
    if st.button("Сгенерировать блок уроков", type="primary"):
        if not block_subject or not section_name:
            st.warning("⚠️ Укажите предмет и название раздела.")
        else:
            with st.spinner(f"Разрабатываю календарно-тематический план из {lessons_count} уроков с компетенциями..."):
                prompt = (
                    f"Составь развернутый план-блок ровно из {lessons_count} последовательных уроков по предмету '{block_subject}' для {block_grade} "
                    f"по разделу: '{section_name}'. "
                    f"Учти следующие компетенции: {block_competences if block_competences else 'Стандартные ключевые и предметные компетенции по стандарту КР'}. "
                    f"Для каждого из {lessons_count} уроков укажи порядковый номер, тему урока, формируемые компетенции, краткое содержание и тип активности учеников. "
                    f"Оформи всё четко и структурированно на русском языке."
                )
                result_text = generate_with_fallback(prompt)
                if result_text:
                    st.session_state.last_result = result_text
                    st.session_state.last_title = f"КТП_{block_subject}_{section_name}"
                    st.success(f"Блок из {lessons_count} уроков успешно сгенерирован и сохранен в памяти!")

# Режим 3: Генератор поурочных планов по фотографиям
elif work_mode == "📸 Генератор поурочных планов по фото (серия уроков)":
    st.subheader("📸 Создание серии поурочных планов по фотографиям")
    st.markdown("Загрузите фотографии страниц учебника, оглавления или программы, выберите количество уроков и укажите акцент на компетенции.")

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
            with st.spinner(f"Анализирую фотографии и формирую КТП из {photo_lessons_count} уроков с компетенциями..."):
                pil_images = [Image.open(f) for f in uploaded_files]
                prompt = (
                    f"Ты — опытный методист и школьный учитель в Кыргызстане. "
                    f"На основе прикрепленных фотографий страниц учебника или программы по предмету '{photo_subject}' для {photo_grade} "
                    f"составь серию ровно из {photo_lessons_count} поурочных планов, охватывающих материал на фото. "
                    f"Обязательно пропиши для уроков требуемые компетенции: {photo_competences if photo_competences else 'Стандартные предметные и ключевые компетенции по стандартам КР'}. "
                    f"Для каждого урока подробно распиши номер, тему, цель, компетенции, этапы урока и задания. "
                    f"Пиши на русском языке, структурированно и профессионально."
                )
                result_text = generate_with_fallback(prompt, images=pil_images)
                if result_text:
                    st.session_state.last_result = result_text
                    st.session_state.last_title = f"КТП_по_фото_{photo_subject}"
                    st.success(f"КТП из {photo_lessons_count} уроков по фотографиям успешно создано и сохранено в памяти!")

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
                    f"Не просто дай готовый ответ, а объясни ученику почему и как это работает, чтобы он понял суть."
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
