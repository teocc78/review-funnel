# Review Funnel

A complete solution for collecting guest reviews and feedback. Guests are emailed a link to rate their stay, and based on their rating, they're either directed to review platforms or shown a feedback form.

## Components

### 1. `index.html` - Rating UI

A mobile-friendly 5-star rating interface with:

- **Clean Design**: Gradient background with smooth animations
- **Star Rating**: Interactive 5-star selector with hover effects
- **Smart Routing**:
  - **4-5 Stars** → Thank you message with buttons linking to:
    - Google Reviews
    - Airbnb
    - VRBO
  - **1-3 Stars** → Feedback form that submits to Google Apps Script

**Features:**
- Fully responsive (mobile, tablet, desktop)
- No dependencies (vanilla HTML/CSS/JS)
- Accessible star interface
- Error and success messages
- Auto-resets after feedback submission

**Deployment:**
1. Host `index.html` on any web server or static host (Netlify, Vercel, S3, etc.)
2. Get the public URL and add it to your `.env` file as `RATING_PAGE_URL`

### 2. `send_requests.py` - Email Sender

Python script that:

- **Reads** `guests.csv` with guest information
- **Filters** guests who checked out yesterday
- **Sends** personalized review request emails via Gmail SMTP
- **Includes** the review page URL in each email

**Features:**
- HTML + plain text email templates
- Checks out dates automatically
- Error handling and logging
- Clear success/failure reporting

**Setup:**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Or manually:
   ```bash
   pip install python-dotenv
   ```

2. **Create `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables:**

   **Gmail Setup:**
   - If you have 2FA enabled (recommended), use an [App Password](https://support.google.com/accounts/answer/185833):
     - Go to Google Account → Security
     - Enable 2-Step Verification
     - Generate an App Password for "Mail" on "Windows Computer"
   - If you don't have 2FA, you can use your regular password (less secure)

   Fill in `.env`:
   ```env
   GMAIL_SMTP_SERVER=smtp.gmail.com
   GMAIL_SMTP_PORT=465
   GMAIL_USERNAME=your-email@gmail.com
   GMAIL_PASSWORD=your-16-character-app-password
   GMAIL_FROM_EMAIL=your-email@gmail.com
   RATING_PAGE_URL=https://yourdomain.com/index.html
   WEBHOOK_URL=https://script.google.com/macros/d/YOUR_SCRIPT_ID/userweb
   ```

4. **Prepare your guest CSV** (`guests.csv`):
   ```csv
   first_name,email,checkout_date
   John,john@example.com,2026-05-09
   Sarah,sarah@example.com,2026-05-10
   ```

5. **Run the script:**
   ```bash
   python send_requests.py
   ```

   The script will:
   - Load all guests from `guests.csv`
   - Filter for those with `checkout_date = yesterday`
   - Send personalized emails to each
   - Show a success summary

### 3. `guests.csv` - Guest Data

CSV file with guest information:

| Column | Description |
|--------|-------------|
| `first_name` | Guest's first name (used in email greeting) |
| `email` | Guest's email address |
| `checkout_date` | Checkout date in `YYYY-MM-DD` format |

**Example:**
```csv
first_name,email,checkout_date
John,john.doe@example.com,2026-05-09
Sarah,sarah.smith@example.com,2026-05-10
```

## Webhook URL Configuration

The webhook URL for feedback submissions can be provided in three ways:

1. **Via `.env` file (Recommended)**:
   Set `WEBHOOK_URL` in your `.env` file. The `send_requests.py` script automatically appends it to the rating page URL when sending emails.

2. **Via URL Query Parameter**:
   Add `?webhook=YOUR_URL` to the rating page URL. Example:
   ```
   https://example.com/index.html?webhook=https://script.google.com/macros/d/YOUR_SCRIPT_ID/userweb
   ```

3. **Hardcoded in HTML**:
   Replace `WEBHOOK_URL_PLACEHOLDER` in `index.html` with your actual webhook URL.

## Integration with Google Apps Script

For low-star ratings (1-3), feedback is submitted to a Google Apps Script that saves to a Google Sheet.

**Setup Google Apps Script:**

1. Go to [script.google.com](https://script.google.com)
2. Create a new project
3. Replace the code with:

```javascript
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const sheet = SpreadsheetApp.getActiveSheet();

    sheet.appendRow([
      new Date(),
      data.rating,
      data.feedback
    ]);

    return ContentService
      .createTextOutput(JSON.stringify({success: true}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({success: false, error: error.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
```

4. Deploy as web app:
   - Click Deploy → New deployment
   - Type: Web app
   - Execute as: your account
   - Who has access: Anyone
5. Copy the deployment URL and add to `.env` as `WEBHOOK_URL`

## Workflow

1. **Daily**: Run `send_requests.py` to send review requests to guests who checked out yesterday
2. **Guest Clicks Link**: Opens `index.html` and rates their stay
3. **5-Star Rating**: Shows thank you message with links to review platforms
4. **1-3 Stars**: Shows feedback form that submits to Google Sheet
5. **Review**: Check Google Sheet for feedback

## Scheduling

To run the script automatically each day:

### macOS/Linux (Cron)
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9 AM:
0 9 * * * /usr/bin/python3 /path/to/send_requests.py >> /path/to/logs/review_funnel.log 2>&1
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 9 AM
4. Set action: Run program
5. Program: `python` or `python.exe`
6. Arguments: `C:\path\to\send_requests.py`

## File Structure

```
review-funnel/
├── index.html           # Rating UI (host on web server)
├── send_requests.py     # Email sender script
├── guests.csv           # Guest data (CSV format)
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Environment variable template
└── README.md            # This file
```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `GMAIL_SMTP_SERVER` | Gmail SMTP server | `smtp.gmail.com` |
| `GMAIL_SMTP_PORT` | SMTP port | `465` |
| `GMAIL_USERNAME` | Gmail email address | `your-email@gmail.com` |
| `GMAIL_PASSWORD` | App password (not regular password) | `xxxx xxxx xxxx xxxx` |
| `GMAIL_FROM_EMAIL` | Sender email address | `your-email@gmail.com` |
| `RATING_PAGE_URL` | Public URL to index.html | `https://yourdomain.com/index.html` |
| `WEBHOOK_URL` | Google Apps Script webhook | `https://script.google.com/macros/...` |

## Troubleshooting

### "Failed to send email" error
- Verify Gmail credentials in `.env`
- If using App Password, make sure it's the 16-character version
- Ensure Gmail SMTP is enabled (usually is by default)

### No guests found
- Check that `guests.csv` has correct format
- Verify `checkout_date` matches yesterday's date (YYYY-MM-DD format)

### Feedback not saving to Google Sheet
- Check that WEBHOOK_URL is correct
- Verify Google Apps Script deployment is set to "Anyone"
- Check browser console (F12) for network errors

### Permission errors
- Make sure `.py` file is executable: `chmod +x send_requests.py`
- Verify `.env` file has correct permissions

## Security Notes

- Never commit `.env` to version control (use `.env.example` template)
- Use Gmail App Passwords instead of regular passwords
- Keep webhook URL private (it can be discovered in network requests, so assume it's public)
- Consider rate limiting on Google Apps Script to prevent abuse

## Future Enhancements

- Support for other email providers (SendGrid, Mailgun)
- Multiple language templates
- A/B testing different email variations
- Dashboard to view feedback and ratings
- Automated responses for low ratings
- Integration with property management systems
