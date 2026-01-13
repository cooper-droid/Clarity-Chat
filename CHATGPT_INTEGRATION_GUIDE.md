# ChatGPT Integration Guide

## ✅ Integration Complete!

Your Fiat Clarity Chat now has a full admin settings panel to configure ChatGPT.

## 🚀 How to Use

### 1. Access the Admin Panel

Open in your browser:
```
http://localhost:3002/admin
```

### 2. Add Your OpenAI API Key

1. In the **OpenAI Configuration** section, find the **Openai Api Key** field
2. Paste your OpenAI API key (starts with `sk-...`)
3. Click **Save All Settings** at the bottom

### 3. Choose Your Model

Available models:
- `gpt-4-turbo-preview` (recommended - best quality)
- `gpt-4` (stable, high quality)
- `gpt-3.5-turbo` (faster, lower cost)

### 4. Adjust Settings

**Temperature** (0.0 - 2.0):
- `0.3` = Very focused and consistent
- `0.7` = Balanced (default)
- `1.0` = More creative and varied

**Max Tokens**:
- Default: `1000` tokens (~750 words)
- Increase for longer responses
- Decrease to save costs

### 5. Customize Behavior

**System Prompt**:
- Edit the full system prompt to change how the AI responds
- Controls tone, structure, and guardrails
- Uses the "Retirement: Redefined" framework by default

**Lead Gate Message**:
- Customize the message shown when asking for contact info

**UI Text**:
- Change chat title, subtitle, welcome message, and button text

## 📊 Available Settings

### OpenAI Configuration
- **API Key**: Your OpenAI API key
- **Model**: Which GPT model to use
- **Temperature**: Response creativity (0-2)
- **Max Tokens**: Maximum response length

### Knowledge Base (RAG)
- **Enable RAG**: Use document search
- **RAG Chunk Limit**: How many document chunks to retrieve
- **Enable Citations**: Show source citations

### Lead Capture
- **Enable Lead Gate**: Require contact info after first message
- **Lead Gate Message**: Custom message for lead capture

### UI Customization
- **Chat Title**: Header title
- **Chat Subtitle**: Header subtitle
- **Welcome Message**: Initial greeting
- **Schedule Button Text**: CTA button text

### System Prompt
- Full control over AI behavior and instructions

## 🧪 Testing

After configuring:

1. Go back to the chat: http://localhost:3002
2. Ask a question: "What is a Roth conversion?"
3. You should get a ChatGPT-powered response!

## 🔑 API Endpoints

All settings are accessible via API:

```bash
# Get all settings
GET http://localhost:8000/admin/settings

# Get specific setting
GET http://localhost:8000/admin/settings/openai_api_key

# Update setting
PUT http://localhost:8000/admin/settings/openai_api_key
Body: {"value": "sk-...", "type": "string"}

# Reset all settings
POST http://localhost:8000/admin/settings/reset

# Get public config (frontend-safe)
GET http://localhost:8000/config
```

## 📝 Example API Usage

### Update API Key via curl:
```bash
curl -X PUT http://localhost:8000/admin/settings/openai_api_key \
  -H "Content-Type: application/json" \
  -d '{"value": "sk-your-key-here", "type": "string"}'
```

### Update Temperature:
```bash
curl -X PUT http://localhost:8000/admin/settings/temperature \
  -H "Content-Type: application/json" \
  -d '{"value": 0.9, "type": "number"}'
```

### Update System Prompt:
```bash
curl -X PUT http://localhost:8000/admin/settings/system_prompt \
  -H "Content-Type: application/json" \
  -d '{"value": "You are a helpful assistant...", "type": "string"}'
```

## 🎛️ How It Works

1. **Settings Storage**: All settings are stored in SQLite database (`chat_settings` table)
2. **Runtime Updates**: Changes take effect immediately (no restart needed)
3. **Default Values**: Sensible defaults are provided for all settings
4. **Type Safety**: Settings are validated by type (string, number, boolean)

## 🔒 Security Notes

**For Production:**
1. Add authentication to `/admin` routes
2. Don't expose API key in frontend
3. Use environment variables for sensitive data
4. Add rate limiting
5. Enable HTTPS

## 💡 Tips

- **Start with defaults**: The default settings are optimized for retirement planning
- **Test in dev mode first**: Leave API key empty to test UI without using API credits
- **Adjust temperature**: Lower (0.3-0.5) for consistent advice, higher (0.8-1.2) for creative responses
- **Monitor costs**: Check your OpenAI usage dashboard regularly
- **Custom prompts**: Tailor the system prompt to your brand voice

## 🐛 Troubleshooting

**"OpenAI API error"**
- Check your API key is correct
- Verify your OpenAI account has credits
- Check the model name is valid

**Settings not saving**
- Check browser console for errors
- Verify backend is running (http://localhost:8000/health)
- Try resetting to defaults

**Dev mode active when API key is set**
- Check `.env` file: set `DEV_MODE=false`
- Restart backend after changing .env

## 📖 Next Steps

1. Add your OpenAI API key in the admin panel
2. Customize the system prompt to match your brand
3. Test with sample questions
4. Adjust temperature and max_tokens based on results
5. Enable/disable features as needed
6. Share the admin URL with your team

---

**Admin Panel**: http://localhost:3002/admin
**Chat Interface**: http://localhost:3002
**API Docs**: http://localhost:8000/docs
