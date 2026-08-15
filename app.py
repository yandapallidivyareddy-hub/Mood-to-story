import os
import base64
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from langserve import add_routes
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from google import genai
from google.genai import types

# ---------------------------
# API Key
# ---------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Story LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.9,
)

# Image Client
img_client = genai.Client(api_key=GOOGLE_API_KEY)

app = FastAPI(title="Mood-to-Story AI")

# ---------------------------
# Frontend
# ---------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Mood-to-Story AI</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">

<style>
*{margin:0;padding:0;box-sizing:border-box}
body{
    font-family:'Poppins',sans-serif;
    background:linear-gradient(135deg,#0f172a,#1e3a8a);
    color:white;
    min-height:100vh;
}
.container{
    max-width:950px;
    margin:auto;
    padding:40px 20px;
}
.card{
    background:rgba(255,255,255,.08);
    backdrop-filter:blur(16px);
    border:1px solid rgba(255,255,255,.15);
    border-radius:22px;
    padding:30px;
    box-shadow:0 15px 35px rgba(0,0,0,.35);
}
h1{
    color:#FFD54F;
    text-align:center;
    font-size:2.2rem;
}
.subtitle{
    text-align:center;
    color:#dbeafe;
    margin:8px 0 25px;
}
.grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:15px;
}
select,textarea{
    width:100%;
    padding:14px;
    border:none;
    border-radius:12px;
    font-size:15px;
    background:white;
    color:#111827;
}
textarea{
    grid-column:1/-1;
    resize:vertical;
}
button{
    width:100%;
    margin-top:18px;
    padding:15px;
    border:none;
    border-radius:12px;
    background:#FACC15;
    color:#111827;
    font-size:16px;
    font-weight:700;
    cursor:pointer;
    transition:.3s;
}
button:hover{
    background:#F59E0B;
    transform:translateY(-2px);
}
#loading{
    display:none;
    text-align:center;
    margin:25px 0;
    color:#fde68a;
}
.spinner{
    width:40px;
    height:40px;
    border:4px solid rgba(255,255,255,.2);
    border-top:4px solid #FACC15;
    border-radius:50%;
    margin:0 auto 12px;
    animation:spin 1s linear infinite;
}
@keyframes spin{
    to{transform:rotate(360deg)}
}
.result{
    display:none;
    margin-top:28px;
    background:white;
    color:#1f2937;
    border-radius:18px;
    overflow:hidden;
}
.result img{
    width:100%;
    display:block;
}
.story{
    padding:24px;
}
.title{
    color:#1d4ed8;
    font-size:1.7rem;
    font-weight:700;
    margin-bottom:12px;
}
.meta{
    display:flex;
    gap:10px;
    flex-wrap:wrap;
    margin-bottom:18px;
}
.badge{
    background:#dbeafe;
    color:#1d4ed8;
    padding:6px 12px;
    border-radius:999px;
    font-size:12px;
    font-weight:600;
}
.content{
    white-space:pre-wrap;
    line-height:1.9;
    font-size:15px;
}
.footer{
    text-align:center;
    margin-top:25px;
    color:#bfdbfe;
    font-size:13px;
}
@media(max-width:700px){
    .grid{grid-template-columns:1fr}
}
</style>
</head>

<body>

<div class="container">

<div class="card">

<h1>📖 Mood-to-Story AI</h1>
<p class="subtitle">Transform your mood into a magical illustrated storybook</p>

<div class="grid">

<select id="m">
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

<select id="g">
<option>Fantasy</option>
<option>Adventure</option>
<option>Mystery</option>
<option>Comedy</option>
<option>Romance</option>
<option>Science Fiction</option>
<option>Friendship</option>
<option>Inspirational</option>
</select>

<select id="s">
<option>Cinematic Storybook</option>
<option>Anime</option>
<option>Watercolor</option>
<option>3D Pixar Style</option>
</select>

<textarea id="i" rows="4"
placeholder="Describe your story idea... (e.g. A little girl discovers a magical forest)"></textarea>

</div>

<button onclick="generateStory()">✨ Create My Story</button>

<div id="loading">
<div class="spinner"></div>
Creating your magical story and illustration...
</div>

<div id="result" class="result">

<img id="storyImage"/>

<div class="story">

<div id="storyTitle" class="title"></div>

<div class="meta">
<div class="badge" id="moodTag"></div>
<div class="badge" id="genreTag"></div>
<div class="badge" id="styleTag"></div>
</div>

<div id="storyText" class="content"></div>

</div>

</div>

</div>

<div class="footer">
✨ Every story is uniquely created using AI
</div>

</div>

<script>
async function generateStory(){

const result=document.getElementById("result");
const loading=document.getElementById("loading");

result.style.display="none";
loading.style.display="block";

const res=await fetch("/generate",{
method:"POST",
headers:{
"Content-Type":"application/x-www-form-urlencoded"
},
body:new URLSearchParams({
mood:m.value,
genre:g.value,
style:s.value,
idea:i.value
})
});

const data=await res.json();

loading.style.display="none";

let title="Untitled Story";
let body=data.story;

const lines=data.story.split("\\n").filter(x=>x.trim()!="");

if(lines.length>0){
title=lines[0].replace(/^#+/,"").trim();
body=lines.slice(1).join("\\n");
}

document.getElementById("storyTitle").innerText=title;
document.getElementById("storyText").innerText=body;

document.getElementById("moodTag").innerText="😊 "+m.value;
document.getElementById("genreTag").innerText="📚 "+g.value;
document.getElementById("styleTag").innerText="🎨 "+s.value;

if(data.image){
const img=document.getElementById("storyImage");
img.src=`data:${data.mime};base64,${data.image}`;
}

result.style.display="block";
result.scrollIntoView({behavior:"smooth"});
}
</script>

</body>
</html>
"""

# ---------------------------
# Story Generator
# ---------------------------
def make_story(mood, genre, idea):

    prompt = f"""
You are a bestselling children's and fantasy author.

Write an original {genre} story in about 300–400 words.

Requirements:
- Mood: {mood}
- Story idea: {idea if idea else "Create your own imaginative idea"}
- Begin with a creative title.
- Include vivid emotions matching the mood.
- Give the main character a memorable name.
- End with a meaningful moral or uplifting ending.
"""

    return llm.invoke(prompt).content

# ---------------------------
# Image Generator
# ---------------------------
def make_image(story, mood, genre, style):

    mood_styles = {
        "Happy":"bright golden sunlight, colorful flowers, joyful atmosphere",
        "Sad":"soft rain, blue tones, emotional cinematic lighting",
        "Excited":"dynamic action, glowing energy, vibrant colors",
        "Peaceful":"calm lake, pastel sky, serene nature",
        "Romantic":"pink sunset, dreamy lighting, magical blossoms",
        "Mysterious":"misty forest, moonlight, magical fog",
        "Scared":"dark castle, eerie shadows, suspenseful lighting",
        "Angry":"storm clouds, dramatic sky, intense atmosphere",
        "Hopeful":"sunrise, warm light rays, inspiring landscape",
        "Adventurous":"epic mountains, ancient ruins, cinematic journey"
    }

    image_prompt = f"""
Illustrate a scene from this story.

STYLE: {style}
GENRE: {genre}
MOOD: {mood}

Atmosphere:
{mood_styles.get(mood)}

Create a highly detailed storybook illustration with expressive characters,
beautiful environment, cinematic composition, rich colors, and magical quality.

Story:
{story}
"""

    try:
        response = img_client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=image_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            ),
        )

        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None):
                return (
                    base64.b64encode(part.inline_data.data).decode(),
                    part.inline_data.mime_type,
                )
    except Exception as e:
        print("Image Error:", e)

    return None, None

# ---------------------------
# Routes
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return HTML

@app.post("/generate")
def generate(
    mood: str = Form(...),
    genre: str = Form(...),
    style: str = Form(...),
    idea: str = Form("")
):
    story = make_story(mood, genre, idea)
    image, mime = make_image(story, mood, genre, style)

    return JSONResponse({
        "story": story,
        "image": image,
        "mime": mime or "image/png"
    })

# LangServe endpoint
chain = RunnableLambda(
    lambda x: {
        "story": make_story(
            x["mood"],
            x["genre"],
            x.get("idea","")
        )
    }
)

add_routes(app, chain, path="/agent")

@app.get("/health")
def health():
    return {"status":"healthy"}

@app.get("/health")
def health(): return {"status":"healthy"}
