from web3 import Web3

class TransferToken:
    def __init__(self, private_key: str, sender_address: str, contract_address: str, gas_price: int, recipient_addresses: list):
        """
        Inisialisasi kelas TransferToken.
        
        Args:
            private_key (str): Kunci privat pengirim.
            sender_address (str): Alamat pengirim.
            contract_address (str): Alamat kontrak token.
            gas_price (int): Harga gas dalam Gwei.
            recipient_addresses (list): Daftar alamat penerima.
        """
        self._rpc_url = "https://assam-rpc.tea.xyz"  # RPC Tea Assam Testnet
        self._web3 = Web3(Web3.HTTPProvider(self._rpc_url))
        
        if not self._web3.is_connected():
            raise Exception("Gagal terhubung ke jaringan")
        
        self._private_key = private_key
        self._sender_address = sender_address
        self._contract_address = contract_address
        self._gas_price = gas_price
        self._recipient_addresses = recipient_addresses
        
        self._contract_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]
        
        self._contract = self._web3.eth.contract(address=self._contract_address, abi=self._contract_abi)
        
        from_account = self._web3.eth.account.from_key(self._private_key)
        if from_account.address.lower() != self._sender_address.lower():
            raise ValueError("Private key tidak sesuai dengan alamat pengirim")

    def transfer(self, amount: float) -> list:
        """
        Melakukan transfer token ke daftar penerima.
        
        Args:
            amount (float): Jumlah token yang akan ditransfer (dalam ether).
        
        Returns:
            list: List dictionary berisi hasil transfer untuk setiap penerima.
        """
        results = []
        
        for recipient_address in self._recipient_addresses:
            try:
                if not self._web3.is_address(recipient_address):
                    raise ValueError("Alamat penerima tidak valid")
                
                amount_wei = self._web3.to_wei(amount, "ether")
                
                nonce = self._web3.eth.get_transaction_count(self._sender_address)
                
                tx = self._contract.functions.transfer(recipient_address, amount_wei).build_transaction({
                    "chainId": 93384,  # Chain ID Tea Assam Testnet
                    "gas": 2000000,    # Batas gas
                    "gasPrice": self._web3.to_wei(str(self._gas_price), "gwei"),  # Harga gas dalam wei
                    "nonce": nonce,    # Nonce untuk urutan transaksi
                })
                
                signed_tx = self._web3.eth.account.sign_transaction(tx, self._private_key)
                
                tx_hash = self._web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                
                tx_receipt = self._web3.eth.wait_for_transaction_receipt(tx_hash)
                
                results.append({
                    "recipient_address": recipient_address,
                    "status": "sukses",
                    "tx_hash": self._web3.to_hex(tx_hash),
                    "block_number": tx_receipt['blockNumber'],
                    "gas_used": tx_receipt['gasUsed']
                })
            except Exception as e:
                results.append({
                    "recipient_address": recipient_address,
                    "status": "gagal",
                    "error": str(e)
                })
        
        return results


