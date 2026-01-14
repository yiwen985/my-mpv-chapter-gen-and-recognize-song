## 安装

```shell
uv tool install --python 3.10 git+https://github.com/yiwen985/my-mpv-chapter-gen-and-recognize-song.git
```

## 使用

```shell
chapter_gen.exe .\out.flv
chapter_recognize.exe .\out.flv
```

或搭配 ContextMenuManager，命令为

```shell
cmd /c chapter_gen.exe "%1"
cmd /c chapter_recognize.exe "%1"
```

右键菜单需要注销或重启后才能生效

## 说明

使用搭配 [my_mpv_config](https://github.com/yiwen985/my_mpv_config)

- chapter_gen.py: 创建章节文件（.chapters.txt），每个章节为非静音部分（>-45 dB 且 >1 分钟），不准确（TODO）
  
  文件内容格式: 00:01:00.123 00:04:00.123 title

- chapter_recognize.py：识别章节歌名并写入到章节文件，用 shazam
  
  不识别有标题的章节
  
