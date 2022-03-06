import secrets
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from ipfs_interface import Ipfs


limiter = Limiter(key_func=get_remote_address)
security = HTTPBasic()


app = FastAPI(
    title="dcr-timestampbot",
    description="dcr-timestampbot REST-API.",
    version="0.0.1",
    docs_url=None,
    openapi_url=None
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Basic auth wall to access swagger docs
def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "############")
    correct_password = secrets.compare_digest(credentials.password, "################")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation(request: Request, username: bool = Depends(get_current_username)):
    if username:
        return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi(request: Request, username: bool = Depends(get_current_username)):
    if username:
        return get_openapi(title=app.title, version=app.version, routes=app.routes)


# template and static files pointer
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Render Landing page
@app.get('/')
@limiter.limit("10/minute")
def homepage(request: Request):
    return templates.TemplateResponse('index.html', {"request":request})


# Route for maunal CID search
@app.post("/")
@limiter.limit("10/minute")
async def form_post(request: Request, _hash: str = Form(...)):
    result = Ipfs(_hash).search()
    if isinstance(result, bytes):
        result = result.decode("utf-8")  
    return templates.TemplateResponse('result.html', context={'request': request, 'result': result})


# Route for ipfs-url in tweets
@app.get("/ipfs/{_hash}")
@limiter.limit("10/minute")
async def get(request: Request, _hash: str):
    result = Ipfs(_hash).search()
    if isinstance(result, bytes):
        result = result.decode("utf-8")
    return templates.TemplateResponse('result.html', context={'request': request, 'result': result})
