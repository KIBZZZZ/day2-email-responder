import os
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Session tracking
session_stats = {
    "emails_processed": 0,
    "responses_generated": 0,
    "total_cost": 0.0,
    "start_time": datetime.now()
}

def load_sample_emails():
    """Load sample emails from JSON file"""
    try:
        with open("sample_emails.json", "r") as f:
            data = json.load(f)
            return data["emails"]
    except Exception as e:
        print(f"❌ Error loading emails: {e}")
        return []

def analyze_email_quick(subject, body):
    """Quick email analysis to determine type, sentiment, priority"""
    
    analysis_prompt = f"""Analyze this email briefly:

Subject: {subject}
Body: {body}

Return ONLY these 4 lines (no extra text):
TYPE: [support/sales/general/feedback/urgent]
SENTIMENT: [positive/negative/neutral/angry]
PRIORITY: [low/medium/high/urgent]
TONE: [professional/friendly/apologetic/enthusiastic]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an email analyst. Be concise."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        analysis = response.choices[0].message.content
        tokens = response.usage.total_tokens
        cost = (response.usage.prompt_tokens / 1000) * 0.00015 + \
               (response.usage.completion_tokens / 1000) * 0.0006
        
        # Parse analysis
        parsed = {}
        for line in analysis.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                parsed[key.strip()] = value.strip()
        
        session_stats["total_cost"] += cost
        
        return {
            "success": True,
            "analysis": parsed,
            "tokens": tokens,
            "cost": cost
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def generate_response_smart(subject, body, analysis):
    """Generate smart response based on analysis"""
    
    email_type = analysis.get("TYPE", "general").lower().split('/')[0]
    recommended_tone = analysis.get("TONE", "professional").lower().split('/')[0]
    sentiment = analysis.get("SENTIMENT", "neutral").lower()
    priority = analysis.get("PRIORITY", "medium").lower()
    
    # System prompt based on analysis
    system_prompts = {
        "support": "You are a helpful customer support rep. Be empathetic and solution-focused.",
        "sales": "You are a friendly sales rep. Be enthusiastic and informative.",
        "urgent": "You are handling an urgent matter. Be apologetic and provide immediate solutions.",
        "feedback": "You are responding to feedback. Be grateful and warm.",
        "general": "You are a professional communicator. Be clear and courteous."
    }
    
    system_prompt = system_prompts.get(email_type, system_prompts["general"])
    
    # Add sentiment-based instructions
    sentiment_instructions = ""
    if "angry" in sentiment or "negative" in sentiment:
        sentiment_instructions = " The sender seems upset, so be extra empathetic and apologetic."
    elif "positive" in sentiment:
        sentiment_instructions = " The sender seems happy, so match their positive energy."
    
    user_prompt = f"""Generate a response to this email:

Subject: {subject}
Body: {body}

Context: This is a {email_type} email with {sentiment} sentiment and {priority} priority.
Tone: Use a {recommended_tone} tone.{sentiment_instructions}

Generate a complete, ready-to-send response (2-4 paragraphs). Include greeting and sign-off."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        generated = response.choices[0].message.content
        tokens = response.usage.total_tokens
        cost = (response.usage.prompt_tokens / 1000) * 0.00015 + \
               (response.usage.completion_tokens / 1000) * 0.0006
        
        session_stats["total_cost"] += cost
        session_stats["responses_generated"] += 1
        
        return {
            "success": True,
            "response": generated,
            "tokens": tokens,
            "cost": cost
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def save_response(email, response_text, analysis, filename_prefix="response"):
    """Save response with metadata"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sender = email['from'].split('@')[0]
    filename = f"{filename_prefix}_{timestamp}_{sender}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("EMAIL RESPONSE DRAFT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"To: {email['from']}\n")
        f.write(f"Re: {email['subject']}\n\n")
        
        f.write("ANALYSIS:\n")
        for key, value in analysis.items():
            f.write(f"  {key}: {value}\n")
        
        f.write("\n" + "-"*70 + "\n\n")
        f.write("DRAFT RESPONSE:\n\n")
        f.write(response_text)
        f.write("\n\n" + "="*70 + "\n")
    
    return filename

def display_email_card(email, index):
    """Display email in a card format"""
    print("\n" + "┏" + "━"*68 + "┓")
    print(f"┃ 📨 EMAIL #{index:<58} ┃")
    print("┣" + "━"*68 + "┫")
    print(f"┃ From: {email['from']:<59} ┃")
    print(f"┃ Subject: {email['subject'][:56]:<56} ┃")
    print("┣" + "━"*68 + "┫")
    
    # Wrap body text
    body_lines = email['body'].split('\n')
    for line in body_lines:
        if len(line) <= 66:
            print(f"┃ {line:<66} ┃")
        else:
            # Wrap long lines
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= 66:
                    current_line += word + " "
                else:
                    print(f"┃ {current_line:<66} ┃")
                    current_line = word + " "
            if current_line:
                print(f"┃ {current_line:<66} ┃")
    
    print("┗" + "━"*68 + "┛")

def display_analysis_card(analysis):
    """Display analysis in a card format"""
    print("\n" + "┏" + "━"*68 + "┓")
    print("┃ 📊 ANALYSIS" + " "*56 + "┃")
    print("┣" + "━"*68 + "┫")
    
    emoji_map = {
        "TYPE": {"support": "🔧", "sales": "💼", "general": "📝", "feedback": "⭐", "urgent": "🚨"},
        "SENTIMENT": {"positive": "😊", "negative": "😞", "neutral": "😐", "angry": "😡"},
        "PRIORITY": {"low": "🟢", "medium": "🟡", "high": "🟠", "urgent": "🔴"},
        "TONE": {"professional": "👔", "friendly": "😊", "apologetic": "🙏", "enthusiastic": "🎉"}
    }
    
    for key, value in analysis.items():
        emoji_dict = emoji_map.get(key, {})
        first_word = value.lower().split('/')[0].split()[0]
        emoji = emoji_dict.get(first_word, "•")
        display_line = f"┃ {emoji} {key}: {value}"
        padding = 68 - len(display_line) + 1
        print(display_line + " "*padding + "┃")
    
    print("┗" + "━"*68 + "┛")

def display_response_card(response_text, tokens, cost):
    """Display response in a card format"""
    print("\n" + "┏" + "━"*68 + "┓")
    print("┃ ✉️  GENERATED RESPONSE" + " "*45 + "┃")
    print("┣" + "━"*68 + "┫")
    
    # Display response with wrapping
    lines = response_text.split('\n')
    for line in lines:
        if len(line) <= 66:
            print(f"┃ {line:<66} ┃")
        else:
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= 66:
                    current_line += word + " "
                else:
                    print(f"┃ {current_line.rstrip():<66} ┃")
                    current_line = word + " "
            if current_line:
                print(f"┃ {current_line.rstrip():<66} ┃")
    
    print("┣" + "━"*68 + "┫")
    print(f"┃ 📊 Tokens: {tokens:<10} | 💰 Cost: ${cost:.6f}" + " "*25 + "┃")
    print("┗" + "━"*68 + "┛")

def show_session_stats():
    """Display session statistics"""
    elapsed = (datetime.now() - session_stats["start_time"]).total_seconds()
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    
    print("\n" + "┏" + "━"*68 + "┓")
    print("┃ 📊 SESSION STATISTICS" + " "*46 + "┃")
    print("┣" + "━"*68 + "┫")
    print(f"┃ Emails processed: {session_stats['emails_processed']:<48} ┃")
    print(f"┃ Responses generated: {session_stats['responses_generated']:<45} ┃")
    print(f"┃ Total cost: ${session_stats['total_cost']:.6f}" + " "*43 + "┃")
    if session_stats['responses_generated'] > 0:
        avg = session_stats['total_cost'] / session_stats['responses_generated']
        print(f"┃ Average cost per response: ${avg:.6f}" + " "*33 + "┃")
    print(f"┃ Session duration: {minutes}m {seconds}s" + " "*42 + "┃")
    print("┗" + "━"*68 + "┛")

def main():
    """Main function"""
    print("\n" + "┏" + "━"*68 + "┓")
    print("┃" + " "*68 + "┃")
    print("┃         🤖 AI EMAIL RESPONDER PRO 🤖" + " "*30 + "┃")
    print("┃         Smart Email Response Generation" + " "*28 + "┃")
    print("┃" + " "*68 + "┃")
    print("┗" + "━"*68 + "┛")
    
    emails = load_sample_emails()
    
    if not emails:
        print("\n❌ No emails to process!")
        return
    
    print(f"\n✅ Loaded {len(emails)} sample emails")
    print("\n📋 This tool will:")
    print("   1. Analyze each email (type, sentiment, priority)")
    print("   2. Generate intelligent responses")
    print("   3. Offer to save responses as drafts")
    print("   4. Track costs and statistics")
    
    input("\n👉 Press Enter to begin...")
    
    for i, email in enumerate(emails, 1):
        session_stats["emails_processed"] += 1
        
        display_email_card(email, i)
        
        print("\n🔄 Step 1: Analyzing email...")
        
        # Analyze email
        analysis_result = analyze_email_quick(email['subject'], email['body'])
        
        if not analysis_result['success']:
            print(f"❌ Analysis failed: {analysis_result['error']}")
            continue
        
        analysis = analysis_result['analysis']
        display_analysis_card(analysis)
        print(f"💰 Analysis cost: ${analysis_result['cost']:.6f}")
        
        # Ask user if they want to generate response
        choice = input("\n👉 Generate response? (y/n/s=skip all remaining): ").strip().lower()
        
        if choice == 's':
            print("⏭️  Skipping remaining emails...")
            break
        
        if choice != 'y':
            print("⏭️  Skipped")
            if i < len(emails):
                input("\n👉 Press Enter for next email...")
            continue
        
        print("\n🔄 Step 2: Generating smart response...")
        
        # Generate response
        response_result = generate_response_smart(
            email['subject'],
            email['body'],
            analysis
        )
        
        if response_result['success']:
            display_response_card(
                response_result['response'],
                response_result['tokens'],
                response_result['cost']
            )
            
            # Ask to save
            save_choice = input("\n💾 Save this response? (y/n): ").strip().lower()
            
            if save_choice == 'y':
                filename = save_response(email, response_result['response'], analysis)
                print(f"✅ Saved to: {filename}")
        else:
            print(f"❌ Response generation failed: {response_result['error']}")
        
        # Continue to next email?
        if i < len(emails):
            cont = input("\n👉 Press Enter for next email (or 'q' to quit): ")
            if cont.lower() == 'q':
                break
    
    # Show final statistics
    show_session_stats()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Program interrupted")
        show_session_stats()