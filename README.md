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

   访问 `http://127.0.0.1:8000/health` 应返回 `{"status": "ok"}`；`http://127.0.0.1:8000/docs` 查看接口文档。

## 运行测试

```bash
uv run pytest -v
```

测试通过设置 `DATABASE_URL=sqlite://:memory:` 覆盖 MySQL 连接（见 `tests/conftest.py`），无需真实数据库即可验证应用启动与响应。
