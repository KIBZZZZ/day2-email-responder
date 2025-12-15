import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_sample_emails():
    """Load sample emails from JSON file"""
    try:
        with open("sample_emails.json", "r") as f:
            data = json.load(f)
            return data["emails"]
    except FileNotFoundError:
        print("❌ Error: sample_emails.json not found!")
        return []
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON in sample_emails.json!")
        return []

def analyze_email(email_subject, email_body):
    """
    Analyze an email to determine:
    - Type (support, sales, general, urgent, feedback, newsletter)
    - Sentiment (positive, negative, neutral, angry, urgent)
    - Priority (low, medium, high, urgent)
    - Key points to address
    """
    
    analysis_prompt = f"""Analyze this email and provide a structured analysis:

Subject: {email_subject}
Body: {email_body}

Provide the analysis in this exact format:
TYPE: [support/sales/general/feedback/newsletter/other]
SENTIMENT: [positive/negative/neutral/angry/urgent]
PRIORITY: [low/medium/high/urgent]
KEY_POINTS: [list 2-3 main points to address in response]
TONE_RECOMMENDATION: [professional/friendly/apologetic/enthusiastic]

Be concise and clear."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert email analyst. Analyze emails quickly and accurately."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3,  # Low temperature for consistent analysis
            max_tokens=200
        )
        
        analysis = response.choices[0].message.content
        tokens = response.usage.total_tokens
        cost = (response.usage.prompt_tokens / 1000) * 0.00015 + \
               (response.usage.completion_tokens / 1000) * 0.0006
        
        return {
            "success": True,
            "analysis": analysis,
            "tokens": tokens,
            "cost": cost
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def parse_analysis(analysis_text):
    """Parse the structured analysis into a dictionary"""
    parsed = {}
    
    lines = analysis_text.strip().split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            parsed[key.strip()] = value.strip()
    
    return parsed

def display_email(email, index):
    """Display email in a nice format"""
    print("\n" + "=" * 70)
    print(f"📧 EMAIL #{index}")
    print("=" * 70)
    print(f"From: {email['from']}")
    print(f"Subject: {email['subject']}")
    print(f"\nBody:\n{email['body']}")
    print("=" * 70)

def display_analysis(analysis_dict):
    """Display analysis in a nice format"""
    print("\n📊 EMAIL ANALYSIS:")
    print("-" * 70)
    
    # Add emojis based on content
    type_emoji = {
        "support": "🔧",
        "sales": "💼",
        "general": "📝",
        "feedback": "⭐",
        "newsletter": "📰",
        "urgent": "🚨"
    }
    
    sentiment_emoji = {
        "positive": "😊",
        "negative": "😞",
        "neutral": "😐",
        "angry": "😡",
        "urgent": "⚠️"
    }
    
    priority_emoji = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🟠",
        "urgent": "🔴"
    }
    
    for key, value in analysis_dict.items():
        if key == "TYPE":
            emoji = type_emoji.get(value.lower().split('/')[0], "📧")
            print(f"{emoji} {key}: {value}")
        elif key == "SENTIMENT":
            emoji = sentiment_emoji.get(value.lower().split('/')[0], "😐")
            print(f"{emoji} {key}: {value}")
        elif key == "PRIORITY":
            emoji = priority_emoji.get(value.lower(), "⚪")
            print(f"{emoji} {key}: {value}")
        else:
            print(f"   {key}: {value}")
    
    print("-" * 70)

def main():
    """Main function to test email analysis"""
    print("\n" + "=" * 70)
    print("          📧 EMAIL ANALYZER 📧")
    print("          Powered by OpenAI GPT-4o-mini")
    print("=" * 70)
    
    # Load sample emails
    emails = load_sample_emails()
    
    if not emails:
        print("\n❌ No emails to analyze!")
        return
    
    print(f"\n✅ Loaded {len(emails)} sample emails")
    
    total_cost = 0.0
    
    # Analyze each email
    for i, email in enumerate(emails, 1):
        display_email(email, i)
        
        print("\n🔄 Analyzing email...")
        
        result = analyze_email(email['subject'], email['body'])
        
        if result['success']:
            parsed = parse_analysis(result['analysis'])
            display_analysis(parsed)
            
            print(f"\n💰 Cost: ${result['cost']:.6f} | Tokens: {result['tokens']}")
            total_cost += result['cost']
        else:
            print(f"\n❌ Analysis failed: {result['error']}")
        
        # Ask if user wants to continue
        if i < len(emails):
            user_input = input("\n👉 Press Enter for next email (or 'q' to quit): ")
            if user_input.lower() == 'q':
                break
    
    # Show total cost
    print("\n" + "=" * 70)
    print("📊 SESSION SUMMARY")
    print("=" * 70)
    print(f"Emails analyzed: {i}")
    print(f"Total cost: ${total_cost:.6f}")
    print(f"Average cost per email: ${total_cost/i:.6f}")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Program interrupted by user")