from web3 import Web3

class ContractToTea:
    def __init__(self, private_key: str, user_address: str, gasprice: int, contract_address: str, amount_in: int):
        self.rpc_url = "https://assam-rpc.tea.xyz"
        self.chain_id = 93384

        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.web3.is_connected():
            raise Exception("Failed to connect to blockchain...")

        self.router_address = "0xACBc89FF219232C058428D166860df4eA0114999"
        self.private_key = private_key
        self.user_address = user_address
        self.contract_address = contract_address
        self.gasprice = gasprice
        self.amount_in = amount_in

        self.router_abi = [
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
                "name": "swapExactTokensForETH",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

        self.router_contract = self.web3.eth.contract(address=self.router_address, abi=self.router_abi)
        self.wtea_address = self.router_contract.functions.WETH().call()
        self.amount_in = self.web3.to_wei(self.amount_in, 'ether')
        self.amount_out_min = 0
        self.to = self.user_address
        self.deadline = self.web3.eth.get_block('latest')['timestamp'] + 600

    def check_token_balance(self, token_address):
        token_abi = [
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
        token_contract = self.web3.eth.contract(address=token_address, abi=token_abi)
        token_balance = token_contract.functions.balanceOf(self.user_address).call()
        return self.web3.from_wei(token_balance, 'ether')

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
            'gasPrice': self.web3.to_wei('{}'.format(self.gasprice), 'gwei'),
            'chainId': self.chain_id
        })
        signed_approve_tx = self.web3.eth.account.sign_transaction(approve_tx, self.private_key)
        approve_tx_hash = self.web3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
        return self.web3.to_hex(approve_tx_hash)

    def swap_contract_to_tea(self, amount_in, amount_out_min, path, to, deadline):
        nonce = self.web3.eth.get_transaction_count(self.user_address)
        tx = self.router_contract.functions.swapExactTokensForETH(
            amount_in,
            amount_out_min,
            path,
            to,
            deadline
        ).build_transaction({
            'from': self.user_address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': self.web3.to_wei('{}'.format(self.gasprice), 'gwei'),
            'chainId': self.chain_id
        })
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return self.web3.to_hex(tx_hash)

    def eksekusi_swap(self):
        result = {}
        
        # Memeriksa saldo token
        result['token_balance_tokens'] = self.check_token_balance(self.contract_address)
        
        # Menentukan jalur swap
        path = [self.contract_address, self.wtea_address]
        result['swap_path'] = path
        
        # Melakukan approval
        approval_tx_hash = self.approve_token(self.contract_address, self.router_address, self.amount_in)
        result['approval_tx_hash'] = approval_tx_hash
        approval_receipt = self.web3.eth.wait_for_transaction_receipt(approval_tx_hash)
        result['approval_status'] = 'sukses' if approval_receipt.status == 1 else 'gagal'
        
        # Melakukan swap
        swap_tx_hash = self.swap_contract_to_tea(self.amount_in, self.amount_out_min, path, self.to, self.deadline)
        result['swap_tx_hash'] = swap_tx_hash
        swap_receipt = self.web3.eth.wait_for_transaction_receipt(swap_tx_hash)
        result['swap_status'] = 'sukses' if swap_receipt.status == 1 else 'gagal'
        
        return result


