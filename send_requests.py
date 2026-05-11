#!/usr/bin/env python3
"""
Send review request emails to guests who checked out yesterday.
"""

import os
import csv
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_yesterday_date():
    """Get yesterday's date as a string in YYYY-MM-DD format."""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def read_guests_csv(filename='guests.csv'):
    """Read guests from CSV file and return list of dicts."""
    guests = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                guests.append(row)
        print(f"✓ Read {len(guests)} guests from {filename}")
        return guests
    except FileNotFoundError:
        print(f"✗ Error: {filename} not found")
        return []
    except Exception as e:
        print(f"✗ Error reading {filename}: {e}")
        return []

def filter_checkout_yesterday(guests):
    """Filter guests who checked out yesterday."""
    yesterday = get_yesterday_date()
    filtered = [g for g in guests if g.get('checkout_date', '').strip() == yesterday]
    print(f"✓ Found {len(filtered)} guests with checkout date {yesterday}")
    return filtered

def create_email_html(first_name, rating_url):
    """Create HTML email template."""
    return f"""
    <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #667eea; margin: 0;">Thank You for Staying With Us!</h1>
                </div>

                <p>Hi {first_name},</p>

                <p>We hope you had a wonderful stay! Your feedback helps us improve and helps future guests discover our property.</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="{rating_url}" style="background-color: #667eea; color: white; padding: 14px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">
                        Share Your Experience
                    </a>
                </p>

                <p>It only takes a minute to leave a review, and it makes a huge difference!</p>

                <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">

                <p style="font-size: 12px; color: #999; margin: 0;">
                    If you have any questions, please don't hesitate to reach out. Thank you for choosing us!
                </p>
            </div>
        </body>
    </html>
    """

def send_email(email_address, first_name, smtp_config, rating_url, webhook_url=None):
    """Send review request email to a guest."""
    try:
        # Append webhook URL as query parameter if provided
        if webhook_url:
            separator = '&' if '?' in rating_url else '?'
            rating_url_with_webhook = f"{rating_url}{separator}webhook={webhook_url}"
        else:
            rating_url_with_webhook = rating_url
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"We'd Love Your Feedback, {first_name}!"
        msg['From'] = smtp_config['from_email']
        msg['To'] = email_address

        # Create plain text fallback
        text_content = f"""
Hello {first_name},

We hope you had a wonderful stay! Your feedback helps us improve.

Please share your experience here: {rating_url_with_webhook}

It only takes a minute to leave a review!

Thank you!
        """

        # Create HTML content
        html_content = create_email_html(first_name, rating_url_with_webhook)

        # Attach parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Send email
        with smtplib.SMTP_SSL(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
            server.login(smtp_config['username'], smtp_config['password'])
            server.sendmail(smtp_config['from_email'], email_address, msg.as_string())

        print(f"✓ Email sent to {email_address} ({first_name})")
        return True

    except Exception as e:
        print(f"✗ Failed to send email to {email_address}: {e}")
        return False

def main():
    """Main function to orchestrate email sending."""
    print("=" * 60)
    print("Review Request Email Sender")
    print("=" * 60)

    # Load environment variables
    smtp_server = os.getenv('GMAIL_SMTP_SERVER')
    smtp_port = int(os.getenv('GMAIL_SMTP_PORT', '465'))
    gmail_username = os.getenv('GMAIL_USERNAME')
    gmail_password = os.getenv('GMAIL_PASSWORD')
    gmail_from_email = os.getenv('GMAIL_FROM_EMAIL')
    rating_url = os.getenv('RATING_PAGE_URL')
    webhook_url = os.getenv('WEBHOOK_URL')

    # Validate environment variables
    required_vars = {
        'GMAIL_SMTP_SERVER': smtp_server,
        'GMAIL_USERNAME': gmail_username,
        'GMAIL_PASSWORD': gmail_password,
        'GMAIL_FROM_EMAIL': gmail_from_email,
        'RATING_PAGE_URL': rating_url,
    }

    missing_vars = [key for key, value in required_vars.items() if not value]
    if missing_vars:
        print(f"✗ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return False

    # Read and filter guests
    guests = read_guests_csv()
    if not guests:
        return False

    guests_to_email = filter_checkout_yesterday(guests)
    if not guests_to_email:
        print("No guests to email today.")
        return True

    # Prepare SMTP config
    smtp_config = {
        'smtp_server': smtp_server,
        'smtp_port': smtp_port,
        'username': gmail_username,
        'password': gmail_password,
        'from_email': gmail_from_email,
    }

    # Send emails
    print(f"\nSending {len(guests_to_email)} review request email(s)...")
    print("-" * 60)

    successful = 0
    failed = 0

    for guest in guests_to_email:
        email = guest.get('email', '').strip()
        first_name = guest.get('first_name', 'Guest').strip()

        if not email:
            print(f"✗ Skipping guest with no email: {first_name}")
            failed += 1
            continue

        if send_email(email, first_name, smtp_config, rating_url, webhook_url):
            successful += 1
        else:
            failed += 1

    # Summary
    print("-" * 60)
    print(f"\nSummary:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print("=" * 60)

    return failed == 0

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
