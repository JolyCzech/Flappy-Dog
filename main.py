import pygame
import random

from objects import Dog, Obstacle, Scoreboard, Terrain


def load_image(path, scale=None):
    """
    Загружает изображение по указанному пути с обработкой исключений.

    :param path: Строка, путь к изображению.
    :param scale: Кортеж (ширина, высота) для масштабирования изображения (опционально).
    :return: Объект pygame.Surface с изображением или заглушка при ошибке.
    """
    try:
        image = pygame.image.load(path)
        if scale:
            image = pygame.transform.scale(image, scale)
        return image
    except Exception as e:
        print(f"Ошибка загрузки изображения '{path}': {e}")
        default_size = scale if scale else (50, 50)
        image = pygame.Surface(default_size)
        image.fill((255, 0, 255))
        return image


def load_sound(path):
    """
    Загружает звуковой файл по указанному пути с обработкой исключений.

    :param path: Строка, путь к звуковому файлу.
    :return: Объект pygame.mixer.Sound или None при ошибке.
    """
    try:
        sound = pygame.mixer.Sound(path)
        return sound
    except Exception as e:
        print(f"Ошибка загрузки звука '{path}': {e}")
        return None


# Инициализация Pygame
pygame.init()
SCREEN = SCREEN_WIDTH, SCREEN_HEIGHT = 288, 512
display_surface_height = 0.80 * SCREEN_HEIGHT
info_screen = pygame.display.Info()

screen_width = info_screen.current_w
screen_height = info_screen.current_h

# Настройка окна в зависимости от разрешения экрана
if screen_width >= screen_height:
    display_window = pygame.display.set_mode(SCREEN, pygame.NOFRAME)
else:
    display_window = pygame.display.set_mode(SCREEN, pygame.NOFRAME | pygame.SCALED | pygame.FULLSCREEN)

frame_clock = pygame.time.Clock()
MAX_FPS = 60

# Определение основных цветов
COLOR_RED = (255, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# Загрузка фоновых изображений с обработкой ошибок
background_day = load_image('Assets/background-day.png')
background_night = load_image('Assets/background-night.png')
background_image = random.choice([background_day, background_night])

# Загрузка изображений препятствий
obstacle_images = [
    load_image('Assets/obstacle-green.png'),
    load_image('Assets/obstacle-red.png')
]
selected_obstacle_image = random.choice(obstacle_images)

# Загрузка изображений для экрана Game Over и стартового логотипа
game_over_image = load_image('Assets/gameover.png')
start_logo = load_image('Assets/start.png', scale=(200, 180))

# Загрузка звуковых эффектов
die_sound = load_sound('Sounds/die.wav')
hit_sound = load_sound('Sounds/hit.wav')
score_sound = load_sound('Sounds/point.wav')
swoosh_sound = load_sound('Sounds/swoosh.wav')
wing_sound = load_sound('Sounds/wing.wav')

# Инициализация игровых объектов
obstacle_collection = pygame.sprite.Group()
terrain_ground = Terrain(display_window)
score_display = Scoreboard(SCREEN_WIDTH // 2, 50, display_window)
dog_pet = Dog(display_window)

# Инициализация игровых переменных
ground_level = 0.80 * SCREEN_HEIGHT
game_speed = 0
game_has_started = False
game_is_over = False
game_restart = False
current_score = 0
initial_screen = True
obstacle_crossed = False
obstacle_spawn_rate = 1600

# Инициализация переменной для отслеживания времени появления препятствий
last_obstacle_spawn = pygame.time.get_ticks() - obstacle_spawn_rate

# Основной игровой цикл
game_running = True
while game_running:
    # Отрисовка выбранного фонового изображения
    display_window.blit(background_image, (0, 0))

    if initial_screen:
        # Если игра на стартовом экране, останавливаем движение
        game_speed = 0
        dog_pet.draw_flap()
        terrain_ground.update(game_speed)
        display_window.blit(start_logo, (50, 20))
    else:
        # Основной игровой процесс, если игра запущена
        if game_has_started and not game_is_over:
            upcoming_obstacle = pygame.time.get_ticks()
            # Проверка, пора ли создавать новое препятствие
            if upcoming_obstacle - last_obstacle_spawn >= obstacle_spawn_rate:
                obstacle_height = display_surface_height // 2
                obstacle_position_offset = random.choice(range(-100, 100, 4))
                total_height = obstacle_height + obstacle_position_offset

                top_obstacle = Obstacle(display_window, selected_obstacle_image, total_height, 1)
                bottom_obstacle = Obstacle(display_window, selected_obstacle_image, total_height, -1)
                obstacle_collection.add(top_obstacle)
                obstacle_collection.add(bottom_obstacle)
                last_obstacle_spawn = upcoming_obstacle

        # Обновление объектов игры
        obstacle_collection.update(game_speed)
        terrain_ground.update(game_speed)
        dog_pet.update()
        score_display.update(current_score)

        # Проверка столкновений между собакой и препятствиями или верхней границей экрана
        if pygame.sprite.spritecollide(dog_pet, obstacle_collection, False) or dog_pet.rect.top <= 0:
            game_has_started = False
            if dog_pet.is_alive:
                if hit_sound:
                    hit_sound.play()
                if die_sound:
                    die_sound.play()
            dog_pet.is_alive = False
            # Изменяем угол поворота собаки после столкновения
            dog_pet.theta = dog_pet.velocity * -2

        # Если собака ударяется о землю, игра заканчивается
        if dog_pet.rect.bottom >= display_surface_height:
            game_speed = 0
            game_is_over = True

        # Обновление счета, если собака успешно пролетела между препятствиями
        if len(obstacle_collection) > 0:
            current_obstacle = obstacle_collection.sprites()[0]
            if (dog_pet.rect.left > current_obstacle.rect.left and
                    dog_pet.rect.right < current_obstacle.rect.right and
                    not obstacle_crossed and
                    dog_pet.is_alive):
                obstacle_crossed = True

            if obstacle_crossed:
                if dog_pet.rect.left > current_obstacle.rect.right:
                    obstacle_crossed = False
                    current_score += 1
                    if score_sound:
                        score_sound.play()

    # Если собака мертва, отображаем экран Game Over
    if not dog_pet.is_alive:
        display_window.blit(game_over_image, (50, 200))

    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                game_running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            # При нажатии мыши на стартовом экране запускаем игру
            if initial_screen:
                game_has_started = True
                game_speed = 2
                initial_screen = False

                game_is_over = False
                last_obstacle_spawn = pygame.time.get_ticks() - obstacle_spawn_rate
                # Очищаем коллекцию препятствий
                obstacle_collection.empty()

                game_speed = 2
                current_score = 0

            # Если игра завершена, перезапускаем её
            if game_is_over:
                initial_screen = True
                dog_pet = Dog(display_window)
                selected_obstacle_image = random.choice(obstacle_images)
                background_image = random.choice([background_day, background_night])

    frame_clock.tick(MAX_FPS)
    pygame.display.update()

pygame.quit()
