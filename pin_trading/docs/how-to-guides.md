This part of the project documentation focuses on a
**problem-oriented** approach. You'll tackle common
tasks that you might have, with the help of the code
provided in this project.

## How To Add Two Numbers?

You have two numbers and you need to add them together.
You're in luck! The `calculator` package can help you
get this done.

Download the code from this GitHub repository and place
the `modules/` folder in the same directory as your
Python script:

    pin_trading/
    │
    ├── modules/
    │   ├── __init__.py
    │   ├── dataset.py
    │   ├── pin_estimation.py
    │   ├── portfolio_build.py
    │   ├── returns.py
    │   └── stock_selection.py
    │
    └── strategy_simulator.py

Inside of `strategy_simulator.py` you can now import the
`add()` function from the `calculator.calculations`
module:

    # strategy_simulator.py
    from calculator.calculations import add

After you've imported the function, you can use it to add any two numbers that you need
to add:

    # strategy_simulator.py
    from calculator.calculations import add

    print(add(20, 22))  # OUTPUT: 42.0

You're now able to add any two numbers, and you'll always get a `float` as a result.
