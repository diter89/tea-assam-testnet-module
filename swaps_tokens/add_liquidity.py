from web3 import Web3

class LiquidityManager:
    def __init__(self, user_address: str, private_key: str, gasprice: int, contract_token: str, amount: int):
        """Inisialisasi LiquidityManager dengan parameter pengguna dan koneksi blockchain."""
        
        self.rpc_url = "https://assam-rpc.tea.xyz"
        self.chain_id = 93384
        self.contract_token = contract_token
        self.private_key = private_key
        self.user_address = user_address
        self.gasprice = gasprice
        self.amount = amount 
        
        
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.web3.is_connected():
            raise Exception("Gagal terhubung ke blockchain.")
        
        
        self.router_address = "0xACBc89FF219232C058428D166860df4eA0114999"
        
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
                    {"internalType": "address", "name": "tokenA", "type": "address"},
                    {"internalType": "address", "name": "tokenB", "type": "address"},
                    {"internalType": "uint256", "name": "amountADesired", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountBDesired", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountAMin", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountBMin", "type": "uint256"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "addLiquidity",
                "outputs": [
                    {"internalType": "uint256", "name": "amountA", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountB", "type": "uint256"},
                    {"internalType": "uint256", "name": "liquidity", "type": "uint256"}
                ],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        self.router_contract = self.web3.eth.contract(address=self.router_address, abi=self.router_abi)
        self.wtea_address = self.router_contract.functions.WETH().call()  # Alamat WTEA
        
        self.token_a_decimals = self.get_token_decimals(self.contract_token)
        self.token_b_decimals = self.get_token_decimals(self.wtea_address)
        
        self.amount_a_desired = int(self.amount * 10**self.token_a_decimals)  # Token A (kontrak)
        self.amount_b_desired = int(self.amount * 10**self.token_b_decimals)  # Token B (WTEA)
        
        self.amount_a_min = int(self.amount_a_desired * 0.90)
        self.amount_b_min = int(self.amount_b_desired * 0.90)
        
        self.to = self.user_address
        
        self.deadline = self.web3.eth.get_block('latest')['timestamp'] + 600

    def get_token_decimals(self, token_address):
        token_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]
        token_contract = self.web3.eth.contract(address=token_address, abi=token_abi)
        return token_contract.functions.decimals().call()

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
        decimals = self.get_token_decimals(token_address)
        return token_balance / 10**decimals

    def check_allowance(self, token_address, spender_address):
        token_abi = [
            {
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]
        token_contract = self.web3.eth.contract(address=token_address, abi=token_abi)
        allowance = token_contract.functions.allowance(self.user_address, spender_address).call()
        decimals = self.get_token_decimals(token_address)
        return allowance / 10**decimals

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
        
        nonce = self.web3.eth.get_transaction_count(self.user_address, 'pending')
        approve_tx = token_contract.functions.approve(spender_address, amount).build_transaction({
            'from': self.user_address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': self.web3.to_wei(self.gasprice + 10, 'gwei'),
            'chainId': self.chain_id
        })
        signed_approve_tx = self.web3.eth.account.sign_transaction(approve_tx, self.private_key)
        approve_tx_hash = self.web3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
        return self.web3.to_hex(approve_tx_hash)

    def check_pair_address(self, token_a_address, token_b_address):
        factory_address = "0x384d179F3f499E876fAd943d270AD38bb414aC24"
        factory_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "tokenA", "type": "address"},
                    {"internalType": "address", "name": "tokenB", "type": "address"}
                ],
                "name": "getPair",
                "outputs": [{"internalType": "address", "name": "pair", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        factory_contract = self.web3.eth.contract(address=factory_address, abi=factory_abi)
        pair_address = factory_contract.functions.getPair(token_a_address, token_b_address).call()
        pair_exists = pair_address != "0x0000000000000000000000000000000000000000"
        return {"pair_exists": pair_exists, "pair_address": pair_address}

    def calculate_required_amount(self, token_address, amount, pair_address):
        pair_abi = [
            {
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"internalType": "uint112", "name": "reserve0", "type": "uint112"},
                    {"internalType": "uint112", "name": "reserve1", "type": "uint112"},
                    {"internalType": "uint32", "name": "blockTimestampLast", "type": "uint32"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "token0",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "token1",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        pair_contract = self.web3.eth.contract(address=pair_address, abi=pair_abi)
        token0 = pair_contract.functions.token0().call()
        token1 = pair_contract.functions.token1().call()
        reserve0, reserve1, _ = pair_contract.functions.getReserves().call()
        
        if token_address == token0:
            if reserve0 == 0:
                return amount
            return (amount * reserve1) // reserve0
        else:
            if reserve1 == 0:
                return amount
            return (amount * reserve0) // reserve1

    def add_liquidity(self, token_a_address, token_b_address, amount_a_desired, amount_b_desired, amount_a_min, amount_b_min, to, deadline):
        """Menambahkan likuiditas dan mengembalikan hash transaksi."""
        nonce = self.web3.eth.get_transaction_count(self.user_address, 'pending')
        current_gas_price = self.web3.eth.gas_price
        gas_price = int(current_gas_price * 1.5)
        
        tx = self.router_contract.functions.addLiquidity(
            token_a_address,
            token_b_address,
            amount_a_desired,
            amount_b_desired,
            amount_a_min,
            amount_b_min,
            to,
            deadline
        ).build_transaction({
            'from': self.user_address,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': gas_price,
            'chainId': self.chain_id
        })
        
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return self.web3.to_hex(tx_hash)

    def main_add_liquidity(self):
        """Metode utama untuk menambahkan likuiditas dan mengembalikan semua informasi dalam dictionary."""
        result = {}
        
        result["token_a_balance_tokens"] = self.check_token_balance(self.contract_token)
        result["token_b_balance_tokens"] = self.check_token_balance(self.wtea_address)
        
        result["allowance_token_a_tokens"] = self.check_allowance(self.contract_token, self.router_address)
        result["allowance_token_b_tokens"] = self.check_allowance(self.wtea_address, self.router_address)
        
        result["approval_tx_hash_token_a"] = self.approve_token(self.contract_token, self.router_address, self.amount_a_desired)
        result["approval_tx_hash_token_b"] = self.approve_token(self.wtea_address, self.router_address, self.amount_b_desired)
        
        try:
            receipt_a = self.web3.eth.wait_for_transaction_receipt(result["approval_tx_hash_token_a"], timeout=300)
            result["approval_status_token_a"] = "sukses" if receipt_a.status == 1 else "gagal"
        except Exception as e:
            result["approval_status_token_a"] = f"error: {str(e)}"
        
        try:
            receipt_b = self.web3.eth.wait_for_transaction_receipt(result["approval_tx_hash_token_b"], timeout=300)
            result["approval_status_token_b"] = "sukses" if receipt_b.status == 1 else "gagal"
        except Exception as e:
            result["approval_status_token_b"] = f"error: {str(e)}"
        
        pair_info = self.check_pair_address(self.contract_token, self.wtea_address)
        result["pair_exists"] = pair_info["pair_exists"]
        result["pair_address"] = pair_info["pair_address"]
        
        result["initial_amount_a_desired_tokens"] = self.amount_a_desired / 10**self.token_a_decimals
        result["initial_amount_b_desired_tokens"] = self.amount_b_desired / 10**self.token_b_decimals
        result["initial_amount_a_desired_wei"] = self.amount_a_desired
        result["initial_amount_b_desired_wei"] = self.amount_b_desired
        
        if pair_info["pair_exists"]:
            required_amount_b = self.calculate_required_amount(self.contract_token, self.amount_a_desired, pair_info["pair_address"])
            if required_amount_b != self.amount_b_desired:
                result["warning"] = f"Jumlah token B disesuaikan dari {self.amount_b_desired} ke {required_amount_b} berdasarkan cadangan."
                self.amount_b_desired = required_amount_b
                self.amount_b_min = int(required_amount_b * 0.90)
        
        result["final_amount_b_desired_tokens"] = self.amount_b_desired / 10**self.token_b_decimals
        result["final_amount_b_desired_wei"] = self.amount_b_desired
        
        result["add_liquidity_tx_hash"] = self.add_liquidity(
            self.contract_token,
            self.wtea_address,
            self.amount_a_desired,
            self.amount_b_desired,
            self.amount_a_min,
            self.amount_b_min,
            self.to,
            self.deadline
        )
        
        try:
            receipt = self.web3.eth.wait_for_transaction_receipt(result["add_liquidity_tx_hash"], timeout=300)
            result["add_liquidity_status"] = "sukses" if receipt.status == 1 else "gagal"
        except Exception as e:
            result["add_liquidity_status"] = f"error: {str(e)}"
        
        return result


