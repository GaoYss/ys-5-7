# 奶茶店会员积分系统

基于 FastAPI + Vue 3 的奶茶店会员积分系统，包含积分获取规则、礼品兑换、会员等级权益、生日礼券发放、积分流水和基础数据看板。

## 功能

- 会员管理：新增会员、查看会员等级、积分和权益。
- 积分获取规则：基础消费积分、周三双倍、新品三倍等规则。
- 礼品兑换：按积分兑换礼品，自动扣减积分和库存。
- 会员等级权益：按积分自动匹配等级，展示折扣、生日积分和权益。
- 生日礼券发放：为当天生日会员发放礼券并赠送生日积分，避免同年重复发放。
- 积分流水：记录消费入账、礼品兑换、生日积分。

## 项目结构

```text
.
├── backend
│   ├── app
│   │   ├── api          # FastAPI 路由模块
│   │   ├── core         # 配置
│   │   ├── db           # SQLite 初始化和连接
│   │   ├── repositories # 数据访问层
│   │   ├── schemas      # Pydantic 入参和响应模型
│   │   └── services     # 业务逻辑
│   ├── Dockerfile
│   └── requirements.txt
├── frontend
│   ├── src
│   │   ├── api          # 接口封装
│   │   ├── components   # 通用组件
│   │   ├── stores       # 页面共享状态
│   │   ├── styles       # 全局样式
│   │   └── views        # 业务视图
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

## Docker Compose 启动

```bash
docker compose up --build
```

启动后访问：

- 前端：http://localhost:19173
- 后端健康检查：http://localhost:19080/health
- API 文档：http://localhost:19080/docs

后端使用 SQLite，数据库文件通过 `backend-data` volume 持久化，首次启动会自动建表并写入演示数据。

## 本地开发

后端：

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

## 常用接口

- `GET /api/members`：会员列表
- `POST /api/members`：新增会员
- `GET /api/points/rules`：积分规则
- `POST /api/points/earn`：消费积分入账
- `GET /api/gifts`：礼品列表
- `POST /api/gifts/redeem`：兑换礼品
- `GET /api/tiers`：等级权益
- `POST /api/vouchers/birthday/issue`：发放当天生日礼券
