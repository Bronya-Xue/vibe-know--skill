# Codex 云端环境

仓库：`Bronya-Xue/vibe-know--skill`；分支：`main`（首次验证也可选包含本配置的分支）。

## 新版 Codex Cloud

1. 打开 **设置 → Codex Cloud → Environments → Create environment**，选择本仓库。
2. 环境名可设为 `vibe-knowledge-film`；共享范围选 **Only me**。使用 Python 3.12；不需要 GPU、API Key、网络密钥、VPN 或云身份。
3. 在设置对话中要求运行：

   ```bash
   bash .codex/setup.sh
   ```

   此脚本安装 Python 依赖、补齐 ffmpeg/Chromium 和字体，然后实际渲染并合成一秒测试片。测试工程会自动删除。
4. **Install script** 填上面的命令。**Start skill** 可填：

   ```text
   进入 vibe-know--skill 仓库。用 python3 .codex/check.py 检查字体、浏览器、视频和音频工具。
   本项目无需启动常驻服务。做视频前先读仓库根目录 SKILL.md，再按它的流程工作。
   需要网页预览时运行 python3 engine/render.py <工程目录> --serve。
   ```
5. 检查设置报告和文件，保存并点击 **Publish**。出现 **Environment published** 后，从该环境新开任务再运行 `python3 .codex/check.py`。

本仓库中的脚本不会自动创建、保存或发布 Codex 环境；这些步骤在环境设置界面完成。

## 网络

安装时需要 PyPI、系统软件源、字体和浏览器下载地址。可使用 **Package managers** 预设，并按实际下载情况添加：

```text
raw.githubusercontent.com
cdn.playwright.dev
playwright.download.prss.microsoft.com
cdn.playwright.download.prss.microsoft.com
```

浏览器已经安装时不会重新下载；字体脚本只补齐缺失文件。渲染及合成过程使用本地文件，不需要互联网。查事实来源时还需允许对应资料网站。

## 验证与使用

```bash
# 环境检查：应出现 PASS，检查 H.264 / AAC、1920×1080 和中文字体
python3 .codex/check.py

# 使用已有例子截图自查
python3 engine/render.py examples/kit_gallery --sheet 1.6 10.4 13.4 22.3

# 建立自己的工程，再按 SKILL.md 写文案、分镜和画面
python3 scripts/new_film.py projects/my_film --world C
```

渲染器依次选择 `VK_BROWSER_EXECUTABLE` 指定的浏览器、PATH 中的 Google Chrome/Chromium、Playwright 下载的 Chromium。
通常不需要设置环境变量。`VK_BROWSER_EXECUTABLE` 如需指定，应填写可执行文件的绝对路径。

## 旧版 Codex Cloud

若界面仍提供 Setup script / Maintenance script，两处均可填写 `bash .codex/setup.sh`；新任务选择已包含本配置的分支。
更新配置后按界面提示重置缓存。新版环境更新后应 Republish，并在新任务中验证。

参考：[当前环境说明](https://developers.openai.com/codex/environments/cloud-environments)、[旧版环境说明](https://developers.openai.com/codex/cloud/environments/)。
