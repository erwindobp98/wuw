from colorama import init, Fore, Style
from requests import Session
from web3 import Web3
import random
import time
import sys



# Inisialisasi colorama
init(autoreset=True)

# Connect to Taiko RPC
lisk_rpc_url = "https://rpc.api.lisk.com"
web3 = Web3(Web3.HTTPProvider(lisk_rpc_url))

# Check network connection
if not web3.is_connected():
    print(Fore.RED + "Tidak dapat terhubung ke jaringan Lisk." + Style.RESET_ALL)
    exit()

# Replace with your actual private key and address
private_key = "isi private key"  # Ganti dengan private key dummy
my_address = Web3.to_checksum_address("isi address wallet")  # Alamat dompet dummy

weth_contract_address = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")

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
gas_price_wrap_gwei = 0.0001  # Adjust as needed
gas_price_unwrap_gwei = 0.0001  # Adjust as needed

# Convert to Wei for use in transactions
max_priority_fee_per_gas_wrap = web3.to_wei(gas_price_wrap_gwei, 'gwei')
max_fee_per_gas_wrap = web3.to_wei(gas_price_wrap_gwei, 'gwei')

max_priority_fee_per_gas_unwrap = web3.to_wei(gas_price_unwrap_gwei, 'gwei')
max_fee_per_gas_unwrap = web3.to_wei(gas_price_unwrap_gwei, 'gwei')


def get_random_amount():
    """Generate a random amount between 0.01 and 0.011 ETH."""
    return web3.to_wei(random.uniform(0.000019, 0.00002), 'ether')

def check_eth_balance():
    balance = web3.eth.get_balance(my_address)
    eth_balance = web3.from_wei(balance, 'ether')
    print(Fore.MAGENTA + f"Saldo ETH: {eth_balance:.6f} ETH" + Style.RESET_ALL)  # Blue
    return balance

def check_weth_balance():
    balance = weth_contract.functions.balanceOf(my_address).call()
    weth_balance = web3.from_wei(balance, 'ether')
    print(Fore.MAGENTA + f"Saldo WETH: {weth_balance:.6f} WETH" + Style.RESET_ALL)  # Blue
    return balance

def get_next_nonce():
    return web3.eth.get_transaction_count(my_address)

from requests import Session

def fetch_task(address, axios_instance):
    try:
        task_payload = get_task(address)
        response = axios_instance.post(
            "https://portal-api.lisk.com/graphql",
            json=task_payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0"
            }
        )
        tasks = response.json().get("data", {}).get("userdrop", {}).get("user", {}).get("tasks", [])
        tasks = [task for group in tasks for task in group.get("tasks", [])]
        return [task for task in tasks if not task.get("progress", {}).get("isCompleted", False)]
    except Exception as error:
        print(Fore.RED + f"Error fetching tasks: {error}" + Style.RESET_ALL)
        return []

def get_task(address):
    return {
        "query": """
        query AirdropUser($filter: UserFilter!, $tasksFilter: QueryFilter) {
          userdrop {
            user(filter: $filter) {
              tasks(filter: $tasksFilter) {
                tasks {
                  id
                  description
                  progress {
                    isCompleted
                  }
                }
              }
            }
          }
        }
        """,
        "variables": {
            "filter": {
                "address": address
            }
        }
    }

def task_claim(address, task_id, task_description, index, axios_instance):
    try:
        print(Fore.YELLOW + f"[{index}] Claiming task: {task_description} ({task_id})" + Style.RESET_ALL)
        task_payload = claim_payload(address, task_id)
        response = axios_instance.post(
            "https://portal-api.lisk.com/graphql",
            json=task_payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0"
            }
        )
        update_status = response.json().get("data", {}).get("userdrop", {}).get("updateTaskStatus", {})
        if update_status.get("success", False):
            print(Fore.GREEN + f"[{index}] Task {task_description} ({task_id}) successfully claimed!" + Style.RESET_ALL)
        else:
            print(Fore.RED + f"[{index}] Failed to claim task {task_description} ({task_id})" + Style.RESET_ALL)
    except Exception as error:
        print(Fore.RED + f"[{index}] Error claiming task {task_description} ({task_id}): {error}" + Style.RESET_ALL)

def claim_payload(address, task_id):
    return {
        "query": """
        mutation UpdateAirdropTaskStatus($input: UpdateTaskStatusInputData!) {
          userdrop {
            updateTaskStatus(input: $input) {
              success
              progress {
                isCompleted
                completedAt
              }
            }
          }
        }
        """,
        "variables": {
            "input": {
                "address": address,
                "taskID": task_id
            }
        }
    }

# Bagian utama untuk mengambil dan mengklaim tugas
def claim_all_tasks(address):
    session = Session()
    print(Fore.BLUE + f"Fetching tasks for address: {address}" + Style.RESET_ALL)
    tasks = fetch_task(address, session)

    if not tasks:
        print(Fore.YELLOW + "No tasks available to claim." + Style.RESET_ALL)
        return

    for index, task in enumerate(tasks, start=1):
        task_id = task["id"]
        task_description = task["description"]
        task_claim(address, task_id, task_description, index, session)

# Panggil fungsi klaim tugas
try:
    claim_all_tasks(my_address)
except Exception as e:
    print(Fore.RED + f"Error during task claiming: {e}" + Style.RESET_ALL)
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
    start_time = time.time()  # Waktu mulai dalam detik

    while time.time() - start_time < timeout:  # Menggunakan detik untuk perbandingan
        try:
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                if receipt['status'] == 1:
                    print(Fore.GREEN + f"Transaction Successful | Tx Hash: {web3.to_hex(tx_hash)} | Network: LISK" + Style.RESET_ALL)  # Green
                    print(f"Transaction execution time: {int(time.time() - start_time)} seconds")  # Menampilkan waktu eksekusi dalam detik
                    return True
                else:
                    print(Fore.RED + f"Transaction Failed | Tx Hash: {web3.to_hex(tx_hash)}" + Style.RESET_ALL)  # Red
                    return False
        except Exception:
            pass
        
        # Hitung waktu tersisa dan tampilkan countdown dalam detik
        remaining_time = timeout - (time.time() - start_time)  # Waktu tersisa dalam detik
        if remaining_time > 0:
            sys.stdout.write(f"\r{Fore.YELLOW}Waiting for confirmation... {int(remaining_time)} seconds remaining...{Style.RESET_ALL}")  # Yellow
            sys.stdout.flush()
        else:
            break
            
        time.sleep(1)  # Tunggu 1 detik sebelum memeriksa lagi
    
    print(Fore.RED + f"\nTimeout waiting for confirmation for Tx Hash: {web3.to_hex(tx_hash)}" + Style.RESET_ALL)  # Red
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
        'chainId': 1135,
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
        print(Fore.BLUE + f"Transaction sent: Wrapping ETH to WETH | Amount: {web3.from_wei(amount_in_wei, 'ether')} WETH | Tx Hash: {web3.to_hex(tx_hash)} | Network: LISK" + Style.RESET_ALL)  # Blue
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
        'chainId': 1135,
        'gas': gas_estimate,
        'maxFeePerGas': max_fee_per_gas_unwrap,
        'maxPriorityFeePerGas': max_priority_fee_per_gas_unwrap,
        'nonce': nonce,
        'data': '0x2e1a7d4d' + amount_in_wei.to_bytes(32, 'big').hex()  # Withdraw function signature
    }

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(Fore.BLUE + f"Transaction sent: Unwrapping WETH to ETH | Amount: {web3.from_wei(amount_in_wei, 'ether')} ETH | Tx Hash: {web3.to_hex(tx_hash)} | Network: LISK" + Style.RESET_ALL)  # Blue
        if wait_for_confirmation(tx_hash):
            return True
    except Exception as e:
        print(Fore.RED + f"Transaction error: {e}" + Style.RESET_ALL)  # Red
    return False

def print_sleep_time(sleep_time):
    """Print the sleep time and count down in milliseconds."""
    print(Fore.BLUE + f"Sleeping for {sleep_time:.2f} seconds..." + Style.RESET_ALL)  # Blue
    total_seconds = int(sleep_time)
    total_milliseconds = int((sleep_time - total_seconds) * 1000)  # Konversi sisa waktu ke milidetik

    for remaining in range(total_seconds, 0, -1):
        for millis in range(1000, 0, -100):  # Hitung mundur dalam milidetik
            sys.stdout.write(f"\r{Fore.YELLOW}{remaining} seconds and {millis//100} milliseconds remaining...{Style.RESET_ALL}")  # Yellow
            sys.stdout.flush()
            time.sleep(0.1)  # Tunggu 100 milidetik untuk update tampilan
        remaining -= 1
    # Tampilkan milidetik terakhir jika ada
    if total_milliseconds > 0:
        sys.stdout.write(f"\r{Fore.YELLOW}0 seconds and {total_milliseconds} milliseconds remaining...{Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(total_milliseconds / 1000)  # Tunggu sisa milidetik terakhir
    print()  # Mencetak newline setelah countdown

wrap_counter = 0
unwrap_counter = 0
total_tx = 0

try:
    while total_tx < 72:
        eth_balance = check_weth_balance()

        # Wrap ETH to WETH
        if wrap_counter < 36 and total_tx < 72:
            if wrap_eth_to_weth():
                wrap_counter += 1
                total_tx += 1
                print(Fore.BLUE + f"Total Transactions: {total_tx} (Wrapping: {wrap_counter})" + Style.RESET_ALL)  # Blue

        # Sleep untuk durasi acak antara transaksi
        sleep_time = random.uniform(12, 15)
        print_sleep_time(sleep_time)  # Memanggil fungsi countdown

        weth_balance = check_eth_balance()

        # Unwrap WETH to ETH
        if unwrap_counter < 36 and total_tx < 72:
            if unwrap_weth_to_eth():
                unwrap_counter += 1
                total_tx += 1
                print(Fore.BLUE + f"Total Transactions: {total_tx} (Unwrapping: {unwrap_counter})" + Style.RESET_ALL)  # Blue

        # Sleep untuk durasi acak antara transaksi
        sleep_time = random.uniform(12, 15)
        print_sleep_time(sleep_time)  # Memanggil fungsi countdown

except KeyboardInterrupt:
    print(Fore.RED + "\nInterrupted by user." + Style.RESET_ALL)
finally:
    print(Fore.MAGENTA + f"Total Transactions: {total_tx} (Wrapping: {wrap_counter}, Unwrapping: {unwrap_counter})" + Style.RESET_ALL)
    print(Fore.YELLOW + "Thank you tod!" + Style.RESET_ALL)
