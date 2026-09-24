# my_dify

一个用于学习 Dify 架构的精简实现。项目从最小 Flask API 开始，逐步加入模型调用、应用管理、Workflow 和 RAG。

## 当前功能

- Flask Application Factory
- `GET /health` 健康检查
- `POST /api/chat` 非流式模型调用
- `POST /api/chat/stream` SSE 流式模型调用
- AI 应用的创建、查询、修改和删除
- 使用应用自己的 Prompt、模型和温度进行普通或流式聊天
- SQLite 数据持久化
- Conversation 与 Message 多轮对话持久化
- OpenAI-compatible 模型客户端
- 基于环境变量的模型配置
- Controller、Schema、Service、Model Runtime 分层
- pytest 单元测试和接口测试（不访问真实网络）

## 安装依赖

```powershell
uv sync
```

## 配置模型

复制 `.env.example` 为 `.env`，然后填写自己的模型配置。不要提交 `.env`。

```dotenv
MY_DIFY_MODEL_BASE_URL=https://api.openai.com/v1
MY_DIFY_MODEL_API_KEY=your-api-key
MY_DIFY_MODEL_NAME=gpt-4.1-mini
MY_DIFY_MODEL_TIMEOUT=30
```

也可以填写其他兼容 OpenAI Chat Completions 协议的服务地址和模型名。

## 启动后端

```powershell
uv run flask --app "my_dify:create_app" init-db
uv run flask --app "my_dify:create_app" run --debug --port 5001
```

## 管理 AI 应用

创建一个应用：

```powershell
$body = @{
  name = "Python 助手"
  description = "帮助学习 Python"
  system_prompt = "你是一名耐心的 Python 老师"
  model_name = "deepseek-flash"
  temperature = 0.5
} | ConvertTo-Json

$app = Invoke-RestMethod `
  -Uri http://127.0.0.1:5001/api/apps `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

查询应用列表：

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5001/api/apps
```

应用创建成功后，可以使用返回的 `id` 发起聊天：

```powershell
$chatBody = @{ message = "什么是 Python 装饰器？" } | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:5001/api/apps/$($app.id)/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body $chatBody
```

对应的流式接口是：

```text
POST /api/apps/{app_id}/chat/stream
```

## 多轮对话

先为应用创建会话：

```powershell
$conversation = Invoke-RestMethod `
  -Uri "http://127.0.0.1:5001/api/apps/$($app.id)/conversations" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"name":"学习 Python"}'
```

向同一个会话连续发送消息，后端会把历史 user 和 assistant 消息一起交给模型：

```powershell
$messageBody = @{ message = "我叫小明" } | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:5001/api/conversations/$($conversation.id)/messages" `
  -Method Post `
  -ContentType "application/json" `
  -Body $messageBody
```

查询完整消息历史：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:5001/api/conversations/$($conversation.id)/messages"
```

流式多轮聊天接口：

```text
POST /api/conversations/{conversation_id}/messages/stream
```

## 调用聊天接口

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:5001/api/chat `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message":"你好"}'
```

## 调用流式聊天接口

使用 `curl.exe -N` 关闭客户端输出缓冲，以便逐条看到 SSE 事件：

```powershell
curl.exe -N `
  -X POST http://127.0.0.1:5001/api/chat/stream `
  -H "Content-Type: application/json" `
  -d '{"message":"请用三句话介绍 Python"}'
```

响应包含 `message`、`done` 或 `error` 事件：

```text
event: message
data: {"delta":"Python"}

event: done
data: {}
```

## 运行测试

```powershell
uv run pytest
```

测试使用假模型和 `httpx.MockTransport`，不会消耗真实模型额度。

## 下一步

使用 Vue 3 和 TypeScript 创建应用列表、应用配置和多轮聊天界面。
