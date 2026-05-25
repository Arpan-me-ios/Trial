import random


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
]


def get_topic() -> str:
    return random.choice(TOPIC_POOL)
