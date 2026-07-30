import pygame

from audio import Audio
from crt import ShaderEffectDisplay
from pet import Pet
from save import load_pet, save_exists, save_pet
from screens import (
    DeathScreen,
    MainScreen,
    MiniGameScreen,
    ScreenAction,
    StartupScreen,
    StoreScreen,
)
from settings import (
    AUTOSAVE_INTERVAL,
    BYPASS,
    FPS,
    HEIGHT,
    SAVE_PATH,
    VIRTUAL_HEIGHT,
    VIRTUAL_WIDTH,
    WIDTH,
)


class Game:
    """Run the application and switch between its screens."""

    def __init__(self):
        pygame.mixer.pre_init(
            frequency=44100,
            size=-16,
            channels=2,
            buffer=512,
        )
        pygame.init()

        self.audio = Audio()
        self.audio.start_music()
        self.display = ShaderEffectDisplay(
            window_size=(WIDTH, HEIGHT),
            surface_size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
            caption="Tamagotchi",
            bypass=BYPASS,
        )
        self.clock = pygame.time.Clock()
        self.pet = None
        self.autosave_timer = 0
        self.main_screen = None
        self.store_screen = None
        self.mini_game_screen = None
        self.death_screen = None
        self.active_screen = StartupScreen(
            self.display,
            self.audio,
            save_available=save_exists(SAVE_PATH),
        )
        self.running = True

    def run(self):
        try:
            while self.running:
                dt = self.clock.tick(FPS) / 1000
                self.handle_events()

                if self.running and self.pet is not None:
                    self.update_pet(dt)

                self.handle_action(self.active_screen.update(dt))
                self.active_screen.draw(self.display.surface)
                self.display.present()
        finally:
            self.close()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            self.handle_action(self.active_screen.handle_event(event))

    def handle_action(self, action):
        if action is None:
            return

        if action is ScreenAction.START_FRESH:
            self.start_game(Pet())

        elif action is ScreenAction.CONTINUE:
            try:
                self.start_game(load_pet(SAVE_PATH))
            except ValueError:
                self.active_screen.show_save_error()
                self.audio.play("denied")

        elif action is ScreenAction.OPEN_STORE:
            self.active_screen = self.store_screen

        elif action is ScreenAction.OPEN_MINI_GAME:
            self.active_screen = self.mini_game_screen

        elif action is ScreenAction.RETURN_TO_MAIN:
            self.active_screen = self.main_screen

        elif action is ScreenAction.QUIT:
            self.running = False

    def start_game(self, pet):
        self.pet = pet
        self.autosave_timer = 0
        self.main_screen = MainScreen(self.display, pet, self.audio)
        self.store_screen = StoreScreen(self.display, pet, self.audio)
        self.mini_game_screen = MiniGameScreen(self.display, pet, self.audio)
        self.death_screen = DeathScreen(self.display, pet, self.audio)
        self.active_screen = (
            self.death_screen if pet.dead else self.main_screen
        )

    def update_pet(self, dt):
        """Advance pet state independently of the currently visible screen."""
        was_dead = self.pet.dead
        self.pet.update_age(dt)
        woke_up = self.pet.update(dt)
        self.main_screen.record_pet_update(woke_up)

        if not was_dead and self.pet.dead:
            self.audio.play("death")
            self.active_screen = self.death_screen

        self.update_autosave(dt)

    def update_autosave(self, dt):
        if self.pet is None:
            return

        self.autosave_timer += max(0, dt)
        if self.autosave_timer < AUTOSAVE_INTERVAL:
            return

        save_pet(SAVE_PATH, self.pet)
        self.autosave_timer %= AUTOSAVE_INTERVAL

    def close(self):
        try:
            if self.pet is not None:
                save_pet(SAVE_PATH, self.pet)
        finally:
            self.audio.close()
            self.display.close()
            pygame.quit()
