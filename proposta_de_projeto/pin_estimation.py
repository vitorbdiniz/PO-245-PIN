import math
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar
from scipy.stats import poisson

import warnings

warnings.filterwarnings('ignore')

all_likelihoods = list()
iteration_likelihood = None


def poisson_likelihood(params, buyers, sellers):
    '''
    Calcula o likelihood para a função descrita por Easley & O'Hara (1996)
    :param params: θ = (alpha, mu, delta, eps_b, eps_s)
    :param buyers: série de fluxo de compra
    :param sellers: série de fluxo de venda
    :return: valor do likelihood invertido
    '''

    log_probability_mass_function = poisson.logpmf
    probability_mass_function = poisson.pmf
    (alpha, mu, delta, eps_b, eps_s) = params

    # Poisson sem ocorrência de evento informacional (Pn)
    Pn_buy = probability_mass_function(buyers, eps_b)
    Pn_sell = probability_mass_function(sellers, eps_s)
    P_nothing = (1 - alpha) * Pn_buy * Pn_sell

    # Poisson com ocorrência de evento informacional de sinal positivo (P_plus)
    P_plus_buy = probability_mass_function(buyers, eps_b + mu)
    P_plus = alpha * delta * P_plus_buy * Pn_sell

    # Poisson com ocorrência de evento informacional de sinal negativo (P_minus)
    P_minus_sell = probability_mass_function(sellers, eps_s + mu)
    P_minus = alpha * (1 - delta) * Pn_buy * P_minus_sell
    likelihood = -np.sum(P_nothing + P_plus + P_minus)

    global iteration_likelihood
    iteration_likelihood = {
        'alpha': alpha,
        'mu': mu,
        'delta': delta,
        'eps_b': eps_b,
        'eps_s': eps_s,
        'likelihood': likelihood
    }
    return likelihood


def estimate_params(data, iterations=10):
    '''
    Estima parâmetros da PIN:
        alpha = probabilidade de evento informacional
        delta = probabilidade condicional de evento com sinal positivo
        mu = fluxo de agentes informados
        eps_s = fluxo de venda de agentes desinformados
        eps_b = fluxo de compra de agentes desinformados

    :param data:
    :param iterations:
    :return:
    '''
    avg = data['comprador'].mean()
    bounds = (
        (0, 1),
        (None, None),
        (0, 1),
        (None, None),
        (None, None),
    )

    while iterations > 0:
        iterations -= 1
        initial_params = [np.random.rand(), avg * np.random.rand(), np.random.rand(), avg * np.random.rand(),
                          avg * np.random.rand()]

        results = minimize(poisson_likelihood, initial_params,
                           args=(data['comprador'].values, data['vendedor'].values),
                           bounds=bounds)
        all_likelihoods.append(iteration_likelihood)
    params = get_highest_likelihood_params()
    return params


def get_highest_likelihood_params():
    '''
    Compara todos os max-likelihoods calculados e seleciona os parametros com maior max-likelihood
    :return:
    '''
    global all_likelihoods
    result_params = {'likelihood': -np.inf}
    for params in all_likelihoods:
        if params['likelihood'] > result_params['likelihood']:
            result_params = params
    result_params.pop('likelihood')
    all_likelihoods = list()
    return result_params


def pin_equation(params):
    '''
    Cálculo da PIN segundo Easley & O'Hara (1996)
    :param params:
    :return:
    '''
    α = params['alpha']
    µ = params['mu']
    εb = params['eps_b']
    εs = params['eps_s']

    return (α * µ) / (α * µ + εb + εs)


def rolling_pin(data, window=60):
    '''
    Calcula PIN para uma janela móvel de um ativo
    :param data:
    :param window:
    :return:
    '''
    data.sort_index(inplace=True)
    results = list()
    for i in range(window, data.shape[0]):
        params = {
            'symbol': data['symbol'].iloc[i],
            'period': data['bucket'].iloc[i],
        }
        frame = data.iloc[i:window + i]
        estimated_params = estimate_params(frame)
        try:
            params['pin'] = pin_equation(estimated_params)
        except KeyError:
            continue
        params.update(estimated_params)
        results.append(params)
    return pd.DataFrame(results)


def estimate_all_pins(path='./data/data_cedro', window=60):
    '''
    Calcula PIN em janelas móveis para todos os ativos
    :param path:
    :param window:
    :return:
    '''
    params = pd.DataFrame()
    for file in os.listdir(path):
        print(file)
        if file.endswith('.csv'):
            data = pd.read_csv(f'{path}/{file}', index_col=0)
            data.sort_values(by='bucket', inplace=True)
            params = pd.concat([params, rolling_pin(data, window)], ignore_index=True)
    return params
