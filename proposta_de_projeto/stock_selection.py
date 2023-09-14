import pandas as pd
import datetime as dt


def filter(volumes):
    '''
    # Aplica Filtro de Ativos

        Critérios de Elegibilidade utilizados pelo Centro de Pesquisa de Economia Financeira (NEFIN) da Faculdade de Economia, Administração, Contabilidade e Atuária da Universidade de São Paulo (FEA - USP)

        Uma ação negociada na B3 será elegível em um período t se cumprir os 3 seguintes critérios:
        1. É a ação mais negociada da empresa no período anterior;
        2. A ação tem uma média de negociação diária de R$ 500 mil no período anterior;
        3. A ação é listada há, pelo menos, 2 anos do momento da observação.
    :param volumes: Volumes financeiros negociados dos ativos
    :return: dataframe binário indicando se tal ativo está elegível para um determinado período
    '''

    mtsf = most_traded_stock_filter(volumes)
    mvf = minimum_volume_filter(volumes)
    mltf = minimum_listed_time_filter(volumes)

    eligible_stocks = mtsf & mvf & mltf
    return eligible_stocks


# ----
def most_traded_stock_filter(volumes, period='M'):
    '''
    Seleciona a ação mais negociada da empresa no período anterior.
    :param volumes: Volumes financeiros negociados dos ativos
    :param period: período de filtragem. Default='M', ou seja, mensal
    :return: dataframe binário indicando se tal ativo está elegível para um determinado período
    '''
    stocks = stocks_per_firm(volumes.columns)
    volumes_periodically = volumes.resample(period).sum()
    result = pd.DataFrame(index=volumes_periodically.index, dtype=bool)
    for firm in stocks.keys():
        if len(stocks[firm]) == 1:
            mtpp = pd.Series([True for _ in result.index], index=result.index, name=stocks[firm][0])
        else:
            mtpp = most_traded_per_period(volumes_periodically[stocks[firm]])

        result = pd.concat([result, mtpp], axis=1)
    return result


def stocks_per_firm(stock_list):
    '''
    Função auxiliar de most_traded_stock_filter, que agrupa ações por empresa
    :param stock_list: lista de ações
    :return: dict cuja chave é o código B3 da empresa e os valores são listas de ações
    '''
    firm_dict = dict()
    for stock in stock_list:
        if stock[0:4] not in firm_dict.keys():
            firm_dict[stock[0:4]] = list()
        firm_dict[stock[0:4]].append(stock)
    return firm_dict


def most_traded_per_period(volumes):
    '''
    Função auxiliar de most_traded_stock_filter, verifica qual ação tem maior liquidez
    :param volumes: Volumes financeiros negociados dos ativos de 1 empresa
    :return: dataframe binário indicando se tal ativo está elegível para um determinado período
    '''
    result = pd.DataFrame(index=volumes.index, columns=volumes.columns, dtype=bool)
    for date in volumes.index:
        if volumes.loc[date].isna().all():
            result.loc[date] = [False for _ in range(len(volumes.loc[date]))]
        else:
            result.loc[date] = volumes.loc[date] == volumes.loc[date].max()
    return result


# ----
def minimum_volume_filter(volumes, period='M', limit=5e5):
    '''
    Filtro de volume mínimo. Verifica se as ações atingem o limite de volume médio exigido
    :param volumes: Volumes financeiros negociados dos ativos de 1 empresa
    :param period: período de filtragem. Default='M', ou seja, mensal
    :param limit: Limite mínimo exigido. Default=5e5, ou seja, 500 mil
    :return: dataframe binário indicando se tal ativo está elegível para um determinado período
    '''
    return volumes.resample(period).mean() >= limit


# ----
def minimum_listed_time_filter(volumes, period='M', limit=500):
    '''
    Filtro de tempo de listagem. Verifica se as ações atingem o tempo mínimo de listagem
    :param volumes: Volumes financeiros negociados dos ativos de 1 empresa
    :param period: período de filtragem. Default='M', ou seja, mensal
    :param limit: Limite mínimo exigido. Default=500, ou seja, 500 dias úteis ou 2 anos
    :return: dataframe binário indicando se tal ativo está elegível para um determinado período
    '''
    result = pd.DataFrame(columns=volumes.columns, index=volumes.index)
    for stock in volumes.columns:
        first_trading_day = get_first_trading_day(volumes[stock])
        if first_trading_day:
            first_eligible_day = first_trading_day + dt.timedelta(days=limit)
        else:
            first_eligible_day = dt.datetime(2200, 1, 1)
        result[stock] = pd.Series(volumes[stock].index > first_eligible_day, index=volumes[stock].index)

    result = result.resample(period).apply(all)
    return result


def get_first_trading_day(volumes: pd.Series):
    '''
    Função auxiliar de minimum_listed_time_filter. Busca primeiro dia de cotação da ação
    :param volumes: Volumes financeiros negociados dos ativos de 1 empresa
    :return: Data da primeira negociação
    '''
    trading_dates = volumes.dropna().index
    return trading_dates[0] if len(trading_dates) > 0 else None
