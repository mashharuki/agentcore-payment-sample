import boto3

agentcore_client = boto3.client(
    'bedrock-agentcore-control',
    region_name='us-east-2'
)

# 有料API(x402対応のリソースサーバー)を探す
target = agentcore_client.create_gateway_target(
    gatewayIdentifier="my-gateway",
    name="Coinbasex402BazaarTarget",
    description="Coinbase x402 Bazaar MCP server for paid API discovery",
    targetConfiguration={
        "mcp": {
            "mcpServer": {
                "endpoint": "https://api.cdp.coinbase.com/platform/v2/x402/discovery/mcp"
            }
        }
    }
)