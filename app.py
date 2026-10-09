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

# Инициализация конфигурации genai
if API_KEY:
    genai.configure(api_key=API_KEY)

# Инициализация кэша в session_state
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
    # Рекламный блок в сайдбаре слева
    st.markdown(
        """
        <div style="border: 2px dashed #ccc; padding: 15px; border-radius: 8px; text-align: center; background-color: #fafafa; color: #666;">
            📢 <b>Приложение для учителей</b><br>
            <span style="font-size: 12px; color: #888;">Качественные разработки для школ КР</span>
        </div>
        """,
        unsafe_allow_html=True
    )

# Основной контент
st.title("📚 Помощник Учителя КР")
st.markdown("Режим поочередной обработки: каждый элемент (урок или задача) прорабатывается индивидуально и оформляется на отдельной странице.")

# Выбор режима работы
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

def generate_single_call(prompt_text, images=None):
    if not API_KEY:
        return "⚠️ Ошибка: API ключ не найден в конфигурации secrets Streamlit."
        
    # Собираем контент для модели
    contents = [prompt_text]
    if images:
        if isinstance(images, list):
            contents.extend(images)
        else:
            contents.append(images)
            
    # Используем проверенные стабильные модели
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(contents)
            if response and response.text:
                return response.text
        except Exception as e:
            time.sleep(1.0)
            continue
    return None

# Режим 1: Один урок
if work_mode == "📝 Генератор Поурочного Плана (Один урок)":
    st.subheader("🗓️ Создание Поурочного Плана")
    
    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("Предмет:", placeholder="Например: Русский язык и литература")
        grade = st.selectbox("Класс:", ["5 класс", "6 класс", "7 класс", "8 класс", "9 класс", "10 класс", "11 класс"])
    with col2:
        duration = st.selectbox("Длительность урока:", ["45 минут", "90 минут (пара)"])
        lesson_topic = st.text_input("Тема урока:", placeholder="Например: И.С. Тургенев, рассказ «Муму»")

    competences = st.text_input("Компетенции (необязательно):", placeholder="Например: ПК-1, ПК-2")
    objectives = st.text_area("Цели обучения (необязательно):", placeholder="Понять образ главного героя...")
    
    if st.button("Сгенерировать поурочный план", type="primary"):
        if not subject or not lesson_topic:
            st.warning("⚠️ Заполните предмет и тему урока.")
        else:
            with st.spinner("Создаю качественный план..."):
                prompt = (
                    f"Ты — опытный методист в Кыргызстане. Составь подробный профессиональный поурочный план "
                    f"по предмету '{subject}' для {grade}. Длительность: {duration}. Тема: {lesson_topic}. "
                    f"Компетенции: {competences if competences else 'Определи по стандарту КР'}. "
                    f"Цели: {objectives if objectives else 'Стандартные'}. "
                    f"СТРОГОЕ ТРЕБОВАНИЕ: Ход урока оформи ИСКЛЮЧИТЕЛЬНО в виде Markdown-таблицы с колонками: "
                    f"| Этап урока и время | Деятельность учителя | Деятельность ученика | Оценивание / Методические указания |"
                )
                res = generate_single_call(prompt)
                if res and not res.startswith("⚠️"):
                    st.session_state.last_result = res
                    st.session_state.last_title = f"Урок_{subject}_{lesson_topic}"
                    st.success("План готов!")
                else:
                    st.error("Не удалось сгенерировать план. Проверьте API-ключ или квоты.")

# Режим 2: Поочередный генератор по тексту
elif work_mode == "📋 Поочередный генератор поурочных планов (серия тем)":
    st.subheader("📚 Поочередная генерация поурочных планов (серия тем)")
    st.markdown("Каждый поурочный план генерируется отдельно, получая свои личные цели, компетенции и полноценную таблицу, а затем объединяется в единый документ с разрывом страниц.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        block_subject = st.text_input("Предмет:", placeholder="Например: История Кыргызстана")
        block_grade = st.selectbox("Класс:", ["5 класс", "6 класс", "7 класс", "8 класс", "9 класс", "10 класс", "11 класс"], key="pb_grade")
    with col_b2:
        lessons_count = st.slider("Количество поурочных планов для создания:", min_value=3, max_value=35, value=10, step=1)
        
    section_name = st.text_input("Название раздела / общей темы:", placeholder="Например: Раздел «Древний Кыргызстан»")
    
    if st.button("Запустить поочередную генерацию", type="primary"):
        if not block_subject or not section_name:
            st.warning("⚠️ Укажите предмет и название раздела.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_lessons_html = []
            
            for i in range(1, lessons_count + 1):
                status_text.text(f"⏳ Генерирую поурочный план {i} из {lessons_count} (пауза для стабильности)...")
                progress_bar.progress(i / lessons_count)
                
                lesson_prompt = (
                    f"Ты — опытный методист в Кыргызстане. Составь ОДИН отдельный поурочный план (Урок № {i}) "
                    f"по предмету '{block_subject}' для {block_grade} по разделу '{section_name}'. "
                    f"Это урок номер {i} из серии в {lessons_count} поурочных планов. Придумай логичную тему для этого урока в рамках раздела. "
                    f"СТРОГАЯ СТРУКТУРА УРОКА: "
                    f"1. Заголовок: ### Урок № {i}. [Тема урока] \n"
                    f"2. Персональные цели этого урока (обучающая, развивающая, воспитательная). \n"
                    f"3. Персональные компетенции для этого урока (КК и ПК по стандарту КР). \n"
                    f"4. Ход урока ОБЯЗАТЕЛЬНО оформи в виде полноценной Markdown-таблицы с колонками: "
                    f"| Этап урока и время | Деятельность учителя | Деятельность ученика | Оценивание | \n"
                    f"Пиши на русском языке подробно и качественно."
                )
                
                lesson_result = generate_single_call(lesson_prompt)
                page_break = '<div style="page-break-after: always; break-after: page;"></div>\n\n' if i > 1 else ''
                
                if lesson_result and not lesson_result.startswith("⚠️"):
                    formatted_lesson = f"{page_break}{lesson_result}\n\n"
                    all_lessons_html.append(formatted_lesson)
                else:
                    all_lessons_html.append(f"{page_break}### Урок № {i}\n(Ошибка генерации этого урока)\n\n")
                
                time.sleep(1.5)  # Безопасная пауза между запросами
            
            full_combined_text = f"# Комплекс поурочных планов: {block_subject} — {section_name}\n\n" + "".join(all_lessons_html)
            
            st.session_state.last_result = full_combined_text
            st.session_state.last_title = f"Поурочные_планы_{block_subject}_{section_name}"
            
            status_text.text("✅ Все поурочные планы успешно сгенерированы и оформлены по отдельным страницам!")
            progress_bar.progress(1.0)
            st.success("Готово! Можете скачать единый документ ниже.")

# Режим 3: Поочередный генератор по фото
elif work_mode == "📸 Поочередный генератор поурочных планов по фото":
    st.subheader("📸 Поочередная генерация поурочных планов по фотографиям учебника")
    st.markdown("Загрузите фото — программа проанализирует их и создаст каждый поурочный план отдельным запросом на новой странице.")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        photo_subject = st.text_input("Предмет:", placeholder="Например: Русская литература", key="pp_sub")
        photo_grade = st.selectbox("Класс:", ["5 класс", "6 класс", "7 класс", "8 класс", "9 класс", "10 класс", "11 класс"], key="pp_grade")
    with col_p2:
        photo_lessons_count = st.slider("Количество поурочных планов:", min_value=3, max_value=35, value=10, step=1, key="pp_count")

    uploaded_files = st.file_uploader("Прикрепите фото страниц программы/учебника", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="pp_files")

    if st.button("Запустить генерацию по фото", type="primary"):
        if not uploaded_files:
            st.warning("⚠️ Прикрепите хотя бы одну фотографию.")
        else:
            pil_images = [Image.open(f) for f in uploaded_files]
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_lessons_html = []
            
            for i in range(1, photo_lessons_count + 1):
                status_text.text(f"⏳ Анализирую фото и создаю поурочный план {i} из {photo_lessons_count}...")
                progress_bar.progress(i / photo_lessons_count)
                
                lesson_prompt = (
                    f"Ты — опытный методист в Кыргызстане. Используя прикрепленные фотографии страниц учебника по предмету '{photo_subject}' для {photo_grade}, "
                    f"составь ОДИН отдельный поурочный план для Урока № {i} (всего планов в серии: {photo_lessons_count}). "
                    f"СТРОГАЯ СТРУКТУРА: "
                    f"1. Заголовок: ### Урок № {i}. [Тема по материалам фото] \n"
                    f"2. Персональные цели урока (обучающая, развивающая, воспитательная). \n"
                    f"3. Персональные компетенции для этого урока (КК и ПК по стандарту КР). \n"
                    f"4. Ход урока ОБЯЗАТЕЛЬНО оформи в виде полноценной Markdown-таблицы с колонками: "
                    f"| Этап урока и время | Деятельность учителя | Деятельность ученика | Оценивание | \n"
                    f"Пиши на русском языке подробно."
                )
                
                lesson_result = generate_single_call(lesson_prompt, images=pil_images)
                page_break = '<div style="page-break-after: always; break-after: page;"></div>\n\n' if i > 1 else ''
                
                if lesson_result and not lesson_result.startswith("⚠️"):
                    formatted_lesson = f"{page_break}{lesson_result}\n\n"
                    all_lessons_html.append(formatted_lesson)
                else:
                    all_lessons_html.append(f"{page_break}### Урок № {i}\n(Ошибка генерации)\n\n")
                    
                time.sleep(1.5)  # Безопасная пауза
            
            full_combined_text = f"# Комплекс поурочных планов по фото: {photo_subject} ({photo_grade})\n\n" + "".join(all_lessons_html)
            
            st.session_state.last_result = full_combined_text
            st.session_state.last_title = f"Поурочные_планы_по_фото_{photo_subject}"
            
            status_text.text("✅ Все поурочные планы по фото успешно созданы на отдельных страницах!")
            progress_bar.progress(1.0)
            st.success("Готово! Материалы скомбинированы в единый документ.")

# Режим 4: Поочередный разбор ДЗ / Задач ученика
else:
    st.subheader("🔍 Поочередный разбор ДЗ / Задач ученика")
    st.markdown("Если ученик скинул несколько задач или вопросов, программа разберет их **строго по очереди**, каждую задачу на отдельной странице.")
    
    hw_subject = st.text_input("Предмет:", placeholder="Например: Алгебра / Физика")
    hw_questions_text = st.text_area("Список вопросов или заданий (каждое с новой строки):", placeholder="1. Решить уравнение 2x + 5 = 15\n2. Найти площадь круга...")
    hw_files = st.file_uploader("Прикрепить фото с задачами (можно несколько)", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="hw_files")

    if st.button("Запустить поочередный разбор задач", type="primary"):
        if not hw_questions_text.strip() and not hw_files:
            st.warning("⚠️ Введите текст заданий или прикрепите фотографии.")
        else:
            raw_tasks = [t.strip() for t in hw_questions_text.split("\n") if t.strip()]
            if not raw_tasks:
                raw_tasks = ["Задачи с прикрепленных фотографий"]
                
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_solutions_html = []
            total_tasks = len(raw_tasks)
            
            pil_images = [Image.open(f) for f in hw_files] if hw_files else None
            
            for idx, task_item in enumerate(raw_tasks, 1):
                status_text.text(f"⏳ Разбираю задачу {idx} из {total_tasks}...")
                progress_bar.progress(idx / total_tasks)
                
                task_prompt = (
                    f"Ты — опытный учитель и репетитор по предмету '{hw_subject}'. "
                    f"Разбери СТРОГО ОДНУ конкретную задачу (Задача № {idx}): '{task_item}'. "
                    f"Если прикреплены фотографии, ориентируйся на них. "
                    f"СТРОГАЯ СТРУКТУРА РАЗБОРА: "
                    f"1. Заголовок: ### Задача № {idx} \n"
                    f"2. Условие. \n"
                    f"3. Пошаговое решение с подробным объяснением каждого действия. \n"
                    f"4. Ответ. \n"
                    f"Пиши понятно и доступно на русском языке."
                )
                
                solution_result = generate_single_call(task_prompt, images=pil_images)
                page_break = '<div style="page-break-after: always; break-after: page;"></div>\n\n' if idx > 1 else ''
                
                if solution_result and not solution_result.startswith("⚠️"):
                    formatted_sol = f"{page_break}{solution_result}\n\n"
                    all_solutions_html.append(formatted_sol)
                else:
                    all_solutions_html.append(f"{page_break}### Задача № {idx}\n(Ошибка разбора)\n\n")
                    
                time.sleep(1.0)
            
            full_combined_solutions = f"# Поочередный разбор ДЗ / Задач по предмету: {hw_subject}\n\n" + "".join(all_solutions_html)
            
            st.session_state.last_result = full_combined_solutions
            st.session_state.last_title = f"Разбор_ДЗ_{hw_subject}"
            
            status_text.text("✅ Все задачи успешно разобщены и оформлены на отдельных страницах!")
            progress_bar.progress(1.0)
            st.success("Готово! Решения сформированы.")

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
