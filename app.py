import os
import base64
import html

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse

from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI

from google import genai
from google.genai import types


# =========================================================
# CONFIGURATION
# =========================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# You can change this in Render Environment Variables if needed.
TEXT_MODEL = os.getenv("TEXT_MODEL", "gemini-3.1-flash-lite-preview")

IMAGE_MODEL = os.getenv(
    "IMAGE_MODEL",
    "gemini-2.5-flash-image"
)


if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is not set. "
        "Add GOOGLE_API_KEY in Render Environment Variables."
    )


# =========================================================
# GEMINI CLIENTS
# =========================================================

llm = ChatGoogleGenerativeAI(
    model=TEXT_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.8,
)

img_client = genai.Client(
    api_key=GOOGLE_API_KEY
)


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Mood-to-Story AI",
    description="Generate beautiful mood-based stories and illustrations.",
    version="2.0"
)


# =========================================================
# MOOD CONFIGURATION
# =========================================================

MOOD_CONFIG = {

    "Happy": {
        "emoji": "😊",
        "visual": "bright warm sunlight, joyful expressions, colorful flowers, golden atmosphere",
        "tone": "joyful, optimistic, heartwarming and playful",
    },

    "Sad": {
        "emoji": "😢",
        "visual": "soft rain, blue twilight, emotional atmosphere, gentle light, peaceful surroundings",
        "tone": "emotional, touching, reflective but ultimately comforting",
    },

    "Excited": {
        "emoji": "🤩",
        "visual": "dynamic lighting, vibrant colors, energetic movement, magical sparks",
        "tone": "energetic, thrilling, adventurous and enthusiastic",
    },

    "Peaceful": {
        "emoji": "🌿",
        "visual": "calm lake, soft clouds, gentle sunlight, peaceful nature, pastel atmosphere",
        "tone": "calm, soothing, thoughtful and relaxing",
    },

    "Romantic": {
        "emoji": "❤️",
        "visual": "sunset, glowing lights, flowers, dreamy atmosphere, warm cinematic lighting",
        "tone": "warm, emotional, beautiful and romantic",
    },

    "Mysterious": {
        "emoji": "🔮",
        "visual": "misty forest, moonlight, mysterious shadows, glowing objects, magical atmosphere",
        "tone": "mysterious, intriguing, suspenseful and imaginative",
    },

    "Scared": {
        "emoji": "😨",
        "visual": "dark forest, dramatic moonlight, mysterious shadows, atmospheric fog",
        "tone": "suspenseful and slightly frightening but suitable for a general audience",
    },

    "Angry": {
        "emoji": "😠",
        "visual": "dramatic clouds, strong lighting, red-orange sunset, intense atmosphere",
        "tone": "intense, powerful, emotional and ultimately constructive",
    },

    "Hopeful": {
        "emoji": "🌟",
        "visual": "sunrise, glowing horizon, golden light, flowers blooming, uplifting atmosphere",
        "tone": "hopeful, inspiring, emotional and uplifting",
    },

    "Adventurous": {
        "emoji": "🗺️",
        "visual": "epic mountains, magical landscapes, dramatic sky, explorer atmosphere",
        "tone": "bold, exciting, adventurous and imaginative",
    },
}


# =========================================================
# STORY GENERATION
# =========================================================

def make_story(mood: str, genre: str, idea: str):

    config = MOOD_CONFIG.get(
        mood,
        MOOD_CONFIG["Happy"]
    )

    tone = config["tone"]

    if not idea.strip():
        idea = (
            "Create an original story that naturally reflects "
            "the selected mood."
        )

    prompt = f"""
You are a professional creative story writer.

Write a beautiful original {genre} story.

MOOD:
{mood}

EMOTIONAL TONE:
{tone}

STORY IDEA:
{idea}

Requirements:

- The story must strongly reflect the selected mood.
- Create an interesting main character.
- Include vivid scenes suitable for illustration.
- Have a clear beginning, middle and ending.
- Make it emotional, imaginative and engaging.
- Write approximately 400-500 words.
- Do not mention AI.

Return ONLY the following format:

TITLE: <story title>

STORY:
<story text>
"""

    response = llm.invoke(prompt)

    content = response.content

    # Gemini/LangChain can sometimes return content
    # as a list of dictionaries.
    if isinstance(content, list):

        text_parts = []

        for item in content:

            if isinstance(item, dict):

                if item.get("type") == "text":

                    text_parts.append(
                        item.get("text", "")
                    )

            elif isinstance(item, str):

                text_parts.append(item)

        content = "\n".join(text_parts)

    elif isinstance(content, dict):

        content = content.get(
            "text",
            ""
        )

    return str(content).strip()


# =========================================================
# IMAGE GENERATION
# =========================================================

def make_image(
    story: str,
    mood: str,
    genre: str,
    style: str
):

    config = MOOD_CONFIG.get(
        mood,
        MOOD_CONFIG["Happy"]
    )

    mood_visual = config["visual"]

    image_prompt = f"""
Create a beautiful storybook illustration.

Mood:
{mood}

Genre:
{genre}

Art Style:
{style}

Mood Visual Direction:
{mood_visual}

Story:
{story}

IMPORTANT VISUAL REQUIREMENTS:

- The image must strongly communicate the selected mood.
- Create a cinematic storybook composition.
- Use rich environmental details.
- Make the scene visually beautiful and emotionally expressive.
- Use lighting appropriate to the mood.
- Do not put paragraphs of text in the image.
- Do not create a poster.
- Create one polished illustration representing the story.
"""

    try:

        response = img_client.models.generate_content(
            model=IMAGE_MODEL,
            contents=image_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

        if not response.candidates:
            return None, None

        parts = response.candidates[0].content.parts

        for part in parts:

            inline_data = getattr(
                part,
                "inline_data",
                None
            )

            if inline_data:

                image_bytes = inline_data.data

                encoded = base64.b64encode(
                    image_bytes
                ).decode("utf-8")

                mime_type = (
                    inline_data.mime_type
                    or "image/png"
                )

                return encoded, mime_type

    except Exception as e:

        print(
            "IMAGE GENERATION ERROR:",
            str(e)
        )

    return None, None


# =========================================================
# HTML PAGE
# =========================================================

HTML = r"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Mood-to-Story AI</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        Inter,
        Arial,
        sans-serif;

    background:
        radial-gradient(
            circle at top right,
            #1e3a8a,
            #0f172a 45%,
            #020617
        );

    color: white;

    min-height: 100vh;
}


/* MAIN CONTAINER */

.container {

    width: 92%;

    max-width: 1050px;

    margin: auto;

    padding: 40px 0 70px;
}


/* HEADER */

.header {

    text-align: center;

    margin-bottom: 30px;
}

.header .icon {

    font-size: 60px;

    margin-bottom: 8px;
}

.header h1 {

    margin: 0;

    font-size: 42px;

    font-weight: 800;

    background:
        linear-gradient(
            90deg,
            #fbbf24,
            #f59e0b,
            #fde68a
        );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;
}

.header p {

    color: #cbd5e1;

    font-size: 17px;

    margin-top: 10px;
}


/* INPUT CARD */

.card {

    background:
        rgba(30, 41, 59, 0.88);

    border:
        1px solid rgba(255,255,255,0.1);

    border-radius: 24px;

    padding: 30px;

    box-shadow:
        0 25px 60px rgba(0,0,0,0.35);

    backdrop-filter: blur(15px);
}


/* GRID */

.form-grid {

    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 18px;
}


/* LABEL */

label {

    display: block;

    font-size: 14px;

    font-weight: 700;

    color: #f8fafc;

    margin-bottom: 8px;
}


/* INPUTS */

select,
textarea {

    width: 100%;

    padding: 14px 16px;

    border-radius: 12px;

    border:
        1px solid #475569;

    background: #0f172a;

    color: white;

    font-size: 15px;

    outline: none;
}

select:focus,
textarea:focus {

    border-color: #f59e0b;

    box-shadow:
        0 0 0 3px
        rgba(245,158,11,0.15);
}

textarea {

    min-height: 110px;

    resize: vertical;
}

.idea {

    grid-column:
        1 / -1;
}


/* BUTTON */

button {

    width: 100%;

    margin-top: 22px;

    padding: 16px;

    border: none;

    border-radius: 13px;

    background:
        linear-gradient(
            135deg,
            #f59e0b,
            #fbbf24
        );

    color: #111827;

    font-size: 17px;

    font-weight: 800;

    cursor: pointer;

    transition: 0.25s;
}

button:hover {

    transform:
        translateY(-2px);

    box-shadow:
        0 10px 25px
        rgba(245,158,11,0.3);
}

button:disabled {

    opacity: 0.6;

    cursor: wait;

    transform: none;
}


/* LOADING */

.loading {

    text-align: center;

    padding: 35px;

    color: #fbbf24;

    font-size: 18px;
}


/* RESULT */

.result {

    margin-top: 30px;

    animation:
        fadeIn 0.5s ease;
}

@keyframes fadeIn {

    from {
        opacity: 0;
        transform: translateY(15px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}


/* MOOD BADGE */

.mood-badge {

    display: inline-flex;

    align-items: center;

    gap: 8px;

    padding: 8px 14px;

    border-radius: 30px;

    background:
        rgba(245,158,11,0.15);

    border:
        1px solid rgba(245,158,11,0.35);

    color: #fbbf24;

    font-weight: 700;

    margin-bottom: 15px;
}


/* IMAGE */

.story-image {

    width: 100%;

    max-height: 550px;

    object-fit: cover;

    border-radius: 20px;

    margin: 10px 0 28px;

    box-shadow:
        0 20px 45px
        rgba(0,0,0,0.4);
}


/* STORY BOX */

.story-box {

    background:
        rgba(15,23,42,0.8);

    border-radius: 20px;

    padding: 28px;

    border:
        1px solid #334155;
}

.story-title {

    font-size: 30px;

    font-weight: 800;

    color: #fbbf24;

    margin-bottom: 22px;
}

.story-text {

    font-size: 17px;

    line-height: 1.9;

    color: #e2e8f0;

    white-space: pre-wrap;
}


/* ERROR */

.error {

    margin-top: 20px;

    padding: 16px;

    border-radius: 12px;

    background:
        rgba(239,68,68,0.15);

    border:
        1px solid rgba(239,68,68,0.4);

    color: #fecaca;
}


/* FOOTER */

.footer {

    text-align: center;

    color: #64748b;

    margin-top: 35px;

    font-size: 13px;
}


/* RESPONSIVE */

@media(max-width: 750px) {

    .form-grid {

        grid-template-columns: 1fr;
    }

    .idea {

        grid-column: auto;
    }

    .header h1 {

        font-size: 32px;
    }

    .card {

        padding: 20px;
    }
}

</style>

</head>


<body>

<div class="container">


    <div class="header">

        <div class="icon">📖✨</div>

        <h1>Mood-to-Story AI</h1>

        <p>
            Transform your mood and imagination
            into a magical illustrated story.
        </p>

    </div>


    <div class="card">

        <div class="form-grid">


            <div>

                <label>🎭 Choose Your Mood</label>

                <select id="mood">

                    <option>Happy</option>

                    <option>Sad</option>

                    <option>Excited</option>

                    <option>Peaceful</option>

                    <option>Romantic</option>

                    <option>Mysterious</option>

                    <option>Scared</option>

                    <option>Angry</option>

                    <option>Hopeful</option>

                    <option>Adventurous</option>

                </select>

            </div>


            <div>

                <label>📚 Choose Genre</label>

                <select id="genre">

                    <option>Fantasy</option>

                    <option>Adventure</option>

                    <option>Mystery</option>

                    <option>Comedy</option>

                    <option>Romance</option>

                    <option>Science Fiction</option>

                    <option>Horror</option>

                    <option>Friendship</option>

                    <option>Inspirational</option>

                </select>

            </div>


            <div>

                <label>🎨 Illustration Style</label>

                <select id="style">

                    <option>Cinematic Storybook</option>

                    <option>Anime</option>

                    <option>Watercolor</option>

                    <option>Fantasy Digital Art</option>

                    <option>Children's Storybook</option>

                </select>

            </div>


            <div class="idea">

                <label>
                    💡 What should your story be about?
                </label>

                <textarea
                    id="idea"
                    placeholder="Example: A student discovers a magical library where every book can change reality..."
                ></textarea>

            </div>

        </div>


        <button
            id="createButton"
            onclick="generateStory()"
        >
            ✨ Create My Story
        </button>


        <div id="output"></div>

    </div>


    <div class="footer">

        Mood-to-Story AI • Powered by Gemini

    </div>

</div>


<script>

async function generateStory() {

    const output =
        document.getElementById("output");

    const button =
        document.getElementById("createButton");

    const mood =
        document.getElementById("mood").value;

    const genre =
        document.getElementById("genre").value;

    const style =
        document.getElementById("style").value;

    const idea =
        document.getElementById("idea").value;


    button.disabled = true;

    button.innerHTML =
        "✨ Creating your story...";


    output.innerHTML = `
        <div class="loading">
            🌙 Creating your story and illustration...<br>
            <small>This may take a little while.</small>
        </div>
    `;


    try {

        const formData =
            new URLSearchParams();

        formData.append("mood", mood);

        formData.append("genre", genre);

        formData.append("style", style);

        formData.append("idea", idea);


        const response =
            await fetch(
                "/generate",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/x-www-form-urlencoded"
                    },

                    body: formData
                }
            );


        const data =
            await response.json();


        if (!response.ok || data.error) {

            throw new Error(
                data.error ||
                "Unable to generate the story."
            );
        }


        let imageHTML = "";

        if (data.image) {

            imageHTML = `
                <img
                    class="story-image"
                    src="data:${data.mime};base64,${data.image}"
                    alt="AI generated story illustration"
                >
            `;

        }


        output.innerHTML = `

            <div class="result">

                <div class="mood-badge">

                    ${data.emoji}

                    Mood:
                    ${escapeHTML(data.mood)}

                </div>


                ${imageHTML}


                <div class="story-box">

                    <div class="story-title">

                        📖 ${escapeHTML(data.title)}

                    </div>


                    <div class="story-text">

                        ${escapeHTML(data.story)}

                    </div>

                </div>

            </div>
        `;


    } catch (error) {

        output.innerHTML = `

            <div class="error">

                ❌ ${escapeHTML(error.message)}

            </div>

        `;

    } finally {

        button.disabled = false;

        button.innerHTML =
            "✨ Create My Story";

    }

}


function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text || "";

    return div.innerHTML;

}

</script>

</body>

</html>
"""


# =========================================================
# HOME
# =========================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
def home():

    return HTML


# =========================================================
# GENERATE STORY
# =========================================================

@app.post("/generate")
def generate(
    mood: str = Form(...),
    genre: str = Form(...),
    style: str = Form(...),
    idea: str = Form("")
):

    try:

        # =====================================
        # 1. GENERATE STORY
        # =====================================

        story_result = make_story(
            mood,
            genre,
            idea
        )


        # =====================================
        # 2. EXTRACT TITLE AND STORY
        # =====================================

        title = "Your Magical Story"

        story = story_result


        if "TITLE:" in story_result:

            parts = story_result.split(
                "STORY:",
                1
            )

            title = (
                parts[0]
                .replace("TITLE:", "")
                .strip()
            )

            if len(parts) > 1:

                story = parts[1].strip()


        # Remove accidental formatting
        story = story.replace(
            "STORY:",
            ""
        ).strip()


        # =====================================
        # 3. GENERATE IMAGE
        # =====================================

        image = None
        mime = "image/png"

        try:

            image, mime = make_image(
                story,
                mood,
                genre,
                style
            )

        except Exception as image_error:

            print(
                "IMAGE ERROR:",
                str(image_error)
            )


        # =====================================
        # 4. MOOD INFORMATION
        # =====================================

        config = MOOD_CONFIG.get(
            mood,
            MOOD_CONFIG["Happy"]
        )


        # =====================================
        # 5. RETURN CLEAN JSON
        # =====================================

        return JSONResponse({

            "success": True,

            "title": title,

            "story": story,

            "mood": mood,

            "genre": genre,

            "style": style,

            "emoji": config["emoji"],

            "image": image,

            "mime": mime

        })


    except Exception as e:

        print(
            "GENERATION ERROR:",
            str(e)
        )

        return JSONResponse(

            status_code=500,

            content={
                "success": False,
                "error": str(e)
            }

        )

# =========================================================
# LANGSERVE ROUTE
# =========================================================
#
# IMPORTANT:
# We use /story-agent instead of /agent because
# your previous Render deployment already had /agent.
#

chain = RunnableLambda(
    lambda x: {
        "story": make_story(
            x.get("mood", "Happy"),
            x.get("genre", "Fantasy"),
            x.get("idea", "")
        )
    }
)


try:

    from langserve import add_routes

    add_routes(
        app,
        chain,
        path="/story-agent"
    )

except Exception as e:

    print(
        "LangServe route registration warning:",
        str(e)
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "Mood-to-Story AI"
    }
