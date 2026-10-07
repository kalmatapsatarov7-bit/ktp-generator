import streamlit as st
from google import genai
from PIL import Image

# Настройка страницы
st.set_page_config(
    page_title="Помощник Учителя",
    page_icon="📚",
    layout="wide"  # Расширенная разметка, чтобы удобно разместить баннеры по бокам
)

# Заголовок приложения
st.title("📚 Помощник Учителя")
st.markdown("Интерактивный образовательный помощник: поурочные планы и разбор домашних заданий.")

# Боковая панель для настроек
with st.sidebar:
    st.header("⚙️ Настройки")
    
    # Поле для API-ключа
    API_KEY = st.text_input(
        "Введите Gemini API Key:",
        type="password",
        help="Получите ключ в Google AI Studio."
    )
    
    st.markdown("---")
    st.markdown("### О программе")
    st.markdown(
        "Инструмент создан для быстрой разработки поурочных планов "
        "и качественного разбора трудных вопросов с учениками."
    )

# Выбор режима работы
option = st.selectbox(
    "Выберите режим работы:",
    ["📝 Генератор Поурочного Плана", "💬 Консультация по ДЗ и объяснение"]
)

st.markdown("---")

# Расширенный список моделей (включая твои пожелания: iPad Flash, Jamie on iPad Latest, Jamie Latest, Jamie Latest Flash и др.)
MODELS_TO_TRY = [
    "jamie-latest-flash",
    "ipad-flash",
    "jamie-on-ipad-latest",
    "jamie-latest",
    "gemini-2.5-flash",
    "gemini-2.5-flash-latest",
    "gemini-2.0-flash",
    "gemini-2.0-flash-latest",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.5-pro"
]

def generate_with_fallback(client, contents):
    """Функция автоматического перебора моделей на случай перегрузки"""
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
            if "429" in err_str or "ResourceExhausted" in err_str or "503" in err_str or "NotFound" in err_str:
                continue
            else:
                continue
    return None

# ==========================================
# РАЗМЕЩЕНИЕ С РЕКЛАМНЫМИ БАННЕРАМИ (Слева, Центр, Справа)
# ==========================================
col_left, col_center, col_right = st.columns([1, 4, 1])

# Левый рекламный баннер
with col_left:
    st.markdown("---")
    st.markdown("### 📢 Реклама")
    st.markdown(
        "<div style='border: 2px dashed #ccc; padding: 15px; text-align: center; border-radius: 10px; color: gray;'>"
        "<b>Место для левого баннера</b><br><br>Ваша реклама здесь"
        "</div>", 
        unsafe_allow_html=True
    )
    st.markdown("---")

# Центральная рабочая область приложения
with col_center:
    # РЕЖИМ 1: Генератор Поурочного Плана
    if option == "📝 Генератор Поурочного Плана":
        st.subheader("📝 Создание Поурочного Плана")

        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            lesson_subject = st.text_input("Предмет:", placeholder="Например: Литература")
            lesson_grade = st.selectbox("Класс:", ["5 класс", "6 класс", "7 класс", "8 класс", "9 класс", "10 класс", "11 класс"])
        with sub_col2:
            lesson_duration = st.selectbox("Длительность урока:", ["45 минут", "90 минут (пара)"])

        lesson_topic = st.text_input("Тема урока:", placeholder="Например: И.С. Тургенев, рассказ «Муму»")
        lesson_goals = st.text_area(
            "Цели обучения (если есть конкретные):",
            placeholder="Например: Понять образ главного героя, развивать навыки анализа текста..."
        )

        lesson_submitted = st.button("Сгенерировать поурочный план", type="primary")

        if lesson_submitted:
            if not lesson_subject.strip() or not lesson_topic.strip():
                st.warning("Пожалуйста, укажите предмет и тему урока.")
            elif not API_KEY:
                st.error("Пожалуйста, укажите API-ключ Gemini в боковой панели слева.")
            else:
                with st.spinner("Разрабатываю поурочный план..."):
                    try:
                        client = genai.Client(api_key=API_KEY)
                        prompt = (
                            f"Ты — высококвалифицированный педагог. Напиши подробный конспект-план "
                            f"урока по предмету '{lesson_subject}' для {lesson_grade} продолжительностью {lesson_duration}. "
                            f"Тема урока: '{lesson_topic}'. "
                            f"Дополнительные цели: {lesson_goals}. "
                            f"Структура плана должна включать: "
                            f"1. Организационный момент и мотивация. "
                            f"2. Актуализация знаний. "
                            f"3. Изучение нового материала (с вопросами для класса). "
                            f"4. Этап закрепления и практики. "
                            f"5. Рефлексия и домашнее задание."
                        )

                        result_text = generate_with_fallback(client, prompt)

                        if result_text:
                            st.success("Поурочный план готов!")
                            st.markdown("---")
                            st.markdown(result_text)
                        else:
                            st.error("⚠️ Все доступные модели перегружены или недоступны. Попробуйте еще раз через минуту.")

                    except Exception as e:
                        st.error(f"Произошла ошибка: {e}")

    # РЕЖИМ 2: Консультация по ДЗ
    else:
        st.subheader("💬 Консультация по ДЗ и объяснение материала")
        
        hw_subject = st.text_input("Предмет:", placeholder="Например: Физика или Математика")
        hw_question = st.text_area("Текст задания или вопрос ученика:", placeholder="Вставьте текст упражнения или опишите вопрос...")
        hw_file = st.file_uploader("Прикрепить фото задания (необязательно):", type=["png", "jpg", "jpeg"])

        hw_submitted = st.button("Получить объяснение", type="primary")

        if hw_submitted:
            if not hw_question.strip() and not hw_file:
                st.warning("Пожалуйста, напишите текст задания или прикрепите фотографию.")
            elif not API_KEY:
                st.error("Пожалуйста, укажите API-ключ Gemini в боковой панели слева.")
            else:
                with st.spinner("Думаю над объяснением..."):
                    try:
                        client = genai.Client(api_key=API_KEY)
                        hw_prompt = (
                            f"Ты — дружелюбный, терпеливый и мудрый учитель, который помогает "
                            f"школьнику разобраться с домашним заданием по предмету "
                            f"'{hw_subject}'. Объясни материал максимально понятно, "
                            f"доступно, с примерами и пошаговым разбором. Не просто дай "
                            f"готовый ответ, а объясни ученику почему и как это "
                            f"работает, чтобы он понял суть."
                        )

                        contents = [hw_prompt]
                        if hw_question.strip():
                            contents.append(f"Задание/Вопрос ученика: {hw_question}")
                        if hw_file is not None:
                            hw_img = Image.open(hw_file)
                            contents.append(hw_img)

                        result_text = generate_with_fallback(client, contents)

                        if result_text:
                            st.success("Разбор готов!")
                            st.markdown("---")
                            st.markdown(result_text)
                        else:
                            st.error(
                                "⚠️ Все доступные модели сейчас перегружены высоким спросом. "
                                "Пожалуйста, подождите минутку и нажмите кнопку ещё раз."
                            )

                    except Exception as e:
                        st.error(f"Произошла ошибка: {e}")

# Правый рекламный баннер
with col_right:
    st.markdown("---")
    st.markdown("### 📢 Реклама")
    st.markdown(
        "<div style='border: 2px dashed #ccc; padding: 15px; text-align: center; border-radius: 10px; color: gray;'>"
        "<b>Место для правого баннера</b><br><br>Ваша реклама здесь"
        "</div>", 
        unsafe_allow_html=True
    )
    st.markdown("---")

# ==========================================
# НИЖНИЙ РЕКЛАМНЫЙ БАННЕР
# ==========================================
st.markdown("---")
st.markdown(
    "<div style='border: 2px dashed #ccc; padding: 20px; text-align: center; border-radius: 10px; color: gray; background-color: #fafafa;'>"
    "<b>📢 Рекламный блок внизу страницы</b> — Отличное место для размещения партнерских ссылок или баннера для монетизации проекта."
    "</div>", 
    unsafe_allow_html=True
)
