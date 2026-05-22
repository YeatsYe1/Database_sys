# 🚀 校园外卖两段式配送数据库系统

> **Campus Delivery Two-Stage Distribution Database System**  
> 期末答辩展示项目 · 基于 MySQL + Streamlit 的全栈数据可视化大屏

---

## 📋 项目概述

本项目设计并实现了一套 **校园外卖两段式配送数据库系统**，包含：

- **创新的两段式配送模式**：干线骑手（商家→寄存点）+ 楼栋骑手（寄存点→寝室）
- **高并发防超卖机制**：利用 MySQL 行级锁 + 触发器实现高并发库存安全扣减
- **全链路状态机**：6 种精细化订单状态流转，双骑手复合追踪
- **实时数据大屏**：基于 Streamlit 打造精美的可视化监控看板

---

## 🏗️ 项目结构

```
campus_delivery_project/
├── campus_delivery_db.sql      # 数据库完整建表脚本（DDL + 存储过程 + 视图 + 种子数据）
├── dashboard_app.py            # Streamlit 数据可视化大屏
├── generate_mock_data.py       # 模拟数据生成器（Faker）
├── requirements.txt            # Python 依赖清单
├── .env.example                # 环境变量配置模板
├── .gitignore                  # Git 忽略规则
└── README.md                   # 项目说明文档（你在这里 📖）
```

---

## ⚙️ 快速开始

### 前置条件

- Python 3.8+
- MySQL 8.0+（支持 Window Function 和 SIGNAL 语法）
- Git（可选，用于版本管理）

### 1️⃣ 克隆 / 下载项目

```bash
git clone <仓库地址>
cd campus_delivery_project
```

### 2️⃣ 配置数据库

登录 MySQL 后执行建表脚本：

```bash
mysql -u root -p < campus_delivery_db.sql
```

该脚本会自动：
- 创建数据库 `campus_delivery_db`
- 创建所有表、索引、视图、触发器、存储过程
- 插入预置种子数据

### 3️⃣ 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 MySQL 密码：

```ini
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=你的数据库密码
MYSQL_DATABASE=campus_delivery_db
MYSQL_CHARSET=utf8mb4
```

### 4️⃣ 安装 Python 依赖

```bash
pip install -r requirements.txt
```

> 💡 建议使用虚拟环境：`python -m venv venv` 后激活再安装。

### 5️⃣ 生成模拟数据（可选）

```bash
python generate_mock_data.py
```

这将生成：
- 👤 50 个学生用户
- 🏪 15 个商家（各 5 道菜品）
- 📦 1000 条历史订单流水

### 6️⃣ 启动数据大屏

```bash
streamlit run dashboard_app.py
```

浏览器会自动打开，查看校园外卖实时数据监控大屏 🎉

---

## 🗄️ 数据库核心设计

### 两段式状态机

```
Paid ──► Stage1_Assigned ──► Arrived_At_Point ──► Stage2_Assigned ──► Completed
  │                              │                        │
  └──────────── Cancelled ◄──────┴────────────────────────┘
```

### 核心表结构

| 表名 | 说明 |
|------|------|
| `users` | 学生用户表（含校园卡余额） |
| `merchants` | 商家信息表 |
| `dishes` | 菜品表（含库存/上架状态） |
| `pickup_points` | 寄存中转点（容量管控） |
| `riders` | 两段式骑手表（干线/楼栋） |
| `orders` | 订单主表（状态机 + 双骑手追踪） |
| `order_items` | 订单明细表 |

### 高并发安全机制

- **防超卖触发器**：`trg_check_dish_stock_before_order` 在插入明细前使用 `SELECT ... FOR UPDATE` 加行锁检查库存
- **自动扣库存触发器**：`trg_reduce_dish_stock_after_order` 下单成功后自动扣减
- **事务保障**：所有存储过程均包含完整的事务回滚机制

---

## 📊 大屏功能

| Tab | 功能 |
|-----|------|
| 📊 寄存柜饱和度预警 | 寄存点容量使用率 + 爆仓警戒线 |
| 🏆 商户销售排行榜 | Top 10 商户销售额排行 |
| 🛵 两段式运力监控 | 订单状态分布饼图 + 运力健康度 |
| 📋 近期订单流水 | 最新 10 条订单详情 |

---

## 👥 参与贡献

1. Fork 本项目
2. 创建你的特性分支：`git checkout -b feature/amazing-feature`
3. 提交你的改动：`git commit -m 'Add amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 发起 Pull Request

---

## 📄 许可证

本项目仅供学习交流使用。

---

<p align="center">
  🏫 校园外卖两段式配送数据库系统 · 期末答辩展示<br>
  Made with ❤️
</p>
