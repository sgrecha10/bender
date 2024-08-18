# import numpy as np
#
#
# m = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
#
# print(m)

import pandas as pd

df = pd.DataFrame(
    [10, 20, 30.01, 40],
    columns=['Целые'],
    index=['a', 'b', 'c', 'd']
)

print(df.loc['c'])
