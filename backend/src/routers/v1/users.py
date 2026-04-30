from uuid import UUID
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException,
    BackgroundTasks,
)


from src.api.schemas import (
    UserOut,
    UserCreate,
    CreateUserResults,
    FailedUser,
    UserUpdate,
)
from src.domain.user import User
from src.domain.enums import Department, UserType

from src.services.user_service import UserService
from src.services.email_service import EmailService
from src.services.auth import AuthService

from src.adapters.unit_of_work import UnitOfWork

from src.dependencies.db import get_uow
from src.dependencies.config import get_config, Config

from src.exceptions import UserAlreadyExistsError, UserNotFoundError
from src.core.security import generate_password, get_password_hash
from src.core.logging import get_logger

logger = get_logger(__name__)


def get_user_service(uow: UnitOfWork = Depends(get_uow)) -> UserService:
    return UserService(uow=uow)


def get_email_service(config: Config = Depends(get_config)) -> EmailService:
    return EmailService(config=config)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
EmailServiceDep = Annotated[EmailService, Depends(get_email_service)]


router: APIRouter = APIRouter(prefix="/users", tags=["users"])


def to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        department=user.department,
        user_type=user.user_type,
    )


@router.get(path="", response_model=list[UserOut])
async def get_all_users(user_service: UserServiceDep):
    users: list[User] = await user_service.get_all_users()
    return [to_user_out(user=user) for user in users]


@router.post(
    path="", response_model=CreateUserResults, status_code=status.HTTP_201_CREATED
)
async def add_users(
    background_tasks: BackgroundTasks,
    new_users: list[UserCreate],
    user_service: UserServiceDep,
    email_service: EmailServiceDep,
):
    logger.info("add_users request received", count=len(new_users))
    users: list = []
    failed_users: list = []
    for user in new_users:
        tmp_pass: str = generate_password()
        tmp_pass_hash: str = get_password_hash(password=tmp_pass)
        new_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            department=user.department,
            user_type=user.user_type,
            hashed_password=tmp_pass_hash,
        )
        try:
            await user_service.create_user(user=new_user)
            users.append(to_user_out(new_user))
            background_tasks.add_task(
                email_service.send_welcome_email, new_user.email, tmp_pass
            )
        except UserAlreadyExistsError as e:
            logger.error(
                "user already exists during bulk create",
                email=new_user.email,
                error=str(e),
            )
            failed_users.append(
                FailedUser(email=new_user.email, reason=f"User already exists: {e}")
            )
    logger.info("add_users complete", created=len(users), failed=len(failed_users))
    return CreateUserResults(success=users, failed=failed_users)


@router.get(path="/{user_id}", response_model=UserOut)
async def get_by_id(user_id: UUID, user_service: UserServiceDep):
    try:
        user: User = await user_service.get_by_id(user_id=user_id)
        return to_user_out(user=user)
    except UserNotFoundError as e:
        logger.error("user not found", user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {user_id} not found",
        )


@router.patch(path="/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID, update_data: UserUpdate, user_service: UserServiceDep
):
    try:
        user: User = await user_service.update_user(
            user_id=user_id,
            first_name=update_data.first_name,
            last_name=update_data.last_name,
            department=update_data.department,
            user_type=update_data.user_type,
            email=update_data.email,
        )
        return to_user_out(user)
    except UserNotFoundError as e:
        logger.error("user not found during update", user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {user_id} not found",
        )


@router.delete(path="/{user_id}")
async def delete_user(user_id: UUID, user_service: UserServiceDep):
    try:
        await user_service.delete_user(user_id=user_id)
    except UserNotFoundError as e:
        logger.error(
            event="User not found during delete", user_id=str(user_id), error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {user_id} not found",
        )


@router.post(path="/{user_id}/reset-user-password")
async def reset_user_password(
    user_id: UUID,
    background_tasks: BackgroundTasks,
    user_service: UserServiceDep,
    email_service: EmailServiceDep,
):
    tmp_password: str = generate_password()
    try:
        user: User = await user_service.reset_user_password(
            user_id=user_id, new_password=tmp_password
        )
        background_tasks.add_task(
            email_service.send_welcome_email, user.email, tmp_password
        )
        return {
            "message": f"user: {user.first_name} has been sent an email with their new credentials"
        }
    except UserNotFoundError as e:
        logger.error(
            "user not found during password reset", user_id=str(user_id), error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {user_id} not found",
        )


@router.post(path="/{user_id}/toggle-user-status", response_model=UserOut)
async def update_user_status(user_id: UUID, user_service: UserServiceDep):
    try:
        user: User = await user_service.toggle_user_status(user_id=user_id)
        return to_user_out(user)
    except UserNotFoundError as e:
        logger.error(
            "user not found during status toggle", user_id=str(user_id), error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {user_id} not found",
        )
