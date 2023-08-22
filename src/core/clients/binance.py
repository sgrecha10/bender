from typing import Tuple

import hmac, hashlib
import requests
from pprint import pprint
from collections import defaultdict


class BinanceClient:
    def __init__(self, credentials: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uri = credentials['uri']
        self.api_key = credentials['api_key']
        self.secret_key = credentials['secret_key']
        # self.hmac = credentials['hmac']

    def _request(self, data: dict, urn: str, method: str) -> Tuple[dict, bool]:
        with requests.Session() as session:
            headers = {
                'X-MBX-APIKEY': self.api_key,
            }
            session.headers.update(headers)

            res = session.request(
                method=method,
                url=self.uri + urn,
                data=data,
            )

            if res.ok:
                try:
                    payload = res.json()
                except ValueError:
                    payload = res.text

                return payload, True

            return {
                'status_code': res.status_code,
                'reason': res.reason
            }, False


    def get_status(self):
        urn = '/sapi/v1/system/status'
        method = 'GET'
        data = {}

        res, is_ok = self._request(data, urn, method)
        return (res, True) if res['status'] == 0 else (res, False)

    def get_coins(self):
        urn = '/sapi/v1/capital/config/getall'
        method = 'GET'
        data = {
            'signature': self._get_sign('')
        }

        return self._request(data, urn, method)

    def get_symbols(self):
        urn = '/sapi/v1/margin/allPairs'
        method = 'GET'
        data = {}

        return self._request(data, urn, method)


    def _get_sign(self, payload):
        m = hmac.new(self.secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256)
        return m.hexdigest()



    # @staticmethod
    # def ed25519_signature(private_key, payload, private_key_pass=None):
    #     private_key = ECC.import_key(private_key, passphrase=private_key_pass)
    #     signer = eddsa.new(private_key, "rfc8032")
    #     signature = signer.sign(payload.encode("utf-8"))
    #     return b64encode(signature)
    #
    #
    #     try:
    #         return self.ed25519_signature(
    #             private_key=self.secret_key,
    #             payload,
    #             self.private_key_pass
    #         )
    #     except ValueError:
    #         return rsa_signature(self.private_key, payload, self.private_key_pass)