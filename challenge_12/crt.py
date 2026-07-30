import pygame
from pygame.locals import DOUBLEBUF, K_b, KEYDOWN, OPENGL, QUIT
from OpenGL.GL import (
    GL_CLAMP_TO_EDGE,
    GL_COLOR_BUFFER_BIT,
    GL_FRAGMENT_SHADER,
    GL_LINEAR,
    GL_NEAREST,
    GL_QUADS,
    GL_RGB,
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNPACK_ALIGNMENT,
    GL_UNSIGNED_BYTE,
    GL_VERTEX_SHADER,
    GL_VIEWPORT,
    glActiveTexture,
    glBegin,
    glBindTexture,
    glClear,
    glClearColor,
    glDeleteTextures,
    glEnable,
    glEnd,
    glGenTextures,
    glGetUniformLocation,
    glGetIntegerv,
    glPixelStorei,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTexSubImage2D,
    glUniform1f,
    glUniform1i,
    glUniform2f,
    glUseProgram,
    glVertex2f,
    glViewport,
)
from OpenGL.GL.shaders import compileProgram, compileShader


DEFAULT_VERTEX_SHADER = """
#version 120

varying vec2 v_uv;

void main() {
    gl_Position = gl_Vertex;
    v_uv = gl_MultiTexCoord0.xy;
}
"""

DEFAULT_FRAGMENT_SHADER = """
#version 120

uniform sampler2D screen_texture;
uniform float time;
uniform vec2 resolution;
uniform float wave_strength;
uniform float chromatic_offset;
uniform float scanline_strength;
uniform float vignette_strength;
uniform float desaturation;
uniform float curvature_strength;
uniform float mask_strength;
uniform float glow_strength;

varying vec2 v_uv;

vec2 curve_uv(vec2 uv) {
    vec2 centered = uv * 2.0 - 1.0;
    float radius2 = dot(centered, centered);
    centered *= 1.0 + curvature_strength * radius2;
    return centered * 0.5 + 0.5;
}

float screen_mask(vec2 uv) {
    vec2 edge_distance = min(uv, vec2(1.0) - uv);
    vec2 edge_width = max(fwidth(uv), vec2(0.0001));
    vec2 edge = smoothstep(vec2(0.0), edge_width, edge_distance);
    return edge.x * edge.y;
}

vec3 sample_crt(vec2 uv) {
    vec2 texel = 1.0 / resolution;

    vec3 color;
    color.r = texture2D(screen_texture, uv + vec2(chromatic_offset, 0.0)).r;
    color.g = texture2D(screen_texture, uv).g;
    color.b = texture2D(screen_texture, uv - vec2(chromatic_offset, 0.0)).b;

    vec3 glow = texture2D(screen_texture, uv + vec2(texel.x * 1.5, 0.0)).rgb;
    glow += texture2D(screen_texture, uv - vec2(texel.x * 1.5, 0.0)).rgb;
    glow += texture2D(screen_texture, uv + vec2(0.0, texel.y * 1.5)).rgb;
    glow += texture2D(screen_texture, uv - vec2(0.0, texel.y * 1.5)).rgb;
    glow += texture2D(screen_texture, uv + texel * vec2(1.2, 1.2)).rgb;
    glow += texture2D(screen_texture, uv + texel * vec2(-1.2, 1.2)).rgb;
    glow += texture2D(screen_texture, uv + texel * vec2(1.2, -1.2)).rgb;
    glow += texture2D(screen_texture, uv + texel * vec2(-1.2, -1.2)).rgb;
    glow *= 0.125;

    return mix(color, glow, glow_strength);
}

vec3 phosphor_mask() {
    float triad = mod(floor(gl_FragCoord.x), 3.0);
    vec3 mask = vec3(0.72);

    if (triad < 1.0) {
        mask.r = 1.22;
    } else if (triad < 2.0) {
        mask.g = 1.22;
    } else {
        mask.b = 1.22;
    }

    float slot = 0.86 + 0.14 * smoothstep(0.15, 0.65, abs(fract(gl_FragCoord.y * 0.5) - 0.5));
    return mix(vec3(1.0), mask * slot, mask_strength);
}

void main() {
    vec2 uv = curve_uv(v_uv);
    uv.x += sin((uv.y * 15.0) + (time * 2.7)) * wave_strength;

    float visible = screen_mask(uv);
    if (visible <= 0.0) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    vec3 color = sample_crt(clamp(uv, vec2(0.0), vec2(1.0)));
    color = pow(color, vec3(2.2));

    float luma = dot(color, vec3(0.2126, 0.7152, 0.0722));
    float scan_position = abs(fract(uv.y * resolution.y) - 0.5);
    float beam_width = mix(0.18, 0.34, clamp(luma * 1.25, 0.0, 1.0));
    float beam = exp(-(scan_position * scan_position) / (beam_width * beam_width));
    float scanline = mix(1.0 - scanline_strength, 1.08, beam);
    color *= scanline;

    color *= phosphor_mask();

    float vignette = 1.0 - smoothstep(0.25, 0.92, distance(uv, vec2(0.5)));
    color *= mix(1.0, vignette, vignette_strength);
    color = mix(color, vec3(color.g), desaturation);
    color *= 1.5;
    color = pow(max(color, vec3(0.0)), vec3(1.0 / 2.2));
    color *= visible;

    gl_FragColor = vec4(color, 1.0);
}
"""


class ShaderEffectDisplay:
    """Pygame display wrapper that presents a surface through a PyOpenGL shader."""

    def __init__(
        self,
        window_size,
        surface_size=None,
        caption=None,
        clear_color=(14, 40, 66),
        vertex_shader=DEFAULT_VERTEX_SHADER,
        fragment_shader=DEFAULT_FRAGMENT_SHADER,
        flags=0,
        bypass=False,
        wave_strength=0.00035,
        chromatic_offset=0.0018,
        scanline_strength=0.34,
        vignette_strength=0.55,
        desaturation=0.03,
        curvature_strength=0.055,
        mask_strength=0.34,
        glow_strength=0.16,
    ):
        self.window_size = window_size
        self.surface_size = surface_size or window_size
        self.wave_strength = wave_strength
        self.chromatic_offset = chromatic_offset
        self.scanline_strength = scanline_strength
        self.vignette_strength = vignette_strength
        self.desaturation = desaturation
        self.curvature_strength = curvature_strength
        self.mask_strength = mask_strength
        self.glow_strength = glow_strength
        self.bypass = bool(bypass)
        self.window = None
        self.display_flags = flags | DOUBLEBUF | OPENGL
        self.drawable_size = window_size

        self._open_window(caption, flags)

        self.surface = pygame.Surface(self.surface_size)
        self.shader_program = self._make_shader_program(vertex_shader, fragment_shader)
        self.texture_id = self._make_texture(self.surface)
        self._texture_size = self.surface.get_size()
        self._uniforms = {}

        self._set_viewport()
        glClearColor(
            clear_color[0] / 255,
            clear_color[1] / 255,
            clear_color[2] / 255,
            1,
        )
        glEnable(GL_TEXTURE_2D)

    def present(self, surface=None, time=None):
        """Upload a pygame surface, render it, and flip the display."""
        source = surface or self.surface
        if source.get_size() != self._texture_size:
            self._replace_texture(source)

        self._upload_surface(source)
        self._draw(source, pygame.time.get_ticks() / 1000 if time is None else time)
        if self.window is None:
            pygame.display.flip()
        else:
            self.window.flip()

    def screen_to_surface(self, pos):
        """Convert display-window coordinates to this effect's surface coordinates."""
        x, y = pos
        return (
            int(x * self.surface_size[0] / self.window_size[0]),
            int(y * self.surface_size[1] / self.window_size[1]),
        )

    def set_bypass(self, bypass):
        """Enable or disable the shader effect for quick A/B checks."""
        self.bypass = bool(bypass)

    def close(self):
        glDeleteTextures([self.texture_id])
        if self.window is not None:
            self.window.destroy()
            self.window = None

    def _open_window(self, caption, flags):
        window_class = getattr(pygame, "Window", None)
        if window_class is None:
            pygame.display.set_mode(self.window_size, self.display_flags)
            if caption:
                pygame.display.set_caption(caption)
            return

        try:
            self.window = window_class(
                title=caption or "pygame window",
                size=self.window_size,
                opengl=True,
                allow_high_dpi=True,
                fullscreen=bool(flags & getattr(pygame, "FULLSCREEN", 0)),
                borderless=bool(flags & getattr(pygame, "NOFRAME", 0)),
                resizable=bool(flags & getattr(pygame, "RESIZABLE", 0)),
                hidden=bool(flags & getattr(pygame, "HIDDEN", 0)),
            )
        except (TypeError, pygame.error):
            self.window = None
            pygame.display.set_mode(self.window_size, self.display_flags)
            if caption:
                pygame.display.set_caption(caption)

    def _set_viewport(self):
        if self.window is None:
            get_drawable_size = getattr(pygame.display, "get_drawable_size", None)
            if get_drawable_size is None:
                self.drawable_size = self.window_size
            else:
                self.drawable_size = get_drawable_size()
        else:
            viewport = glGetIntegerv(GL_VIEWPORT)
            viewport_size = (int(viewport[2]), int(viewport[3]))
            if viewport_size[0] > 0 and viewport_size[1] > 0:
                self.drawable_size = viewport_size
            else:
                self.drawable_size = self.window.size
        glViewport(0, 0, *self.drawable_size)

    def _uniform_location(self, name):
        if name not in self._uniforms:
            self._uniforms[name] = glGetUniformLocation(self.shader_program, name)
        return self._uniforms[name]

    def _make_shader_program(self, vertex_shader, fragment_shader):
        return compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )

    def _make_texture(self, surface):
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        width, height = surface.get_size()
        pixels = pygame.image.tostring(surface, "RGB", True)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            width,
            height,
            0,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            pixels,
        )
        return texture_id

    def _replace_texture(self, surface):
        glDeleteTextures([self.texture_id])
        self.texture_id = self._make_texture(surface)
        self._texture_size = surface.get_size()

    def _upload_surface(self, surface):
        width, height = surface.get_size()
        pixels = pygame.image.tostring(surface, "RGB", True)

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexSubImage2D(
            GL_TEXTURE_2D,
            0,
            0,
            0,
            width,
            height,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            pixels,
        )

    def _draw(self, surface, time):
        glClear(GL_COLOR_BUFFER_BIT)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        if self.bypass:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        else:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        if self.bypass:
            glUseProgram(0)
            self._draw_fullscreen_quad()
            return

        glUseProgram(self.shader_program)
        glUniform1i(self._uniform_location("screen_texture"), 0)
        glUniform1f(self._uniform_location("time"), time)
        glUniform2f(self._uniform_location("resolution"), *surface.get_size())
        glUniform1f(self._uniform_location("wave_strength"), self.wave_strength)
        glUniform1f(self._uniform_location("chromatic_offset"), self.chromatic_offset)
        glUniform1f(self._uniform_location("scanline_strength"), self.scanline_strength)
        glUniform1f(self._uniform_location("vignette_strength"), self.vignette_strength)
        glUniform1f(self._uniform_location("desaturation"), self.desaturation)
        glUniform1f(self._uniform_location("curvature_strength"), self.curvature_strength)
        glUniform1f(self._uniform_location("mask_strength"), self.mask_strength)
        glUniform1f(self._uniform_location("glow_strength"), self.glow_strength)

        self._draw_fullscreen_quad()
        glUseProgram(0)

    def _draw_fullscreen_quad(self):
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(-1, -1)
        glTexCoord2f(1, 0)
        glVertex2f(1, -1)
        glTexCoord2f(1, 1)
        glVertex2f(1, 1)
        glTexCoord2f(0, 1)
        glVertex2f(-1, 1)
        glEnd()


def run_demo():
    pygame.init()

    clock = pygame.time.Clock()
    effect = ShaderEffectDisplay(
        window_size=(800, 600),
        surface_size=(160, 120),
        caption="PyOpenGL shader effect demo",
    )
    screen = effect.surface

    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == QUIT:
                done = True
            elif event.type == KEYDOWN and event.key == K_b:
                effect.set_bypass(not effect.bypass)

        screen.fill((255, 0, 255))
        pygame.draw.circle(screen, (0, 0, 0), (100, 100), 20)
        pygame.draw.circle(screen, (0, 0, 200), (0, 0), 10)
        pygame.draw.circle(screen, (200, 0, 0), (160, 120), 30)
        pygame.draw.line(screen, (250, 250, 0), (0, 120), (160, 0))

        effect.present()
        clock.tick(30)

    effect.close()
    pygame.quit()


if __name__ == "__main__":
    run_demo()
