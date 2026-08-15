import os
import re

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Mood-to-Story AI",
    description="Creative AI story generator powered by Gemini",
    version="1.0.0"
)


# ============================================================
# GEMINI
# ============================================================

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY or GEMINI_API_KEY is not configured."
    )


# IMPORTANT:
# Do not use the old gemini-2.5-flash model that caused the 404.
#
# Set the model through Render environment variable:
# GEMINI_MODEL
#
# Example:
# GEMINI_MODEL=gemini-3-flash-preview

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3-flash-preview"
)


llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=API_KEY,
    temperature=0.9,
    max_output_tokens=2500
)


# ============================================================
# REQUEST MODEL
# ============================================================

class StoryRequest(BaseModel):
    mood: str
    genre: str
    idea: str


# ============================================================
# STORY GENERATOR
# ============================================================

def clean_story(text: str) -> str:

    if not text:
        return "✨ Something magical went wrong. Please try again."

    # Remove accidental markdown code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Remove unwanted JSON-like wrappers
    text = text.replace("{'type': 'text', 'text':", "")
    text = text.replace('"type": "text"', "")
    text = text.replace('"text":', "")

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def make_story(mood: str, genre: str, idea: str):

    prompt = f"""
You are a highly creative children's story writer.

Write a beautiful, imaginative and engaging short story.

Story requirements:

Mood: {mood}
Genre: {genre}
Story idea: {idea}

IMPORTANT RULES:

1. Write only the story.
2. Do NOT explain how you created the story.
3. Do NOT mention AI or Gemini.
4. Do NOT generate images.
5. Do NOT include image prompts.
6. Use simple, easy-to-understand English.
7. Make the story creative and magical.
8. Give the story a catchy title.
9. Divide the story into short paragraphs.
10. Naturally include suitable emojis throughout the story.
11. Use approximately 700-1000 words.
12. Make the beginning interesting.
13. Include a small problem or adventure.
14. Build excitement.
15. End with a meaningful or happy conclusion.
16. Keep the story suitable for general audiences.

Use this format:

📖 [Story Title]

[Story]

✨ The End ✨
"""

    response = llm.invoke(prompt)

    content = response.content

    # LangChain/Gemini can sometimes return a list of content blocks.
    if isinstance(content, list):

        parts = []

        for item in content:

            if isinstance(item, dict):

                if item.get("type") == "text":
                    parts.append(item.get("text", ""))

            elif isinstance(item, str):
                parts.append(item)

        content = "\n".join(parts)

    return clean_story(str(content))


# ============================================================
# API
# ============================================================

@app.get("/", response_class=HTMLResponse)
def home():

    return HTML_PAGE


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "Mood-to-Story AI",
        "model": MODEL_NAME
    }


@app.post("/generate")
def generate(request: StoryRequest):

    try:

        story = make_story(
            request.mood,
            request.genre,
            request.idea
        )

        return {
            "success": True,
            "mood": request.mood,
            "genre": request.genre,
            "story": story
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# FRONTEND
# ============================================================

HTML_PAGE = """
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

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        linear-gradient(
            135deg,
            #07152f,
            #102d5c,
            #07152f
        );

    color: white;

    min-height: 100vh;

    padding: 30px 15px;
}


.container {

    width: 100%;

    max-width: 900px;

    margin: auto;
}


.header {

    text-align: center;

    margin-bottom: 30px;
}


.logo {

    font-size: 48px;

    margin-bottom: 5px;
}


h1 {

    margin: 0;

    font-size: 38px;

    color: #ffd43b;
}


.subtitle {

    margin-top: 10px;

    color: #d8e5ff;

    font-size: 17px;
}


.card {

    background: rgba(255,255,255,0.08);

    border: 1px solid rgba(255,255,255,0.15);

    border-radius: 22px;

    padding: 28px;

    backdrop-filter: blur(12px);

    box-shadow:
        0 20px 50px rgba(0,0,0,0.3);

    margin-bottom: 25px;
}


label {

    display: block;

    font-weight: bold;

    margin-bottom: 10px;

    color: #ffd43b;

    font-size: 16px;
}


select,
textarea {

    width: 100%;

    padding: 14px;

    border-radius: 12px;

    border: 1px solid #526d9e;

    background: #0b1d3d;

    color: white;

    font-size: 16px;

    outline: none;

    margin-bottom: 20px;
}


select:focus,
textarea:focus {

    border-color: #ffd43b;

}


textarea {

    min-height: 130px;

    resize: vertical;
}


button {

    width: 100%;

    padding: 16px;

    border: none;

    border-radius: 14px;

    background: #ffd43b;

    color: #07152f;

    font-size: 18px;

    font-weight: bold;

    cursor: pointer;

    transition: 0.2s;
}


button:hover {

    transform: translateY(-2px);

    box-shadow:
        0 8px 20px rgba(255,212,59,0.3);
}


button:disabled {

    opacity: 0.6;

    cursor: wait;

}


.story-card {

    display: none;

    background: #fffdf5;

    color: #263238;

    border-radius: 22px;

    padding: 35px;

    box-shadow:
        0 20px 50px rgba(0,0,0,0.35);
}


.story-header {

    text-align: center;

    margin-bottom: 25px;
}


.story-header h2 {

    color: #102d5c;

    font-size: 30px;

    margin-bottom: 10px;
}


.badges {

    display: flex;

    justify-content: center;

    gap: 10px;

    flex-wrap: wrap;
}


.badge {

    background: #fff0a8;

    color: #102d5c;

    padding: 7px 14px;

    border-radius: 20px;

    font-weight: bold;

    font-size: 14px;
}


.story {

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 18px;

    line-height: 1.9;

    white-space: pre-wrap;
}


.loading {

    text-align: center;

    display: none;

    margin-top: 15px;

    color: #ffd43b;

}


.error {

    display: none;

    margin-top: 15px;

    padding: 12px;

    border-radius: 10px;

    background: #5b1b24;

    color: #ffd9dd;
}


.footer {

    text-align: center;

    margin-top: 25px;

    color: #9fb5d8;

    font-size: 14px;
}


@media (max-width: 600px) {

    h1 {
        font-size: 30px;
    }

    .card {
        padding: 20px;
    }

    .story-card {
        padding: 22px;
    }

    .story {
        font-size: 17px;
    }

}

</style>

</head>


<body>

<div class="container">

    <div class="header">

        <div class="logo">📖✨</div>

        <h1>Mood-to-Story AI</h1>

        <div class="subtitle">
            Transform your mood and imagination into a magical story.
        </div>

    </div>


    <div class="card">

        <label>🎭 Choose Your Mood</label>

        <select id="mood">

            <option>Happy 😊</option>
            <option>Sad 😢</option>
            <option>Excited 🤩</option>
            <option>Peaceful 😌</option>
            <option>Romantic ❤️</option>
            <option>Mysterious 🕵️</option>
            <option>Scared 😨</option>
            <option>Angry 😠</option>
            <option>Hopeful 🌈</option>
            <option>Adventurous 🗺️</option>

        </select>


        <label>📚 Choose Genre</label>

        <select id="genre">

            <option>Fantasy 🧙</option>
            <option>Adventure 🗺️</option>
            <option>Mystery 🔎</option>
            <option>Comedy 😂</option>
            <option>Romance ❤️</option>
            <option>Science Fiction 🚀</option>
            <option>Horror 👻</option>
            <option>Friendship 🤝</option>
            <option>Inspirational 🌟</option>

        </select>


        <label>💡 What should your story be about?</label>

        <textarea
            id="idea"
            placeholder="Example: A student discovers a magical library where every book he reads turns into reality..."
        ></textarea>


        <button
            id="generateBtn"
            onclick="generateStory()"
        >
            ✨ Create My Story
        </button>


        <div
            class="loading"
            id="loading"
        >
            ✨ Creating your magical story...
        </div>


        <div
            class="error"
            id="error"
        ></div>

    </div>


    <div
        class="story-card"
        id="storyCard"
    >

        <div class="story-header">

            <h2>📖 Your Magical Story</h2>

            <div class="badges">

                <span
                    class="badge"
                    id="moodBadge"
                ></span>

                <span
                    class="badge"
                    id="genreBadge"
                ></span>

            </div>

        </div>


        <div
            class="story"
            id="story"
        ></div>

    </div>


    <div class="footer">

        📖 Mood-to-Story AI • Powered by Gemini ✨

    </div>

</div>


<script>

async function generateStory() {

    const mood =
        document.getElementById("mood").value;

    const genre =
        document.getElementById("genre").value;

    const idea =
        document.getElementById("idea").value.trim();


    const button =
        document.getElementById("generateBtn");

    const loading =
        document.getElementById("loading");

    const error =
        document.getElementById("error");

    const storyCard =
        document.getElementById("storyCard");

    const story =
        document.getElementById("story");


    if (!idea) {

        error.style.display = "block";

        error.textContent =
            "💡 Please enter an idea for your story.";

        return;
    }


    error.style.display = "none";

    storyCard.style.display = "none";

    loading.style.display = "block";

    button.disabled = true;

    button.textContent = "✨ Creating...";


    try {

        const response =
            await fetch("/generate", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    mood: mood,
                    genre: genre,
                    idea: idea

                })

            });


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.error ||
                "Unable to generate the story."
            );

        }


        document.getElementById(
            "moodBadge"
        ).textContent =
            "😊 " + mood;


        document.getElementById(
            "genreBadge"
        ).textContent =
            "📚 " + genre;


        story.textContent =
            data.story;


        storyCard.style.display =
            "block";


        storyCard.scrollIntoView({
            behavior: "smooth"
        });

    }

    catch (err) {

        error.style.display =
            "block";

        error.textContent =
            "❌ " + err.message;

    }

    finally {

        loading.style.display =
            "none";

        button.disabled =
            false;

        button.textContent =
            "✨ Create My Story";

    }

}

</script>

</body>

</html>
"""
