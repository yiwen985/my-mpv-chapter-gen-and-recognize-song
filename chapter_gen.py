from datetime import timedelta
from pathlib import Path
import subprocess
import re
import sys
import traceback

INPUT = sys.argv[1]
MIN_DURATION = 60  # 秒
NOISE_DB = -45  # 静音阈值
MIN_SILENCE = 0.5  # 静音最短时长


def get_duration(path):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    return float(subprocess.check_output(cmd).decode().strip())


def detect_silence(path):
    cmd = [
        "ffmpeg",
        "-i",
        path,
        "-af",
        f"silencedetect=noise={NOISE_DB}dB:d={MIN_SILENCE}",
        "-f",
        "null",
        "-",
    ]
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, encoding="utf-8")  # 不能用 run

    silence = []
    start = None

    for line in p.stderr:
        if "silence_start" in line:
            # start = float(re.search(r"silence_start: (\d+(\.\d+)?)", line).group(1))
            match = re.search(r"silence_start: (\d+(\.\d+)?)", line)
            if match:
                start = float(match.group(1))
        elif "silence_end" in line:
            end = float(re.search(r"silence_end: (\d+(\.\d+)?)", line).group(1))
            silence.append((start, end))
            start = None

    return silence


def get_non_silence(silence, total):
    segments = []
    prev_end = 0.0

    for s_start, s_end in silence:
        dur = s_start - prev_end
        if dur >= MIN_DURATION:
            segments.append((prev_end, s_start))
        prev_end = s_end

    # 文件结尾
    if total - prev_end >= MIN_DURATION:
        segments.append((prev_end, total))

    return segments


def cut_non_silence(path, non_silence):
    path = Path(INPUT)
    clips_dir = path.parent / Path("切片")
    clips_dir.mkdir(exist_ok=True)
    out_files = []
    for i, (s, e) in enumerate(non_silence, 1):
        out = clips_dir / path.with_stem(f"{path.stem}_{i}").name
        cmd = [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            str(s),
            "-to",
            str(e),
            "-i",
            path,
            "-c",
            "copy",
            out,
        ]
        subprocess.Popen(cmd)
        out_files.append(out)
    return out_files


def seconds_to_duration(seconds: float):
    if seconds < 0:
        return "00:00:00.000"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)

    # h, m 转为 int 确保没有小数点
    # s 使用 :06.3f 确保秒和毫秒格式正确
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def format_timedelta(delta: timedelta):
    return seconds_to_duration(delta.total_seconds())


def main():
    total = get_duration(INPUT)
    silence = detect_silence(INPUT)
    non_silence = get_non_silence(silence, total)
    chapters_file = INPUT + ".chapters.txt"

    with open(chapters_file, "w", encoding="utf-8") as f:
        for i, (s, e) in enumerate(non_silence, 1):
            f.write(f"{seconds_to_duration(s - 0.5)} {seconds_to_duration(e + 0.5)}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"发生错误：{e}")
        traceback.print_exc()
        input("回车退出")
