
import os, base64
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from langserve import add_routes
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from google import genai
from google.genai import types

GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")
llm=ChatGoogleGenerativeAI(model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY,temperature=0)
img_client=genai.Client(api_key=GOOGLE_API_KEY)
app=FastAPI(title="Mood-to-Story AI")

HTML="""<!DOCTYPE html><html><head><meta charset='utf-8'>
<title>Mood-to-Story AI</title><style>
body{font-family:Arial;margin:0;background:#111827;color:#fff}
.wrap{max-width:900px;margin:auto;padding:32px}
.card{background:#1f2937;padding:24px;border-radius:18px}
select,textarea,button{width:100%;padding:12px;margin:8px 0;border-radius:10px;border:none}
button{background:#f59e0b;font-weight:bold}.story{white-space:pre-wrap;line-height:1.7}
img{width:100%;border-radius:16px;margin:16px 0}
</style></head><body><div class='wrap'><div class='card'>
<h1>📖 Mood-to-Story AI</h1><p>Turn your mood into a magical illustrated story.</p>
<select id=m><option>Happy</option><option>Sad</option><option>Excited</option><option>Peaceful</option></select>
<select id=g><option>Fantasy</option><option>Adventure</option><option>Mystery</option></select>
<select id=s><option>Cinematic storybook</option><option>Anime</option><option>Watercolor</option></select>
<textarea id=i rows=3 placeholder='What should the story be about?'></textarea>
<button onclick=go()>✨ Create Story</button><div id=o></div></div></div>
<script>
async function go(){
o.innerHTML='Generating...';
const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},
body:new URLSearchParams({mood:m.value,genre:g.value,style:s.value,idea:i.value})});
const d=await r.json();
o.innerHTML=(d.image?`<img src="data:${d.mime};base64,${d.image}">`:'')+`<div class=story>${d.story}</div>`;
}
</script></body></html>"""

def make_story(mood,genre,idea):
    prompt=f"Write a {genre} story (300 words). Mood:{mood}. Idea:{idea}. Give a title then story."
    return llm.invoke(prompt).content

def make_image(story,style):
    try:
        r=img_client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=f"Create a {style} illustration for: {story}",
            config=types.GenerateContentConfig(response_modalities=["TEXT","IMAGE"]))
        for p in r.candidates[0].content.parts:
            if getattr(p,"inline_data",None):
                return base64.b64encode(p.inline_data.data).decode(),p.inline_data.mime_type
    except Exception:
        pass
    return None,None

@app.get("/",response_class=HTMLResponse)
def home(): return HTML

@app.post("/generate")
def gen(mood:str=Form(...),genre:str=Form(...),style:str=Form(...),idea:str=Form("")):
    story=make_story(mood,genre,idea)
    img,mime=make_image(story,style)
    return JSONResponse({"story":story,"image":img,"mime":mime or "image/png"})

chain=RunnableLambda(lambda x: {"story":make_story(x["mood"],x["genre"],x.get("idea",""))})
add_routes(app,chain,path="/agent")

@app.get("/health")
def health(): return {"status":"healthy"}
