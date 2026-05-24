import logging

logger = logging.getLogger(__name__)


class UniswapGetPositionService:
    def __init__(self, position_manager_contract):
        self.position_manager_contract = position_manager_contract

    def get_position(
        self,
        token_id: int,
    ) -> dict:
        """Retrieve exists pool position."""
        position = self.position_manager_contract.functions.positions(token_id).call()

        logger.info(
            'Pool %s, liquidity: %s',
            token_id,
            position[7],
        )

        return {
            'token0': position[2],
            'token1': position[3],
            'fee': position[4],
            'tick_lower': position[5],
            'tick_upper': position[6],
            'liquidity': position[7],
            'tokens_owed0': position[10],
            'tokens_owed1': position[11],
        }
