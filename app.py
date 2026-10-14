import streamlit as st
import google.generativeai as genai
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

if API_KEY:
    genai.configure(api_key=API_KEY)

if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_title" not in st.session_state:
    st.session_state.last_title = "Поурочный_план"

# Боковая панель
with st.sidebar:
    st.title("Настройки")
    st.markdown("---")
    st.markdown("### ℹ️ О программе")
    st.markdown(
        "Инструмент для глубокой поурочной генерации и поочередного разбора заданий. Каждая задача и каждый план прорабатываются отдельно, а на выходе формируется единый документ с разрывом страниц для каждого урока."
    )
    st.markdown("---")
    st.markdown(
        """
        <div style="border: 2px dashed #ccc; padding: 15px; border-radius: 8px; text-align: center; background-color: #fafafa; color: #666;">
            📢 <b>Приложение для учителей</b><br>
            <span style="font-size: 12px; color: #888;">Качественные разработки для школ КР</span>
        </div>
        """,
        unsafe_allow_html=True
    )

st.title("📚 Помощник Учителя КР")
st.markdown("Режим поочередной обработки: каждый элемент (урок или задача) прорабатывается отдельно и оформляется на отдельной странице.")

work_mode = st.selectbox(
    "Выберите режим работы:",
    [
        "📝 Генератор Поурочного Плана (Один урок)",
        "📋 Поочередный генератор поурочных планов (серия тем)",
        "📸 Поочередный генератор поурочных планов по фото",
        "🔍 Поочередный разбор ДЗ / Задач ученика"
    ]
)

st.markdown("---")

def generate_with_retry(prompt_text, images=None, max_retries=3):
    """
    Устойчивая функция запроса к актуальным моделям с автоповтором
    """
    if not API_KEY:
        return "⚠️ Ошибка: API ключ не найден в конфигурации secrets Streamlit."
        
    contents = [prompt_text]
    if images:
        if isinstance(images, list):
            contents.extend(images)
        else:
            contents.append(images)
            
    # Используем только актуальные рабочие модели (без устаревших 1.5-flash)
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-3.8"]
    
    last_error = ""
    for model_name in models_to_try:
        for attempt in range(1, max_retries + 1):
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(contents)
                if response and response.text:
                    return response.text
            except Exception as e:
                last_error = str(e)
                time.sleep(3.0 * attempt)
                continue
                
    return f"⚠️ Не удалось сгенерировать. Ошибка: {last_error}"

# Режим 1: Один урок
if work_mode == "📝 Генератор Поурочного Плана (Один урок)":
    st.subheader("🗓️ Создание Поурочного Плана")
    
    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("Предмет:", placeholder="Например: История Кыргызстана")
        grade = st.selectbox("Класс:", ["5 класс", "6 класс", "7 класс", "8 класс", "9 класс", "10 класс", "11 класс"])
    with col2:
        duration = st.selectbox("Длительность урока:", ["45 минут", "90 минут (пара)"])
        lesson_topic = st.text_input("Тема урока:", placeholder="Например: Введение в историю Кыргызстана VII класса")

    competences = st.text_input("Компетенции (необязательно):", placeholder="Например: КК-1, ПК-1")
    objectives = st.text_area("Цели обучения (необязательно):", placeholder="Понять основные исторические источники...")
    
    if st.button("Сгенерировать поурочный план", type="primary"):
        if not subject or not lesson_topic:
            st.warning("⚠️ Заполните предмет и тему урока.")
        else:
            with st.spinner("Создаю подробный поурочный план..."):
                prompt = (
                    f"Ты — опытный методист-педагог в Кыргызстане. Составь максимально подробный, профессиональный, развернутый поурочный план "
                    f"по предмету '{subject}' для {grade}. Длительность: {duration}. Тема: {lesson_topic}. "
                    f"Учти в работе стандарты образования Кыргызской Республики.\n\n"
                    f"ОБЯЗАТЕЛЬНАЯ ПОДРОБНАЯ СТРУКТУРА:\n"
                    f"1. Заголовок: ### ПОУРОЧНЫЙ ПЛАН: {lesson_topic}\n"
                    f"2. Блок «1. Цели урока:» (подробно распиши: а) Обучающая, б) Развивающая, в) Воспитательная).\n"
                    f"3. Блок «2. Ключевые и предметные компетенции (по стандарту КР):» (укажи КК-1, КК-2, ПК-1 и др. с их полной расшифровкой).\n"
                    f"4. Блок «3. Оборудование и наглядные пособия:» (подробный список материалов, карт, учебников).\n"
                    f"5. Блок «4. Ход урока:» — оформи ИСКЛЮЧИТЕЛЬНО в виде большой, детализированной Markdown-таблицы со следующими колонками:\n"
                    f"| Этап урока и время | Деятельность учителя | Деятельность ученика | Оценивание / Методические указания |\n\n"
                    f"Пиши ОЧЕНЬ развернуто и глубоко на русском языке. Не сокращай фразы!"
                )
                res = generate_with_retry(prompt)
                if res and not res.startswith("⚠️"):
                    st.session_state.last_result = res
                    st.session_state.last_title = f"Урок_{subject}_{lesson_topic}"
                    st.success("План готов!")
                else:
                    st.error(res if res else "Не удалось сгенерировать план.")

# Режим 2: Поочередная генерация серии подробных уроков
elif work_mode == "📋 Поочередный генератор поурочных планов (серия тем)":
    st.subheader("📚 Поочередная генерация серии полноценных поурочных планов")
    st.markdown("Каждый урок генерируется отдельным детальным запросом. Каждый новый план начинается строго с новой страницы!")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        block_subject = st.text_input("Предмет:", placeholder="Например: История Кыргызстана")
        block_grade = st.selectbox("Класс:", ["5 класс", "6 класс", "7 класс", "8 класс", "9 класс", "10 класс", "11 класс"], key="pb_grade")
    with col_b2:
        lessons_count = st.slider("Количество поурочных планов для создания:", min_value=2, max_value=20, value=5, step=1)
        
    section_name = st.text_input("Название раздела / общей темы:", placeholder="Например: Раздел «Древний Кыргызстан»")
    
    if st.button("Запустить поочередную генерацию", type="primary"):
        if not block_subject or not section_name:
            st.warning("⚠️ Укажите предмет и название раздела.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_lessons_list = []
            
            for i in range(1, lessons_count + 1):
                status_text.markdown(f"⏳ **Генерирую урок {i} из {lessons_count}...**")
                progress_bar.progress(i / lessons_count)
                
                lesson_prompt = (
                    f"Ты — опытный методист-педагог в Кыргызстане. Напиши ПОЛНОЦЕННЫЙ, БОЛЬШОЙ И ПОДРОБНЫЙ поурочный план (Урок № {i}) "
                    f"по предмету '{block_subject}' для {block_grade} по разделу '{section_name}'. "
                    f"Это урок {i} из серии {lessons_count} уроков. Сформулируй конкретную, логичную тему урока в рамках раздела.\n\n"
                    f"СТРОГИЕ ТРЕБОВАНИЯ К ФОРМАТУ И ОБЪЕМУ:\n"
                    f"1. Заголовок: ### Урок № {i}. [Тема урока]\n"
                    f"2. **1. Цели урока:** (распиши детально обучающую, развивающую и воспитательную цели).\n"
                    f"3. **2. Ключевые и предметные компетенции (по стандарту КР):** (укажи конкретно КК-1, КК-2, ПК-1, ПК-2 с расшифровкой).\n"
                    f"4. **3. Оборудование и наглядность:** (полный перечень).\n"
                    f"5. **4. Ход урока:** ОБЯЗАТЕЛЬНО оформи в виде огромной подробной Markdown-таблицы с колонками:\n"
                    f"| Этап урока и время | Деятельность учителя | Деятельность ученика | Оценивание |\n\n"
                    f"Пиши МАКСИМАЛЬНО подробно, детально и качественно. Не экономь слова, не сокращай таблицы!"
                )
                
                lesson_result = generate_with_retry(lesson_prompt)
                page_break_code = '\n\n<div style="page-break-after: always; break-after: page;"></div>\n\n---\n\n' if i > 1 else ''
                
                if lesson_result and not lesson_result.startswith("⚠️"):
                    all_lessons_list.append(f"{page_break_code}{lesson_result}")
                else:
                    all_lessons_list.append(f"{page_break_code}### Урок № {i}\n({lesson_result})")
                
                time.sleep(3.5)
            
            full_combined_text = f"# Комплекс поурочных планов: {block_subject} — {section_name}\n\n" + "".join(all_lessons_list)
            
            st.session_state.last_result = full_combined_text
            st.session_state.last_title = f"Поурочные_планы_{block_subject}_{section_name}"
            
            status_text.text("✅ Все уроки успешно сгенерированы!")
            progress_bar.progress(1.0)
            st.success("Готово! Скачайте полный документ ниже.")

# Режим 3: Поочередный генератор по фото
elif work_mode == "📸 Поочередный генератор поурочных планов по фото":
    st.subheader("📸 Поочередная генерация поурочных планов по фотографиям")
    st.markdown("Загрузите фото — программа проработает каждый урок по отдельности.")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        photo_subject = st.text_input("Предмет:", placeholder="Например: Русская литература", key="pp_sub")
        photo_grade = st.selectbox("Класс:", ["5 класс", "6 класс", "7 класс", "8 класс", "9 класс", "10 класс", "11 класс"], key="pp_grade")
    with col_p2:
        photo_lessons_count = st.slider("Количество уроков:", min_value=2, max_value=15, value=3, step=1, key="pp_count")

    uploaded_files = st.file_uploader("Прикрепите фото страниц учебника", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="pp_files")

    if st.button("Запустить генерацию по фото", type="primary"):
        if not uploaded_files:
            st.warning("⚠️ Прикрепите хотя бы одну фотографию.")
        else:
            pil_images = [Image.open(f) for f in uploaded_files]
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_lessons_list = []
            
            for i in range(1, photo_lessons_count + 1):
                status_text.markdown(f"⏳ **Анализирую фото и создаю урок {i} из {photo_lessons_count}...**")
                progress_bar.progress(i / photo_lessons_count)
                
                lesson_prompt = (
                    f"Ты — опытный методист в Кыргызстане. На основе прикрепленных фотографий учебника по предмету '{photo_subject}' ({photo_grade}) "
                    f"составь ОДИН развернутый и полный поурочный план для Урока № {i}.\n\n"
                    f"СТРУКТУРА:\n"
                    f"1. Заголовок: ### Урок № {i}. [Тема по фото]\n"
                    f"2. Цели урока (обучающая, развивающая, воспитательная).\n"
                    f"3. Компетенции КР (КК и ПК).\n"
                    f"4. Ход урока в виде большой Markdown-таблицы (Этап, Деятельность учителя, Деятельность ученика, Оценивание).\n"
                    f"Пиши максимально подробно."
                )
                
                lesson_result = generate_with_retry(lesson_prompt, images=pil_images)
                page_break_code = '\n\n<div style="page-break-after: always; break-after: page;"></div>\n\n---\n\n' if i > 1 else ''
                
                if lesson_result and not lesson_result.startswith("⚠️"):
                    all_lessons_list.append(f"{page_break_code}{lesson_result}")
                else:
                    all_lessons_list.append(f"{page_break_code}### Урок № {i}\n({lesson_result})")
                    
                time.sleep(3.5)
            
            full_combined_text = f"# Комплекс поурочных планов по фото: {photo_subject} ({photo_grade})\n\n" + "".join(all_lessons_list)
            st.session_state.last_result = full_combined_text
            st.session_state.last_title = f"Поурочные_планы_по_фото_{photo_subject}"
            
            status_text.text("✅ Все уроки по фото созданы!")
            progress_bar.progress(1.0)
            st.success("Готово!")

# Режим 4: Поочередный разбор ДЗ / Задач ученика
else:
    st.subheader("🔍 Поочередный разбор ДЗ / Задач ученика")
    st.markdown("Разбор каждой задачи по отдельности на отдельном листе.")
    
    hw_subject = st.text_input("Предмет:", placeholder="Например: Алгебра / Физика")
    hw_questions_text = st.text_area("Список вопросов или заданий (каждое с новой строки):", placeholder="1. Решить уравнение 2x + 5 = 15\n2. Найти площадь круга...")
    hw_files = st.file_uploader("Прикрепить фото с задачами", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="hw_files")

    if st.button("Запустить поочередный разбор задач", type="primary"):
        if not hw_questions_text.strip() and not hw_files:
            st.warning("⚠️ Введите текст заданий или прикрепите фотографии.")
        else:
            raw_tasks = [t.strip() for t in hw_questions_text.split("\n") if t.strip()]
            if not raw_tasks:
                raw_tasks = ["Задачи с прикрепленных фотографий"]
                
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_solutions_list = []
            total_tasks = len(raw_tasks)
            pil_images = [Image.open(f) for f in hw_files] if hw_files else None
            
            for idx, task_item in enumerate(raw_tasks, 1):
                status_text.markdown(f"⏳ **Разбираю задачу {idx} из {total_tasks}...**")
                progress_bar.progress(idx / total_tasks)
                
                task_prompt = (
                    f"Ты — опытный учитель и репетитор по предмету '{hw_subject}'. "
                    f"Разбери СТРОГО ОДНУ конкретную задачу (Задача № {idx}): '{task_item}'. "
                    f"Напиши условие, детальное пошаговое решение с пояснениями и четкий ответ."
                )
                
                solution_result = generate_with_retry(task_prompt, images=pil_images)
                page_break_code = '\n\n<div style="page-break-after: always; break-after: page;"></div>\n\n---\n\n' if idx > 1 else ''
                
                if solution_result and not solution_result.startswith("⚠️"):
                    all_solutions_list.append(f"{page_break_code}{solution_result}")
                else:
                    all_solutions_list.append(f"{page_break_code}### Задача № {idx}\n({solution_result})")
                    
                time.sleep(3.0)
            
            full_combined_solutions = f"# Поочередный разбор ДЗ: {hw_subject}\n\n" + "".join(all_solutions_list)
            st.session_state.last_result = full_combined_solutions
            st.session_state.last_title = f"Разбор_ДЗ_{hw_subject}"
            
            status_text.text("✅ Все задачи подробно разобраны!")
            progress_bar.progress(1.0)
            st.success("Готово!")

# Блок вывода результатов и скачивания
if st.session_state.last_result:
    st.markdown("---")
    st.subheader("📄 Сгенерированный материал:")
    
    st.download_button(
        label="📥 Скачать единый документ (.txt / открыть можно в Word)",
        data=st.session_state.last_result,
        file_name=f"{st.session_state.last_title}.txt",
        mime="text/plain",
        type="primary"
    )
            
    st.markdown("---")
    st.markdown(st.session_state.last_result, unsafe_allow_html=True)

# Рекламный блок внизу страницы
st.markdown("---")
st.markdown(
    """
    <div style="border: 2px dashed #bbb; padding: 20px; border-radius: 10px; text-align: center; background-color: #fcfcfc; color: #666;">
        📢 <b>Приложение для создания поурочных планов</b><br>
        <span style="font-size: 13px; color: #888;">Качественные поурочные разработки для учителей школ</span>
    </div>
    """,
    unsafe_allow_html=True
)
