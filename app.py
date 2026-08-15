import os
import re
import base64
import html

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse

from google import genai
from google.genai import types


# ============================================================
# CONFIGURATION
# ============================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY environment variable is not set."
    )


# Gemini client
client = genai.Client(api_key=GOOGLE_API_KEY)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Mood-to-Story AI",
    description="Create mood-based illustrated stories using Gemini."
)


# ============================================================
# MOOD CONFIGURATION
# ============================================================

MOOD_CONFIG = {

    "Happy": {
        "emoji": "😊",
        "tone": (
            "joyful, bright, playful, warm, positive, "
            "hopeful and full of wonder"
        ),
        "visual": (
            "warm sunlight, bright colors, smiling characters, "
            "magical glowing atmosphere"
        )
    },

    "Sad": {
        "emoji": "😢",
        "tone": (
            "gentle, emotional, thoughtful and touching, "
            "but ending with hope"
        ),
        "visual": (
            "soft blue tones, gentle rain, emotional atmosphere, "
            "warm light appearing at the end"
        )
    },

    "Excited": {
        "emoji": "🤩",
        "tone": (
            "energetic, thrilling, adventurous, fast-moving "
            "and full of surprises"
        ),
        "visual": (
            "dynamic action, bright colors, magical sparks, "
            "dramatic movement"
        )
    },

    "Peaceful": {
        "emoji": "😌",
        "tone": (
            "calm, relaxing, gentle, comforting and beautiful"
        ),
        "visual": (
            "soft sunlight, pastel colors, peaceful landscape, "
            "gentle clouds and calm atmosphere"
        )
    },

    "Romantic": {
        "emoji": "❤️",
        "tone": (
            "warm, sweet, emotional, caring and hopeful"
        ),
        "visual": (
            "soft sunset, warm golden light, flowers, "
            "gentle magical atmosphere"
        )
    },

    "Mysterious": {
        "emoji": "🔮",
        "tone": (
            "curious, mysterious, suspenseful and magical"
        ),
        "visual": (
            "moonlight, glowing objects, mysterious shadows, "
            "ancient places and magical atmosphere"
        )
    },

    "Scared": {
        "emoji": "😨",
        "tone": (
            "slightly spooky, suspenseful and mysterious, "
            "but suitable for young readers and ending safely"
        ),
        "visual": (
            "dark blue night, mist, mysterious shadows, "
            "glowing lights and safe magical fantasy"
        )
    },

    "Angry": {
        "emoji": "😡",
        "tone": (
            "intense, emotional and energetic, showing conflict "
            "that is solved in a positive way"
        ),
        "visual": (
            "dramatic sky, strong lighting, energetic movement, "
            "red and orange magical effects"
        )
    },

    "Hopeful": {
        "emoji": "🌱",
        "tone": (
            "inspiring, positive, emotional and full of hope"
        ),
        "visual": (
            "sunrise, golden light, growing plants, "
            "bright sky and uplifting atmosphere"
        )
    },

    "Adventurous": {
        "emoji": "⚔️",
        "tone": (
            "brave, exciting, imaginative and full of discovery"
        ),
        "visual": (
            "fantasy landscapes, mountains, magical paths, "
            "adventure and exploration"
        )
    }
}


# ============================================================
# STORY GENERATION
# ============================================================

def make_story(mood: str, genre: str, idea: str):

    config = MOOD_CONFIG.get(
        mood,
        MOOD_CONFIG["Happy"]
    )

    tone = config["tone"]

    if not idea.strip():
        idea = (
            "Create an original story based on the selected "
            "mood and genre."
        )

    prompt = f"""
You are a professional children's story writer.

Create a beautiful original {genre} story.

SELECTED MOOD:
{mood}

EMOTIONAL TONE:
{tone}

STORY IDEA:
{idea}

IMPORTANT WRITING RULES:

1. Use VERY SIMPLE English.
2. Use short and easy sentences.
3. Avoid difficult words.
4. Write for students around 10-14 years old.
5. Make the story imaginative and enjoyable.
6. The selected mood must be clearly felt throughout the story.
7. Include a clear beginning, middle and ending.
8. Use vivid scenes that can easily be illustrated.
9. Do not mention AI.
10. Do not use complicated vocabulary.
11. Write approximately 400-500 words.

Return ONLY this format:

TITLE: <short creative title>

STORY:
<story paragraphs>
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        # Google GenAI normally provides response.text
        story_text = getattr(response, "text", None)

        if not story_text:

            # Fallback extraction
            parts = []

            if getattr(response, "candidates", None):

                for candidate in response.candidates:

                    content = getattr(
                        candidate,
                        "content",
                        None
                    )

                    if content:

                        for part in getattr(
                            content,
                            "parts",
                            []
                        ):

                            text = getattr(
                                part,
                                "text",
                                None
                            )

                            if text:
                                parts.append(text)

            story_text = "\n".join(parts)

        if not story_text:
            raise RuntimeError(
                "Gemini returned an empty story."
            )

        return story_text.strip()

    except Exception as e:

        print(
            "STORY GENERATION ERROR:",
            repr(e)
        )

        raise RuntimeError(
            f"Story generation failed: {str(e)}"
        )


# ============================================================
# CLEAN STORY
# ============================================================

def clean_story(raw_story: str):

    raw_story = raw_story.strip()

    title = "Your Magical Story"

    # Extract title
    title_match = re.search(
        r"TITLE\s*:\s*(.+?)(?:\n|$)",
        raw_story,
        re.IGNORECASE
    )

    if title_match:

        title = title_match.group(1).strip()

        raw_story = re.sub(
            r"TITLE\s*:\s*.+?(?:\n|$)",
            "",
            raw_story,
            count=1,
            flags=re.IGNORECASE
        )

    # Remove STORY label
    raw_story = re.sub(
        r"^\s*STORY\s*:\s*",
        "",
        raw_story,
        flags=re.IGNORECASE
    )

    # Remove accidental markdown
    raw_story = raw_story.replace(
        "**",
        ""
    )

    raw_story = raw_story.replace(
        "*",
        ""
    )

    raw_story = raw_story.replace(
        "```",
        ""
    )

    # Normalize excessive whitespace
    raw_story = re.sub(
        r"\n{3,}",
        "\n\n",
        raw_story
    )

    return title.strip(), raw_story.strip()


# ============================================================
# IMAGE GENERATION
# ============================================================

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

    visual = config["visual"]

    # Only use the beginning of the story so that the
    # image prompt remains focused.
    story_summary = story[:2500]

    image_prompt = f"""
Create a beautiful illustrated storybook scene.

STORY:
{story_summary}

MOOD:
{mood}

GENRE:
{genre}

VISUAL MOOD:
{visual}

ILLUSTRATION STYLE:
{style}

IMPORTANT:

- Create ONE main cinematic scene from the story.
- Make the main character clearly visible.
- Make the image colorful and detailed.
- The image should feel like a children's storybook.
- Keep the image family-friendly.
- Do NOT put text, letters, captions or words inside the image.
- Do NOT create a book cover.
- Create an actual scene from the story.
- Make the image visually magical and engaging.
"""

    try:

        print(
            f"Generating image using "
            f"gemini-3.1-flash-image..."
        )

        # Current Gemini image-generation API
        interaction = client.interactions.create(
            model="gemini-3.1-flash-image",
            input=image_prompt
        )

        output_image = getattr(
            interaction,
            "output_image",
            None
        )

        if not output_image:

            raise RuntimeError(
                "Gemini completed the request but "
                "did not return an image."
            )

        image_data = getattr(
            output_image,
            "data",
            None
        )

        if not image_data:

            raise RuntimeError(
                "Gemini returned an image object "
                "without image data."
            )

        # The Interactions API returns base64 image data
        if isinstance(image_data, bytes):

            encoded = base64.b64encode(
                image_data
            ).decode("utf-8")

        else:

            encoded = str(image_data)

        print("IMAGE GENERATION SUCCESS")

        return encoded, "image/png", None

    except Exception as e:

        error_message = str(e)

        print(
            "IMAGE GENERATION ERROR:",
            repr(e)
        )

        return (
            None,
            None,
            error_message
        )


# ============================================================
# HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Mood-to-Story AI</title>


<style>

/* =========================================================
   GLOBAL
========================================================= */

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        Inter,
        Arial,
        Helvetica,
        sans-serif;

    background:
        radial-gradient(
            circle at top,
            #243b64 0%,
            #111827 45%,
            #080d18 100%
        );

    color: #ffffff;

    min-height: 100vh;
}


/* =========================================================
   HEADER
========================================================= */

.header {

    text-align: center;

    padding: 45px 20px 25px;
}

.logo {

    font-size: 48px;

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
            #fde68a,
            #f59e0b
        );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;
}

.header p {

    color: #cbd5e1;

    font-size: 17px;

    margin-top: 12px;
}


/* =========================================================
   MAIN CONTAINER
========================================================= */

.container {

    max-width: 1050px;

    margin: auto;

    padding: 20px;
}


/* =========================================================
   CARD
========================================================= */

.card {

    background:
        rgba(31, 41, 55, 0.88);

    border:
        1px solid
        rgba(255,255,255,0.08);

    border-radius: 24px;

    padding: 30px;

    box-shadow:
        0 25px 70px
        rgba(0,0,0,0.35);

    backdrop-filter:
        blur(12px);

    margin-bottom: 25px;
}


/* =========================================================
   FORM GRID
========================================================= */

.form-grid {

    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 18px;
}

.field {

    display: flex;

    flex-direction: column;
}

.field.full {

    grid-column:
        1 / -1;
}


label {

    font-weight: 700;

    margin-bottom: 8px;

    color: #f8fafc;
}


select,
textarea {

    width: 100%;

    border: 1px solid
        #475569;

    background: #111827;

    color: white;

    padding: 14px 15px;

    border-radius: 12px;

    outline: none;

    font-size: 15px;

    transition: 0.2s;
}


select:focus,
textarea:focus {

    border-color: #f59e0b;

    box-shadow:
        0 0 0 3px
        rgba(245,158,11,0.15);
}


textarea {

    min-height: 120px;

    resize: vertical;
}


/* =========================================================
   BUTTON
========================================================= */

.generate-btn {

    width: 100%;

    margin-top: 22px;

    padding: 16px;

    border: none;

    border-radius: 14px;

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

    transition:
        transform 0.2s,
        box-shadow 0.2s;
}


.generate-btn:hover {

    transform:
        translateY(-2px);

    box-shadow:
        0 12px 30px
        rgba(245,158,11,0.25);
}


.generate-btn:disabled {

    opacity: 0.65;

    cursor: wait;

    transform: none;
}


/* =========================================================
   LOADING
========================================================= */

.loading {

    display: none;

    text-align: center;

    padding: 30px;
}


.spinner {

    width: 42px;

    height: 42px;

    border:
        4px solid
        #334155;

    border-top-color:
        #f59e0b;

    border-radius: 50%;

    animation:
        spin 1s linear infinite;

    margin:
        0 auto 15px;
}


@keyframes spin {

    to {
        transform: rotate(360deg);
    }

}


/* =========================================================
   STORY RESULT
========================================================= */

.result {

    display: none;
}


.mood-badge {

    display: inline-flex;

    align-items: center;

    gap: 8px;

    background:
        rgba(245,158,11,0.12);

    border:
        1px solid
        rgba(245,158,11,0.35);

    color: #fbbf24;

    padding: 8px 14px;

    border-radius: 999px;

    font-size: 14px;

    font-weight: 700;

    margin-bottom: 15px;
}


.story-title {

    font-family:
        Georgia,
        serif;

    font-size: 38px;

    line-height: 1.2;

    color: #fbbf24;

    margin:
        0 0 22px;
}


/* =========================================================
   IMAGE
========================================================= */

.image-wrapper {

    width: 100%;

    overflow: hidden;

    border-radius: 20px;

    margin-bottom: 30px;

    background: #0f172a;

    border:
        1px solid
        rgba(255,255,255,0.08);
}


.story-image {

    width: 100%;

    display: block;

    max-height: 620px;

    object-fit: cover;
}


/* =========================================================
   STORY TEXT
========================================================= */

.story-text {

    max-width: 850px;

    margin: auto;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 19px;

    line-height: 1.9;

    color: #e5e7eb;
}


.story-text p {

    margin:
        0 0 20px;
}


.divider {

    height: 1px;

    background:
        linear-gradient(
            90deg,
            transparent,
            #475569,
            transparent
        );

    margin:
        30px 0;
}


/* =========================================================
   ERROR
========================================================= */

.error {

    display: none;

    background:
        rgba(127,29,29,0.35);

    border:
        1px solid
        rgba(248,113,113,0.4);

    color: #fecaca;

    padding: 16px;

    border-radius: 12px;

    margin-top: 20px;

    line-height: 1.6;
}


/* =========================================================
   FOOTER
========================================================= */

.footer {

    text-align: center;

    color: #64748b;

    padding:
        20px;

    font-size: 14px;
}


/* =========================================================
   RESPONSIVE
========================================================= */

@media(max-width: 750px) {

    .form-grid {

        grid-template-columns: 1fr;
    }

    .field.full {

        grid-column:
            auto;
    }

    .header h1 {

        font-size: 32px;
    }

    .story-title {

        font-size: 30px;
    }

    .story-text {

        font-size: 17px;
    }

    .card {

        padding: 20px;
    }

}

</style>

</head>


<body>


<header class="header">

    <div class="logo">
        📖✨
    </div>

    <h1>
        Mood-to-Story AI
    </h1>

    <p>
        Transform your mood and imagination
        into a magical illustrated story.
    </p>

</header>


<main class="container">


<!-- =====================================================
     INPUT CARD
===================================================== -->

<section class="card">

    <div class="form-grid">


        <div class="field">

            <label>
                🎭 Choose Your Mood
            </label>

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


        <div class="field">

            <label>
                📚 Choose Genre
            </label>

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


        <div class="field">

            <label>
                🎨 Illustration Style
            </label>

            <select id="style">

                <option>
                    Cinematic Storybook
                </option>

                <option>
                    Colorful Children's Book
                </option>

                <option>
                    Anime
                </option>

                <option>
                    Watercolor
                </option>

                <option>
                    Fantasy Art
                </option>

                <option>
                    3D Animated
                </option>

            </select>

        </div>


        <div class="field full">

            <label>
                💡 What should your story be about?
            </label>

            <textarea
                id="idea"
                placeholder="Example: A student discovers a magical library where every book he reads turns into reality. Use simple words."
            ></textarea>

        </div>

    </div>


    <button
        class="generate-btn"
        id="generateBtn"
        onclick="generateStory()"
    >

        ✨ Create My Story

    </button>


    <div
        class="error"
        id="error"
    ></div>


</section>


<!-- =====================================================
     LOADING
===================================================== -->

<div
    class="card loading"
    id="loading"
>

    <div class="spinner"></div>

    <strong>
        Creating your magical story...
    </strong>

    <p>
        Gemini is writing your story
        and creating its illustration.
    </p>

</div>


<!-- =====================================================
     RESULT
===================================================== -->

<section
    class="card result"
    id="result"
>

    <div
        class="mood-badge"
        id="moodBadge"
    ></div>


    <h2
        class="story-title"
        id="storyTitle"
    ></h2>


    <div
        class="image-wrapper"
        id="imageWrapper"
    >

        <img
            class="story-image"
            id="storyImage"
            alt="AI generated story illustration"
        >

    </div>


    <div class="divider"></div>


    <article
        class="story-text"
        id="storyText"
    ></article>

</section>


</main>


<footer class="footer">

    Mood-to-Story AI
    • Powered by Gemini

</footer>


<script>


// ========================================================
// GENERATE STORY
// ========================================================

async function generateStory() {


    const mood =
        document.getElementById("mood").value;


    const genre =
        document.getElementById("genre").value;


    const style =
        document.getElementById("style").value;


    const idea =
        document.getElementById("idea").value;


    const button =
        document.getElementById("generateBtn");


    const loading =
        document.getElementById("loading");


    const result =
        document.getElementById("result");


    const error =
        document.getElementById("error");


    // Reset UI

    error.style.display = "none";

    result.style.display = "none";

    loading.style.display = "block";

    button.disabled = true;

    button.innerHTML =
        "⏳ Creating Your Story...";


    try {


        const body =
            new URLSearchParams();


        body.append(
            "mood",
            mood
        );


        body.append(
            "genre",
            genre
        );


        body.append(
            "style",
            style
        );


        body.append(
            "idea",
            idea
        );


        const response =
            await fetch(
                "/generate",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/x-www-form-urlencoded"
                    },

                    body: body
                }
            );


        const data =
            await response.json();


        if (!response.ok ||
            !data.success) {

            throw new Error(
                data.error ||
                "Something went wrong."
            );
        }


        // ==================================================
        // TITLE
        // ==================================================

        document.getElementById(
            "storyTitle"
        ).textContent =
            data.title;


        // ==================================================
        // MOOD
        // ==================================================

        document.getElementById(
            "moodBadge"
        ).textContent =
            `${data.emoji} Mood: ${data.mood}`;


        // ==================================================
        // STORY
        // ==================================================

        const storyText =
            document.getElementById(
                "storyText"
            );


        // Escape HTML for safety

        const safeStory =
            escapeHtml(data.story);


        // Convert paragraphs to <p>

        storyText.innerHTML =
            safeStory
                .split(/\n\s*\n/)
                .filter(
                    p => p.trim()
                )
                .map(
                    p =>
                        `<p>${p.trim()}</p>`
                )
                .join("");


        // ==================================================
        // IMAGE
        // ==================================================

        const imageWrapper =
            document.getElementById(
                "imageWrapper"
            );


        const image =
            document.getElementById(
                "storyImage"
            );


        if (data.image) {

            image.src =
                `data:${data.mime};base64,${data.image}`;

            image.alt =
                `${data.mood} story illustration`;

            imageWrapper.style.display =
                "block";

        } else {

            imageWrapper.style.display =
                "none";

            console.warn(
                "Image was not generated:",
                data.image_error
            );
        }


        // ==================================================
        // SHOW RESULT
        // ==================================================

        result.style.display =
            "block";


        result.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });


    } catch (err) {


        console.error(err);


        error.innerHTML =
            `<strong>⚠️ Generation Error</strong><br><br>
             ${escapeHtml(err.message)}`;


        error.style.display =
            "block";


    } finally {


        loading.style.display =
            "none";


        button.disabled =
            false;


        button.innerHTML =
            "✨ Create My Story";

    }

}


// ========================================================
// ESCAPE HTML
// ========================================================

function escapeHtml(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text;

    return div.innerHTML;
}


</script>


</body>

</html>
"""


# ============================================================
# HOME
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
def home():

    return HTML


# ============================================================
# GENERATE ENDPOINT
# ============================================================

@app.post("/generate")
def generate(

    mood: str = Form(...),

    genre: str = Form(...),

    style: str = Form(...),

    idea: str = Form("")

):

    try:

        # ----------------------------------------------------
        # STORY
        # ----------------------------------------------------

        raw_story = make_story(
            mood,
            genre,
            idea
        )


        title, story = clean_story(
            raw_story
        )


        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        image = None

        mime = "image/png"

        image_error = None


        image, mime, image_error = make_image(
            story,
            mood,
            genre,
            style
        )


        # ----------------------------------------------------
        # MOOD
        # ----------------------------------------------------

        mood_config = MOOD_CONFIG.get(
            mood,
            MOOD_CONFIG["Happy"]
        )


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return JSONResponse({

            "success": True,

            "title": title,

            "story": story,

            "mood": mood,

            "genre": genre,

            "style": style,

            "emoji":
                mood_config["emoji"],

            "image": image,

            "mime":
                mime,

            "image_error":
                image_error

        })


    except Exception as e:

        print(
            "GENERATION ERROR:",
            repr(e)
        )

        return JSONResponse(

            status_code=500,

            content={

                "success": False,

                "error": str(e)

            }

        )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {

        "status": "healthy",

        "service":
            "Mood-to-Story AI"

    }
