import json

from django.test import SimpleTestCase

from core.clients.redis_client import RedisClient


class RedisClientTest(SimpleTestCase):
    def setUp(self) -> None:
        self.conn = RedisClient(db_number=15)
        self.conn.flushall()
        self.group_name = 'bid'
        self.data = [
            [
			    "25806.89000000",
			    "8.40658000",
		    ],
            [
                "23226.00000000",
                "0.16350000",
            ],
            [
                "12903.44000000",
                "0.00092000",
            ],
            [
                "25782.93000000",
                "0.08082000",
            ],
            [
                "25770.78000000",
                "0.00028000",
            ],
            [
                "25762.67000000",
                "0.03664000",
            ],
            [
                "25756.98000000",
                "0.04857000",
            ],
	    ]

    def _to_float(self, data: list):
        return list(map(lambda x: (float(x[0]), float(x[1])), data))

    def _json_loads(self, data: list):
        return list(map(lambda x: json.loads(x), data))

    def test_set_dom(self):
        for item in self.data:
            self.conn.set_dom(
                group_name=self.group_name,
                data=item,
            )

        result_0 = self.conn.zrange(
            name=self.group_name,
            start=0,
            end=-1,
            withscores=True,
        )
        price_exists_item = [
            '25806.89000000',
			'5.40658000',
		]
        self.conn.set_dom(
            group_name=self.group_name,
            data=price_exists_item,
        )
        result_1 = self.conn.zrange(
            name=self.group_name,
            start=0,
            end=-1,
            withscores=True,
        )
        self.assertEqual(len(result_0), len(result_1))
        self.assertEqual(
            result_1,
            [('[12903.44, 0.00092]', 12903.44), ('[23226.0, 0.1635]', 23226.0), ('[25756.98, 0.04857]', 25756.98),
             ('[25762.67, 0.03664]', 25762.67), ('[25770.78, 0.00028]', 25770.78), ('[25782.93, 0.08082]', 25782.93),
             ('[25806.89, 5.40658]', 25806.89)],
        )

        price_does_not_exist_item = [
            '35806.89000000',
            '5.40658000',
        ]
        self.conn.set_dom(
            group_name=self.group_name,
            data=price_does_not_exist_item,
        )
        result_2 = self.conn.zrange(
            name=self.group_name,
            start=0,
            end=-1,
            withscores=True,
        )
        self.assertEqual(len(result_0) + 1, len(result_2))
        self.assertEqual(
            result_2,
            [('[12903.44, 0.00092]', 12903.44), ('[23226.0, 0.1635]', 23226.0), ('[25756.98, 0.04857]', 25756.98),
             ('[25762.67, 0.03664]', 25762.67), ('[25770.78, 0.00028]', 25770.78), ('[25782.93, 0.08082]', 25782.93),
             ('[25806.89, 5.40658]', 25806.89), ('[35806.89, 5.40658]', 35806.89)],
        )

    def test_get_dom_by_price(self):
        for item in self.data:
            self.conn.set_dom(
                group_name=self.group_name,
                data=item,
            )

        result = self.conn.get_dom_by_price(group_name=self.group_name)
        self.assertEqual(
            result,
            list(map(lambda x: list(x), sorted(self._to_float(self.data), key=lambda x: x[0]))),
        )

        result = self.conn.get_dom_by_price(group_name=self.group_name, desc=True)
        self.assertEqual(
            result,
            list(map(lambda x: list(x), sorted(self._to_float(self.data), key=lambda x: x[0], reverse=True))),
        )

    def test_get_dom_by_price_slice(self):
        for item in self.data:
            self.conn.set_dom(
                group_name=self.group_name,
                data=item,
            )

        result = self.conn.get_dom_by_price(
            group_name=self.group_name,
            start=2,
            end=5,
        )
        self.assertEqual(
            result,
            [[25756.98, 0.04857], [25762.67, 0.03664], [25770.78, 0.00028], [25782.93, 0.08082]],
        )

        result = self.conn.get_dom_by_price(
            group_name=self.group_name,
            start=2,
            end=5,
            desc=True,
        )
        self.assertEqual(
            result,
            [[25770.78, 0.00028], [25762.67, 0.03664], [25756.98, 0.04857], [23226.0, 0.1635]],
        )
