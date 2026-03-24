# 专家文献检索工具 - 使用指南

## 🎯 功能简介

输入专家姓名，自动查询其最近发表的学术论文。

**特色功能：**
- ✅ 支持中文姓名（自动转拼音）
- ✅ 支持英文姓名
- ✅ 显示论文标题、PMID、发表日期、期刊
- ✅ 提供论文 PDF 链接
- ✅ 导出 CSV、Markdown 格式

## 📦 安装步骤

### 方式 1：自动安装（推荐）

1. **解压文件**
   ```
   解压 expert-paper-finder.zip 到任意目录
   ```

2. **运行安装脚本**
   ```bash
   cd expert-paper-finder
   chmod +x install.sh
   ./install.sh
   ```

3. **按照提示操作**
   - 自动安装所有依赖
   - 可选配置 NCBI API Key（提高查询速度）

### 方式 2：手动安装

1. **安装依赖**
   ```bash
   cd expert-paper-finder
   pip3 install -r requirements.txt
   ```

2. **配置 API Key（可选）**
   ```bash
   export NCBI_API_KEY=你的API密钥
   ```

## 🚀 使用方法

### 启动服务器

```bash
cd expert-paper-finder
python3 scripts/server.py
```

### 打开浏览器

访问：http://localhost:5000

### 使用界面

1. **输入专家姓名**
   - 英文：`Zhang Zemin`
   - 中文：`张泽民`（自动转拼音）

2. **可选：输入机构**
   - 提高查询准确性

3. **选择时间范围**
   - 最近 3/6/12/24 个月

4. **点击"开始查询"**

5. **查看结果**
   - 论文列表
   - 导出 CSV/Markdown
   - 下载 PDF

## 📖 使用技巧

### 查询更准确

- 英文名格式：`Zhang Zemin` 或 `Zhang Z`
- 中文姓名：直接输入，自动转拼音
- 添加机构名可以提高准确性

### 常见问题

**Q: 查不到结果？**
- 检查姓名拼写是否正确
- 尝试不同的姓名格式（如 Zhang Zemin 或 Zhang Z）
- 扩大时间范围（如 12 个月）

**Q: 查询速度慢？**
- 配置 NCBI API Key（速度提升 3 倍）
- 减少查询结果数

**Q: 中文名查不到？**
- 确认 PubMed 中使用的是拼音
- 尝试直接输入英文拼写

## 🔧 高级功能

### 命令行查询

```bash
# 查询专家论文
python3 scripts/expert_search.py search --author "Zhang Zemin" --months 12

# 导出结果
python3 scripts/expert_search.py export --input results.json --format csv --output results.csv
```

### 添加专家信息

```bash
python3 scripts/expert_crawler.py add --cn "张泽民" --en "Zhang Zemin" --org "北京大学"
```

## 📁 文件说明

```
expert-paper-finder/
├── install.sh              # 安装脚本
├── requirements.txt        # Python 依赖
├── README_USER.md          # 本文件
├── scripts/
│   ├── server.py          # Web 服务器
│   ├── expert_search.py   # 查询工具
│   └── expert_crawler.py  # 专家管理
├── assets/
│   └── index.html         # Web UI
└── data/                   # 数据目录
```

## 💡 提示

- 首次使用建议配置 NCBI API Key
- 中文姓名会自动转为多种拼音格式尝试
- 结果会自动保存，可随时查看

## 🆘 获取帮助

遇到问题？
1. 检查 Python 版本（需要 3.7+）
2. 确认网络连接正常
3. 查看 PubMed 是否能访问

---

**祝你使用愉快！🎉**
