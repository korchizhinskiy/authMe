from fastapi.applications import FastAPI

from app.infrastructure.exception_handler import setup_exception_handlers
from app.infrastructure.ioc.dependencies import init_di
from app.infrastructure.log_config import configure_logging

# TODO: Set main router by package layer (in init module)

app = FastAPI(swagger_ui_parameters={"persistAuthorization": True})

init_di(app)

configure_logging()
setup_exception_handlers(app)
