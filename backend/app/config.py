from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, sourced from environment variables (and .env in dev)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"  # dev | test | prod
    log_json: bool = False

    database_url: str = "postgresql+psycopg://bank:bank@localhost:5432/bankforms"

    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    admin_api_token: str = "change-me"

    # Identity verification provider
    kyc_provider: str = "mock"  # mock | idmatrix | experian

    # Equifax IDMatrix (Australia) — production URL: https://vedaxml.com/sys2/idmatrix-v4
    idmatrix_url: str = "https://ctaau.vedaxml.com/cta/sys2/idmatrix-v4"
    idmatrix_username: str = ""
    idmatrix_password: str = ""
    idmatrix_reason_for_enquiry: str = "Account opening"

    # Experian CrossCore (Australia: production host is https://api.experian.com.au)
    experian_base_url: str = "https://sandbox-api.experian.com.au"
    experian_token_path: str = "/oauth2/v1/token"
    # The exact CrossCore endpoint and workflow are assigned during Experian onboarding;
    # the request/response mapping lives in app/adapters/kyc.py.
    experian_kyc_path: str = "/decisionanalytics/crosscore/v2/submit"
    experian_client_id: str = ""
    experian_client_secret: str = ""
    experian_username: str = ""
    experian_password: str = ""

    # Email / SendGrid
    email_provider: str = "console"  # console | sendgrid
    sendgrid_api_key: str = ""
    email_from: str = "investments@example-bank.test"
    email_from_name: str = "Example Bank Investments"

    rate_limit_per_minute: int = 30

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_production_settings(settings: Settings) -> None:
    """Refuse to boot in prod with obviously unsafe configuration."""
    if settings.env != "prod":
        return
    problems: list[str] = []
    if settings.admin_api_token in ("", "change-me") or len(settings.admin_api_token) < 16:
        problems.append("ADMIN_API_TOKEN must be set to a strong value (16+ chars)")
    if settings.kyc_provider == "mock":
        problems.append("KYC_PROVIDER=mock must not be used in prod")
    if settings.kyc_provider == "experian" and not (
        settings.experian_client_id and settings.experian_client_secret
    ):
        problems.append("Experian credentials are required when KYC_PROVIDER=experian")
    if settings.kyc_provider == "idmatrix":
        if not (settings.idmatrix_username and settings.idmatrix_password):
            problems.append("IDMatrix credentials are required when KYC_PROVIDER=idmatrix")
        if "idmatrix-mock" in settings.idmatrix_url or settings.idmatrix_username == "idm-demo":
            problems.append(
                "The bundled IDMatrix mock endpoint/credentials must not be used in prod"
            )
    if settings.email_provider != "sendgrid":
        problems.append("EMAIL_PROVIDER=sendgrid is required in prod")
    if settings.email_provider == "sendgrid" and not settings.sendgrid_api_key:
        problems.append("SENDGRID_API_KEY is required when EMAIL_PROVIDER=sendgrid")
    if problems:
        raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))
