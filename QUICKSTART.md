# Quick Start Guide

## Prerequisites
- Docker & Docker Compose installed
- Groq API Key (Free at https://console.groq.com)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/text-to-sql.git
cd text-to-sql
```

2. Create `.env` file:
```bash
GROQ_API_KEY=your_groq_api_key_here
```

3. Start the application:
```bash
docker-compose -f docker-compose-simple.yml up -d
```

4. Open `frontend.html` in your browser

## Usage

1. Upload your CSV/Excel/JSON file
2. Ask questions in plain English
3. Get instant SQL results!

## Example Questions
- "Show me first 20 rows"
- "What is the highest value in price column?"
- "Show me average of all numeric columns"

## Stop the application
```bash
docker-compose -f docker-compose-simple.yml down
```
