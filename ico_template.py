"""
===================================
NEX ICO Template
Author: Thomas Saunders
Email: tom@neonexchange.org
Date: Dec 11 2017

===================================
Bridge Protocol MainNet Deployment
Author: StTa/AnHy
Email: stamberg@bridgeprotocol.io/ahyduchak@bridgeprotocol.io
Date: Feb 21 2018

===================================
Guardium Token Contract
Author: Chris Hayes
Email: tech@guardium.co
Date: May 1 2018
"""

from boa.blockchain.vm.Neo.Runtime import GetTrigger, CheckWitness, Notify
from boa.blockchain.vm.Neo.Blockchain import GetHeight, GetHeader, GetBlock
from boa.blockchain.vm.Neo.Header import GetTimestamp
from boa.blockchain.vm.Neo.Block import GetTransactions
from boa.blockchain.vm.Neo.TriggerType import Application, Verification
from boa.blockchain.vm.Neo.Transaction import GetUnspentCoins
from guardium.common.storage import StorageAPI
from guardium.common.txio import Attachments, get_asset_attachments
from guardium.token.token import Token
from guardium.token.nep5 import NEP5Handler
from guardium.token.crowdsale import Crowdsale


def Main(operation, args):
    """

    :param operation: str The name of the operation to perform
    :param args: list A list of arguments along with the operation
    :return:
        bytearray: The result of the operation
    """

    trigger = GetTrigger()
    token = Token()

    #print("Executing ICO Template")

    # This is used in the Verification portion of the contract
    # To determine whether a transfer of system assets ( NEO/Gas) involving
    # This contract's address can proceed
    if trigger == Verification:

        # check if the invoker is the owner of this contract
        is_owner = CheckWitness(token.owner)

        # If owner, proceed
        if is_owner:

            return True

        # Otherwise, we need to lookup the assets and determine
        # If attachments of assets is ok
        attachments = get_asset_attachments()  # type:Attachments

        storage = StorageAPI()

        crowdsale = Crowdsale()

        return crowdsale.can_exchange(token, attachments, storage, True)

    elif trigger == Application:

        if operation != None:

            nep = NEP5Handler()

            for op in nep.get_methods():
                if operation == op:
                    return nep.handle_nep51(operation, args, token)

            if operation == 'deploy':
                return deploy(token)

            if operation == 'burn_unsold_tokens':
                return burnUnsoldTokens(token)

            if operation == 'pause_sale':
                return pauseSale(token)

            if operation == 'resume_sale':
                return resumeSale(token)

            if operation == 'end_ico':
                return endICO(token)

            if operation == 'circulation':
                storage = StorageAPI()
                return token.get_circulation(storage)

            # the following are handled by crowdsale

            sale = Crowdsale()

            if operation == 'mintTokens':
                return sale.exchange(token)

            if operation == 'crowdsale_register':
                return sale.kyc_register(args, token)

            if operation == 'crowdsale_status':
                return sale.kyc_status(args)

            if operation == 'crowdsale_available':
                return token.crowdsale_available_amount()

            return 'unknown operation'

    return False


def deploy(token: Token):
    """
    :param token: Token The token to deploy
    :return:
        bool: Whether the operation was successful
    """
    if not CheckWitness(token.owner):
        print("Not Contract Owner, Denied.")
        return False

    storage = StorageAPI()

    if not storage.get('Initialized.'):
        print("Deploying Contract")

        # do deploy logic
        storage.put('Initialized.', 1)
        storage.put('paused', 1)  # Pause the sale by default

        storage.put(token.total_supply_key, token.total_supply)
        storage.put(token.token_sale_end_time_key, token.token_sale_end_time)  # Based on timestamp, has to be changeable
        storage.put(token.owner, token.initial_amount_company)  # Initial 80M to company and presale buyers
        token.add_to_circulation(token.initial_amount_company, storage)

        return True

    return False


def burnUnsoldTokens(token: Token):
    if not CheckWitness(token.owner):
        print("Not Contract Owner, Denied.")
        return False
    else:
        print("Burning Unsold Tokens..")
        token.burn_unsold_tokens()
        return True

    return False


def pauseSale(token: Token):
    """
    :param token: Token The token to stop
    :return:
        bool: Whether the operation was successful
    """
    if not CheckWitness(token.owner):
        print("Not Contract Owner, Denied.")
        return False

    else:
        storage = StorageAPI()
        storage.put('paused', 1)
        print("Sale Paused.")
        return True


def resumeSale(token: Token):
    if not CheckWitness(token.owner):
        print("Not Contract Owner, Denied.")
        return False

    else:
        storage = StorageAPI()
        storage.put('paused', 0)
        print("Sale Resumed..")
        return True


def endICO(token: Token):
    """
    :param token: End the ICO manually
    :return:
        bool: Whether the operation was successful
    """
    if not CheckWitness(token.owner):
        print("Not Contract Owner, Denied.")
        return False
    else:
        token.end_ico()
        return True

    return False
