import _data
import pin_estimation
import stock_selection
import portfolio_build
import returns


def portfolio_workflow():
    '''
    Executa o passo a passo para a construção do portfolio.
    OBS.: Workflow da PIN deve ter sido previamente executado
    :return:
    '''
    data = _data.load_all_data()
    eligible_stocks = stock_selection.filter(data['volumes'])
    portfolios = portfolio_build.portfolio_build(
        data['pin_results'],
        eligible_stocks,
    )
    r = returns.calculate_all_portfolios_returns(portfolios['weights'], data['closing_prices'])

    _data.save_data({'returns': r})
    _data.save_data(portfolios['pins'], path='./data/results/pins')
    _data.save_data(portfolios['weights'], path='./data/results/weights')
    _data.save_data({'eligible_stocks': eligible_stocks})


def pin_workflow():
    '''
    Executa o passo-a-passo para as estimativas das PINs
    :return:
    '''
    estimations = pin_estimation.estimate_all_pins()
    _data.save_data({'pin_results.csv': estimations}, path='./data/results/pins')


def complete_workflow():
    '''
    Executa toda a operação: estimativa das PINs e construção de portfólios
    :return:
    '''
    pin_workflow()
    portfolio_workflow()


def workflow_selection(workflow='complete'):
    '''
    Seleciona o workflow a ser seguido
    :param workflow: nome do workflow
    :return:
    '''
    if workflow == 'portfolio':
        portfolio_workflow()
    elif workflow == 'pin':
        pin_workflow()
    else:
        complete_workflow()


if __name__ == '__main__':
    workflow_selection()
