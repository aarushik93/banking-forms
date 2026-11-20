"""Initial schema: funds, applications, audit_events

Revision ID: 0001
Revises:
Create Date: 2026-11-20

"""
import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "funds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.Integer(), nullable=False),
        sa.Column("annual_charge_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_funds_code", "funds", ["code"], unique=True)

    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("reference", sa.String(length=20), nullable=False),
        sa.Column("resume_token", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=10), nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("address_line1", sa.String(length=255), nullable=True),
        sa.Column("address_line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=3), nullable=True),
        sa.Column("postcode", sa.String(length=10), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("years_at_address", sa.Integer(), nullable=True),
        sa.Column("employment_status", sa.String(length=30), nullable=True),
        sa.Column("annual_income", sa.Integer(), nullable=True),
        sa.Column("nationality", sa.String(length=2), nullable=True),
        sa.Column("tax_residency_country", sa.String(length=2), nullable=True),
        sa.Column("tfn", sa.String(length=9), nullable=True),
        sa.Column("fund_code", sa.String(length=20), nullable=True),
        sa.Column("initial_investment", sa.Numeric(12, 2), nullable=True),
        sa.Column("monthly_contribution", sa.Numeric(12, 2), nullable=True),
        sa.Column("source_of_funds", sa.String(length=30), nullable=True),
        sa.Column("account_holder_name", sa.String(length=100), nullable=True),
        sa.Column("bsb", sa.String(length=6), nullable=True),
        sa.Column("account_number", sa.String(length=9), nullable=True),
        sa.Column("accepted_terms", sa.Boolean(), nullable=False),
        sa.Column("accepted_risk", sa.Boolean(), nullable=False),
        sa.Column("consent_kyc", sa.Boolean(), nullable=False),
        sa.Column("kyc_status", sa.String(length=20), nullable=True),
        sa.Column("kyc_reference", sa.String(length=100), nullable=True),
        sa.Column("kyc_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", sa.String(length=20), nullable=True),
        sa.Column("decision_note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_applications_reference", "applications", ["reference"], unique=True)
    op.create_index("ix_applications_status", "applications", ["status"])
    op.create_index("ix_applications_email", "applications", ["email"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "application_id",
            sa.Uuid(),
            sa.ForeignKey("applications.id"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_events_application_id", "audit_events", ["application_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_application_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_applications_email", table_name="applications")
    op.drop_index("ix_applications_status", table_name="applications")
    op.drop_index("ix_applications_reference", table_name="applications")
    op.drop_table("applications")
    op.drop_index("ix_funds_code", table_name="funds")
    op.drop_table("funds")
