import os
import re
import base64
import logging
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from langserve import add_routes
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI

from google import genai
from google.genai import types


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mood_story_ai")


# ============================================================
# API KEY
# ============================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY environment variable is not set."
    )


# ============================================================
# GEMINI CLIENTS
# ============================================================

# Text generation
story_llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.9,
)

# Direct Google GenAI client for image generation
google_client = genai.Client(
    api_key=GOOGLE_API_KEY
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Mood-to-Story AI",
    version="1.0.0",
    description=(
        "AI story generator that transforms moods and ideas "
        "into stories and illustrations."
    )
)


# ============================================================
# STORY GENERATION
# ============================================================

def generate_story(
    mood: str,
    genre: str,
    character: str,
    setting: str,
    topic: str,
    length: str
) -> str:

    length_instruction = {
        "Short": "around 300-400 words",
        "Medium": "around 500-700 words",
        "Long": "around 800-1000 words"
    }.get(length, "around 500-700 words")

    prompt = f"""
You are a creative storyteller.

Create an original, emotionally engaging story using these inputs:

MOOD:
{mood}

GENRE:
{genre}

MAIN CHARACTER:
{character}

SETTING:
{setting}

USER'S IDEA:
{topic}

STORY LENGTH:
{length_instruction}

Requirements:

1. Give the story a beautiful title.
2. Match the emotional tone to the selected mood.
3. Make the story immersive and easy to read.
4. Include a clear beginning, middle and ending.
5. Give the main character personality.
6. Include sensory descriptions.
7. Include dialogue when appropriate.
8. Do not mention that AI created the story.
9. Do not explain the writing process.
10. Do not use markdown headings inside the story.
11. Keep the story suitable for students and general audiences.

Return ONLY:

TITLE:
<story title>

STORY:
<complete story>
"""

    response = story_llm.invoke(prompt)

    content = response.content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif "text" in item:
                    parts.append(item["text"])

        content = "\n".join(parts)

    return str(content).strip()


# ============================================================
# EXTRACT TITLE
# ============================================================

def extract_title(story_text: str) -> str:

    match = re.search(
        r"TITLE:\s*(.+)",
        story_text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return "Your Magical Story"


# ============================================================
# EXTRACT STORY BODY
# ============================================================

def extract_story_body(story_text: str) -> str:

    match = re.search(
        r"STORY:\s*(.*)",
        story_text,
        re.IGNORECASE | re.DOTALL
    )

    if match:
        return match.group(1).strip()

    return story_text.strip()


# ============================================================
# IMAGE PROMPT
# ============================================================

def create_image_prompt(
    story: str,
    mood: str,
    genre: str,
    character: str,
    setting: str,
    art_style: str
) -> str:

    return f"""
Create a beautiful cinematic illustration for this original story.

MOOD:
{mood}

GENRE:
{genre}

CHARACTER:
{character}

SETTING:
{setting}

ART STYLE:
{art_style}

STORY:
{story}

IMAGE REQUIREMENTS:

- Create ONE visually striking storybook illustration.
- Capture the most important emotional moment of the story.
- Make the characters expressive.
- Match the lighting and atmosphere to the mood.
- Clearly show the setting.
- Use rich visual storytelling.
- Keep the image appropriate for students and general audiences.
- Do not add captions.
- Do not add text.
- Do not add logos.
- Do not add watermarks.
- Make it look like professional storybook artwork.
"""


# ============================================================
# IMAGE GENERATION
# ============================================================

def generate_story_image(
    story: str,
    mood: str,
    genre: str,
    character: str,
    setting: str,
    art_style: str
):

    prompt = create_image_prompt(
        story=story,
        mood=mood,
        genre=genre,
        character=character,
        setting=setting,
        art_style=art_style
    )

    try:

        response = google_client.models.generate_content(
            model="gemini-3.1-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

        for part in response.parts:

            if part.inline_data is not None:

                image_bytes = part.inline_data.data

                mime_type = (
                    part.inline_data.mime_type
                    or "image/png"
                )

                encoded = base64.b64encode(
                    image_bytes
                ).decode("utf-8")

                return {
                    "image": encoded,
                    "mime_type": mime_type
                }

        logger.warning(
            "Image generation returned no image."
        )

        return None

    except Exception as e:

        logger.exception(
            "Image generation failed"
        )

        return None


# ============================================================
# MAIN STORYBOOK AGENT
# ============================================================

def run_story_agent(data: Dict[str, Any]) -> Dict[str, Any]:

    mood = str(
        data.get("mood", "Happy")
    ).strip()

    genre = str(
        data.get("genre", "Fantasy")
    ).strip()

    character = str(
        data.get("character", "A student")
    ).strip()

    setting = str(
        data.get("setting", "A magical forest")
    ).strip()

    topic = str(
        data.get(
            "topic",
            "A surprising adventure"
        )
    ).strip()

    length = str(
        data.get("length", "Short")
    ).strip()

    art_style = str(
        data.get(
            "art_style",
            "Cinematic storybook"
        )
    ).strip()

    if not topic:
        topic = "A surprising adventure"

    logger.info(
        "Generating story: mood=%s genre=%s",
        mood,
        genre
    )

    # --------------------------------------------------------
    # STEP 1: STORY
    # --------------------------------------------------------

    story_raw = generate_story(
        mood=mood,
        genre=genre,
        character=character,
        setting=setting,
        topic=topic,
        length=length
    )

    title = extract_title(
        story_raw
    )

    story = extract_story_body(
        story_raw
    )

    # --------------------------------------------------------
    # STEP 2: IMAGE
    # --------------------------------------------------------

    image_result = generate_story_image(
        story=story,
        mood=mood,
        genre=genre,
        character=character,
        setting=setting,
        art_style=art_style
    )

    result = {
        "title": title,
        "story": story,
        "mood": mood,
        "genre": genre,
        "character": character,
        "setting": setting,
        "art_style": art_style,
        "image": None,
        "image_mime_type": None
    }

    if image_result:

        result["image"] = image_result["image"]

        result["image_mime_type"] = (
            image_result["mime_type"]
        )

    return result


# ============================================================
# LANGSERVE INPUT
# ============================================================

def story_chain_input(data):

    if not isinstance(data, dict):

        raise ValueError(
            "Input must be a JSON object."
        )

    return run_story_agent(data)


story_chain = RunnableLambda(
    story_chain_input
)


# ============================================================
# LANGSERVE ROUTE
# ============================================================

add_routes(
    app,
    story_chain,
    path="/agent",
    playground_type="default"
)


# ============================================================
# BEAUTIFUL FRONTEND
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
async def home():

    return """
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Mood-to-Story AI</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    min-height: 100vh;

    font-family:
        Inter,
        Arial,
        Helvetica,
        sans-serif;

    background:
        radial-gradient(
            circle at top left,
            #6c5ce7,
            transparent 35%
        ),
        radial-gradient(
            circle at bottom right,
            #00cec9,
            transparent 35%
        ),
        #0b1020;

    color: white;

    padding: 30px 16px;
}


.container {

    max-width: 1100px;

    margin: auto;
}


.header {

    text-align: center;

    margin-bottom: 30px;
}


.logo {

    font-size: 48px;

    margin-bottom: 8px;
}


h1 {

    margin: 0;

    font-size: 42px;

    font-weight: 800;

    background:
        linear-gradient(
            90deg,
            #ffeaa7,
            #81ecec
        );

    -webkit-background-clip: text;

    -webkit-text-fill-color:
        transparent;
}


.subtitle {

    margin-top: 12px;

    color: #cfd5ff;

    font-size: 17px;
}


.card {

    background:
        rgba(
            255,
            255,
            255,
            0.09
        );

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            0.15
        );

    backdrop-filter:
        blur(20px);

    border-radius: 24px;

    padding: 30px;

    box-shadow:
        0 25px 70px
        rgba(
            0,
            0,
            0,
            0.3
        );
}


.grid {

    display: grid;

    grid-template-columns:
        repeat(
            2,
            1fr
        );

    gap: 18px;
}


.full {

    grid-column:
        1 / -1;
}


label {

    display: block;

    margin-bottom: 8px;

    font-weight: 700;

    color: #f7f7ff;
}


input,
select,
textarea {

    width: 100%;

    padding: 14px 16px;

    border-radius: 12px;

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            0.18
        );

    background:
        rgba(
            0,
            0,
            0,
            0.25
        );

    color: white;

    font-size: 15px;

    outline: none;
}


select option {

    color: black;
}


textarea {

    min-height: 120px;

    resize: vertical;
}


input:focus,
select:focus,
textarea:focus {

    border-color:
        #81ecec;

    box-shadow:
        0 0 0 3px
        rgba(
            129,
            236,
            236,
            0.12
        );
}


.generate {

    width: 100%;

    margin-top: 24px;

    padding: 16px;

    border: none;

    border-radius: 14px;

    font-size: 17px;

    font-weight: 800;

    cursor: pointer;

    color: #151525;

    background:
        linear-gradient(
            90deg,
            #ffeaa7,
            #81ecec
        );

    transition:
        transform .2s,
        box-shadow .2s;
}


.generate:hover {

    transform:
        translateY(-2px);

    box-shadow:
        0 12px 30px
        rgba(
            129,
            236,
            236,
            0.25
        );
}


.generate:disabled {

    opacity: .5;

    cursor:
        not-allowed;

    transform:
        none;
}


.loading {

    display: none;

    text-align: center;

    padding: 30px;

    color: #81ecec;

    font-weight: bold;
}


.result {

    display: none;

    margin-top: 30px;
}


.story-card {

    overflow: hidden;

    background:
        rgba(
            255,
            255,
            255,
            0.08
        );

    border-radius: 24px;

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            0.12
        );
}


.story-image {

    width: 100%;

    max-height: 600px;

    object-fit: cover;

    display: block;
}


.story-content {

    padding: 30px;
}


.story-title {

    font-size: 32px;

    margin:
        0 0 20px;

    color: #ffeaa7;
}


.story-text {

    font-size: 17px;

    line-height: 1.9;

    white-space: pre-wrap;

    color: #f1f3ff;
}


.tags {

    display: flex;

    flex-wrap: wrap;

    gap: 8px;

    margin-bottom: 20px;
}


.tag {

    padding:
        7px 12px;

    border-radius: 30px;

    background:
        rgba(
            129,
            236,
            236,
            0.12
        );

    color:
        #81ecec;

    font-size: 13px;
}


.error {

    margin-top: 20px;

    padding: 15px;

    background:
        rgba(
            255,
            0,
            0,
            0.12
        );

    border:
        1px solid
        rgba(
            255,
            100,
            100,
            .3
        );

    border-radius: 12px;

    color: #ffb3b3;
}


.links {

    text-align: center;

    margin-top: 22px;
}


.links a {

    color:
        #81ecec;

    margin:
        0 10px;

    text-decoration:
        none;

    font-size:
        14px;
}


@media(max-width: 700px) {

    h1 {
        font-size: 32px;
    }

    .grid {
        grid-template-columns:
            1fr;
    }

    .full {
        grid-column:
            auto;
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

<div class="logo">
    ✨
</div>

<h1>
    Mood-to-Story AI
</h1>

<div class="subtitle">
    Turn your mood and imagination into a magical storybook.
</div>

</div>


<div class="card">


<div class="grid">


<div>

<label>
    🎭 Mood
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


<div>

<label>
    📚 Genre
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


<div>

<label>
    👤 Main Character
</label>

<select id="character">

<option>A student</option>
<option>A young hero</option>
<option>A princess</option>
<option>A mysterious traveler</option>
<option>A friendly robot</option>
<option>A magical creature</option>
<option>A detective</option>
<option>A custom character</option>

</select>

</div>


<div>

<label>
    🌍 Setting
</label>

<select id="setting">

<option>A magical forest</option>
<option>A futuristic city</option>
<option>A mysterious school</option>
<option>An enchanted kingdom</option>
<option>Outer space</option>
<option>An underwater world</option>
<option>A small village</option>
<option>A hidden island</option>

</select>

</div>


<div>

<label>
    📖 Story Length
</label>

<select id="length">

<option>Short</option>
<option>Medium</option>
<option>Long</option>

</select>

</div>


<div>

<label>
    🎨 Art Style
</label>

<select id="artStyle">

<option>Cinematic storybook</option>
<option>Anime</option>
<option>Fantasy illustration</option>
<option>Watercolor</option>
<option>Pixar-inspired cartoon</option>
<option>Digital painting</option>
<option>Comic book</option>

</select>

</div>


<div class="full">

<label>
    ✍️ What should the story be about?
</label>

<textarea
    id="topic"
    placeholder="Example: A student discovers a mysterious door behind the school library..."
></textarea>

</div>


</div>


<button
    class="generate"
    id="generateButton"
    onclick="generateStory()"
>
    ✨ Create My Storybook
</button>


<div
    class="loading"
    id="loading"
>
    ✨ Writing your story...<br>
    🎨 Creating your illustration...
</div>


<div
    id="error"
    class="error"
    style="display:none;"
></div>


</div>


<div
    class="result"
    id="result"
>


<div class="story-card">


<img
    id="storyImage"
    class="story-image"
    style="display:none;"
>


<div class="story-content">


<div
    class="tags"
    id="tags"
></div>


<h2
    class="story-title"
    id="storyTitle"
></h2>


<div
    class="story-text"
    id="storyText"
></div>


</div>

</div>


</div>


<div class="links">

<a
    href="/docs"
    target="_blank"
>
    API Docs
</a>

<a
    href="/agent/playground/"
    target="_blank"
>
    LangServe Playground
</a>

<a
    href="/health"
    target="_blank"
>
    Health
</a>

</div>


</div>


<script>


async function generateStory() {

    const button =
        document.getElementById(
            "generateButton"
        );

    const loading =
        document.getElementById(
            "loading"
        );

    const result =
        document.getElementById(
            "result"
        );

    const error =
        document.getElementById(
            "error"
        );


    const mood =
        document.getElementById(
            "mood"
        ).value;

    const genre =
        document.getElementById(
            "genre"
        ).value;

    const character =
        document.getElementById(
            "character"
        ).value;

    const setting =
        document.getElementById(
            "setting"
        ).value;

    const length =
        document.getElementById(
            "length"
        ).value;

    const artStyle =
        document.getElementById(
            "artStyle"
        ).value;

    const topic =
        document.getElementById(
            "topic"
        ).value.trim();


    button.disabled = true;

    loading.style.display =
        "block";

    result.style.display =
        "none";

    error.style.display =
        "none";


    try {

        const response =
            await fetch(
                "/create-story",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            mood:
                                mood,

                            genre:
                                genre,

                            character:
                                character,

                            setting:
                                setting,

                            topic:
                                topic,

                            length:
                                length,

                            art_style:
                                artStyle
                        })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Something went wrong."
            );

        }


        document.getElementById(
            "storyTitle"
        ).textContent =
            data.title;


        document.getElementById(
            "storyText"
        ).textContent =
            data.story;


        document.getElementById(
            "tags"
        ).innerHTML =

            `<span class="tag">
                ${escapeHtml(data.mood)}
            </span>

            <span class="tag">
                ${escapeHtml(data.genre)}
            </span>

            <span class="tag">
                ${escapeHtml(data.art_style)}
            </span>`;


        const image =
            document.getElementById(
                "storyImage"
            );


        if (
            data.image &&
            data.image_mime_type
        ) {

            image.src =
                "data:" +
                data.image_mime_type +
                ";base64," +
                data.image;

            image.style.display =
                "block";

        } else {

            image.style.display =
                "none";

        }


        result.style.display =
            "block";


        result.scrollIntoView({
            behavior: "smooth"
        });


    }

    catch (err) {

        console.error(err);

        error.textContent =
            "Error: " +
            err.message;

        error.style.display =
            "block";

    }

    finally {

        button.disabled =
            false;

        loading.style.display =
            "none";

    }

}


function escapeHtml(text) {

    const div =
        document.createElement(
            "div"
        );

    div.textContent =
        text;

    return div.innerHTML;

}


</script>


</body>

</html>
"""


# ============================================================
# CREATE STORY ENDPOINT
# ============================================================

@app.post("/create-story")
async def create_story(data: Dict[str, Any]):

    try:

        result = run_story_agent(data)

        return JSONResponse(
            content=result
        )

    except Exception as e:

        logger.exception(
            "Story generation failed"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "Mood-to-Story AI"
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.getenv(
            "PORT",
            "8000"
        )
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
