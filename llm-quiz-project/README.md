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

## Deployment to Render

### Option 1: Using render.yaml (Recommended)

1. Push your code to GitHub
2. Connect your repository to Render
3. Render will automatically detect `render.yaml` and configure the service
4. Set environment variables in Render dashboard:
   - `OPENAI_API_KEY`
   - `YOUR_EMAIL`
   - `YOUR_SECRET`

### Option 2: Manual Setup

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt && playwright install --with-deps chromium`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3
4. Add environment variables (same as above)

### Important Notes

- The build command includes Playwright browser installation
- Playwright is used for JavaScript-rendered quiz pages
- If Playwright fails, the app falls back to simple HTTP requests
- Ensure all three environment variables are set in Render's dashboard

## License

MIT License
