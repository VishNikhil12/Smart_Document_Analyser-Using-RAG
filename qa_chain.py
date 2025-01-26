from langchain.chains.question_answering import load_qa_chain
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from typing import Tuple, List, Dict
import logging

logger = logging.getLogger(__name__)

class QASystem:
    def __init__(self, services):
        self.services = services
        self.search = services['search']
        self.embeddings = services['embeddings']
        self.youtube = services.get('youtube')
        
    def get_answer(self, query: str, vector_store) -> Tuple[str, str, List[Dict]]:
        """Hybrid QA with YouTube and web resources"""
        try:
            # Get relevant document chunks
            docs_with_scores = vector_store.similarity_search_with_score(query, k=5)
            
            # Get YouTube and web resources
            yt_links = self._get_youtube_links(query)
            web_links = self._get_web_links(query)
            
            # Combine all resources
            all_links = self._combine_links(yt_links, web_links)
            
            # Generate answer with references
            answer = self._generate_answer_with_references(query, docs_with_scores, all_links)
            return answer, "combined", all_links
        except Exception as e:
            return f"Error processing query: {str(e)}", "error", []
        
    def _get_youtube_links(self, query: str) -> List[Dict]:
        """Search YouTube using API"""
        try:
            if not self.youtube:
                return []
                
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=3,
                type='video',
                relevanceLanguage='en',
                videoEmbeddable='true'
            ).execute()
            
            return [{
                'type': 'youtube',
                'title': item['snippet']['title'],
                'url': f"https://youtu.be/{item['id']['videoId']}",
                'description': item['snippet']['description'][:200] + '...',
                'thumbnail': item['snippet']['thumbnails']['default']['url']
            } for item in search_response.get('items', [])]
            
        except Exception as e:
            logger.error(f"YouTube search failed: {str(e)}")
            return []
        
    def _get_web_links(self, query: str) -> List[Dict]:
        """Get web search results"""
        try:
            if not self.search:
                return []
                
            results = self.search.results(query, 3)
            return [{
                'type': 'web',
                'title': res['title'],
                'url': res['link'],
                'description': res['snippet'][:200] + '...'
            } for res in results]
            
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return []

    def generate_summary(self, vector_store, focus: str = None) -> Tuple[str, List[Dict]]:
        """Generate summary with resource links"""
        try:
            query = focus or "Provide comprehensive summary of key points"
            docs = vector_store.similarity_search(query, k=7)
            context = "\n".join([doc.page_content for doc in docs][:3])
            
            summary_chain = load_summarize_chain(
                ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.2),
                chain_type="map_reduce",
                combine_prompt=self._summary_prompt(),
                verbose=False
            )
            summary = summary_chain.run(docs)
            
            # Generate contextual links
            links = self._generate_contextual_links(summary, context)
            return summary, links
            
        except Exception as e:
            return f"Summary generation failed: {str(e)}", []

    def _generate_contextual_links(self, query: str, context: str) -> List[Dict]:
        try:
            search_query = f"{query} {context[:500]}".strip()
            # Use the search wrapper's built-in results method
            results = self.search.results(search_query, 5)
            
            curated_links = []
            for res in results:
                link_type = "youtube" if "youtube.com" in res['link'] else "web"
                curated_links.append({
                    'type': link_type,
                    'title': res['title'],
                    'url': res['link'],
                    'snippet': res['snippet'][:150] + '...'
                })
            
            return sorted(curated_links, 
                key=lambda x: x['type'] == 'youtube', 
                reverse=True
            )[:3]
            
        except Exception as e:
          return []

    def _web_search(self, query: str) -> Tuple[str, List[Dict]]:
        """Enhanced web search with link aggregation"""
        try:
            results = self.search.results(query, 3)
            docs = [Document(page_content=res['snippet']) for res in results]
            links = [{
                'type': "youtube" if "youtube.com" in res['link'] else "web",
                'title': res['title'],
                'url': res['link'],
                'snippet': res['snippet']
            } for res in results]
            
            chain = load_qa_chain(
                ChatGoogleGenerativeAI(model="gemini-pro"),
                prompt=self._web_prompt()
            )
            answer = chain.run({"input_documents": docs, "question": query})
            return answer, links
            
        except Exception as e:
            return f"Web search failed: {str(e)}", []
        
    def _combine_links(self, yt_links: List[Dict], web_links: List[Dict]) -> List[Dict]:
        """Combine and prioritize relevant links"""
        # Prioritize YouTube links if query seems to ask for video content
        combined = yt_links + web_links
        return sorted(combined, key=lambda x: x['type'] == 'youtube', reverse=True)[:5]

    def _generate_answer_with_references(self, query: str, docs, links: List[Dict]) -> str:
        """Generate answer with embedded references"""
        try:
            # Format document context
            context = "\n".join([doc[0].page_content for doc in docs[:2]])
            
            # Format resource links
            resource_section = ""
            if links:
                resource_section = "\n\n🔗 Relevant Resources:\n"
                for i, link in enumerate(links, 1):
                    icon = "🎥" if link['type'] == 'youtube' else "🌐"
                    resource_section += f"{i}. {icon} [{link['title']}]({link['url']})\n"
            
            prompt = f"""Based on the following context and resources, provide a comprehensive answer to the question.
            Include relevant citations and links where appropriate.

            Question: {query}

            Context:
            {context}

            {resource_section}

            Please provide a detailed answer that:
            1. Directly addresses the question
            2. References the context when relevant
            3. Suggests relevant resources for further reading
            4. Uses markdown formatting for better readability
            """
            
            model = self.services['gemini']
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Answer generation failed: {str(e)}")
            return f"Failed to generate answer: {str(e)}"

    # Prompt templates remain the same as previous
    def _qa_prompt(self):
        return PromptTemplate.from_template("""
        Context Information:
        {context}
        
        User Question: {question}
        
        Provide detailed, evidence-based answer. Include markdown formatting when appropriate:
        """)

    def _summary_prompt(self):
        return PromptTemplate.from_template("""
        Synthesize key information from these documents:
        {text}
        
        Include in summary:
        - Core concepts and themes
        - Critical details and data points
        - Technical terminology explanations
        - Conclusions and implications
        
        Structured Summary (use markdown headings):
        """)

    def _web_prompt(self):
        return PromptTemplate.from_template("""
        Integrate information from these web results:
        {context}
        
        Original Query: {question}
        
        Generate comprehensive answer with source citations:
        """)
        
    def generate_image_caption(self, image_bytes, prompt=None):
        """Generate image captions using Gemini 1.5 Flash"""
        try:
            model = self.services['gemini']
            base_prompt = """Analyze this image and generate detailed caption covering:
            1. Main subjects and their relationships
            2. Contextual environment
            3. Visual composition
            4. Atmosphere/tone"""

            # Create a list of content parts
            content = [prompt or base_prompt]
            
            # Add image bytes as content
            content.append({
                "mime_type": "image/jpeg",
                "data": image_bytes
            })

            response = model.generate_content(
                contents=content,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1024
                }
            )
            
            if response.text:
                return response.text
            return "No caption could be generated"
            
        except Exception as e:
            return f"Caption error: {str(e)}"
        
        
    def process_extracted_text(self, text, query=None):
        """Analyze extracted text with optional user query"""
        try:
            if not query:
                return text
                
            model = self.services['gemini']
            prompt = f"""Extracted Text:
            {text}
            
            User Instruction: {query}
            
            Generate comprehensive response:"""
            
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Text analysis failed: {str(e)}"























# from langchain.chains.question_answering import load_qa_chain
# from langchain.chains.summarize import load_summarize_chain
# from langchain.prompts import PromptTemplate
# from langchain.schema import Document
# from langchain_google_genai import ChatGoogleGenerativeAI
# import io
# from PIL import Image
# import google.generativeai as genai

# class QASystem:
#     def __init__(self, services):
#         self.services = services
#         self.embeddings = services['embeddings']
#         self.search = services['search']
        
#     def get_answer(self, query, vector_store):
#         """Hybrid QA workflow with confidence threshold"""
#         try:
#             docs_with_scores = vector_store.similarity_search_with_score(query, k=5)
            
#             # Use web search if document relevance is low
#             if docs_with_scores and max(score for _, score in docs_with_scores) < 0.5:
#                 return self._web_search(query), "web"
            
#             docs = [doc for doc, _ in docs_with_scores]
            
#             chain = load_qa_chain(
#                 ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3),
#                 prompt=self._qa_prompt()
#             )
#             return chain.run({"input_documents": docs, "question": query}), "pdf"
#         except Exception as e:
#             return f"QA processing failed: {str(e)}", "error"

#     def generate_summary(self, vector_store, focus=None):
#         """Context-aware document summarization"""
#         try:
#             query = focus or "Provide comprehensive summary of key points"
#             docs = vector_store.similarity_search(query, k=7)
            
#             summary_chain = load_summarize_chain(
#                 ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.2),
#                 chain_type="map_reduce",
#                 combine_prompt=self._summary_prompt(),
#                 verbose=False
#             )
#             return summary_chain.run(docs)
#         except Exception as e:
#             return f"Summary generation failed: {str(e)}"

#     def generate_image_caption(self, image, prompt=None):
#         """Generate image captions using Gemini 1.5 Flash"""
#         try:
#             model = self.services['gemini']  # Should be initialized as gemini-1.5-flash
#             base_prompt = """Analyze this image and generate detailed caption covering:
#             1. Main subjects and their relationships
#             2. Contextual environment
#             3. Visual composition
#             4. Atmosphere/tone"""
            
#             response = model.generate_content(
#                 contents=[
#                     prompt or base_prompt,
#                     image  # Direct PIL Image input
#                 ],
#                 generation_config={
#                     "temperature": 0.4,
#                     "max_output_tokens": 512
#                 }
#             )
            
#             # Proper response handling for Gemini 1.5
#             if response.candidates and len(response.candidates) > 0:
#                 if (parts := response.candidates[0].content.parts):
#                     return parts[0].text
#             return "No caption could be generated"
            
#         except Exception as e:
#             return f"Caption error: {str(e)}"

#     def process_extracted_text(self, text, query=None):
#         """Analyze extracted text with optional user query"""
#         try:
#             if not query:
#                 return text  # Return raw text if no query provided
                
#             model = self.services['gemini']
#             prompt = f"""Extracted Text:
#             {text}
            
#             User Instruction: {query}
            
#             Generate comprehensive response:"""
            
#             response = model.generate_content(prompt)
#             return response.text
#         except Exception as e:
#             return f"Text analysis failed: {str(e)}"

#     def _web_search(self, query):
#         """Fallback to web search results"""
#         try:
#             results = self.search.results(query, 3)
#             docs = [Document(page_content=res['snippet']) for res in results]
            
#             chain = load_qa_chain(
#                 ChatGoogleGenerativeAI(model="gemini-pro"),
#                 prompt=self._web_prompt()
#             )
#             return chain.run({"input_documents": docs, "question": query})
#         except Exception as e:
#             return f"Web search failed: {str(e)}"

#     def _qa_prompt(self):
#         return PromptTemplate.from_template(
#             """Context Information:
#             {context}
            
#             User Question: {question}
            
#             Provide detailed, evidence-based answer:"""
#         )

#     def _summary_prompt(self):
#         return PromptTemplate.from_template(
#             """Synthesize key information from these documents:
#             {text}
            
#             Include in summary:
#             - Core concepts and themes
#             - Critical details and data points
#             - Technical terminology explanations
#             - Conclusions and implications
            
#             Structured Summary:"""
#         )

#     def _web_prompt(self):
#         return PromptTemplate.from_template(
#             """Integrate information from these web results:
#             {context}
            
#             Original Query: {question}
            
#             Generate comprehensive answer:"""
#         )




































