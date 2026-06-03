"""
Reg Factory — Event Listener + Auto-Delivery Bot
Monitors the RegFactory contract for AccountMinted events and sends accounts via Telegram.
"""

import os
import json
import time
import logging
from web3 import Web3
from web3.middleware import geth_poa_middleware
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# ── Config ──
RPC_URL = os.getenv('RPC_URL', 'https://bsc-dataseed.binance.org/')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '0xAF73362CC150eb9d92c2abd84c1F88D4DB7dc0E5')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '30'))  # seconds

# Account pool (simulated — replace with real reg-factory output)
ACCOUNT_POOL = [
    {"email": "acc1@outlook.com", "password": "pass1", "chatgpt_cookie": "sk-xxx1", "claude_cookie": "session-xxx1", "grok_cookie": "token-xxx1"},
    {"email": "acc2@outlook.com", "password": "pass2", "chatgpt_cookie": "sk-xxx2", "claude_cookie": "session-xxx2", "grok_cookie": "token-xxx2"},
    # ... loaded dynamically from reg-factory output
]

# ── Web3 Setup ──
w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Contract ABI (minimal — just the event)
CONTRACT_ABI = json.loads('''[
  {"type":"event","name":"AccountMinted","inputs":[
    {"name":"user","type":"address","indexed":true},
    {"name":"tokenId","type":"uint256","indexed":true},
    {"name":"quantity","type":"uint256","indexed":false},
    {"name":"totalPaid","type":"uint256","indexed":false},
    {"name":"timestamp","type":"uint256","indexed":false}
  ]}
]''')

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)

# ── Telegram ──
def send_telegram(user_address: str, accounts: list):
    """Send account credentials to the user via Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        log.warning("TELEGRAM_BOT_TOKEN not set, skipping notification")
        return

    msg = f"🎉 *MINT DELIVERED!*\n\n"
    msg += f"Address: `{user_address}`\n"
    msg += f"Accounts: {len(accounts)}\n\n"
    for i, acc in enumerate(accounts, 1):
        msg += f"*Account {i}:*\n"
        msg += f"Email: `{acc['email']}`\n"
        msg += f"Password: `{acc['password']}`\n"
        msg += f"ChatGPT: `{acc['chatgpt_cookie']}`\n"
        msg += f"Claude: `{acc['claude_cookie']}`\n"
        msg += f"Grok: `{acc['grok_cookie']}`\n\n"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            log.error(f"Telegram send failed: {resp.text}")
    except Exception as e:
        log.error(f"Telegram error: {e}")


def get_available_accounts(quantity: int) -> list:
    """Pop accounts from pool. In production, pull from reg-factory output."""
    if len(ACCOUNT_POOL) < quantity:
        log.warning(f"Not enough accounts in pool: need {quantity}, have {len(ACCOUNT_POOL)}")
        return []
    accounts = ACCOUNT_POOL[:quantity]
    del ACCOUNT_POOL[:quantity]
    return accounts


# ── Main Loop ──
def main():
    log.info(f"Starting Reg Factory listener on contract {CONTRACT_ADDRESS}")
    log.info(f"Poll interval: {POLL_INTERVAL}s")
    log.info(f"Accounts in pool: {len(ACCOUNT_POOL)}")

    last_block = w3.eth.block_number

    while True:
        try:
            current_block = w3.eth.block_number
            if current_block > last_block:
                # Get AccountMinted events from new blocks
                events = contract.events.AccountMinted.get_logs(
                    from_block=last_block,
                    to_block=current_block
                )

                for event in events:
                    args = event['args']
                    user = args['user']
                    quantity = args['quantity']
                    token_id = args['tokenId']
                    total_paid = args['totalPaid']

                    log.info(f"Mint detected: user={user} qty={quantity} tokenId={token_id} paid={total_paid}")

                    # Deliver accounts
                    accounts = get_available_accounts(quantity)
                    if accounts:
                        send_telegram(user, accounts)
                        log.info(f"Delivered {len(accounts)} accounts to {user}")
                    else:
                        log.warning(f"No accounts available for {user}, tokenId={token_id}")

                last_block = current_block

        except Exception as e:
            log.error(f"Error in poll loop: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
