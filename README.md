# Elysium Model Management System

A comprehensive Streamlit application for model management, featuring AI-powered client brief processing, advanced search capabilities, and automated portfolio generation.

## 🌟 Features

- **Model Catalogue**: Browse and search through model portfolios with advanced filtering
- **Apollo Intelligence Dashboard**: Analytics and performance metrics for models and bookings
- **Athena AI Assistant**: AI-powered client brief parsing and model matching
- **Portfolio Generation**: Automated PDF portfolio creation with multiple templates
- **Cross-platform Compatibility**: Designed for cloud deployment

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd elysium
   ```

2. **Install dependencies**
   ```bash
   cd elysium_streamlit_app
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Access the application**
   Open your browser to `http://localhost:8501`

## 📁 Project Structure

```
elysium/
├── elysium_streamlit_app/          # Main Streamlit application
│   ├── app.py                      # Main application entry point
│   ├── path_config.py              # Centralized path management
│   ├── apollo_data.py              # Apollo dashboard data loader
│   ├── apollo_image_utils.py       # Image handling utilities
│   ├── athena_core.py              # AI-powered client brief processing
│   ├── athena_ui.py                # Athena UI components
│   ├── template_manager.py         # PDF template management
│   ├── requirements.txt            # Python dependencies
│   ├── .streamlit/
│   │   └── config.toml             # Streamlit configuration
│   └── pages/
│       └── apollo.py               # Apollo dashboard page
├── out/                            # Data files (CSV)
│   ├── models_normalized.csv
│   ├── bookings.csv
│   ├── clients.csv
│   ├── model_performance.csv
│   └── athena_events.csv
└── elysium_kb/
    └── images/                     # Model portfolio images
```

## ☁️ Cloud Deployment

### Streamlit Cloud

1. **Prepare your repository**
   - Ensure all files are committed to your Git repository
   - The main application file should be `elysium_streamlit_app/app.py`

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Set the main file path: `elysium_streamlit_app/app.py`
   - Deploy!

3. **Configuration**
   - The app uses `.streamlit/config.toml` for cloud-optimized settings
   - All paths are automatically resolved using the centralized path management system

### Heroku Deployment

1. **Create required files in the project root**
   
   Create `Procfile`:
   ```
   web: streamlit run elysium_streamlit_app/app.py --server.port=$PORT --server.address=0.0.0.0
   ```
   
   Create `runtime.txt`:
   ```
   python-3.11.0
   ```

2. **Deploy to Heroku**
   ```bash
   heroku create your-app-name
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

### Docker Deployment

1. **Create Dockerfile in project root**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY elysium_streamlit_app/ ./elysium_streamlit_app/
   COPY out/ ./out/
   COPY elysium_kb/ ./elysium_kb/
   
   RUN pip install -r elysium_streamlit_app/requirements.txt
   
   EXPOSE 8501
   
   CMD ["streamlit", "run", "elysium_streamlit_app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Build and run**
   ```bash
   docker build -t elysium-app .
   docker run -p 8501:8501 elysium-app
   ```

## 🔧 Configuration

### Environment Variables

- `OLLAMA_URL`: URL for Ollama LLM service (default: http://localhost:11434/api/generate)
- `OLLAMA_MODEL`: Model name for Ollama (default: gemma3:4b)

### Data Requirements

The application requires the following CSV files in the `out/` directory:
- `models_normalized.csv`: Model information and attributes
- `bookings.csv`: Booking history and revenue data
- `clients.csv`: Client information
- `model_performance.csv`: Model performance metrics
- `athena_events.csv`: AI assistant interaction logs

### Image Assets

Model portfolio images should be organized in `elysium_kb/images/` with the structure:
```
elysium_kb/images/
├── model_name_1/
│   ├── thumbnail.jpg
│   ├── portfolio1.jpg
│   └── portfolio2.jpg
└── model_name_2/
    ├── thumbnail.jpg
    └── portfolio1.jpg
```

## 🤖 AI Features

### Athena AI Assistant

- **Client Brief Parsing**: Natural language processing of client requirements
- **Model Matching**: AI-powered model recommendation based on parsed criteria
- **Email Generation**: Automated pitch email creation
- **PDF Portfolio Generation**: Dynamic portfolio creation with multiple templates

**Note**: AI features require a local Ollama installation for development. In cloud deployments, these features may be disabled if Ollama is not available.

## 🛠️ Development

### Adding New Features

1. **Path Management**: Use the centralized `path_config.py` for all file operations
2. **Data Loading**: Extend `apollo_data.py` for new data sources
3. **UI Components**: Add new pages in the `pages/` directory
4. **Templates**: Add new PDF templates in the `templates/` directory

### Testing

Run the test suite to validate functionality:
```bash
cd elysium_streamlit_app
python test_final_validation.py
```

## 📋 Dependencies

### Core Dependencies
- `streamlit>=1.28.0`: Web application framework
- `pandas>=2.0.0`: Data manipulation
- `plotly>=5.15.0`: Interactive visualizations
- `Pillow>=10.0.0`: Image processing

### Optional Dependencies
- `weasyprint>=60.0`: PDF generation (may require system dependencies)
- `jinja2>=3.1.0`: Template rendering
- `reportlab>=4.0.0`: Alternative PDF generation

## 🚨 Troubleshooting

### Common Issues

1. **Missing Data Files**
   - Ensure all CSV files are present in the `out/` directory
   - Check file permissions and accessibility

2. **Image Loading Issues**
   - Verify image files exist in `elysium_kb/images/`
   - Check image file formats (JPG, PNG supported)

3. **AI Features Not Working**
   - Ollama service may not be available in cloud deployments
   - AI features will gracefully degrade with fallback behavior

4. **PDF Generation Issues**
   - WeasyPrint may require additional system dependencies
   - Consider using ReportLab as an alternative

### Support

For deployment issues or feature requests, please check the project documentation or create an issue in the repository.

## 📄 License

This project is proprietary software. All rights reserved.
