# Импорт функции randint для генерации координат для
# расположения кораблей, а также для хода компьютера
from random import randint, choice

# Определение класса точек на поле Dot
class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    # Сравнение точек по их координатам
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    # Отображение точек в виде строк
    # def __repr__(self):
    #     return f'Dot({self.x}, {self.y})'

# Определение класса Ship — корабль на игровом поле
class Ship:
    def __init__(self, bow, length, orientation):
        self.bow = bow
        self.length = length
        self.orientation = orientation
        self.lives = length

    # Свойство, возвращающее список точек, занимаемых кораблем
    @property
    def dots(self):
        ship_dots = []
        for i in range(self.length):
            cur_x = self.bow.x
            cur_y = self.bow.y
            if self.orientation == 0:
                cur_x += i
            elif self.orientation == 1:
                cur_y += i
            ship_dots.append(Dot(cur_x, cur_y))
        return ship_dots

    # Проверка того, был ли корабль подбит по заданной точке
    def shooten(self, shot):
        return shot in self.dots

# Определение класса исключения для доски Board
class BoardException(Exception):
    pass

# Исключение для ошибки выстрела за доску
class BoardOutException(BoardException):
    def __str__(self):
        return 'Выстрел за доску!'

# Исключение для ошибки повторного выстрела в ту же клетку
class BoardUsedException(BoardException):
    def __str__(self):
        return 'Вы уже стреляли в эту клетку!'

# Исключение для ошибки расположения корабля на доске
class BoardWrongShipException(BoardException):
    pass

# Определение класса Board — игровая доска
class Board:
    def __init__(self, size=6, hidden=False):
        self.size = size
        self.hidden = hidden
        self.count = 0

        self.field = [['O'] * size for _ in range(size)]
        self.busy = []
        self.ships = []

    # Вывод доски в виде строки для отображения
    def __str__(self):
        res = ''
        res += '  | ' + ' | '.join([str(i) for i in range(1, self.size + 1)]) + ' | \n'
        for i, row in enumerate(self.field):
            res += f"{i + 1} | " + ' | '.join(row) + ' | \n'
        if self.hidden:
            res = res.replace('■', 'O')
        return res

    # Проверка выхода точки за пределы доски
    def out(self, dot):
        return not ((0 <= dot.x < self.size) and (0 <= dot.y < self.size))

    # Обвод коробля по контуру
    def contour(self, ship, verb=False):
        near = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]

        for dot in ship.dots:
            for dx, dy in near:
                cur = Dot(dot.x + dx, dot.y + dy)
                if not self.out(cur) and cur not in self.busy:
                    if verb:
                        self.field[cur.x][cur.y] = '.'
                    self.busy.append(cur)

    # Добавление корабля на доску
    def add_ship(self, ship):
        for dot in ship.dots:
            if self.out(dot) or dot in self.busy:
                raise BoardWrongShipException()
        for dot in ship.dots:
            self.field[dot.x][dot.y] = '■'
            self.busy.append(dot)

        self.ships.append(ship)
        self.contour(ship)

    # Обработка выстрела по заданной точке на доске
    def shot(self, dot):
        if self.out(dot):
            raise BoardOutException()

        if dot in self.busy:
            raise BoardUsedException()

        self.busy.append(dot)

        for ship in self.ships:
            if ship.shooten(dot):
                ship.lives -= 1
                self.field[dot.x][dot.y] = 'X'
                if ship.lives == 0:
                    self.count += 1
                    self.contour(ship, verb=True)
                    print('Корабль уничтожен!')
                    return False
                else:
                    print('Корабль ранен!')
                    return True

        self.field[dot.x][dot.y] = '.'
        print('Мимо!')
        return False

    # Очистка выстрелов для начала новой игры
    def begin(self):
        self.busy = []

    # Проверка на победу
    def defeat(self):
        return self.count == len(self.ships)

# Определение класса Player — класс игрока, родительский для классов AI и User
class Player:
    def __init__(self, board, enemy):
        self.board = board
        self.enemy = enemy

    # Метод ask должен быть определен в наследниках
    def ask(self):
        raise NotImplementedError()

    # Осуществление хода игрока или компьютера
    def move(self):
        while True:
            try:
                target = self.ask()
                repeat = self.enemy.shot(target)
                return repeat
            except BoardException as e:
                print(e)

class AI(Player):
    def __init__(self, board, enemy):
        super().__init__(board, enemy)
        self.last_target = None  # Последняя цель выстрела

    # Генерация случайных координат для хода компьютера
    def ask(self):
        if self.last_target is None:
            # Если у AI нет раненых кораблей, генерируются случайные координаты
            d = self.get_random_target()
        else:
            # Иначе производится выстрел в соседние клетки от последней раненой точки
            d = self.get_next_target()

        # Проверка на то, что точка ещё не была использована для выстрела
        if d not in self.enemy.busy:
            print(f'Ход компьютера: {d.x + 1} {d.y + 1}')
            return d

    def get_random_target(self):
        available_dots = [
            Dot(x, y) for x in range(self.board.size) for y in range(self.board.size)
            if Dot(x, y) not in self.enemy.busy
        ]
        return choice(available_dots)

    def get_next_target(self):
        # Получение списка соседних точек от последней раненой точки
        neighbors = [
            Dot(self.last_target.x + dx, self.last_target.y + dy)
            for dx in range(-1, 2)
            for dy in range(-1, 2)
            if dx != 0 or dy != 0
        ]

        # Выбор только тех точек, которые не выходят за границы поля и еще не были использованы
        available_neighbors = [
            neighbor for neighbor in neighbors
            if not self.board.out(neighbor) and neighbor not in self.enemy.busy
        ]

        if available_neighbors:
            # Если есть доступные соседние точки, идёт выбор одой из них
            return choice(available_neighbors)
        else:
            # Если доступных соседних точек нет, идёт возвращение случайных координат
            return Dot(randint(0, 5), randint(0, 5))

class User(Player):
    # Запрос у пользователя координат хода
    def ask(self):
        while True:
            coords = input('Ваш ход: ').split()
            if len(coords) != 2:
                print('Введите 2 координаты через пробел!')
                continue

            x, y = coords
            if not (x.isdigit()) or not (y.isdigit()):
                print('Введите числа!')
                continue

            x, y = int(x), int(y)
            return Dot(x - 1, y - 1)

# Определение основного класса игры
class Game:
    def __init__(self):
        self.lens = [3, 2, 2, 1, 1, 1, 1]
        self.size = 6
        ai = self.random_board()
        ai.hidden = True
        user = self.random_board()

        self.ai = AI(ai, user)
        self.user = User(user, ai)

    def try_board(self):
        board = Board(size=self.size)
        attempts = 0
        for l in self.lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = Ship(Dot(randint(0, self.size), randint(0, self.size)), l, randint(0, 1))
                try:
                    board.add_ship(ship)
                    break
                except BoardWrongShipException:
                    pass
        board.begin()
        return board

    # Генерация случайного расположения кораблей на досках
    def random_board(self):
        board = None
        while board is None:
            board = self.try_board()
        return board

    # Приветствие игрока
    def greet(self):
        print('-'*62)
        print('-'*19+'Добро пожаловать в игру'+'-'*20)
        print('-'*22+'<< Морской бой! >>'+'-'*22)
        print('-'*62)
        print('Формат ввода: x y')
        print('x - номер строки, y - номер столбца')

    @staticmethod
    def format_board_line(line, width):
        return line + ' ' * (width - len(line))

    def print_board(self):
        # Вывод досок игрока и компьютера на экран
        user_board_lines = str(self.user.board).split('\n')
        ai_board_lines = str(self.ai.board).split('\n')

        # Выравнивание количества строк в досках
        max_lines = max(len(user_board_lines), len(ai_board_lines))
        user_board_lines.extend([' ' * len(line) for line in range(len(user_board_lines), max_lines)])
        ai_board_lines.extend([' ' * len(line) for line in range(len(ai_board_lines), max_lines)])

        # Максимальная длина строк для выравнивания
        max_line_length = max(len(line) for line in user_board_lines + ai_board_lines)

        # Объединение строк досок вместе и их вывод
        print('-' * (max_line_length * 2 + 6))
        print('   Доска игрока:               |      Доска компьютера:')
        print('-' * (max_line_length * 2 + 6))
        for user_line, ai_line in zip(user_board_lines, ai_board_lines):
            formatted_user_line = self.format_board_line(user_line, max_line_length)
            formatted_ai_line = self.format_board_line(ai_line, max_line_length)
            print(f'{formatted_user_line}   |   {formatted_ai_line}')
        print('-' * (max_line_length * 2 + 6))

    # Реализация основного игрового цикла
    def loop(self):
        num = 0
        while True:
            self.print_board()
            if num % 2 == 0:
                print('-'*62)
                print('Ходит игрок!')
                repeat = self.user.move()
            else:
                print('-'*62)
                print('Ходит компьютер!')
                repeat = self.ai.move()
            if repeat:
                num -= 1

            if self.ai.board.defeat():
                self.print_board()
                print('-'*62)
                print('Игрок победил!')
                break

            if self.user.board.defeat():
                self.print_board()
                print('-'*62)
                print('Компьютер победил!')
                break

            num += 1

    # Запуск игрового цикла
    def start(self):
        self.greet()
        self.loop()

# Создание объекта игры и запуск игры
if __name__ == '__main__':
    game = Game()
    game.start()