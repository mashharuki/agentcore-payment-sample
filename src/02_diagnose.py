import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError, LoginRefreshRequired


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


REGION = "us-west-2"
PAYMENT_MANAGER_ID = "paymentmanager-kkrc0cwayx"


def main() -> int:
    control = boto3.client("bedrock-agentcore-control", region_name=REGION)

    try:
        managers = control.list_payment_managers().get("paymentManagers", [])
        logger.info("payment managers: %d", len(managers))

        connectors = control.list_payment_connectors(
            paymentManagerId=PAYMENT_MANAGER_ID
        ).get("paymentConnectors", [])
        logger.info("payment connectors: %d", len(connectors))
        for c in connectors:
            logger.info(
                "connector id=%s status=%s type=%s",
                c.get("paymentConnectorId"),
                c.get("status"),
                c.get("type"),
            )

        providers = control.list_payment_credential_providers().get(
            "paymentCredentialProviders", []
        )
        logger.info("payment credential providers: %d", len(providers))
        for p in providers:
            logger.info(
                "provider id=%s status=%s type=%s",
                p.get("paymentCredentialProviderId"),
                p.get("status"),
                p.get("type"),
            )

    except Exception as e:  # show friendly remediation for auth expiry
        msg = str(e)
        if isinstance(e, LoginRefreshRequired) or "refresh token has expired" in msg:
            logger.error("AWS 認証セッションの期限が切れています。`aws login` を実行してください。")
            return 2
        if isinstance(e, (ClientError, BotoCoreError)):
            logger.error("AWS API エラー: %s", msg)
            return 1
        logger.exception("Unexpected error")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
