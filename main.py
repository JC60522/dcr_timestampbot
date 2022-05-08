import json, secrets, re
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from ipfs_interface import Ipfs
from markupsafe import Markup


limiter = Limiter(key_func=get_remote_address)
security = HTTPBasic()


app = FastAPI(
    title="dcr-timestampbot",
    description="dcr-timestampbot",
    version="0.0.1",
    docs_url=None,
    openapi_url=None)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_methods=["GET", "POST"],
)


# Basic auth wall to access swagger docs
def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "######")
    correct_password = secrets.compare_digest(credentials.password, "######")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation(username: bool = Depends(get_current_username)):
    if username:
        return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi(username: bool = Depends(get_current_username)):
    if username:
        return get_openapi(title=app.title, version=app.version, routes=app.routes)


# template and static files pointer
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Render Landing page
@app.get('/')
@limiter.limit("3/minute")
def homepage(request: Request, username):
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
        result = Markup(f'<hr size="8"><br><b>{result}</b><br>'
                        f' <a href="https://twitter.com/{json.loads(result)["user"]["screen_name"]}/status/'
                        f'{json.loads(result)["id_str"]}"><b style="color: red; ">'
                        f'View on Twitter<b></a><br><hr size="8">''')
    return templates.TemplateResponse('result.html', context={'request': request, 'result': result})


# Route for ipfs-url in tweets
@app.get("/ipfs/{_hash}")
@limiter.limit("3/minute")
async def get(request: Request, _hash: str):
    if re.match(r'^[Qm][1-9A-Za-z]{44}[^OIl]$', _hash) is None:
        return templates.TemplateResponse('result.html',
                                          context={'request': request, 'result': Markup(f'''<b>Bad Query</b>
                                                  <br><a href="https://dcr-timestampbot.com"><b style="color: red; ">
                                                  Back to Home<b></a>''')})
    result = Ipfs(_hash).search()
    if isinstance(result, bytes):
        result = result.decode("utf-8")
        result = Markup(f'<hr size="8"><br><b>{result}</b><br>'
                        f' <a href="https://twitter.com/{json.loads(result)["user"]["screen_name"]}/status/'
                        f'{json.loads(result)["id_str"]}"><b style="color: red; ">'
                        f'View on Twitter<b></a><br><hr size="8">''')
    return templates.TemplateResponse('result.html', context={'request': request, 'result': result})
