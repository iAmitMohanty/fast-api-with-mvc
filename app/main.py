import logging
from fastapi import FastAPI, Depends, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.dependencies import get_current_user
from app.db.database import Base, engine, get_db
from app.controllers.customer_controller import CustomerController
from app.controllers.auth_controller import AuthController
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.auth_schema import UserRegister, UserLogin, UserResponse, TokenResponse, RefreshTokenRequest
from app.models.user import User
from app.utils.response_wrapper import success_response, error_response
import app.models.customer  # noqa: F401 — registers Customer model with Base metadata
import app.models.user  # noqa: F401 — registers User model with Base metadata

setup_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)
logger.info("Database tables verified / created.")

app = FastAPI(title=settings.APP_TITLE, version=settings.APP_VERSION)


# ── Global Validation Error Handler ───────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(message="Validation failed", error=errors).model_dump(),
    )


# ── Auth Routes (public) ───────────────────────────────────────────────────────

@app.post("/auth/register", status_code=201)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    logger.info("POST /auth/register — username=%s", payload.username)
    user = AuthController.register(payload, db)
    return JSONResponse(
        status_code=201,
        content=success_response(
            message="User registered successfully",
            data=UserResponse.model_validate(user).model_dump(),
        ).model_dump(),
    )


@app.post("/auth/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    logger.info("POST /auth/login — username=%s", payload.username)
    token: TokenResponse = AuthController.login(payload, db)
    return success_response(message="Login successful", data=token.model_dump())


@app.post("/auth/refresh")
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    logger.info("POST /auth/refresh")
    token: TokenResponse = AuthController.refresh(payload.refresh_token, db)
    return success_response(message="Token refreshed successfully", data=token.model_dump())


@app.post("/auth/logout", status_code=200)
def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("POST /auth/logout — username=%s", current_user.username)
    AuthController.logout(current_user, db)
    return success_response(message="Logged out successfully")


# ── Customer Routes (protected) ────────────────────────────────────────────────

@app.get("/customers", status_code=200)
def list_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("GET /customers — user=%s", current_user.username)
    customers = CustomerController.get_all(db)
    data = [CustomerResponse.model_validate(c).model_dump(mode="json") for c in customers]
    logger.info("GET /customers — returned %d records", len(data))
    return success_response(message="Customers fetched successfully", data=data)


@app.get("/customers/{customer_id}")
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("GET /customers/%s — user=%s", customer_id, current_user.username)
    customer = CustomerController.get_by_id(customer_id, db)
    return success_response(
        message="Customer fetched successfully",
        data=CustomerResponse.model_validate(customer).model_dump(mode="json"),
    )


@app.post("/customers", status_code=201)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("POST /customers — email=%s user=%s", payload.email, current_user.username)
    customer = CustomerController.create(payload, db)
    logger.info("POST /customers — created id=%s", customer.id)
    return JSONResponse(
        status_code=201,
        content=success_response(
            message="Customer created successfully",
            data=CustomerResponse.model_validate(customer).model_dump(mode="json"),
        ).model_dump(),
    )


@app.put("/customers/{customer_id}")
def update_customer(
    customer_id: str,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("PUT /customers/%s — user=%s", customer_id, current_user.username)
    customer = CustomerController.update(customer_id, payload, db)
    logger.info("PUT /customers/%s — updated successfully", customer_id)
    return success_response(
        message="Customer updated successfully",
        data=CustomerResponse.model_validate(customer).model_dump(mode="json"),
    )


@app.delete("/customers/{customer_id}", status_code=200)
def delete_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("DELETE /customers/%s — user=%s", customer_id, current_user.username)
    CustomerController.delete(customer_id, db)
    logger.info("DELETE /customers/%s — deleted successfully", customer_id)
    return success_response(message="Customer deleted successfully")
