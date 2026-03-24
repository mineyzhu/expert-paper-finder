#!/usr/bin/env python3
"""
国内高校/研究所专家信息爬虫
自动从官网抓取专家的中文名、英文名、机构、领域、主页链接
"""

import os
import sys
import re
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Callable
from urllib.parse import urljoin, urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False
    logger.warning("缺少依赖库，请运行: pip install requests beautifulsoup4 lxml")


class UniversityCrawler:
    """高校/研究所专家爬虫基类"""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self.experts = []
    
    def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """获取页面内容"""
        for i in range(retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return response.text
            except Exception as e:
                logger.warning(f"获取页面失败 (尝试 {i+1}/{retries}): {url} - {e}")
                time.sleep(2)
        return None
    
    def parse_experts_page(self, html: str) -> List[Dict]:
        """解析专家列表页 - 子类需要实现"""
        raise NotImplementedError
    
    def get_expert_detail(self, url: str) -> Dict:
        """获取专家详情 - 子类需要实现"""
        raise NotImplementedError
    
    def crawl(self) -> List[Dict]:
        """执行爬取"""
        logger.info(f"开始爬取 {self.name}...")
        self.experts = self.parse_experts_page(self.fetch_page(self.base_url))
        logger.info(f"完成！共爬取 {len(self.experts)} 位专家")
        return self.experts


# 预设的高校/研究所爬虫
class PekingUniversityCrawler(UniversityCrawler):
    """北京大学爬虫"""
    
    def __init__(self):
        super().__init__("北京大学", "https://www.pku.edu.cn/")
        # 北京大学生命科学学院/BIOPIC
        self.faculty_pages = [
            "https://www.bio.pku.edu.cn/",
            "https://biopic.pku.edu.cn/",
        ]
    
    def parse_faculty_page(self, html: str) -> List[Dict]:
        """解析师资页面"""
        experts = []
        soup = BeautifulSoup(html, 'lxml')
        
        # 常见的师资列表容器
        for container in soup.find_all(['ul', 'div'], class_=re.compile(r'faculty|teacher|professor|member|team')):
            for item in container.find_all('li'):
                link = item.find('a')
                if link and link.get('href'):
                    name = link.get_text(strip=True)
                    if name and len(name) >= 2:
                        experts.append({
                            'name_cn': name,
                            'name_en': '',
                            'org': '北京大学',
                            'field': '',
                            'homepage': urljoin(self.base_url, link['href'])
                        })
        
        return experts
    
    def crawl(self) -> List[Dict]:
        """执行爬取"""
        all_experts = []
        for page in self.faculty_pages:
            logger.info(f"爬取: {page}")
            html = self.fetch_page(page)
            if html:
                experts = self.parse_faculty_page(html)
                all_experts.extend(experts)
        
        # 去重
        seen = set()
        unique_experts = []
        for exp in all_experts:
            if exp['name_cn'] not in seen:
                seen.add(exp['name_cn'])
                unique_experts.append(exp)
        
        self.experts = unique_experts
        logger.info(f"完成！共爬取 {len(self.experts)} 位专家")
        return self.experts


class TsinghuaUniversityCrawler(UniversityCrawler):
    """清华大学爬虫"""
    
    def __init__(self):
        super().__init__("清华大学", "https://www.tsinghua.edu.cn/")


class UCASCrawler(UniversityCrawler):
    """中国科学院爬虫"""
    
    def __init__(self):
        super().__init__("中国科学院", "https://www.cas.ac.cn/")
        self.institutes = [
            "https://www.pbc.cn/",
            "https://www.ibp.cas.cn/",
            "https://www.genetics.ac.cn/",
        ]


class ExpertDataCrawler:
    """专家数据爬虫管理器"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # 可用的爬虫
        self.crawlers = {
            'pku': PekingUniversityCrawler,
            'tsinghua': TsinghuaUniversityCrawler,
            'cas': UCASCrawler,
        }
    
    def crawl_all(self, targets: List[str] = None) -> List[Dict]:
        """爬取所有目标"""
        all_experts = []
        
        if targets is None:
            targets = list(self.crawlers.keys())
        
        for target in targets:
            if target in self.crawlers:
                try:
                    crawler = self.crawlers[target]()
                    experts = crawler.crawl()
                    all_experts.extend(experts)
                except Exception as e:
                    logger.error(f"爬取 {target} 失败: {e}")
        
        return all_experts
    
    def crawl_single(self, target: str) -> List[Dict]:
        """爬取单个目标"""
        return self.crawl_all([target])
    
    def save_experts(self, experts: List[Dict], output_file: str = None):
        """保存专家数据"""
        if output_file is None:
            output_file = os.path.join(self.data_dir, 'experts_scraped.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'experts': experts,
                'crawl_time': datetime.now().isoformat(),
                'total': len(experts)
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已保存 {len(experts)} 位专家到 {output_file}")
        return output_file


def interactive_crawl():
    """交互式爬取"""
    print("\n" + "=" * 60)
    print("🏛️  国内高校/研究所专家信息爬虫")
    print("=" * 60)
    
    if not HAS_DEPENDENCIES:
        print("\n❌ 缺少依赖库！请先安装：")
        print("   pip install requests beautifulsoup4 lxml")
        return
    
    crawler_manager = ExpertDataCrawler()
    
    print("\n📚 可爬取的机构：")
    print("   1. pku      - 北京大学")
    print("   2. tsinghua - 清华大学")
    print("   3. cas     - 中国科学院")
    print("   all       - 爬取所有")
    
    choice = input("\n请选择要爬取的机构: ").strip().lower()
    
    if choice == 'all':
        experts = crawler_manager.crawl_all()
    elif choice in crawler_manager.crawlers:
        experts = crawler_manager.crawl_single(choice)
    else:
        print("❌ 无效选择")
        return
    
    if experts:
        print(f"\n✅ 成功爬取 {len(experts)} 位专家")
        
        # 显示前10个
        print("\n前10位专家预览：")
        for i, exp in enumerate(experts[:10], 1):
            print(f"  {i}. {exp.get('name_cn', 'N/A')} - {exp.get('org', 'N/A')}")
        
        # 保存
        output = crawler_manager.save_experts(experts)
        print(f"\n💾 已保存到: {output}")
    else:
        print("\n❌ 未爬取到任何专家信息")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='国内高校/研究所专家信息爬虫')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # crawl 命令
    crawl_parser = subparsers.add_parser('crawl', help='爬取专家信息')
    crawl_parser.add_argument('--target', default='all', help='目标机构 (pku|tsinghua|cas|all)')
    crawl_parser.add_argument('--output', help='输出文件')
    
    # interactive 命令
    subparsers.add_parser('interactive', help='交互式爬取')
    
    args = parser.parse_args()
    
    if args.command == 'crawl':
        crawler_manager = ExpertDataCrawler()
        experts = crawler_manager.crawl_all([args.target] if args.target != 'all' else None)
        crawler_manager.save_experts(experts, args.output)
    
    elif args.command == 'interactive':
        interactive_crawl()
    
    else:
        parser.print_help()
        print("\n示例:")
        print("  python3 expert_scraper.py interactive  # 交互式爬取")
        print("  python3 expert_scraper.py crawl --target pku  # 爬取北京大学")


if __name__ == '__main__':
    main()
