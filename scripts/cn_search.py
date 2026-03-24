#!/usr/bin/env python3
"""
中文名查询工具
直接输入中文名，自动转换为英文名进行查询
"""

import csv
import sys
import os

def load_names_mapping(csv_file):
    """加载名字对应表"""
    mapping = {}
    if not os.path.exists(csv_file):
        return mapping
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 中文名 -> 英文名
            cn_name = row.get('中文名', '').strip()
            en_name = row.get('英文名', '').strip()
            if cn_name and en_name:
                mapping[cn_name] = {
                    'en_name': en_name,
                    'org': row.get('机构', '').strip(),
                    'field': row.get('领域', '').strip()
                }
    
    return mapping

def search_by_chinese_name(cn_name, csv_file):
    """用中文名查询"""
    mapping = load_names_mapping(csv_file)
    
    if cn_name in mapping:
        info = mapping[cn_name]
        print(f"\n✅ 找到对应信息：")
        print(f"   中文名: {cn_name}")
        print(f"   英文名: {info['en_name']}")
        print(f"   机构: {info['org']}")
        print(f"   领域: {info['field']}")
        return info['en_name'], info.get('org', '')
    else:
        print(f"\n❌ 未找到 '{cn_name}' 的对应信息")
        print(f"\n📝 当前支持的中文名：")
        for cn, info in mapping.items():
            print(f"   - {cn} -> {info['en_name']}")
        return None, None

def add_mapping(cn_name, en_name, org='', field='', csv_file='data/names_mapping.csv'):
    """添加新的名字对应"""
    # 检查文件是否存在
    file_exists = os.path.exists(csv_file)
    
    with open(csv_file, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # 如果文件不存在，写入表头
        if not file_exists:
            writer.writerow(['中文名', '英文名', '机构', '领域'])
        
        # 写入新记录
        writer.writerow([cn_name, en_name, org, field])
    
    print(f"✅ 已添加: {cn_name} -> {en_name}")

def main():
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, '..', 'data', 'names_mapping.csv')
    csv_file = os.path.normpath(csv_file)
    
    if len(sys.argv) < 2:
        print("=" * 60)
        print("🔍 中文名查询工具")
        print("=" * 60)
        print("\n用法:")
        print("  python3 cn_search.py <中文名>              # 查询")
        print("  python3 cn_search.py add <中文名> <英文名> # 添加")
        print("  python3 cn_search.py list                 # 列出所有")
        print("\n示例:")
        print("  python3 cn_search.py 张泽民")
        print("  python3 cn_search.py add 李明 Li Ming")
        print("  python3 cn_search.py list")
        print("\n📁 名字对应表: data/names_mapping.csv")
        print("=" * 60)
        
        # 显示当前支持的名字
        mapping = load_names_mapping(csv_file)
        if mapping:
            print("\n✅ 已配置的中文名：")
            for cn, info in mapping.items():
                print(f"   • {cn} -> {info['en_name']}")
        return
    
    command = sys.argv[1]
    
    if command == 'list':
        # 列出所有
        mapping = load_names_mapping(csv_file)
        if not mapping:
            print("❌ 名字对应表为空")
            print(f"   编辑文件添加: {csv_file}")
            return
        
        print("\n📋 名字对应表：")
        print("-" * 60)
        for cn, info in mapping.items():
            print(f"  {cn:10s} -> {info['en_name']:20s} ({info['org']})")
        print("-" * 60)
    
    elif command == 'add':
        if len(sys.argv) < 4:
            print("❌ 请提供中文名和英文名")
            print("   示例: python3 cn_search.py add 张三 Zhang San")
            return
        
        cn_name = sys.argv[2]
        en_name = sys.argv[3]
        org = sys.argv[4] if len(sys.argv) > 4 else ''
        field = sys.argv[5] if len(sys.argv) > 5 else ''
        
        add_mapping(cn_name, en_name, org, field, csv_file)
    
    else:
        # 假设是中文名，查询
        cn_name = command
        en_name, org = search_by_chinese_name(cn_name, csv_file)
        
        if en_name:
            # 自动调用 expert_search.py 进行查询
            print(f"\n🔍 正在用英文名查询...")
            
            # 构建命令
            cmd_parts = ['python3', 'scripts/expert_search.py', 'search', 
                        '--author', en_name,
                        '--months', '12',
                        '--max-results', '50']
            
            if org:
                cmd_parts.extend(['--affiliation', org])
            
            cmd = ' '.join(cmd_parts)
            print(f"\n📝 执行命令: {cmd}\n")
            
            os.system(cmd)

if __name__ == '__main__':
    main()
