from uuid import UUID

from fastapi import APIRouter, Depends

from intric.image_generation_models.presentation.image_generation_model_models import (
    ImageGenerationModelPublic,
    ImageGenerationModelUpdate,
)
from intric.main.container.container import Container
from intric.main.models import NOT_PROVIDED, PaginatedResponse
from intric.roles.permissions import Permission, validate_permission
from intric.server.dependencies.container import get_container
from intric.server.protocol import responses

from intric.audit.application.audit_metadata import AuditMetadata
from intric.audit.domain.action_types import ActionType
from intric.audit.domain.entity_types import EntityType

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ImageGenerationModelPublic])
async def get_image_generation_models(
    container: Container = Depends(get_container(with_user=True)),
):
    service = container.image_generation_model_crud_service()
    models = await service.get_image_generation_models()

    return PaginatedResponse(
        items=[ImageGenerationModelPublic.from_domain(model) for model in models]
    )


@router.get(
    "/{id}/",
    response_model=ImageGenerationModelPublic,
    responses=responses.get_responses([404]),
)
async def get_image_generation_model(
    id: UUID,
    container: Container = Depends(get_container(with_user=True)),
):
    service = container.image_generation_model_crud_service()
    model = await service.get_image_generation_model(model_id=id)

    return ImageGenerationModelPublic.from_domain(model)


@router.post(
    "/{id}/",
    response_model=ImageGenerationModelPublic,
    responses=responses.get_responses([404]),
)
async def update_image_generation_model(
    id: UUID,
    update: ImageGenerationModelUpdate,
    container: Container = Depends(get_container(with_user=True)),
):
    service = container.image_generation_model_crud_service()
    user = container.user()

    validate_permission(user, Permission.ADMIN)

    image_generation_model_repo = container.image_generation_model_repo()
    old_model = await image_generation_model_repo.one(model_id=id)

    model = await service.update_image_generation_model(
        model_id=id,
        is_org_enabled=update.is_org_enabled,
        security_classification=update.security_classification,
    )

    changes = {}

    if update.is_org_enabled is not NOT_PROVIDED:
        if old_model.is_org_enabled != model.is_org_enabled:
            changes["is_org_enabled"] = {
                "old": old_model.is_org_enabled,
                "new": model.is_org_enabled,
            }

    if update.security_classification is not NOT_PROVIDED:
        old_sc_name = (
            old_model.security_classification.name
            if old_model.security_classification
            else None
        )
        new_sc_name = (
            model.security_classification.name
            if model.security_classification
            else None
        )
        if old_sc_name != new_sc_name:
            changes["security_classification"] = {
                "old": old_sc_name,
                "new": new_sc_name,
            }

    if changes:
        audit_service = container.audit_service()
        await audit_service.log_async(
            tenant_id=user.tenant_id,
            actor_id=user.id,
            action=ActionType.IMAGE_GENERATION_MODEL_UPDATED,
            entity_type=EntityType.IMAGE_GENERATION_MODEL,
            entity_id=id,
            description=f"Updated settings for {model.name}",
            metadata=AuditMetadata.standard(
                actor=user,
                target=model,
                changes=changes,
            ),
        )

    return ImageGenerationModelPublic.from_domain(model)
