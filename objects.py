import pygame
import random

# Константы экрана
SCREEN = WIDTH, HEIGHT = 288, 512
display_height = 0.80 * HEIGHT

# Инициализация микшера для звуков
pygame.mixer.init()


def load_image(path, scale=None):
    """
    Загружает изображение по указанному пути с обработкой исключений.

    :param path: Путь к изображению.
    :param scale: Кортеж (ширина, высота) для масштабирования изображения (необязательно).
    :return: Загруженное изображение или Surface-заглушка при ошибке.
    """
    try:
        image = pygame.image.load(path)
        if scale:
            image = pygame.transform.scale(image, scale)
        return image
    except Exception as e:
        print(f"Ошибка загрузки изображения '{path}': {e}")
        # Возвращаем Surface-заглушку (магенту)
        size = scale if scale else (50, 50)
        image = pygame.Surface(size)
        image.fill((255, 0, 255))
        return image


def load_sound(path):
    """
    Загружает звуковой файл по указанному пути с обработкой исключений.

    :param path: Путь к звуковому файлу.
    :return: Загруженный звук или None при ошибке.
    """
    try:
        sound = pygame.mixer.Sound(path)
        return sound
    except Exception as e:
        print(f"Ошибка загрузки звука '{path}': {e}")
        return None


# Загрузка звука взмаха крыла
flap_sound = load_sound('Sounds/wing.wav')


class Dog:
    """
    Класс, представляющий собаку в игре.

    Отвечает за анимацию, физику (гравитация, прыжок) и отрисовку собаки.
    """

    def __init__(self, window):
        """
        Инициализация объекта Dog.

        :param window: Окно, в котором будет отрисовываться собака.
        """
        self.window = window
        self.image_list = []
        # Загрузка изображений собаки с обработкой ошибок
        for i in range(2, 12):
            img = load_image(f'Assets/Dog/d{i}.png', (44, 28))
            self.image_list.append(img)
        self.reset()

    def update(self):
        """
        Обновляет состояние собаки:
          - Применяет гравитацию.
          - Обрабатывает прыжок при нажатии мыши.
          - Анимирует крылья и поворот изображения.
          - Отрисовывает собаку.
        """
        # Гравитация
        self.velocity += 0.3
        if self.velocity >= 8:
            self.velocity = 8
        if self.rect.bottom <= display_height:
            self.rect.y += int(self.velocity)

        if self.is_alive:
            # Прыжок по нажатию кнопки мыши
            if pygame.mouse.get_pressed()[0] == 1 and not self.has_jumped:
                if flap_sound:
                    flap_sound.play()
                self.has_jumped = True
                self.velocity = -6
            if pygame.mouse.get_pressed()[0] == 0:
                self.has_jumped = False

            self.animate_wing()
            # Вращение изображения в зависимости от скорости
            self.image = pygame.transform.rotate(self.image_list[self.image_index], self.velocity * -2)
        else:
            # При смерти — постепенное вращение
            if self.rect.bottom <= display_height:
                self.rotation_angle -= 2
            self.image = pygame.transform.rotate(self.image_list[self.image_index], self.rotation_angle)

        self.window.blit(self.image, self.rect)

    def animate_wing(self):
        """
        Обновляет счетчик анимации для смены кадров полёта.
        """
        self.animation_counter += 1
        if self.animation_counter > 5:
            self.animation_counter = 0
            self.image_index += 1
        if self.image_index >= 10:
            self.image_index = 0

    def draw_flap(self):
        """
        Отображает собаку с эффектом «подёргивания» (flap) до начала игры.
        """
        self.animate_wing()
        if self.flap_position <= -10 or self.flap_position > 10:
            self.flap_increment *= -1
        self.flap_position += self.flap_increment
        self.rect.y += self.flap_increment
        self.rect.x = WIDTH // 2 - 20
        self.image = self.image_list[self.image_index]
        self.window.blit(self.image, self.rect)

    def reset(self):
        """
        Сбрасывает параметры собаки в исходное состояние.
        """
        self.image_index = 0
        self.image = self.image_list[self.image_index]
        self.rect = self.image.get_rect()
        self.rect.x = 60
        self.rect.y = int(display_height) // 2
        self.animation_counter = 0
        self.velocity = 0
        self.has_jumped = False
        self.is_alive = True
        self.rotation_angle = 0
        self.mid_position = display_height // 2
        self.flap_position = 0
        self.flap_increment = 1


class Terrain:
    """
    Класс, отвечающий за отрисовку и движение грунта.
    """

    def __init__(self, window):
        """
        Инициализация объекта Terrain.

        :param window: Окно, в котором будет отрисовываться грунт.
        """
        self.window = window
        self.image1 = load_image('Assets/terrain.png')
        self.image2 = self.image1
        self.rect1 = self.image1.get_rect()
        self.rect1.x = 0
        self.rect1.y = int(display_height)
        self.rect2 = self.image2.get_rect()
        self.rect2.x = WIDTH
        self.rect2.y = int(display_height)

    def update(self, speed):
        """
        Обновляет положение грунта в зависимости от скорости.

        :param speed: Скорость перемещения грунта.
        """
        self.rect1.x -= speed
        self.rect2.x -= speed

        if self.rect1.right <= 0:
            self.rect1.x = WIDTH - 5
        if self.rect2.right <= 0:
            self.rect2.x = WIDTH - 5

        self.window.blit(self.image1, self.rect1)
        self.window.blit(self.image2, self.rect2)


class Obstacle(pygame.sprite.Sprite):
    """
    Класс, представляющий препятствие в игре.

    Наследуется от pygame.sprite.Sprite для удобного управления группой спрайтов.
    """

    def __init__(self, window, image, y, position):
        """
        Инициализация препятствия.

        :param window: Окно для отрисовки.
        :param image: Изображение препятствия.
        :param y: Координата Y для позиционирования.
        :param position: Позиция препятствия (1 для верхнего, -1 для нижнего).
        """
        super(Obstacle, self).__init__()
        self.window = window
        self.image = image
        self.rect = self.image.get_rect()
        obstacle_gap = 100 // 2
        x = WIDTH

        if position == 1:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect.bottomleft = (x, y - obstacle_gap)
        elif position == -1:
            self.rect.topleft = (x, y + obstacle_gap)

    def update(self, speed):
        """
        Обновляет положение препятствия и удаляет его, если оно вышло за экран.

        :param speed: Скорость движения препятствия.
        """
        self.rect.x -= speed
        if self.rect.right < 0:
            self.kill()
        self.window.blit(self.image, self.rect)


class Scoreboard:
    """
    Класс для отображения счета игры.
    """

    def __init__(self, x, y, window):
        """
        Инициализация Scoreboard.

        :param x: Координата X для отображения счета.
        :param y: Координата Y для отображения счета.
        :param window: Окно, в котором будет отображаться счет.
        """
        self.digits = []
        # Загрузка изображений для цифр
        for digit in range(10):
            img = load_image(f'Assets/Score/{digit}.png')
            self.digits.append(img)
        self.x = x
        self.y = y
        self.window = window

    def update(self, score):
        """
        Обновляет и отображает текущий счет.

        :param score: Текущее значение счета.
        """
        score_str = str(score)
        for index, num in enumerate(score_str):
            image = self.digits[int(num)]
            rect = image.get_rect()
            rect.topleft = (self.x - 15 * len(score_str) + 30 * index, self.y)
            self.window.blit(image, rect)
