import streamlit as st
import google.generativeai as genai
from PIL import Image
import time

st.set_page_config(
    page_title="Помощник Учителя КР",
    page_icon="📚",
    layout="wide"
)

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if API_KEY:
    genai.configure(api_key=API_KEY)

if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_title" not in st.session_state:
    st.session_state.last_title = "Поурочный_план"

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
st.markdown("Режим обработки: стабильная генерация качественных поурочных планов без зависаний.")

work_mode = st.selectbox(
    "Выберите режим работы:",
    [
        "📝 Генератор Поурочного Плана (Один урок)",
        "📋 Генератор серии уроков (Пакет до 4 уроков)",
        "📸 Генератор уроков по фото (Пакет до 4 уроков)",
        "🔍 Разбор ДЗ / Задач ученика"
    ]
)

st.markdown("---")

def generate_call(prompt_text, images=None):
    if not API_KEY:
        return "⚠️ Ошибка: API ключ не найден в конфигурации secrets Streamlit."
        
    contents = [prompt_text]
    if images:
        if isinstance(images, list):
            contents.extend(images)
        else:
            contents.append(images)
            
    try:
        model = genai.GenerativeModel("gemini-3.8")
        response = model.generate_content(contents)
        if response and response.text:
            return response.text
    except Exception as e:
        return f"⚠️ Ошибка: {str(e)}"
    return "⚠️ Не удалось получить ответ."

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
                    f"3. Блок «2. Ключевые и предметные компетенции (по стандарту КР):» (укажи КК-1, КК-2, ПК-1 и др. с расшифровкой).\n"
                    f"4. Блок «3. Оборудование и наглядные пособия:».\n"
                    f"5. Блок «4. Ход урока:» — оформи в виде большой, детализированной Markdown-таблицы:\n"
                    f"| Этап урока и время | Деятельность учителя | Деятельность ученика | Оценивание / Методические указания |\n\n"
                    f"Пиши ОЧЕНЬ развернуто и глубоко на русском языке."
                )
                res = generate_call(prompt)
                if res and not res.startswith("⚠️"):
                    st.session_state.last_result = res
                    st.session_state.last_title = f"Урок_{subject}_{lesson_topic}"
                    st.success("План готов!")
                else:
                    st.error(res)

# Режим 2: Пакет уроков (до 4 штук за раз стабильно)
elif work_mode == "📋 Генератор серии уроков (Пакет до 4 уроков)":
    st.subheader("📚 Генерация пакета поурочных планов (до 4 уроков)")
    st.markdown("Оптимальный объем для мгновенной генерации без зависаний сервера. Каждый урок подробный и на новой странице.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        block_subject = st.text_input("Предмет:", placeholder="Например: История Кыргызстана")
        block_grade = st.selectbox("Класс:", ["5 класс", "6 класс", "7 класс", "8 класс", "9 класс", "10 класс", "11 класс"], key="pb_grade")
    with col_b2:
        lessons_count = st.slider("Количество уроков:", min_value=2, max_value=4, value=3, step=1)
        
    section_name = st.text_input("Название раздела / общей темы:", placeholder="Например: Раздел «Древний Кыргызстан»")
    
    if st.button("Сгенерировать пакет уроков", type="primary"):
        if not block_subject or not section_name:
            st.warning("⚠️ Укажите предмет и название раздела.")
        else:
            with st.spinner(f"Генерирую комплекс из {lessons_count} подробных уроков... Пожалуйста, подождите."):
                package_prompt = (
                    f"Ты — опытный методист-педагог в Кыргызстане. Составь комплексный документ, содержащий ровно {lessons_count} подробных поурочных планов "
                    f"по предмету '{block_subject}' для {block_grade} по разделу '{section_name}'.\n\n"
                    f"ТРЕБОВАНИЯ К ОФОРМЛЕНИЮ КАЖДОГО УРОКА:\n"
                    f"Составь {lessons_count} последовательных уроков. Для КАЖДОГО урока пропиши полноценный план по структуре:\n"
                    f"<div style='page-break-after: always; break-after: page;'></div>\n\n"
                    f"### Урок № X. [Тема урока]\n"
                    f"1. **Цели урока:** (обучающая, развивающая, воспитательная).\n"
                    f"2. **Ключевые и предметные компетенции (по стандарту КР):** (КК-1, КК-2, ПК-1 и др.).\n"
                    f"3. **Оборудование и материалы.**\n"
                    f"4. **Ход урока:** (обязательно в виде подробной Markdown-таблицы):\n"
                    f"| Этап урока и время | Деятельность учителя | Деятельность ученика | Оценивание |\n\n"
                    f"Напиши качественный, развернутый материал для всех уроков без сокращений на русском языке."
                )
                
                package_result = generate_call(package_prompt)
                
                if package_result and not package_result.startswith("⚠️"):
                    full_combined_text = f"# Комплекс поурочных планов: {block_subject} — {section_name}\n\n" + package_result
                    st.session_state.last_result = full_combined_text
                    st.session_state.last_title = f"Поурочные_планы_{block_subject}_{section_name}"
                    st.success("✅ Пакет уроков успешно сгенерирован!")
                else:
                    st.error(package_result)

# Режим 3: Генерация по фото
elif work_mode == "📸 Генератор уроков по фото (Пакет до 4 уроков)":
    st.subheader("📸 Генерация поурочных планов по фотографии")
    st.markdown("Загрузите фото страницы учебника — программа создаст качественный пакет уроков.")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        photo_subject = st.text_input("Предмет:", placeholder="Например: Русская литература", key="pp_sub")
        photo_grade = st.selectbox("Класс:", ["5 класс", "6 класс", "7 класс", "8 класс", "9 класс", "10 класс", "11 класс"], key="pp_grade")
    with col_p2:
        photo_lessons_count = st.slider("Количество уроков:", min_value=2, max_value=4, value=3, step=1, key="pp_count")

    uploaded_files = st.file_uploader("Прикрепите фото страниц учебника", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="pp_files")

    if st.button("Запустить генерацию по фото", type="primary"):
        if not uploaded_files:
            st.warning("⚠️ Прикрепите хотя бы одну фотографию.")
        else:
            pil_images = [Image.open(f) for f in uploaded_files]
            with st.spinner("Анализирую фото и формирую комплекс уроков..."):
                photo_prompt = (
                    f"Ты — опытный методист в Кыргызстане. Используя прикрепленные фотографии страниц учебника по предмету '{photo_subject}' для {photo_grade}, "
                    f"составь комплекс из {photo_lessons_count} подробных поурочных планов.\n\n"
                    f"Для каждого урока сделай разрыв страницы (<div style='page-break-after: always; break-after: page;'></div>), "
                    f"укажи тему, цели, компетенции КР и большую подробную таблицу хода урока (Этап, Деятельность учителя, Деятельность ученика, Оценивание)."
                )
                
                photo_result = generate_call(photo_prompt, images=pil_images)
                
                if photo_result and not photo_result.startswith("⚠️"):
                    st.session_state.last_result = photo_result
                    st.session_state.last_title = f"Поурочные_планы_по_фото_{photo_subject}"
                    st.success("✅ Планы по фото успешно созданы!")
                else:
                    st.error(photo_result)

# Режим 4: Разбор ДЗ
else:
    st.subheader("🔍 Разбор ДЗ / Задач ученика")
    st.markdown("Разбор задач по шагам.")
    
    hw_subject = st.text_input("Предмет:", placeholder="Например: Алгебра / Физика")
    hw_questions_text = st.text_area("Список вопросов или заданий:", placeholder="1. Решить уравнение 2x + 5 = 15\n2. Найти площадь круга...")
    hw_files = st.file_uploader("Прикрепить фото с задачами", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="hw_files")

    if st.button("Запустить разбор задач", type="primary"):
        if not hw_questions_text.strip() and not hw_files:
            st.warning("⚠️ Введите текст заданий или прикрепите фотографии.")
        else:
            pil_images = [Image.open(f) for f in hw_files] if hw_files else None
            with st.spinner("Разбираю задачи..."):
                task_prompt = (
                    f"Ты — опытный учитель и репетитор по предмету '{hw_subject}'. "
                    f"Разбери указанные задачи: '{hw_questions_text}'. "
                    f"Для каждой задачи напиши условие, пошаговое решение с пояснениями и ответ."
                )
                
                solution_result = generate_call(task_prompt, images=pil_images)
                
                if solution_result and not solution_result.startswith("⚠️"):
                    st.session_state.last_result = solution_result
                    st.session_state.last_title = f"Разбор_ДЗ_{hw_subject}"
                    st.success("✅ Разбор готов!")
                else:
                    st.error(solution_result)

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
