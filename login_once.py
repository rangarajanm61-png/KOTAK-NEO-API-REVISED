from neo_api_client import NeoAPI
from dotenv import load_dotenv
import os
from option_chain import calculate_pcr
from option_chain import calculate_greeks
load_dotenv()
import numpy as np
from scipy.stats import norm
from datetime import datetime
consumer_key = os.getenv("CONSUMER_KEY")

client = NeoAPI(
    consumer_key=consumer_key,
    environment="prod"
)

mobile = os.getenv("MOBILE_NUMBER")
ucc = os.getenv("UCC")
totp = input("Enter TOTP from authenticator app: ")

response = client.totp_login(
    mobile_number="+91" + str(mobile),
    ucc=ucc,
    totp=totp
)