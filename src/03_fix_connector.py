import os
import json
import boto3
from botocore.exceptions import ClientError, LoginRefreshRequired


REGION = os.getenv("REGION", "us-west-2")
PAYMENT_MANAGER_ID = os.getenv("PAYMENT_MANAGER_ID", "paymentmanager-kkrc0cwayx")
PAYMENT_CONNECTOR_ID = os.getenv("PAYMENT_CONNECTOR_ID", "test1234-wxxu1phdpx")
PROVIDER_NAME = os.getenv("PAYMENT_PROVIDER_NAME", "coinbase-provider-main")


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"missing env var: {name}")
    return value


def find_provider_arn_by_name(control, provider_name: str) -> str | None:
    providers = control.list_payment_credential_providers().get(
        "paymentCredentialProviders", []
    )
    for provider in providers:
        if provider.get("name") != provider_name:
            continue
        arn = provider.get("paymentCredentialProviderArn") or provider.get(
            "credentialProviderArn"
        )
        if arn:
            return arn
    return None


def main() -> int:
    control = boto3.client("bedrock-agentcore-control", region_name=REGION)

    # 1) provider resolve/create (idempotent)
    provider_arn = find_provider_arn_by_name(control, PROVIDER_NAME)
    if provider_arn:
        print(f"provider already exists; reusing: {PROVIDER_NAME}")
    else:
        api_key_id = required_env("COINBASE_API_KEY_ID")
        api_key_secret = required_env("COINBASE_API_KEY_SECRET")
        wallet_secret = required_env("COINBASE_WALLET_SECRET")

        try:
            create_res = control.create_payment_credential_provider(
                name=PROVIDER_NAME,
                credentialProviderVendor="CoinbaseCDP",
                providerConfigurationInput={
                    "coinbaseCdpConfiguration": {
                        "apiKeyId": api_key_id,
                        "apiKeySecret": api_key_secret,
                        "walletSecret": wallet_secret,
                    }
                },
            )
        except ClientError as e:
            if (
                e.response.get("Error", {}).get("Code") == "ValidationException"
                and "already exists" in str(e)
            ):
                provider_arn = find_provider_arn_by_name(control, PROVIDER_NAME)
                if not provider_arn:
                    raise RuntimeError(
                        "Provider already exists but ARN could not be resolved by name"
                    ) from e
            else:
                raise

        if not provider_arn:
            # API model returns `credentialProviderArn` for this operation.
            provider_arn = (
                create_res.get("credentialProviderArn")
                or create_res.get("paymentCredentialProviderArn")
            )

    if not provider_arn:
        raise RuntimeError("Failed to resolve provider ARN")

    # 2) connector update
    update_res = control.update_payment_connector(
        paymentManagerId=PAYMENT_MANAGER_ID,
        paymentConnectorId=PAYMENT_CONNECTOR_ID,
        type="CoinbaseCDP",
        credentialProviderConfigurations=[
            {"coinbaseCDP": {"credentialProviderArn": provider_arn}}
        ],
    )

    print("provider resolved and connector updated")
    print(json.dumps({
        "providerArn": provider_arn,
        "connectorId": update_res.get("paymentConnectorId"),
        "connectorStatus": update_res.get("status"),
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}")
        if isinstance(e, ValueError) and "missing env var:" in str(e):
            print("Set required env vars:")
            print("  COINBASE_API_KEY_ID")
            print("  COINBASE_API_KEY_SECRET")
            print("  COINBASE_WALLET_SECRET")
        elif isinstance(e, LoginRefreshRequired) or "refresh token has expired" in str(e):
            print("Run `aws login` and retry.")
        raise
