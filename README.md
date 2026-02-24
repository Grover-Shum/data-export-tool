# 数据导出Web工具

## 功能介绍

这是一个基于自然语言的电商客服数据导出工具，外包同学可以通过浏览器输入自然语言命令，快速导出客服对话数据。

### 核心功能

- **自然语言解析**：支持中文自然语言命令，自动提取店铺信息、ID和时间范围
- **一键导出**：输入命令后自动执行数据导出流程
- **文件下载**：导出完成后自动触发浏览器下载
- **临时存储**：文件下载后自动删除，不占用服务器存储空间

## 技术架构

- **后端框架**：FastAPI (Python 3.11+)
- **前端**：原生HTML/CSS/JavaScript
- **部署方式**：Railway / Render / 传统服务器

## 项目结构

```
src/
├── web/
│   ├── app.py              # FastAPI应用主文件
│   ├── parser.py           # 自然语言解析器
│   ├── run_server.py       # 服务器启动脚本
│   ├── requirements.txt    # Python依赖
│   └── static/
│       └── index.html      # Web界面
├── tools/
│   ├── dataDownload.py     # 数据下载脚本
│   ├── pigeon_conversation-linux-x64  # Linux可执行文件
│   └── pigeon_conversation-mac-arm    # Mac可执行文件
```

## 快速开始

### 1. 准备可执行文件

将Linux版本的pigeon可执行文件放到 `src/tools/` 目录下：
- Linux x64: `pigeon_conversation-linux-x64`
- Linux ARM: `pigeon_conversation-linux-arm`

### 2. 安装依赖

```bash
pip install -r src/web/requirements.txt
```

### 3. 启动服务

```bash
bash start_web.sh
```

或者直接运行：

```bash
python src/web/run_server.py
```

服务将在 `http://localhost:8000` 启动

### 4. 访问界面

打开浏览器访问 `http://localhost:8000`

## 云平台部署（推荐）

### 方式一：Railway部署（最简单）

Railway提供免费的Python应用托管，部署非常简单：

#### 1. 准备代码

```bash
# 初始化git仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit"
```

#### 2. 部署到Railway

**方法A：通过GitHub（推荐）**

1. 将代码推送到GitHub仓库
2. 访问 [Railway](https://railway.app/)
3. 使用GitHub账号登录
4. 点击 "New Project" → "Deploy from GitHub repo"
5. 选择你的仓库
6. Railway会自动检测Dockerfile并部署

**方法B：通过Railway CLI**

```bash
# 安装Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 初始化项目
railway init

# 部署
railway up
```

#### 3. 配置域名

部署完成后，Railway会提供一个域名，也可以绑定自定义域名。

### 方式二：Render部署

Render也提供免费的Web服务托管：

#### 1. 准备代码

同Railway的步骤1

#### 2. 部署到Render

1. 访问 [Render](https://render.com/)
2. 使用GitHub账号登录
3. 点击 "New" → "Web Service"
4. 连接你的GitHub仓库
5. Render会自动检测 `render.yaml` 配置文件
6. 点击 "Apply" 开始部署

#### 3. 配置说明

Render会自动：
- 使用Dockerfile构建镜像
- 设置健康检查路径 `/api/health`
- 分配免费域名

### 方式三：Fly.io部署

Fly.io提供免费的Linux容器服务：

#### 1. 安装Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
```

#### 2. 登录并部署

```bash
# 登录
fly auth login

# 创建应用
fly apps create data-export-tool

# 部署
fly deploy
```

## 传统服务器部署

### 方式一：一键部署（推荐）

使用提供的部署脚本，自动完成所有配置：

```bash
# 1. 上传代码到服务器
scp -r Script/ user@server:/tmp/

# 2. SSH登录服务器
ssh user@server

# 3. 运行一键部署脚本
cd /tmp/Script
sudo bash deploy.sh
```

部署脚本会自动：
- 安装系统依赖（Python3, Nginx）
- 复制项目文件到 `/opt/data-export-tool`
- 安装Python依赖包
- 创建systemd服务
- 配置Nginx反向代理
- 启动服务

### 方式二：手动部署

#### 1. 直接运行（测试环境）

```bash
# 上传代码到服务器
scp -r Script/ user@server:/path/to/

# SSH登录服务器
ssh user@server

# 进入项目目录
cd /path/to/Script

# 安装依赖
pip install -r src/web/requirements.txt

# 启动服务
python src/web/run_server.py
```

#### 2. 使用Systemd服务（生产环境）

##### 创建systemd服务文件

```bash
sudo nano /etc/systemd/system/data-export.service
```

内容如下：

```ini
[Unit]
Description=Data Export Web Tool
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/Script
ExecStart=/usr/bin/python3 src/web/run_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

##### 启动服务

```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start data-export

# 设置开机自启
sudo systemctl enable data-export

# 查看服务状态
sudo systemctl status data-export

# 查看日志
sudo journalctl -u data-export -f
```

##### 停止/重启服务

```bash
# 停止服务
sudo systemctl stop data-export

# 重启服务
sudo systemctl restart data-export
```

#### 3. 使用Nginx反向代理（外网访问）

##### 安装Nginx

```bash
sudo apt update
sudo apt install nginx
```

##### 配置Nginx

```bash
sudo nano /etc/nginx/sites-available/data-export
```

内容如下：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 增加超时时间，适应大文件下载
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

##### 启用配置

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/data-export /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载Nginx
sudo systemctl reload nginx
```

##### 添加HTTPS支持（可选）

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

## 使用说明

### 命令格式

```
请帮我导出[店铺名称]店铺ID为[数字]从[年份]年[月份]月[日期]日[小时]点到[年份]年[月份]月[日期]日[小时]点的数据
```

### 示例

```
请帮我导出修丽可官方旗舰店店铺ID为8226405从2026年2月9日10点到2026年2月9日17点的数据
```

### 使用步骤

1. 打开Web界面
2. 在输入框中输入导出命令（支持Ctrl+Enter快捷提交）
3. 点击"开始导出"按钮
4. 等待处理完成，文件将自动下载
5. 文件下载后会自动从服务器删除，不占用存储空间

## API文档

访问 `http://your-domain/docs` 查看Swagger API文档

### 主要接口

#### POST /api/export
导出数据接口

**请求体：**
```json
{
  "text": "请帮我导出修丽可官方旗舰店店铺ID为8226405从2026年2月9日10点到2026年2月9日17点的数据"
}
```

**响应：**
```json
{
  "success": true,
  "message": "数据导出成功",
  "data": {
    "shop_name": "修丽可官方旗舰店",
    "shop_id": "8226405",
    "start_time": "2026-02-09 10:00",
    "end_time": "2026-02-09 17:00",
    "filename": "修丽可官方旗舰店2月9日10点-2月9日17点标注数据.xlsx",
    "download_url": "/api/download/uuid-here"
  }
}
```

#### GET /api/download/{file_id}
下载文件接口（下载后自动删除）

#### GET /api/files
获取当前可下载的文件列表

#### GET /api/health
健康检查接口

## 生产环境建议

### 1. 安全配置

- **访问控制**：建议添加用户认证机制
- **IP白名单**：限制访问IP范围
- **速率限制**：防止接口被滥用
- **输入验证**：严格验证用户输入

### 2. 性能优化

- 使用Nginx反向代理处理静态文件
- 配置合适的worker数量
- 设置合理的超时时间

### 3. 监控和日志

- 使用systemd管理服务，自动重启
- 配置日志轮转，避免日志文件过大
- 监控服务状态和资源使用情况

## 故障排查

### 服务无法启动

检查端口是否被占用：
```bash
lsof -i :8000
```

### 文件下载失败

检查文件权限：
```bash
chmod +x src/tools/pigeon_conversation-linux-x64
```

### 导出失败

查看详细日志：
```bash
# 如果使用systemd
sudo journalctl -u data-export -f

# 如果直接运行
# 查看控制台输出
```

### Railway/Render部署失败

1. 检查Dockerfile是否正确
2. 确认pigeon可执行文件已包含在代码中
3. 查看部署日志定位具体错误

## 维护说明

### 更新代码

**云平台部署：**
```bash
git add .
git commit -m "Update"
git push
# Railway/Render会自动重新部署
```

**传统服务器部署：**
```bash
cd /path/to/Script
git pull
sudo systemctl restart data-export
```

### 查看服务状态

```bash
sudo systemctl status data-export
```

### 查看实时日志

```bash
sudo journalctl -u data-export -f
```

## 注意事项

1. **文件临时存储**：导出的文件在下载后会自动删除，不会占用服务器存储空间
2. **并发限制**：建议控制并发导出数量，避免服务器资源耗尽
3. **网络要求**：确保服务器可以访问数据下载接口
4. **Python版本**：建议使用Python 3.11或更高版本
5. **可执行文件**：确保提供正确平台的pigeon可执行文件

## 平台对比

| 平台 | 免费额度 | 部署难度 | 推荐度 |
|------|---------|---------|--------|
| Railway | $5/月额度 | ⭐ 最简单 | ⭐⭐⭐⭐⭐ |
| Render | 750小时/月 | ⭐⭐ 简单 | ⭐⭐⭐⭐ |
| Fly.io | 3个小型VM | ⭐⭐⭐ 中等 | ⭐⭐⭐ |
| 传统服务器 | 无限制 | ⭐⭐⭐⭐⭐ 复杂 | ⭐⭐ |

## 联系方式

如有问题，请联系技术支持团队。
