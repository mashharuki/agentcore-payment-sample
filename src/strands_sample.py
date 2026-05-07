# Strands Agentを使った統合パターン
from strands import Agent
from strands_tools import http_request
from bedrock_agentcore.payments import PaymentManager
from bedrock_agentcore.payments.integrations.config import AgentCorePaymentsPluginConfig
from bedrock_agentcore.payments.integrations.strands.plugin import AgentCorePaymentsPlugin

# ここは作成された値を入力する
PAYMENT_MANAGER_ARN = ""
PAYMENT_CONNECTOR_ID = ""

manager = PaymentManager(
    payment_manager_arn=PAYMENT_MANAGER_ARN,
    region_name="us-west-2"
)

# Create payment instrument (Ethereum)
instrument = manager.create_payment_instrument(
    user_id="test-user-123",
    payment_connector_id=PAYMENT_CONNECTOR_ID,
    payment_instrument_type="EMBEDDED_CRYPTO_WALLET",
    payment_instrument_details={"embeddedCryptoWallet": {"network": "ETHEREUM",
    "linkedAccounts": [{
                "email": {
                    "emailAddress": "myemail@example.com"
                }
            }]
   }},
)

# 支払いセッション(100ドル分は承認無しに自動支払いを可能とする)
session = manager.create_payment_session(
    user_id="test-user-123",
    limits={"maxSpendAmount": {"value": "100.00", "currency": "USD"}},
    expiry_time_in_minutes=60
)

# Configure the plugin
config = AgentCorePaymentsPluginConfig(
    payment_manager_arn=PAYMENT_MANAGER_ARN,
    user_id="test-user-123",
    payment_instrument_id=instrument["paymentInstrumentId"],
    payment_session_id=session["paymentSessionId"],
    region="us-west-2",
)

# Create the plugin
plugin = AgentCorePaymentsPlugin(config=config)

# Create agent with the plugin
agent = Agent(
    system_prompt="You are a helpful assistant that can access paid APIs.",
    tools=[http_request],
    plugins=[plugin],
)

# The agent automatically handles 402 responses
agent("Access the premium endpoint at https://api.run402.com/tiers/v1/prototype")