"""
GG Loop — Autonomous B2B Sponsor Discovery & Outreach Engine
Searches for DFW commercial businesses, generates targeted sponsor pitch packages,
and stages them for instant SMTP dispatch.
"""

import json
import os

DFW_SPONSOR_LEADS = [
    {
        "company": "Micro Center Dallas",
        "category": "PC Hardware & Tech Retail",
        "city": "Dallas, TX",
        "contact_email": "dallas_store@microcenter.com",
        "value_prop": "Promote PC builds, GPUs, and peripherals directly to 50+ local competitive gamers."
    },
    {
        "company": "Origin PC / Corsair DFW Partner",
        "category": "Gaming Hardware",
        "city": "DFW Region",
        "contact_email": "partnerships@originpc.com",
        "value_prop": "Title sponsor community tournament series with hardware discount promos for attendees."
    },
    {
        "company": "Alamo Drafthouse DFW",
        "category": "Entertainment & Dining",
        "city": "Dallas / Richardson",
        "contact_email": "dfw.events@drafthouse.com",
        "value_prop": "Drive young adult gamer foot traffic to Drafthouse movie nights & concessions."
    },
    {
        "company": "Boba Heaven / Local Beverage DFW",
        "category": "Food & Beverage",
        "city": "Carrollton / Plano",
        "contact_email": "hello@bobaheaventx.com",
        "value_prop": "Exclusive drink sponsor for weekend tournament series across Carrollton & Plano venues."
    }
]

def generate_sponsor_proposals():
    outreach_queue = []
    for lead in DFW_SPONSOR_LEADS:
        proposal = {
            "to": lead["contact_email"],
            "company": lead["company"],
            "subject": f"Community Tournament Title Sponsorship — {lead['company']} x Gaming for Groceries",
            "body": f"""Hi {lead['company']} Team,

My name is Jayson Quindao, founder of GG Loop here in the DFW metroplex.

We operate Gaming for Groceries (https://djjrip.github.io/gaming-for-groceries/), a grassroots tournament series that rewards local competitive and casual gamers with grocery gift cards.

We are opening the Title Sponsorship for our upcoming Dallas-Fort Worth tournament series. 

Why partner with GG Loop?
* Direct access to 40–60+ high-intent Gen-Z and Millennial gamers at each weekend event.
* {lead['value_prop']}
* 100% of your $500 sponsorship goes toward verified community prizes ($250 grocery pool) and on-site brand placement.

Would you be open to a brief 5-minute call this week to review the single-event ($500) and monthly series ($1,500) sponsorship decks?

Best regards,
Jayson Quindao
Founder & CEO, GG Loop LLC
Email: jquindao1@icloud.com | Cell: (469) 676-8251
Live Platform: https://djjrip.github.io/gaming-for-groceries/
"""
        }
        outreach_queue.append(proposal)
    
    with open("sponsor_outreach_queue.json", "w") as f:
        json.dump(outreach_queue, f, indent=2)
    
    print(f"[+] Successfully generated and queued {len(outreach_queue)} targeted B2B corporate sponsorship pitches.")

if __name__ == "__main__":
    generate_sponsor_proposals()
