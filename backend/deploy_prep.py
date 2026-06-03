"""
Deploy RegFactory.sol to BSC via raw RPC calls.
Requires: compiled bytecode + abi already provided.
"""
import json
import requests
import hashlib
import hmac

# ── Config ──
PRIVATE_KEY = '3794ca64fc56fd04fb38f85e0f7652d32da9f5796f9f71050f48e600ecb9280d'
RPC_URL = 'https://bsc-dataseed.binance.org/'

# Solidity 0.8.20+ with OpenZeppelin imports — need to compile offline first
# Using a pre-compiled bytecode from Remix or Hardhat

# For now, let's use a simpler approach — we'll prepare the deploy tx
# using eth_account library or just send raw tx

def get_nonce(address):
    resp = requests.post(RPC_URL, json={
        "jsonrpc": "2.0", "method": "eth_getTransactionCount",
        "params": [address, "latest"], "id": 1
    })
    return int(resp.json()['result'], 16)

def get_gas_price():
    resp = requests.post(RPC_URL, json={
        "jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1
    })
    return int(resp.json()['result'], 16)

def estimate_gas(tx_data):
    resp = requests.post(RPC_URL, json={
        "jsonrpc": "2.0", "method": "eth_estimateGas",
        "params": [tx_data], "id": 1
    })
    return int(resp.json()['result'], 16)

# Print info
addr = '0xab6dab4b9502c723160e357c4ffc935744da7f75'
print(f"Deployer: {addr}")
print(f"Nonce: {get_nonce(addr)}")
print(f"Gas price: {get_gas_price()}")
print(f"Gas price (gwei): {get_gas_price() / 1e9:.2f}")
