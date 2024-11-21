import requests
import datetime
from colorama import Fore, Style, init
import time
import sys

# Inisialisasi colorama
init(autoreset=True)

def animated_print(text, color=Fore.WHITE, delay=0.05):
    for char in text:
        sys.stdout.write(color + char + Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(delay)
    print()  # Untuk baris baru di akhir animasi


def calculate_gas_fee(gas_used, gas_price_gwei):
    gas_price_wei = gas_price_gwei * 1e9
    gas_fee_wei = gas_used * gas_price_wei
    return gas_fee_wei / 1e18

def get_eth_price():
    try:
        url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd'
        response = requests.get(url)
        data = response.json()
        
        if 'ethereum' not in data or 'usd' not in data['ethereum']:
            print(Fore.RED + 'Gagal mendapatkan harga ETH.')
            return None
        
        return data['ethereum']['usd']
    except requests.RequestException as e:
        print(Fore.RED + f'Error fetching ETH price: {e}')
        return None

def get_transaction_data_from_taiko(address):
    try:
        now = int(time.time())
        start_of_today = int(datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        start_of_period = int(datetime.datetime(2024, 9, 16, tzinfo=datetime.timezone.utc).timestamp())
        
        url = f'https://api.taikoscan.io/api?module=account&action=txlist&address={address}'
        response = requests.get(url)
        
        if response.status_code != 200:
            print(Fore.RED + f"Failed to fetch transaction data: {response.status_code}")
            return
        
        data = response.json()
        
        if 'result' not in data:
            print(Fore.YELLOW + 'Tidak ada data transaksi ditemukan.')
            return

        total_gas_fee_today = 0
        tx_count_today = 0
        total_gas_fee_from_sep16 = 0
        tx_count_from_sep16 = 0
        
        for tx in data['result']:
            tx_timestamp = int(tx['timeStamp'])
            gas_used = int(tx['gasUsed'])
            gas_price_gwei = int(tx['gasPrice'])

            gas_fee = calculate_gas_fee(gas_used, gas_price_gwei)
            
            if tx_timestamp >= start_of_today:
                total_gas_fee_today += gas_fee
                tx_count_today += 1

            if tx_timestamp >= start_of_period:
                total_gas_fee_from_sep16 += gas_fee
                tx_count_from_sep16 += 1
        
        eth_to_usd_rate = get_eth_price()
        
        if not eth_to_usd_rate:
            print(Fore.RED + 'Gagal mendapatkan harga ETH, perhitungan tidak dapat dilanjutkan.')
            return
        
        adjusted_gas_fee_eth_today = total_gas_fee_today / 1e9
        total_gas_fee_usd_today = adjusted_gas_fee_eth_today * eth_to_usd_rate

        adjusted_gas_fee_eth_from_sep16 = total_gas_fee_from_sep16 / 1e9
        total_gas_fee_usd_from_sep16 = adjusted_gas_fee_eth_from_sep16 * eth_to_usd_rate

        return {
            'total_gas_fee_today': total_gas_fee_today,
            'tx_count_today': tx_count_today,
            'total_gas_fee_from_sep16': total_gas_fee_from_sep16,
            'tx_count_from_sep16': tx_count_from_sep16,
            'adjusted_gas_fee_eth_today': adjusted_gas_fee_eth_today,
            'total_gas_fee_usd_today': total_gas_fee_usd_today,
            'adjusted_gas_fee_eth_from_sep16': adjusted_gas_fee_eth_from_sep16,
            'total_gas_fee_usd_from_sep16': total_gas_fee_usd_from_sep16
        }

    except requests.RequestException as e:
        print(Fore.RED + f'Error fetching transaction data: {e}')
        return None

def get_final_data(address):
    try:
        final_url = f'https://trailblazer.mainnet.taiko.xyz/user/final?address={address}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; TaikoRankChecker/1.0)'
        }
        response = requests.get(final_url, headers=headers)

        if response.status_code == 403:
            print(Fore.RED + "Gagal mengambil data final: Akses ditolak (403). Pastikan Anda memiliki izin akses.")
            return None

        if response.status_code != 200:
            print(Fore.RED + f"Gagal mengambil data final: {response.status_code}")
            return None

        data = response.json()
        return {
            "score": data.get('score', 'N/A'),
            "multiplier": data.get('multiplier', 'N/A'),
            "total": data.get('total', 'N/A')
        }
    except requests.RequestException as e:
        print(Fore.RED + f'Error fetching final data: {e}')
        return None

def get_rank_data(address):
    try:
        rank_url = f'https://trailblazer.mainnet.taiko.xyz/s2/user/rank?address={address}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; TaikoRankChecker/1.0)'
        }
        response = requests.get(rank_url, headers=headers)
        if response.status_code != 200:
            print(Fore.RED + f"Failed to fetch rank data: {response.status_code}")
            return None

        return response.json()
    except requests.RequestException as e:
        print(Fore.RED + f'Error fetching rank data: {e}')
        return None

def display_taiko_data(address):
    transaction_data = get_transaction_data_from_taiko(address)
    final_data = get_final_data(address)
    rank_data = get_rank_data(address)

    if transaction_data:
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.02)
        animated_print("                  Taiko Transaction Data              ", color=Fore.GREEN, delay=0.02)
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.02)
        if 'adjusted_gas_fee_eth_today' in transaction_data:
            animated_print(f"Gas Fee ETH (Hari Ini)       : {transaction_data['adjusted_gas_fee_eth_today']:.10f} ETH", color=Fore.YELLOW, delay=0.02)
        
        if 'total_gas_fee_usd_today' in transaction_data:
            animated_print(f"Gas Fee USD (Hari Ini)       : ${transaction_data['total_gas_fee_usd_today']:.2f}", color=Fore.YELLOW, delay=0.02)
        
        if 'tx_count_today' in transaction_data:
            animated_print(f"Jumlah Tx Hari Ini           : {transaction_data['tx_count_today']} transaksi", color=Fore.GREEN, delay=0.02)
        
        if 'adjusted_gas_fee_eth_from_sep16' in transaction_data:
            animated_print(f"Total Gas Fee ETH TAIKO S2   : {transaction_data['adjusted_gas_fee_eth_from_sep16']:.10f} ETH", color=Fore.BLUE, delay=0.02)
        
        if 'total_gas_fee_usd_from_sep16' in transaction_data:
            animated_print(f"Total Gas Fee USD TAIKO S2   : ${transaction_data['total_gas_fee_usd_from_sep16']:.2f}", color=Fore.BLUE, delay=0.02)
        
        if 'tx_count_from_sep16' in transaction_data:
            animated_print(f"Jumlah Tx TAIKO S2           : {transaction_data['tx_count_from_sep16']} transaksi", color=Fore.GREEN, delay=0.02)

    if rank_data:
        rank = rank_data.get('rank', 'N/A')
        score = rank_data.get('score', 'N/A')
        multiplier = rank_data.get('multiplier', 'N/A')
        total_score = rank_data.get('totalScore', 'N/A')
        total = rank_data.get('total', 'N/A')
        blacklisted = rank_data.get('blacklisted', 'N/A')
        breakdown = rank_data.get('breakdown', 'N/A')

        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.02)
        animated_print("                  Taiko Rank Data              ", color=Fore.GREEN, delay=0.02)
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.02)
        animated_print(f"Rank                         : {rank}", color=Fore.YELLOW, delay=0.02)
        animated_print(f"Score                        : {score}", color=Fore.YELLOW, delay=0.02)
        animated_print(f"Multiplier                   : {multiplier}", color=Fore.CYAN, delay=0.02)
        animated_print(f"Total Score                  : {total_score}", color=Fore.CYAN, delay=0.02)
        animated_print(f"Total                        : {total}", color=Fore.BLUE, delay=0.02)
        animated_print(f"Blacklisted                  : {blacklisted}", color=Fore.RED, delay=0.02)
        animated_print(f"Breakdown                    : {breakdown}", color=Fore.MAGENTA, delay=0.02)

    if final_data:
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.02)
        animated_print("                  Informasi Data Final Taiko              ", color=Fore.GREEN, delay=0.02)
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.02)
        animated_print(f"Score                        : {final_data['score']}", color=Fore.YELLOW, delay=0.02)
        animated_print(f"Multiplier                   : {final_data['multiplier']}", color=Fore.CYAN, delay=0.02)
        animated_print(f"Total                        : {final_data['total']}", color=Fore.BLUE, delay=0.02)
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.02)


if __name__ == "__main__":
    try:
        animated_print("Selamat datang di Taiko Rank Checker S2!", color=Fore.CYAN, delay=0.02)
        address = input("Masukkan alamat wallet: ")
        display_taiko_data(address)
    except KeyboardInterrupt:
        animated_print("\nDihentikan oleh pengguna.", color=Fore.RED, delay=0.02)
    finally:
        animated_print("Terima kasih telah menggunakan layanan ini! 🥳", color=Fore.YELLOW, delay=0.02)

