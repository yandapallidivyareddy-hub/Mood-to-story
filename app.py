import os
import base64
import html
import traceback

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from google import genai
from google.genai import types


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Mood-to-Story AI",
    description="Generate magical stories and illustrations with Gemini"
)


# =========================================================
# GEMINI CLIENT
# =========================================================

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY or GOOGLE_API_KEY is not configured in Render."
    )

client = genai.Client(api_key=API_KEY)


# =========================================================
# MODELS
# =========================================================

# Text model
TEXT_MODEL = "gemini-3.5-flash"

# Image model
IMAGE_MODEL = "gemini-3.1-flash-image"


# =========================================================
# REQUEST MODEL
# =========================================================

class StoryRequest(BaseModel):
    mood: str = "Happy"
    genre: str = "Fantasy"
    style: str = "Cinematic Storybook"
    idea: str = ""


# =========================================================
# STORY GENERATION
# =========================================================

def make_story(mood: str, genre: str, idea: str):

    prompt = f"""
You are a children's story writer.

Create a magical short story based on:

Mood: {mood}
Genre: {genre}
Story idea: {idea}

IMPORTANT RULES:

- Use very simple English.
- Use short and clear sentences.
- Make the story suitable for students and children.
- Do not use complicated vocabulary.
- Create a clear beginning, middle and ending.
- Make the story imaginative and emotional.
- Include a positive ending.
- Write around 600-800 words.
- Give the story a beautiful title.
- Do NOT include markdown symbols.
- Do NOT include HTML.
"""

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt
    )

    return response.text.strip()


# =========================================================
# IMAGE GENERATION
# =========================================================

def make_image(mood: str, genre: str, style: str, idea: str, story: str):

    image_prompt = f"""
Create a beautiful illustrated children's storybook scene.

Story idea:
{idea}

Mood:
{mood}

Genre:
{genre}

Illustration style:
{style}

Story:
{story[:4000]}

Create ONE main cinematic illustration that represents the most magical
and important moment of the story.

Requirements:

- Children's storybook illustration
- Beautiful fantasy atmosphere
- Cinematic composition
- Warm magical lighting
- Rich details
- Friendly and imaginative
- Expressive characters
- Suitable for children
- No scary or disturbing elements
- No text
- No words
- No letters
- No watermark-like text
- Landscape composition
- 16:9 aspect ratio
"""

    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=image_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="16:9",
                image_size="1K"
            )
        )
    )

    image_data = None
    image_mime = "image/png"

    # Look through Gemini response parts
    if response.candidates:

        for candidate in response.candidates:

            if not candidate.content:
                continue

            for part in candidate.content.parts:

                # Image returned by Gemini
                if getattr(part, "inline_data", None):

                    image_data = part.inline_data.data

                    if part.inline_data.mime_type:
                        image_mime = part.inline_data.mime_type

                    break

            if image_data:
                break

    if not image_data:
        raise RuntimeError(
            "Gemini generated the story but did not return an image."
        )

    # Convert bytes to Base64 for browser
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    return {
        "mime_type": image_mime,
        "base64": image_base64
    }


# =========================================================
# HOME PAGE
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home():

    return """
<!DOCTYPE html>
<html lang="en">

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
    font-family: Arial, Helvetica, sans-serif;

    background:
        radial-gradient(circle at top left, #243b70, transparent 40%),
        radial-gradient(circle at bottom right, #14213d, transparent 40%),
        #07152e;

    color: white;
    min-height: 100vh;
}

.container {
    width: 92%;
    max-width: 1100px;
    margin: auto;
    padding: 40px 0;
}

.hero {
    text-align: center;
    margin-bottom: 35px;
}

.hero-icon {
    font-size: 55px;
}

h1 {
    margin: 10px 0;
    font-size: 42px;
    color: #ffd43b;
}

.subtitle {
    color: #d7def2;
    font-size: 18px;
}

.card {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 22px;
    padding: 30px;
    backdrop-filter: blur(12px);
    box-shadow: 0 20px 60px rgba(0,0,0,0.35);
}

.form-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
}

label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
    color: #ffd43b;
}

select,
textarea {

    width: 100%;

    padding: 14px;

    border-radius: 12px;

    border: 1px solid #40557f;

    background: #101f3d;

    color: white;

    font-size: 15px;
}

textarea {
    min-height: 120px;
    resize: vertical;
}

.full {
    grid-column: 1 / -1;
}

button {

    width: 100%;

    margin-top: 25px;

    padding: 17px;

    border: none;

    border-radius: 14px;

    background: #ffd43b;

    color: #07152e;

    font-size: 18px;

    font-weight: bold;

    cursor: pointer;

    transition: 0.2s;
}

button:hover {
    transform: translateY(-2px);
    background: #ffe477;
}

button:disabled {
    opacity: 0.6;
    cursor: wait;
}

.loading {
    display: none;
    text-align: center;
    margin: 25px 0;
    color: #ffd43b;
}

.result {
    margin-top: 35px;
    display: none;
}

.story-title {
    color: #ffd43b;
    font-size: 30px;
    margin-bottom: 15px;
}

.story {
    white-space: pre-wrap;
    line-height: 1.8;
    font-size: 17px;
    color: #f3f6ff;
}

.image-section {
    margin-top: 35px;
}

.image-section h2 {
    color: #ffd43b;
}

.story-image {
    width: 100%;
    max-width: 100%;
    border-radius: 18px;
    display: block;
    margin-top: 15px;
    box-shadow: 0 15px 50px rgba(0,0,0,0.45);
}

.error {
    background: rgba(255, 70, 70, 0.15);
    border: 1px solid rgba(255, 100, 100, 0.4);
    padding: 15px;
    border-radius: 12px;
    color: #ffb3b3;
    margin-top: 20px;
    display: none;
}

.footer {
    text-align: center;
    margin-top: 40px;
    color: #9eacce;
}

@media(max-width: 800px) {

    .form-grid {
        grid-template-columns: 1fr;
    }

    h1 {
        font-size: 32px;
    }

    .full {
        grid-column: auto;
    }
}

</style>

</head>


<body>

<div class="container">

    <div class="hero">

        <div class="hero-icon">📖✨</div>

        <h1>Mood-to-Story AI</h1>

        <div class="subtitle">
            Transform your mood and imagination into a magical illustrated story.
        </div>

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
                    <option>Disney-like Cartoon</option>
                    <option>Watercolor Storybook</option>
                    <option>Fantasy Digital Art</option>
                    <option>Anime Storybook</option>
                    <option>3D Animated Story</option>

                </select>

            </div>


            <div class="full">

                <label>
                    💡 What should your story be about?
                </label>

                <textarea id="idea"
                    placeholder="Example: A student discovers a magical library where every book he reads turns into reality. Use simple words."></textarea>

            </div>

        </div>


        <button id="generateBtn"
                onclick="generateStory()">

            ✨ Create My Story

        </button>


        <div class="loading" id="loading">

            ✨ Creating your story and magical illustration...
            <br>
            <br>
            This may take a little while.

        </div>


        <div class="error" id="error"></div>


        <div class="result" id="result">

            <div id="moodLabel"></div>

            <div class="story-title" id="storyTitle"></div>

            <div class="story" id="storyText"></div>


            <div class="image-section">

                <h2>🎨 Story Illustration</h2>

                <img id="storyImage"
                     class="story-image"
                     alt="AI generated story illustration">

            </div>

        </div>

    </div>


    <div class="footer">

        Mood-to-Story AI • Powered by Gemini ✨

    </div>

</div>


<script>

async function generateStory() {

    const mood =
        document.getElementById("mood").value;

    const genre =
        document.getElementById("genre").value;

    const style =
        document.getElementById("style").value;

    const idea =
        document.getElementById("idea").value.trim();


    if (!idea) {

        alert("Please enter a story idea.");

        return;
    }


    const button =
        document.getElementById("generateBtn");

    const loading =
        document.getElementById("loading");

    const result =
        document.getElementById("result");

    const errorBox =
        document.getElementById("error");


    button.disabled = true;

    loading.style.display = "block";

    result.style.display = "none";

    errorBox.style.display = "none";


    try {

        const response = await fetch("/generate", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                mood: mood,
                genre: genre,
                style: style,
                idea: idea

            })

        });


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail || "Something went wrong."
            );

        }


        document.getElementById("moodLabel").innerHTML =
            "😊 Mood: " + data.mood;


        document.getElementById("storyTitle").innerText =
            data.title;


        document.getElementById("storyText").innerText =
            data.story;


        // IMPORTANT:
        // Display Gemini-generated image

        document.getElementById("storyImage").src =
            "data:" +
            data.image_mime +
            ";base64," +
            data.image;


        result.style.display = "block";


        // Scroll to result

        result.scrollIntoView({
            behavior: "smooth"
        });

    }

    catch(error) {

        console.error(error);

        errorBox.innerText =
            "❌ " + error.message;

        errorBox.style.display = "block";

    }

    finally {

        button.disabled = false;

        loading.style.display = "none";

    }

}

</script>

</body>

</html>
"""


# =========================================================
# GENERATE ENDPOINT
# =========================================================

@app.post("/generate")
def generate(request: StoryRequest):

    try:

        print("Generating story...")

        print("Mood:", request.mood)
        print("Genre:", request.genre)
        print("Style:", request.style)


        # ---------------------------------------------
        # Generate story
        # ---------------------------------------------

        story = make_story(
            request.mood,
            request.genre,
            request.idea
        )


        print("Story generated successfully.")


        # ---------------------------------------------
        # Generate image
        # ---------------------------------------------

        print("Generating illustration...")

        image = make_image(
            request.mood,
            request.genre,
            request.style,
            request.idea,
            story
        )


        print("Illustration generated successfully.")


        # ---------------------------------------------
        # Extract title
        # ---------------------------------------------

        lines = [
            line.strip()
            for line in story.splitlines()
            if line.strip()
        ]


        title = "Your Magical Story"

        if lines:

            first_line = lines[0]

            first_line = first_line.replace(
                "#", ""
            ).strip()

            if len(first_line) < 100:

                title = first_line

                story_without_title = "\n".join(
                    lines[1:]
                )

            else:

                story_without_title = story

        else:

            story_without_title = story


        return JSONResponse({

            "success": True,

            "mood": request.mood,

            "genre": request.genre,

            "style": request.style,

            "title": title,

            "story": story_without_title,

            "image": image["base64"],

            "image_mime": image["mime_type"]

        })


    except Exception as e:

        print("\nERROR:")
        traceback.print_exc()

        return JSONResponse(

            status_code=500,

            content={
                "success": False,
                "detail": str(e)
            }

        )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "text_model": TEXT_MODEL,
        "image_model": IMAGE_MODEL
    }
