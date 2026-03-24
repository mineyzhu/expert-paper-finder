#!/usr/bin/env python3
"""
Expert Paper Finder - Flask 后端服务
提供 REST API 支持 Web UI
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

# 导入查询模块
sys.path.insert(0, os.path.dirname(__file__))
from expert_search import PubMedSearcher, PDFDownloader, ResultExporter

app = Flask(__name__)
CORS(app)

# 配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
RESULTS_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'results')
PDF_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'pdfs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

def is_chinese(s):
    """判断是否包含中文字符"""
    return any('\u4e00' <= c <= '\u9fff' for c in s)

def to_pinyin(name):
    """简单的中文转拼音"""
    # 使用 pypinyin
    try:
        from pypinyin import lazy_pinyin, Style
        chars = [c for c in name if '\u4e00' <= c <= '\u9fff']
        if chars:
            return lazy_pinyin(chars, style=Style.NORMAL)
        return [name]
    except:
        return [name]

def build_search_queries(name):
    """构建搜索查询列表"""
    # 如果不包含中文，直接返回
    if not is_chinese(name):
        # 清理符号
        name_clean = re.sub(r'[^\w\s]', '', name).strip()
        return [name_clean.replace(' ', '+')]
    
    # 中文名转换
    pinyin = to_pinyin(name)
    
    results = []
    if len(pinyin) == 2:
        # 姓 + 名
        results.append(f"{pinyin[0]} {pinyin[1]}")
        results.append(f"{pinyin[1]} {pinyin[0]}")
        results.append(f"{pinyin[0]} {pinyin[1][0]}")
        results.append(pinyin[0])
    elif len(pinyin) >= 3:
        # 姓 + 全名
        given = ''.join(pinyin[1:])
        results.append(f"{pinyin[0]} {given}")
        results.append(f"{given} {pinyin[0]}")
        results.append(f"{pinyin[0]} {given[0]}")
        results.append(pinyin[0])
    
    return results

@app.route('/api/search', methods=['POST'])
def search():
    """查询专家文献"""
    try:
        data = request.json
        author = data.get('author', '').strip()
        affiliation = data.get('affiliation', '').strip()
        months = int(data.get('months', 6))
        max_results = int(data.get('max_results', 100))
        
        if not author:
            return jsonify({'error': '作者名不能为空'}), 400
        
        original_author = author
        is_cn = is_chinese(author)
        
        print(f"[查询] 输入: {author}, 中文: {is_cn}")
        
        # 构建查询列表
        search_queries = build_search_queries(author)
        print(f"[查询] 查询列表: {search_queries}")
        
        # 执行查询
        searcher = PubMedSearcher(api_key=os.getenv('NCBI_API_KEY'))
        all_papers = []
        used_query = None
        
        for query in search_queries:
            # 转换为 PubMed 格式
            pubmed_query = query.replace(' ', '+')
            print(f"[查询] 尝试: {pubmed_query}")
            
            pmids = searcher.search(
                author=pubmed_query,
                affiliation=affiliation or None,
                months=months,
                max_results=max_results
            )
            
            if pmids:
                print(f"[查询] 成功! PMID: {len(pmids)}")
                papers = searcher.fetch_details(pmids)
                all_papers.extend(papers)
                used_query = pubmed_query
                break
        
        if not all_papers:
            return jsonify({
                'query_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'author': author,
                    'original_author': original_author,
                    'affiliation': affiliation,
                    'months': months,
                    'total_results': 0
                },
                'papers': []
            })
        
        # 去重
        seen = set()
        unique_papers = []
        for paper in all_papers:
            if paper['pmid'] not in seen:
                seen.add(paper['pmid'])
                unique_papers.append(paper)
        
        # 保存结果
        result_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = os.path.join(RESULTS_FOLDER, f'result_{result_id}.json')
        
        query_metadata = {
            'timestamp': datetime.now().isoformat(),
            'author': used_query or author,
            'original_author': original_author,
            'affiliation': affiliation,
            'months': months,
            'total_results': len(unique_papers),
            'result_id': result_id
        }
        
        ResultExporter.to_json(unique_papers, result_file, query_metadata)
        
        return jsonify({
            'query_metadata': query_metadata,
            'papers': unique_papers
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/fetch-pdf', methods=['POST'])
def fetch_pdf():
    """下载 PDF"""
    try:
        data = request.json
        result_id = data.get('result_id')
        
        if not result_id:
            return jsonify({'error': 'result_id 不能为空'}), 400
        
        # 加载结果
        result_file = os.path.join(RESULTS_FOLDER, f'result_{result_id}.json')
        if not os.path.exists(result_file):
            return jsonify({'error': '结果文件不存在'}), 404
        
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        papers = result_data.get('papers', [])
        
        # 下载 PDF
        downloader = PDFDownloader(max_workers=5)
        success_count = 0
        
        for paper in papers:
            if downloader.download_pdf(paper, PDF_FOLDER):
                success_count += 1
        
        # 保存更新后的结果
        ResultExporter.to_json(papers, result_file, result_data.get('query_metadata'))
        
        return jsonify({
            'total': len(papers),
            'success': success_count,
            'failed': len(papers) - success_count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export', methods=['POST'])
def export():
    """导出结果"""
    try:
        data = request.json
        result_id = data.get('result_id')
        format_type = data.get('format', 'csv')
        
        if not result_id:
            return jsonify({'error': 'result_id 不能为空'}), 400
        
        # 加载结果
        result_file = os.path.join(RESULTS_FOLDER, f'result_{result_id}.json')
        if not os.path.exists(result_file):
            return jsonify({'error': '结果文件不存在'}), 404
        
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        papers = result_data.get('papers', [])
        query_metadata = result_data.get('query_metadata', {})
        
        # 导出
        export_file = os.path.join(
            RESULTS_FOLDER,
            f'export_{result_id}.{format_type}'
        )
        
        if format_type == 'csv':
            ResultExporter.to_csv(papers, export_file)
        elif format_type == 'markdown':
            ResultExporter.to_markdown(papers, export_file, query_metadata)
        else:
            return jsonify({'error': '不支持的格式'}), 400
        
        return send_file(export_file, as_attachment=True)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/')
def index():
    """提供 Web UI"""
    ui_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'index.html')
    if os.path.exists(ui_path):
        with open(ui_path, 'r', encoding='utf-8') as f:
            return f.read()
    return 'Web UI not found', 404


if __name__ == '__main__':
    print("🚀 Expert Paper Finder API Server")
    print("📍 http://localhost:5000")
    print("📚 Web UI: http://localhost:5000/")
    print("🔗 API: http://localhost:5000/api/")
    print("\n按 Ctrl+C 停止服务器\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
