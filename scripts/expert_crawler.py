#!/usr/bin/env python3
"""
专家信息抓取工具
自动从多个来源抓取专家信息（中文名、英文名、机构、领域、主页链接）
"""

import os
import sys
import json
import csv
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExpertCrawler:
    """专家信息抓取器"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        self.experts_file = os.path.join(data_dir, 'experts.json')
        self.cache_file = os.path.join(data_dir, 'experts_cache.json')
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 已知的专家数据（内置）
        self.builtin_experts = self._get_builtin_experts()
    
    def _get_builtin_experts(self) -> List[Dict]:
        """获取内置的专家数据"""
        return [
            {
                'name_cn': '张泽民',
                'name_en': 'Zhang Z',
                'org': '北京大学',
                'org_en': 'Peking University',
                'field': '单细胞测序',
                'field_en': 'Single-cell Sequencing',
                'homepage': 'https://www.pkusam.edu.cn/',
                'google_scholar': 'https://scholar.google.com/citations?user=XXXXX',
                'source': 'manual',
                'last_updated': datetime.now().isoformat()
            }
        ]
    
    def load_experts(self) -> List[Dict]:
        """加载已保存的专家数据"""
        if not os.path.exists(self.experts_file):
            return self.builtin_experts.copy()
        
        try:
            with open(self.experts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('experts', self.builtin_experts.copy())
        except Exception as e:
            logger.error(f"加载专家数据失败: {e}")
            return self.builtin_experts.copy()
    
    def save_experts(self, experts: List[Dict]):
        """保存专家数据"""
        try:
            with open(self.experts_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'experts': experts,
                    'last_update': datetime.now().isoformat(),
                    'total_count': len(experts)
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存 {len(experts)} 条专家信息")
        except Exception as e:
            logger.error(f"保存专家数据失败: {e}")
    
    def add_expert(self, name_cn: str, name_en: str, org: str = '', 
                   field: str = '', homepage: str = ''):
        """添加新专家"""
        experts = self.load_experts()
        
        # 检查是否已存在
        for expert in experts:
            if expert['name_cn'] == name_cn or expert['name_en'] == name_en:
                logger.warning(f"专家 {name_cn} 已存在")
                return expert
        
        # 添加新专家
        expert = {
            'name_cn': name_cn,
            'name_en': name_en,
            'org': org,
            'org_en': '',
            'field': field,
            'field_en': '',
            'homepage': homepage,
            'google_scholar': '',
            'source': 'manual',
            'last_updated': datetime.now().isoformat()
        }
        
        experts.append(expert)
        self.save_experts(experts)
        
        logger.info(f"已添加专家: {name_cn} ({name_en})")
        return expert
    
    def update_expert(self, name_cn: str, **kwargs):
        """更新专家信息"""
        experts = self.load_experts()
        
        for expert in experts:
            if expert['name_cn'] == name_cn:
                for key, value in kwargs.items():
                    if value:
                        expert[key] = value
                expert['last_updated'] = datetime.now().isoformat()
                expert['source'] = 'updated'
                break
        
        self.save_experts(experts)
    
    def search_expert(self, query: str) -> List[Dict]:
        """搜索专家"""
        experts = self.load_experts()
        query = query.lower()
        
        results = []
        for expert in experts:
            if (query in expert['name_cn'].lower() or
                query in expert['name_en'].lower() or
                query in expert.get('org', '').lower() or
                query in expert.get('field', '').lower()):
                results.append(expert)
        
        return results
    
    def export_to_csv(self, csv_file: str = None):
        """导出为 CSV 格式"""
        if csv_file is None:
            csv_file = os.path.join(self.data_dir, 'experts.csv')
        
        experts = self.load_experts()
        
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'name_cn', 'name_en', 'org', 'org_en', 
                'field', 'field_en', 'homepage', 'google_scholar',
                'source', 'last_updated'
            ])
            writer.writeheader()
            writer.writerows(experts)
        
        logger.info(f"已导出 CSV: {csv_file}")
        return csv_file
    
    def export_to_search_csv(self) -> str:
        """导出为查询用的 CSV 格式（简化版）"""
        csv_file = os.path.join(self.data_dir, 'names_mapping.csv')
        experts = self.load_experts()
        
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['中文名', '英文名', '机构', '领域'])
            
            for expert in experts:
                writer.writerow([
                    expert['name_cn'],
                    expert['name_en'],
                    expert.get('org', ''),
                    expert.get('field', '')
                ])
        
        logger.info(f"已导出查询用 CSV: {csv_file}")
        return csv_file
    
    def get_all_experts(self) -> List[Dict]:
        """获取所有专家"""
        return self.load_experts()
    
    def print_experts(self):
        """打印所有专家列表"""
        experts = self.load_experts()
        
        print("\n" + "=" * 80)
        print(f"📋 专家信息库 (共 {len(experts)} 位专家)")
        print("=" * 80)
        
        for i, expert in enumerate(experts, 1):
            print(f"\n{i}. {expert['name_cn']} ({expert['name_en']})")
            print(f"   机构: {expert.get('org', 'N/A')}")
            print(f"   领域: {expert.get('field', 'N/A')}")
            if expert.get('homepage'):
                print(f"   主页: {expert['homepage']}")
        
        print("\n" + "=" * 80)
    
    def update_all(self):
        """更新所有专家信息（预留接口）"""
        logger.info("开始更新专家信息...")
        
        experts = self.load_experts()
        
        # TODO: 接入真实的抓取源
        # 目前只是更新时间戳
        for expert in experts:
            expert['last_updated'] = datetime.now().isoformat()
            expert['source'] = 'auto_updated'
        
        self.save_experts(experts)
        
        # 同时更新查询用的 CSV
        self.export_to_search_csv()
        
        logger.info(f"✅ 更新完成，共 {len(experts)} 位专家")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='专家信息抓取工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # list 命令
    subparsers.add_parser('list', help='列出所有专家')
    
    # add 命令
    add_parser = subparsers.add_parser('add', help='添加专家')
    add_parser.add_argument('--cn', required=True, help='中文名')
    add_parser.add_argument('--en', required=True, help='英文名')
    add_parser.add_argument('--org', default='', help='机构')
    add_parser.add_argument('--field', default='', help='领域')
    add_parser.add_argument('--homepage', default='', help='主页链接')
    
    # update 命令
    update_parser = subparsers.add_parser('update', help='更新专家')
    update_parser.add_argument('--cn', required=True, help='中文名')
    update_parser.add_argument('--org', default='', help='机构')
    update_parser.add_argument('--field', default='', help='领域')
    update_parser.add_argument('--homepage', default='', help='主页链接')
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索专家')
    search_parser.add_argument('query', help='搜索关键词')
    
    # export 命令
    subparsers.add_parser('export', help='导出数据')
    
    # refresh 命令
    subparsers.add_parser('refresh', help='刷新/更新所有专家')
    
    args = parser.parse_args()
    
    crawler = ExpertCrawler()
    
    if args.command == 'list':
        crawler.print_experts()
    
    elif args.command == 'add':
        crawler.add_expert(
            name_cn=args.cn,
            name_en=args.en,
            org=args.org,
            field=args.field,
            homepage=args.homepage
        )
    
    elif args.command == 'update':
        crawler.update_expert(
            name_cn=args.cn,
            org=args.org,
            field=args.field,
            homepage=args.homepage
        )
    
    elif args.command == 'search':
        results = crawler.search_expert(args.query)
        if results:
            print(f"\n🔍 找到 {len(results)} 位专家:")
            for expert in results:
                print(f"  • {expert['name_cn']} ({expert['name_en']}) - {expert.get('org', '')}")
        else:
            print(f"\n❌ 未找到 '{args.query}' 相关专家")
    
    elif args.command == 'export':
        csv_file = crawler.export_to_csv()
        search_csv = crawler.export_to_search_csv()
        print(f"\n✅ 已导出:")
        print(f"   完整数据: {csv_file}")
        print(f"   查询用: {search_csv}")
    
    elif args.command == 'refresh':
        crawler.update_all()
        print("\n✅ 所有专家信息已更新！")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
