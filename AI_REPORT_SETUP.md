# AI Report Generator Setup

## Getting Your Google API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

## Configuration

1. Open the file `.streamlit/secrets.toml`
2. Replace `your-google-api-key-here` with your actual API key:
   ```toml
   GOOGLE_API_KEY = "AIzaSy..."
   ```
3. Save the file

## Using the AI Report Generator

1. Run the optimizer first to generate data
2. Navigate to the "🤖 AI Report" tab
3. Select report focus areas and length
4. Click "Generate AI Report"
5. Ask follow-up questions in the chat interface

## Features

- **Comprehensive Reports**: Generate detailed analysis of optimization results
- **Cross-Questioning**: Ask specific questions about the data
- **Multiple Focus Areas**: Choose what aspects to emphasize
- **Downloadable Reports**: Export reports as Markdown files
- **Interactive Chat**: Get AI-powered answers to your questions

## Note

The API key is stored locally in `.streamlit/secrets.toml` and is not committed to version control (make sure to add it to `.gitignore`).
