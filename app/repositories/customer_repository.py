import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from app.models.customer import Customer
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate


class CustomerRepository:

    @staticmethod
    def find_all(db: Session) -> list[Customer]:
        stmt = select(Customer).order_by(Customer.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def find_by_id(customer_id: str, db: Session) -> Optional[Customer]:
        stmt = select(Customer).where(Customer.id == customer_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def find_by_email(email: str, db: Session) -> Optional[Customer]:
        stmt = select(Customer).where(Customer.email == email)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(payload: CustomerCreate, db: Session) -> Customer:
        customer = Customer(
            id=str(uuid.uuid4()),
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def update(customer: Customer, payload: CustomerUpdate, db: Session) -> Customer:
        update_data = payload.model_dump(exclude_unset=True)
        stmt = (
            update(Customer)
            .where(Customer.id == customer.id)
            .values(**update_data)
            .execution_options(synchronize_session="fetch")
        )
        db.execute(stmt)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def delete(customer: Customer, db: Session) -> None:
        db.delete(customer)
        db.commit()
