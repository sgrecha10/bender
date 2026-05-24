import logging

from web3 import Web3
from web3.contract.contract import Contract

logger = logging.getLogger(__name__)


class UniswapQuoterService:
    def __init__(
        self,
        quoter_contract: type[Contract] | Contract,
    ):
        self.quoter_contract = quoter_contract

    def get_quote_exact_input_single(
        self,
        amount_in: int,
        token_in: str,
        token_out: str,
        pool_fee: int,
    ) -> int:

        params = {
            'tokenIn': Web3.to_checksum_address(token_in),
            'tokenOut': Web3.to_checksum_address(token_out),
            'fee': pool_fee,
            'amountIn': amount_in,
            'sqrtPriceLimitX96': 0,
        }

        amount_out = self.quoter_contract.functions.quoteExactInputSingle(**params).call()

        logger.info(
            'Quoted amount_out=%s',
            amount_out,
        )

        return amount_out
