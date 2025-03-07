import itertools

__dot = ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"]
dot_clockwise = itertools.cycle(reversed(__dot))
dot_counter_clockwise = itertools.cycle(__dot)

__snake = ["⣆", "⡇", "⠏", "⠛", "⠹", "⢸", "⣰", "⣤"]
snake_clockwise = itertools.cycle(__snake)
snake_counter_clockwise = itertools.cycle(reversed(__snake))
