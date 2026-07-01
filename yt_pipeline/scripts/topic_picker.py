import json
import random
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = PROJECT_ROOT / "assets" / "state"
RECENT_TOPICS_PATH = STATE_DIR / "recent_topics.json"
RECENT_TOPIC_LIMIT = 40


TOPIC_POOL = [
    "My business partner secretly moved our emergency fund, so I used the audit trail to take back control.",
    "My fiance demanded I pay his debt before the wedding, then I found the spreadsheet he hid from me.",
    "My sister stole my startup idea for a pitch competition, so I let the judges see the original timestamps.",
    "My boss took credit for the deal that saved the company, so I prepared one calm email with every receipt.",
    "My roommate used my credit card for luxury trips, so I turned her own travel posts into the repayment plan.",
    "My cousin tried to sell our grandmother's house behind the family, so I followed the public records.",
    "My ex drained our shared account after the breakup, but forgot every transfer had his name on it.",
    "My coworker framed me for missing cash, so I asked security for one camera angle everyone ignored.",
    "My uncle cut me out of the family business, then begged me to fix the client database he never backed up.",
    "My best friend borrowed money for rent, then posted a new car, so I made repayment impossible to dodge.",
    "My landlord kept my deposit for fake damages, so I used move-in photos and city records to win twice.",
    "My brother tried to sabotage my promotion, but his anonymous complaint included one detail only he knew.",
    "My husband said our savings were gone because of bills, then his new girlfriend tagged him at a resort.",
    "My manager fired me in front of everyone, then called me at midnight because I was the only one with the client password.",
    "My stepmom sold my late mother's necklace online, so I bought it back under a fake name and waited for dinner.",
    "My ex best friend invited everyone to her wedding except me, then used my stolen vows in the ceremony.",
    "My coworker deleted my presentation fifteen minutes before the board meeting, but forgot the projector was synced to my tablet.",
    "My fiance's mother tried to cancel my dress order, so the boutique owner sent me the call recording.",
    "My brother borrowed my car for one hour and returned it wrecked, then claimed I gave him permission to sell it.",
    "My boss told HR I was unstable, but the security badge logs proved who was really in the office at 2 a.m.",
    "My ex put my name on his loan application, so I let the bank hear the voicemail he thought I deleted.",
    "My roommate hid my rent payments for months, then panicked when the landlord asked for one simple receipt.",
    "My cousin announced my pregnancy at a family party, so I revealed the secret she made everyone promise to keep.",
    "My sister wore my wedding dress to her engagement party, then discovered I had already changed the venue.",
    "My father left the family business to my lazy brother, then my brother realized every supplier only trusted me.",
    "My boss gave my promotion to his nephew, so I showed the CEO the numbers with both names removed.",
    "My ex tried to ruin my credit before moving out, but he forgot I worked at the bank that flagged the pattern.",
    "My friend group chose the person who lied about me, so I let them find out during the vacation I quietly stopped funding.",
    "My uncle forged my signature on a property form, then asked why the notary wanted to meet him in person.",
    "My fiance used our wedding fund to pay his ex's rent, so I made one phone call before the invitations went out.",
    "My coworker stole my client list, then accidentally emailed the proof to the client she was trying to poach.",
    "My neighbor blamed me for damage she caused, but her own doorbell camera recorded the whole thing.",
    "My aunt hid my inheritance letter, so I brought the lawyer to Thanksgiving and asked her to explain the envelope.",
    "My boyfriend said he was working late, but the delivery app sent me the receipt for two dinners across town.",
    "My boss cut my commission in half, so I let the biggest client ask why my name was missing from the contract.",
    "My best friend copied my small business, then ordered inventory from the supplier who had signed my exclusivity agreement.",
    "My ex told everyone I was broke, so I invited him to the auction where I bought back the house he lost.",
    "My sister-in-law tried to get me banned from the family reunion, so I brought the group chat screenshots as party favors.",
    "My landlord raised my rent after I fixed the building for free, so I sent the city every inspection photo.",
    "My roommate sold my gaming setup while I was at work, then found out the buyer was my coworker.",
    "My fiance failed the loyalty test he created for me, and his own rules cost him the wedding.",
    "My cousin used my child's medical fund for a vacation, so I let the fundraiser donors see the bank memo.",
    "My boss asked me to train my replacement, so I trained her to ask why the company was breaking its own policy.",
    "My ex tried to keep my dog, but the microchip appointment exposed the lie he told the court.",
    "My brother-in-law mocked my job at dinner, then begged me to approve his mortgage application on Monday.",
    "My friend stole my lottery ticket as a prank, then learned the store camera had audio.",
    "My mother-in-law switched the seating chart to humiliate me, so I gave her table the surprise speech.",
    "My coworker reported my side hustle to HR, then HR asked why she was logged into my store account.",
    "My ex drained the honeymoon account, so I used the cancellation policy to give myself the trip anyway.",
    "My cousin took credit for caring for grandma, but the pharmacy records showed who had been paying every month.",
    "My boss blamed me for losing the account, then the client asked to speak only to the person he fired.",
    "My bridesmaid leaked my wedding plans, so I sent her three fake versions and watched which one appeared online.",
    "My roommate pretended she paid utilities, but the power company had one name on every failed payment.",
    "My sister tried to steal my baby name, then accidentally revealed the reason everyone stopped trusting her.",
    "My ex posted a breakup story for sympathy, so I replied with one screenshot and said nothing else.",
    "My uncle tried to sell my late father's tools, then the buyer recognized my engraved initials.",
    "My boss denied my overtime, so I used his calendar invites to calculate every unpaid hour.",
    "My fiance's best man exposed his secret at the rehearsal dinner, and I realized I had been protecting the wrong person.",
    "My neighbor kept stealing packages, so I mailed myself a decoy box with a legal notice inside.",
    "My coworker sabotaged my interview, then the hiring manager asked why her email came from my account.",
    "My ex's new girlfriend messaged me to brag, then accidentally helped me find the money he hid.",
    "My family called me selfish for refusing to pay again, so I showed them the spreadsheet of every loan they never repaid.",
    "My boss laughed when I quit, then discovered I owned the software license his department relied on.",
    "My cousin faked an emergency to steal my concert tickets, so I let the venue scan the real QR code first.",
    "My father-in-law demanded a prenup to protect his son, then my lawyer found out his son had no assets.",
    "My friend sold my handmade designs at a market, then a customer asked why my logo was still on the tags.",
    "My ex tried to make me pay his taxes, but his accountant copied me on the email that ended everything.",
    "My sister deleted my college acceptance email, so I opened the backup account she did not know existed.",
    "My manager gave my bonus to the team favorite, then payroll asked why my employee ID was on the winning project.",
    "My aunt tried to shame me over money at dinner, so I quietly paid the bill with the card from the company she mocked.",
    "My coworker faked being sick during launch week, then posted the beach photo that saved my career.",
]


def _load_recent_topics() -> list[str]:
    if not RECENT_TOPICS_PATH.exists():
        return []
    try:
        data = json.loads(RECENT_TOPICS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return [str(topic) for topic in data if isinstance(topic, str)]


def _save_recent_topics(topics: list[str]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    RECENT_TOPICS_PATH.write_text(
        json.dumps(topics[-RECENT_TOPIC_LIMIT:], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_topic() -> str:
    recent_topics = _load_recent_topics()
    recent_set = set(recent_topics)
    available_topics = [topic for topic in TOPIC_POOL if topic not in recent_set]
    if not available_topics:
        available_topics = TOPIC_POOL[:]
        recent_topics = []

    topic = random.choice(available_topics)
    _save_recent_topics([*recent_topics, topic])
    return topic
