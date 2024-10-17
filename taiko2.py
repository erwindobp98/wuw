from web3 import Web3
import time
import os

taiko_rpc_url = "https://rpc.taiko.tools"
web3 = Web3(Web3.HTTPProvider(taiko_rpc_url))

if not web3.is_connected():
    print("Tidak dapat terhubung ke jaringan Taiko.")
    exit()

private_key = "isi private key"  # Ganti dengan private key
my_address = Web3.to_checksum_address("isi wallet address")  # Alamat dompet Anda

weth_contract_address = Web3.to_checksum_address("0xA51894664A773981C6C112C43ce576f315d5b1B6")

weth_abi = '''
[
    {
        "constant":true,
        "inputs":[{"name":"account","type":"address"}],
        "name":"balanceOf",
        "outputs":[{"name":"balance","type":"uint256"}],
        "payable":false,
        "stateMutability":"view",
        "type":"function"
    },
    {
        "constant":false,
        "inputs":[{"name":"wad","type":"uint256"}],
        "name":"withdraw",
        "outputs":[],
        "payable":false,
        "stateMutability":"nonpayable",
        "type":"function"
    },
    {
        "constant":false,
        "inputs":[{"name":"wad","type":"uint256"}],
        "name":"deposit",
        "outputs":[],
        "payable":true,
        "stateMutability":"payable",
        "type":"function"
    }
]
'''

weth_contract = web3.eth.contract(address=weth_contract_address, abi=weth_abi)

amount_in_wei = web3.to_wei(0.000013, 'ether') # Nilai Swap

gas_price_gwei = 0.14 # Nilai Gwei
max_priority_fee_per_gas = web3.to_wei(gas_price_gwei, 'gwei')
max_fee_per_gas = web3.to_wei(gas_price_gwei, 'gwei')

def check_eth_balance():
    balance = web3.eth.get_balance(my_address)
    return balance

def check_weth_balance():
    return weth_contract.functions.balanceOf(my_address).call()

def get_next_nonce():
    return web3.eth.get_transaction_count(my_address)

def has_sufficient_balance(amount_in_wei, is_wrap=True):
    try:
        if is_wrap:
            gas_estimate = weth_contract.functions.deposit(amount_in_wei).estimate_gas({'from': my_address, 'value': amount_in_wei})
        else:
            gas_estimate = weth_contract.functions.withdraw(amount_in_wei).estimate_gas({'from': my_address})
        
        total_cost = max_priority_fee_per_gas * gas_estimate
        
        if is_wrap:
            return check_eth_balance() >= total_cost
        else:
            return check_weth_balance() >= amount_in_wei
    except Exception as e:
        print(f"Error saat memeriksa saldo: {e}")
        return False

def wait_for_confirmation(tx_hash, timeout=300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            if receipt and receipt['status'] == 1:
                print(f"Status: Transaksi {web3.to_hex(tx_hash)} berhasil dikonfirmasi.")
                return True
            elif receipt and receipt['status'] == 0:
                print(f"Status: Transaksi {web3.to_hex(tx_hash)} gagal.")
                return False
        except Exception as e:
            pass
        time.sleep(30)
    print(f"Status: Timeout menunggu konfirmasi untuk transaksi {web3.to_hex(tx_hash)}.")
    return False

def wrap_eth_to_weth(amount_in_wei):
    if not has_sufficient_balance(amount_in_wei, is_wrap=True):
        print("Saldo ETH tidak cukup untuk wrapping. Menunggu hingga cukup.")
        return False

    nonce = get_next_nonce()
    gas_estimate = weth_contract.functions.deposit(amount_in_wei).estimate_gas({'from': my_address, 'value': amount_in_wei})
    
    transaction = {
        'to': weth_contract_address,
        'chainId': 167000,
        'gas': gas_estimate,
        'maxFeePerGas': max_fee_per_gas,
        'maxPriorityFeePerGas': max_priority_fee_per_gas,
        'nonce': nonce,
        'value': amount_in_wei,
        'data': '0xd0e30db0'
    }

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"\nStatus: Wrapping ETH ke WETH berhasil dikirim.")
        print(f"Tx Hash: {web3.to_hex(tx_hash)}")
        if wait_for_confirmation(tx_hash):
            return True
    except Exception as e:
        print(f"Error saat mengirim transaksi wrapping: {e}")
    return False

def unwrap_weth_to_eth(amount_in_wei):
    if not has_sufficient_balance(amount_in_wei, is_wrap=False):
        print("Saldo WETH tidak cukup untuk unwrapping. Menunggu hingga cukup.")
        return False

    nonce = get_next_nonce()
    gas_estimate = weth_contract.functions.withdraw(amount_in_wei).estimate_gas({'from': my_address})
    
    transaction = {
        'to': weth_contract_address,
        'chainId': 167000,
        'gas': gas_estimate,
        'maxFeePerGas': max_fee_per_gas,
        'maxPriorityFeePerGas': max_priority_fee_per_gas,
        'nonce': nonce,
        'data': '0x2e1a7d4d' + amount_in_wei.to_bytes(32, 'big').hex()
    }

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"\nStatus: Unwrapping WETH ke ETH berhasil dikirim.")
        print(f"Tx Hash: {web3.to_hex(tx_hash)}")
        if wait_for_confirmation(tx_hash):
            return True
    except Exception as e:
        print(f"Error saat mengirim transaksi unwrapping: {e}")
    return False

wrap_counter = 0
unwrap_counter = 0
total_tx = 0

while total_tx < 82:
    if wrap_counter < 41 and total_tx < 82:
        if wrap_eth_to_weth(amount_in_wei):
            wrap_counter += 1
            total_tx += 1
            print(f"Total Transaksi: {total_tx} (Wrapping: {wrap_counter})")
    
    if unwrap_counter < 41 and total_tx < 82:
        if unwrap_weth_to_eth(amount_in_wei):
            unwrap_counter += 1
            total_tx += 1
            print(f"Total Transaksi: {total_tx} (Unwrapping: {unwrap_counter})")

    if total_tx >= 82:
        break

    time.sleep(10)
