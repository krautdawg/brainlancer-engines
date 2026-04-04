import os
import secrets
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

APP_PASSWORD = os.getenv("APP_PASSWORD", "br4inlancer")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

app = FastAPI(docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, session_cookie="bl_session")

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Brainlancer — Login</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>tailwind.config={theme:{extend:{colors:{sky:'#00B3FF',mint:'#00FFC5'},fontFamily:{inter:['Inter','sans-serif']}}}}</script>
  <style>*{font-family:'Inter',sans-serif}</style>
</head>
<body class="bg-slate-50 min-h-screen flex items-center justify-center">
  <div class="bg-white border border-slate-200 rounded-2xl p-8 w-full max-w-sm shadow-md">
    <h1 class="text-2xl font-bold text-slate-900 text-center mb-2">Brainlancer</h1>
    <p class="text-slate-400 text-center text-sm mb-6">AI Automation Engine Portfolio</p>
    <form method="post" action="/login">
      <input type="password" name="password" placeholder="Password" autofocus
             class="w-full bg-white border border-slate-300 rounded-lg px-4 py-3 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-sky focus:ring-2 focus:ring-sky/20 mb-4" />
      <button type="submit"
              class="w-full bg-sky hover:bg-sky/80 text-white font-semibold py-3 rounded-lg transition-all shadow-sm">
        Enter
      </button>
      {error}
    </form>
  </div>
</body>
</html>"""


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("authenticated"):
        return RedirectResponse("/", status_code=302)
    return HTMLResponse(LOGIN_HTML.replace("{error}", ""))


@app.post("/login")
async def login_submit(request: Request):
    form = await request.form()
    if form.get("password") == APP_PASSWORD:
        request.session["authenticated"] = True
        return RedirectResponse("/", status_code=303)
    return HTMLResponse(
        LOGIN_HTML.replace("{error}", '<p class="text-red-400 text-sm text-center mt-3">Wrong password</p>'),
        status_code=401
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if not request.session.get("authenticated"):
        return RedirectResponse("/login", status_code=302)
    html = open("index.html").read()
    return HTMLResponse(html)
