# POI 知识图谱展示系统

这是一个基于 Flask 开发的景点信息展示系统，用于展示和管理景点信息（POI - Points of Interest）构成的空间图谱。系统提供了景点信息的可视化展示、分类浏览和详细信息查看等功能。

## 安装说明

1. cd poi_v1

2. 创建并激活 Conda 环境：

```bash
conda env create -f environment.yml
conda activate poi_2
```
3. 运行应用：

```bash
python poi.py
```
4. 在浏览器中访问：

- 打开终端中显示的链接（通常是 http://127.0.0.1:5000/）
- 或者直接在浏览器中输入 http://localhost:5000

## 项目结构

```
poi_v1/
├── static/          # 静态资源文件
├── templates/       # HTML 模板文件
├── environment.yml  # Conda 环境配置文件
├── poi.py          # 主程序文件
└── README.md       # 项目说明文档
```
## 依赖项

- Flask 3.0.3
- Jinja2 3.1.6
- Werkzeug 3.0.6
- 其他依赖详见 environment.yml

## 使用说明

1. 启动应用后，系统会自动加载所有景点信息
2. 在主页可以浏览所有景点
3. 点击景点卡片可以查看详细信息
4. 使用分类筛选功能可以快速找到感兴趣的景点

## 注意事项

- 确保已安装 Conda 环境管理工具
- 运行前请确保已激活正确的 Conda 环境
- 如果遇到端口占用问题，可以修改 poi.py 中的端口号

## 技术支持

如有问题，请提交 Issue 或联系项目维护者。
