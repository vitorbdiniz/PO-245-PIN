import datetime as dt

import numpy as np
import pandas as pd


def portfolio_build(pin_model, eligible_stocks, pin_quantile=0.75, delta_quantile=0.8, weight_sum_limit=1,
                    leverage=True, fixed_income_weight=1):
    """
        Constroi portfolios a partir dos PINs e das ações elegíveis. Se houver alavancagem, cria portfólio short.
        Nos portfólios long e long only são selecionadas as ações pelos maiores PINs e maiores deltas.
        Já o portfólio short  são selecionadas as ações pelos maiores PINs e menores deltas.
        O portfólio long alavancado em uma taxa de `fixed_income_weight` aloca tal taxa na SELIC.
    :param pin_model: resultados do modelo PIN executado previamente
    :param eligible_stocks: dataframe binário com ações elegíveis
    :param pin_quantile: Quantil utilizado como mínimo para seleção de ações por PIN
    :param delta_quantile: Quantil utilizado como mínimo para seleção de ações por Delta (1-delta_quantile) será utilizado para o portfólio short.
    :param weight_sum_limit: Peso total do portfolio.
    :param leverage: flag de alavancagem.
    :param fixed_income_weight: percentual alocado na SELIC, em caso de alavancagem
    :return: dicionário contendo 2 sub-dicionários: um com pesos dos ativos selecionados e um com as PINs desses ativos.
    """
    dates = get_unique_dates(pin_model['period'])
    long_portfolio_pin = pd.DataFrame()
    short_portfolio_pin = pd.DataFrame()

    for date in eligible_stocks.index:
        if not eligible_stocks.loc[date].any():
            continue
        if date < dates[0]:
            continue
        if date > dt.datetime.now():
            continue
        pins = get_pins(pin_model, eligible_stocks, date)
        long, short = select_asset_by_delta(pins, q=delta_quantile)
        long = select_asset_by_pin(long, q=pin_quantile)
        short = select_asset_by_pin(short, q=pin_quantile)

        long_portfolio_pin = pd.concat([long_portfolio_pin, long], axis=0)

        if leverage:
            short_portfolio_pin = pd.concat([short_portfolio_pin, short], axis=0)

        long_weights = get_portfolio_weights(long_portfolio_pin, weight_sum_limit, leverage, fixed_income_weight)
        short_weights = get_portfolio_weights(short_portfolio_pin, fixed_income_weight, leverage=False,
                                              fixed_income_weight=0)
        longonly_weights = get_portfolio_weights(long_portfolio_pin, weight_sum_limit=1, leverage=False,
                                                 fixed_income_weight=0)
        portfolios = {
            'pins': {
                'long': long_portfolio_pin,
                'short': short_portfolio_pin,
            },
            'weights': {
                'long': long_weights,
                'short': short_weights,
                'longonly': longonly_weights,
            }
        }
    return portfolios


def get_pins(pin_model, eligible_stocks, date):
    """
    Busca as PINs das ações elegíveis para uma determinada data
    :param pin_model: resultados do modelo PIN executado previamente
    :param eligible_stocks: dataframe binário com ações elegíveis
    :param date: data de referência
    :return: Dataframe de PINs e outros estimadores (como delta)
    """
    eligible_stocks_on_date = eligible_stocks.loc[date]
    stocks = eligible_stocks_on_date[eligible_stocks_on_date].index
    pins = get_pins_per_date(pin_model, date)
    pins = pins[pins['symbol'].isin(stocks)].copy()
    return pins


def get_pins_per_date(pin_model, date):
    """
    Seleciona valor da PIN de referência para uma data
    :param pin_model: resultados do modelo PIN executado previamente
    :param date: data de referência
    :return: Dataframe de PINs e outros estimadores (como delta)
    """
    date_found = False
    first_date = pin_model['period'].min()
    pin_on_date = None
    while not date_found and date >= first_date:
        pin_on_date = pin_model[pin_model['period'] == date]
        if pin_on_date.shape[0] > 0:
            date_found = True
        else:
            date = date - dt.timedelta(days=1)
    return pin_on_date


def select_asset_by_delta(pins, q):
    """
    Seleciona ativos com deltas fora do intervalo [inferior, superior] definido pelos quantis q e 1-q
    :param pins: resultados do modelo PIN para uma data específica
    :param q: quantil
    :return: ativos selecionados para portfolios long e short
    """
    delta_inf = np.quantile(pins['delta'], q=1 - q)
    delta_sup = np.quantile(pins['delta'], q=q)
    long = pins[pins['delta'] > delta_sup].copy()
    short = pins[pins['delta'] < delta_inf].copy()

    return long, short


def select_asset_by_pin(pins, q):
    """

    Seleciona ativos com PIN acima do definido pelo quantil q
    :param pins: resultados do modelo PIN para uma data específica
    :param q: quantil
    :return: ativos selecionados
    """
    lim = np.quantile(pins['pin'], q=q)
    result = pins[pins['pin'] > lim].copy()
    return result


def get_unique_dates(dates):
    """
    Retira duplicatas da coleção
    :param dates: coleção de datas
    :return: lista de datas ordenadas e sem repetição
    """
    unique_dates = list(set(dates))
    unique_dates.sort()
    return unique_dates


def get_portfolio_weights(portfolio, weight_sum_limit=1, leverage=True, fixed_income_weight=1):
    """
    Calcula pesos para os Portfólios
    :param portfolio: Dicionário de ações selecionadas
    :param weight_sum_limit: Limite máximo de peso do portfólio sem alavancagem
    :param leverage: Flag de alavancagem
    :param fixed_income_weight: Peso alocado na SELIC
    :return:
    """
    portfolio_weights = dict()
    port_per_period = portfolio.groupby('period')
    for period in port_per_period.groups.keys():
        p = port_per_period.get_group(period)
        weights = get_weights(p, weight_sum_limit=weight_sum_limit)
        if leverage:
            weights['SELIC'] = fixed_income_weight
        portfolio_weights[period] = weights
    return portfolio_weights


def get_weights(portfolio, method='equal', weight_sum_limit=1):
    """
    Calcula pesos para 1 única data. Atualmente, os pesos são distribuídos com o método igualitário.
    :param portfolio: Ações selecionadas para o portfólio
    :param method: Método de distribuição de pesos. Por enquanto, apenas igualitário.
    :param weight_sum_limit: Peso máximo do portólio
    :return:
    """
    weights = dict()
    n = portfolio.shape[0]
    if method == 'equal':
        weights = {
            stock: 1 / n * weight_sum_limit
            for stock in portfolio['symbol']
        }
    return weights
