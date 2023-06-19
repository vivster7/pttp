def a():
    for i in range(10):
        b()


def b():
    for i in range(10):
        c()


def c():
    for i in range(10):
        d()


def d():
    pass


if __name__ == '__main__':
    a()
