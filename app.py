if uploaded_files:
    if st.button("🚀 Сформировать поурочные планы на все темы с КТП", type="primary"):
        
        # Контейнер для всплывающего окна
        ad_modal = st.empty()
        
        # Переменная состояния для отслеживания закрытия учителем
        if "ad_closed" not in st.session_state:
            st.session_state.ad_closed = False

        try:
            images = [Image.open(f) for f in uploaded_files]
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = """
            Ты — опытный методист школьного образования КР.
            Проанализируй фото КТП и найди ВСЕ темы уроков.
            Составь для каждой темы поурочный план и верни STRICTLY JSON-массив.
            """
            
            response = None
            
            # Цикл на 10 секунд
            for remaining in range(10, -1, -1):
                # Если учитель уже нажал крестик — больше не показываем баннер
                if not st.session_state.get("close_ad_clicked", False):
                    with ad_modal.container():
                        
                        # Если 10 секунд прошло — показываем активную кнопку/крестик
                        if remaining == 0:
                            top_bar_html = """
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <span style="font-size: 12px; color: #856404; font-weight: bold;">Рекламная пауза</span>
                                <span style="color: #28a745; font-weight: bold; font-size: 13px;">✅ Можно закрыть</span>
                            </div>
                            """
                        else:
                            top_bar_html = f"""
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <span style="font-size: 12px; color: #856404; font-weight: bold;">Рекламная пауза</span>
                                <span style="color: #6c757d; font-size: 12px;">Закрытие через {remaining} сек...</span>
                            </div>
                            """
                        
                        st.markdown(
                            f"""
                            <div style="background-color: #fff3cd; border: 2px solid #ffc107; padding: 15px 20px; border-radius: 12px; text-align: center; margin: 15px 0; position: relative;">
                                {top_bar_html}
                                <h4 style="color: #856404; margin: 5px 0 10px 0;">⏳ Идет обработка КТП и составление уроков...</h4>
                                <hr style="border-top: 1px dashed #ffc107; margin: 10px 0;">
                                <a href="https://example.com" target="_blank" style="font-size: 17px; font-weight: bold; color: #0d6efd; text-decoration: none;">
                                    📢 Специальное предложение: Комплект методических материалов для учителей!
                                </a>
                                <p style="font-size: 11px; color: #6c757d; margin-top: 6px; margin-bottom: 0;">
                                    Нажмите на ссылку, чтобы открыть в новой вкладке
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Появление кнопки «Закрыть ✖» ровно через 10 секунд
                        if remaining == 0:
                            if st.button("✖ Закрыть рекламу", key="btn_close_ad"):
                                st.session_state.close_ad_clicked = True
                                ad_modal.empty()# Запускаем генерацию Gemini в самом начале цикла
                if response is None:
                    response = model.generate_content([prompt, *images])
                
                time.sleep(1)
            
            # Парсинг и сборка Word-файла
            clean_json = response.text.replace("`json", "").replace("```", "").strip()
            lessons_data = json.loads(clean_json)
            docx_file = create_multi_lesson_docx(lessons_data)
            
            # Автоматически полностью очищаем баннер после завершения работы
            ad_modal.empty()
            st.session_state.close_ad_clicked = False
            
            st.success(f"✨ Готово! Успешно сформировано планов уроков: {len(lessons_data)}")
            st.download_button(
                label="📥 Скачать все поурочные планы в одном Word (.docx)",
                data=docx_file,
                file_name="Комплект_поурочных_планов.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary"
            )
            
        except Exception as e:
            ad_modal.empty()
            st.error(f"Произошла ошибка при обработке: {e}")
