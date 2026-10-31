# 千古人物志 · 纯代码古风卡点视频引擎

每集 93.75 秒、1080×1920 竖屏、五回章回体，全部用 Python（Pillow + numpy）绘制，ffmpeg 合成。

## 运行
```bash
pip install pillow numpy   # 另需 ffmpeg
python3 render_<人物>.py 输出.mp4            # 完整渲染（约 5 分钟 / 4 核）
python3 render_<人物>.py 预览.png 9.2,30.5   # 只渲染指定秒数的预览帧
```
- 引擎依赖链：render_gufeng → render_story → render_full → render_long → 各集脚本（后一集 import 前一集的辅助函数）
- `fonts/` 毛笔字体与宋体，`m2/music2_clean.wav` 已去人声提示音的配乐（116.16 BPM）
- `docs/选题队列.md` 每日制作顺序，`docs/每日工作流说明.md` 固定流程与质量规则
