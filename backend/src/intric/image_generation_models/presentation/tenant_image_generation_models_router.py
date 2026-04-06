from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

import sqlalchemy as sa

from intric.authentication.auth_dependencies import get_current_active_user
from intric.database.database import AsyncSession, get_session_with_transaction
from intric.database.tables.ai_models_table import ImageGenerationModels
from intric.database.tables.model_providers_table import ModelProviders
from intric.image_generation_models.domain.image_generation_model_repo import (
    ImageGenerationModelRepository,
)
from intric.image_generation_models.presentation.image_generation_model_models import (
    ImageGenerationModelPublic,
)
from intric.main.exceptions import (
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
)
from intric.server.protocol import responses
from intric.users.user import UserInDB

router = APIRouter()


class TenantImageGenerationModelCreate(BaseModel):
    provider_id: UUID = Field(..., description="Model provider ID")
    name: str = Field(
        ...,
        description="Model identifier (e.g., 'dall-e-3', 'stable-diffusion-xl')",
    )
    display_name: str = Field(..., description="User-friendly display name")
    family: str = Field(
        default="openai",
        description="Model family (e.g., 'openai', 'stability', 'flux')",
    )
    hosting: str = Field(default="swe", description="Hosting location (swe, eu, usa)")
    is_active: bool = Field(default=True, description="Enable in organization")


class TenantImageGenerationModelUpdate(BaseModel):
    display_name: str | None = Field(None, description="User-friendly display name")
    description: str | None = Field(None, description="Model description")
    family: str | None = Field(None, description="Model family")
    hosting: str | None = Field(None, description="Hosting location (swe, eu, usa)")
    open_source: bool | None = Field(None, description="Is the model open source")
    stability: str | None = Field(
        None, description="Model stability (stable, experimental)"
    )


@router.post(
    "/",
    response_model=ImageGenerationModelPublic,
    responses=responses.get_responses([400, 404]),
)
async def create_tenant_image_generation_model(
    model_create: TenantImageGenerationModelCreate,
    user: UserInDB = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session_with_transaction),
):
    stmt = sa.select(ModelProviders).where(
        ModelProviders.id == model_create.provider_id,
        ModelProviders.tenant_id == user.tenant_id,
    )
    result = await session.execute(stmt)
    provider = result.scalar_one_or_none()

    if not provider:
        raise NotFoundException(
            "Model provider not found or does not belong to your organization"
        )

    if not provider.is_active:
        raise BadRequestException("Model provider is not active")

    new_model = ImageGenerationModels(
        tenant_id=user.tenant_id,
        provider_id=model_create.provider_id,
        name=model_create.name,
        litellm_model_name=None,
        family=model_create.family,
        hosting=model_create.hosting,
        org=None,
        stability="stable",
        open_source=False,
        nickname=model_create.display_name,
        description=None,
        hf_link=None,
        is_deprecated=False,
        is_enabled=model_create.is_active,
        security_classification_id=None,
    )

    session.add(new_model)
    await session.flush()

    repo = ImageGenerationModelRepository(session, user)
    image_generation_model = await repo.one(new_model.id)

    await session.commit()

    return ImageGenerationModelPublic.from_domain(image_generation_model)


@router.put(
    "/{model_id}/",
    response_model=ImageGenerationModelPublic,
    responses=responses.get_responses([403, 404]),
)
async def update_tenant_image_generation_model(
    model_id: UUID,
    model_update: TenantImageGenerationModelUpdate,
    user: UserInDB = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session_with_transaction),
):
    stmt = sa.select(ImageGenerationModels).where(
        ImageGenerationModels.id == model_id,
        ImageGenerationModels.tenant_id == user.tenant_id,
    )
    result = await session.execute(stmt)
    model = result.scalar_one_or_none()

    if not model:
        raise NotFoundException(
            "Model not found or does not belong to your organization"
        )

    if model.tenant_id is None:
        raise UnauthorizedException("Cannot update global models")

    if model_update.display_name is not None:
        model.nickname = model_update.display_name
    if model_update.description is not None:
        model.description = model_update.description
    if model_update.family is not None:
        model.family = model_update.family
    if model_update.hosting is not None:
        model.hosting = model_update.hosting
    if model_update.open_source is not None:
        model.open_source = model_update.open_source
    if model_update.stability is not None:
        model.stability = model_update.stability

    await session.flush()

    repo = ImageGenerationModelRepository(session, user)
    image_generation_model = await repo.one(model.id)

    await session.commit()

    return ImageGenerationModelPublic.from_domain(image_generation_model)


@router.delete(
    "/{model_id}/",
    responses=responses.get_responses([403, 404]),
)
async def delete_tenant_image_generation_model(
    model_id: UUID,
    user: UserInDB = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session_with_transaction),
):
    stmt = sa.select(ImageGenerationModels).where(
        ImageGenerationModels.id == model_id,
        ImageGenerationModels.tenant_id == user.tenant_id,
    )
    result = await session.execute(stmt)
    model = result.scalar_one_or_none()

    if not model:
        raise NotFoundException(
            "Model not found or does not belong to your organization"
        )

    if model.tenant_id is None:
        raise UnauthorizedException("Cannot delete global models")

    try:
        await session.delete(model)
        await session.commit()
    except sa.exc.IntegrityError:
        await session.rollback()
        raise BadRequestException("MODEL_IN_USE")

    return {"success": True}
