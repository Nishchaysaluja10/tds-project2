# LLM Analysis Quiz Project

This project automatically solves data analysis quiz questions using GPT-4.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create `.env` file with:
   ```
   OPENAI_API_KEY=your_key
   YOUR_EMAIL=your_email
   YOUR_SECRET=your_secret
   ```

3. Run:
   ```
   python app.py
   ```

## API Endpoint

POST to `/quiz` with:
```json
{
  "email": "your_email",
  "secret": "your_secret",
  "url": "quiz_url"
}
```

## License

MIT License
