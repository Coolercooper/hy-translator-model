# 腾讯混元 1.8B Q4_K_M 翻译模型 (CPU版)

- 1. 需在本地下载模型文件   `[HY-MT1.5-1.8B-GGUF](https://www.modelscope.cn/models/Tencent-Hunyuan/HY-MT1.5-1.8B-GGUF)`
- 2. 模型文件默认名为 `HY-MT1.5-1.8B-Q4_K_M.gguf`，可在 `.env` 中修改

## 硬件要求
- **CPU**: 推荐 4 核及以上
- **内存**: > 2GB（当前配置下每个 Worker 实例约占 1~1.5GB 内存）

## 一、部署指南

### 1. 准备配置
复制环境变量模板，并根据宿主机实际情况修改：
```bash
cp .env.example .env
```

### 2. 配置环境变量
按实际情况修改 `.env`，至少确认以下两项：
- `HOST_MODEL_DIR`：宿主机 GGUF 模型目录
- `GGUF_MODEL_FILE`：模型文件名（默认 `HY-MT1.5-1.8B-Q4_K_M.gguf`）

## 二、启动服务

```bash
docker compose up -d --build
```

## 三、健康检查

```bash
curl http://localhost:8000/health
```

成功示例：
```json
{"status":"ok"}
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
