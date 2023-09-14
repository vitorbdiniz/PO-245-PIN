import pandas as pd
import datetime as dt


def calculate_all_portfolios_returns(portfolios_weights, prices, leverage=True):
    '''
    Calcula retornos de todos os portfolios gerados
    :param portfolios_weights:
    :param prices:
    :param leverage:
    :return:
    '''
    returns = prices.pct_change()
    all_returns = {
        portfolio_name: calculate_portfolio_returns(weights, returns)
        for portfolio_name, weights in portfolios_weights.items()
    }
    if leverage:
        all_returns['long_short'] = all_returns['long'] - all_returns['short']
    return pd.DataFrame(all_returns)


def calculate_portfolio_returns(portfolio_weights, returns):
    '''
    Calcula retornos de 1 único portfólio
    :param portfolio_weights:
    :param returns:
    :return:
    '''
    first_date = min(portfolio_weights.keys())
    selic = get_selic(first_date, dt.datetime.now())
    dates = pd.Series(portfolio_weights.keys(), index=portfolio_weights.keys())
    portfolio_returns = dict()
    for date in returns.index:
        if date <= first_date:
            continue
        portfolio = get_portfolio(portfolio_weights, dates, date)
        stocks_retuns = get_stocks_returns(portfolio, returns.loc[date], selic.loc[date])
        portfolio_returns[date] = stocks_retuns
    return pd.Series(portfolio_returns)


def get_portfolio(portfolio_weights, dates, date):
    '''
    Busca portfólio de uma data específica
    :param portfolio_weights:
    :param dates:
    :param date:
    :return:
    '''
    i = dates.index.get_indexer([date], method='pad')[0]
    if date == dates.index[i]:
        # Carteira montada apenas no fechamento
        date -= dt.timedelta(days=1)
        i = dates.index.get_indexer([date], method='pad')[0]
    target_date = dates.index[i]
    return portfolio_weights[target_date]


def get_stocks_returns(portfolio, returns, selic):
    '''
    Calcula retornos de Ações
    :param portfolio:
    :param returns:
    :param selic:
    :return:
    '''
    stocks_returns = 0
    for stock in portfolio.keys():
        weight = portfolio[stock]
        if stock == 'SELIC':
            r = selic
        else:
            r = returns[stock] if pd.notna(returns[stock]) else 0
        stocks_returns += r * weight
    return stocks_returns


def get_selic(start, end):
    '''
    Busca valor diário da Selic
    :param start:
    :param end:
    :return:
    '''
    str_start = start.strftime('%d/%m/%Y')
    str_end = end.strftime('%d/%m/%Y')
    url = "http://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=csv&dataInicial=" + str_start + "&dataFinal=" + str_end
    selic = pd.read_csv(url, sep=";", decimal=',')
    selic.index = [dt.datetime.strptime(date, '%d/%m/%Y') for date in selic['data']]
    selic['valor'] = selic['valor'] / 100
    return selic['valor']
