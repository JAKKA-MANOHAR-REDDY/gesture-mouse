import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import math
import time
import os
import json
import sys

# =====================================================
# AIRBOARD PRO
# Touchless PC + Whiteboard + Presentation + Document + Calibration
# Home Screen + Saved Settings + Pages + Backgrounds
# Updated Drawing Mode:
# - Black writing screen
# - Index-only gesture required to draw/erase
# =====================================================

cv2.setUseOptimized(True)

try:
    cv2.setNumThreads(2)
except Exception:
    pass

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

APP_NAME = "AirBoard Pro"
SETTINGS_FILE = "airboard_settings.json"
SAVE_FOLDER = "saved_drawings"

# =====================================================
# DEFAULT SETTINGS
# =====================================================

DEFAULT_SETTINGS = {
    "performance_mode": "balanced",
    "camera_width": 1280,
    "camera_height": 720,
    "camera_fps": 30,
    "process_width": 480,
    "process_height": 270,
    "process_every_n_frames": 1,

    "move_hand": "Left",
    "click_hand": "Right",

    "smoothening": 5,
    "dead_zone": 3,
    "control_margin_x": 175,
    "control_margin_y": 95,
    "scroll_sensitivity": 1.05,

    "brush_size": 16,
    "color_index": 0,
    "show_ui": True,
    "dwell_click": False,
    "board_background": "camera",

    "calibrated_bounds": None
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            loaded = json.load(file)

        settings = DEFAULT_SETTINGS.copy()
        settings.update(loaded)
        return settings

    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings():
    data = {
        "performance_mode": performance_mode,
        "camera_width": CAMERA_WIDTH,
        "camera_height": CAMERA_HEIGHT,
        "camera_fps": CAMERA_FPS,
        "process_width": PROCESS_WIDTH,
        "process_height": PROCESS_HEIGHT,
        "process_every_n_frames": PROCESS_EVERY_N_FRAMES,

        "move_hand": move_hand_setting,
        "click_hand": click_hand_setting,

        "smoothening": smoothening,
        "dead_zone": dead_zone,
        "control_margin_x": CONTROL_MARGIN_X,
        "control_margin_y": CONTROL_MARGIN_Y,
        "scroll_sensitivity": scroll_sensitivity,

        "brush_size": brush_size,
        "color_index": color_index,
        "show_ui": show_ui,
        "dwell_click": dwell_click_mode,
        "board_background": board_background,

        "calibrated_bounds": calibrated_bounds
    }

    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
    except Exception:
        pass


settings = load_settings()

# =====================================================
# CAMERA / PERFORMANCE SETTINGS
# =====================================================

performance_mode = settings["performance_mode"]

CAMERA_WIDTH = settings["camera_width"]
CAMERA_HEIGHT = settings["camera_height"]
CAMERA_FPS = settings["camera_fps"]

PROCESS_WIDTH = settings["process_width"]
PROCESS_HEIGHT = settings["process_height"]
PROCESS_EVERY_N_FRAMES = settings["process_every_n_frames"]


def apply_performance_mode(mode):
    global performance_mode
    global CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS
    global PROCESS_WIDTH, PROCESS_HEIGHT, PROCESS_EVERY_N_FRAMES

    performance_mode = mode

    if mode == "low":
        CAMERA_WIDTH = 960
        CAMERA_HEIGHT = 540
        CAMERA_FPS = 30
        PROCESS_WIDTH = 400
        PROCESS_HEIGHT = 225
        PROCESS_EVERY_N_FRAMES = 2

    elif mode == "quality":
        CAMERA_WIDTH = 1280
        CAMERA_HEIGHT = 720
        CAMERA_FPS = 30
        PROCESS_WIDTH = 640
        PROCESS_HEIGHT = 360
        PROCESS_EVERY_N_FRAMES = 1

    else:
        CAMERA_WIDTH = 1280
        CAMERA_HEIGHT = 720
        CAMERA_FPS = 30
        PROCESS_WIDTH = 480
        PROCESS_HEIGHT = 270
        PROCESS_EVERY_N_FRAMES = 1


# =====================================================
# CONTROL SETTINGS
# =====================================================

move_hand_setting = settings["move_hand"]
click_hand_setting = settings["click_hand"]

smoothening = settings["smoothening"]
dead_zone = settings["dead_zone"]

CONTROL_MARGIN_X = settings["control_margin_x"]
CONTROL_MARGIN_Y = settings["control_margin_y"]

scroll_sensitivity = settings["scroll_sensitivity"]

click_delay = 0.55
double_tap_window = 0.42

last_left_click = 0
last_right_click = 0
last_double_click = 0
last_index_thumb_tap = 0

right_pinch_active = False
middle_pinch_active = False

screen_w, screen_h = pyautogui.size()

prev_x = screen_w // 2
prev_y = screen_h // 2

# =====================================================
# APP MODES
# =====================================================

drawing_mode = False
presentation_mode = False
document_mode = False
tutorial_mode = False
show_ui = settings["show_ui"]
dwell_click_mode = settings["dwell_click"]
calibration_mode = False
gesture_locked = False

active_mode = "READY"
status_message = "Ready"

toast_message = "Welcome to AirBoard Pro"
toast_time = time.time()

mode_card_title = ""
mode_card_subtitle = ""
mode_card_time = 0

# =====================================================
# UI TRAILS
# =====================================================

move_trail = []
click_trail = []
drawing_trail = []
MAX_TRAIL_LENGTH = 18

# =====================================================
# CALIBRATION
# =====================================================

calibration_points = []
calibration_step = 0
calibrated_bounds = settings["calibrated_bounds"]

calibration_steps = [
    "TOP LEFT",
    "TOP RIGHT",
    "BOTTOM LEFT",
    "BOTTOM RIGHT",
    "CENTER"
]

# =====================================================
# DRAWING / WHITEBOARD
# =====================================================

drawing_canvas = None

draw_prev_x = None
draw_prev_y = None
erase_prev_x = None
erase_prev_y = None

brush_size = settings["brush_size"]
MIN_BRUSH_SIZE = 4
MAX_BRUSH_SIZE = 90

color_names = [
    "YELLOW",
    "GREEN",
    "BLUE",
    "RED",
    "PURPLE",
    "WHITE",
    "ORANGE",
    "CYAN"
]

brush_colors = [
    (0, 255, 255),
    (0, 255, 0),
    (255, 0, 0),
    (0, 0, 255),
    (255, 0, 255),
    (255, 255, 255),
    (0, 165, 255),
    (255, 255, 0)
]

color_index = settings["color_index"]
color_index = max(0, min(color_index, len(brush_colors) - 1))
brush_color = brush_colors[color_index]

strokes = []
redo_stack = []
current_draw_stroke = None
current_erase_stroke = None

whiteboard_pages = []
current_page_index = 0

board_backgrounds = ["camera", "blackboard", "whiteboard", "grid", "dark"]
board_background = settings["board_background"]

if board_background not in board_backgrounds:
    board_background = "camera"

# =====================================================
# PRESENTATION / DOCUMENT / DWELL
# =====================================================

swipe_start_x = None
swipe_start_time = 0
last_slide_action = 0
slide_cooldown = 0.85
swipe_distance = 115

last_zoom_action = 0
zoom_cooldown = 0.7

dwell_start_time = 0
dwell_last_x = None
dwell_last_y = None
dwell_clicked = False

DWELL_SECONDS = 1.1
DWELL_RADIUS = 35

# =====================================================
# MEDIAPIPE SETUP
# =====================================================

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    max_num_hands=2,
    model_complexity=0,
    min_detection_confidence=0.55,
    min_tracking_confidence=0.55
)

last_results = None
frame_count = 0

# =====================================================
# WINDOW
# =====================================================

cv2.namedWindow(APP_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(APP_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# =====================================================
# BASIC HELPERS
# =====================================================

def set_status(text):
    global status_message, toast_message, toast_time

    status_message = text
    toast_message = text
    toast_time = time.time()


def show_mode_card(title, subtitle):
    global mode_card_title, mode_card_subtitle, mode_card_time

    mode_card_title = title
    mode_card_subtitle = subtitle
    mode_card_time = time.time()


def dist(a, b):
    ax = int(a.x * PROCESS_WIDTH)
    ay = int(a.y * PROCESS_HEIGHT)
    bx = int(b.x * PROCESS_WIDTH)
    by = int(b.y * PROCESS_HEIGHT)

    return math.hypot(ax - bx, ay - by)


def landmark_point(hand, landmark_id, display_w, display_h):
    lm = hand.landmark[landmark_id]
    return int(lm.x * display_w), int(lm.y * display_h)


def process_point(hand, landmark_id):
    lm = hand.landmark[landmark_id]
    return int(lm.x * PROCESS_WIDTH), int(lm.y * PROCESS_HEIGHT)


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def get_current_mode_name():
    if calibration_mode:
        return "CALIBRATION"

    if drawing_mode:
        return "WHITEBOARD"

    if presentation_mode:
        return "PRESENTATION"

    if document_mode:
        return "DOCUMENT"

    if gesture_locked:
        return "LOCKED"

    return "MOUSE"


def make_gradient_frame(width=1280, height=720):
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    for y in range(height):
        intensity = int(18 + (y / height) * 40)
        frame[y, :] = (intensity, intensity, intensity + 18)

    return frame


# =====================================================
# GESTURE HELPERS
# =====================================================

def is_index_only(hand):
    """
    True only when index finger is open and middle/ring/pinky are folded.
    This prevents accidental drawing when the full palm is open.
    """

    index_up = hand.landmark[8].y < hand.landmark[6].y
    middle_down = hand.landmark[12].y > hand.landmark[10].y
    ring_down = hand.landmark[16].y > hand.landmark[14].y
    pinky_down = hand.landmark[20].y > hand.landmark[18].y

    return index_up and middle_down and ring_down and pinky_down


# =====================================================
# HOME SCREEN
# =====================================================

def draw_home_screen():
    selected_tip = "Press 1, 2, 3, 4, or 5"

    while True:
        frame = make_gradient_frame(1280, 720)

        cv2.putText(
            frame,
            "AIRBOARD PRO",
            (375, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            2.0,
            (255, 255, 255),
            4
        )

        cv2.putText(
            frame,
            "Touchless PC + Whiteboard + Presentation Controller",
            (300, 205),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        menu_items = [
            "1  Start Gesture Control",
            "2  Start With Tutorial",
            "3  Low-End PC Mode",
            "4  Quality Mode",
            "5  Exit"
        ]

        x = 390
        y = 300

        for i, item in enumerate(menu_items):
            box_y = y + i * 65

            cv2.rectangle(
                frame,
                (x - 25, box_y - 38),
                (x + 520, box_y + 15),
                (28, 28, 40),
                -1
            )

            cv2.rectangle(
                frame,
                (x - 25, box_y - 38),
                (x + 520, box_y + 15),
                (0, 255, 255),
                2
            )

            cv2.putText(
                frame,
                item,
                (x, box_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

        cv2.putText(
            frame,
            f"Current performance mode: {performance_mode.upper()}",
            (390, 645),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 0),
            2
        )

        cv2.putText(
            frame,
            selected_tip,
            (470, 685),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            1
        )

        cv2.imshow(APP_NAME, frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("1"):
            return "start"

        if key == ord("2"):
            return "tutorial"

        if key == ord("3"):
            apply_performance_mode("low")
            selected_tip = "Low-End PC Mode selected. Press 1 to start."

        if key == ord("4"):
            apply_performance_mode("quality")
            selected_tip = "Quality Mode selected. Press 1 to start."

        if key == ord("5") or key == ord("q"):
            return "exit"


def draw_loading_screen():
    stages = [
        "Initializing Camera",
        "Loading Hand Tracking Engine",
        "Preparing Gesture Controls",
        "Building Premium UI",
        "Ready"
    ]

    for i, stage in enumerate(stages):
        frame = make_gradient_frame(1280, 720)

        cv2.putText(
            frame,
            "AIRBOARD PRO",
            (390, 270),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.8,
            (255, 255, 255),
            3
        )

        cv2.putText(
            frame,
            "Touchless PC + Whiteboard + Presentation Controller",
            (310, 320),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            stage,
            (470, 405),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )

        bar_x = 340
        bar_y = 450
        bar_w = 600
        bar_h = 22

        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80, 80, 80), 2)

        progress = int((i + 1) / len(stages) * bar_w)

        cv2.rectangle(
            frame,
            (bar_x, bar_y),
            (bar_x + progress, bar_y + bar_h),
            (0, 255, 255),
            -1
        )

        cv2.putText(
            frame,
            f"{int((i + 1) / len(stages) * 100)}%",
            (610, 500),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        cv2.imshow(APP_NAME, frame)
        cv2.waitKey(380)


# =====================================================
# UI DRAWING
# =====================================================

def draw_glass(frame, x1, y1, x2, y2, alpha=0.36):
    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (x1, y1),
        (x2, y2),
        (12, 12, 18),
        -1
    )

    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


def draw_neon_rect(frame, x1, y1, x2, y2, color, thickness=2):
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    cv2.rectangle(frame, (x1 - 4, y1 - 4), (x2 + 4, y2 + 4), color, 1)


def draw_soft_circle(frame, x, y, color):
    cv2.circle(frame, (x, y), 36, color, 1)
    cv2.circle(frame, (x, y), 24, color, 2)
    cv2.circle(frame, (x, y), 10, color, -1)


def draw_line(frame, p1, p2, color, thickness=3):
    cv2.line(frame, p1, p2, color, thickness)


def add_trail(trail_list, x, y):
    trail_list.append((x, y, time.time()))

    if len(trail_list) > MAX_TRAIL_LENGTH:
        trail_list.pop(0)


def render_trail(frame, trail_list, color):
    if len(trail_list) < 2:
        return

    now = time.time()

    for i in range(1, len(trail_list)):
        x1, y1, _ = trail_list[i - 1]
        x2, y2, t2 = trail_list[i]

        age = now - t2

        if age > 1.0:
            continue

        thickness = max(1, int(8 * (1 - age)))
        cv2.line(frame, (x1, y1), (x2, y2), color, thickness)

    for x, y, t in trail_list:
        age = now - t

        if age > 1.0:
            continue

        radius = max(2, int(10 * (1 - age)))
        cv2.circle(frame, (x, y), radius, color, -1)


def draw_mode_chip(frame, x, y, text, color):
    width = 160 + len(text) * 5
    height = 38

    draw_glass(frame, x, y, x + width, y + height, alpha=0.45)
    cv2.rectangle(frame, (x, y), (x + width, y + height), color, 2)

    cv2.putText(
        frame,
        text,
        (x + 15, y + 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2
    )


def draw_mode_card(frame):
    if time.time() - mode_card_time > 1.35:
        return

    h, w, _ = frame.shape

    card_w = int(w * 0.52)
    card_h = int(h * 0.24)

    x1 = int((w - card_w) / 2)
    y1 = int((h - card_h) / 2)
    x2 = x1 + card_w
    y2 = y1 + card_h

    draw_glass(frame, x1, y1, x2, y2, alpha=0.62)
    draw_neon_rect(frame, x1, y1, x2, y2, (0, 255, 255), 2)

    cv2.putText(
        frame,
        mode_card_title,
        (x1 + 45, y1 + 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.1,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        mode_card_subtitle,
        (x1 + 45, y1 + 125),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        (0, 255, 255),
        2
    )


def draw_mode_dock(frame):
    h, w, _ = frame.shape

    modes = [
        ("MOUSE", not drawing_mode and not presentation_mode and not document_mode and not calibration_mode),
        ("WHITEBOARD", drawing_mode),
        ("PRESENT", presentation_mode),
        ("DOCUMENT", document_mode),
        ("CALIBRATE", calibration_mode)
    ]

    dock_w = 720
    dock_h = 58

    x1 = int((w - dock_w) / 2)
    y1 = h - 235
    x2 = x1 + dock_w
    y2 = y1 + dock_h

    draw_glass(frame, x1, y1, x2, y2, alpha=0.45)

    item_w = int(dock_w / len(modes))

    for i, (name, active) in enumerate(modes):
        ix1 = x1 + i * item_w + 8
        ix2 = ix1 + item_w - 16

        color = (0, 255, 255) if active else (120, 120, 120)

        if active:
            cv2.rectangle(frame, (ix1, y1 + 8), (ix2, y2 - 8), color, 2)

        cv2.putText(
            frame,
            name,
            (ix1 + 12, y1 + 37),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            color,
            2
        )


def draw_status_toast(frame):
    if time.time() - toast_time > 2.2:
        return

    h, w, _ = frame.shape

    box_w = min(760, 250 + len(toast_message) * 8)
    box_h = 55

    x1 = int((w - box_w) / 2)
    y1 = 150

    draw_glass(frame, x1, y1, x1 + box_w, y1 + box_h, alpha=0.60)

    cv2.rectangle(
        frame,
        (x1, y1),
        (x1 + box_w, y1 + box_h),
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        toast_message[:75],
        (x1 + 20, y1 + 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


def draw_color_palette(frame):
    start_x = 55
    y = 160

    cv2.putText(
        frame,
        "COLORS",
        (start_x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    x = start_x + 105

    for i, color in enumerate(brush_colors):
        box_x = x + i * 43
        thickness = 4 if i == color_index else 1

        cv2.rectangle(
            frame,
            (box_x, y - 23),
            (box_x + 30, y + 8),
            color,
            -1
        )

        cv2.rectangle(
            frame,
            (box_x, y - 23),
            (box_x + 30, y + 8),
            (255, 255, 255),
            thickness
        )

        cv2.putText(
            frame,
            str(i + 1),
            (box_x + 9, y + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (255, 255, 255),
            1
        )


def draw_control_box(frame):
    h, w, _ = frame.shape

    if calibrated_bounds:
        x1p, y1p, x2p, y2p = calibrated_bounds

        x1 = int(x1p * w / PROCESS_WIDTH)
        x2 = int(x2p * w / PROCESS_WIDTH)
        y1 = int(y1p * h / PROCESS_HEIGHT)
        y2 = int(y2p * h / PROCESS_HEIGHT)

        label = "CALIBRATED AREA"
        color = (0, 255, 0)
    else:
        x1 = int(CONTROL_MARGIN_X * w / PROCESS_WIDTH)
        x2 = int((PROCESS_WIDTH - CONTROL_MARGIN_X) * w / PROCESS_WIDTH)
        y1 = int(CONTROL_MARGIN_Y * h / PROCESS_HEIGHT)
        y2 = int((PROCESS_HEIGHT - CONTROL_MARGIN_Y) * h / PROCESS_HEIGHT)

        label = "EASY CONTROL AREA"
        color = (0, 255, 255)

    if drawing_mode:
        label = "BLACK WHITEBOARD"
        color = (255, 0, 255)
    elif presentation_mode:
        label = "PRESENTATION AREA"
        color = (0, 255, 255)
    elif document_mode:
        label = "DOCUMENT AREA"
        color = (0, 255, 0)
    elif calibration_mode:
        label = "CALIBRATION AREA"
        color = (0, 165, 255)

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    cv2.putText(
        frame,
        label,
        (x1 + 10, max(30, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2
    )


def draw_hand_lines(frame, hand, display_w, display_h, color):
    connections = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (0, 9), (9, 10), (10, 11), (11, 12),
        (0, 13), (13, 14), (14, 15), (15, 16),
        (0, 17), (17, 18), (18, 19), (19, 20),
        (5, 9), (9, 13), (13, 17),
        (5, 13), (9, 17),
        (4, 8), (8, 12), (12, 16), (16, 20)
    ]

    for a, b in connections:
        p1 = landmark_point(hand, a, display_w, display_h)
        p2 = landmark_point(hand, b, display_w, display_h)
        cv2.line(frame, p1, p2, color, 5)

    for a, b in connections:
        p1 = landmark_point(hand, a, display_w, display_h)
        p2 = landmark_point(hand, b, display_w, display_h)
        cv2.line(frame, p1, p2, (255, 255, 255), 2)

    for i in range(21):
        x, y = landmark_point(hand, i, display_w, display_h)
        cv2.circle(frame, (x, y), 6, color, -1)
        cv2.circle(frame, (x, y), 10, (255, 255, 255), 1)


def draw_tutorial(frame):
    h, w, _ = frame.shape

    panel_w = int(w * 0.84)
    panel_h = int(h * 0.84)

    x1 = int((w - panel_w) / 2)
    y1 = int((h - panel_h) / 2)
    x2 = x1 + panel_w
    y2 = y1 + panel_h

    draw_glass(frame, x1, y1, x2, y2, alpha=0.76)
    draw_neon_rect(frame, x1, y1, x2, y2, (0, 255, 255), 2)

    cv2.putText(
        frame,
        "AIRBOARD PRO TUTORIAL",
        (x1 + 40, y1 + 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.1,
        (255, 255, 255),
        2
    )

    lines = [
        "NORMAL MOUSE MODE",
        "Left index = move cursor | Left index + middle = scroll",
        "Right thumb + middle = left click",
        "Right thumb + index = right click",
        "Right thumb + index double tap = double click",
        "",
        "WHITEBOARD MODE",
        "Black screen only. No camera preview.",
        "Left index-only gesture = draw",
        "Right index-only gesture = erase",
        "Full palm = pointer moves only, no writing",
        "Z = undo | Y = redo | C = clear | M = save",
        "[ / ] = brush and eraser size | 1-8/N = color",
        "A = new page | Left/Right arrows = change page",
        "",
        "PRESENTATION MODE",
        "P = enter/exit | Swipe left/right = previous/next slide",
        "Left index = laser/draw | Right index = erase",
        "",
        "DOCUMENT MODE",
        "O = enter/exit | Left index up/down = scroll",
        "Right thumb+index top = zoom in | bottom = zoom out",
        "",
        "EXTRA",
        "F1 low | F2 balanced | F3 quality | X dwell | L lock | H hide UI | Q quit"
    ]

    start_y = y1 + 100

    for i, line in enumerate(lines):
        if line in [
            "NORMAL MOUSE MODE",
            "WHITEBOARD MODE",
            "PRESENTATION MODE",
            "DOCUMENT MODE",
            "EXTRA"
        ]:
            color = (0, 255, 255)
            scale = 0.60
            thickness = 2
        else:
            color = (255, 255, 255)
            scale = 0.47
            thickness = 1

        cv2.putText(
            frame,
            line,
            (x1 + 45, start_y + i * 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness
        )


def draw_calibration_card(frame, move_hand, display_w, display_h):
    h, w, _ = frame.shape

    panel_w = int(w * 0.68)
    panel_h = int(h * 0.45)

    x1 = int((w - panel_w) / 2)
    y1 = int((h - panel_h) / 2)
    x2 = x1 + panel_w
    y2 = y1 + panel_h

    draw_glass(frame, x1, y1, x2, y2, alpha=0.72)
    draw_neon_rect(frame, x1, y1, x2, y2, (0, 165, 255), 2)

    step_name = calibration_steps[calibration_step]

    cv2.putText(
        frame,
        "SMART CALIBRATION",
        (x1 + 40, y1 + 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.1,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Step {calibration_step + 1} of {len(calibration_steps)}",
        (x1 + 40, y1 + 105),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Point your move-hand index finger to: {step_name}",
        (x1 + 40, y1 + 155),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Press SPACE to confirm   |   Press ESC to cancel",
        (x1 + 40, y1 + 210),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 0),
        2
    )

    dot_x = x1 + 45
    dot_y = y2 - 55

    for i in range(len(calibration_steps)):
        color = (0, 255, 255) if i <= calibration_step else (80, 80, 80)
        cv2.circle(frame, (dot_x + i * 45, dot_y), 12, color, -1)

    if move_hand:
        ix, iy = landmark_point(move_hand, 8, display_w, display_h)
        cv2.circle(frame, (ix, iy), 35, (0, 165, 255), 3)
        cv2.circle(frame, (ix, iy), 8, (0, 165, 255), -1)


def draw_ui(frame):
    if not show_ui:
        return

    h, w, _ = frame.shape

    top_height = 190 if drawing_mode or presentation_mode else 145

    draw_glass(frame, 25, 25, w - 25, top_height, alpha=0.40)

    cv2.putText(
        frame,
        "AIRBOARD PRO",
        (55, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.05,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Touchless PC + Whiteboard + Presentation Controller",
        (55, 95),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 255),
        2
    )

    mode_color = (0, 255, 255)

    if active_mode in ["MOVE", "SCROLL", "DOCUMENT SCROLL"]:
        mode_color = (0, 255, 0)
    elif active_mode in ["LEFT CLICK", "RIGHT CLICK", "DOUBLE CLICK", "DWELL CLICK"]:
        mode_color = (255, 255, 0)
    elif active_mode in ["DRAW", "LASER", "ANNOTATE"]:
        mode_color = brush_color
    elif active_mode == "ERASE":
        mode_color = (0, 0, 255)
    elif active_mode in ["CALIBRATION", "NEXT SLIDE", "PREVIOUS SLIDE"]:
        mode_color = (0, 165, 255)

    draw_mode_chip(frame, 55, 112, f"MODE: {get_current_mode_name()}", mode_color)

    cv2.putText(
        frame,
        status_message[:80],
        (270, 138),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.56,
        (255, 255, 0),
        2
    )

    if drawing_mode or presentation_mode:
        cv2.putText(
            frame,
            f"BRUSH: {brush_size}",
            (w - 420, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"COLOR: {color_names[color_index]}",
            (w - 420, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            brush_color,
            2
        )

        cv2.putText(
            frame,
            f"PAGE: {current_page_index + 1}/{max(1, len(whiteboard_pages))}",
            (w - 420, 135),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.56,
            (0, 255, 255),
            2
        )

        draw_color_palette(frame)

    else:
        cv2.putText(
            frame,
            f"MOVE HAND: {move_hand_setting}",
            (w - 390, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"CLICK HAND: {click_hand_setting}",
            (w - 390, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (255, 255, 255),
            2
        )

    draw_mode_dock(frame)

    draw_glass(frame, 25, h - 170, w - 25, h - 25, alpha=0.40)

    if calibration_mode:
        line1 = "K = Cancel calibration | SPACE = Confirm point | ESC = Cancel"
        line2 = "Move your index finger to the target area shown in the center card."

    elif drawing_mode:
        line1 = "D = Exit | Index-only = Write/Erase | Full palm = No writing | Z Undo | Y Redo | C Clear | M Save"
        line2 = "[ ] Size | 1-8/N Color | A New Page | Arrow keys Pages | T Tutorial | H Hide UI | Q Quit"

    elif presentation_mode:
        line1 = "P = Exit | Swipe left/right = Slides | Left index = Laser/Draw | Right index = Erase"
        line2 = "Z/Y Undo/Redo | C Clear | M Save | [ ] Size | 1-8/N Color | Q Quit"

    elif document_mode:
        line1 = "O = Exit Document Mode | Left index up/down = Scroll | Right thumb+index = Zoom"
        line2 = "T = Tutorial | H = Hide UI | Q = Quit"

    else:
        dwell_text = "ON" if dwell_click_mode else "OFF"
        cal_text = "ON" if calibrated_bounds else "OFF"
        lock_text = "ON" if gesture_locked else "OFF"
        line1 = f"D Whiteboard | P Presentation | O Document | K Calibration({cal_text}) | X Dwell({dwell_text}) | L Lock({lock_text})"
        line2 = "F1 Low | F2 Balanced | F3 Quality | T Tutorial | H Hide UI | S Swap | R Reset | Q Quit"

    cv2.putText(
        frame,
        line1,
        (55, h - 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.54,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        line2,
        (55, h - 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.54,
        (0, 255, 255),
        2
    )

    draw_status_toast(frame)
    draw_mode_card(frame)


# =====================================================
# WHITEBOARD BACKGROUNDS / PAGES
# =====================================================

def create_background(frame):
    h, w, _ = frame.shape

    if drawing_mode:
        bg = np.zeros_like(frame)
        bg[:] = (0, 0, 0)
        return bg

    if board_background == "camera":
        return frame.copy()

    if board_background == "blackboard":
        bg = np.zeros_like(frame)
        bg[:] = (25, 45, 35)
        return bg

    if board_background == "whiteboard":
        bg = np.zeros_like(frame)
        bg[:] = (245, 245, 245)
        return bg

    if board_background == "dark":
        bg = np.zeros_like(frame)
        bg[:] = (18, 18, 25)
        return bg

    if board_background == "grid":
        bg = np.zeros_like(frame)
        bg[:] = (245, 245, 245)

        for x in range(0, w, 40):
            cv2.line(bg, (x, 0), (x, h), (210, 210, 210), 1)

        for y in range(0, h, 40):
            cv2.line(bg, (0, y), (w, y), (210, 210, 210), 1)

        return bg

    return frame.copy()


def ensure_page_exists(frame):
    global drawing_canvas, whiteboard_pages, current_page_index

    if drawing_canvas is None:
        drawing_canvas = np.zeros_like(frame)

    if drawing_canvas.shape != frame.shape:
        drawing_canvas = np.zeros_like(frame)
        whiteboard_pages.clear()
        current_page_index = 0

    if len(whiteboard_pages) == 0:
        whiteboard_pages.append({
            "canvas": drawing_canvas.copy(),
            "strokes": [],
            "redo": []
        })


def save_current_page():
    global whiteboard_pages

    if len(whiteboard_pages) == 0:
        return

    finish_draw_strokes()

    whiteboard_pages[current_page_index]["canvas"] = drawing_canvas.copy()
    whiteboard_pages[current_page_index]["strokes"] = strokes.copy()
    whiteboard_pages[current_page_index]["redo"] = redo_stack.copy()


def load_current_page():
    global drawing_canvas, strokes, redo_stack

    if len(whiteboard_pages) == 0:
        return

    page = whiteboard_pages[current_page_index]
    drawing_canvas = page["canvas"].copy()
    strokes = page["strokes"].copy()
    redo_stack = page["redo"].copy()


def new_page(frame):
    global whiteboard_pages, current_page_index, drawing_canvas, strokes, redo_stack
    global current_draw_stroke, current_erase_stroke

    save_current_page()

    drawing_canvas = np.zeros_like(frame)
    strokes = []
    redo_stack = []
    current_draw_stroke = None
    current_erase_stroke = None

    whiteboard_pages.append({
        "canvas": drawing_canvas.copy(),
        "strokes": [],
        "redo": []
    })

    current_page_index = len(whiteboard_pages) - 1

    set_status(f"New page created: {current_page_index + 1}")
    show_mode_card("NEW WHITEBOARD PAGE", f"Page {current_page_index + 1}")


def next_page():
    global current_page_index

    if len(whiteboard_pages) <= 1:
        set_status("Only one page")
        return

    save_current_page()

    current_page_index = (current_page_index + 1) % len(whiteboard_pages)
    load_current_page()

    set_status(f"Page {current_page_index + 1}")
    show_mode_card("WHITEBOARD PAGE", f"Page {current_page_index + 1}")


def previous_page():
    global current_page_index

    if len(whiteboard_pages) <= 1:
        set_status("Only one page")
        return

    save_current_page()

    current_page_index = (current_page_index - 1) % len(whiteboard_pages)
    load_current_page()

    set_status(f"Page {current_page_index + 1}")
    show_mode_card("WHITEBOARD PAGE", f"Page {current_page_index + 1}")


def change_background():
    global board_background

    index = board_backgrounds.index(board_background)
    board_background = board_backgrounds[(index + 1) % len(board_backgrounds)]

    set_status(f"Background: {board_background}")
    show_mode_card("BACKGROUND CHANGED", board_background.upper())


# =====================================================
# DRAWING HELPERS
# =====================================================

def blend_drawing(frame, canvas):
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)

    mask_inv = cv2.bitwise_not(mask)

    frame_bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
    drawing_fg = cv2.bitwise_and(canvas, canvas, mask=mask)

    return cv2.add(frame_bg, drawing_fg)


def rebuild_canvas():
    global drawing_canvas

    if drawing_canvas is None:
        return

    drawing_canvas[:] = 0

    for stroke in strokes:
        points = stroke["points"]
        color = stroke["color"]
        size = stroke["size"]

        if len(points) < 2:
            continue

        for i in range(1, len(points)):
            cv2.line(drawing_canvas, points[i - 1], points[i], color, size)


def finish_draw_strokes():
    global current_draw_stroke, current_erase_stroke

    if current_draw_stroke is not None:
        if len(current_draw_stroke["points"]) > 1:
            strokes.append(current_draw_stroke)
            redo_stack.clear()

        current_draw_stroke = None

    if current_erase_stroke is not None:
        if len(current_erase_stroke["points"]) > 1:
            strokes.append(current_erase_stroke)
            redo_stack.clear()

        current_erase_stroke = None


def undo_stroke():
    finish_draw_strokes()

    if len(strokes) > 0:
        redo_stack.append(strokes.pop())
        rebuild_canvas()
        set_status("Undo")
    else:
        set_status("Nothing to undo")


def redo_stroke():
    finish_draw_strokes()

    if len(redo_stack) > 0:
        strokes.append(redo_stack.pop())
        rebuild_canvas()
        set_status("Redo")
    else:
        set_status("Nothing to redo")


def clear_drawing():
    global drawing_canvas
    global current_draw_stroke, current_erase_stroke

    if drawing_canvas is not None:
        drawing_canvas[:] = 0

    strokes.clear()
    redo_stack.clear()

    current_draw_stroke = None
    current_erase_stroke = None

    set_status("Drawing cleared")


def save_screenshot(frame):
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    filename = f"airboard_{int(time.time())}.png"
    path = os.path.join(SAVE_FOLDER, filename)

    cv2.imwrite(path, frame)

    set_status(f"Saved: {path}")


def handle_drawing_tools(frame, left_hand, right_hand, display_w, display_h):
    global draw_prev_x, draw_prev_y, erase_prev_x, erase_prev_y
    global current_draw_stroke, current_erase_stroke, active_mode

    # LEFT HAND = DRAW ONLY WITH INDEX-ONLY GESTURE
    if left_hand:
        draw_hand_lines(frame, left_hand, display_w, display_h, brush_color)

        index = left_hand.landmark[8]

        x = int(index.x * display_w)
        y = int(index.y * display_h)

        draw_soft_circle(frame, x, y, brush_color)
        add_trail(drawing_trail, x, y)

        if is_index_only(left_hand):
            if current_draw_stroke is None:
                current_draw_stroke = {
                    "points": [],
                    "color": brush_color,
                    "size": brush_size
                }

            current_draw_stroke["points"].append((x, y))

            if draw_prev_x is None or draw_prev_y is None:
                draw_prev_x = x
                draw_prev_y = y

            cv2.line(
                drawing_canvas,
                (draw_prev_x, draw_prev_y),
                (x, y),
                brush_color,
                brush_size
            )

            draw_prev_x = x
            draw_prev_y = y

            active_mode = "DRAW"

        else:
            if current_draw_stroke is not None:
                if len(current_draw_stroke["points"]) > 1:
                    strokes.append(current_draw_stroke)
                    redo_stack.clear()

                current_draw_stroke = None

            draw_prev_x = None
            draw_prev_y = None

            if active_mode == "READY":
                active_mode = "POINTER"

    else:
        if current_draw_stroke is not None:
            if len(current_draw_stroke["points"]) > 1:
                strokes.append(current_draw_stroke)
                redo_stack.clear()

            current_draw_stroke = None

        draw_prev_x = None
        draw_prev_y = None

    # RIGHT HAND = ERASE ONLY WITH INDEX-ONLY GESTURE
    if right_hand:
        draw_hand_lines(frame, right_hand, display_w, display_h, (0, 0, 255))

        index = right_hand.landmark[8]

        x = int(index.x * display_w)
        y = int(index.y * display_h)

        cv2.circle(frame, (x, y), brush_size + 16, (0, 0, 255), 2)
        cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)

        add_trail(click_trail, x, y)

        if is_index_only(right_hand):
            if current_erase_stroke is None:
                current_erase_stroke = {
                    "points": [],
                    "color": (0, 0, 0),
                    "size": brush_size + 24
                }

            current_erase_stroke["points"].append((x, y))

            if erase_prev_x is None or erase_prev_y is None:
                erase_prev_x = x
                erase_prev_y = y

            cv2.line(
                drawing_canvas,
                (erase_prev_x, erase_prev_y),
                (x, y),
                (0, 0, 0),
                brush_size + 24
            )

            erase_prev_x = x
            erase_prev_y = y

            active_mode = "ERASE"

        else:
            if current_erase_stroke is not None:
                if len(current_erase_stroke["points"]) > 1:
                    strokes.append(current_erase_stroke)
                    redo_stack.clear()

                current_erase_stroke = None

            erase_prev_x = None
            erase_prev_y = None

    else:
        if current_erase_stroke is not None:
            if len(current_erase_stroke["points"]) > 1:
                strokes.append(current_erase_stroke)
                redo_stack.clear()

            current_erase_stroke = None

        erase_prev_x = None
        erase_prev_y = None


# =====================================================
# MODE TOGGLES
# =====================================================

def reset_all():
    global move_hand_setting, click_hand_setting
    global prev_x, prev_y
    global last_left_click, last_right_click, last_double_click
    global calibrated_bounds

    move_hand_setting = "Left"
    click_hand_setting = "Right"

    prev_x = screen_w // 2
    prev_y = screen_h // 2

    last_left_click = 0
    last_right_click = 0
    last_double_click = 0

    calibrated_bounds = None

    set_status("Controls reset")


def swap_hands():
    global move_hand_setting, click_hand_setting

    if move_hand_setting == "Left":
        move_hand_setting = "Right"
        click_hand_setting = "Left"
    else:
        move_hand_setting = "Left"
        click_hand_setting = "Right"

    set_status("Hands swapped")


def toggle_drawing_mode():
    global drawing_mode, presentation_mode, document_mode, calibration_mode
    global draw_prev_x, draw_prev_y, erase_prev_x, erase_prev_y

    drawing_mode = not drawing_mode

    if drawing_mode:
        presentation_mode = False
        document_mode = False
        calibration_mode = False

        set_status("Black Whiteboard Mode ON")
        show_mode_card("BLACK WHITEBOARD", "Index-only to write • Full palm will not write")
    else:
        set_status("Whiteboard Mode OFF")
        show_mode_card("MOUSE MODE", "Cursor control restored")

    draw_prev_x = None
    draw_prev_y = None
    erase_prev_x = None
    erase_prev_y = None

    finish_draw_strokes()


def toggle_presentation_mode():
    global presentation_mode, drawing_mode, document_mode, calibration_mode
    global draw_prev_x, draw_prev_y, erase_prev_x, erase_prev_y
    global swipe_start_x

    presentation_mode = not presentation_mode

    if presentation_mode:
        drawing_mode = False
        document_mode = False
        calibration_mode = False

        set_status("Presentation Mode ON")
        show_mode_card("PRESENTATION MODE", "Swipe slides • Laser pointer • Annotations")
    else:
        set_status("Presentation Mode OFF")
        show_mode_card("MOUSE MODE", "Cursor control restored")

    draw_prev_x = None
    draw_prev_y = None
    erase_prev_x = None
    erase_prev_y = None
    swipe_start_x = None

    finish_draw_strokes()


def toggle_document_mode():
    global document_mode, drawing_mode, presentation_mode, calibration_mode

    document_mode = not document_mode

    if document_mode:
        drawing_mode = False
        presentation_mode = False
        calibration_mode = False

        set_status("Document Mode ON")
        show_mode_card("DOCUMENT MODE", "Scroll and zoom documents touchlessly")
    else:
        set_status("Document Mode OFF")
        show_mode_card("MOUSE MODE", "Cursor control restored")


def start_calibration():
    global calibration_mode, drawing_mode, presentation_mode, document_mode
    global calibration_points, calibration_step

    calibration_mode = True
    drawing_mode = False
    presentation_mode = False
    document_mode = False

    calibration_points = []
    calibration_step = 0

    set_status("Calibration started")
    show_mode_card("SMART CALIBRATION", "Teach the app your hand control area")


def cancel_calibration():
    global calibration_mode, calibration_points, calibration_step

    calibration_mode = False
    calibration_points = []
    calibration_step = 0

    set_status("Calibration cancelled")
    show_mode_card("CALIBRATION CANCELLED", "Back to normal controls")


def confirm_calibration_point(move_hand):
    global calibration_mode, calibration_points, calibration_step, calibrated_bounds

    if not move_hand:
        set_status("No move hand detected")
        return

    x, y = process_point(move_hand, 8)

    calibration_points.append((x, y))
    calibration_step += 1

    if calibration_step >= len(calibration_steps):
        xs = [p[0] for p in calibration_points[:4]]
        ys = [p[1] for p in calibration_points[:4]]

        x_min = clamp(min(xs), 5, PROCESS_WIDTH - 20)
        x_max = clamp(max(xs), 20, PROCESS_WIDTH - 5)

        y_min = clamp(min(ys), 5, PROCESS_HEIGHT - 20)
        y_max = clamp(max(ys), 20, PROCESS_HEIGHT - 5)

        if x_max - x_min < 80 or y_max - y_min < 60:
            calibrated_bounds = None

            set_status("Calibration failed: area too small")
            show_mode_card("CALIBRATION FAILED", "Try using a bigger hand area")
        else:
            calibrated_bounds = (x_min, y_min, x_max, y_max)

            set_status("Calibration complete")
            show_mode_card("CALIBRATION COMPLETE", "Cursor now fits your hand movement")

        calibration_mode = False
        calibration_points = []
        calibration_step = 0
    else:
        set_status(f"Captured {calibration_steps[calibration_step - 1]}")


def toggle_tutorial():
    global tutorial_mode
    tutorial_mode = not tutorial_mode


def toggle_ui():
    global show_ui
    show_ui = not show_ui


def toggle_dwell_click():
    global dwell_click_mode
    dwell_click_mode = not dwell_click_mode
    set_status("Dwell click ON" if dwell_click_mode else "Dwell click OFF")


def toggle_lock():
    global gesture_locked

    gesture_locked = not gesture_locked

    set_status("Gesture lock ON" if gesture_locked else "Gesture lock OFF")
    show_mode_card("GESTURE LOCK", "Controls paused" if gesture_locked else "Controls resumed")


def next_color():
    global color_index, brush_color

    color_index = (color_index + 1) % len(brush_colors)
    brush_color = brush_colors[color_index]

    set_status(f"Color: {color_names[color_index]}")


def set_color(index):
    global color_index, brush_color

    if 0 <= index < len(brush_colors):
        color_index = index
        brush_color = brush_colors[color_index]

        set_status(f"Color: {color_names[color_index]}")


def change_brush_size(amount):
    global brush_size

    brush_size = clamp(brush_size + amount, MIN_BRUSH_SIZE, MAX_BRUSH_SIZE)
    set_status(f"Brush and eraser size: {brush_size}")


def set_runtime_performance(mode):
    apply_performance_mode(mode)
    set_status(f"Performance mode: {mode}")
    show_mode_card("PERFORMANCE MODE", mode.upper())


# =====================================================
# CONTROL HANDLERS
# =====================================================

def get_mapping_bounds():
    if calibrated_bounds:
        return calibrated_bounds

    return (
        CONTROL_MARGIN_X,
        CONTROL_MARGIN_Y,
        PROCESS_WIDTH - CONTROL_MARGIN_X,
        PROCESS_HEIGHT - CONTROL_MARGIN_Y
    )


def update_dwell_click(curr_x, curr_y, now):
    global dwell_start_time, dwell_last_x, dwell_last_y
    global dwell_clicked, last_left_click, active_mode

    if not dwell_click_mode:
        return

    if dwell_last_x is None:
        dwell_last_x = curr_x
        dwell_last_y = curr_y
        dwell_start_time = now
        dwell_clicked = False
        return

    movement = math.hypot(curr_x - dwell_last_x, curr_y - dwell_last_y)

    if movement < DWELL_RADIUS:
        progress = now - dwell_start_time

        if not dwell_clicked and progress > DWELL_SECONDS:
            pyautogui.click()

            dwell_clicked = True
            last_left_click = now
            active_mode = "DWELL CLICK"

            set_status("Dwell click")
    else:
        dwell_last_x = curr_x
        dwell_last_y = curr_y
        dwell_start_time = now
        dwell_clicked = False


def handle_presentation_swipe(left_hand, display_w, now):
    global swipe_start_x, swipe_start_time, last_slide_action
    global active_mode

    if not left_hand:
        swipe_start_x = None
        return

    index = left_hand.landmark[8]
    x = int(index.x * display_w)

    if swipe_start_x is None:
        swipe_start_x = x
        swipe_start_time = now
        return

    dx = x - swipe_start_x
    dt = now - swipe_start_time

    if dt < 0.7 and now - last_slide_action > slide_cooldown:
        if dx > swipe_distance:
            pyautogui.press("right")

            last_slide_action = now
            swipe_start_x = None
            active_mode = "NEXT SLIDE"

            set_status("Next slide")

        elif dx < -swipe_distance:
            pyautogui.press("left")

            last_slide_action = now
            swipe_start_x = None
            active_mode = "PREVIOUS SLIDE"

            set_status("Previous slide")

    if dt > 0.7:
        swipe_start_x = x
        swipe_start_time = now


def handle_document_mode(frame, move_hand, click_hand, display_w, display_h, now):
    global active_mode, last_zoom_action

    if move_hand:
        draw_hand_lines(frame, move_hand, display_w, display_h, (0, 255, 0))

        index = move_hand.landmark[8]

        x = int(index.x * display_w)
        y = int(index.y * display_h)

        draw_soft_circle(frame, x, y, (0, 255, 0))
        add_trail(move_trail, x, y)

        center_y = display_h // 2
        scroll_power = int((y - center_y) / 12)

        if abs(scroll_power) > 2:
            pyautogui.scroll(-scroll_power)
            active_mode = "DOCUMENT SCROLL"

    if click_hand:
        draw_hand_lines(frame, click_hand, display_w, display_h, (0, 0, 255))

        thumb = click_hand.landmark[4]
        index = click_hand.landmark[8]

        pinch_d = dist(thumb, index)

        ix = int(index.x * display_w)
        iy = int(index.y * display_h)

        cv2.circle(frame, (ix, iy), 18, (0, 0, 255), 2)
        add_trail(click_trail, ix, iy)

        if pinch_d < 18 and now - last_zoom_action > zoom_cooldown:
            if iy < display_h // 2:
                pyautogui.hotkey("ctrl", "+")
                set_status("Zoom in")
            else:
                pyautogui.hotkey("ctrl", "-")
                set_status("Zoom out")

            active_mode = "ZOOM"
            last_zoom_action = now


def handle_mouse_clicks(frame, click_hand, display_w, display_h, now):
    global last_left_click, last_right_click, last_double_click
    global last_index_thumb_tap
    global right_pinch_active, middle_pinch_active
    global active_mode

    thumb = click_hand.landmark[4]
    index = click_hand.landmark[8]
    middle = click_hand.landmark[12]

    ix = int(index.x * display_w)
    iy = int(index.y * display_h)

    tx = int(thumb.x * display_w)
    ty = int(thumb.y * display_h)

    mx = int(middle.x * display_w)
    my = int(middle.y * display_h)

    draw_soft_circle(frame, ix, iy, (0, 0, 255))
    add_trail(click_trail, ix, iy)

    index_thumb_d = dist(thumb, index)
    middle_thumb_d = dist(thumb, middle)

    if middle_thumb_d < 18:
        if not middle_pinch_active and now - last_left_click > click_delay:
            pyautogui.click()

            last_left_click = now
            active_mode = "LEFT CLICK"

            set_status("Left click")
            draw_line(frame, (tx, ty), (mx, my), (255, 255, 0), 5)

        middle_pinch_active = True
    else:
        middle_pinch_active = False

    if index_thumb_d < 18:
        if not right_pinch_active and now - last_right_click > 0.18:
            if now - last_index_thumb_tap < double_tap_window:
                pyautogui.doubleClick()

                last_double_click = now
                last_index_thumb_tap = 0
                active_mode = "DOUBLE CLICK"

                set_status("Double click")
                draw_line(frame, (tx, ty), (ix, iy), (255, 0, 255), 5)
            else:
                pyautogui.rightClick()

                last_right_click = now
                last_index_thumb_tap = now
                active_mode = "RIGHT CLICK"

                set_status("Right click")
                draw_line(frame, (tx, ty), (ix, iy), (255, 255, 0), 5)

        right_pinch_active = True
    else:
        right_pinch_active = False


# =====================================================
# STARTUP
# =====================================================

home_action = draw_home_screen()

if home_action == "exit":
    cv2.destroyAllWindows()
    sys.exit()

if home_action == "tutorial":
    tutorial_mode = True

draw_loading_screen()

# =====================================================
# CAMERA SETUP
# =====================================================

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

# =====================================================
# MAIN LOOP
# =====================================================

while True:
    ok, frame = cap.read()

    if not ok:
        break

    frame = cv2.flip(frame, 1)

    display_h, display_w, _ = frame.shape

    ensure_page_exists(frame)

    small = cv2.resize(frame, (PROCESS_WIDTH, PROCESS_HEIGHT), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    frame_count += 1

    if frame_count % PROCESS_EVERY_N_FRAMES == 0:
        last_results = hands.process(rgb)

    results = last_results

    detected = {}

    if results and results.multi_hand_landmarks and results.multi_handedness:
        for i, handedness in enumerate(results.multi_handedness):
            label = handedness.classification[0].label
            detected[label] = results.multi_hand_landmarks[i]

    move_hand = detected.get(move_hand_setting)
    click_hand = detected.get(click_hand_setting)

    left_hand = detected.get("Left")
    right_hand = detected.get("Right")

    now = time.time()
    active_mode = "READY"

    base_frame = create_background(frame)

    draw_control_box(base_frame)

    render_trail(base_frame, move_trail, (0, 255, 0))
    render_trail(base_frame, click_trail, (0, 0, 255))
    render_trail(base_frame, drawing_trail, brush_color)

    if gesture_locked:
        active_mode = "LOCKED"

    elif calibration_mode:
        active_mode = "CALIBRATION"

        if move_hand:
            draw_hand_lines(base_frame, move_hand, display_w, display_h, (0, 165, 255))

        draw_calibration_card(base_frame, move_hand, display_w, display_h)

    elif drawing_mode:
        handle_drawing_tools(base_frame, left_hand, right_hand, display_w, display_h)
        base_frame = blend_drawing(base_frame, drawing_canvas)

    elif presentation_mode:
        handle_presentation_swipe(left_hand, display_w, now)
        handle_drawing_tools(base_frame, left_hand, right_hand, display_w, display_h)

        if left_hand:
            index = left_hand.landmark[8]

            lx = int(index.x * display_w)
            ly = int(index.y * display_h)

            cv2.circle(base_frame, (lx, ly), 22, brush_color, 3)
            cv2.circle(base_frame, (lx, ly), 6, brush_color, -1)

            add_trail(drawing_trail, lx, ly)

            if active_mode == "READY":
                active_mode = "LASER"

        base_frame = blend_drawing(base_frame, drawing_canvas)

    elif document_mode:
        handle_document_mode(base_frame, move_hand, click_hand, display_w, display_h, now)

    else:
        finish_draw_strokes()

        if move_hand:
            draw_hand_lines(base_frame, move_hand, display_w, display_h, (0, 255, 0))

        if click_hand:
            draw_hand_lines(base_frame, click_hand, display_w, display_h, (0, 0, 255))

        if move_hand:
            index = move_hand.landmark[8]
            middle = move_hand.landmark[12]

            ix = int(index.x * PROCESS_WIDTH)
            iy = int(index.y * PROCESS_HEIGHT)

            mx = int(middle.x * PROCESS_WIDTH)
            my = int(middle.y * PROCESS_HEIGHT)

            draw_ix = int(index.x * display_w)
            draw_iy = int(index.y * display_h)

            draw_mx = int(middle.x * display_w)
            draw_my = int(middle.y * display_h)

            draw_soft_circle(base_frame, draw_ix, draw_iy, (0, 255, 0))
            add_trail(move_trail, draw_ix, draw_iy)

            x_min, y_min, x_max, y_max = get_mapping_bounds()

            ix_clamped = clamp(ix, x_min, x_max)
            iy_clamped = clamp(iy, y_min, y_max)

            target_x = np.interp(ix_clamped, (x_min, x_max), (0, screen_w))
            target_y = np.interp(iy_clamped, (y_min, y_max), (0, screen_h))

            dx = target_x - prev_x
            dy = target_y - prev_y

            if abs(dx) < dead_zone:
                dx = 0

            if abs(dy) < dead_zone:
                dy = 0

            curr_x = prev_x + dx / smoothening
            curr_y = prev_y + dy / smoothening

            curr_x = clamp(curr_x, 0, screen_w - 1)
            curr_y = clamp(curr_y, 0, screen_h - 1)

            pyautogui.moveTo(curr_x, curr_y)

            prev_x = curr_x
            prev_y = curr_y

            active_mode = "MOVE"

            update_dwell_click(curr_x, curr_y, now)

            scroll_distance = math.hypot(mx - ix, my - iy)

            if scroll_distance < 24:
                draw_line(base_frame, (draw_ix, draw_iy), (draw_mx, draw_my), (0, 255, 255), 5)

                center_y = PROCESS_HEIGHT // 2
                scroll_power = int((iy - center_y) / scroll_sensitivity)

                if scroll_power != 0:
                    pyautogui.scroll(-scroll_power)

                active_mode = "SCROLL"

        if click_hand:
            handle_mouse_clicks(base_frame, click_hand, display_w, display_h, now)

    draw_ui(base_frame)

    if tutorial_mode:
        draw_tutorial(base_frame)

    cv2.imshow(APP_NAME, base_frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    elif key == ord("d"):
        toggle_drawing_mode()

    elif key == ord("p"):
        toggle_presentation_mode()

    elif key == ord("o"):
        toggle_document_mode()

    elif key == ord("k"):
        if calibration_mode:
            cancel_calibration()
        else:
            start_calibration()

    elif key == 32:
        if calibration_mode:
            confirm_calibration_point(move_hand)

    elif key == 27:
        if calibration_mode:
            cancel_calibration()

    elif key == ord("t"):
        toggle_tutorial()

    elif key == ord("h"):
        toggle_ui()

    elif key == ord("x"):
        toggle_dwell_click()

    elif key == ord("l"):
        toggle_lock()

    elif key == ord("s"):
        if not drawing_mode and not presentation_mode and not document_mode and not calibration_mode:
            swap_hands()

    elif key == ord("r"):
        if not drawing_mode and not presentation_mode and not document_mode and not calibration_mode:
            reset_all()

    elif key == ord("z"):
        if drawing_mode or presentation_mode:
            undo_stroke()

    elif key == ord("y"):
        if drawing_mode or presentation_mode:
            redo_stroke()

    elif key == ord("c"):
        if drawing_mode or presentation_mode:
            clear_drawing()

    elif key == ord("m"):
        save_screenshot(base_frame)

    elif key == ord("n"):
        if drawing_mode or presentation_mode:
            next_color()

    elif key == ord("["):
        if drawing_mode or presentation_mode:
            change_brush_size(-4)

    elif key == ord("]"):
        if drawing_mode or presentation_mode:
            change_brush_size(4)

    elif key == ord("a"):
        if drawing_mode:
            new_page(base_frame)

    elif key == ord("b"):
        if drawing_mode:
            change_background()

    elif key == 81:
        if drawing_mode:
            previous_page()

    elif key == 83:
        if drawing_mode:
            next_page()

    elif key == 0:
        set_runtime_performance("low")

    elif key == 1:
        set_runtime_performance("balanced")

    elif key == 2:
        set_runtime_performance("quality")

    elif key in [
        ord("1"), ord("2"), ord("3"), ord("4"),
        ord("5"), ord("6"), ord("7"), ord("8")
    ]:
        if drawing_mode or presentation_mode:
            set_color(int(chr(key)) - 1)

finish_draw_strokes()
save_current_page()
save_settings()

cap.release()
cv2.destroyAllWindows()