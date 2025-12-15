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
    except Exception as e:
        print(f"❌ Error loading emails: {e}")
        return []

def generate_response(email_subject, email_body, tone="professional", email_type="general"):
    """
    Generate an appropriate email response based on the email content.
    
    Args:
        email_subject: Subject line of incoming email
        email_body: Body text of incoming email
        tone: Desired tone (professional, friendly, apologetic, enthusiastic)
        email_type: Type of email (support, sales, general, etc.)
    """
    
    # System prompts for different scenarios
    system_prompts = {
        "support": """You are a helpful customer support representative. Generate professional, 
                     empathetic email responses that address the customer's concerns clearly. 
                     Always acknowledge their issue, provide helpful information, and offer next steps.""",
        
        "sales": """You are a friendly sales representative. Generate engaging email responses 
                   that answer questions, highlight value, and move conversations forward. 
                   Be enthusiastic but not pushy.""",
        
        "general": """You are a professional business communicator. Generate clear, concise 
                     email responses that address all points raised while maintaining a 
                     courteous and professional tone.""",
        
        "urgent": """You are responding to an urgent matter. Generate a response that acknowledges 
                    the urgency, apologizes for any delays, and provides immediate next steps. 
                    Be empathetic but solution-focused.""",
        
        "feedback": """You are responding to customer feedback. Generate a warm, appreciative 
                      response that thanks them sincerely and reinforces their decision to 
                      share their experience."""
    }
    
    system_prompt = system_prompts.get(email_type, system_prompts["general"])
    
    # Tone adjustments
    tone_instructions = {
        "professional": "Keep the tone strictly professional and formal.",
        "friendly": "Use a warm, friendly tone while remaining professional.",
        "apologetic": "Be apologetic and empathetic. Acknowledge mistakes if any.",
        "enthusiastic": "Be enthusiastic and energetic while staying professional."
    }
    
    tone_instruction = tone_instructions.get(tone, tone_instructions["professional"])
    
    user_prompt = f"""Generate a response to this email:

Subject: {email_subject}
Body: {email_body}

Tone requirement: {tone_instruction}

Generate a complete, ready-to-send email response including:
- Appropriate greeting
- Clear response addressing all points
- Professional sign-off
- Do NOT include "Subject:" line (we'll keep the same subject)

Keep the response concise (2-4 paragraphs)."""

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
        
        generated_response = response.choices[0].message.content
        tokens = response.usage.total_tokens
        cost = (response.usage.prompt_tokens / 1000) * 0.00015 + \
               (response.usage.completion_tokens / 1000) * 0.0006
        
        return {
            "success": True,
            "response": generated_response,
            "tokens": tokens,
            "cost": cost
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def display_email(email, index):
    """Display incoming email"""
    print("\n" + "=" * 70)
    print(f"📨 INCOMING EMAIL #{index}")
    print("=" * 70)
    print(f"From: {email['from']}")
    print(f"Subject: {email['subject']}")
    print(f"\nBody:\n{email['body']}")
    print("=" * 70)

def display_response(response_text):
    """Display generated response"""
    print("\n" + "=" * 70)
    print("📧 GENERATED RESPONSE")
    print("=" * 70)
    print(response_text)
    print("=" * 70)

def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("          📧 AI EMAIL RESPONDER 📧")
    print("          Generate Professional Email Responses")
    print("=" * 70)
    
    emails = load_sample_emails()
    
    if not emails:
        print("\n❌ No emails to process!")
        return
    
    print(f"\n✅ Loaded {len(emails)} sample emails\n")
    
    # Choose mode
    print("Choose mode:")
    print("1. Auto mode (respond to all emails automatically)")
    print("2. Interactive mode (choose tone for each email)")
    
    mode = input("\nEnter choice (1 or 2): ").strip()
    
    total_cost = 0.0
    responses_generated = 0
    
    for i, email in enumerate(emails, 1):
        display_email(email, i)
        
        # Determine tone and type
        if mode == "2":
            print("\nChoose tone for response:")
            print("1. Professional")
            print("2. Friendly")
            print("3. Apologetic")
            print("4. Enthusiastic")
            
            tone_choice = input("Enter choice (1-4) [default: 1]: ").strip()
            tone_map = {
                "1": "professional",
                "2": "friendly",
                "3": "apologetic",
                "4": "enthusiastic"
            }
            tone = tone_map.get(tone_choice, "professional")
        else:
            # Auto-determine tone based on email type
            if "urgent" in email.get('priority', '').lower():
                tone = "apologetic"
            elif "feedback" in email.get('type', '').lower():
                tone = "enthusiastic"
            elif "sales" in email.get('type', '').lower():
                tone = "friendly"
            else:
                tone = "professional"
        
        email_type = email.get('type', 'general')
        
        print(f"\n🔄 Generating {tone} response for {email_type} email...")
        
        result = generate_response(
            email['subject'],
            email['body'],
            tone,
            email_type
        )
        
        if result['success']:
            display_response(result['response'])
            print(f"\n💰 Cost: ${result['cost']:.6f} | Tokens: {result['tokens']}")
            total_cost += result['cost']
            responses_generated += 1
            
            # Option to save
            save = input("\n💾 Save this response? (y/n): ").strip().lower()
            if save == 'y':
                filename = f"response_{i}_{email['from'].split('@')[0]}.txt"
                with open(filename, 'w') as f:
                    f.write(f"To: {email['from']}\n")
                    f.write(f"Re: {email['subject']}\n\n")
                    f.write(result['response'])
                print(f"✅ Saved to {filename}")
        else:
            print(f"\n❌ Error: {result['error']}")
        
        # Continue?
        if i < len(emails):
            cont = input("\n👉 Press Enter for next email (or 'q' to quit): ")
            if cont.lower() == 'q':
                break
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SESSION SUMMARY")
    print("=" * 70)
    print(f"Emails processed: {i}")
    print(f"Responses generated: {responses_generated}")
    print(f"Total cost: ${total_cost:.6f}")
    if responses_generated > 0:
        print(f"Average cost per response: ${total_cost/responses_generated:.6f}")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Program interrupted")