from datetime import datetime, timedelta
import os
from pathlib import Path
import subprocess
import sys
import traceback
from shazam import Shazam


def str_to_timedelta(time_str: str) -> timedelta:
    """
    Docstring for str_to_timedelta

    :param time_str: Description
    :type time_str: str
    :return: Description
    :rtype: timedelta
    """
    temp = time_str
    if "." not in temp:
        temp += ".0"
    try:
        t = datetime.strptime(temp, "%H:%M:%S.%f")
    except ValueError as e:
        raise ValueError(
            f"时间格式不正确: '{time_str}'。请确保格式为 HH:MM:SS 或 HH:MM:SS.f"
        ) from e

    return t - datetime(1900, 1, 1)


def ffmpeg_cut_quick(input: Path, start_time, end_time, output: Path):
    # ffmpeg -v error -ss start_time -to end_time -i input -y output
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-ss",
        start_time,
        "-to",
        end_time,
        "-i",
        str(input),
        # "-c:a",
        # "copy",
        "-y",
        str(output),
    ]

    task = subprocess.run(command, stderr=subprocess.PIPE, encoding="utf-8")
    if task.returncode != 0:
        raise Exception(f"命令：{command}\n执行 ffmpeg 命令发生未知错误: {task.stderr}")
    return task.stderr


# f = Path(sys.argv[1])
# f1 = ffmpeg_cut_quick(f, 0, 10, f"{f}_p1.mp3")
# f2 = ffmpeg_cut_quick(f, 10, 20, f"{f}_p2.mp3")
# f3 = ffmpeg_cut_quick(f, 20, 30, f"{f}_p3.mp3")


def parse_line(line: str) -> tuple[str, str, str]:
    """
    Docstring for parse_line

    :param line: start_time [end_time] [title]
    :type line: str
    :return: (开始时间, 结束时间|"", 标题|"")
    :rtype: tuple
    """
    parts = line.strip().split(maxsplit=2)
    it = iter(parts)
    # 1. 解析开始时间 (必填)
    try:
        start_time = next(it)
        # 建议直接存为 float 或 timedelta，方便后续计算
        str_to_timedelta(start_time)
    except (StopIteration, ValueError):
        raise ValueError(f"解析错误，无效的开始时间: '{line}'")

    # 2. 尝试解析第二个参数
    end_time = next(it, "")
    title = ""

    if end_time:
        try:
            # 尝试看第二个参数是不是时间
            str_to_timedelta(end_time)
            # 如果是时间，那么第三个部分就是标题
            title = next(it, "")
        except ValueError:
            # 如果第二个参数不是时间，那它本身就是标题的开始
            # 此时标题应该是 parts 剩下的所有部分
            end_time = ""
            title = " ".join(parts[1:])

    return start_time, end_time, title


def recognize_song(file) -> str:
    """
    Docstring for recognize_song

    :param file: Description
    :return: song's name | ""
    :rtype: str
    """
    mp3_file = open(file, "rb").read()

    with Shazam(mp3_file) as shazam:
        res = shazam.result
        return res["track"]["title"] if res["matches"] else ""


def main():
    f = Path(sys.argv[1])
    chapter_file = f"{sys.argv[1]}.chapters.txt"
    chapter_lines = []
    with open(chapter_file, "r", encoding="utf-8") as cf:
        # 只保留 strip() 后不为空的行
        chapter_lines = [line.strip() for line in cf if line.strip()]

    # f = Path(
    #     "z:/573893-帅比笙歌超可爱OvO/2026.01/12/录制-573893-20260112-180559-989-唱歌！.flv"
    # )
    new_lines = []

    for line in chapter_lines:
        parts = parse_line(line)
        start_time, end_time, title = parts
        if title:
            new_lines.append(f"{' '.join(part for part in parts if part)}\n")
            continue
        start_seconds = str_to_timedelta(start_time).total_seconds() + 5
        for i in range(1, 4):
            print(f"第{i}次识别")
            end_seconds = start_seconds + 10
            out = Path("temp.mp3")
            try:
                ffmpeg_cut_quick(f, str(start_seconds), str(end_seconds), out)
            except Exception as e:
                print(e)
                input("回车退出")
                exit(1)
            title = recognize_song(out)
            if out.exists():
                os.remove(out)
            if title:
                break
            start_seconds = end_seconds

        # title = title if title else "未知歌曲"
        new_lines.append(f"{start_time} {end_time} {title}\n")

    with open(chapter_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"发生错误：{e}")
        traceback.print_exc()
        input("回车退出")
