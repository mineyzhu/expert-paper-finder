#!/usr/bin/env python3
"""
中文姓名转拼音工具
使用 pypinyin 库将中文姓名转换为多种拼音格式
"""

try:
    from pypinyin import lazy_pinyin, Style
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False

def is_chinese(char):
    """判断是否是中文字符"""
    return '\u4e00' <= char <= '\u9fff'

def chinese_to_pinyin(name):
    """中文名转拼音列表"""
    if not name:
        return []
    
    # 清理
    name = name.strip()
    if not name:
        return []
    
    # 如果不包含中文，直接返回原名
    if not any(is_chinese(c) for c in name):
        return [name]
    
    if not HAS_PYPINYIN:
        # 没有 pypinyin，返回原名
        return [name]
    
    # 使用 pypinyin 转换
    # 拆分为单个汉字
    chars = [c for c in name if is_chinese(c)]
    
    if len(chars) == 0:
        return [name]
    
    # 获取带声标的完整拼音
    full_pinyin = lazy_pinyin(chars, style=Style.NORMAL)
    
    results = []
    
    if len(chars) == 1:
        # 只有一个字
        results.append(full_pinyin[0])
    elif len(chars) == 2:
        # 两个字：姓 + 名
        surname = full_pinyin[0]
        given = full_pinyin[1]
        
        # 全拼：姓 名
        results.append(f"{surname} {given}")
        # 全拼：名 姓
        results.append(f"{given} {surname}")
        # 缩写：姓 首字母
        results.append(f"{surname} {given[0]}")
        # 单独姓
        results.append(surname)
        # 单独名
        results.append(given)
    elif len(chars) >= 3:
        # 三个字及以上
        surname = full_pinyin[0]
        given_parts = full_pinyin[1:]
        given_full = ''.join(given_parts)
        given_first = ''.join([p[0] for p in given_parts])
        
        # 全拼：姓 + 全名
        results.append(f"{surname} {given_full}")
        # 全拼：全名 + 姓
        results.append(f"{given_full} {surname}")
        # 缩写：姓 + 名首字母
        results.append(f"{surname} {given_first}")
        # 单独姓
        results.append(surname)
        # 单独名
        results.append(given_full)
    
    # 去重，保持顺序
    seen = set()
    unique_results = []
    for r in results:
        if r not in seen and r:
            seen.add(r)
            unique_results.append(r)
    
    return unique_results

def name_to_search_queries(name):
    """中文名转换为搜索查询列表"""
    pinyin_list = chinese_to_pinyin(name)
    
    queries = []
    for pinyin in pinyin_list:
        # 替换空格为 +（PubMed 搜索格式）
        query = pinyin.replace(' ', '+')
        queries.append(query)
    
    return queries

def is_chinese_name(name):
    """判断是否是中文名"""
    return any(is_chinese(c) for c in name)

# 测试
if __name__ == '__main__':
    test_names = ['张泽民', '李明', '王芳', '方翘', '赵乾坤']
    
    for name in test_names:
        print(f"\n{name}:")
        queries = name_to_search_queries(name)
        for q in queries[:5]:  # 只显示前5个
            print(f"  - {q}")
