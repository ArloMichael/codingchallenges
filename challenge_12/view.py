import random

import pygame

from settings import (
    CRITICAL_FLASH_MS,
    CRITICAL_TEXT_COLOR,
    CRITICAL_THRESHOLD,
    FONT_PATH,
    HUD_FONT_SIZE,
    HUD_TEXT_COLOR,
    NAME_CURSOR_BLINK_MS,
    NAME_TAG_BACKGROUND,
    NAME_TAG_COLOR,
    NAME_TAG_IDLE_X_OFFSET,
    STAT_ICON_TEXT_GAP,
    STAT_ROW_HEIGHT,
    TOAST_BACKGROUND_COLOR,
    VIRTUAL_HEIGHT,
    VIRTUAL_WIDTH,
)
from ui import Animation, TextButton, load_frames, load_icon


class MainView:
    """Own the main screen's controls, animation, and drawing."""

    def __init__(self, display):
        self.display = display
        self.canvas = display.surface
        self.font = pygame.font.Font(FONT_PATH, HUD_FONT_SIZE)
        self.icons = {
            "food": load_icon("food"),
            "happiness": load_icon("happy"),
            "energy": load_icon("energy"),
            "balance": load_icon("money"),
        }
        self.animations = {
            "idle": Animation(load_frames("animations", "idle", 2), 0.75),
            "run": Animation(load_frames("animations", "run", 12), 0.15),
            "sleep": Animation(load_frames("animations", "sleep", 2), 1),
        }
        self.state = "idle"
        self.state_timer = 0
        self.action_buttons = {
            "feed": TextButton("FEED", (2, 128, 37, 16), self.font),
            "play": TextButton("PLAY", (42, 128, 37, 16), self.font),
            "rest": TextButton("REST", (82, 128, 37, 16), self.font),
        }
        self.store_button = TextButton("SHOP", (122, 128, 37, 16), self.font)
        self.game_button = TextButton("GAME", (162, 128, 37, 16), self.font)
        self.name_tag_rect = pygame.Rect(0, 0, 0, 0)
        self.age_rect = pygame.Rect(0, 0, 0, 0)
        self.toast = None
        self.toast_rect = pygame.Rect(0, 0, 0, 0)
        self.toast_close_rect = pygame.Rect(0, 0, 0, 0)

    def handle_click(self, pos, pet):
        """Return (button_hit, enabled_action) for a screen-space click."""
        canvas_pos = self.display.screen_to_surface(pos)

        if self.store_button.handle_click(canvas_pos, disabled=pet.dead):
            return True, None if pet.dead else "store"

        if self.game_button.handle_click(canvas_pos, disabled=pet.dead):
            return True, None if pet.dead else "game"

        for action, button in self.action_buttons.items():
            disabled = self.is_button_disabled(action, pet)
            if button.handle_click(canvas_pos, disabled):
                return True, None if disabled else action

        return False, None

    def handle_release(self, pos, pet):
        canvas_pos = self.display.screen_to_surface(pos)
        self.store_button.handle_release(canvas_pos, disabled=pet.dead)
        self.game_button.handle_release(canvas_pos, disabled=pet.dead)

        for action, button in self.action_buttons.items():
            button.handle_release(
                canvas_pos,
                self.is_button_disabled(action, pet),
            )

    def action_performed(self, action):
        if action == "rest":
            self.state_timer = 0
            self.set_state("sleep")

    def update_controls(self, dt):
        self.store_button.update(dt)
        self.game_button.update(dt)

        for button in self.action_buttons.values():
            button.update(dt)

    def show_toast(self, icon_name, message):
        self.toast = (icon_name, message)

    def handle_toast_click(self, screen_pos):
        if self.toast is None:
            return None

        canvas_pos = self.display.screen_to_surface(screen_pos)
        if not self.toast_rect.collidepoint(canvas_pos):
            return None

        if self.toast_close_rect.collidepoint(canvas_pos):
            self.toast = None
            self.toast_rect = pygame.Rect(0, 0, 0, 0)
            self.toast_close_rect = pygame.Rect(0, 0, 0, 0)
            return "dismissed"

        return "blocked"

    def update(self, dt, pet, woke_up=False):
        if woke_up and self.state == "sleep":
            self.set_state("idle")

        self.state_timer += dt

        if pet.is_food_death_active():
            if self.state == "sleep":
                self.set_state("idle")
        elif pet.is_resting() or pet.is_energy_sleep_active():
            self.set_state("sleep")
        elif self.state_timer >= 3:
            self.state_timer = 0
            self.set_state(random.choice(pet.animation_choices))

        self.animations[self.state].update(dt)

    def set_state(self, new_state):
        if new_state != self.state:
            self.state = new_state
            self.animations[self.state].reset()

    def is_button_disabled(self, button_name, pet):
        return not pet.can_perform(button_name)

    def name_tag_clicked(self, screen_pos):
        canvas_pos = self.display.screen_to_surface(screen_pos)
        return self.name_tag_rect.collidepoint(canvas_pos)

    def draw(self, surface, pet, displayed_name=None, editing_name=False):
        self.canvas = surface
        self.canvas.fill((40, 40, 40))
        self.draw_pet(
            pet,
            pet.name if displayed_name is None else displayed_name,
            editing_name,
        )
        self.draw_stats(pet)
        self.draw_age(pet)
        self.draw_food_death_countdown(pet)
        self.draw_buttons(pet)
        self.draw_toast()

    def draw_pet(self, pet, displayed_name, editing_name=False):
        image = self.animations[self.state].image
        rect = image.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2))
        if not (pet.is_food_death_active() and self.is_critical_flash_on()):
            self.canvas.blit(image, rect)

        self.draw_name_tag(displayed_name, rect, editing_name)

    def draw_name_tag(self, name, pet_rect, editing=False):
        cursor_visible = (
            editing
            and pygame.time.get_ticks() // NAME_CURSOR_BLINK_MS % 2 == 0
        )
        layout_name = f"{name}_" if editing else name
        displayed_name = layout_name if cursor_visible else name
        color = CRITICAL_TEXT_COLOR if editing else NAME_TAG_COLOR
        layout = self.font.render(
            layout_name.upper(),
            False,
            color,
        )
        text = self.font.render(
            displayed_name.upper(),
            False,
            color,
        )
        text_rect = layout.get_rect(
            midbottom=(pet_rect.centerx, pet_rect.top - 4)
        )
        if not editing:
            glyph_bounds = layout.get_bounding_rect()
            text_rect.x += (
                layout.get_width() // 2
                - glyph_bounds.centerx
                + NAME_TAG_IDLE_X_OFFSET
            )

        self.name_tag_rect = text_rect.inflate(6, 4)

        pygame.draw.rect(
            self.canvas,
            NAME_TAG_BACKGROUND,
            self.name_tag_rect,
        )
        if editing:
            pygame.draw.rect(self.canvas, color, self.name_tag_rect, 1)

        self.canvas.blit(text, text_rect)

    def draw_stats(self, pet):
        rows = [
            ("food", self.icons["food"], pet.stats["food"]),
            ("happiness", self.icons["happiness"], pet.stats["happiness"]),
            ("energy", self.icons["energy"], pet.stats["energy"]),
            (None, self.icons["balance"], pet.balance),
        ]

        for index, (stat, label, value) in enumerate(rows):
            self.draw_stat(index, label, value, self.stat_text_color(stat, value))

    def draw_food_death_countdown(self, pet):
        if not pet.is_food_death_active():
            return

        countdown = int(pet.food_death_timer + 0.999)
        text = self.font.render(str(countdown), False, CRITICAL_TEXT_COLOR)
        rect = text.get_rect(midtop=(VIRTUAL_WIDTH // 2, 2))
        self.canvas.blit(text, rect)

    def draw_age(self, pet):
        age_text = self.font.render(
            f"{pet.life_stage} {pet.age_text}",
            False,
            HUD_TEXT_COLOR,
        )
        self.age_rect = age_text.get_rect(
            topright=(VIRTUAL_WIDTH - 2, 2)
        )
        mouse_pos = self.display.screen_to_surface(pygame.mouse.get_pos())
        label = (
            pet.personality
            if self.age_rect.collidepoint(mouse_pos)
            else f"{pet.life_stage} {pet.age_text}"
        )
        text = self.font.render(label, False, HUD_TEXT_COLOR)
        rect = text.get_rect(topright=self.age_rect.topright)
        self.canvas.blit(text, rect)

    def stat_text_color(self, stat, value):
        if stat and value <= CRITICAL_THRESHOLD:
            if self.is_critical_flash_on():
                return CRITICAL_TEXT_COLOR

        return HUD_TEXT_COLOR

    def is_critical_flash_on(self):
        return pygame.time.get_ticks() // CRITICAL_FLASH_MS % 2 == 0

    def draw_stat(self, index, label, value, color):
        x = 2
        y = 2 + index * STAT_ROW_HEIGHT

        if isinstance(label, pygame.Surface):
            self.canvas.blit(label, (x, y))
            text = self.font.render(f"{int(value)}", False, color)
            text_y = y + (label.get_height() - text.get_height()) // 2
            self.canvas.blit(text, (x + label.get_width() + STAT_ICON_TEXT_GAP, text_y))
            return

        text = self.font.render(f"{label} {int(value)}", False, color)
        self.canvas.blit(text, (x, y))

    def draw_toast(self):
        if self.toast is None:
            return

        icon_name, message = self.toast
        icon = self.icons[icon_name]
        text = self.font.render(message, False, HUD_TEXT_COLOR)
        close_text = self.font.render("X", False, HUD_TEXT_COLOR)
        gap = STAT_ICON_TEXT_GAP
        padding_x = 3
        padding_y = 2
        content_width = (
            icon.get_width()
            + gap
            + text.get_width()
            + gap
            + close_text.get_width()
        )
        content_height = max(
            icon.get_height(),
            text.get_height(),
            close_text.get_height(),
        )
        rect = pygame.Rect(
            0,
            0,
            content_width + padding_x * 2,
            content_height + padding_y * 2,
        )
        rect.midtop = (VIRTUAL_WIDTH // 2, 14)
        self.toast_rect = rect

        pygame.draw.rect(self.canvas, TOAST_BACKGROUND_COLOR, rect)
        pygame.draw.rect(self.canvas, HUD_TEXT_COLOR, rect, 1)

        icon_rect = icon.get_rect(
            midleft=(rect.left + padding_x, rect.centery)
        )
        text_rect = text.get_rect(
            midleft=(icon_rect.right + gap, rect.centery)
        )
        close_rect = close_text.get_rect(
            midleft=(text_rect.right + gap, rect.centery)
        )
        self.toast_close_rect = close_rect.inflate(4, 4)
        self.canvas.blit(icon, icon_rect)
        self.canvas.blit(text, text_rect)
        self.canvas.blit(close_text, close_rect)

    def draw_buttons(self, pet):
        mouse_pos = self.display.screen_to_surface(pygame.mouse.get_pos())
        mouse_pressed = pygame.mouse.get_pressed()

        for action, button in self.action_buttons.items():
            button.draw(
                self.canvas,
                mouse_pos,
                mouse_pressed,
                self.is_button_disabled(action, pet),
            )
        self.store_button.draw(
            self.canvas,
            mouse_pos,
            mouse_pressed,
            disabled=pet.dead,
        )
        self.game_button.draw(
            self.canvas,
            mouse_pos,
            mouse_pressed,
            disabled=pet.dead,
        )
