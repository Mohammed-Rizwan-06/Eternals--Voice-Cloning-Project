"""
VoxShield - Scam Pattern Catalog & Entity Regexes
Module: backend.scam_intelligence.patterns
Owner: Keerthi
Problem Statement #26104

Compiled regex patterns, lexicons, and severity weights covering
CXO Impersonation, Digital Arrest, UPI/KYC Fraud, and Remote Access Coercion.
"""

import re
from typing import Dict, List
from .models import ScamCategory

# ----------------------------------------------------------------------
# Entity Extraction Regexes (Telephony & Indian Financial Context)
# ----------------------------------------------------------------------
ENTITY_REGEXES = {
    # Indian Rupees: Rs. 50,000, ₹ 25 Lakhs, 5 Crore, 10,000 INR
    "inr_amount": re.compile(
        r"(?:(?:rs\.?|inr|₹)\s*[\d,]+(?:\.\d+)?(?:\s*(?:lakh|lakhs|crore|crores|thousand|k))?|"
        r"[\d,]+(?:\.\d+)?\s*(?:lakh|lakhs|crore|crores)\s*(?:rupees|rs|inr)?)",
        re.IGNORECASE
    ),
    # US Dollars / Foreign Currency: $500,000, 25000 USD
    "usd_amount": re.compile(
        r"(?:\$\s*[\d,]+(?:\.\d+)?|[\d,]+(?:\.\d+)?\s*(?:usd|dollars))",
        re.IGNORECASE
    ),
    # Indian UPI Virtual Payment Addresses (VPA)
    "upi_id": re.compile(
        r"\b[a-zA-Z0-9.\-_]{2,256}@(oksbi|okhdfcbank|okicici|okaxis|paytm|apl|ybl|axl|upi|sbi|hdfcbank|icici|kotak|barodampay)\b",
        re.IGNORECASE
    ),
    # OTP patterns: 4 to 6 digit codes mentioned in context
    "otp_code": re.compile(
        r"(?:otp|one\s*time\s*password|code|pin|verification\s*code)\s*(?:is|was|:)?\s*([0-9]{4,6})\b|"
        r"\b([0-9]{4,6})\s*(?:is\s*your\s*otp|is\s*the\s*code)",
        re.IGNORECASE
    ),
    # Indian Bank Names
    "bank_name": re.compile(
        r"\b(state\s*bank\s*of\s*india|sbi|hdfc(?:\s*bank)?|icici(?:\s*bank)?|axis\s*bank|"
        r"punjab\s*national\s*bank|pnb|bank\s*of\s*baroda|bob|kotak(?:\s*mahindra)?|"
        r"reserve\s*bank\s*of\s*india|rbi|canara\s*bank|union\s*bank|indusind\s*bank)\b",
        re.IGNORECASE
    ),
    # Remote Desktop Tools
    "remote_tools": re.compile(
        r"\b(anydesk|teamviewer|quicksupport|rustdesk|ultraviewer|zoho\s*assist|any\s*desk|team\s*viewer)\b",
        re.IGNORECASE
    ),
    # Claimed Law Enforcement Authorities (Digital Arrest)
    "law_authorities": re.compile(
        r"\b(cbi|central\s*bureau\s*of\s*investigation|mumbai\s*police|delhi\s*police|"
        r"cyber\s*crime(?:\s*branch|\s*cell)?|narcotics\s*control\s*bureau|ncb|"
        r"enforcement\s*directorate|ed|customs\s*department|customs\s*office|"
        r"supreme\s*court|trai|telecom\s*regulatory\s*authority)\b",
        re.IGNORECASE
    ),
    # IFSC code format (e.g., SBIN0001234, HDFC0000456)
    "ifsc_code": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
    # General Account Numbers (9 to 18 digits)
    "account_number": re.compile(r"(?:account|a/c)\s*(?:number|no\.?)?\s*(?:is|:)?\s*([0-9]{9,18})\b", re.IGNORECASE),
}


# ----------------------------------------------------------------------
# Scam Pattern Catalog (Categorized with weights 0.1 to 1.0)
# ----------------------------------------------------------------------
SCAM_PATTERNS = {
    # 1. CXO Impersonation / CEO Fraud (Problem 26104 Core Focus)
    ScamCategory.CXO_IMPERSONATION: [
        {
            "id": "CXO_001",
            "regex": re.compile(r"(?:i\s*am|this\s*is)\s*(?:the\s*)?(?:ceo|cfo|managing\s*director|director|vp|president)\b", re.IGNORECASE),
            "weight": 0.40,
            "desc": "Claiming executive identity (CEO/CFO/Director)",
        },
        {
            "id": "CXO_002",
            "regex": re.compile(r"(?:confidential|secret|urgent)\s*(?:acquisition|merger|deal|vendor\s*payment|settlement)\b", re.IGNORECASE),
            "weight": 0.50,
            "desc": "Secret / confidential acquisition or settlement narrative",
        },
        {
            "id": "CXO_003",
            "regex": re.compile(r"(?:bypass|skip|waive)\s*(?:the\s*)?(?:dual\s*approval|po|purchase\s*order|approval\s*process|authorization|verification)\b", re.IGNORECASE),
            "weight": 0.70,
            "desc": "Explicit demand to bypass authorization or procurement protocol",
        },
        {
            "id": "CXO_004",
            "regex": re.compile(r"(?:wire|transfer|remit|rtgs|neft)\s*(?:funds|money|the\s*amount|[\d,]+\s*(?:lakh|lakhs|crore|crores|rupees)?)\s*(?:immediately|right\s*now|within\s*\d+\s*(?:mins|minutes|hours))\b", re.IGNORECASE),
            "weight": 0.65,
            "desc": "High urgency wire transfer demand",
        },
        {
            "id": "CXO_005",
            "regex": re.compile(r"(?:in\s*a\s*board\s*meeting|in\s*a\s*closed\s*conference|cannot\s*take\s*calls|don't\s*(?:message|slack|email)\s*me)\b", re.IGNORECASE),
            "weight": 0.45,
            "desc": "Out-of-band communication suppression ('in a meeting, do not call')",
        },
    ],

    # 2. Digital Arrest / Law Enforcement Impersonation (Problem 26104 Core Focus)
    ScamCategory.DIGITAL_ARREST: [
        {
            "id": "DAR_001",
            "regex": re.compile(r"(?:parcel|package|consignment)\s*(?:intercepted|seized|held)\s*(?:at\s*customs|at\s*airport|with\s*(?:drugs|mdma|narcotics|contraband|fake\s*passports)|contains\s*(?:narcotics|drugs|contraband))\b", re.IGNORECASE),
            "weight": 0.75,
            "desc": "Contraband/drugs parcel interception claim",
        },
        {
            "id": "DAR_002",
            "regex": re.compile(r"(?:aadhaar|pan)\s*(?:card)?\s*(?:is\s*)?(?:linked\s*to|misused\s*in|found\s*in)?\s*(?:in\s*)?(?:money\s*laundering|illegal\s*accounts|terror\s*funding)\b", re.IGNORECASE),
            "weight": 0.70,
            "desc": "Identity document misuse in money laundering allegation",
        },
        {
            "id": "DAR_003",
            "regex": re.compile(r"(?:digital\s*arrest|arrest\s*warrant|non[- ]bailable\s*warrant|immediate\s*arrest)\b", re.IGNORECASE),
            "weight": 0.85,
            "desc": "Digital arrest or non-bailable warrant intimidation",
        },
        {
            "id": "DAR_004",
            "regex": re.compile(r"(?:do\s*not\s*disconnect|stay\s*on\s*(?:video\s*call|the\s*line|skype)|camera\s*must\s*be\s*on)\b", re.IGNORECASE),
            "weight": 0.60,
            "desc": "Forced continuous connection / isolation demand",
        },
        {
            "id": "DAR_005",
            "regex": re.compile(r"(?:transfer|deposit)\s*(?:[\d,]+\s*(?:lakh|lakhs|rupees|rs)?\s*)?(?:security\s*deposit|clearance\s*amount|bail|verification\s*funds)?\s*(?:to\s*rbi|to\s*court|to\s*government\s*account)\b", re.IGNORECASE),
            "weight": 0.85,
            "desc": "Extortion disguised as court/RBI security deposit",
        },
    ],

    # 3. UPI & Banking / KYC Expiry Fraud
    ScamCategory.UPI_BANKING_FRAUD: [
        {
            "id": "BNK_001",
            "regex": re.compile(r"(?:kyc|aadhaar|pan)\s*(?:is\s*)?(?:expired|suspended|pending|blocked|deactivated)\b", re.IGNORECASE),
            "weight": 0.45,
            "desc": "KYC / account suspension urgency pretext",
        },
        {
            "id": "BNK_002",
            "regex": re.compile(r"(?:share|tell|give|enter)\s*(?:me\s*)?(?:the\s*)?(?:6[- ]digit|4[- ]digit)?\s*(?:otp|one[- ]time[- ]password|code)\b", re.IGNORECASE),
            "weight": 0.90,
            "desc": "Direct request for OTP / One Time Password",
        },
        {
            "id": "BNK_003",
            "regex": re.compile(r"(?:enter|type)\s*(?:your\s*)?(?:upi\s*pin|mpin)\s*(?:to\s*receive|to\s*claim|for\s*refund)\b", re.IGNORECASE),
            "weight": 0.95,
            "desc": "Entering UPI PIN to receive money (classic UPI scam vector)",
        },
        {
            "id": "BNK_004",
            "regex": re.compile(r"(?:electricity|power)\s*(?:bill\s*unpaid|connection\s*will\s*be\s*cut|disconnected\s*tonight)\b", re.IGNORECASE),
            "weight": 0.65,
            "desc": "Electricity disconnection threat lure",
        },
        {
            "id": "BNK_005",
            "regex": re.compile(r"(?:credit\s*card\s*limit|reward\s*points\s*expiry|redeem\s*points\s*into\s*cash)\b", re.IGNORECASE),
            "weight": 0.40,
            "desc": "Card limit upgrade or reward point lure",
        },
    ],

    # 4. Remote Access Coercion
    ScamCategory.REMOTE_ACCESS_COERCION: [
        {
            "id": "RMT_001",
            "regex": re.compile(r"(?:install|download|open)\s*(?:anydesk|teamviewer|quicksupport|rustdesk|ultraviewer)\b", re.IGNORECASE),
            "weight": 0.90,
            "desc": "Command to install remote access tool",
        },
        {
            "id": "RMT_002",
            "regex": re.compile(r"(?:share|read)\s*(?:the\s*)?(?:9[- ]digit|10[- ]digit)?\s*(?:code|id|number)\s*(?:from\s*(?:anydesk|the\s*app|the\s*screen))\b", re.IGNORECASE),
            "weight": 0.85,
            "desc": "Requesting remote desktop connection ID",
        },
        {
            "id": "RMT_003",
            "regex": re.compile(r"(?:accept|allow)\s*(?:the\s*)?(?:permission|screen\s*share|prompt|access)\b", re.IGNORECASE),
            "weight": 0.60,
            "desc": "Instructing victim to grant screen control",
        },
    ],

    # 5. Safe Account Scam
    ScamCategory.SAFE_ACCOUNT_SCAM: [
        {
            "id": "SAF_001",
            "regex": re.compile(r"(?:transfer|move|shift)\s*(?:all\s*)?(?:funds|money|balance)\s*to\s*(?:a\s*)?(?:safe|secure|rbi|government|temporary)\s*(?:account|reserve)\b", re.IGNORECASE),
            "weight": 0.90,
            "desc": "Transfer funds to 'safe account' for verification",
        },
        {
            "id": "SAF_002",
            "regex": re.compile(r"(?:money|funds)\s*will\s*be\s*(?:refunded|returned|credited\s*back)\s*(?:within|in)\s*(?:\d+\s*(?:minutes|hours)|shortly)\b", re.IGNORECASE),
            "weight": 0.50,
            "desc": "Promise of immediate refund after verification",
        },
    ],

    # 6. Credential Harvesting
    ScamCategory.CREDENTIAL_HARVESTING: [
        {
            "id": "CRD_001",
            "regex": re.compile(r"(?:tell|share|enter)\s*(?:your\s*)?(?:cvv|atm\s*pin|net\s*banking\s*password|login\s*password)\b", re.IGNORECASE),
            "weight": 0.95,
            "desc": "Demanding CVV or NetBanking password",
        },
    ],
}


# -------------------------------------------------------------
# Behavioral / Psychological Coercion Markers
# -------------------------------------------------------------
PSYCHOLOGICAL_MARKERS = {
    "urgency": [
        re.compile(r"\b(immediately|right\s*now|within\s*\d+\s*(?:mins|minutes|hour|hours)|urgently|asap|without\s*delay|time\s*is\s*running\s*out)\b", re.IGNORECASE),
        re.compile(r"\b(before\s*the\s*deadline|in\s*the\s*next\s*15\s*minutes|account\s*blocked\s*in\s*1\s*hour)\b", re.IGNORECASE),
    ],
    "authority": [
        re.compile(r"\b(cbi|officer|inspector|superintendent|director|commissioner|legal\s*action|court\s*order|police\s*case)\b", re.IGNORECASE),
        re.compile(r"\b(ceo|cfo|head\s*office|board\s*of\s*directors|executive\s*order)\b", re.IGNORECASE),
    ],
    "secrecy_isolation": [
        re.compile(r"\b(do\s*not\s*tell\s*(?:anyone|your\s*family|colleagues|manager|the\s*branch|bank\s*officials))\b", re.IGNORECASE),
        re.compile(r"\b(strictly\s*confidential|keep\s*this\s*to\s*yourself|do\s*not\s*mention\s*this\s*to\s*anyone)\b", re.IGNORECASE),
    ],
    "coercion_threat": [
        re.compile(r"\b(arrest|jail|police\s*van|heavy\s*penalty|fir\s*lodged|account\s*frozen|permanent\s*damage)\b", re.IGNORECASE),
    ],
}
