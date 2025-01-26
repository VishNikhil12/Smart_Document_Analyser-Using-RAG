# 🤖 Smart Document Analyzer

A powerful document analysis tool that combines the capabilities of Google's AI services to provide intelligent document processing, image analysis, and interactive quiz generation.


## ✨ Features

### 📑 Document Analysis
- **Smart Text Processing**: Extract and analyze text from PDF documents
- **Intelligent Q&A**: Ask questions about your documents and get contextual answers
- **Resource Integration**: Automatically fetches relevant web and YouTube resources
- **Dynamic Summarization**: Generate focused summaries of your documents

### 🖼️ Image Analysis
- **OCR Capabilities**: Extract text from images using Google Cloud Vision
- **Smart Captioning**: Generate detailed image descriptions
- **Visual Analysis**: Analyze image content, objects, and composition
- **Interactive Queries**: Ask questions about image content

### 🎯 Quiz Generation
- **Automatic Quiz Creation**: Generate quizzes from PDF content
- **Interactive Interface**: User-friendly quiz taking experience
- **Progress Tracking**: Track scores and review answers
- **Customizable Difficulty**: Adapt to different knowledge levels

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Google Cloud Platform Account
- Required API Keys:
  - Google API Key
  - YouTube API Key
  - Google Custom Search Engine ID
  - Google Cloud Vision API Credentials

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/smart-document-analyzer.git
cd smart-document-analyzer
```

2. Create and activate a virtual environment:
```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```env
GOOGLE_API_KEY=your_api_key
YOUTUBE_API_KEY=your_youtube_key
GOOGLE_CSE_ID=your_search_engine_id
GOOGLE_APPLICATION_CREDENTIALS=path_to_service_account.json
```

### Running the Application

```bash
streamlit run main.py
```



## 💡 Usage Examples

### Document Analysis Mode
![Document Analysis Mode](assets\document_analysis.png)
- Upload PDFs and interact with their content through natural language questions
- Get intelligent answers with relevant web and YouTube resources
- Generate comprehensive summaries of your documents

### Image Analysis Mode
![Image Analysis Mode](assets\Image_analysis.png)
- Extract text from images with advanced OCR
- Generate detailed captions and analyze visual content
- Ask specific questions about the image contents

### Quiz Generation Mode
![Quiz Generation Mode](assets\quiz_generator.png)
- Transform PDF content into interactive quizzes
- Track your progress and review your answers
- Learn through engaging question-answer format

## 🔒 Security

- All API keys and credentials are managed securely through environment variables
- Service account authentication for Google Cloud services
- Safe handling of user data and uploaded files



## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

