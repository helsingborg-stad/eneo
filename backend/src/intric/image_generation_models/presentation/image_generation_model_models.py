from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from intric.image_generation_models.domain.image_generation_model import (
    ImageGenerationModel,
)
from intric.main.models import NOT_PROVIDED, BaseResponse, ModelId, NotProvided
from intric.security_classifications.presentation.security_classification_models import (
    SecurityClassificationPublic,
)


class ImageGenerationModelPublic(BaseResponse):
    name: str
    nickname: Optional[str] = None
    family: Optional[str] = None
    is_deprecated: bool
    open_source: bool
    hf_link: Optional[str] = None
    stability: Optional[str] = None
    hosting: Optional[str] = None
    description: Optional[str] = None
    org: Optional[str] = None
    litellm_model_name: Optional[str] = None
    can_access: bool = False
    is_locked: bool = True
    lock_reason: Optional[str] = None
    is_org_enabled: bool = False
    credential_provider: Optional[str] = None
    security_classification: Optional[SecurityClassificationPublic] = None
    tenant_id: Optional[UUID] = None
    provider_id: Optional[UUID] = None
    provider_name: Optional[str] = None
    provider_type: Optional[str] = None

    @classmethod
    def from_domain(cls, model: ImageGenerationModel):
        security_classification = None
        if model.security_classification:
            security_classification = SecurityClassificationPublic.from_domain(
                model.security_classification,
                return_none_if_not_enabled=False,
            )

        return cls(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            name=model.name,
            nickname=model.nickname,
            family=model.family,
            is_deprecated=model.is_deprecated,
            open_source=model.open_source,
            hf_link=model.hf_link,
            stability=model.stability,
            hosting=model.hosting,
            description=model.description,
            org=model.org,
            litellm_model_name=model.litellm_model_name,
            can_access=model.can_access,
            is_locked=model.is_locked,
            lock_reason=model.lock_reason,
            is_org_enabled=model.is_org_enabled,
            credential_provider=model.get_credential_provider_name(),
            security_classification=security_classification,
            tenant_id=model.tenant_id,
            provider_id=model.provider_id,
            provider_name=model.provider_name,
            provider_type=model.provider_type,
        )


class ImageGenerationModelSecurityStatus(ImageGenerationModelPublic):
    meets_security_classification: Optional[bool] = None


class ImageGenerationModelUpdate(BaseModel):
    is_org_enabled: bool | NotProvided = NOT_PROVIDED
    security_classification: ModelId | None | NotProvided = NOT_PROVIDED
