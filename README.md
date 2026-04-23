# 腾讯混元 1.8B Q4_K_M 翻译模型

- 1. 需在本地下载模型文件   `[HY-MT1.5-1.8B-GGUF](https://www.modelscope.cn/models/Tencent-Hunyuan/HY-MT1.5-1.8B-GGUF)`
- 2. 模型文件默认名为 `HY-MT1.5-1.8B-Q4_K_M.gguf`，可在 `.env` 中修改

## 硬件要求
- **CPU**: 推荐 4 核及以上
- **内存**: > 2GB（当前配置下每个 Worker 实例约占 1~1.5GB 内存）

## 运行模式

- Docker 模式：当前为 Linux 容器 CPU 版，适合通用服务器部署。
- macOS 模式：新增原生 Metal GPU 版，适合 Apple Silicon 机器本地部署。

说明：Apple GPU 无法按当前项目的 Linux 容器方式稳定透传给 Docker 内 llama.cpp，因此 mac GPU 模式采用宿主机原生运行，而不是复用现有 Dockerfile。

## 一、部署指南

### 1.1 Docker CPU 模式

#### 1. 准备配置
复制环境变量模板，并根据宿主机实际情况修改：
```bash
cp .env.example .env
```

#### 2. 配置环境变量
按实际情况修改 `.env`，至少确认以下两项：
- `HOST_MODEL_DIR`：宿主机 GGUF 模型目录
- `GGUF_MODEL_FILE`：模型文件名（默认 `HY-MT1.5-1.8B-Q4_K_M.gguf`）

## 二、启动服务

```bash
docker compose up -d --build
```

### 1.2 macOS Metal GPU 模式

#### 1. 准备配置
```bash
cp .env.mac.example .env
```

#### 2. 修改 `.env`
至少确认以下配置：

```env
MODEL_FILE=/绝对路径/HY-MT1.5-1.8B-Q4_K_M.gguf
LLAMA_BACKEND=metal
LLAMA_N_GPU_LAYERS=-1
UVICORN_WORKERS=1
```

补充说明：
- `MODEL_FILE` 在 mac 原生模式下直接指向本机模型绝对路径。
- `UVICORN_WORKERS` 建议保持 `1`，避免多进程重复加载模型占满内存。
- 首次启动会重新编译 `llama-cpp-python` 以启用 Metal。

#### 3. 启动

```bash
chmod +x run_mac.sh
./run_mac.sh
```

默认监听：`http://0.0.0.0:8000`

## 三、健康检查

```bash
curl http://localhost:8000/health
```

成功示例：
```json
{"status":"ok","backend":"cpu","gpu_layers":0}
```

## 四、调用接口（OpenAI 兼容）

### 4.1 无 APIKEY

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	-d '{
		"model": "HY-MT1.5-1.8B-Q4_K_M",
		"temperature": 0.2,
		"messages": [
			{"role": "system", "content": "你是专业翻译，只输出译文。"},
			{"role": "user", "content": "翻译为简体中文：Hello world"}
		]
	}'
```

### 4.2 启用 APIKEY（推荐）

在 `.env` 设置：
```env
APIKEY=your-secret-key
```

调用时加 Header：
```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer your-secret-key" \
	-d '{
		"model": "HY-MT1.5-1.8B-Q4_K_M",
		"messages": [{"role": "user", "content": "翻译为简体中文：Hello world"}]
	}'
```

## 五、沉浸式翻译插件对接

- API 地址：`http://<服务器IP>:8000/v1/chat/completions`
- API Key：与 `.env` 中 `APIKEY` 一致（若未设置可留空）
- Method：`POST`
- Content-Type：`application/json`

请求体建议：
```json
{
	"model": "HY-MT1.5-1.8B-Q4_K_M",
	"messages": [
		{"role": "system", "content": "你是专业翻译，只输出译文。"},
		{"role": "user", "content": "{{text}}"}
	],
	"temperature": 0.2
}
```

说明：
- `temperature` 建议 `0.0 ~ 0.4`，翻译会更稳定。

## 六、更多

停止：
```bash
docker compose down
```

更新：
```bash
docker compose up -d --build
```
