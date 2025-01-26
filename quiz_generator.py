from langchain.text_splitter import RecursiveCharacterTextSplitter
import time
import google.generativeai as genai

class QuizGenerator:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000,
            chunk_overlap=500
        )
        self.retry_delay = 5  # Seconds between retries
        self.max_retries = 3
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_quiz(self, pdf_text):
        """
        Generate a quiz from PDF text with error handling and retry logic.
        
        Args:
            pdf_text (str): Text extracted from PDF documents.
        
        Returns:
            list: List of structured quiz questions.
        
        Raises:
            RuntimeError: If quiz generation fails after retries.
        """
        try:
            # Split text into manageable chunks
            chunks = self.text_splitter.split_text(pdf_text)
            context = "\n".join(chunks[:3])  # Use first 3 chunks for context

            # Define quiz generation prompt
            prompt = f"""Generate 5 MCQ questions from this context:
            {context}
            
            Follow this EXACT format:
            
            Question 1: [question text]
            A) [option 1]
            B) [option 2]
            C) [option 3]
            D) [option 4]
            Answer: [letter]
            
            [Repeat for Questions 2-5]"""

            # Retry logic for rate limits
            for attempt in range(self.max_retries):
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.7,
                            "max_output_tokens": 800,
                        }
                    )
                    return self.parse_quiz(response.text)
                except Exception as e:
                    if "429" in str(e) and attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    raise

        except Exception as e:
            raise RuntimeError(f"Quiz generation failed: {str(e)}")

    def parse_quiz(self, response_text):
        """
        Parse the model's response into structured quiz questions.
        
        Args:
            response_text (str): Raw response text from the model.
        
        Returns:
            list: List of structured quiz questions.
        """
        questions = []
        current_q = {}
        
        # Split and clean response text
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        
        # Parse each line
        for line in lines:
            if line.lower().startswith("question"):
                if current_q:
                    questions.append(current_q)
                current_q = {"question": "", "options": [], "answer": ""}
                current_q["question"] = line.split(":", 1)[-1].strip()
            elif line.startswith(("A)", "B)", "C)", "D)")):
                current_q["options"].append(line[3:].strip())
            elif line.lower().startswith("answer:"):
                current_q["answer"] = line.split(":")[-1].strip().lower()[0]
        
        # Filter and return valid questions
        return [q for q in questions if self._is_valid_question(q)][:5]

    def _is_valid_question(self, question):
        """
        Validate the structure of a quiz question.
        
        Args:
            question (dict): Quiz question to validate.
        
        Returns:
            bool: True if the question is valid, False otherwise.
        """
        return (
            len(question.get("options", [])) == 4 and 
            question.get("answer") in ['a', 'b', 'c', 'd'] and 
            bool(question.get("question"))
        )