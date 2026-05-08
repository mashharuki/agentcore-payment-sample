import logging
from bedrock_agentcore.payments import PaymentManager

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定数
PAYMENT_MANAGER_ARN = "arn:aws:bedrock-agentcore:us-west-2:796032104877:payment-manager/paymentmanager-kkrc0cwayx"
PAYMENT_CONNECTOR_ID = "test1234-wxxu1phdpx"
REGION = "us-west-2"
USER_ID = "test-user-123"

# PaymentManager の初期化
try:
    logger.info(f"Initializing PaymentManager: {PAYMENT_MANAGER_ARN}")
    manager = PaymentManager(
        payment_manager_arn=PAYMENT_MANAGER_ARN,
        region_name=REGION
    )
    logger.info("✓ PaymentManager initialized")
except Exception as e:
    logger.error(f"✗ PaymentManager initialization failed: {e}")
    raise

# Pattern 1: Minimal embedded crypto wallet (no linked accounts)
patterns = [
    {
        "name": "Pattern 1: Minimal EMBEDDED_CRYPTO_WALLET (no linked accounts)",
        "instrument_type": "EMBEDDED_CRYPTO_WALLET",
        "details": {
            "embeddedCryptoWallet": {
                "network": "ETHEREUM"
            }
        }
    },
    {
        "name": "Pattern 2: With empty linkedAccounts",
        "instrument_type": "EMBEDDED_CRYPTO_WALLET",
        "details": {
            "embeddedCryptoWallet": {
                "network": "ETHEREUM",
                "linkedAccounts": []
            }
        }
    },
    {
        "name": "Pattern 3: With email linkedAccount",
        "instrument_type": "EMBEDDED_CRYPTO_WALLET",
        "details": {
            "embeddedCryptoWallet": {
                "network": "ETHEREUM",
                "linkedAccounts": [{"email": {"emailAddress": "test@example.com"}}]
            }
        }
    },
    {
        "name": "Pattern 4: Different network (POLYGON)",
        "instrument_type": "EMBEDDED_CRYPTO_WALLET",
        "details": {
            "embeddedCryptoWallet": {
                "network": "POLYGON"
            }
        }
    },
]

# 各パターンで試す
for i, pattern in enumerate(patterns, 1):
    logger.info(f"\n=== Attempting {pattern['name']} ===")
    try:
        logger.info(f"Parameters:")
        logger.info(f"  - connector_id: {PAYMENT_CONNECTOR_ID}")
        logger.info(f"  - instrument_type: {pattern['instrument_type']}")
        logger.info(f"  - details: {pattern['details']}")
        
        instrument = manager.create_payment_instrument(
            user_id=USER_ID,
            payment_connector_id=PAYMENT_CONNECTOR_ID,
            payment_instrument_type=pattern['instrument_type'],
            payment_instrument_details=pattern['details']
        )
        
        logger.info(f"✓✓✓ SUCCESS! ✓✓✓")
        logger.info(f"Created instrument: {instrument}")
        print(f"\n✅ Pattern {i} succeeded:\n{pattern['name']}")
        break
        
    except Exception as e:
        error_str = str(e)
        logger.warning(f"✗ Failed: {error_str[:200]}")
        if "network" in error_str.lower():
            logger.warning("  → Issue with network parameter")
        elif "linkedAccounts" in error_str:
            logger.warning("  → Issue with linkedAccounts parameter")
        elif "not found" in error_str.lower():
            logger.warning("  → Connector or resource not found")
        else:
            logger.warning(f"  → Other error (see details above)")

logger.info("\n=== Test Complete ===")
