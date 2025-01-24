import numpy as np
import pandas as pd

# dates = pd.date_range('1995-12-31', periods=480, freq='M', name='Date')
# stoks = pd.Index(['s{:04d}'.format(i) for i in range(4000)])
# df = pd.DataFrame(
#     data=np.random.rand(480, 4000),
#     index=dates,
#     columns=stoks,
# )
# print(df.tail())
# print(df.iloc[:5, :5])
# print(stoks)





m, n = 480, 10000
dates = pd.date_range('1995-12-31', periods=m, freq='M', name='Date')
stocks = pd.Index(['s{:04d}'.format(i) for i in range(n)])
df = pd.DataFrame(np.random.rand(m, n), dates, stocks)
market = pd.Series(np.random.rand(m), dates, name='Market')
df = pd.concat([df, market], axis=1)

# print(df.head())

def beta(df, market=None):
    # If the market values are not passed,
    # I'll assume they are located in a column
    # named 'Market'.  If not, this will fail.
    if market is None:
        market = df['Market']
        df = df.drop('Market', axis=1)
    X = market.values.reshape(-1, 1)
    X = np.concatenate([np.ones_like(X), X], axis=1)
    b = np.linalg.pinv(X.T.dot(X)).dot(X.T).dot(df.values)
    return pd.Series(b[1], df.columns, name=df.index[-1])

def roll(df, w):
    for i in range(df.shape[0] - w + 1):
        yield pd.DataFrame(df.values[i:i+w, :], df.index[i:i+w], df.columns)

# betas = pd.concat([beta(sdf) for sdf in roll(df.pct_change().dropna(), 12)], axis=1).T

# print(betas)


def calc_beta(df):
    np_array = df.values
    m = np_array[:,0] # market returns are column zero from numpy array
    s = np_array[:,1] # stock returns are column one from numpy array
    covariance = np.cov(s,m) # Calculate covariance between stock and market
    beta = covariance[0,1]/covariance[1,1]
    return beta

def calc_beta_pdf(df):
    variance = df.var()
    return variance, df['s0001'].var()



print(df)
# print(calc_beta(df))
print(calc_beta_pdf(df))


# experimental setup

# m, n = 12, 2
# dates = pd.date_range('1995-12-31', periods=m, freq='M', name='Date')
#
# cols = ['Open', 'High', 'Low', 'Close']
# dfs = {'s{:04d}'.format(i): pd.DataFrame(np.random.rand(m, 4), dates, cols) for i in range(n)}
#
# market = pd.Series(np.random.rand(m), dates, name='Market')
#
# df = pd.concat([market] + [dfs[k].Close.rename(k) for k in dfs.keys()], axis=1).sort_index(inplace=True)
#
# betas = pd.concat([beta(sdf) for sdf in roll(df.pct_change().dropna(), 12)], axis=1).T

# for c, col in betas.iteritems():
#     df[c]['Beta'] = col

# df['s0000'].head(20)
