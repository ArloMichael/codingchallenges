import pygame

from settings import BASE_DIR, BUTTON_CLICK_HOLD_TIME


class Animation:
    def __init__(self, frames, frame_time=0.2):
        self.frames = frames
        self.frame_time = frame_time
        self.time = 0

    def update(self, dt):
        self.time += dt

    def reset(self):
        self.time = 0

    @property
    def image(self):
        frame = int(self.time / self.frame_time)
        return self.frames[frame % len(self.frames)]


def load_frames(folder, name, count):
    folder_path = BASE_DIR / "images" / folder / name
    return [load_image(folder_path / f"{frame}.png") for frame in range(count)]


def load_icon(name):
    return load_image(BASE_DIR / "images" / "icons" / f"{name}.png")


def load_image(path):
    image = pygame.image.load(path)
    try:
        return image.convert_alpha()
    except pygame.error:
        return image


class TextButton:
    """Code-drawn button with normal, hover, pressed, and disabled states."""

    def __init__(self, text, rect, font):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.font = font
        self.click_hold_timer = 0

    def update(self, dt):
        self.click_hold_timer = max(0, self.click_hold_timer - dt)

    def handle_click(self, pos, disabled=False):
        if not self.rect.collidepoint(pos):
            return False

        if not disabled:
            self.click_hold_timer = BUTTON_CLICK_HOLD_TIME

        return True

    def handle_release(self, pos, disabled=False):
        if not disabled and self.rect.collidepoint(pos):
            self.click_hold_timer = BUTTON_CLICK_HOLD_TIME

    def draw(self, surface, mouse_pos, mouse_pressed, disabled=False):
        hovered = self.rect.collidepoint(mouse_pos)
        pressed = (
            not disabled
            and ((hovered and mouse_pressed[0]) or self.click_hold_timer > 0)
        )

        if disabled:
            background = (55, 55, 55)
            foreground = (115, 115, 115)
        elif pressed:
            background = (105, 105, 105)
            foreground = (255, 255, 255)
        elif hovered:
            background = (80, 80, 80)
            foreground = (255, 255, 255)
        else:
            background = (60, 60, 60)
            foreground = (225, 225, 225)

        pygame.draw.rect(surface, background, self.rect)
        pygame.draw.rect(surface, foreground, self.rect, 1)

        text = self.font.render(self.text, False, foreground)
        text_rect = text.get_rect(center=self.rect.center)
        glyph_bounds = text.get_bounding_rect()
        text_rect.x += text.get_width() // 2 - glyph_bounds.centerx
        surface.blit(text, text_rect)
