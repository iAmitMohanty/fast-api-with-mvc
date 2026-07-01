import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.customer import Customer
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate
from app.repositories.customer_repository import CustomerRepository

logger = logging.getLogger(__name__)


class CustomerController:

    @staticmethod
    def get_all(db: Session) -> list[Customer]:
        return CustomerRepository.find_all(db)

    @staticmethod
    def get_by_id(customer_id: str, db: Session) -> Customer:
        customer = CustomerRepository.find_by_id(customer_id, db)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id '{customer_id}' not found",
            )
        return customer

    @staticmethod
    def create(payload: CustomerCreate, db: Session) -> Customer:
        if CustomerRepository.find_by_email(payload.email, db):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{payload.email}' is already registered",
            )
        try:
            return CustomerRepository.create(payload, db)
        except IntegrityError as e:
            db.rollback()
            logger.error("DB IntegrityError on create: %s", e.orig)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Database conflict: {e.orig}",
            )

    @staticmethod
    def update(customer_id: str, payload: CustomerUpdate, db: Session) -> Customer:
        customer = CustomerController.get_by_id(customer_id, db)
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )
        if payload.email and payload.email != customer.email:
            if CustomerRepository.find_by_email(payload.email, db):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{payload.email}' is already taken",
                )
        try:
            return CustomerRepository.update(customer, payload, db)
        except IntegrityError as e:
            db.rollback()
            logger.error("DB IntegrityError on update: %s", e.orig)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Database conflict: {e.orig}",
            )

    @staticmethod
    def delete(customer_id: str, db: Session) -> None:
        customer = CustomerController.get_by_id(customer_id, db)
        CustomerRepository.delete(customer, db)
