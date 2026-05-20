# Web 平台 MVP

这个仓库现在有一个面向“一条视频，多平台发布”的 Web 平台入口。

## 启动后端

```bash
uv run python sau_web_platform.py
```

默认监听：

```text
http://localhost:5409
```

## 启动前端

```bash
cd sau_frontend
npm install
npm run dev
```

默认访问：

```text
http://localhost:5173
```

## Cloudflare Pages 部署

前端是 Vite 静态站点，适合部署到 Cloudflare Pages。

GitHub 连接 Pages 时使用：

```text
Root directory: sau_frontend
Build command: npm ci && npm run build
Build output directory: dist
```

也可以从本地直接部署：

```bash
cd sau_frontend
npm install
npm run build
npx wrangler pages deploy dist --project-name turbo-publisher
```

生产环境需要配置后端地址：

```text
VITE_API_BASE_URL=https://your-api-domain.example.com/api
```

## Cloudflare 后端方案

这个项目的后端需要 Python、Chrome/Patchright 和真实浏览器自动化，不适合直接部署到 Cloudflare Workers 或 Pages Functions。

推荐部署结构：

- 前端：Cloudflare Pages
- 后端：VPS、本机、容器主机或后续 Cloudflare Containers
- 入口：Cloudflare Tunnel 或反向代理域名，例如 `https://publisher-api.example.com`

Cloudflare Tunnel 本地调试可以使用：

```bash
cloudflared tunnel --url http://localhost:5409
```

拿到公开 URL 后，把前端环境变量 `VITE_API_BASE_URL` 指到该 URL 的 `/api`。

## 已接入能力

- 平台列表：抖音、快手、小红书、视频号、Bilibili
- 账号文件列表：读取 `cookies/*.json`
- Web 登录任务：抖音、快手、小红书、视频号
- 素材上传：视频和封面
- 发布任务：一条视频按顺序提交到多个平台
- 任务状态：轮询查看运行中、成功、失败、部分成功

## 说明

- Bilibili 登录仍建议使用 CLI，本地终端二维码体验更稳定。
- 视频号 Web 端当前接入视频上传，图文发布还没有开放。
- Web 后端会直接调用 `sau_cli.py` 里的主线上传函数。
- 真实发布会打开浏览器并操作平台创作者后台，测试时请使用草稿或测试账号。
