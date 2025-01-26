import streamlit as st
from typing import List, Dict, Optional
from urllib.parse import urlparse, urlunparse, quote

class StreamlitUI:
    def __init__(self):
        self._set_page_config()
        self._set_css()

    def _set_page_config(self):
        st.set_page_config(
            page_title="Smart Document Analyzer",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def _set_css(self):
        st.markdown("""
        <style>
            .analysis-box {
                padding: 1.5rem;
                border-radius: 10px;
                margin: 1rem 0;
                border: 2px solid #4CAF50;
                background-color: #ffffff;
            }
            .resource-card {
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 8px;
                background: #ffffff;
                border: 1px solid #dee2e6;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .youtube-card {
                border-left: 4px solid #ff0000;
            }
            .web-card {
                border-left: 4px solid #2E86C1;
            }
            .analysis-header {
                color: #2E7D32;
                font-size: 1.3rem;
                margin-bottom: 1rem;
                font-weight: bold;
            }
            .text-response {
                background-color: #ffffff;
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
                border: 1px solid #e0e0e0;
                color: #333333;
                font-size: 1.1rem;
                line-height: 1.6;
            }
            .chat-message {
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 8px;
                background: #ffffff;
                border: 1px solid #e0e0e0;
                color: #333333;
            }
            .stTextInput > div > div > input {
                color: #333333;
                font-size: 1.1rem;
            }
            .stTextArea > div > div > textarea {
                color: #333333;
                font-size: 1.1rem;
            }
        </style>
        """, unsafe_allow_html=True)

    def navigation(self):
        st.sidebar.title("Navigation")
        return st.sidebar.radio(
            "Select Mode",
            ["Document Analysis", "Quiz Generator", "Image Analysis"],
            index=0
        )

    def document_analysis_ui(self):
        st.title("📑 Smart Document Analyzer")
        
        # File uploader in a clean container
        with st.container():
            st.markdown("### Upload Documents")
            files = st.file_uploader(
                "Choose PDF files",
                type=["pdf"],
                accept_multiple_files=True,
                key="doc_upload"
            )
            return files

    def quiz_generation_ui(self):
        st.title("🎯 PDF Quiz Generator")
        with st.expander("Upload Quiz Document", expanded=True):
            return st.file_uploader(
                "Choose a PDF file", 
                type=["pdf"]
            )

    def image_analysis_ui(self):
        st.title("🖼️ Image Analysis")
        with st.container():
            col1, col2 = st.columns([2, 3])
            with col1:
                image_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "webp"])
                analysis_type = st.radio("Analysis Mode:", ["Text Extraction", "Image Captioning"])
            with col2:
                user_query = st.text_area("Your Question/Instructions:", height=150)
            return image_file, user_query, analysis_type

    def show_processing_status(self, message):
        return st.status(f"{message}...", expanded=True)

    def summary_input(self):
        return st.text_input("Summary Focus Area:", placeholder="Leave blank for general summary")

    def display_summary(self, summary: str, links: List[Dict]):
        with st.container():
            st.markdown("""<div class="analysis-box"><div class="analysis-header">📝 Document Summary</div>""", 
                      unsafe_allow_html=True)
            st.markdown(summary)
            if links:
                st.subheader("🔗 Recommended Resources")
                self._display_links(links)
            st.markdown("</div>", unsafe_allow_html=True)

    def _display_links(self, links: List[Dict]):
        for link in links:
            card_class = "youtube-card" if link['type'] == 'youtube' else 'web-card'
            st.markdown(f"""
            <div class="resource-card {card_class}">
                <b>{link['title']}</b><br>
                <small>{link['url']}</small>
                <p style="color: #666;">{link.get('snippet', '')}</p>
            </div>
            """, unsafe_allow_html=True)

    def display_chat_message(self, entry: Dict):
        with st.chat_message("user"):
            st.markdown(entry["question"])
        with st.chat_message("assistant"):
            st.markdown(entry["answer"])
            self._source_badge(entry["source"], entry.get("links", []))
            self._display_resource_links(entry.get("links", []))

    def _source_badge(self, source: str, links: List[Dict]):
        badge_color = "#2E86C1" if source == "pdf" else "#27AE60"
        st.markdown(f'<div style="display: inline-block; padding: 0.25rem 0.75rem; margin: 0.5rem 0; border-radius: 15px; background-color: {badge_color}; color: white;">{source.upper()}</div>', 
                   unsafe_allow_html=True)
        if links:
            with st.expander("🌐 Relevant Resources"):
                self._display_links(links)

    def _display_resource_links(self, links: List[Dict]):
        with st.expander("📚 View Recommended Resources", expanded=False):
            for link in links:
                self._display_single_link(link)

    def _display_single_link(self, link: Dict):
        try:
            icon = "🎥" if link['type'] == 'youtube' else "🌐"
            source_type = "YouTube Video" if link['type'] == 'youtube' else "Web Article"
            encoded_url = self._validate_url(link['url'])
            
            st.markdown(f"""
            <div class="resource-card {'youtube-card' if link['type'] == 'youtube' else 'web-card'}">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <div style="font-size: 1.2rem;">{icon}</div>
                    <div><b>{source_type}</b></div>
                </div>
                <a href="{encoded_url}" target="_blank" rel="noopener noreferrer" 
                   style="color: inherit; text-decoration: none;">
                    <h4 style="margin: 0 0 8px 0;">{link['title']}</h4>
                </a>
                <p style="color: #666; margin: 0; font-size: 0.9em;">
                    {self._truncate_text(link.get('snippet', ''), 200)}
                </p>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error displaying resource: {str(e)}")

    def _validate_url(self, url: str) -> str:
        parsed = urlparse(url)
        safe_path = quote(parsed.path)
        return urlunparse((
            parsed.scheme or 'https',
            parsed.netloc,
            safe_path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))

    def _truncate_text(self, text: str, max_length: int) -> str:
        return text[:max_length-3] + '...' if len(text) > max_length else text
    
    
    def display_image_analysis(self, text_response: Optional[str] = None, 
                             caption: Optional[str] = None, 
                             query: Optional[str] = None):
        """Display image analysis results with optional query context"""
        with st.container():
            if text_response:
                st.markdown("""
                <div class="analysis-box">
                    <div class="analysis-header">📄 Analysis Results</div>
                    <div class="content">
                """, unsafe_allow_html=True)
                
                if query:
                    st.markdown(f"**Your Question:** {query}")
                    st.markdown("---")
                
                st.markdown("#### Extracted Text")
                st.markdown(f'<div class="text-response">{text_response}</div>', 
                          unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
            
            if caption:
                st.markdown("""
                <div class="analysis-box">
                    <div class="analysis-header">📷 Generated Caption</div>
                    <div class="content">
                """, unsafe_allow_html=True)
                
                if query:
                    st.markdown(f"**Your Instruction:** {query}")
                    st.markdown("---")
                
                st.markdown(caption)
                st.markdown("</div></div>", unsafe_allow_html=True)































# import streamlit as st

# class StreamlitUI:
#     def __init__(self):
#         self._set_page_config()
#         self._set_css()

#     def _set_page_config(self):
#         st.set_page_config(
#             page_title="Smart Document Analyzer",
#             page_icon="🤖",
#             layout="wide",
#             initial_sidebar_state="expanded"
#         )

#     def _set_css(self):
#         st.markdown("""
#         <style>
#             .analysis-box {
#                 padding: 1.5rem;
#                 border-radius: 10px;
#                 margin: 1rem 0;
#                 border: 2px solid #4CAF50;
#                 background-color: #f0f4f8;
#             }
#             .analysis-header {
#                 color: #2E7D32;
#                 font-size: 1.3rem;
#                 margin-bottom: 1rem;
#             }
#             .text-response {
#                 background-color: #fff3e0;
#                 padding: 1rem;
#                 border-radius: 8px;
#                 margin: 1rem 0;
#             }
#             .status-box {
#                 padding: 1rem;
#                 border-radius: 0.5rem;
#                 margin: 1rem 0;
#                 background-color: #f8f9fa;
#                 border: 1px solid #dee2e6;
#             }
#             @keyframes fadeIn {
#                 from { opacity: 0; }
#                 to { opacity: 1; }
#             }
#         </style>
#         """, unsafe_allow_html=True)

#     def navigation(self):
#         st.sidebar.title("Navigation")
#         return st.sidebar.radio(
#             "Select Mode",
#             ["Document Analysis", "Quiz Generator", "Image Analysis"],
#             index=0,
#             key="nav_radio"
#         )

#     def document_analysis_ui(self):
#         st.title("📑 Smart Document Analyzer")
#         with st.expander("Upload Documents", expanded=True):
#             return st.file_uploader(
#                 "Choose PDF files", 
#                 type=["pdf"], 
#                 accept_multiple_files=True,
#                 key="doc_uploader",
#                 help="Upload one or multiple PDF documents for analysis"
#             )

#     def quiz_generation_ui(self):
#         st.title("🎯 PDF Quiz Generator")
#         with st.expander("Upload Quiz Document", expanded=True):
#             return st.file_uploader(
#                 "Choose a PDF file", 
#                 type=["pdf"],
#                 key="quiz_uploader",
#                 help="Upload a single PDF document to generate quiz questions"
#             )

#     def image_analysis_ui(self):
#         st.title("🖼️ Image Analysis")
#         with st.container():
#             col1, col2 = st.columns([2, 3])
            
#             with col1:
#                 image_file = st.file_uploader(
#                     "Upload Image",
#                     type=["png", "jpg", "jpeg", "webp"],
#                     key="image_uploader",
#                     help="Upload any image for analysis"
#                 )
#                 analysis_type = st.radio(
#                     "Analysis Mode:",
#                     ["Text Extraction", "Image Captioning"],
#                     index=0,
#                     key="analysis_mode"
#                 )
                
#             with col2:
#                 user_query = st.text_area(
#                     "Your Question/Instructions:",
#                     placeholder="What would you like to know about this image?",
#                     height=150,
#                     key="image_query"
#                 )
            
#             return image_file, user_query, analysis_type

#     def show_processing_status(self, message):
#         return st.status(f"{message}...", expanded=True)

#     def summary_input(self):
#         return st.text_input(
#             "Summary Focus Area:",
#             placeholder="Leave blank for general summary",
#             key="summary_focus"
#         )

#     def display_summary(self, summary):
#         with st.container():
#             st.markdown("""
#             <div class="analysis-box">
#                 <div class="analysis-header">📝 Document Summary</div>
#                 <div class="content">
#             """, unsafe_allow_html=True)
#             st.markdown(summary)
#             st.markdown("</div></div>", unsafe_allow_html=True)

#     def display_quiz(self, quiz_state):
#         total = len(quiz_state["quiz"])
#         current = quiz_state["current_question"]
        
#         if current < total:
#             question = quiz_state["quiz"][current]
#             st.markdown(f"""
#             <div class="analysis-box">
#                 <h3>Question {current+1}/{total}</h3>
#                 <p><strong>{question['question']}</strong></p>
#             </div>
#             """, unsafe_allow_html=True)
            
#             return st.radio(
#                 "Select your answer:",
#                 question["options"],
#                 key=f"quiz_question_{current}",
#                 index=None
#             )
#         else:
#             self._show_quiz_results(quiz_state["user_answers"], total)
#             return None

#     def display_image_analysis(self, text_response=None, caption=None, query=None):
#         """Display image analysis results with optional query context"""
#         with st.container():
#             if text_response:
#                 st.markdown("""
#                 <div class="analysis-box">
#                     <div class="analysis-header">📄 Analysis Results</div>
#                     <div class="content">
#                 """, unsafe_allow_html=True)
                
#                 if query:
#                     st.markdown(f"**Your Question:** {query}")
#                     st.markdown("---")
                
#                 st.markdown("#### Extracted Text")
#                 st.code(text_response.get('raw_text'))
                
#                 if text_response.get('processed_response'):
#                     st.markdown("---")
#                     st.markdown("#### Generated Response")
#                     st.markdown(text_response['processed_response'])
                
#                 st.markdown("</div></div>", unsafe_allow_html=True)
            
#             if caption:
#                 st.markdown("""
#                 <div class="analysis-box">
#                     <div class="analysis-header">📷 Generated Caption</div>
#                     <div class="content">
#                 """, unsafe_allow_html=True)
                
#                 if query:
#                     st.markdown(f"**Your Instruction:** {query}")
#                     st.markdown("---")
                
#                 st.markdown(caption)
#                 st.markdown("</div></div>", unsafe_allow_html=True)

#     def _show_quiz_results(self, user_answers, total):
#         correct = sum(1 for ans in user_answers if ans["selected"] == ans["correct"])
#         st.success(f"🎉 Quiz Complete! Score: {correct}/{total}")
#         st.progress(correct / total)
        
#         with st.expander("📝 Review Answers", expanded=True):
#             for i, ans in enumerate(user_answers):
#                 st.markdown(f"**Question {i+1}**")
#                 st.markdown(f"✅ **Correct:** {ans['correct']}")
#                 st.markdown(f"💡 **Your answer:** {ans['selected']}")
#                 st.divider()

#     def _source_badge(self, source):
#         badge_color = "#2E86C1" if source == "pdf" else "#27AE60"
#         st.markdown(
#             f'<div style="display: inline-block; padding: 0.25rem 0.75rem; '
#             f'margin-top: 0.5rem; border-radius: 15px; '
#             f'background-color: {badge_color}; color: white; '
#             f'font-size: 0.8rem;">{source.upper()}</div>',
#             unsafe_allow_html=True
#         )


















