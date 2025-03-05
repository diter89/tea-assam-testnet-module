from web3 import Web3
import locale

class TeaToContract:
    def __init__(self, private_key: str, user_address: str, amount: int, contract_address: str, gasprice: int):
        self.rpc_url = "https://assam-rpc.tea.xyz"
        self.chain_id = 93384
        self.private_key = private_key
        self.user_address = user_address
        self.amount = amount
        self.contract_address = contract_address
        self.gasprice = gasprice
        
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.web3.is_connected():
            raise Exception("Gagal terhubung ke blockchain.")
        
        self.router_address = "0xACBc89FF219232C058428D166860df4eA0114999"
        self.router_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "_factory", "type": "address"},
                    {"internalType": "address", "name": "_WETH", "type": "address"}
                ],
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
            {
                "inputs": [],
                "name": "WETH",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactTokensForTokens",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        self.router_contract = self.web3.eth.contract(address=self.router_address, abi=self.router_abi)
        
        self.amount_in = self.web3.to_wei(self.amount, 'ether')
        self.amount_out_min = 0
        self.deadline = self.web3.eth.get_block('latest')['timestamp'] + 600  # Deadline 10 menit

    def get_wtea_address(self):
        return self.router_contract.functions.WETH().call()

    def check_tea_balance(self):
        tea_balance = self.web3.eth.get_balance(self.user_address)
        return self.web3.from_wei(tea_balance, 'ether')

    def wrap_tea(self, amount):
        wtea_address = self.get_wtea_address()
        wtea_abi = [
            {
                "constant": False,
                "inputs": [],
                "name": "deposit",
                "outputs": [],
                "payable": True,
                "stateMutability": "payable",
                "type": "function"
            }
        ]
        wtea_contract = self.web3.eth.contract(address=wtea_address, abi=wtea_abi)
        nonce = self.web3.eth.get_transaction_count(self.user_address)
        wrap_tx = wtea_contract.functions.deposit().build_transaction({
            'from': self.user_address,
            'nonce': nonce,
            'value': amount,
            'gas': 100000,
            'gasPrice': self.web3.to_wei(str(self.gasprice), 'gwei'),
            'chainId': self.chain_id
        })
        signed_wrap_tx = self.web3.eth.account.sign_transaction(wrap_tx, self.private_key)
        wrap_tx_hash = self.web3.eth.send_raw_transaction(signed_wrap_tx.raw_transaction)
        return self.web3.to_hex(wrap_tx_hash)

    def check_wtea_balance(self):
        wtea_address = self.get_wtea_address()
        wtea_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]
        wtea_contract = self.web3.eth.contract(address=wtea_address, abi=wtea_abi)
        wtea_balance = wtea_contract.functions.balanceOf(self.user_address).call()
        return self.web3.from_wei(wtea_balance, 'ether')

    def approve_token(self, token_address, spender_address, amount):
        token_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "spender", "type": "address"},
                    {"name": "value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        token_contract = self.web3.eth.contract(address=token_address, abi=token_abi)
        nonce = self.web3.eth.get_transaction_count(self.user_address)
        approve_tx = token_contract.functions.approve(spender_address, amount).build_transaction({
            'from': self.user_address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': self.web3.to_wei(str(self.gasprice), 'gwei'),
            'chainId': self.chain_id
        })
        signed_approve_tx = self.web3.eth.account.sign_transaction(approve_tx, self.private_key)
        approve_tx_hash = self.web3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
        return self.web3.to_hex(approve_tx_hash)

    def swap_tokens(self, amount_in, amount_out_min, path, to, deadline):
        nonce = self.web3.eth.get_transaction_count(self.user_address)
        tx = self.router_contract.functions.swapExactTokensForTokens(
            amount_in, amount_out_min, path, to, deadline
        ).build_transaction({
            'from': self.user_address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': self.web3.to_wei(str(self.gasprice), 'gwei'),
            'chainId': self.chain_id
        })
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return self.web3.to_hex(tx_hash)

    def eksekusi(self):
        result = {}
        system_locale = locale.getlocale()[0]
        is_indonesian = "id" in system_locale.lower() if system_locale else False

        result["tea_balance_tokens"] = self.check_tea_balance()

        amount_to_wrap = self.web3.to_wei(1, 'ether')
        result["wrap_tx_hash"] = self.wrap_tea(amount_to_wrap)
        self.web3.eth.wait_for_transaction_receipt(result["wrap_tx_hash"])

        result["wtea_balance_tokens"] = self.check_wtea_balance()

        wtea_address = self.get_wtea_address()
        result["approval_tx_hash"] = self.approve_token(wtea_address, self.router_address, self.amount_in)
        self.web3.eth.wait_for_transaction_receipt(result["approval_tx_hash"])

        path = [wtea_address, self.contract_address]
        result["swap_tx_hash"] = self.swap_tokens(self.amount_in, self.amount_out_min, path, self.user_address, self.deadline)
        swap_receipt = self.web3.eth.wait_for_transaction_receipt(result["swap_tx_hash"])

        result["swap_status"] = "sukses" if swap_receipt.status == 1 else "gagal"
        result["message"] = (
            "Transaksi swap berhasil" if is_indonesian else "Swap transaction successful"
        ) if swap_receipt.status == 1 else (
            "Transaksi swap gagal" if is_indonesian else "Swap transaction failed"
        )
        
        return result

