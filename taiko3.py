from web3 import Web3
import time
import os
import random
from colorama import init, Fore, Style

# Inisialisasi colorama
init(autoreset=True)

def art():
    width = 50  # Lebar area teks yang ingin dipusatkan
    print(Fore.YELLOW + r"""
================================================
""" + "Airdrop Community".center(width) + """
================================================
""" + "Bot : TAIKO".center(width) + """
""" + "Telegram Channel : @airdropcom9".center(width) + """
""" + "Telegram Group : @airdropcom8".center(width) + """
================================================
""" + Fore.GREEN)

if __name__ == "__main__":
    art()

# Connect to Taiko RPC
taiko_rpc_url = "https://rpc.ankr.com/taiko"
web3 = Web3(Web3.HTTPProvider(taiko_rpc_url))

# Check network connection
if not web3.is_connected():
    print(Fore.RED + "Tidak dapat terhubung ke jaringan Taiko." + Style.RESET_ALL)  # Red
    exit()

# Replace with your actual private key and address
private_key = "isi private key"  # Ganti dengan private key
my_address = Web3.to_checksum_address("isi address")  # Alamat dompet Anda

weth_contract_address = Web3.to_checksum_address("0xA51894664A773981C6C112C43ce576f315d5b1B6")

# WETH contract ABI
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

# Define gas prices at the top of your script
gas_price_wrap_gwei = 0.11  # Adjust as needed
gas_price_unwrap_gwei = 0.11  # Adjust as needed

# Convert to Wei for use in transactions
max_priority_fee_per_gas_wrap = web3.to_wei(gas_price_wrap_gwei, 'gwei')
max_fee_per_gas_wrap = web3.to_wei(gas_price_wrap_gwei, 'gwei')

max_priority_fee_per_gas_unwrap = web3.to_wei(gas_price_unwrap_gwei, 'gwei')
max_fee_per_gas_unwrap = web3.to_wei(gas_price_unwrap_gwei, 'gwei')


def get_random_amount():
    """Generate a random amount between 0.01 and 0.011 ETH."""
    return web3.to_wei(random.uniform(0.19953, 0.2), 'ether')

def check_eth_balance():
    balance = web3.eth.get_balance(my_address)
    eth_balance = web3.from_wei(balance, 'ether')
    print(Fore.BLUE + f"Saldo ETH: {eth_balance:.6f} ETH" + Style.RESET_ALL)  # Blue
    return balance

def check_weth_balance():
    balance = weth_contract.functions.balanceOf(my_address).call()
    weth_balance = web3.from_wei(balance, 'ether')
    print(Fore.BLUE + f"Saldo WETH: {weth_balance:.6f} WETH" + Style.RESET_ALL)  # Blue
    return balance

def get_next_nonce():
    return web3.eth.get_transaction_count(my_address)

def has_sufficient_balance(amount_in_wei, is_wrap=True, max_priority_fee_per_gas=max_priority_fee_per_gas_wrap, max_fee_per_gas=max_fee_per_gas_wrap):
    try:
        if is_wrap:
            gas_estimate = weth_contract.functions.deposit(amount_in_wei).estimate_gas({'from': my_address, 'value': amount_in_wei})
        else:
            gas_estimate = weth_contract.functions.withdraw(amount_in_wei).estimate_gas({'from': my_address})

        total_cost = max_priority_fee_per_gas * gas_estimate
        # Check ETH or WETH balance based on transaction type
        if is_wrap:
            eth_balance = check_eth_balance()
            if eth_balance >= total_cost:
                print(Fore.GREEN + f"Sufficient ETH Balance. Required: {web3.from_wei(total_cost, 'ether')} ETH" + Style.RESET_ALL)
                return True
            else:
                print(Fore.YELLOW + f"Insufficient funds. Balance: {web3.from_wei(eth_balance, 'ether')} ETH, Required: {web3.from_wei(total_cost, 'ether')} ETH" + Style.RESET_ALL)
        else:
            weth_balance = check_weth_balance()
            if weth_balance >= amount_in_wei:
                print(Fore.GREEN + f"Sufficient WETH Balance. Required: {web3.from_wei(amount_in_wei, 'ether')} WETH" + Style.RESET_ALL)
                return True
            else:
                print(Fore.YELLOW + f"Insufficient funds. Balance: {web3.from_wei(weth_balance, 'ether')} WETH, Required: {web3.from_wei(amount_in_wei, 'ether')} WETH" + Style.RESET_ALL)
        return False
    except Exception as e:
        print(Fore.RED + f"Error estimating gas: {e}" + Style.RESET_ALL)
        return False


def wait_for_confirmation(tx_hash, timeout=300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                if receipt['status'] == 1:
                    print(Fore.GREEN + f"Transaction Successful | Tx Hash: {web3.to_hex(tx_hash)} | Network: Taiko" + Style.RESET_ALL)  # Green
                    print(f"Transaction execution time: {int(time.time() - start_time)} seconds")
                    return True
                else:
                    print(Fore.RED + f"Transaction Failed | Tx Hash: {web3.to_hex(tx_hash)}" + Style.RESET_ALL)  # Red
                    return False
        except Exception:
            pass
        time.sleep(30)  # Wait before checking again
    print(Fore.RED + f"Timeout waiting for confirmation for Tx Hash: {web3.to_hex(tx_hash)}" + Style.RESET_ALL)  # Red
    return False

def wrap_eth_to_weth():
    amount_in_wei = get_random_amount()  # Get a random amount for wrapping
    if not has_sufficient_balance(amount_in_wei, is_wrap=True):
        print(Fore.YELLOW + "Waiting for sufficient ETH balance..." + Style.RESET_ALL)  # Yellow
        return False

    print(Fore.YELLOW + f"Preparing to wrap: {web3.from_wei(amount_in_wei, 'ether')} ETH to WETH" + Style.RESET_ALL)  # Blue

    nonce = get_next_nonce()
    gas_estimate = weth_contract.functions.deposit(amount_in_wei).estimate_gas({'from': my_address, 'value': amount_in_wei})
    transaction = {
        'to': weth_contract_address,
        'chainId': 167000,
        'gas': gas_estimate,
        'maxFeePerGas': max_fee_per_gas_wrap,
        'maxPriorityFeePerGas': max_priority_fee_per_gas_wrap,
        'nonce': nonce,
        'value': amount_in_wei,
        'data': '0xd0e30db0'  # Deposit function signature
    }

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(Fore.BLUE + f"Transaction sent: Wrapping ETH to WETH | Amount: {web3.from_wei(amount_in_wei, 'ether')} WETH | Tx Hash: {web3.to_hex(tx_hash)} | Network: Taiko" + Style.RESET_ALL)  # Blue
        if wait_for_confirmation(tx_hash):
            return True
    except Exception as e:
        print(Fore.RED + f"Transaction error: {e}" + Style.RESET_ALL)  # Red
    return False

def unwrap_weth_to_eth():
    amount_in_wei = get_random_amount()  # Get a random amount for unwrapping
    if not has_sufficient_balance(amount_in_wei, is_wrap=False):
        print(Fore.YELLOW + "Waiting for sufficient WETH balance..." + Style.RESET_ALL)  # Yellow
        return False

    print(Fore.YELLOW + f"Preparing to unwrap: {web3.from_wei(amount_in_wei, 'ether')} WETH to ETH" + Style.RESET_ALL)  # Blue

    nonce = get_next_nonce()
    gas_estimate = weth_contract.functions.withdraw(amount_in_wei).estimate_gas({'from': my_address})
    transaction = {
        'to': weth_contract_address,
        'chainId': 167000,
        'gas': gas_estimate,
        'maxFeePerGas': max_fee_per_gas_unwrap,
        'maxPriorityFeePerGas': max_priority_fee_per_gas_unwrap,
        'nonce': nonce,
        'data': '0x2e1a7d4d' + amount_in_wei.to_bytes(32, 'big').hex()  # Withdraw function signature
    }

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(Fore.BLUE + f"Transaction sent: Unwrapping WETH to ETH | Amount: {web3.from_wei(amount_in_wei, 'ether')} ETH | Tx Hash: {web3.to_hex(tx_hash)} | Network: Taiko" + Style.RESET_ALL)  # Blue
        if wait_for_confirmation(tx_hash):
            return True
    except Exception as e:
        print(Fore.RED + f"Transaction error: {e}" + Style.RESET_ALL)  # Red
    return False

wrap_counter = 0
unwrap_counter = 0
total_tx = 0

try:
    while total_tx < 74:
        eth_balance = check_weth_balance()

        # Wrap ETH to WETH
        if wrap_counter < 37 and total_tx < 74:
            if wrap_eth_to_weth():
                wrap_counter += 1
                total_tx += 1
                print(Fore.BLUE + f"Total Transactions: {total_tx} (Wrapping: {wrap_counter})" + Style.RESET_ALL)  # Blue

        # Optional: Sleep for a random duration between transactions
        sleep_time = random.uniform(15, 25)
        print(Fore.BLUE + f"Sleeping for {sleep_time:.2f} seconds before the next transaction." + Style.RESET_ALL)  # Blue
        time.sleep(sleep_time)

        weth_balance = check_eth_balance()

        # Unwrap WETH to ETH
        if unwrap_counter < 37 and total_tx < 74:
            if unwrap_weth_to_eth():
                unwrap_counter += 1
                total_tx += 1
                print(Fore.BLUE + f"Total Transactions: {total_tx} (Unwrapping: {unwrap_counter})" + Style.RESET_ALL)  # Blue

        # Optional: Sleep for a random duration between transactions
        sleep_time = random.uniform(15, 25)
        print(Fore.BLUE + f"Sleeping for {sleep_time:.2f} seconds before the next transaction." + Style.RESET_ALL)  # Blue
        time.sleep(sleep_time)

except KeyboardInterrupt:
    print(Fore.RED + "\nInterrupted by user." + Style.RESET_ALL)
finally:
        print(Fore.MAGENTA + f"Total Transactions: {total_tx} (Wrapping: {wrap_counter}, Unwrapping: {unwrap_counter})" + Style.RESET_ALL)
        print(Fore.YELLOW + "Thank you tod!" + Style.RESET_ALL)

