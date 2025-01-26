from dotenv import load_dotenv
import streamlit as st
import os
import io
from PIL import Image
from ui import StreamlitUI
from config import initialize_services
from document_processor import DocumentProcessor
from qa_chain import QASystem
from quiz_generator import QuizGenerator

load_dotenv()

class DocumentAnalyzerApp:
    def __init__(self):
        self.ui = StreamlitUI()
        self.services = self._initialize_services()
        self.doc_processor = DocumentProcessor(self.services)
        self.qa_system = QASystem(self.services)
        self.quiz_gen = QuizGenerator()
        self._init_session_states()

    def _init_session_states(self):
        defaults = {
            'vector_store': None,
            'chat_history': {
                'document_analysis': [],
                'image_analysis': [],
                'quiz_generator': []
            },
            'quiz': {"quiz": None, "current_question": 0, "user_answers": []},
            'processed_files': set(),
            'summary_generated': False,
            'image_analysis': {"result": None, "type": None},
            'current_mode': 'Document Analysis'
        }
        for key, val in defaults.items():
            st.session_state.setdefault(key, val)

    def _initialize_services(self):
        try:
            return initialize_services()
        except Exception as e:
            st.error(f"Service initialization failed: {str(e)}")
            st.stop()

    def run(self):
        mode = self.ui.navigation()
        # Update current mode
        st.session_state.current_mode = mode
        
        {
            "Document Analysis": self._document_flow,
            "Quiz Generator": self._quiz_flow,
            "Image Analysis": self._image_flow
        }[mode]()

    def _document_flow(self):
        pdf_files = self.ui.document_analysis_ui()
        
        # Process documents if uploaded
        if pdf_files:
            self._process_docs(pdf_files)
            self._handle_summary()
        
        # Always show chat input, but handle responses only if documents are processed
        query = st.chat_input("Ask about your documents...")
        if query:
            if not st.session_state.vector_store:
                st.warning("⚠️ Please upload documents first to ask questions.")
            else:
                with self.ui.show_processing_status("Finding answer") as status:
                    try:
                        answer, source, links = self.qa_system.get_answer(
                            query, st.session_state.vector_store
                        )
                        st.session_state.chat_history['document_analysis'].append({
                            "question": query, 
                            "answer": answer,
                            "source": source,
                            "links": links
                        })
                        status.update(state="complete")
                    except Exception as e:
                        status.update(label="❌ Failed", state="error")
                        st.error(str(e))
        
        # Display chat history
        for entry in st.session_state.chat_history['document_analysis']:
            self.ui.display_chat_message(entry)

    def _process_docs(self, pdf_files):
        current_files = {f.name for f in pdf_files}
        if st.session_state.processed_files != current_files:
            with self.ui.show_processing_status("Analyzing documents") as status:
                try:
                    text = self.doc_processor.extract_text(pdf_files)
                    chunks = self.doc_processor.split_text(text)
                    st.session_state.vector_store = self.doc_processor.create_vector_store(
                        chunks, self.services['embeddings']
                    )
                    st.session_state.processed_files = current_files
                    status.update(label="✓ Documents processed", state="complete")
                except Exception as e:
                    status.update(label="❌ Processing failed", state="error")
                    st.error(str(e))

    def _handle_summary(self):
        if st.button("📝 Generate Summary"):
            st.session_state.summary_generated = True
        if st.session_state.summary_generated:
            with st.form("summary_form"):
                focus = self.ui.summary_input()
                if st.form_submit_button("Generate"):
                    with self.ui.show_processing_status("Generating summary") as status:
                        try:
                            summary, links = self.qa_system.generate_summary(
                                st.session_state.vector_store, focus
                            )
                            self.ui.display_summary(summary, links)
                            status.update(label="✓ Summary generated", state="complete")
                        except Exception as e:
                            status.update(label="❌ Failed", state="error")
                            st.error(str(e))

    def _image_flow(self):
        image_file, query, analysis_type = self.ui.image_analysis_ui()
        if image_file and st.button("Analyze"):
            with self.ui.show_processing_status("Processing image") as status:
                try:
                    # Read image bytes
                    image_bytes = image_file.getvalue()
                    
                    if analysis_type == "Image Captioning":
                        caption = self.qa_system.generate_image_caption(image_bytes, query)
                        st.session_state.image_analysis = {"result": caption, "type": "caption"}
                        
                        # Add to chat history
                        if query:
                            st.session_state.chat_history['image_analysis'].append({
                                "question": query,
                                "answer": caption,
                                "source": "image",
                                "links": []
                            })
                    else:
                        # Extract text using OCR
                        text = self.doc_processor.extract_image_text(image_bytes)
                        processed = self.qa_system.process_extracted_text(text, query)
                        st.session_state.image_analysis = {"result": processed, "type": "text"}
                        
                        # Add to chat history
                        if query:
                            st.session_state.chat_history['image_analysis'].append({
                                "question": query,
                                "answer": processed,
                                "source": "ocr",
                                "links": []
                            })
                            
                    status.update(label="✓ Analysis complete", state="complete")
                except Exception as e:
                    status.update(label="❌ Failed", state="error")
                    st.error(f"Image processing failed: {str(e)}")
        
        # Display analysis results
        if st.session_state.image_analysis["result"]:
            if st.session_state.image_analysis["type"] == "caption":
                self.ui.display_image_analysis(caption=st.session_state.image_analysis["result"], query=query)
            else:
                self.ui.display_image_analysis(text_response=st.session_state.image_analysis["result"], query=query)
            
            # Add clear button
            if st.button("Clear Results"):
                st.session_state.image_analysis = {"result": None, "type": None}
        
        # Display chat history for image analysis
        if st.session_state.chat_history['image_analysis']:
            st.markdown("### Previous Analyses")
            for entry in st.session_state.chat_history['image_analysis']:
                self.ui.display_chat_message(entry)

    def _quiz_flow(self):
        if uploaded_file := self.ui.quiz_generation_ui():
            if st.button("Generate Quiz"):
                with self.ui.show_processing_status("Generating quiz"):
                    try:
                        text = self.doc_processor.extract_text([uploaded_file])
                        quiz = self.quiz_gen.generate_quiz(text)
                        st.session_state.quiz.update({
                            "quiz": quiz,
                            "current_question": 0,
                            "user_answers": []
                        })
                    except Exception as e:
                        st.error(str(e))
        
        if st.session_state.quiz["quiz"]:
            self._handle_quiz()

    def _handle_quiz(self):
        current = st.session_state.quiz["current_question"]
        total = len(st.session_state.quiz["quiz"])
        
        if current < total:
            question = st.session_state.quiz["quiz"][current]
            st.markdown(f"**Question {current+1}/{total}**")
            selected = st.radio(question["question"], question["options"], index=None)
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Next ➡️", disabled=not selected):
                    st.session_state.quiz["user_answers"].append(selected)
                    st.session_state.quiz["current_question"] += 1
                    st.rerun()
            with col2:
                if current > 0 and st.button("⬅️ Previous"):
                    st.session_state.quiz["current_question"] -= 1
                    st.rerun()
        else:
            self._show_results()

    def _show_results(self):
        correct = sum(1 for ans, q in zip(st.session_state.quiz["user_answers"], 
                                       st.session_state.quiz["quiz"]) 
                    if ans == q["answer"])
        st.success(f"Score: {correct}/{len(st.session_state.quiz['quiz'])}")
        st.progress(correct/len(st.session_state.quiz["quiz"]))
        
        with st.expander("Review Answers"):
            for i, (ans, q) in enumerate(zip(st.session_state.quiz["user_answers"], 
                                           st.session_state.quiz["quiz"])):
                st.markdown(f"**Q{i+1}:** {q['question']}")
                st.markdown(f"✅ **Correct:** {q['options'][ord(q['answer'])-97]}")
                st.markdown(f"💡 **Your answer:** {ans if ans else 'None'}")
                st.divider()

if __name__ == "__main__":
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        st.error("Missing Google credentials! Check .env file")
        st.stop()
    
    DocumentAnalyzerApp().run()


























































