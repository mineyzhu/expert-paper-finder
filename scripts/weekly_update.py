#!/usr/bin/env python3
"""
定时任务：每周自动更新专家数据
设置在每周日自动运行
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.expert_crawler import ExpertCrawler
from datetime import datetime

def main():
    print("=" * 60)
    print("🔄 专家数据自动更新任务")
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    crawler = ExpertCrawler()
    
    # 执行更新
    crawler.update_all()
    
    # 导出查询用 CSV
    csv_file = crawler.export_to_search_csv()
    
    print("\n✅ 更新任务完成！")
    print(f"📁 导出文件: {csv_file}")
    print("=" * 60)

if __name__ == '__main__':
    main()
