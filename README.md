# Collector 作业拾者

## 特点

基于 ChatGPT / GPT 3.5 和多项先进技术的作业辅助工具

用户能够上传清晰完整的题目（如试卷、教辅）图片后，交由 生成器 生成答案，并且可向生成器继续提问，优化答案并提供详细解析

可与生成器对话聊天，实现实时答疑的效果，语言模型可真正理解题目，并从它的模型中整合答案。与作业帮等依赖题库的搜题手段不同，Collector 就像一位你永远在线，且回答速度超快的老师

解答能力可随技术进步而升级，如最新发布的 GPT 4 就对数理逻辑推算进行了很大的升级

## 体验

尚不完善，建议移动设备使用

由于服务器性能带宽限制，会存在速度慢、卡的问题

Azure Source: <https://collector.jiecs.top>

with Cloudflare: <https://azure-tokyo.gfwin.icu>

## 使用

### 0. 准备

本项目需要支持 Docker 的环境
运行以下命令克隆存储库

```shell
git clone https://github.com/jiesou/Collector
cd Collector
```

### 1. 配置

项目根目录创建 `.env` 文件，填入 OpenAI API Key

内容示例：

```shell
OPENAI_API_KEY=sk-xxxxx
```

### 2. 构建并运行

可参考项目中 `scripts/reinstall.sh` 提供的脚本，也可自行调整参数

```shell
sh ./scripts/reinstall.sh
```
