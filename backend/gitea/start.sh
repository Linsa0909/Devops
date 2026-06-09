#!/bin/bash
# Gitea — 自建 Git 仓库服务
# 启动后访问 http://localhost:3000

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 首次初始化
if [ ! -f "$SCRIPT_DIR/gitea.db" ]; then
    echo "🔧 首次初始化 Gitea..."
    "$SCRIPT_DIR/gitea" migrate -c "$SCRIPT_DIR/app.ini" 2>/dev/null

    # 创建管理员用户
    GITEA_WORK_DIR="$SCRIPT_DIR/data" "$SCRIPT_DIR/gitea" admin user create \
        --admin --username devops --password devops123 --email devops@local \
        -c "$SCRIPT_DIR/app.ini" 2>/dev/null
    echo "✅ 管理员: devops / devops123"
fi

echo "🌐 Gitea 启动: http://localhost:3000"
echo "   用户名: devops"
echo "   密码:   devops123"
echo ""

"$SCRIPT_DIR/gitea" web --port 3000 -c "$SCRIPT_DIR/app.ini"
