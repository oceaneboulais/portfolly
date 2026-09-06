#!/usr/bin/env python3
"""
Chroma-key (blue screen) replacement for iPhone-shot video.

Removes a blue-screen background from an input video and composites the
foreground subject over a second "background" video, matching real-time
playback speed even if the two clips have different resolutions, frame
rates, or durations (the background is looped/frozen as needed).

Designed for 4K/60fps clips (or any resolution/frame rate) but processes
frame-by-frame so it works regardless of size, at the cost of runtime.

Requirements:
    - Python packages: opencv-python, numpy
        pip install opencv-python numpy
    - System binary: ffmpeg (used for final encoding + copying audio)
        macOS:  brew install ffmpeg

Usage:
    python remove_blue_background.py FOREGROUND.mov BACKGROUND.mov OUTPUT.mp4

Common options:
    --preview 5          Only render the first 5 seconds (fast sanity check)
    --hue 105 --hue-tolerance 18 --sat-min 60 --val-min 40
                         Manually override the auto-detected key color
    --no-auto-detect     Disable auto sampling of the blue-screen color
    --no-despill         Disable blue-spill suppression on edges
    --feather 21         Mask edge blur kernel size (odd int, default 21)

Example:
    python remove_blue_background.py IMG_1234.MOV new_bg.MOV composited.mp4
"""

import argparse
import shutil
import subprocess
import sys
import time

try:
    import cv2
    import numpy as np
except ImportError as exc:  # pragma: no cover - environment guidance only
    sys.exit(
        "Missing dependency: {}\n"
        "Install requirements with:\n"
        "    pip install opencv-python numpy".format(exc)
    )


def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        sys.exit(
            "ffmpeg was not found on PATH. Install it first, e.g.:\n"
            "    brew install ffmpeg"
        )


def open_capture(path, label):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        sys.exit(f"Could not open {label} video: {path}")
    return cap


def sample_key_color(cap, sample_frames=5, border_frac=0.06):
    """Auto-detect the blue-screen color by sampling a border strip on the
    first few frames (assumes the screen fills the edges of the frame)."""
    hues, sats, vals = [], [], []
    for _ in range(sample_frames):
        ret, frame = cap.read()
        if not ret:
            break
        h, w = frame.shape[:2]
        bt = max(1, int(min(h, w) * border_frac))
        strip = np.concatenate(
            [
                frame[:bt, :].reshape(-1, 3),
                frame[-bt:, :].reshape(-1, 3),
                frame[:, :bt].reshape(-1, 3),
                frame[:, -bt:].reshape(-1, 3),
            ]
        )
        hsv_strip = cv2.cvtColor(strip.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
        hues.append(np.median(hsv_strip[:, 0]))
        sats.append(np.median(hsv_strip[:, 1]))
        vals.append(np.median(hsv_strip[:, 2]))

    # Rewind so the real processing loop re-reads these frames.
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    if not hues:
        return None
    return float(np.median(hues)), float(np.median(sats)), float(np.median(vals))


def build_mask(hsv_frame, hue, hue_tolerance, sat_min, val_min):
    lower = np.array([max(0, hue - hue_tolerance), sat_min, val_min], dtype=np.uint8)
    upper = np.array([min(179, hue + hue_tolerance), 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv_frame, lower, upper)

    # Clean up speckle noise, then close small holes inside the key region.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    return mask


def cover_resize(frame, target_w, target_h):
    """Resize+center-crop `frame` to exactly (target_w, target_h) without
    distorting aspect ratio (like CSS `background-size: cover`)."""
    h, w = frame.shape[:2]
    scale = max(target_w / w, target_h / h)
    new_w, new_h = int(round(w * scale)), int(round(h * scale))
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
    resized = cv2.resize(frame, (new_w, new_h), interpolation=interp)
    x0 = (new_w - target_w) // 2
    y0 = (new_h - target_h) // 2
    return resized[y0 : y0 + target_h, x0 : x0 + target_w]


def suppress_spill(frame_f, blue_amount):
    """Reduce excess blue on edge/partially-keyed pixels so no blue halo
    remains around the subject. `blue_amount` is a 0..1 float mask."""
    b, g, r = frame_f[..., 0], frame_f[..., 1], frame_f[..., 2]
    avg_rg = (r + g) / 2.0
    excess = np.clip(b - avg_rg, 0, None)
    b_corrected = b - excess * blue_amount
    return np.dstack([b_corrected, g, r])


def process(args):
    check_ffmpeg()

    fg_cap = open_capture(args.foreground, "foreground")
    bg_cap = open_capture(args.background, "background")

    fps = fg_cap.get(cv2.CAP_PROP_FPS) or 60.0
    width = int(fg_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(fg_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(fg_cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if args.preview:
        total_frames = min(total_frames or 1 << 30, int(round(args.preview * fps)))

    bg_fps = bg_cap.get(cv2.CAP_PROP_FPS) or fps

    if args.auto_detect:
        detected = sample_key_color(fg_cap)
        if detected:
            hue, sat, val = detected
            args.hue = args.hue if args.hue is not None else hue
            print(f"Auto-detected key color: hue={hue:.1f} sat={sat:.1f} val={val:.1f}")
        else:
            print("Auto-detect found no frames; falling back to defaults.")

    hue = args.hue if args.hue is not None else 105.0  # typical chroma-blue

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{width}x{height}", "-r", f"{fps}",
        "-i", "-",
        "-i", args.foreground,
        "-map", "0:v:0", "-map", "1:a:0?",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", str(args.crf), "-preset", args.preset,
        "-c:a", "aac", "-shortest",
        args.output,
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    bg_accum = 0.0
    bg_step = bg_fps / fps
    bg_frame = None
    frame_index = 0
    start_time = time.time()

    try:
        while True:
            if total_frames and frame_index >= total_frames:
                break
            ret, frame = fg_cap.read()
            if not ret:
                break

            # Advance the background reader at its own real-time pace,
            # looping back to the start whenever it runs out of frames.
            bg_accum += bg_step
            while bg_accum >= 1.0 or bg_frame is None:
                ret_bg, candidate = bg_cap.read()
                if not ret_bg:
                    bg_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret_bg, candidate = bg_cap.read()
                    if not ret_bg:
                        sys.exit("Background video has no readable frames.")
                bg_frame = candidate
                bg_accum -= 1.0

            bg_resized = cover_resize(bg_frame, width, height)

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = build_mask(hsv, hue, args.hue_tolerance, args.sat_min, args.val_min)

            # Feather the hard mask into a soft alpha matte.
            k = args.feather | 1  # ensure odd kernel size
            soft_mask = cv2.GaussianBlur(mask, (k, k), 0).astype(np.float32) / 255.0
            alpha_fg = 1.0 - soft_mask  # 1 = keep foreground, 0 = show background

            frame_f = frame.astype(np.float32)
            if args.despill:
                frame_f = suppress_spill(frame_f, soft_mask)

            alpha_3 = alpha_fg[..., None]
            composite = frame_f * alpha_3 + bg_resized.astype(np.float32) * (1.0 - alpha_3)
            composite = np.clip(composite, 0, 255).astype(np.uint8)

            proc.stdin.write(composite.tobytes())

            frame_index += 1
            if frame_index % 60 == 0 or frame_index == total_frames:
                elapsed = time.time() - start_time
                rate = frame_index / elapsed if elapsed > 0 else 0
                denom = total_frames or frame_index
                pct = 100 * frame_index / denom
                print(
                    f"\r{frame_index}/{denom or '?'} frames "
                    f"({pct:5.1f}%) - {rate:.1f} fps",
                    end="",
                    flush=True,
                )
    except KeyboardInterrupt:
        print("\nInterrupted, stopping ffmpeg...")
        proc.terminate()
        raise
    except BrokenPipeError:
        sys.exit("\nffmpeg closed the pipe unexpectedly (check its stderr above).")
    finally:
        fg_cap.release()
        bg_cap.release()
        if proc.stdin:
            try:
                proc.stdin.close()
            except OSError:
                pass
        proc.wait()

    print()
    if proc.returncode != 0:
        sys.exit(f"ffmpeg exited with code {proc.returncode}")
    print(f"Done: {args.output}")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("foreground", help="Blue-screen source video")
    p.add_argument("background", help="Replacement background video")
    p.add_argument("output", help="Output video path (e.g. output.mp4)")

    p.add_argument("--preview", type=float, default=None, help="Only render the first N seconds")

    p.add_argument("--hue", type=float, default=None, help="Key hue, 0-179 (OpenCV HSV scale)")
    p.add_argument("--hue-tolerance", type=float, default=18.0, help="Hue window width (default: 18)")
    p.add_argument("--sat-min", type=float, default=60.0, help="Minimum saturation to key out (default: 60)")
    p.add_argument("--val-min", type=float, default=40.0, help="Minimum brightness to key out (default: 40)")
    p.add_argument("--no-auto-detect", dest="auto_detect", action="store_false",
                    help="Disable automatic blue-screen color sampling")
    p.add_argument("--no-despill", dest="despill", action="store_false",
                    help="Disable blue-spill suppression")
    p.add_argument("--feather", type=int, default=21, help="Mask edge blur kernel size, odd int (default: 21)")

    p.add_argument("--crf", type=int, default=18, help="x264 quality, lower=better (default: 18)")
    p.add_argument("--preset", default="medium", help="x264 speed preset (default: medium)")
    return p.parse_args()


if __name__ == "__main__":
    process(parse_args())
