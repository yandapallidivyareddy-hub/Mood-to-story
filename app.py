# ============================================================
# DIVINE WISDOM AI
# AI-Powered Scripture-Based Life Guidance
#
# Stack:
#   FastAPI
#   LangServe
#   LangChain
#   Gemini 3.5 Flash
#
# Features:
#   - Beautiful web interface
#   - LangChain Agent
#   - LangServe Playground
#   - Scripture retrieval tool
#   - Sanskrit scripture references
#   - Modern-life guidance
#   - Multiple deities / traditions
#   - Health endpoint
#   - Render / Colab compatible
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import os
import json
import logging
import uvicorn

from typing import Any

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from langserve import add_routes

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger("divine_wisdom_ai")


# ============================================================
# GOOGLE GEMINI CONFIGURATION
# ============================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:

    raise ValueError(
        "GOOGLE_API_KEY environment variable is not set."
    )


# ============================================================
# GEMINI MODEL
# ============================================================

llm = ChatGoogleGenerativeAI(

    model="gemini-3.5-flash",

    google_api_key=GOOGLE_API_KEY,

    temperature=0.2

)


# ============================================================
# SCRIPTURE DATABASE
# ============================================================
#
# IMPORTANT:
#
# The "source_text" field is intended to contain the source
# text itself.
#
# "translation" is an English rendering.
#
# "explanation" is NOT presented as scripture.
#
# The AI must never modify source_text and present the modified
# version as an original quotation.
#
# ============================================================

SCRIPTURES = [

    # --------------------------------------------------------
    # KRISHNA - BHAGAVAD GITA
    # --------------------------------------------------------

    {
        "deity": "Krishna",

        "tradition": "Vaishnavism",

        "scripture": "Bhagavad Gita",

        "reference": "Bhagavad Gita 2.47",

        "themes": [
            "career",
            "failure",
            "results",
            "stress",
            "work",
            "effort",
            "anxiety"
        ],

        "source_text": (
            "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन । "
            "मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥"
        ),

        "transliteration": (
            "karmaṇy-evādhikāras te mā phaleṣu kadācana "
            "mā karma-phala-hetur bhūr mā te saṅgo 'stv akarmaṇi"
        ),

        "translation": (
            "You have a claim to action alone, never to its fruits. "
            "Do not make the fruits of action your sole motive, "
            "nor become attached to inaction."
        )
    },


    {
        "deity": "Krishna",

        "tradition": "Vaishnavism",

        "scripture": "Bhagavad Gita",

        "reference": "Bhagavad Gita 2.48",

        "themes": [
            "success",
            "failure",
            "balance",
            "peace",
            "stress",
            "equanimity"
        ],

        "source_text": (
            "योगस्थः कुरु कर्माणि सङ्गं त्यक्त्वा धनञ्जय । "
            "सिद्ध्यसिद्ध्योः समो भूत्वा समत्वं योग उच्यते ॥"
        ),

        "transliteration": (
            "yogasthaḥ kuru karmāṇi saṅgaṃ tyaktvā dhanañjaya "
            "siddhy-asiddhyoḥ samo bhūtvā samatvaṃ yoga ucyate"
        ),

        "translation": (
            "Established in yoga, perform your actions, abandoning "
            "attachment and remaining even-minded in success and failure."
        )
    },


    {
        "deity": "Krishna",

        "tradition": "Vaishnavism",

        "scripture": "Bhagavad Gita",

        "reference": "Bhagavad Gita 6.5",

        "themes": [
            "self improvement",
            "mind",
            "discipline",
            "confidence",
            "motivation"
        ],

        "source_text": (
            "उद्धरेदात्मनात्मानं नात्मानमवसादयेत् । "
            "आत्मैव ह्यात्मनो बन्धुरात्मैव रिपुरात्मनः ॥"
        ),

        "transliteration": (
            "uddhared ātmanātmānaṃ nātmānam avasādayet "
            "ātmaiva hyātmano bandhur ātmaiva ripur ātmanaḥ"
        ),

        "translation": (
            "Let a person lift oneself by oneself and not degrade oneself; "
            "the self alone can be one's friend, and the self alone one's enemy."
        )
    },


    {
        "deity": "Krishna",

        "tradition": "Vaishnavism",

        "scripture": "Bhagavad Gita",

        "reference": "Bhagavad Gita 18.63",

        "themes": [
            "decision",
            "choice",
            "confusion",
            "life",
            "independence"
        ],

        "source_text": (
            "इति ते ज्ञानमाख्यातं गुह्याद्गुह्यतरं मया । "
            "विमृश्यैतदशेषेण यथेच्छसि तथा कुरु ॥"
        ),

        "transliteration": (
            "iti te jñānam ākhyātaṃ guhyād guhyataraṃ mayā "
            "vimṛśyaitad aśeṣeṇa yathecchasi tathā kuru"
        ),

        "translation": (
            "Thus I have explained to you knowledge more secret than the secret. "
            "Reflect fully on this, and then act as you choose."
        )
    },


    # --------------------------------------------------------
    # RAMA - RAMAYANA
    # --------------------------------------------------------

    {
        "deity": "Rama",

        "tradition": "Vaishnavism",

        "scripture": "Valmiki Ramayana",

        "reference": "Valmiki Ramayana - Dharma and conduct teachings",

        "themes": [
            "dharma",
            "duty",
            "truth",
            "responsibility",
            "leadership",
            "family"
        ],

        "source_text": (
            "धर्मो हि परमो लोके धर्मे सत्यं प्रतिष्ठितम्"
        ),

        "transliteration": (
            "dharmo hi paramo loke dharme satyaṃ pratiṣṭhitam"
        ),

        "translation": (
            "Dharma is supreme in the world; truth is established in dharma."
        )
    },


    # --------------------------------------------------------
    # VISHNU
    # --------------------------------------------------------

    {
        "deity": "Vishnu",

        "tradition": "Vaishnavism",

        "scripture": "Bhagavad Gita",

        "reference": "Bhagavad Gita 4.7",

        "themes": [
            "justice",
            "dharma",
            "protection",
            "evil",
            "righteousness"
        ],

        "source_text": (
            "यदा यदा हि धर्मस्य ग्लानिर्भवति भारत । "
            "अभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम् ॥"
        ),

        "transliteration": (
            "yadā yadā hi dharmasya glānir bhavati bhārata "
            "abhyutthānam adharmasya tadātmānaṃ sṛjāmy aham"
        ),

        "translation": (
            "Whenever there is a decline of dharma and a rise of adharma, "
            "then I manifest Myself."
        )
    },


    {
        "deity": "Vishnu",

        "tradition": "Vaishnavism",

        "scripture": "Bhagavad Gita",

        "reference": "Bhagavad Gita 4.8",

        "themes": [
            "justice",
            "protection",
            "righteousness",
            "evil",
            "dharma"
        ],

        "source_text": (
            "परित्राणाय साधूनां विनाशाय च दुष्कृताम् । "
            "धर्मसंस्थापनार्थाय सम्भवामि युगे युगे ॥"
        ),

        "transliteration": (
            "paritrāṇāya sādhūnāṃ vināśāya ca duṣkṛtām "
            "dharma-saṃsthāpanārthāya sambhavāmi yuge yuge"
        ),

        "translation": (
            "For the protection of the righteous, for the destruction "
            "of evildoers, and for the establishment of dharma, "
            "I manifest Myself age after age."
        )
    },


    # --------------------------------------------------------
    # SHIVA
    # --------------------------------------------------------

    {
        "deity": "Shiva",

        "tradition": "Shaivism",

        "scripture": "Shiva-related Hindu traditions",

        "reference": "Shiva tradition - meditation and self-mastery",

        "themes": [
            "meditation",
            "anger",
            "ego",
            "self control",
            "transformation",
            "peace"
        ],

        "source_text": (
            "ॐ नमः शिवाय"
        ),

        "transliteration": (
            "oṃ namaḥ śivāya"
        ),

        "translation": (
            "Salutations to Shiva."
        )
    },


    # --------------------------------------------------------
    # PARVATI / DEVI
    # --------------------------------------------------------

    {
        "deity": "Parvati",

        "tradition": "Shakta",

        "scripture": "Devi Mahatmya / Devi tradition",

        "reference": "Devi Mahatmya 5.16",

        "themes": [
            "strength",
            "compassion",
            "divine feminine",
            "courage",
            "protection"
        ],

        "source_text": (
            "या देवी सर्वभूतेषु शक्तिरूपेण संस्थिता । "
            "नमस्तस्यै नमस्तस्यै नमस्तस्यै नमो नमः ॥"
        ),

        "transliteration": (
            "yā devī sarva-bhūteṣu śakti-rūpeṇa saṃsthitā "
            "namas tasyai namas tasyai namas tasyai namo namaḥ"
        ),

        "translation": (
            "To the Goddess who abides in all beings in the form of power, "
            "salutations to Her again and again."
        )
    },


    {
        "deity": "Parvati",

        "tradition": "Shakta",

        "scripture": "Devi Mahatmya",

        "reference": "Devi Mahatmya 5.18",

        "themes": [
            "wisdom",
            "consciousness",
            "knowledge",
            "inner strength"
        ],

        "source_text": (
            "या देवी सर्वभूतेषु बुद्धिरूपेण संस्थिता । "
            "नमस्तस्यै नमस्तस्यै नमस्तस्यै नमो नमः ॥"
        ),

        "transliteration": (
            "yā devī sarva-bhūteṣu buddhi-rūpeṇa saṃsthitā "
            "namas tasyai namas tasyai namas tasyai namo namaḥ"
        ),

        "translation": (
            "To the Goddess who abides in all beings in the form of intelligence, "
            "salutations to Her again and again."
        )
    },


    # --------------------------------------------------------
    # LAKSHMI
    # --------------------------------------------------------

    {
        "deity": "Lakshmi",

        "tradition": "Shakta / Vaishnava",

        "scripture": "Sri Sukta",

        "reference": "Sri Sukta",

        "themes": [
            "wealth",
            "prosperity",
            "abundance",
            "success",
            "gratitude"
        ],

        "source_text": (
            "ॐ हिरण्यवर्णां हरिणीं सुवर्णरजतस्रजाम् । "
            "चन्द्रां हिरण्मयीं लक्ष्मीं जातवेदो म आवह ॥"
        ),

        "transliteration": (
            "oṃ hiraṇyavarṇāṃ hariṇīṃ suvarṇarajatasrajām "
            "candrāṃ hiraṇmayīṃ lakṣmīṃ jātavedo ma āvaha"
        ),

        "translation": (
            "O Jatavedas, bring to me Lakshmi, golden-hued and radiant, "
            "adorned with gold and silver, shining like the moon."
        )
    },


    # --------------------------------------------------------
    # HANUMAN
    # --------------------------------------------------------

    {
        "deity": "Hanuman",

        "tradition": "Vaishnavism / Ramabhakti",

        "scripture": "Hanuman Chalisa",

        "reference": "Hanuman Chalisa - opening invocation",

        "themes": [
            "courage",
            "fear",
            "strength",
            "devotion",
            "confidence",
            "discipline"
        ],

        "source_text": (
            "श्रीगुरु चरन सरोज रज निज मनु मुकुरु सुधारि । "
            "बरनऊँ रघुबर बिमल जसु जो दायकु फल चारि ॥"
        ),

        "transliteration": (
            "śrī guru caraṇa saroja raja nija manu mukuru sudhāri "
            "baranauṃ raghubara bimala jasu jo dāyaku phala cāri"
        ),

        "translation": (
            "Having cleansed the mirror of my mind with the dust of the "
            "lotus feet of my Guru, I describe the pure glory of Raghubara."
        )
    },


    # --------------------------------------------------------
    # NARASIMHA
    # --------------------------------------------------------

    {
        "deity": "Narasimha",

        "tradition": "Vaishnavism",

        "scripture": "Bhagavata Purana tradition",

        "reference": "Narasimha narrative - Bhagavata Purana",

        "themes": [
            "fear",
            "protection",
            "courage",
            "devotion",
            "justice"
        ],

        "source_text": (
            "ॐ उग्रं वीरं महाविष्णुं ज्वलन्तं सर्वतोमुखम् । "
            "नृसिंहं भीषणं भद्रं मृत्युमृत्युं नमाम्यहम् ॥"
        ),

        "transliteration": (
            "oṃ ugraṃ vīraṃ mahāviṣṇuṃ jvalantaṃ sarvatomukham "
            "nṛsiṃhaṃ bhīṣaṇaṃ bhadraṃ mṛtyuṃ mṛtyuṃ namāmy aham"
        ),

        "translation": (
            "I bow to Narasimha, fierce and heroic, the great Vishnu, "
            "radiant in all directions, formidable and auspicious."
        )
    },


    # --------------------------------------------------------
    # VAMANA
    # --------------------------------------------------------

    {
        "deity": "Vamana",

        "tradition": "Vaishnavism",

        "scripture": "Bhagavata Purana",

        "reference": "Bhagavata Purana - Vamana narrative",

        "themes": [
            "humility",
            "pride",
            "generosity",
            "dharma",
            "leadership"
        ],

        "source_text": (
            "उपेक्षिता मे यद् भर्त्रा दैत्येन्द्रेणात्मवैभवम्"
        ),

        "transliteration": (
            "upekṣitā me yad bhartrā daityendreṇātma-vaibhavam"
        ),

        "translation": (
            "The Vamana tradition teaches through the encounter with "
            "Bali and the themes of humility, generosity and divine order."
        )
    },


    # --------------------------------------------------------
    # MATSYA
    # --------------------------------------------------------

    {
        "deity": "Matsya",

        "tradition": "Vaishnavism",

        "scripture": "Matsya Purana / Bhagavata tradition",

        "reference": "Matsya Avatar tradition",

        "themes": [
            "protection",
            "knowledge",
            "crisis",
            "preservation",
            "wisdom"
        ],

        "source_text": (
            "मत्स्यावतार"
        ),

        "transliteration": (
            "matsyāvatāra"
        ),

        "translation": (
            "The Matsya Avatar tradition is associated with preservation "
            "and protection through a great cosmic crisis."
        )
    },


    # --------------------------------------------------------
    # KURMA
    # --------------------------------------------------------

    {
        "deity": "Kurma",

        "tradition": "Vaishnavism",

        "scripture": "Bhagavata Purana tradition",

        "reference": "Kurma Avatar - Churning of the Ocean",

        "themes": [
            "support",
            "stability",
            "patience",
            "teamwork",
            "difficulties"
        ],

        "source_text": (
            "कूर्मावतार"
        ),

        "transliteration": (
            "kūrmāvatāra"
        ),

        "translation": (
            "The Kurma Avatar tradition represents support and stability "
            "during the churning of the cosmic ocean."
        )
    },


    # --------------------------------------------------------
    # VARAHA
    # --------------------------------------------------------

    {
        "deity": "Varaha",

        "tradition": "Vaishnavism",

        "scripture": "Bhagavata Purana tradition",

        "reference": "Varaha Avatar",

        "themes": [
            "protection",
            "rescue",
            "courage",
            "earth",
            "crisis"
        ],

        "source_text": (
            "वराहावतार"
        ),

        "transliteration": (
            "varāhāvatāra"
        ),

        "translation": (
            "The Varaha Avatar tradition represents the restoration "
            "and protection of the Earth."
        )
    },


    # --------------------------------------------------------
    # PARASHURAMA
    # --------------------------------------------------------

    {
        "deity": "Parashurama",

        "tradition": "Vaishnavism",

        "scripture": "Ramayana / Mahabharata / Purana traditions",

        "reference": "Parashurama Avatar tradition",

        "themes": [
            "discipline",
            "justice",
            "strength",
            "responsibility",
            "anger"
        ],

        "source_text": (
            "परशुरामावतार"
        ),

        "transliteration": (
            "paraśurāmāvatāra"
        ),

        "translation": (
            "The Parashurama tradition explores discipline, strength, "
            "justice and responsibility."
        )
    },


    # --------------------------------------------------------
    # BUDDHA
    # --------------------------------------------------------

    {
        "deity": "Buddha",

        "tradition": "Vaishnavism - Dashavatara tradition",

        "scripture": "Dashavatara tradition",

        "reference": "Buddha Avatar tradition",

        "themes": [
            "compassion",
            "peace",
            "desire",
            "suffering",
            "mindfulness"
        ],

        "source_text": (
            "बुद्धावतार"
        ),

        "transliteration": (
            "buddhāvatāra"
        ),

        "translation": (
            "The Buddha Avatar tradition is associated with compassion, "
            "non-harm and spiritual discernment."
        )
    },


    # --------------------------------------------------------
    # KALKI
    # --------------------------------------------------------

    {
        "deity": "Kalki",

        "tradition": "Vaishnavism",

        "scripture": "Bhagavata Purana tradition",

        "reference": "Kalki Avatar tradition",

        "themes": [
            "dharma",
            "justice",
            "future",
            "righteousness",
            "change"
        ],

        "source_text": (
            "कल्क्यवतार"
        ),

        "transliteration": (
            "kalkyavatāra"
        ),

        "translation": (
            "The Kalki Avatar tradition is associated with the restoration "
            "of dharma at the end of an age."
        )
    }

]


# ============================================================
# SCRIPTURE RETRIEVAL
# ============================================================

def retrieve_scriptures(
    problem: str,
    deity: str = "All",
    top_k: int = 3
):

    problem_lower = problem.lower()

    candidates = []

    for item in SCRIPTURES:

        if deity and deity.lower() != "all":

            if item["deity"].lower() != deity.lower():
                continue

        score = 0

        for theme in item["themes"]:

            if theme.lower() in problem_lower:
                score += 3

        # Additional semantic keyword matching
        keyword_groups = {

            "career": [
                "job",
                "career",
                "work",
                "interview",
                "placement",
                "promotion",
                "office",
                "profession"
            ],

            "failure": [
                "failed",
                "failure",
                "rejected",
                "rejection",
                "lost",
                "setback"
            ],

            "stress": [
                "stress",
                "stressed",
                "pressure",
                "anxiety",
                "anxious",
                "worried"
            ],

            "fear": [
                "fear",
                "afraid",
                "scared",
                "nervous"
            ],

            "money": [
                "money",
                "financial",
                "finance",
                "wealth",
                "income",
                "debt"
            ],

            "anger": [
                "angry",
                "anger",
                "rage",
                "irritated"
            ],

            "relationship": [
                "relationship",
                "love",
                "family",
                "friend",
                "marriage"
            ],

            "confidence": [
                "confidence",
                "confident",
                "self doubt",
                "doubt"
            ],

            "decision": [
                "decision",
                "choose",
                "choice",
                "confused"
            ]
        }

        for theme, keywords in keyword_groups.items():

            if theme in item["themes"]:

                for keyword in keywords:

                    if keyword in problem_lower:
                        score += 2

        if score > 0:

            candidates.append(
                (score, item)
            )

    # Sort highest relevance first
    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    results = [
        item
        for score, item in candidates[:top_k]
    ]

    # If nothing matches, use broadly applicable Gita teaching
    if not results:

        fallback = [
            item
            for item in SCRIPTURES
            if item["reference"] == "Bhagavad Gita 2.47"
        ]

        results = fallback[:1]

    return results


# ============================================================
# SCRIPTURE TOOL
# ============================================================

@tool
def scripture_lookup(
    problem: str,
    preferred_deity: str = "All"
) -> str:
    """
    Retrieve relevant scripture records from the curated
    scripture database.

    The tool returns source text, reference, transliteration,
    and translation. The AI must not modify source_text.
    """

    results = retrieve_scriptures(
        problem=problem,
        deity=preferred_deity,
        top_k=3
    )

    output = []

    for item in results:

        output.append({

            "deity": item["deity"],

            "tradition": item["tradition"],

            "scripture": item["scripture"],

            "reference": item["reference"],

            "source_text": item["source_text"],

            "transliteration": item["transliteration"],

            "translation": item["translation"],

            "themes": item["themes"]

        })

    return json.dumps(
        output,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# AGENT
# ============================================================

agent = create_agent(

    model=llm,

    tools=[
        scripture_lookup
    ],

    system_prompt="""

You are Divine Wisdom AI.

You provide respectful, scripture-grounded guidance for
real-life situations.

Your purpose is NOT to replace teachers, scholars, counselors,
doctors, lawyers, financial advisors or other professionals.

============================================================
CORE RULE
============================================================

ALWAYS call scripture_lookup before giving spiritual guidance.

Never invent a scripture quotation.

Never create a Sanskrit verse yourself.

Never present an AI-generated sentence as an original scripture.

The "source_text" returned by scripture_lookup is the only
text that may be presented as the source scripture.

You may explain the scripture in your own words.

============================================================
SOURCE HANDLING
============================================================

For every retrieved scripture provide:

Scripture
Reference
Sanskrit / Source Text
Transliteration
English Translation

Clearly distinguish:

DIRECT SCRIPTURE
from
AI EXPLANATION

If the database contains a tradition-level record rather than
a complete quotation, say so clearly.

Do NOT falsely claim that a short traditional phrase is a
complete verse.

============================================================
REAL-LIFE GUIDANCE
============================================================

Connect the teaching to the user's actual situation.

Give practical actions.

Do not simply give a religious quotation.

For example, if someone failed an interview:

- acknowledge the setback
- identify what is under their control
- connect this with the retrieved teaching
- suggest practical preparation
- suggest a healthy next step

============================================================
RESPONSE FORMAT
============================================================

Always use these sections:

1. Situation Summary

2. Relevant Deity / Tradition

3. Scripture Source

4. Direct Scripture

5. Transliteration

6. English Translation

7. What This Teaching Means

8. Applying It to Your Situation

9. Practical Steps

10. Daily Reflection

11. Important Note

============================================================
IMPORTANT NOTE
============================================================

End with a short note explaining that the response is
educational/spiritual guidance and that interpretations of
scripture can differ among traditions and teachers.

If the user's situation involves a serious medical,
psychological, legal, financial or safety issue, encourage
appropriate professional help instead of presenting scripture
as a substitute.

Be respectful toward all Hindu traditions.

Do not claim that one deity is universally superior to
another.

Do not make unsupported historical or theological claims.
"""
)


# ============================================================
# RESULT EXTRACTION
# ============================================================

def extract_agent_text(result: Any) -> str:

    if result is None:

        return "No guidance was generated."


    # ------------------------------------------
    # Dictionary result
    # ------------------------------------------

    if isinstance(result, dict):

        messages = result.get(
            "messages",
            []
        )

        if messages:

            for message in reversed(messages):

                content = getattr(
                    message,
                    "content",
                    None
                )

                if content is not None:

                    text = normalize_content(
                        content
                    )

                    if text.strip():

                        return text


        # Sometimes output is directly present
        if "output" in result:

            return normalize_content(
                result["output"]
            )


    # ------------------------------------------
    # Direct message
    # ------------------------------------------

    content = getattr(
        result,
        "content",
        None
    )

    if content is not None:

        return normalize_content(
            content
        )


    # ------------------------------------------
    # String
    # ------------------------------------------

    if isinstance(result, str):

        return result


    return str(result)


# ============================================================
# NORMALIZE LANGCHAIN / GEMINI CONTENT
# ============================================================

def normalize_content(content: Any) -> str:

    if isinstance(
        content,
        str
    ):

        return content


    if isinstance(
        content,
        list
    ):

        parts = []

        for item in content:

            if isinstance(
                item,
                str
            ):

                parts.append(item)

            elif isinstance(
                item,
                dict
            ):

                if item.get("type") == "text":

                    text = item.get(
                        "text",
                        ""
                    )

                    if text:

                        parts.append(
                            str(text)
                        )

                elif "text" in item:

                    parts.append(
                        str(item["text"])
                    )

        return "\n".join(parts)


    if isinstance(
        content,
        dict
    ):

        if "text" in content:

            return str(
                content["text"]
            )

        return json.dumps(
            content,
            ensure_ascii=False,
            indent=2
        )


    return str(content)


# ============================================================
# RUN AGENT
# ============================================================

def run_guidance(
    problem: str,
    deity: str
) -> str:

    problem = problem.strip()

    deity = (
        deity.strip()
        if deity
        else "All"
    )

    prompt = f"""

User's real-life situation:

{problem}

Preferred deity or tradition:

{deity}

Please:

1. Use scripture_lookup first.
2. Use only the returned scripture source text as direct scripture.
3. Do not invent quotations.
4. Explain the retrieved teaching.
5. Connect it to the user's situation.
6. Provide practical steps.
7. Follow the required response format.
"""

    try:

        result = agent.invoke(

            {
                "messages": [
                    (
                        "user",
                        prompt
                    )
                ]
            }

        )

        return extract_agent_text(
            result
        )

    except Exception as e:

        logger.exception(
            "Agent execution failed"
        )

        raise RuntimeError(
            f"Guidance generation failed: {str(e)}"
        )


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(

    title="Divine Wisdom AI",

    version="2.0.0",

    description=(
        "Scripture-grounded AI guidance using "
        "LangChain, LangServe and Gemini."
    )

)


# ============================================================
# BEAUTIFUL FRONTEND
# ============================================================

HTML_PAGE = r"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Divine Wisdom AI</title>

<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {

    min-height: 100vh;

    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background:
        radial-gradient(
            circle at top left,
            #163b78 0%,
            #081b3a 40%,
            #030d20 100%
        );

    color: #ffffff;

    padding: 30px 18px;

}


/* =========================================================
   BACKGROUND
   ========================================================= */

.background-glow {

    position: fixed;

    width: 350px;

    height: 350px;

    border-radius: 50%;

    background:
        rgba(244, 196, 0, 0.12);

    filter: blur(80px);

    top: -100px;

    right: -100px;

    pointer-events: none;

}


/* =========================================================
   MAIN CONTAINER
   ========================================================= */

.container {

    width: 100%;

    max-width: 1050px;

    margin: auto;

}


/* =========================================================
   HEADER
   ========================================================= */

.header {

    text-align: center;

    padding: 30px 20px 25px;

}

.logo {

    width: 70px;

    height: 70px;

    margin: auto;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 50%;

    background:
        linear-gradient(
            135deg,
            #ffd83d,
            #e3a900
        );

    color: #071a3d;

    font-size: 34px;

    box-shadow:
        0 10px 35px
        rgba(245, 196, 0, 0.25);

}

.header h1 {

    margin-top: 18px;

    font-size: 42px;

    font-weight: 800;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #f5d25a
        );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;

}

.header p {

    margin-top: 10px;

    color: #c9d5eb;

    font-size: 16px;

}


/* =========================================================
   CARD
   ========================================================= */

.card {

    background:
        rgba(255, 255, 255, 0.97);

    color: #17233f;

    border-radius: 24px;

    padding: 34px;

    box-shadow:
        0 25px 70px
        rgba(0, 0, 0, 0.35);

}


/* =========================================================
   FORM
   ========================================================= */

label {

    display: block;

    margin-bottom: 9px;

    margin-top: 18px;

    font-size: 14px;

    font-weight: 700;

    color: #102b58;

}

textarea,
select {

    width: 100%;

    border: 1px solid #d7dce6;

    border-radius: 13px;

    padding: 15px;

    font-size: 15px;

    outline: none;

    background: #fbfcff;

    color: #17233f;

    transition: .2s;

}

textarea {

    min-height: 155px;

    resize: vertical;

}

textarea:focus,
select:focus {

    border-color: #d7a900;

    box-shadow:
        0 0 0 3px
        rgba(245, 196, 0, 0.15);

}


/* =========================================================
   BUTTON
   ========================================================= */

button {

    width: 100%;

    margin-top: 25px;

    padding: 16px;

    border: none;

    border-radius: 13px;

    background:
        linear-gradient(
            135deg,
            #ffd83d,
            #e5b300
        );

    color: #071a3d;

    font-size: 17px;

    font-weight: 800;

    cursor: pointer;

    transition: .25s;

}

button:hover {

    transform: translateY(-2px);

    box-shadow:
        0 10px 25px
        rgba(225, 176, 0, .25);

}

button:disabled {

    opacity: .6;

    cursor: not-allowed;

    transform: none;

}


/* =========================================================
   LOADING
   ========================================================= */

.loading {

    display: none;

    margin-top: 25px;

    padding: 18px;

    border-radius: 12px;

    background: #f3f6fb;

    text-align: center;

    color: #17396d;

    font-weight: 700;

}


/* =========================================================
   RESULT
   ========================================================= */

.result {

    display: none;

    margin-top: 30px;

    padding: 27px;

    border-radius: 16px;

    background: #f6f8fc;

    border-left:
        5px solid #e8b800;

    color: #17233f;

    line-height: 1.85;

    white-space: pre-wrap;

    overflow-x: auto;

}

.result-title {

    font-size: 19px;

    font-weight: 800;

    color: #102b58;

    margin-bottom: 15px;

}


/* =========================================================
   FOOTER
   ========================================================= */

.footer {

    text-align: center;

    padding: 24px;

    color: #aebbd2;

    font-size: 13px;

}

.footer a {

    color: #f4cb3b;

    text-decoration: none;

    margin: 0 7px;

}


/* =========================================================
   RESPONSIVE
   ========================================================= */

@media(max-width:700px) {

    body {

        padding: 15px;

    }

    .header h1 {

        font-size: 30px;

    }

    .card {

        padding: 22px;

    }

}

</style>

</head>


<body>

<div class="background-glow"></div>


<div class="container">


    <div class="header">

        <div class="logo">
            ॐ
        </div>

        <h1>
            Divine Wisdom AI
        </h1>

        <p>
            Ancient wisdom. Modern guidance.
        </p>

        <p>
            Explore scripture-grounded perspectives
            for real-life situations.
        </p>

    </div>


    <div class="card">


        <label for="problem">

            Describe Your Situation

        </label>


        <textarea
            id="problem"
            placeholder="Example: I failed an important interview and I am losing confidence. What guidance can I find in scripture?"
        ></textarea>


        <label for="deity">

            Choose a Deity / Tradition

        </label>


        <select id="deity">

            <option value="All">
                All Traditions
            </option>

            <option value="Krishna">
                Krishna
            </option>

            <option value="Rama">
                Rama
            </option>

            <option value="Vishnu">
                Vishnu
            </option>

            <option value="Shiva">
                Shiva
            </option>

            <option value="Parvati">
                Parvati / Devi
            </option>

            <option value="Lakshmi">
                Lakshmi
            </option>

            <option value="Hanuman">
                Hanuman
            </option>

            <option value="Narasimha">
                Narasimha
            </option>

            <option value="Vamana">
                Vamana
            </option>

            <option value="Matsya">
                Matsya
            </option>

            <option value="Kurma">
                Kurma
            </option>

            <option value="Varaha">
                Varaha
            </option>

            <option value="Parashurama">
                Parashurama
            </option>

            <option value="Buddha">
                Buddha
            </option>

            <option value="Kalki">
                Kalki
            </option>

        </select>


        <button
            id="submitButton"
            onclick="getGuidance()"
        >

            ✨ Receive Guidance

        </button>


        <div
            id="loading"
            class="loading"
        >

            🪷 Consulting the scripture
            knowledge base...

        </div>


        <div
            id="result"
            class="result"
        ></div>


    </div>


    <div class="footer">

        <div>

            <a href="/docs" target="_blank">
                API Docs
            </a>

            |

            <a
                href="/agent/playground/"
                target="_blank"
            >
                LangServe Playground
            </a>

            |

            <a
                href="/health"
                target="_blank"
            >
                Health
            </a>

        </div>

        <div style="margin-top:10px;">

            Divine Wisdom AI ·
            LangChain · LangServe · Gemini

        </div>

    </div>


</div>


<script>


async function getGuidance() {


    const problem =
        document.getElementById(
            "problem"
        ).value.trim();


    const deity =
        document.getElementById(
            "deity"
        ).value;


    const button =
        document.getElementById(
            "submitButton"
        );


    const loading =
        document.getElementById(
            "loading"
        );


    const result =
        document.getElementById(
            "result"
        );


    if (!problem) {

        result.style.display =
            "block";

        result.textContent =
            "Please describe your situation first.";

        return;

    }


    button.disabled = true;

    loading.style.display =
        "block";

    result.style.display =
        "none";


    const formData =
        new FormData();


    formData.append(
        "problem",
        problem
    );


    formData.append(
        "deity",
        deity
    );


    try {


        const response =
            await fetch(
                "/guide",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        loading.style.display =
            "none";


        result.style.display =
            "block";


        if (!response.ok) {

            result.textContent =
                data.response ||
                data.detail ||
                "An error occurred.";

            return;

        }


        let answer =
            data.response;


        if (
            typeof answer ===
            "object"
        ) {

            answer =
                JSON.stringify(
                    answer,
                    null,
                    2
                );

        }


        result.textContent =
            answer;


    }

    catch(error) {


        loading.style.display =
            "none";


        result.style.display =
            "block";


        result.textContent =
            "Unable to connect to the server.\n\n"
            + error.message;


    }

    finally {

        button.disabled = false;

    }

}


</script>


</body>

</html>
"""


# ============================================================
# HOME PAGE
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
async def home():

    return HTML_PAGE


# ============================================================
# MAIN GUIDANCE API
# ============================================================

@app.post(
    "/guide"
)
async def guide(

    problem: str = Form(...),

    deity: str = Form("All")

):

    problem = problem.strip()

    deity = deity.strip()


    if not problem:

        raise HTTPException(

            status_code=400,

            detail=(
                "Please describe your situation."
            )

        )


    try:

        response = run_guidance(

            problem=problem,

            deity=deity

        )


        return JSONResponse(

            content={

                "response": response

            }

        )


    except Exception as e:

        logger.exception(
            "Guidance endpoint failed"
        )

        return JSONResponse(

            status_code=500,

            content={

                "response":
                    f"Error: {str(e)}"

            }

        )


# ============================================================
# LANGSERVE INPUT
# ============================================================

def langserve_input(
    data: dict
):

    if not isinstance(
        data,
        dict
    ):

        raise ValueError(
            "Input must be a JSON object."
        )


    problem = data.get(
        "problem",
        ""
    )


    deity = data.get(
        "deity",
        "All"
    )


    if not isinstance(
        problem,
        str
    ):

        raise ValueError(
            "'problem' must be a string."
        )


    if not isinstance(
        deity,
        str
    ):

        deity = "All"


    problem = problem.strip()

    deity = deity.strip()


    if not problem:

        raise ValueError(
            "The 'problem' field is required."
        )


    return run_guidance(

        problem=problem,

        deity=deity

    )


# ============================================================
# LANGSERVE CHAIN
# ============================================================

guidance_chain = RunnableLambda(
    langserve_input
)


# ============================================================
# LANGSERVE ROUTES
# ============================================================

add_routes(

    app,

    guidance_chain,

    path="/agent",

    playground_type="default"

)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health"
)
async def health():

    return {

        "status": "healthy",

        "service": "Divine Wisdom AI",

        "version": "2.0.0",

        "model": "gemini-3.5-flash",

        "langserve": True

    }


# ============================================================
# API INFORMATION
# ============================================================

@app.get(
    "/api/info"
)
async def api_info():

    return {

        "name":
            "Divine Wisdom AI",

        "description":
            "Scripture-grounded AI guidance",

        "model":
            "gemini-3.5-flash",

        "framework":
            "FastAPI",

        "agent":
            "LangChain",

        "langserve":
            True,

        "routes": {

            "home":
                "/",

            "guidance":
                "/guide",

            "langserve":
                "/agent",

            "playground":
                "/agent/playground/",

            "invoke":
                "/agent/invoke",

            "stream":
                "/agent/stream",

            "docs":
                "/docs",

            "health":
                "/health"

        },

        "deities": [

            "Krishna",
            "Rama",
            "Vishnu",
            "Shiva",
            "Parvati",
            "Lakshmi",
            "Hanuman",
            "Narasimha",
            "Vamana",
            "Matsya",
            "Kurma",
            "Varaha",
            "Parashurama",
            "Buddha",
            "Kalki"

        ]

    }


# ============================================================
# STARTUP
# ============================================================

@app.on_event(
    "startup"
)
async def startup_event():

    logger.info(
        "=============================================="
    )

    logger.info(
        "Divine Wisdom AI started successfully"
    )

    logger.info(
        "Gemini model: gemini-3.5-flash"
    )

    logger.info(
        "Scripture records: %d",
        len(SCRIPTURES)
    )

    logger.info(
        "LangServe endpoint: /agent"
    )

    logger.info(
        "LangServe Playground: /agent/playground/"
    )

    logger.info(
        "Health endpoint: /health"
    )

    logger.info(
        "=============================================="
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "8000"
        )
    )


    uvicorn.run(

        "app:app",

        host="0.0.0.0",

        port=port,

        reload=False

    )
