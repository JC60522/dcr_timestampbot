import json, re
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from ipfs_interface import Ipfs
from markupsafe import Markup


app = FastAPI(
    redoc_url=None,
    docs_url=None,
    openapi_url=None)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_methods=["GET", "POST"],
)


# template and static files pointer
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Render Landing page
@app.get('/')
@limiter.limit("3/minute")
def homepage(request: Request):
    return templates.TemplateResponse('index.html', {"request": request})


# Route for maunal CID search
@app.post("/")
@limiter.limit("3/minute")
async def form_post(request: Request, _hash: str = Form(...)):
    if re.match(r'^[Qm][1-9A-Za-z]{44}[^OIl]$', _hash) is None:
        return templates.TemplateResponse('result.html',
                                          context={'request': request, 'result': Markup(f'''<b>Bad Query</b>
                                          <br><a href="https://dcr-timestampbot.com"><b style="color: red; ">
                                          Back to Home<b></a>''')})
    result = Ipfs(_hash).search()
    if not result:
        return templates.TemplateResponse('result.html', context={'request': request, 'result': Markup(f'''<b>CID Not Found</b>
                                          <br><a href="https://dcr-timestampbot.com"><b style="color: red; ">
                                          Back to Home<b></a>''')})
    if isinstance(result, bytes):
        result = result.decode("utf-8")
        result = Markup(f'{json.loads(result)}"')
    return templates.TemplateResponse('result.html', context={'request': request, 'result': result})


# Route for ipfs-url in tweets
@app.get("/ipfs/{_hash}")
@limiter.limit("3/minute")
async def get(request: Request, _hash: str):
    if re.match(r'^[Qm][1-9A-Za-z]{44}[^OIl]$', _hash) is None:
        return templates.TemplateResponse('result.html',
                                          context={'request': request, 'result': Markup(f'<pre class="result__thread result__thread--fail">Invalid query format. Make sure it starts with "Qm" and is 46 characters long.</pre>'
                                          f'<a href="https://dcr-timestampbot.com">Back Home</a>')})
    result = Ipfs(_hash).search()
    if isinstance(result, bytes):
        result = result.decode("utf-8")
        result = Markup(f'<pre class="result__thread result__thread--success">{result}</pre>'
                        f'<div class="result__twitter"><a target="__blank" href="https://twitter.com/{json.loads(result)["user"]["screen_name"]}/status/'
                        f'{json.loads(result)["id_str"]}">'
                        f'View on Twitter</a></div>''')
    return templates.TemplateResponse('result.html', context={'request': request, 'result': result})
