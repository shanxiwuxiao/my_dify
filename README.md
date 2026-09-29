# my_dify

一个用于学习大模型应用工程的全栈平台，采用 Flask、Vue 3、TypeScript、SQLAlchemy、PostgreSQL 和 OpenAI-compatible API 实现。

## 功能

- 邮箱密码注册、登录、Cookie Session 与用户数据隔离
- AI 应用 CRUD、Prompt 草稿调试、不可变版本发布
- DeepSeek/OpenAI-compatible 多供应商与加密 API Key
- 多轮会话、SSE 流式输出、停止生成和历史恢复
- 文本知识库、重叠分块、向量检索、RAG 上下文与引用
- DAG Workflow：模板、条件、知识、工具、LLM 节点
- 受控工具和有限轮次 Agent
- 模型调用耗时/错误/字符用量监控
- 评测集、批量回归评测和通过率
- Alembic 数据库迁移、Render PostgreSQL、Docker 部署

## 架构

```text
Vue 3 + TypeScript
        │ REST / POST-SSE
Flask Controllers
        │
Services ── Model Runtime / RAG / Workflow / Agent / Evaluation
        │
Repositories + SQLAlchemy
        │
SQLite（开发）/ PostgreSQL（生产）
```

API Key 只在服务端加密保存，不会返回前端。所有应用、供应商、知识库、工作流、评测集均按当前用户隔离。

## 本地开发

要求 Python 3.10、uv、Node.js 和 pnpm。

```powershell
cd C:\Users\HUAWEI\Desktop\code\my_dify
Copy-Item .env.example .env
uv sync
uv run flask --app my_dify:create_app db upgrade
uv run flask --app my_dify:create_app run --debug --port 5001
```

另开终端：

```powershell
cd C:\Users\HUAWEI\Desktop\code\my_dify\web
pnpm install
pnpm dev
```

访问 `http://127.0.0.1:5173`。Vite 会将 `/api` 和 `/health` 代理到 Flask。

## 环境变量

```dotenv
MY_DIFY_MODEL_BASE_URL=https://api.deepseek.com
MY_DIFY_MODEL_API_KEY=replace-me
MY_DIFY_MODEL_NAME=deepseek-chat
MY_DIFY_MODEL_TIMEOUT=30
MY_DIFY_DATABASE_URL=sqlite:///my_dify.db
MY_DIFY_SECRET_KEY=replace-with-a-long-random-secret
MY_DIFY_SESSION_COOKIE_SECURE=false
MY_DIFY_MAX_CONTENT_LENGTH=2000000
```

生产环境必须使用随机 `MY_DIFY_SECRET_KEY`。修改该值后，已加密的供应商 API Key 将无法解密，因此应将其作为需要备份的长期密钥。

## 数据库迁移

```powershell
uv run flask --app my_dify:create_app db upgrade
uv run flask --app my_dify:create_app db migrate -m "describe change"
uv run flask --app my_dify:create_app db downgrade
```

修改模型后先生成迁移，检查迁移文件，再在全新数据库和已有测试数据库上执行升级。生产环境不要使用 `db.create_all()` 替代迁移。

## 测试与构建

```powershell
uv run pytest
cd web
pnpm build
```

测试使用假模型或 `httpx.MockTransport`，不会消耗真实 API 额度。

## Render 部署

仓库根目录的 `render.yaml` 会创建：

- Docker Web Service
- Render PostgreSQL
- 随机 Session/加密密钥
- DeepSeek 环境变量
- `/health` 健康检查

部署步骤：

1. 将代码推送到 GitHub。
2. 在 Render 新建 Blueprint 并连接仓库。
3. 首次创建时填写 `MY_DIFY_MODEL_API_KEY`。
4. 等待 Docker 构建、`flask db upgrade` 和健康检查完成。
5. 注册新账号，再配置额外模型供应商。

每次部署都会在 Gunicorn 启动前运行 Alembic 升级。不要提交 `.env`、`api/instance/*.db`、`web/dist` 或 `node_modules`。

## 主要页面

```text
/auth             注册与登录
/apps             应用管理
/model-providers  模型供应商
/knowledge        知识库和检索测试
/workflows        工作流编辑与运行
/observability    评测与监控
```

## 已知边界

- 当前文档入口为纯文本和 Markdown 粘贴，尚未加入 PDF/Word 解析和对象存储。
- 默认向量器是可替换的本地哈希向量器，适合学习和小规模部署；生产检索可替换为 Embedding API 与 pgvector。
- Workflow 前端使用 JSON 编辑器，执行器已经支持 DAG；可视化拖拽画布属于后续增强。
- 评测判定使用期望文本包含匹配，可进一步加入语义指标和 LLM-as-a-Judge。
