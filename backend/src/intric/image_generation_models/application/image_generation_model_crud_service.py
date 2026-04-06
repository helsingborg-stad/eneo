from typing import TYPE_CHECKING, Union

from intric.main.models import NOT_PROVIDED, ModelId
from intric.roles.permissions import Permission, validate_permissions

if TYPE_CHECKING:
    from uuid import UUID

    from intric.image_generation_models.domain.image_generation_model_repo import (
        ImageGenerationModelRepository,
    )
    from intric.main.models import NotProvided
    from intric.security_classifications.domain.repositories.security_classification_repo_impl import (  # noqa: E501
        SecurityClassificationRepoImpl,
    )
    from intric.users.user import UserInDB


class ImageGenerationModelCRUDService:
    def __init__(
        self,
        user: "UserInDB",
        image_generation_model_repo: "ImageGenerationModelRepository",
        security_classification_repo: "SecurityClassificationRepoImpl",
    ):
        self.image_generation_model_repo = image_generation_model_repo
        self.security_classification_repo = security_classification_repo
        self.user = user

    async def get_image_generation_models(self):
        return await self.image_generation_model_repo.all()

    async def get_image_generation_model(self, model_id: "UUID"):
        return await self.image_generation_model_repo.one(model_id=model_id)

    @validate_permissions(Permission.ADMIN)
    async def update_image_generation_model(
        self,
        model_id: "UUID",
        is_org_enabled: Union[bool, "NotProvided"],
        security_classification: Union[ModelId, None, "NotProvided"] = NOT_PROVIDED,
    ):
        image_generation_model = await self.image_generation_model_repo.one(model_id=model_id)

        if security_classification is not NOT_PROVIDED:
            if security_classification is None:
                image_generation_model.security_classification = None
            else:
                em_security_classification = await self.security_classification_repo.one(
                    id=security_classification.id
                )
                image_generation_model.security_classification = em_security_classification

        image_generation_model.update(is_org_enabled=is_org_enabled)

        return await self.image_generation_model_repo.update(image_generation_model)
