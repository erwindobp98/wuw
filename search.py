from web3 import Web3

# Koneksi ke node Taiko Mainnet (ganti URL dengan endpoint node Anda)
WEB3_PROVIDER_URI = "https://taiko-rpc.publicnode.com"
web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))

# Periksa koneksi
if not web3.is_connected():
    raise Exception("Tidak dapat terhubung ke node Taiko Mainnet")

print("Terhubung ke node Taiko Mainnet.")

# Smart contract yang ingin diperiksa
CONTRACT_ADDRESS = "0xA51894664A773981C6C112C43ce576f315d5b1B6" # WETH TAIKO

# Awalan dan akhiran yang dicari
ADDRESS_PREFIX = "0xc131" # Tambahkan address awal
ADDRESS_SUFFIX = "4B42" # Tambahkan address terakhir

# Mulai blok dan akhir blok untuk pencarian
START_BLOCK = 705400  # Ganti dengan blok awal yang relevan untuk jaringan Taiko
END_BLOCK = web3.eth.block_number

print(f"Mencari transaksi dari blok {START_BLOCK} hingga {END_BLOCK} di jaringan Taiko Mainnet...")

# Fungsi untuk memeriksa apakah sebuah alamat sesuai kriteria
def is_matching_address(address):
    return address.startswith(ADDRESS_PREFIX) and address.endswith(ADDRESS_SUFFIX)

# Loop melalui blok untuk mencari transaksi
for block_number in range(START_BLOCK, END_BLOCK + 1):
    print(f"Memproses blok {block_number}...")
    block = web3.eth.get_block(block_number, full_transactions=True)
    for tx in block.transactions:
        # Periksa apakah transaksi menuju kontrak target
        if tx.to and tx.to.lower() == CONTRACT_ADDRESS.lower():
            # Periksa apakah pengirim memiliki awalan dan akhiran yang sesuai
            if is_matching_address(tx['from']):
                address = tx['from']
                print("Alamat yang cocok telah ditemukan:")
                print(f"https://debank.com/profile/{address}")
                print(f"https://trailblazers.taiko.xyz/profile/{address}")
                exit()  # Hentikan program setelah menemukan address
