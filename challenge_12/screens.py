import random
from enum import Enum, auto

import pygame

from settings import (
    CRITICAL_TEXT_COLOR,
    FONT_PATH,
    HUD_FONT_SIZE,
    HUD_TEXT_COLOR,
    MOOD_MESSAGES,
    PET_NAME_MAX_LENGTH,
    PERSONALITY_MOOD_MESSAGES,
    RPS_BEATS,
    RPS_CHOICES,
    RPS_DRAW_REWARD,
    RPS_WIN_REWARD,
    STORE_ITEMS,
    VIRTUAL_WIDTH,
)
from ui import TextButton
from view import MainView


def draw_centered(surface, font, message, y, color=HUD_TEXT_COLOR):
    text = font.render(message, False, color)
    surface.blit(text, text.get_rect(midtop=(VIRTUAL_WIDTH // 2, y)))


def mouse_state(display):
    return (
        display.screen_to_surface(pygame.mouse.get_pos()),
        pygame.mouse.get_pressed(),
    )


class ScreenAction(Enum):
    START_FRESH = auto()
    CONTINUE = auto()
    OPEN_STORE = auto()
    OPEN_MINI_GAME = auto()
    RETURN_TO_MAIN = auto()
    QUIT = auto()


class StartupScreen:
    def __init__(self, display, audio, save_available=False):
        self.display = display
        self.audio = audio
        self.save_available = save_available
        self.font = pygame.font.Font(FONT_PATH, HUD_FONT_SIZE)
        self.message = None
        self.buttons = [
            (
                TextButton("NEW GAME", (50, 58, 100, 18), self.font),
                ScreenAction.START_FRESH,
            ),
            (
                TextButton("CONTINUE", (50, 84, 100, 18), self.font),
                ScreenAction.CONTINUE,
            ),
            (
                TextButton("QUIT", (50, 110, 100, 18), self.font),
                ScreenAction.QUIT,
            ),
        ]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.display.screen_to_surface(event.pos)
            for button, action in self.buttons:
                disabled = (
                    action is ScreenAction.CONTINUE and not self.save_available
                )
                if button.handle_click(pos, disabled):
                    if disabled:
                        self.audio.play("denied")
                        return

                    self.audio.play("click")
                    return action

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            pos = self.display.screen_to_surface(event.pos)
            for button, action in self.buttons:
                disabled = (
                    action is ScreenAction.CONTINUE and not self.save_available
                )
                button.handle_release(pos, disabled)

    def update(self, dt):
        for button, _ in self.buttons:
            button.update(dt)

    def draw(self, surface):
        surface.fill((40, 40, 40))
        draw_centered(surface, self.font, "TAMAGOTCHI", 18)

        if self.message:
            draw_centered(
                surface, self.font, self.message, 39, CRITICAL_TEXT_COLOR
            )

        mouse_pos, mouse_pressed = mouse_state(self.display)
        for button, action in self.buttons:
            disabled = action is ScreenAction.CONTINUE and not self.save_available
            button.draw(surface, mouse_pos, mouse_pressed, disabled)

    def show_save_error(self):
        self.message = "SAVE INVALID"
        self.save_available = False

class DeathScreen:
    """Show a memorial and offer a fresh start after the pet dies."""

    def __init__(self, display, pet, audio):
        self.display = display
        self.pet = pet
        self.audio = audio
        self.font = pygame.font.Font(FONT_PATH, HUD_FONT_SIZE)
        self.buttons = [
            (
                TextButton("NEW PET", (15, 122, 82, 18), self.font),
                ScreenAction.START_FRESH,
            ),
            (
                TextButton("QUIT", (103, 122, 82, 18), self.font),
                ScreenAction.QUIT,
            ),
        ]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.display.screen_to_surface(event.pos)
            for button, action in self.buttons:
                if button.handle_click(pos):
                    self.audio.play("click")
                    return action

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            pos = self.display.screen_to_surface(event.pos)
            for button, _ in self.buttons:
                button.handle_release(pos)

    def update(self, dt):
        for button, _ in self.buttons:
            button.update(dt)

    def draw(self, surface):
        surface.fill((40, 40, 40))
        draw_centered(
            surface, self.font, "GAME OVER", 5, CRITICAL_TEXT_COLOR
        )
        draw_centered(
            surface,
            self.font,
            f"GOODBYE {self.pet.name.upper()}",
            22,
        )
        draw_centered(
            surface,
            self.font,
            f"{self.pet.life_stage} {self.pet.age_text}",
            70,
        )

        mouse_pos, mouse_pressed = mouse_state(self.display)
        for button, _ in self.buttons:
            button.draw(surface, mouse_pos, mouse_pressed)

class MainScreen:
    def __init__(self, display, pet, audio):
        self.pet = pet
        self.audio = audio
        self.view = MainView(display)
        self.renaming = False
        self.name_buffer = pet.name
        self.pending_wake = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            toast_action = self.view.handle_toast_click(event.pos)
            if toast_action:
                if toast_action == "dismissed":
                    self.audio.play("click")
                return

        if self.renaming:
            return self.handle_name_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.view.name_tag_clicked(event.pos):
                self.renaming = True
                self.name_buffer = self.pet.name
                pygame.key.start_text_input()
                self.audio.play("click")
                return

            button_hit, action = self.view.handle_click(event.pos, self.pet)

            if action == "store":
                self.audio.play("click")
                return ScreenAction.OPEN_STORE

            if action == "game":
                self.audio.play("click")
                return ScreenAction.OPEN_MINI_GAME

            if self.pet.dead:
                if button_hit:
                    self.audio.play("denied")
                return

            if not button_hit:
                self.pet.balance += 1
                self.audio.play("coin")
            elif action and self.pet.perform(action):
                self.view.action_performed(action)
                self.audio.play("click")
            elif button_hit:
                self.audio.play("denied")

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.view.handle_release(event.pos, self.pet)

    def handle_name_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.finish_renaming(save=False)

        elif event.key == pygame.K_RETURN:
            self.finish_renaming(save=True)

        elif event.key == pygame.K_BACKSPACE:
            self.name_buffer = self.name_buffer[:-1]

        else:
            character = getattr(event, "unicode", "")
            if (
                len(self.name_buffer) < PET_NAME_MAX_LENGTH
                and self.valid_name_character(character)
            ):
                self.name_buffer += character

    def finish_renaming(self, save):
        if save:
            name = self.name_buffer.strip()
            if not name:
                self.audio.play("denied")
                return

            self.pet.name = name
            self.audio.play("click")

        self.renaming = False
        pygame.key.stop_text_input()

    def valid_name_character(self, character):
        return bool(character) and (
            character.isalnum() or character in " -_"
        )

    def update(self, dt):
        self.show_mood_events()

        if self.pet.dead:
            return

        self.view.update_controls(dt)
        self.view.update(dt, self.pet, self.pending_wake)
        self.pending_wake = False

    def record_pet_update(self, woke_up):
        """Retain wake events until the main screen can present them."""
        self.pending_wake = self.pending_wake or woke_up

    def show_mood_events(self):
        personality_messages = PERSONALITY_MOOD_MESSAGES.get(
            self.pet.personality,
            {},
        )
        for stat, change in self.pet.drain_mood_events():
            message = (
                personality_messages
                .get(stat, {})
                .get(change, MOOD_MESSAGES[stat][change])
            )
            self.view.show_toast(stat, message)

    def draw(self, surface):
        displayed_name = self.name_buffer if self.renaming else self.pet.name
        self.view.draw(
            surface,
            self.pet,
            displayed_name=displayed_name,
            editing_name=self.renaming,
        )


class StoreScreen:
    def __init__(self, display, pet, audio):
        self.display = display
        self.pet = pet
        self.audio = audio
        self.font = pygame.font.Font(FONT_PATH, HUD_FONT_SIZE)
        self.message = None
        self.item_buttons = {}

        for index, (item_name, item) in enumerate(STORE_ITEMS.items()):
            label = f"{item['label']} ${item['price']}"
            self.item_buttons[item_name] = TextButton(
                label,
                (20, 35 + index * 24, 160, 18),
                self.font,
            )

        self.back_button = TextButton("BACK", (60, 122, 80, 18), self.font)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.display.screen_to_surface(event.pos)

            if self.back_button.handle_click(pos):
                self.audio.play("click")
                return ScreenAction.RETURN_TO_MAIN

            for item_name, button in self.item_buttons.items():
                disabled = self.pet.balance < STORE_ITEMS[item_name]["price"]
                if button.handle_click(pos, disabled):
                    if not disabled and self.pet.buy(item_name):
                        self.message = "PURCHASED"
                        self.audio.play("purchase")
                    else:
                        self.message = "NOT ENOUGH MONEY"
                        self.audio.play("denied")
                    return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            pos = self.display.screen_to_surface(event.pos)
            self.back_button.handle_release(pos)

            for item_name, button in self.item_buttons.items():
                disabled = self.pet.balance < STORE_ITEMS[item_name]["price"]
                button.handle_release(pos, disabled)

    def update(self, dt):
        self.back_button.update(dt)
        for button in self.item_buttons.values():
            button.update(dt)

    def draw(self, surface):
        surface.fill((40, 40, 40))
        draw_centered(surface, self.font, "STORE", 4)
        draw_centered(
            surface,
            self.font,
            f"BALANCE {self.pet.balance}",
            19,
        )

        mouse_pos, mouse_pressed = mouse_state(self.display)
        for item_name, button in self.item_buttons.items():
            disabled = self.pet.balance < STORE_ITEMS[item_name]["price"]
            button.draw(surface, mouse_pos, mouse_pressed, disabled)

        if self.message:
            draw_centered(surface, self.font, self.message, 107)

        self.back_button.draw(surface, mouse_pos, mouse_pressed)

class MiniGameScreen:
    def __init__(self, display, pet, audio):
        self.display = display
        self.pet = pet
        self.audio = audio
        self.font = pygame.font.Font(FONT_PATH, HUD_FONT_SIZE)
        self.player_choice = None
        self.computer_choice = None
        self.result_message = None
        self.result_color = HUD_TEXT_COLOR
        self.choice_buttons = {
            "rock": TextButton("ROCK", (14, 40, 40, 18), self.font),
            "paper": TextButton("PAPER", (59, 40, 48, 18), self.font),
            "scissors": TextButton(
                "SCISSORS",
                (112, 40, 74, 18),
                self.font,
            ),
        }
        self.back_button = TextButton("BACK", (60, 122, 80, 18), self.font)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.display.screen_to_surface(event.pos)

            if self.back_button.handle_click(pos):
                self.audio.play("click")
                return ScreenAction.RETURN_TO_MAIN

            for choice, button in self.choice_buttons.items():
                if button.handle_click(pos):
                    self.play_round(choice)
                    return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            pos = self.display.screen_to_surface(event.pos)
            self.back_button.handle_release(pos)
            for button in self.choice_buttons.values():
                button.handle_release(pos)

    def play_round(self, player_choice):
        computer_choice = random.choice(RPS_CHOICES)
        outcome = self.round_outcome(player_choice, computer_choice)

        self.player_choice = player_choice
        self.computer_choice = computer_choice

        if outcome == "win":
            self.pet.balance += RPS_WIN_REWARD
            self.result_message = f"YOU WIN +${RPS_WIN_REWARD}"
            self.result_color = HUD_TEXT_COLOR
            self.audio.play("coin")

        elif outcome == "draw":
            self.pet.balance += RPS_DRAW_REWARD
            self.result_message = f"DRAW +${RPS_DRAW_REWARD}"
            self.result_color = HUD_TEXT_COLOR
            self.audio.play("coin")

        else:
            self.result_message = "YOU LOSE"
            self.result_color = CRITICAL_TEXT_COLOR
            self.audio.play("denied")

    def round_outcome(self, player_choice, computer_choice):
        if player_choice == computer_choice:
            return "draw"
        if RPS_BEATS[player_choice] == computer_choice:
            return "win"
        return "loss"

    def update(self, dt):
        self.back_button.update(dt)
        for button in self.choice_buttons.values():
            button.update(dt)

    def draw(self, surface):
        surface.fill((40, 40, 40))
        draw_centered(surface, self.font, "ROCK PAPER SCISSORS", 4)
        draw_centered(
            surface,
            self.font,
            f"BALANCE {self.pet.balance}",
            19,
        )

        mouse_pos, mouse_pressed = mouse_state(self.display)
        for button in self.choice_buttons.values():
            button.draw(surface, mouse_pos, mouse_pressed)

        if self.result_message:
            draw_centered(
                surface,
                self.font,
                f"YOU: {self.player_choice.upper()}",
                70,
            )
            draw_centered(
                surface,
                self.font,
                f"CPU: {self.computer_choice.upper()}",
                84,
            )
            draw_centered(
                surface,
                self.font,
                self.result_message,
                100,
                self.result_color,
            )

        self.back_button.draw(surface, mouse_pos, mouse_pressed)
