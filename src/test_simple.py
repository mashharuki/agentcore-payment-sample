#!/usr/bin/env python3
"""
Payment Instrument 作成テスト - LinkedAccounts が必須
"""
import logging
from bedrock_agentcore.payments import PaymentManager

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PAYMENT_MANAGER_ARN = "arn:aws:bedrock-agentcore:us-west-2:796032104877:payment-manager/paymentmanager-kkrc0cwayx"
PAYMENT_CONNECTOR_ID = "test1234-wxxu1phdpx"
REGION = "us-west-2"
USER_ID = "test-user-123"

manager = PaymentManager(
    payment_manager_arn=PAYMENT_MANAGER_ARN,
    region_name=REGION
)

# linkedAccounts は必須だと判明したので、シンプルに試す
try:
    logger.info("Creating payment instrument with linkedAccounts...")
    instrument = manager.create_payment_instrument(
        user_id=USER_ID,
        payment_connector_id=PAYMENT_CONNECTOR_ID,
        payment_instrument_type="EMBEDDED_CRYPTO_WALLET",
        payment_instrument_details={
            "embeddedCryptoWallet": {
                "network": "ETHEREUM",
                "linkedAccounts": [{"email": {"emailAddress": "test@example.com"}}]
            }
        }
    )
    logger.info(f"✅ SUCCESS!")
    logger.info(f"Instrument ID: {instrument.get('paymentInstrumentId')}")
except Exception as e:
    logger.error(f"❌ FAILED: {str(e)[:300]}")
    # エラーの詳細を表示
    import traceback
    traceback.print_exc()
