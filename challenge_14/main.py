import questionary
from moviepy import *
from moviepy.video.tools.subtitles import SubtitlesClip
from pathlib import Path
from decimal import Decimal

edit = None

VIDEO_EXTS = [".mov", ".mp4", ".mkv"]
AUDIO_EXTS = [".mp3", ".wav", ".flac", ".m4a"]
IMAGE_EXTS = [".jpg", ".jpeg", ".png"]

def is_number(number):
    if not number:
        return False
    
    try:
        _ = Decimal(number)
        return True
    except Exception:
        return False

def generate_text_clip(txt):
    return TextClip(
        text=txt,
        font_size=50,
        color="white",
        stroke_color="black",
        stroke_width=2,
        method="caption",
        size=(edit.w - 100, None),
        text_align="center",
    )

def trim():
    global edit
    start = Decimal(questionary.text("Start time (s)", validate=lambda x: is_number(x) and Decimal(x) <= edit.duration).ask())
    end = Decimal(questionary.text("End time (s)", validate=lambda x: is_number(x) and start < Decimal(x) <= edit.duration).ask())

    edit = edit.subclipped(float(start), float(end))

def audio():
    global edit
    audio_file = None

    while not audio_file:
        audio_file = questionary.path("Load file", validate=lambda x: (x != "" and Path(x).exists() and Path(x).suffix in AUDIO_EXTS)).ask()

    path = Path(audio_file).expanduser()

    bg_audio = AudioFileClip(path)

    bg_audio = bg_audio.with_volume_scaled(0.3)
    mixed_audio = CompositeAudioClip([edit.audio, bg_audio])
    edit = edit.with_audio(mixed_audio)

def text():
    global edit
    start = Decimal(questionary.text("Start time (s)", validate=lambda x: is_number(x) and Decimal(x) <= edit.duration).ask())
    end = Decimal(questionary.text("End time (s)", validate=lambda x: is_number(x) and start < Decimal(x) <= edit.duration).ask())
    duration = end - start

    text = questionary.text("Text to overlay").ask()

    text_overlay = (TextClip("Arial", text=text, color='white', font_size=64).with_position('center').with_duration(float(duration)))

    edit = CompositeVideoClip([edit, text_overlay])

def image():
    global edit
    start = Decimal(questionary.text("Start time (s)", validate=lambda x: is_number(x) and Decimal(x) <= edit.duration).ask())
    end = Decimal(questionary.text("End time (s)", validate=lambda x: is_number(x) and start < Decimal(x) <= edit.duration).ask())
    duration = end - start

    image_file = None

    while not image_file:
        image_file = questionary.path("Load file", validate=lambda x: (x != "" and Path(x).exists() and Path(x).suffix in IMAGE_EXTS)).ask()

    path = Path(image_file).expanduser()

    image_overlay = (ImageClip(path)).resized(width=100).with_position('center').with_duration(float(duration))

    edit = CompositeVideoClip([edit, image_overlay])

def filters():
    global edit
    filter_type = questionary.select("Effect", choices=["B&W", "Mirror"]).ask()
    match filter_type:
        case "B&W":
            edit = edit.with_effects([vfx.BlackAndWhite()])
        case "Mirror":
            edit = edit.with_effects([vfx.MirrorX()])

def subtitles():
    global edit

    subtitle_file = None

    while not subtitle_file:
        subtitle_file = questionary.path("Load file", validate=lambda x: (x != "" and Path(x).exists() and Path(x).suffix == ".srt")).ask()

    path = Path(subtitle_file).expanduser()

    subtitles = SubtitlesClip(path, make_textclip=generate_text_clip)
    subtitles = subtitles.with_position(('center', 'bottom'))
    edit = CompositeVideoClip([edit, subtitles])

def preview():
    global edit
    try:
        edit.preview()
    except OSError:
        pass

def export():
    global edit
    export_type = questionary.select("Format", choices=["Normal", "GIF"]).ask()

    if export_type == "GIF":
        start = Decimal(questionary.text("Start time (s)", validate=lambda x: is_number(x) and Decimal(x) <= edit.duration).ask())
        end = Decimal(questionary.text("End time (s)", validate=lambda x: is_number(x) and start < Decimal(x) <= edit.duration).ask())
        gif_copy = edit.subclipped(float(start), float(end))

        filename = None
        while not filename:
            filename = questionary.path("Output Filepath", validate=lambda x: (x != "" and Path(x).suffix == ".gif")).ask()

        gif_copy.write_gif(filename, fps=15)
        exit()

    filename = None
    while not filename:
        filename = questionary.path("Output Filepath", validate=lambda x: (x != "" and Path(x).suffix in VIDEO_EXTS)).ask()

    path = Path(filename).expanduser()
    edit.write_videofile(path, logger="bar")
    exit()


def main():
    global edit
    path = questionary.path("Load file", validate=lambda x: (x != "" and Path(x).exists() and Path(x).suffix in VIDEO_EXTS)).ask()

    if not path:
        exit()

    path = Path(path).expanduser()

    try:
        edit = VideoFileClip(path)
    except Exception as e:
        print("Error loading video!")
        exit()

    while True:
        choice = questionary.select(
            "Video Editor",
            choices=[
                "Trim",
                "Add audio",
                "Add text",
                "Add image",
                "Add filter",
                "Add subtitles",
                "Preview video",
                "Export video",
                "Exit",
            ],
            erase_when_done=True,
        ).ask()

        match choice:
            case "Trim":
                trim()

            case "Add audio":
                audio()

            case "Add text":
                text()

            case "Add image":
                image()

            case "Add filter":
                filters()

            case "Add subtitles":
                subtitles()

            case "Preview video":
                preview()

            case "Export video":
                export()

            case "Exit" | None:
                confirm = questionary.confirm("Are you sure you want to exit? All edits will be lost!", auto_enter=False).ask()
                if confirm:
                    break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass