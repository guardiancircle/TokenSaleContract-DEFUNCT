from guardium.common.storage import StorageAPI
from boa.blockchain.vm.Neo.Blockchain import GetHeight, GetHeader, GetBlock
from boa.blockchain.vm.Neo.Header import GetTimestamp


class Token():
    """
    Basic settings for an NEP5 Token and ICO
    """
    name = 'Guardium'
    symbol = 'GDM'
    decimals = 8

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Guardium Control Wallet
    owner = b'\xb3\xc0\xa3\xef\\\x98\x94\xdf\xfb\x07B\xb5\xc8\x18\xa7\x07"\x19\xc27'  # DEVELOPMENT
    whitelister = b'~\xc4\x96\x16=\xa8\x1f\xfe\x9d\xbe\xe4bsvP\x07a\xd1\\q'  # WHITELISTER
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    # 100M total GDM supply
    in_circulation_key = b'gdm_in_circ'
    total_supply_key = b'gdm_tot_supply'
    token_sale_end_time_key = b'gdm_sale_end'

    total_supply = 100000000 * 100000000  # 100M tokens
    initial_amount_company = 80000000 * 100000000  # 80M to company account (includes coins for presale buyers, advisors, etc.)

    tokens_per_neo = 200 * 100000000
    tokens_per_gas = 70 * 100000000

    token_sale_start_time = 1525158000  # 05/01/2018 @ 7:00am (UTC)
    token_sale_end_time = 1527836400  # 06/01/2018 @ 7:00am (UTC)

    def end_ico(self):
        # Ends ICO Manually

        storage = StorageAPI()

        height = GetHeight()
        header = GetHeader(height)
        time = header.Timestamp

        storage.put(self.token_sale_end_time_key, time)     # Based on timestamp

        return True

    def burn_unsold_tokens(self):
        # Burns unsold tokens by modifying total supply

        storage = StorageAPI()

        in_circ = storage.get(self.in_circulation_key)
        storage.put(self.total_supply_key, in_circ)

        return True

    def crowdsale_available_amount(self):
        """
        :return: int The amount of tokens left for sale in the crowdsale
        """
        storage = StorageAPI()

        in_circ = storage.get(self.in_circulation_key)
        current_supply = storage.get(self.total_supply_key)
        available = current_supply - in_circ

        if available < 0:
            return 0

        return available

    def add_to_circulation(self, amount: int, storage: StorageAPI):
        """
        Adds an amount of token to circlulation

        :param amount: int the amount to add to circulation
        :param storage:StorageAPI A StorageAPI object for storage interaction
        """
        current_supply = storage.get(self.in_circulation_key)
        current_supply += amount
        storage.put(self.in_circulation_key, current_supply)

    def get_circulation(self, storage: StorageAPI):
        """
        Get the total amount of tokens in circulation

        :param storage:StorageAPI A StorageAPI object for storage interaction
        :return:
            int: Total amount in circulation
        """
        return storage.get(self.in_circulation_key)
