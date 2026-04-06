from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from intric.database.tables.ai_models_table import ImageGenerationModels
from intric.database.tables.model_providers_table import ModelProviders
from intric.database.tables.security_classifications_table import SecurityClassification
from intric.image_generation_models.domain.image_generation_model import ImageGenerationModel
from intric.main.exceptions import NotFoundException

if TYPE_CHECKING:
    from uuid import UUID

    from intric.database.database import AsyncSession
    from intric.users.user import UserInDB


class ImageGenerationModelRepository:
    def __init__(self, session: "AsyncSession", user: "UserInDB"):
        self.session = session
        self.user = user

    async def all(self, with_deprecated: bool = False):
        stmt = (
            sa.select(ImageGenerationModels, ModelProviders.name, ModelProviders.provider_type)
            .outerjoin(ModelProviders, ImageGenerationModels.provider_id == ModelProviders.id)
            .options(
                selectinload(ImageGenerationModels.security_classification),
                selectinload(ImageGenerationModels.security_classification).options(
                    selectinload(SecurityClassification.tenant)
                ),
            )
            .where(
                sa.or_(
                    ImageGenerationModels.tenant_id.is_(None),
                    ImageGenerationModels.tenant_id == self.user.tenant_id
                )
            )
            .order_by(
                ImageGenerationModels.org,
                ImageGenerationModels.created_at,
                ImageGenerationModels.name,
            )
        )

        if not with_deprecated:
            stmt = stmt.where(ImageGenerationModels.is_deprecated == False)  # noqa

        result = await self.session.execute(stmt)
        rows = result.all()

        return [
            ImageGenerationModel.to_domain(
                db_model=image_generation_model,
                user=self.user,
                provider_name=provider_name,
                provider_type=provider_type,
            )
            for image_generation_model, provider_name, provider_type in rows
        ]

    async def one_or_none(self, model_id: "UUID") -> Optional["ImageGenerationModel"]:
        stmt = (
            sa.select(ImageGenerationModels, ModelProviders.name, ModelProviders.provider_type)
            .outerjoin(ModelProviders, ImageGenerationModels.provider_id == ModelProviders.id)
            .options(
                selectinload(ImageGenerationModels.security_classification),
                selectinload(ImageGenerationModels.security_classification).options(
                    selectinload(SecurityClassification.tenant)
                ),
            )
            .where(
                ImageGenerationModels.id == model_id,
                sa.or_(
                    ImageGenerationModels.tenant_id.is_(None),
                    ImageGenerationModels.tenant_id == self.user.tenant_id
                )
            )
        )

        result = await self.session.execute(stmt)
        row = result.one_or_none()

        if row is None:
            return

        image_generation_model, provider_name, provider_type = row
        return ImageGenerationModel.to_domain(
            db_model=image_generation_model,
            user=self.user,
            provider_name=provider_name,
            provider_type=provider_type,
        )

    async def one(self, model_id: "UUID") -> "ImageGenerationModel":
        image_generation_model = await self.one_or_none(model_id=model_id)

        if image_generation_model is None:
            raise NotFoundException()

        return image_generation_model

    async def update(self, image_generation_model: "ImageGenerationModel"):
        security_classification_id = (
            image_generation_model.security_classification.id
            if image_generation_model.security_classification
            else None
        )

        stmt = (
            sa.update(ImageGenerationModels)
            .values(
                is_enabled=image_generation_model.is_org_enabled,
                security_classification_id=security_classification_id,
            )
            .where(
                ImageGenerationModels.id == image_generation_model.id,
                ImageGenerationModels.tenant_id == self.user.tenant_id,
            )
        )
        await self.session.execute(stmt)

        return await self.one(model_id=image_generation_model.id)
