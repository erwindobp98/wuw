from web3 import Web3
import time
import os
import sys
import random
from colorama import Fore  # Import untuk warna

def animated_print(text, color=Fore.WHITE, delay=0.02):
    """Mencetak teks dengan animasi dan opsi warna."""
    # Terapkan warna jika diberikan
    sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(Fore.RESET)  # Reset warna setelah selesai
    print()  # Untuk baris baru di akhir animasi

# Daftar RPC Taiko
taiko_rpc_list = [
    "https://rpc.ankr.com/taiko",
    "https://rpc.taiko.xyz",
    "wss://taiko-rpc.publicnode.com",
    "https://rpc.mainnet.taiko.xyz",
    "https://taiko.drpc.org",
    "wss://taiko.drpc.org",
    "https://rpc.taiko.tools" 
]

def get_connected_web3():
    """Coba koneksi ke daftar RPC hingga berhasil."""
    for rpc_url in taiko_rpc_list:
        web3_instance = Web3(Web3.HTTPProvider(rpc_url))
        if web3_instance.is_connected():
            animated_print(f"Terhubung ke RPC: {rpc_url}", color=Fore.GREEN)
            return web3_instance, rpc_url
        else:
            animated_print(f"Gagal terhubung ke RPC: {rpc_url}", color=Fore.RED)
    animated_print("Tidak ada RPC yang bisa terhubung.", color=Fore.RED)
    exit()

# Coba hubungkan ke salah satu RPC
web3, active_rpc_url = get_connected_web3()

# Cek ulang koneksi sebelum transaksi
def check_connection():
    """Periksa koneksi ke jaringan dan pilih ulang RPC jika koneksi terputus."""
    global web3, active_rpc_url
    if not web3.is_connected():
        animated_print(f"Koneksi terputus dengan RPC: {active_rpc_url}. Mencoba RPC lain...", color=Fore.YELLOW)
        previous_rpc = active_rpc_url  # Simpan RPC sebelumnya untuk log
        web3, active_rpc_url = get_connected_web3()
        if active_rpc_url != previous_rpc:
            animated_print(f"Berpindah ke RPC baru: {active_rpc_url}", color=Fore.CYAN)
    else:
        animated_print(f"Koneksi tetap stabil dengan RPC: {active_rpc_url}", color=Fore.GREEN)

# Ganti dengan private key dan alamat dompet Anda
private_key = "isi private key"  # Ganti dengan private key
my_address = Web3.to_checksum_address("isi wallet address")  # Alamat dompet Anda

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

# Tentukan harga gas di awal skrip
gas_price_wrap_gwei = 0.18  # Sesuaikan sesuai kebutuhan
gas_price_unwrap_gwei = 0.165  # Sesuaikan sesuai kebutuhan

# Konversi ke Wei untuk digunakan dalam transaksi
max_priority_fee_per_gas_wrap = web3.to_wei(gas_price_wrap_gwei, 'gwei')
max_fee_per_gas_wrap = web3.to_wei(gas_price_wrap_gwei, 'gwei')

max_priority_fee_per_gas_unwrap = web3.to_wei(gas_price_unwrap_gwei, 'gwei')
max_fee_per_gas_unwrap = web3.to_wei(gas_price_unwrap_gwei, 'gwei')

# Tambahkan panggilan check_connection sebelum semua operasi terkait web3

def get_random_amount():
    """Menghasilkan jumlah acak antara 0.01 dan 0.011 ETH."""
    return web3.to_wei(random.uniform(0.173654, 0.173674), 'ether')


def check_eth_balance():
    balance = web3.eth.get_balance(my_address)
    eth_balance = web3.from_wei(balance, 'ether')
    animated_print(f"Saldo ETH: {eth_balance:.6f} ETH", color=Fore.MAGENTA)
    return balance

def check_weth_balance():
    balance = weth_contract.functions.balanceOf(my_address).call()
    weth_balance = web3.from_wei(balance, 'ether')
    animated_print(f"Saldo WETH: {weth_balance:.6f} WETH", color=Fore.MAGENTA)
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
        # Periksa saldo ETH atau WETH berdasarkan jenis transaksi
        if is_wrap:
            eth_balance = check_eth_balance()
            if eth_balance >= total_cost:
                animated_print(f"Saldo ETH cukup. Dibutuhkan: {web3.from_wei(total_cost, 'ether')} ETH", color=Fore.GREEN)
                return True
            else:
                animated_print(f"Saldo tidak cukup. Saldo: {web3.from_wei(eth_balance, 'ether')} ETH, Dibutuhkan: {web3.from_wei(total_cost, 'ether')} ETH", color=Fore.RED)
        else:
            weth_balance = check_weth_balance()
            if weth_balance >= amount_in_wei:
                animated_print(f"Saldo WETH cukup. Dibutuhkan: {web3.from_wei(amount_in_wei, 'ether')} WETH", color=Fore.GREEN)
                return True
            else:
                animated_print(f"Saldo tidak cukup. Saldo: {web3.from_wei(weth_balance, 'ether')} WETH, Dibutuhkan: {web3.from_wei(amount_in_wei, 'ether')} WETH", color=Fore.RED)
        return False
    except Exception as e:
        animated_print(f"Kesalahan dalam estimasi gas: {e}", color=Fore.RED)
        return False


def wait_for_confirmation(tx_hash, timeout=300):
    start_time = time.time()  # Waktu mulai dalam detik
    global web3, active_rpc_url

    while time.time() - start_time < timeout:  # Menggunakan detik untuk perbandingan
        try:
            # Periksa koneksi secara berkala, ganti RPC jika perlu
            if not web3.is_connected():
                animated_print(f"Koneksi terputus dengan RPC: {active_rpc_url}. Mencoba RPC lain...", color=Fore.YELLOW)
                previous_rpc = active_rpc_url
                web3, active_rpc_url = get_connected_web3()
                animated_print(f"Berpindah ke RPC baru: {active_rpc_url}", color=Fore.CYAN)

            # Coba ambil receipt transaksi
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                if receipt['status'] == 1:
                    animated_print(f"Transaksi Sukses | Tx Hash: {web3.to_hex(tx_hash)} | Jaringan: Taiko", color=Fore.GREEN)
                    animated_print(f"Waktu eksekusi transaksi: {int(time.time() - start_time)} detik", color=Fore.GREEN)  # Menampilkan waktu eksekusi dalam detik
                    return True
                else:
                    animated_print(f"Transaksi Gagal | Tx Hash: {web3.to_hex(tx_hash)}", color=Fore.RED)
                    return False

        except Exception:
            pass

        # Hitung waktu tersisa dan tampilkan countdown dalam detik
        remaining_time = timeout - (time.time() - start_time)  # Waktu tersisa dalam detik
        if remaining_time > 0:
            sys.stdout.write(f"\r{Fore.YELLOW}Menunggu konfirmasi... {int(remaining_time)} detik tersisa...") # Dengan warna
            sys.stdout.flush()
        else:
            break

        time.sleep(1)  # Tunggu 1 detik sebelum memeriksa lagi

    animated_print(f"\nWaktu habis menunggu konfirmasi untuk Tx Hash: {web3.to_hex(tx_hash)}", color=Fore.RED)
    return False

def wrap_eth_to_weth(): 
    amount_in_wei = get_random_amount()  # Mengambil jumlah acak untuk membungkus ETH
    if not has_sufficient_balance(amount_in_wei, is_wrap=True):
        animated_print("Menunggu saldo ETH yang cukup...", color=Fore.YELLOW, delay=0.02)  # Dengan warna dan delay
        return False

    animated_print(f"Mempersiapkan untuk membungkus: {web3.from_wei(amount_in_wei, 'ether')} ETH menjadi WETH", color=Fore.CYAN, delay=0.02)

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
        'data': '0xd0e30db0'  # Signature fungsi deposit
    }

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        animated_print(f"Transaksi terkirim: Membungkus ETH menjadi WETH | Jumlah: {web3.from_wei(amount_in_wei, 'ether')} WETH | Tx Hash: {web3.to_hex(tx_hash)} | Jaringan: Taiko", color=Fore.BLUE, delay=0.01)  # Dengan warna dan delay
        if wait_for_confirmation(tx_hash):
            check_connection()  # Pastikan koneksi tetap stabil setelah transaksi
            return True
    except Exception as e:
        animated_print(f"Kesalahan transaksi: {e}", color=Fore.RED, delay=0.02)  # Dengan warna dan delay
    return False

def unwrap_weth_to_eth():
    amount_in_wei = get_random_amount()  # Mengambil jumlah acak untuk membuka WETH
    if not has_sufficient_balance(amount_in_wei, is_wrap=False):
        animated_print("Menunggu saldo WETH yang cukup...", color=Fore.YELLOW, delay=0.02)  # Dengan warna dan delay
        return False

    animated_print(f"Mempersiapkan untuk membuka: {web3.from_wei(amount_in_wei, 'ether')} WETH menjadi ETH", color=Fore.CYAN, delay=0.02)

    nonce = get_next_nonce()
    try:
        gas_estimate = weth_contract.functions.withdraw(amount_in_wei).estimate_gas({'from': my_address})
    except Exception as e:
        animated_print(f"Kesalahan dalam estimasi gas: {e}", color=Fore.RED, delay=0.01)  # Dengan warna dan delay
        return False

    transaction = {
        'to': weth_contract_address,
        'chainId': 167000,
        'gas': gas_estimate,
        'maxFeePerGas': max_fee_per_gas_unwrap,
        'maxPriorityFeePerGas': max_priority_fee_per_gas_unwrap,
        'nonce': nonce,
        'data': '0x2e1a7d4d' + amount_in_wei.to_bytes(32, 'big').hex()  # Signature fungsi withdraw
    }

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        animated_print(f"Transaksi terkirim: Membuka WETH menjadi ETH | Jumlah: {web3.from_wei(amount_in_wei, 'ether')} ETH | Tx Hash: {web3.to_hex(tx_hash)} | Jaringan: Taiko", color=Fore.BLUE, delay=0.01)  # Dengan warna dan delay
        
        # Menunggu konfirmasi transaksi dengan pengecekan koneksi
        if wait_for_confirmation(tx_hash):
            check_connection()  # Pastikan koneksi tetap stabil setelah transaksi
            return True
    except Exception as e:
        animated_print(f"Kesalahan transaksi: {e}", color=Fore.RED, delay=0.02)  # Dengan warna dan delay
    return False

def print_sleep_time(sleep_time):
    """Cetak waktu tidur dan hitung mundur dalam milidetik."""
    animated_print(f"Tidur selama {sleep_time:.2f} detik...", color=Fore.YELLOW, delay=0.02)  # Dengan warna dan delay
    total_seconds = int(sleep_time)
    total_milliseconds = int((sleep_time - total_seconds) * 1000)  # Konversi sisa waktu ke milidetik

    for remaining in range(total_seconds, 0, -1):
        for millis in range(1000, 0, -100):  # Hitung mundur dalam milidetik
            sys.stdout.write(f"\r{Fore.YELLOW}{remaining} detik dan {millis//100} milidetik tersisa...")  # Dengan warna
            sys.stdout.flush()
            time.sleep(0.1)  # Tunggu 100 milidetik untuk update tampilan
        remaining -= 1
    # Tampilkan milidetik terakhir jika ada
    if total_milliseconds > 0:
        sys.stdout.write(f"\r{Fore.YELLOW}0 detik dan {total_milliseconds} milidetik tersisa...")  # Dengan warna
        sys.stdout.flush()
        time.sleep(total_milliseconds / 1000)  # Tunggu sisa milidetik terakhir
    print()  # Mencetak newline setelah countdown

wrap_counter = 0
unwrap_counter = 0
total_tx = 0

try:
    while total_tx < 148:
        eth_balance = check_weth_balance()

        # Membungkus ETH menjadi WETH
        if wrap_counter < 74 and total_tx < 148:
            if wrap_eth_to_weth():
                wrap_counter += 1
                total_tx += 1
                animated_print(f"Total Transaksi: {total_tx} (Membungkus: {wrap_counter})", color=Fore.CYAN, delay=0.02)  # Dengan warna dan delay

        # Tidur untuk durasi acak antara transaksi
        sleep_time = random.uniform(12, 15)
        print_sleep_time(sleep_time)  # Memanggil fungsi countdown

        weth_balance = check_eth_balance()

        # Membuka WETH menjadi ETH
        if unwrap_counter < 74 and total_tx < 148:
            if unwrap_weth_to_eth():
                unwrap_counter += 1
                total_tx += 1
                animated_print(f"Total Transaksi: {total_tx} (Membuka: {unwrap_counter})", color=Fore.CYAN, delay=0.02)  # Dengan warna dan delay

        # Tidur untuk durasi acak antara transaksi
        sleep_time = random.uniform(12, 15)
        print_sleep_time(sleep_time)  # Memanggil fungsi countdown

except KeyboardInterrupt:
    animated_print("\nDihentikan oleh pengguna.", color=Fore.RED, delay=0.01)  # Dengan warna dan delay
finally:
    animated_print(f"Total Transaksi: {total_tx} (Membungkus: {wrap_counter}, Membuka: {unwrap_counter})", color=Fore.MAGENTA, delay=0.02)  # Dengan warna dan delay
    animated_print("Terima kasih tod!", color=Fore.YELLOW, delay=0.02)  # Dengan warna dan delay

