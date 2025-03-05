from web3 import Web3

class TeaAssamBatchTransfer:
    def __init__(self, private_key, sender_address, recipient_addresses, amount_per_address, contract_address, maxPriorityFeePerGas="1800", maxFeePerGas="2000"):
        self.rpc_url = "https://assam-rpc.tea.xyz"
        self.chain_id = 93384

        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.web3.is_connected():
            raise Exception("Gagal terhubung ke blockchain.")

        self.private_key = private_key
        self.sender_address = sender_address
        self.recipient_addresses = recipient_addresses
        self.amount_per_address = self.web3.to_wei(amount_per_address, "ether")
        self.TOKEN_BATH_ADDRESS = contract_address

        self.maxPriorityFeePerGas = self.web3.to_wei(maxPriorityFeePerGas, "gwei")
        self.maxFeePerGas = self.web3.to_wei(maxFeePerGas, "gwei")

        self.batch_transfer_contract_address = "0xAB60Db6Bc74B6A5869A874F32d57Dc1CB6234766"

        self.batch_transfer_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "token", "type": "address"},
                    {"internalType": "address[]", "name": "recipients", "type": "address[]"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"}
                ],
                "name": "batchTransfer",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

        self.batch_transfer_contract = self.web3.eth.contract(
            address=self.batch_transfer_contract_address, 
            abi=self.batch_transfer_abi
        )

        self.erc20_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "spender", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]

        self.token_contract = self.web3.eth.contract(address=self.TOKEN_BATH_ADDRESS, abi=self.erc20_abi)

    def check_balance(self):
        """Memeriksa saldo token pengirim dan mengembalikan dalam wei dan ether."""
        sender_balance_wei = self.token_contract.functions.balanceOf(self.sender_address).call()
        sender_balance_eth = self.web3.from_wei(sender_balance_wei, "ether")
        return sender_balance_wei, sender_balance_eth

    def approve_token(self):
        """Melakukan approve token dan mengembalikan status dan hash transaksi."""
        total_needed = self.amount_per_address * len(self.recipient_addresses)
        nonce = self.web3.eth.get_transaction_count(self.sender_address)
        tx = self.token_contract.functions.approve(
            self.batch_transfer_contract_address, total_needed
        ).build_transaction({
            "from": self.sender_address,
            "nonce": nonce,
            "gas": 100000,
            "maxPriorityFeePerGas": self.maxPriorityFeePerGas,
            "maxFeePerGas": self.maxFeePerGas,
            "chainId": self.chain_id
        })
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        status = "sukses" if receipt.status == 1 else "gagal"
        return status, self.web3.to_hex(tx_hash)

    def batch_transfer(self):
        """Melakukan batch transfer dan mengembalikan status dan hash transaksi."""
        nonce = self.web3.eth.get_transaction_count(self.sender_address)
        tx = self.batch_transfer_contract.functions.batchTransfer(
            self.TOKEN_BATH_ADDRESS, self.recipient_addresses, self.amount_per_address
        ).build_transaction({
            "from": self.sender_address,
            "nonce": nonce,
            "gas": 500000,
            "maxPriorityFeePerGas": self.maxPriorityFeePerGas,
            "maxFeePerGas": self.maxFeePerGas,
            "chainId": self.chain_id
        })
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        status = "sukses" if receipt.status == 1 else "gagal"
        return status, self.web3.to_hex(tx_hash)

    def run(self):
        """Menjalankan seluruh proses dan mengembalikan list of dictionaries."""
        result_list = []
        try:
            sender_balance_wei, sender_balance_eth = self.check_balance()
            total_needed_wei = self.amount_per_address * len(self.recipient_addresses)
            total_needed_eth = self.web3.from_wei(total_needed_wei, "ether")

            result_list.append({
                "step": "check_balance",
                "balance_wei": sender_balance_wei,
                "balance_eth": sender_balance_eth,
                "total_needed_wei": total_needed_wei,
                "total_needed_eth": total_needed_eth
            })

            if sender_balance_wei < total_needed_wei:
                result_list.append({
                    "step": "error",
                    "status": "gagal",
                    "error": f"Saldo tidak cukup! Anda butuh {total_needed_eth} BATH."
                })
                return result_list

            approve_status, approve_tx_hash = self.approve_token()
            result_list.append({
                "step": "approve",
                "status": approve_status,
                "tx_hash": approve_tx_hash
            })

            if approve_status != "sukses":
                result_list.append({
                    "step": "error",
                    "status": "gagal",
                    "error": "Approve gagal."
                })
                return result_list

            batch_status, batch_tx_hash = self.batch_transfer()
            result_list.append({
                "step": "batch_transfer",
                "status": batch_status,
                "tx_hash": batch_tx_hash
            })

            result_list.append({
                "step": "final",
                "status": batch_status,
                "message": "Batch Transfer Sukses!" if batch_status == "sukses" else "Batch Transfer Gagal!"
            })

        except Exception as e:
            result_list.append({
                "step": "exception",
                "status": "error",
                "error": str(e)
            })

        return result_list


