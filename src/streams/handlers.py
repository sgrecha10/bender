import json
from collections import defaultdict
import os
from core.clients.binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient
from pprint import pprint

output_dict = defaultdict()

def message_handler(_, message):
    # logging.info(message)

    json_data = json.loads(message)
    print(json_data)
    # print('bid', json_data['b'])

    # bid_list = json_data.get('b')
    # for bid, quantity in bid_list:
    #     output_dict[bid] = float(quantity)
    # data = list(sorted(output_dict.items(), key=lambda item: float(item[0]), reverse=True))
    #
    # os.system('clear')
    # os.system('clear')
    # pprint(data)


def start_stream():
    my_client = SpotWebsocketStreamClient(on_message=message_handler)
    my_client.diff_book_depth(symbol="bnbusdt")
    # time.sleep(5)
    # my_client.stop()


# if __name__ == '__main__':
#     start_stream()
