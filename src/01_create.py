import boto3
import logging
import re
from botocore.exceptions import ClientError

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS clients
control_client = boto3.client('bedrock-agentcore-control', region_name='us-west-2')
agentcore_client = boto3.client('bedrock-agentcore', region_name='us-west-2')

REGION = "us-west-2"
PAYMENT_MANAGER_NAME = "paymentmanager-sample"
PAYMENT_CONNECTOR_NAME = "stripe-connector-sample"

# Step 1: Payment Manager作成（または既存のものを列挙）
try:
    logger.info("=== Step 1: List existing Payment Managers ===")
    response = control_client.list_payment_managers()
    payment_managers = response.get('paymentManagers', [])
    logger.info(f"Found {len(payment_managers)} payment manager(s)")
    
    if payment_managers:
        manager_arn = payment_managers[0]['paymentManagerArn']
        logger.info(f"Using existing Payment Manager: {manager_arn}")
    else:
        logger.error("No payment managers found. Please create one via AWS Console or API.")
        logger.info("To create a Payment Manager, use: agentcore_client.create_payment_manager(...)")
        raise ValueError("Payment Manager not found in account")

except ClientError as e:
    logger.error(f"Failed to list payment managers: {e}")
    raise

# Step 2: List existing Payment Connectors
try:
    logger.info("\n=== Step 2: List existing Payment Connectors ===")
    # Extract Payment Manager ID from ARN
    manager_id = manager_arn.split('/')[-1]
    logger.info(f"Payment Manager ID: {manager_id}")
    
    # Using control client to list connectors
    response = control_client.list_payment_connectors(paymentManagerId=manager_id)
    connectors = response.get('paymentConnectors', [])
    logger.info(f"Found {len(connectors)} payment connector(s)")
    
    provider_arns = {
        p.get('paymentCredentialProviderArn')
        for p in control_client.list_payment_credential_providers().get('paymentCredentialProviders', [])
        if p.get('paymentCredentialProviderArn')
    }

    usable_connector = None
    connector_id_pattern = re.compile(r"([0-9a-z]-?){1,100}-[0-9a-z]{10}$")

    for c in connectors:
        cid = c.get('paymentConnectorId', '')
        try:
            detail = control_client.get_payment_connector(
                paymentManagerId=manager_id,
                paymentConnectorId=cid,
            )
        except Exception as ge:
            logger.warning(f"Skip connector {cid}: detail取得不可 ({ge})")
            continue

        if not connector_id_pattern.match(cid):
            logger.warning(f"Skip connector {cid}: ID形式が不正")
            continue
        if detail.get('status') != 'READY':
            logger.warning(f"Skip connector {cid}: status={detail.get('status')}")
            continue

        referenced_arns = []
        for cfg in detail.get('credentialProviderConfigurations', []):
            coinbase_arn = cfg.get('coinbaseCDP', {}).get('credentialProviderArn')
            stripe_arn = cfg.get('stripePrivy', {}).get('credentialProviderArn')
            if coinbase_arn:
                referenced_arns.append(coinbase_arn)
            if stripe_arn:
                referenced_arns.append(stripe_arn)

        missing_arns = [arn for arn in referenced_arns if arn not in provider_arns]
        if missing_arns:
            logger.warning(f"Skip connector {cid}: provider未登録 {missing_arns}")
            continue

        usable_connector = cid
        break

    if usable_connector:
        logger.info(f"Using existing Payment Connector: {usable_connector}")
        PAYMENT_CONNECTOR_ID = usable_connector
    else:
        logger.error("No usable payment connector found.")
        logger.info("要件: READY status, 正しいID形式, 参照credential providerが実在")
        raise ValueError("Usable Payment Connector not found")

except ClientError as e:
    if "AccessDenied" in str(e):
        logger.warning(f"Access denied to list payment connectors: {e}")
        raise
    else:
        logger.error(f"Failed to list payment connectors: {e}")
        raise

except Exception as e:
    logger.error(f"Unexpected error listing payment connectors: {e}")
    raise

# Step 3: Create or retrieve Payment Manager
try:
    logger.info(f"\n=== Step 3: Confirm Payment Manager ===")
    from bedrock_agentcore.payments import PaymentManager
    
    manager = PaymentManager(
        payment_manager_arn=manager_arn,
        region_name=REGION
    )
    logger.info(f"PaymentManager initialized: {manager_arn}")
    
except Exception as e:
    logger.error(f"Failed to initialize PaymentManager: {e}")
    raise

logger.info("\n=== Configuration Summary ===")
logger.info(f"Payment Manager ARN: {manager_arn}")
logger.info(f"Payment Connector ID: {PAYMENT_CONNECTOR_ID}")
logger.info(f"Region: {REGION}")

print("\n✅ Setup complete - these values are required for create_payment_instrument")
print(f"PAYMENT_MANAGER_ARN = '{manager_arn}'")
print(f"PAYMENT_CONNECTOR_ID = '{PAYMENT_CONNECTOR_ID}'")
