# Overview

This is a Russian language AI chatbot web application that uses GigaChat API from Sber, a professional Russian language model. The application provides a clean chat interface where users can have conversations with the AI via API calls and generate images through SeaArt AI integration. The system is built with Flask as the backend web framework and features real-time model status monitoring, session-based chat history, and a responsive Bootstrap-based frontend.

**Key Features:**
- **AI Image Generation**: Integrated SeaArt AI service with fallback to Pollinations.ai and Unsplash
- **Intelligent Search**: Multi-source search capabilities (Perplexity, Yandex, DuckDuckGo, Wikipedia)
- **Smart Detection**: Automatic detection of image generation requests and search queries
- **Rich Media Support**: Image display with modal view, download capabilities, and prompt attribution
- **Responsive Design**: Bootstrap-based UI with mobile support and intuitive controls

# Recent Changes

**2025-08-08 - SeaArt AI Image Generation Integration:**
- ✅ Integrated SeaArt AI service for AI image generation capabilities
- ✅ Added intelligent image request detection with 15+ trigger keywords
- ✅ Implemented fallback system using Pollinations.ai and Unsplash for reliability
- ✅ Created responsive image display with click-to-expand modal functionality
- ✅ Added image download capabilities and service attribution
- ✅ Updated UI with image generation commands and status indicators

**2025-08-08 - Internet Search Integration Improvements:**
- ✅ Fixed response ordering: Search results now properly integrated into AI responses instead of appearing after
- ✅ Expanded keyword detection system with 40+ indicators across categories: temporal, financial, weather, news, technology, sports, locations
- ✅ Completed Yandex Search API XML parsing implementation
- ✅ Resolved LSP type checking errors in token management
- ✅ Enhanced search result formatting and source attribution

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The frontend uses a traditional server-rendered approach with Flask templates, enhanced with vanilla JavaScript for interactivity. The UI is built with Bootstrap 5 for responsive design and Font Awesome for icons. The chat interface features a sidebar with model status and controls, and a main chat area with message history. JavaScript handles real-time interactions including message sending, model status checking, and UI updates.

## Backend Architecture
The backend follows a modular Flask application structure with separation of concerns:

- **Flask Web Server**: Handles HTTP requests, template rendering, and API endpoints
- **AI Model Manager**: Manages the GPT model lifecycle including loading, inference, and memory management
- **Session Management**: Uses Flask sessions to maintain chat history per user
- **Threaded Model Loading**: Models are loaded asynchronously in background threads to prevent blocking the web interface

## Model Integration
The application integrates with GigaChat API from Sber for professional AI responses. The model manager handles:

- Automatic OAuth token management and refresh
- Secure API communication with Sber's GigaChat service
- Message context preparation for dialogue continuity
- Error handling and fallback responses
- Real-time status monitoring and API health checks

## Data Storage
The system uses session-based storage for chat history, storing conversation data in Flask sessions. This provides temporary persistence per user session without requiring a database. Chat history is maintained as a list of message objects with role and content fields.

## API Structure
The application exposes several REST API endpoints:
- `/api/chat` - Main chat endpoint that accepts POST requests and returns AI responses or generated images
- `/api/model_status` - GET endpoint for GigaChat model status monitoring
- `/api/image_status` - GET endpoint for image generation service status
- `/api/clear` - POST endpoint for clearing chat history
- `/api/history` - GET endpoint for retrieving chat history

The chat endpoint automatically detects image generation requests and returns appropriate media responses with metadata including image URLs, prompts, and service attribution.

# External Dependencies

## Python Libraries
- **Flask**: Web framework for HTTP handling and templating
- **PyTorch**: Deep learning framework for model inference
- **Transformers**: Hugging Face library for GPT model integration
- **Werkzeug**: WSGI utilities including proxy fix middleware

## AI Model
- **GigaChat API**: Professional Russian language model from Sber
- **Model Access**: Cloud-based API with OAuth2 authentication
- **Capabilities**: Advanced dialogue, context understanding, professional responses

## Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive UI components
- **Font Awesome 6**: Icon library for UI elements
- **Vanilla JavaScript**: No additional JavaScript frameworks, uses native browser APIs

## Infrastructure
- **WSGI Server**: Compatible with standard WSGI deployment (Gunicorn, uWSGI, etc.)
- **GPU Support**: Optional CUDA acceleration for faster inference
- **Session Storage**: Uses Flask's built-in session management with configurable secret key