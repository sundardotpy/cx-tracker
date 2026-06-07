import os
from supabase import create_client, Client
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

ISSUE_TAGS = [
    "Aadhar / PAN Queries", "Advisory", "App and Dashboard Bugs", "Asset General Enquiry",
    "Asset Limit", "Asset NRI", "Asset Risk", "Asset Specific Requirement", "Asset YTM/Coupon",
    "Bank Account linking issues", "Bond Purchase Cancellation", "Bond Purchase Issue",
    "Bond Purchase Order Status", "Bond Purchase Process", "Dashboard - Portfolio values",
    "FD Bugs", "FD Interest", "FD KYC", "FD Not Visible in Portfolio", "FD Order Status",
    "FD Withdrawal", "Flexi General Enquiry", "Form 121", "Form 121 Status & Confirmation",
    "Form 121 bugs", "Interest / Principal Not Credited", "Interest Repayment Breakup",
    "Interest Repayment Issue", "Interest Repayment When/Where", "KYC Process and Steps",
    "KYC Status", "Liquidity Cancellation", "Liquidity Charges", "Liquidity DDPI Status",
    "Liquidity Funds Not Received", "Liquidity General Enquiry", "Liquidity Process",
    "Liquidity Status Update", "Login & OTP Issue", "Net Banking Unavailable", "No query asked",
    "Nominee", "OTP Not Received", "PT Refund Pending", "Partnership", "Portfolio and Risk",
    "Profile Change", "Refer & Earn Not Activated", "Referral Reward Calculation",
    "Referred User Not Showing", "Request for RM", "SEBI KYC Delete Account", "SEBI KYC Demat Query",
    "SEBI KYC Details Change", "SEBI KYC Documents", "SEBI KYC General Enquiry", "SEBI KYC HUF",
    "SEBI KYC NSDL SPEEDE", "SGBs Not Visible in Portfolio", "SIP Cancellation",
    "SIP General Enquiry", "SIP Instalment Skip", "SIP Modification", "Selfie Capture",
    "Tax Deduction", "Taxation 15G/H", "Taxation Capital Gain/Loss", "Taxation Statement/Reports",
    "Taxation TDS Certificate", "Unsubscribe Whatsapp", "Wint Ivory General Query"
]

def seed_database():
    print("🔄 Connecting to Supabase to clear and seed tables...")
    
    # 1. Clear old data to prevent duplication conflicts
    supabase.table('users').delete().neq('username', '').execute()
    supabase.table('tags').delete().neq('name', '').execute()
    
    # 2. Add Admin user credentials
    hashed_password = generate_password_hash('5478')
    supabase.table('users').insert({"username": "kitten", "password": hashed_password}).execute()
    print("🟢 Admin account seeded")
    
    # 3. Add CX tags
    tag_objects = [{"name": tag} for tag in ISSUE_TAGS]
    supabase.table('tags').insert(tag_objects).execute()
    print(f"🟢 Successfully uploaded {len(ISSUE_TAGS)} CX tracking tags straight to Supabase!")

if __name__ == '__main__':
    seed_database()