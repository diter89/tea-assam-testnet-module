from web3 import Web3

class DexChecker:
    RPC_URL = "https://assam-rpc.tea.xyz"
    FACTORY_ADDRESS = "0x384d179F3f499E876fAd943d270AD38bb414aC24"
    Router_ADDRESS = "0xACBc89FF219232C058428D166860df4eA0114999" 
    DEX_FACTORY_ABI = [
        {
            "inputs": [
                {"internalType": "address", "name": "tokenA", "type": "address"},
                {"internalType": "address", "name": "tokenB", "type": "address"}
            ],
            "name": "getPair",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    LP_TOKEN_ABI = [
        {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "payable": False, "stateMutability": "view", "type": "function"},
        {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "payable": False, "stateMutability": "view", "type": "function"},
        {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
        {"constant": True, "inputs": [{"name": "", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
        {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"}
    ]

    ERC20_ABI = [
        {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"},
        {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"}
    ]

    def __init__(self, token_default: str, token_contract: str):
        self.TOKEN_A =  token_default
        self.TOKEN_B =  token_contract
        
        self.web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        self.check_connection()
        self.factory_contract = self.web3.eth.contract(address=self.FACTORY_ADDRESS, abi=self.DEX_FACTORY_ABI)

    def check_connection(self):
        if not self.web3.is_connected():
            raise Exception("Gagal terhubung ke blockchain!")

    def get_pair_address(self):
        return self.factory_contract.functions.getPair(self.TOKEN_A, self.TOKEN_B).call()

    def get_lp_token_details(self, pair_address):
        lp_contract = self.web3.eth.contract(address=pair_address, abi=self.LP_TOKEN_ABI)
        token0 = lp_contract.functions.token0().call()
        token1 = lp_contract.functions.token1().call()
        total_supply = lp_contract.functions.totalSupply().call()
        
        decimals_lp = lp_contract.functions.decimals().call()
        
        token0_contract = self.web3.eth.contract(address=token0, abi=self.ERC20_ABI)
        token1_contract = self.web3.eth.contract(address=token1, abi=self.ERC20_ABI)
        reserve_token0 = token0_contract.functions.balanceOf(pair_address).call()
        reserve_token1 = token1_contract.functions.balanceOf(pair_address).call()
        
        decimals_token0 = token0_contract.functions.decimals().call()
        decimals_token1 = token1_contract.functions.decimals().call()
        
        total_supply_normal = total_supply / 10**decimals_lp
        reserve_token0_normal = reserve_token0 / 10**decimals_token0
        reserve_token1_normal = reserve_token1 / 10**decimals_token1
        
        if reserve_token1_normal > 0:
            price_ratio = reserve_token0_normal / reserve_token1_normal
        else:
            price_ratio = "Tidak dapat dihitung (saldo nol)"
        return {
            "token0": token0,
            "token1": token1,
            "total_supply": total_supply_normal,
            "reserve_token0": reserve_token0_normal,
            "reserve_token1": reserve_token1_normal,
            "price_ratio": price_ratio
        }

    def info(self):
        return {
                "default_token": "{}".format(self.TOKEN_A),
                "contract_token": "{}".format(self.TOKEN_B)
                } 

    def details(self):
        pair_address = self.get_pair_address()
        if pair_address != "0x0000000000000000000000000000000000000000":
            detail = self.get_lp_token_details(pair_address)
            return {
                    "pair_found": "{}".format(pair_address),
                    "default_token": "{}".format(detail["token0"]),
                    "contract_token": "{}".format(detail["token1"]),
                    "total_supply": "{:.6f}".format(detail["total_supply"]),
                    "reserve_default_token": "{:.6f}".format(detail["reserve_token0"]),
                    "reserve_contract_token": "{:.6f}".format(detail["reserve_token1"]),
                    "price_ratio": "{}".format(detail["price_ratio"]),
                    }
        else:
            return "❌ pair belum ada di DEX Factory"


