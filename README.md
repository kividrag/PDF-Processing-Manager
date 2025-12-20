# **PDF Processing Manager**

A modern desktop application for batch processing PDF documents using AI models, with an intuitive folder-based organization system and real-time progress tracking.

## 🚀 Features

### **Core Functionality**
- **Batch PDF Processing**: Process multiple PDFs in a single operation
- **AI-Powered Analysis**: Use Hugging Face models (default: DeepSeek-V3.2) to analyze PDF content
- **Custom Instructions**: Define specific prompts/instructions for each processing task
- **Asynchronous Processing**: Run multiple processes simultaneously without blocking the UI

### **Organizational Features**
- **Folder Management**: Organize processes into custom folders
- **Process Dashboard**: Real-time statistics (total, running, completed, failed)
- **Detailed Logs**: Comprehensive logging for each process
- **Output Management**: Automatically organized output files

### **User Experience**
- **Modern UI**: Clean, responsive interface with light/dark themes
- **Process Controls**: Pause, resume, cancel, and delete operations
- **Progress Tracking**: Visual progress bars and file counters
- **Output Access**: Quick access to processed files via folder buttons

## 📋 Requirements

### **Python Dependencies**
```txt
PyQt6
openai
pdfplumber
```

### **API Requirements**
- Hugging Face API key (free tier available)
- Internet connection for model access

## 🛠️ Installation

### **Method 1: Direct Installation**
```bash
# Clone the repository
git clone https://github.com/username/pdf-processing-manager.git
cd pdf-processing-manager

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### **Method 2: Executable Build (Recommended)**
```bash
# Build executable using PyInstaller
pyinstaller --onefile --windowed --name "PDFProcessor" main.py

# The executable will be in the 'dist' folder
```

## ⚙️ Configuration

### **First-Time Setup**
1. Launch the application
2. Click **Settings** (⚙ button)
3. Enter your Hugging Face API key
4. Set default output folder
5. Choose your preferred theme (Light/Dark)

### **API Key Setup**
1. Get a free API key from [Hugging Face](https://huggingface.co/settings/tokens)
2. Copy the key into the Settings dialog
3. Save settings

## 📖 Usage Guide

### **Creating a New Process**
1. Click **"📄 New Process"**
2. Fill in process details:
   - **Process Name**: Descriptive name for your task
   - **Instruction**: Specific prompt for the AI model
   - **Model**: AI model to use (default: deepseek-ai/DeepSeek-V3.2:novita)
   - **PDF Folder**: Folder containing PDFs to process
3. Click **"🚀 Create & Start"**

### **Managing Processes**
- **Pause/Resume**: Temporarily stop or continue processing
- **Cancel**: Stop processing entirely
- **Delete**: Remove process and its outputs
- **Open Folder**: View processed files
- **View Logs**: See detailed processing history

### **Folder Organization**
- Create folders to organize different projects
- Drag-and-drop reordering (if implemented in future)
- Delete folders (including all contained processes)

## 🏗️ Project Structure

```
pdf-processing-manager/
├── main.py                   # Main application entry point
├── requirements.txt          # Required libraries
├── utils/
│   └── pdf_extract.py        # PDF text extraction utilities
├── saves/                    # Persistent data storage (auto-generated)
│   ├── app_settings.json     # User settings
│   ├── processes_state.json  # Process state data
│   └── folders_state.json    # Folder organization data
└── README.md                 # Documentation
```

## 🔧 Technical Details

### **Architecture**
- **GUI Framework**: PyQt6 for modern, responsive interface
- **Threading**: QThread-based worker threads for non-blocking operations
- **State Management**: JSON-based persistence for processes and settings
- **Error Handling**: Comprehensive error recovery and logging

### **Processing Pipeline**
1. **PDF Extraction**: Uses PyMuPDF for reliable text extraction
2. **AI Processing**: Sends extracted text to Hugging Face models
3. **Result Storage**: Saves outputs as numbered text files
4. **Progress Tracking**: Real-time updates with detailed logging

### **Supported Models**
- Default: `ServiceNow-AI/Apriel-1.6-15b-Thinker:together`
- Any model available via Hugging Face router
- Custom models with appropriate API access

## 🚨 Troubleshooting

### **Common Issues**

| Issue | Solution |
|-------|----------|
| "API key not configured" | Set your Hugging Face API key in Settings |
| "No PDF files found" | Ensure PDF folder contains .pdf files |
| "Failed to create output folder" | Check write permissions for output directory |
| "Model not responding" | Verify internet connection and API key validity |
| "Corrupted PDF" | Application skips corrupted PDFs and continues |

### **Performance Tips**
- Process smaller batches for better monitoring
- Use appropriate models for your task complexity
- Monitor API rate limits with Hugging Face
- Keep PDFs under 10MB for optimal processing

## 🔒 Security & Privacy

- **API Keys**: Stored locally in encrypted settings file
- **Data Processing**: Files processed locally, only text sent to API
- **No Cloud Storage**: All outputs saved to your local machine
- **Temporary Files**: No persistent storage of extracted content

## 📈 Future Enhancements

### **Planned Features**
- [ ] Batch process scheduling
- [ ] Export/Import process configurations
- [ ] Advanced PDF parsing (tables, images)
- [ ] Custom output formats (JSON, CSV)
- [ ] Plugin system for custom processors
- [ ] Cloud sync for settings and processes

### **In Development**
- [ ] Process templates for common tasks
- [ ] Advanced statistics and analytics
- [ ] API usage monitoring and cost estimation

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Note**: This application requires an active internet connection for AI model access. Processing times may vary based on PDF size, model complexity, and API availability.

---
