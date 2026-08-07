# accelgor

基于 FastAPI + Tortoise ORM 的标准 HTTP 接口服务。

## 技术栈

- Python 3.10+（本地开发环境固定为 3.12，见 `.python-version`）
- Web 框架：FastAPI
- ORM：Tortoise ORM（MySQL 驱动使用 asyncmy）
- 数据库：MySQL 8
- 依赖管理：uv
- 测试：pytest + pytest-asyncio + httpx / FastAPI TestClient

## 目录结构

```
app/
├── main.py              # FastAPI 应用入口，挂载 Tortoise 与路由
├── core/
│   ├── config.py         # 环境配置（pydantic-settings，读取 .env）
│   └── security.py       # 密码哈希工具（bcrypt）
├── db/
│   └── tortoise_config.py # Tortoise ORM 连接配置
├── models/                # Tortoise 模型
├── schemas/               # Pydantic 请求/响应模型
├── api/
│   ├── deps.py            # 公共依赖项（如登录态校验）
│   └── v1/router.py       # v1 接口汇总路由
└── utils/                 # 工具函数

sql/        # 数据库建表 SQL
docs/       # 开发设计文档
uploads/    # 图片上传保存目录
tests/      # pytest 测试
```

## 快速开始

1. 安装依赖（需要先安装 [uv](https://docs.astral.sh/uv/)）：

   ```bash
   uv sync
   ```

2. 复制环境变量文件并按需修改：

   ```bash
   cp .env.example .env
   ```

3. 启动本地 MySQL（需要 Docker）：

   ```bash
   docker compose up -d
   ```

4. 启动开发服务：

   ```bash
   uv run uvicorn app.main:app --reload
   ```

   访问 `http://127.0.0.1:8000/health` 应返回 `{"status": "ok"}`。

## REST Client 接口调试

项目已提供基于 VS Code REST Client 的接口请求文件，位置如下：

- 注册接口：[docs/register_user.http](docs/register_user.http)
- 登录接口：[docs/login.http](docs/login.http)
- 串联演示脚本（注册/登录/鉴权）：[docs/hello_world.http](docs/hello_world.http)
- 图片上传接口（原始二进制 body）：[docs/upload.http](docs/upload.http)

### 使用方法

1. 安装 VS Code 扩展：`Huachao Mao.rest-client`。
2. 启动服务：

   ```bash
   uv run uvicorn app.main:app --reload
   ```

3. 打开对应的 `.http` 文件，点击请求上方的 `Send Request` 按钮即可直接发起请求。

### 上传接口 curl 示例（推荐真实文件调试）

上传 PNG：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/uploads/" \
   -H "Content-Type: image/png" \
   --data-binary "@/absolute/path/to/demo.png"
```

上传 JPEG：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/uploads/" \
   -H "Content-Type: image/jpeg" \
   --data-binary "@/absolute/path/to/demo.jpg"
```

### 串联演示（推荐）

可直接打开 [docs/hello_world.http](docs/hello_world.http)，按文件内顺序执行：

1. 注册普通用户
2. 普通用户登录并自动提取 `user_access_token`
3. 调用 `/api/v1/users/hello/user`（预期返回 `"Hello World"`）
4. 调用 `/api/v1/users/hello/admin`（预期 403）
5. admin 用户登录并自动提取 `admin_access_token`
6. 调用 `/api/v1/users/hello/admin`（预期返回 `"Hello World"`）


响应示例：

```json
"Hello World"
```

### 推荐插件

- `Huachao Mao.rest-client`：用于直接执行 `.http` / `.rest` 请求文件。
- `ms-python.python`：Python 开发与调试支持。
- `ms-azuretools.vscode-docker`：如果你需要管理 Docker 容器。

## 运行测试

```bash
uv run pytest -v
```

测试通过设置 `DATABASE_URL=sqlite://:memory:` 覆盖 MySQL 连接（见 `tests/conftest.py`），无需真实数据库即可验证应用启动与响应。

## 时间处理约定

为避免本地时区与 UTC 混用导致的鉴权误判，项目统一使用 `app/utils/time.py` 中的时间方法：

- `utc_now()`：返回当前 UTC 时间（aware datetime）
- `utc_after(**delta_kwargs)`：返回当前 UTC 时间之后的时间点
- `utc_before(**delta_kwargs)`：返回当前 UTC 时间之前的时间点

请不要在业务代码和测试中直接书写 `datetime.now()`、`datetime.utcnow()` 或 `datetime.now() ± timedelta(...)`。

推荐写法示例：

```python
from app.utils.time import utc_after, utc_before, utc_now

expires_at = utc_after(minutes=3)
expired_at = utc_before(minutes=3)
current = utc_now()
```

项目测试中有约束用例 `tests/test_time_convention.py`，用于拦截非统一写法。
