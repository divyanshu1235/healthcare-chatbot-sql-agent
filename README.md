# 🏥 Healthcare Data Assistant

A powerful AI-powered healthcare data analysis tool that combines SQL generation with conversational AI to help healthcare professionals and researchers query and understand medical data.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Gradio](https://img.shields.io/badge/Gradio-5.34.2-orange.svg)
![Together AI](https://img.shields.io/badge/Together%20AI-Mixtral%208x7B-purple.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- **🤖 Dual Mode Interface**: SQL Agent for direct queries and Chatbot for conversational interactions
- **🧠 Intelligent SQL Generation**: Converts natural language to SQL queries using Mixtral-8x7B-Instruct
- **💬 Conversational Memory**: Maintains context across multiple interactions
- **📚 Medical Knowledge Integration**: Fetches medical definitions from Wikipedia
- **🏥 Healthcare-Focused**: Specifically designed for medical data analysis
- **📊 Rich Data Visualization**: Beautiful table formatting with pandas
- **🔗 Database Integration**: Works with SQLite databases containing healthcare data

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Together AI API key
- Healthcare dataset (CSV files)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/healthcare-data-assistant.git
   cd healthcare-data-assistant
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   echo "TOGETHER_API_KEY=your_api_key_here" > .env
   ```

5. **Prepare your data**
   ```bash
   # Place your CSV files in the dataset/ folder
   # Run the database creation script
   python create_health_db.py
   ```

6. **Launch the application**
   ```bash
   python python.py
   ```

The application will open in your browser at `http://127.0.0.1:7864`

## 📊 Database Schema

The application works with two main tables:

### DIAGNOSIS Table
- `Id` (integer): Primary key, unique identifier for each diagnosis event
- `CardNumber` (integer): Patient's card number
- `DiagnosisDate` (text): Date and time of diagnosis (DD/MM/YYYY HH:MM)
- `Diagnosis` (text): Diagnosis description

### HIS_LOGS Table
- `Id` (integer): Primary key, unique identifier for each log event
- `RefType` (text): Reference type (type of event)
- `DoctorId` (integer): Doctor's ID
- `RefDateTime` (text): Date and time of the event (DD/MM/YYYY HH:MM)
- `LocationName` (text): Name of the location
- `LocationAreaName` (text): Area within the location
- `CardNumber` (text): Patient's card number (may have leading zeros)

## 🎯 Usage Examples

### SQL Agent Mode
Ask questions to generate and execute SQL queries:

- "How many diagnoses are there?"
- "List all unique diagnoses"
- "Show all diagnoses for Id 10"
- "What are the top 5 most common diagnoses?"
- "How many patients had events in the ICU?"

### Chatbot Mode
Have natural conversations about your data:

- "What is CKD?" (includes medical definition)
- "How many patients had ICU events?"
- "What are the most common diagnoses?"
- "Tell me about diabetes cases"

## 🛠️ Technology Stack

- **Backend**: Python 3.8+
- **AI Model**: Mixtral-8x7B-Instruct (via Together AI)
- **Web Interface**: Gradio
- **Database**: SQLite
- **Data Processing**: Pandas
- **Medical Knowledge**: Wikipedia API
- **Language Processing**: LangChain

## 📁 Project Structure

```
healthcare-data-assistant/
├── python.py                 # Main application
├── create_health_db.py       # Database creation script
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── .gitignore               # Git ignore file
├── README.md                # This file
├── dataset/                 # Data files
│   ├── HIS_Logs.csv         # Healthcare logs data
│   └── Export_Diagnosis.csv # Diagnosis data
└── health.db               # SQLite database (generated)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
TOGETHER_API_KEY=your_together_ai_api_key_here
```

### Model Configuration

The application uses Mixtral-8x7B-Instruct with the following settings:
- Temperature: 0.1 (for consistent SQL generation)
- Max Tokens: 500
- Model: `mistralai/Mixtral-8x7B-Instruct-v0.1`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Together AI](https://together.ai/) for providing the Mixtral-8x7B-Instruct model
- [Gradio](https://gradio.app/) for the beautiful web interface
- [LangChain](https://langchain.com/) for LLM integration
- [Pandas](https://pandas.pydata.org/) for data manipulation

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/healthcare-data-assistant/issues) page
2. Create a new issue with detailed information
3. Contact the maintainers

## 🔮 Future Enhancements

- [ ] Support for additional database types (PostgreSQL, MySQL)
- [ ] Advanced data visualization with charts and graphs
- [ ] Export functionality for reports
- [ ] Multi-language support
- [ ] Integration with additional medical knowledge bases
- [ ] Real-time data streaming capabilities

---

**Made with ❤️ for the healthcare community** 