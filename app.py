import os
import base64

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from google import genai


# ============================================================
# CONFIGURATION
# ============================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is not configured. "
        "Please add GOOGLE_API_KEY in Render Environment Variables."
    )

client = genai.Client(api_key=GOOGLE_API_KEY)

app = FastAPI(
    title="Mood-to-Story AI",
    description="Generate mood-based stories with AI illustrations",
    version="1.0.0"
)


# ============================================================
# MOOD VISUAL SETTINGS
# ============================================================

MOOD_VISUALS = {

    "Happy":
        "bright golden sunlight, colorful flowers, joyful expressions, "
        "warm atmosphere, vibrant colors",

    "Sad":
        "gentle rain, soft blue tones, emotional expressions, "
        "quiet atmosphere, soft cinematic lighting",

    "Excited":
        "dynamic movement, vibrant colors, glowing energy, "
        "dramatic composition, energetic atmosphere",

    "Peaceful":
        "calm lake, soft clouds, pastel colors, peaceful nature, "
        "gentle sunlight, serene atmosphere",

    "Romantic":
        "beautiful sunset, warm pink and purple sky, flowers, "
        "dreamy atmosphere, soft glowing light",

    "Mysterious":
        "misty forest, moonlight, mysterious shadows, "
        "magical glowing objects, dark blue atmosphere",

    "Scared":
        "dark forest, fog, dramatic shadows, mysterious castle, "
        "suspenseful atmosphere, dim lighting",

    "Angry":
        "dramatic storm clouds, intense lighting, powerful expressions, "
        "strong atmosphere, red-orange sky",

    "Hopeful":
        "beautiful sunrise, golden rays of light, peaceful landscape, "
        "uplifting atmosphere, warm colors",

    "Adventurous":
        "epic mountains, ancient ruins, dramatic sky, "
        "adventurous journey, cinematic environment"
}


# ============================================================
# FRONTEND
# ============================================================

HTML = """
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Mood-to-Story AI</title>

<link
href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap"
rel="stylesheet">

<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {

    font-family: 'Poppins', sans-serif;

    min-height: 100vh;

    background:
        radial-gradient(
            circle at top left,
            #1e3a8a 0%,
            transparent 35%
        ),
        radial-gradient(
            circle at bottom right,
            #312e81 0%,
            transparent 35%
        ),
        #020617;

    color: white;

    padding: 30px 15px;
}


/* ============================================================
   MAIN CONTAINER
   ============================================================ */

.container {

    max-width: 1000px;

    margin: auto;
}


/* ============================================================
   HEADER
   ============================================================ */

.header {

    text-align: center;

    margin-bottom: 25px;
}

.header h1 {

    font-size: 42px;

    font-weight: 700;

    background:
        linear-gradient(
            90deg,
            #facc15,
            #fde68a
        );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;
}

.header p {

    color: #cbd5e1;

    margin-top: 8px;

    font-size: 16px;
}


/* ============================================================
   INPUT CARD
   ============================================================ */

.card {

    background:
        rgba(15, 23, 42, 0.82);

    border:
        1px solid
        rgba(255,255,255,0.12);

    border-radius: 24px;

    padding: 30px;

    box-shadow:
        0 25px 60px
        rgba(0,0,0,0.35);

    backdrop-filter: blur(15px);
}


/* ============================================================
   INPUT GRID
   ============================================================ */

.input-grid {

    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 16px;

    margin-bottom: 18px;
}

.field label {

    display: block;

    font-size: 13px;

    color: #cbd5e1;

    margin-bottom: 7px;

    font-weight: 500;
}


select,
textarea {

    width: 100%;

    padding: 14px;

    border-radius: 12px;

    border: 1px solid #334155;

    background: #f8fafc;

    color: #0f172a;

    font-family: inherit;

    font-size: 14px;

    outline: none;
}

select:focus,
textarea:focus {

    border-color: #facc15;

    box-shadow:
        0 0 0 3px
        rgba(250,204,21,0.15);
}


textarea {

    min-height: 120px;

    resize: vertical;

    margin-bottom: 16px;
}


/* ============================================================
   BUTTON
   ============================================================ */

.generate-btn {

    width: 100%;

    padding: 16px;

    border: none;

    border-radius: 13px;

    background:
        linear-gradient(
            135deg,
            #facc15,
            #f59e0b
        );

    color: #111827;

    font-family: inherit;

    font-size: 16px;

    font-weight: 700;

    cursor: pointer;

    transition: 0.3s;

    box-shadow:
        0 8px 20px
        rgba(245,158,11,0.25);
}

.generate-btn:hover {

    transform: translateY(-2px);

    box-shadow:
        0 12px 25px
        rgba(245,158,11,0.35);
}

.generate-btn:disabled {

    opacity: 0.6;

    cursor: not-allowed;

    transform: none;
}


/* ============================================================
   LOADING
   ============================================================ */

.loading {

    display: none;

    text-align: center;

    padding: 30px 10px;
}

.spinner {

    width: 45px;

    height: 45px;

    border-radius: 50%;

    border:
        4px solid
        rgba(255,255,255,0.15);

    border-top:
        4px solid
        #facc15;

    animation:
        spin 0.9s linear infinite;

    margin: auto;
}

@keyframes spin {

    to {
        transform: rotate(360deg);
    }
}

.loading p {

    margin-top: 12px;

    color: #fde68a;

    font-size: 14px;
}


/* ============================================================
   RESULT
   ============================================================ */

.result {

    display: none;

    margin-top: 28px;

    background: #ffffff;

    color: #1e293b;

    border-radius: 22px;

    overflow: hidden;

    box-shadow:
        0 25px 60px
        rgba(0,0,0,0.35);
}


/* ============================================================
   IMAGE
   ============================================================ */

.story-image {

    width: 100%;

    display: block;

    max-height: 560px;

    object-fit: cover;
}


/* ============================================================
   STORY CONTENT
   ============================================================ */

.story-content {

    padding: 30px;
}

.story-title {

    font-size: 30px;

    color: #1e3a8a;

    font-weight: 700;

    margin-bottom: 15px;
}


.tags {

    display: flex;

    flex-wrap: wrap;

    gap: 8px;

    margin-bottom: 22px;
}

.tag {

    padding: 7px 13px;

    border-radius: 999px;

    background: #eff6ff;

    color: #1d4ed8;

    font-size: 12px;

    font-weight: 600;
}


.story-text {

    white-space: pre-wrap;

    line-height: 1.9;

    font-size: 15px;

    color: #334155;
}


.moral {

    margin-top: 25px;

    padding: 18px;

    border-left:
        5px solid
        #facc15;

    background: #fffbeb;

    border-radius: 10px;

    color: #713f12;
}

.moral strong {

    display: block;

    margin-bottom: 5px;
}


/* ============================================================
   ERROR
   ============================================================ */

.error {

    display: none;

    margin-top: 20px;

    padding: 15px;

    background: #450a0a;

    border:
        1px solid
        #ef4444;

    border-radius: 10px;

    color: #fecaca;

    font-size: 14px;
}


/* ============================================================
   FOOTER
   ============================================================ */

.footer {

    text-align: center;

    color: #94a3b8;

    font-size: 13px;

    margin-top: 25px;
}


/* ============================================================
   MOBILE
   ============================================================ */

@media (max-width: 750px) {

    .input-grid {

        grid-template-columns: 1fr;
    }

    .header h1 {

        font-size: 32px;
    }

    .card {

        padding: 20px;
    }

    .story-content {

        padding: 20px;
    }

    .story-title {

        font-size: 24px;
    }
}

</style>

</head>


<body>


<div class="container">


<!-- ========================================================
     HEADER
     ======================================================== -->

<div class="header">

    <h1>📖 Mood-to-Story AI</h1>

    <p>
        Turn your emotions and imagination into a magical
        illustrated story.
    </p>

</div>


<!-- ========================================================
     INPUT CARD
     ======================================================== -->

<div class="card">


<div class="input-grid">


<div class="field">

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


<div class="field">

<label>📚 Choose Genre</label>

<select id="genre">

<option>Fantasy</option>
<option>Adventure</option>
<option>Mystery</option>
<option>Comedy</option>
<option>Romance</option>
<option>Science Fiction</option>
<option>Friendship</option>
<option>Inspirational</option>

</select>

</div>


<div class="field">

<label>🎨 Illustration Style</label>

<select id="style">

<option>Cinematic Storybook</option>
<option>Anime</option>
<option>Watercolor</option>
<option>3D Animated</option>
<option>Fantasy Art</option>

</select>

</div>


</div>


<label
style="
display:block;
font-size:13px;
color:#cbd5e1;
margin-bottom:7px;
">

💡 Your Story Idea

</label>


<textarea
id="idea"
placeholder="Example: A student discovers a magical forest behind her school..."
></textarea>


<button
id="generateButton"
class="generate-btn"
onclick="generateStory()"
>

✨ Create My Story

</button>


<!-- LOADING -->

<div id="loading" class="loading">

<div class="spinner"></div>

<p>
Creating your story and magical illustration...
</p>

<p style="font-size:12px;color:#94a3b8;">
This may take a little while because AI is creating both the story and image.
</p>

</div>


<!-- ERROR -->

<div id="error" class="error"></div>


<!-- ========================================================
     RESULT
     ======================================================== -->

<div id="result" class="result">


<img
id="storyImage"
class="story-image"
alt="AI generated story illustration"
/>


<div class="story-content">


<div
id="storyTitle"
class="story-title"
>
</div>


<div class="tags">

<span
id="moodTag"
class="tag"
>
</span>

<span
id="genreTag"
class="tag"
>
</span>

<span
id="styleTag"
class="tag"
>
</span>

</div>


<div
id="storyText"
class="story-text"
>
</div>


<div
id="moral"
class="moral"
style="display:none;"
>

<strong>🌟 Moral of the Story</strong>

<span id="moralText"></span>

</div>


</div>

</div>


</div>


<div class="footer">

✨ Powered by Google Gemini AI

</div>


</div>


<script>


// ============================================================
// GENERATE STORY
// ============================================================

async function generateStory() {


const mood =
document.getElementById("mood").value;

const genre =
document.getElementById("genre").value;

const style =
document.getElementById("style").value;

const idea =
document.getElementById("idea").value;


const result =
document.getElementById("result");

const loading =
document.getElementById("loading");

const error =
document.getElementById("error");

const button =
document.getElementById("generateButton");


result.style.display = "none";

error.style.display = "none";

loading.style.display = "block";

button.disabled = true;

button.innerText = "✨ Creating...";


try {


const response = await fetch(
"/generate",
{
method: "POST",

headers: {
"Content-Type":
"application/x-www-form-urlencoded"
},

body:
new URLSearchParams({

mood: mood,

genre: genre,

style: style,

idea: idea

})

}
);


const data =
await response.json();


if (!response.ok || !data.success) {

throw new Error(
data.error ||
"Unable to generate the story."
);

}


// ========================================================
// PARSE STORY
// ========================================================

let story =
data.story || "";

let title =
"Your Magical Story";

let storyText =
story;

let moral =
"";


const titleMatch =
story.match(
/TITLE:\\s*(.*?)(?=\\n|STORY:)/is
);

if (titleMatch) {

title =
titleMatch[1].trim();

}


const storyMatch =
story.match(
/STORY:\\s*(.*?)(?=\\nMORAL:|$)/is
);

if (storyMatch) {

storyText =
storyMatch[1].trim();

}


const moralMatch =
story.match(
/MORAL:\\s*(.*)$/is
);

if (moralMatch) {

moral =
moralMatch[1].trim();

}


// ========================================================
// DISPLAY
// ========================================================

document.getElementById(
"storyTitle"
).innerText = title;


document.getElementById(
"storyText"
).innerText = storyText;


document.getElementById(
"moodTag"
).innerText =
"🎭 " + mood;


document.getElementById(
"genreTag"
).innerText =
"📚 " + genre;


document.getElementById(
"styleTag"
).innerText =
"🎨 " + style;


// ========================================================
// MORAL
// ========================================================

if (moral) {

document.getElementById(
"moralText"
).innerText = moral;

document.getElementById(
"moral"
).style.display = "block";

}


// ========================================================
// IMAGE
// ========================================================

if (data.image) {

const image =
document.getElementById(
"storyImage"
);

image.src =
"data:" +
data.mime +
";base64," +
data.image;

image.style.display = "block";

} else {

document.getElementById(
"storyImage"
).style.display = "none";

}


// ========================================================
// SHOW RESULT
// ========================================================

result.style.display = "block";


result.scrollIntoView({
behavior: "smooth",
block: "start"
});


} catch (err) {


error.innerText =
"❌ " + err.message;

error.style.display = "block";


} finally {

loading.style.display = "none";

button.disabled = false;

button.innerText =
"✨ Create My Story";

}

}


</script>


</body>

</html>
"""


# ============================================================
# STORY GENERATION
# ============================================================

def make_story(mood, genre, idea):

    prompt = f"""
You are a creative bestselling story writer.

Create an original {genre} story of approximately
300–400 words.

Selected Mood:
{mood}

Story Idea:
{idea if idea.strip() else "Create an imaginative story based on the selected mood."}

IMPORTANT INSTRUCTIONS:

1. The entire story must strongly reflect the selected mood.
2. Create a memorable main character.
3. Include a clear beginning, middle and ending.
4. Use vivid descriptions.
5. Make the emotional atmosphere match the mood.
6. Make the story engaging and suitable for a general audience.
7. End with a meaningful moral.

Return EXACTLY in this format:

TITLE:
<creative story title>

STORY:
<complete story>

MORAL:
<one meaningful sentence>
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        if not response.text:

            raise RuntimeError(
                "Gemini returned an empty story."
            )

        return response.text

    except Exception as e:

        print(
            "STORY GENERATION ERROR:",
            str(e)
        )

        raise RuntimeError(
            f"Story generation failed: {str(e)}"
        )


# ============================================================
# IMAGE GENERATION
# ============================================================

def make_image(
    story,
    mood,
    genre,
    style
):

    mood_visual =
        MOOD_VISUALS.get(
            mood,
            "beautiful cinematic atmosphere"
        )

    image_prompt = f"""
Create a beautiful illustrated storybook scene.

MOOD:
{mood}

GENRE:
{genre}

ART STYLE:
{style}

MOOD VISUAL ATMOSPHERE:
{mood_visual}

STORY:
{story}

IMPORTANT:

Create ONE main cinematic illustration
representing the most important visual moment
of the story.

The image must:

- Clearly reflect the selected mood.
- Match the genre.
- Match the requested art style.
- Have expressive characters.
- Have a beautiful environment.
- Have cinematic lighting.
- Have strong emotional atmosphere.
- Look like a professional storybook illustration.
- Be visually appealing.
- Contain NO text.
- Contain NO captions.
- Contain NO watermark.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.1-flash-image",
            contents=image_prompt
        )

        if not response.candidates:

            print(
                "IMAGE GENERATION: "
                "No candidates returned."
            )

            return None, None

        for part in response.candidates[0].content.parts:

            if getattr(
                part,
                "inline_data",
                None
            ):

                image_bytes = (
                    part.inline_data.data
                )

                mime_type = (
                    part.inline_data.mime_type
                    or "image/png"
                )

                return (
                    base64.b64encode(
                        image_bytes
                    ).decode("utf-8"),

                    mime_type
                )

        print(
            "IMAGE GENERATION: "
            "No image data returned."
        )

    except Exception as e:

        print(
            "IMAGE GENERATION ERROR:",
            str(e)
        )

    return None, None


# ============================================================
# HOME PAGE
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

        print(
            f"Generating story | "
            f"Mood={mood} | "
            f"Genre={genre} | "
            f"Style={style}"
        )

        # Generate story
        story = make_story(
            mood,
            genre,
            idea
        )

        # Generate matching image
        image, mime = make_image(
            story,
            mood,
            genre,
            style
        )

        return JSONResponse({

            "success": True,

            "story": story,

            "image": image,

            "mime":
                mime or "image/png"

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


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "Mood-to-Story AI"
    }
