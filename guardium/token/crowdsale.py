from boa.blockchain.vm.Neo.Blockchain import GetHeight, GetHeader
from boa.blockchain.vm.Neo.Header import GetTimestamp
from boa.blockchain.vm.Neo.Block import GetTransactions
from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Runtime import Notify, CheckWitness
from boa.code.builtins import concat
from guardium.token.token import Token
from guardium.common.storage import StorageAPI
from guardium.common.txio import Attachments, get_asset_attachments

OnTransfer = RegisterAction('transfer', 'from', 'to', 'amount')
OnRefund = RegisterAction('refund', 'to', 'amount')
OnContribution = RegisterAction('contribution', 'from', 'neo', 'tokens')

OnInvalidKYCAddress = RegisterAction('invalid_registration', 'address')
OnKYCRegister = RegisterAction('kyc_registration', 'address')


class Crowdsale():
    kyc_key = b'kyc_ok'
    limited_round_key = b'r1'

    def kyc_register(self, args, token: Token):
        """
        :param args:list a list of addresses to register
        :param token:Token A token object with your ICO settings
        :return:
            int: The number of addresses to register for KYC
        """
        attachments = get_asset_attachments()

        ok_count = 0
        if CheckWitness(token.owner) or attachments.sender_addr == token.whitelister:
            storage = StorageAPI()

            for address in args:
                if len(address) == 20:
                    kyc_storage_key = concat(self.kyc_key, address)
                    storage.put(kyc_storage_key, True)
                    OnKYCRegister(address)
                    ok_count += 1

        return ok_count

    def kyc_status(self, args):
        """
        Gets the KYC Status of an address

        :param args:list a list of arguments
        :return:
            bool: Returns the kyc status of an address
        """
        storage = StorageAPI()

        if len(args) > 0:
            address = args[0]
            kyc_storage_key = concat(self.kyc_key, address)
            return storage.get(kyc_storage_key)

        return False

    def exchange(self, token: Token):
        """
        :param token:Token The token object with NEP5/sale settings
        :return:
            bool: Whether the exchange was successful
        """

        attachments = get_asset_attachments()  # type:  Attachments
        storage = StorageAPI()

        # this looks up whether the exchange can proceed
        can_exchange = self.can_exchange(token, attachments, storage, False)
        if can_exchange <= 0:
            print("Cannot exchange value. Refund process initiated.")
            # This should only happen in the case that there are a lot of TX on the final
            # block before the total amount is reached.  An amount of TX will get through
            # the verification phase because the total amount cannot be updated during that phase
            # because of this, there should be a process in place to manually refund tokens
            if attachments.neo_attached > 0:
                OnRefund(attachments.sender_addr, attachments.neo_attached)

            if attachments.gas_attached > 0:
                OnRefund(attachments.sender_addr, attachments.gas_attached)

            return False

        # lookup the current balance of the address
        current_balance = storage.get(attachments.sender_addr)

        # calculate the amount of tokens the attached neo/gas will earn
        neo_earn = attachments.neo_attached * token.tokens_per_neo / 100000000
        gas_earn = attachments.gas_attached * token.tokens_per_gas / 100000000
        exchanged_tokens = neo_earn + gas_earn

        # add it to the the exchanged tokens and persist in storage
        new_total = exchanged_tokens + current_balance
        storage.put(attachments.sender_addr, new_total)

        # update the in circulation amount
        token.add_to_circulation(exchanged_tokens, storage)

        # dispatch transfer event
        OnTransfer(attachments.receiver_addr, attachments.sender_addr, exchanged_tokens)

        return True

    def can_exchange(self, token: Token, attachments: Attachments, storage: StorageAPI, verify_only: bool) -> bool:
        # """
        # Determines if the contract invocation meets all requirements for the ICO exchange
        # of neo or gas into NEP5 Tokens.
        # Note: This method can be called via both the Verification portion of an SC or the Application portion
        #
        # When called in the Verification portion of an SC, it can be used to reject TX that do not qualify
        # for exchange, thereby reducing the need for manual NEO or GAS refunds considerably
        #
        # :param token:Token A token object with your ICO settings
        # :param attachments:Attachments An attachments object with information about attached NEO/Gas assets
        # :param storage:StorageAPI A StorageAPI object for storage interaction
        # :return:
        #     bool: Whether an invocation meets requirements for exchange
        #
        # """

        # Check if the emergency stop has been activated
        print('Checking if sale is paused.')
        paused = storage.get('paused')
        if paused:
            print("Token Sale Paused")
            return False

        # To accept NEO:
        print('Checking if NEO or GAS are attached.')
        if attachments.neo_attached == 0 and attachments.gas_attached == 0:
            print("No NEO or GAS Attached")
            return False

        # the following looks up whether an address has been registered with the contract for KYC regulations
        print('Checking if address is whitelisted.')
        address = attachments.sender_addr
        kyc_storage_key = concat(self.kyc_key, address)
        whitelisted = storage.get(kyc_storage_key)
        if not whitelisted:
            print("Not Whitelisted in KYC.")
            return False

        # caluclate the amount requested
        amount_requested_neo = attachments.neo_attached * token.tokens_per_neo / 100000000
        amount_requested_gas = attachments.gas_attached * token.tokens_per_gas / 100000000
        amount_requested = amount_requested_neo + amount_requested_gas

        can_exchange = self.calculate_can_exchange(token, amount_requested, attachments.sender_addr, verify_only)

        return can_exchange

    def calculate_can_exchange(self, token: Token, amount: int, address, verify_only: bool):
        """
        Perform custom token exchange calculations here.

        :param token:Token The token settings for the sale
        :param amount:int Number of tokens to convert from asset to tokens
        :param address:bytearray The address to mint the tokens to
        :return:
            bool: Whether or not an address can exchange a specified amount
        """

        height = GetHeight()
        header = GetHeader(height)
        time = header.Timestamp

        # if time < token.token_sale_start_time:
        if time < token.token_sale_start_time:
            print("Token Sale Pending")
            return False

        storage = StorageAPI()

        sale_end = storage.get(token.token_sale_end_time_key)

        if time > sale_end:
            print("Token Sale Over")
            return False

        current_in_circulation = storage.get(token.in_circulation_key)
        current_total_supply = storage.get(token.total_supply_key)

        new_amount = current_in_circulation + amount

        if new_amount > current_total_supply:
            print("Amount greater than total supply")
            return False

        # All checks passed this transaction can continue
        return True
