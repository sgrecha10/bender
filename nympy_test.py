# import numpy as np
#
#
# m = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
#
# print(m)

# import pandas as pd
#
# df = pd.DataFrame(
#     [10, 20, 30.01, 40],
#     columns=['Целые'],
#     index=['a', 'b', 'c', 'd']
# )
#
# print(df.loc['c'])


# import matplotlib as mpl
# import matplotlib.pyplot as plt
#
# import numpy as np
#
# # plt.style.use('seaborn')
# # mpl.rcParams['font.family'] = 'serif'
# # mpl.rcParams['font.serif'] = 'Times New Roman'
#
# np.random.seed(1000)
# y = np.random.standard_normal(20)
#
# x = np.arange(len(y))
# # pit.plot(x, y)
# plt.plot(y)
# # pit.plot(y, yerr=np.random.standard_normal(20))
#
# plt.savefig('foo.png')


import pandas as pd
import cufflinks as cf
import plotly.offline as plyo
import numpy as np
import plotly.io as pio


plyo.init_notebook_mode(connected=True)
cf.go_offline()

a = np.random.standard_normal((258, 5)).cumsum(axis=0)
index = pd.date_range('2019-1-1', freq='B', periods=len(a))
index = index.astype(str)  # отсебятина, проверить

df = pd.DataFrame(100 + 5 * a, columns=list('abcde'), index=index)
# df.head()

# plyo.iplot(df.iplot(asFigure=True), image='png', filename='ply_01')

qf = df[['a', 'b']].iplot(
    asFigure=True,
    theme='polar',
    title='График временных рядов',
    xTitle='Дата',
    yTitle='Значение',
    mode={'a': 'markers', 'b': 'lines+markers'},
    symbol={'a': 'circle', 'b': 'diamond'},
    size=3.5,
    colors={'a': 'blue', 'b': 'magenta'},
)

# qf = cf.QuantFig(


# pio.write_image(qf, "op.png")

res = pio.to_html(qf)

f = open("demofile2.html", "a")
f.write(res)
f.close()

# print(res)

# plyo.iplot(fig, image='png', filename='ply_02')



# import plotly
# import plotly.graph_objs as go
# import plotly.express as px
# from plotly.subplots import make_subplots
# import numpy as np
# import pandas as pd
#
# x = np.arange(0, 5, 0.1)
#
#
# def f(x):
#     return x**2
#
#
# fig = px.scatter(x=x, y=f(x))
# # fig.show()
# fig.write_image('fig1.png')
