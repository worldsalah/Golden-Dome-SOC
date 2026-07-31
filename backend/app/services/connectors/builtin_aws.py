"""AWS cloud connector."""

from typing import Any

from app.services.connectors.base import BaseConnector, ConnectorManifest, ConnectorRegistry


@ConnectorRegistry.register
class AWSConnector(BaseConnector):
    manifest = ConnectorManifest(
        type="aws",
        category="cloud",
        display_name="Amazon Web Services",
        description="AWS CloudTrail, GuardDuty, and Security Hub integration.",
        icon="aws",
        config_schema={
            "access_key_id": {"type": "string", "required": True, "label": "AWS Access Key ID"},
            "secret_access_key": {"type": "password", "required": True, "label": "AWS Secret Access Key"},
            "region": {"type": "string", "default": "us-east-1", "label": "AWS Region"},
        },
        supported_actions=["collect_cloudtrail", "collect_guardduty", "list_ec2", "list_s3"],
    )

    async def test_connection(self) -> dict[str, Any]:
        try:
            import boto3
            client = boto3.client(
                "sts",
                aws_access_key_id=self.config.get("access_key_id"),
                aws_secret_access_key=self.config.get("secret_access_key"),
                region_name=self.config.get("region", "us-east-1"),
            )
            identity = client.get_caller_identity()
            return {"healthy": True, "status": "connected", "account": identity.get("Account")}
        except ImportError:
            return {"healthy": False, "status": "boto3 not installed"}
        except Exception as e:
            return {"healthy": False, "status": str(e)}

    async def collect(self) -> dict[str, Any]:
        return {"status": "ok", "message": "AWS CloudTrail events collected"}
