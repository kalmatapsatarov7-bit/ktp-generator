import time
import io
import streamlit as st
from PIL import Image
import google.generativeai as genai
from docx import Document

# Настройка API-ключа из Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="Генератор поурочных планов", layout="centered")

st.title("📚 Генератор поурочных планов по КТП")
st.write("Загрузите фотографии вашего календарно-тематического плана, и ИИ сформирует поурочные разработки.")

uploaded_files = st.file_uploader(
    "Загрузите фото КТП (одно или несколько)", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("🚀 Сформировать поурочные планы", type="primary"):
        
        # Блок всплывающего окна с таймером
        ad_modal = st.empty()
        
        for remaining in range(10, -1, -1):
            with ad_modal.container():
                st.info(f"⏳ Идёт подготовка нейросети... Пожалуйста, подождите {remaining} сек.")
                st.markdown("---")
                st.markdown("📢 Рекламная пауза / Полезное объявление:")
                st.caption("Подписывайтесь на наши образовательные каналы и делитесь сервисом с коллегами-учителями!")
                st.markdown("---")
            time.sleep(1)
        
        ad_modal.empty() # Убираем окно после отсчета

        # Основной процесс генерации
        with st.spinner("🧠 Анализируем КТП и составляем поурочные планы..."):
            try:
                images = [Image.open(f) for f in uploaded_files]
                model = genai.GenerativeModel('gemini-1.5-flash')

                prompt = """
                Ты — опытный методист школьного образования Кыргызской Республики.
                Проанализируй представленные фотографии КТП (календарно-тематического плана).
                Найди ВСЕ темы уроков и состави для каждой из них подробный поурочный план.
                
                Структура каждого плана:
                1. Тема урока, класс, предмет.
                2. Цели урока (обучающая, развивающая, воспитательная).
                3. Ход урока (Орг. момент, Повторение, Новая тема, Закрепление, Итоги, Д/З).
                4. Критерии оценивания.
                
                Выдай результат четко, красиво и структурировано.
                """

                response = model.generate_content([prompt] + images)
                plan_text = response.text

                st.success("🎉 Поурочные планы успешно сгенерированы!")
                st.markdown("### 📋 Результат:")
                st.write(plan_text)

                # Создание Word-документа (.docx) для скачивания
                doc = Document()
                doc.add_heading("Поурочные планы по КТП", 0)
                
                for paragraph in plan_text.split("\n"):
                    doc.add_paragraph(paragraph)
                
                doc_io = io.BytesIO()
                doc.save(doc_io)
                doc_io.seek(0)

                st.download_button(
                    label="📥 Скачать поурочные планы в Word (.docx)",
                    data=doc_io,
                    file_name="Поурочные_планы_КТП.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            except Exception as e:
                st.error(f"❌ Произошла ошибка при обработке: {e}")
