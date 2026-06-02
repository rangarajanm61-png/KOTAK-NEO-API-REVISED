from neo_api_client import NeoAPI

consumer_key = input("Enter consumer key: ")

client = NeoAPI(
    consumer_key=consumer_key,
    environment="prod"
)

ucc = input("Enter Kotak UCC/client code: ")
totp = input("Enter TOTP from authenticator app: ")

response = client.totp_login(
    ucc=ucc,
    totp=totp
)

print("Login response:", response)
