from neo_api_client import NeoAPI

spot_data = client.search_scrip(
    exchange_segment="nse_cm",
    symbol="NIFTY"
)

print(spot_data)