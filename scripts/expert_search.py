#!/usr/bin/env python3
"""
Expert Paper Finder - PubMed 专家文献检索工具
查询专家最近发表的论文，获取元数据和 PDF
"""

import argparse
import json
import csv
import os
import sys
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlencode
import logging
import xml.etree.ElementTree as ET

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PubMedSearcher:
    """PubMed 文献查询器"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('NCBI_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ExpertPaperFinder/1.0 (compatible; NCBI)'
        })
        # 速率限制：无 API Key 时 3 req/s，有 Key 时 10 req/s
        self.delay = 0.4 if self.api_key else 0.35
    
    def _build_query(self, author: str, affiliation: Optional[str] = None, 
                     months: int = 6) -> str:
        """构建 PubMed 查询字符串 - 优化版，更精确匹配"""
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)
        
        date_range = f"{start_date.strftime('%Y/%m/%d')}[PDAT] : {end_date.strftime('%Y/%m/%d')}[PDAT]"
        
        # 解析作者名
        # 如果是 "姓 名" 格式（如 "Zhang Zemin"），拆分为姓和名
        name_parts = author.strip().split()
        
        if len(name_parts) >= 2:
            # 完整名字：姓 + 名
            last_name = name_parts[0]
            first_name = name_parts[1]
            
            # 使用 "姓[AU] AND 名[Author]" 格式进行精确匹配
            # 这是 PubMed 推荐的方式
            query_parts = [
                f'{last_name}[AU]',  # 作者字段 - 姓
                f'FirstName[{first_name}]',  # 名
                date_range
            ]
        else:
            # 只有姓或缩写
            query_parts = [
                f'{author}[AU]',  # 作者字段
                date_range
            ]
        
        if affiliation:
            query_parts.append(f'{affiliation}[Affiliation]')
        
        return ' AND '.join(query_parts)
    
    def search(self, author: str, affiliation: Optional[str] = None, 
               months: int = 6, max_results: int = 100) -> List[str]:
        """
        搜索 PubMed，返回 PMID 列表
        
        Args:
            author: 作者名（支持中英文）
            affiliation: 机构名（可选）
            months: 查询范围（月数）
            max_results: 最大结果数
        
        Returns:
            PMID 列表
        """
        query = self._build_query(author, affiliation, months)
        logger.info(f"查询: {query}")
        
        params = {
            'db': 'pubmed',
            'term': query,
            'rettype': 'xml',  # 改为 XML
            'retmax': max_results,
            'tool': 'ExpertPaperFinder',
            'email': 'noreply@example.com'
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/esearch.fcgi",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            # 解析 XML 响应
            root = ET.fromstring(response.text)
            pmids = []
            for id_elem in root.findall('.//Id'):
                if id_elem.text:
                    pmids.append(id_elem.text)
            
            count_elem = root.find('.//Count')
            total = int(count_elem.text) if count_elem is not None else 0
            
            logger.info(f"找到 {total} 篇论文，返回 {len(pmids)} 个 PMID")
            return pmids
            
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return []
    
    def fetch_details(self, pmids: List[str]) -> List[Dict]:
        """
        获取论文详细信息
        
        Args:
            pmids: PMID 列表
        
        Returns:
            论文信息字典列表
        """
        if not pmids:
            return []
        
        papers = []
        batch_size = 100
        
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i+batch_size]
            logger.info(f"获取详情: {i+1}-{min(i+batch_size, len(pmids))}/{len(pmids)}")
            
            params = {
                'db': 'pubmed',
                'id': ','.join(batch),
                'rettype': 'xml',  # 改为 XML
                'tool': 'ExpertPaperFinder',
                'email': 'noreply@example.com'
            }
            
            if self.api_key:
                params['api_key'] = self.api_key
            
            try:
                response = self.session.get(
                    f"{self.BASE_URL}/efetch.fcgi",
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                
                # 解析 XML 响应
                root = ET.fromstring(response.text)
                
                for article_elem in root.findall('.//PubmedArticle'):
                    pmid_elem = article_elem.find('.//PMID')
                    if pmid_elem is not None and pmid_elem.text:
                        pmid = pmid_elem.text
                        paper = self._parse_article_xml(pmid, article_elem)
                        papers.append(paper)
                
                time.sleep(self.delay)
                
            except Exception as e:
                logger.error(f"获取详情失败: {e}")
                continue
        
        return papers
    
    def _parse_article(self, pmid: str, article: Dict) -> Dict:
        """解析单篇论文信息"""
        
        # 基本信息
        title = article.get('title', 'N/A')
        
        # 作者
        authors = []
        for author in article.get('authors', []):
            name = author.get('name', '')
            if name:
                authors.append(name)
        
        # 发表日期
        pub_date_str = 'N/A'
        pub_year = None
        pub_month = None
        
        if 'pubdate' in article:
            pub_date_str = article['pubdate']
            try:
                # 尝试解析日期
                date_obj = datetime.strptime(pub_date_str, '%Y %b %d')
                pub_year = date_obj.year
                pub_month = date_obj.month
            except:
                try:
                    date_obj = datetime.strptime(pub_date_str, '%Y %b')
                    pub_year = date_obj.year
                    pub_month = date_obj.month
                except:
                    pass
        
        # 期刊
        journal = article.get('source', 'N/A')
        
        # DOI
        doi = 'N/A'
        for aid in article.get('articleids', []):
            if aid.get('idtype') == 'doi':
                doi = aid.get('value', 'N/A')
                break
        
        # 摘要
        abstract = article.get('abstract', 'N/A')
        if isinstance(abstract, list):
            abstract = ' '.join(abstract)
        
        # 关键词
        keywords = []
        for kw in article.get('keywords', []):
            if isinstance(kw, dict):
                keywords.append(kw.get('value', ''))
            else:
                keywords.append(str(kw))
        
        # PDF URL
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmid}/pdf/" if pmid else 'N/A'
        
        return {
            'pmid': pmid,
            'title': title,
            'authors': authors,
            'journal': journal,
            'pub_date': pub_date_str,
            'pub_year': pub_year,
            'pub_month': pub_month,
            'doi': doi,
            'abstract': abstract,
            'keywords': keywords,
            'pdf_url': pdf_url,
            'pdf_status': 'unknown',
            'pubmed_url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            'doi_url': f"https://doi.org/{doi}" if doi != 'N/A' else 'N/A'
        }

    # 月份映射表
    MONTH_MAP = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
        'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    def _parse_article_xml(self, pmid: str, article_elem: ET.Element) -> Dict:
        """从 XML 元素解析单篇论文信息"""
        
        # 标题
        title_elem = article_elem.find('.//ArticleTitle')
        title = title_elem.text if title_elem is not None else 'N/A'
        
        # 作者
        authors = []
        for author_elem in article_elem.findall('.//Author'):
            last_name = author_elem.find('LastName')
            first_name = author_elem.find('ForeName')
            if last_name is not None and last_name.text:
                name = last_name.text
                if first_name is not None and first_name.text:
                    name = f"{first_name.text} {name}"
                authors.append(name)
        
        # 期刊
        journal_elem = article_elem.find('.//Journal/Title')
        journal = journal_elem.text if journal_elem is not None else 'N/A'
        
        # 发表日期
        pub_date_str = 'N/A'
        pub_year = None
        pub_month = None
        
        pub_date_elem = article_elem.find('.//PubDate')
        if pub_date_elem is not None:
            year_elem = pub_date_elem.find('Year')
            month_elem = pub_date_elem.find('Month')
            day_elem = pub_date_elem.find('Day')
            
            if year_elem is not None and year_elem.text:
                pub_year = int(year_elem.text)
                month_raw = month_elem.text.lower() if month_elem is not None and month_elem.text else '01'
                day_str = day_elem.text if day_elem is not None and day_elem.text else '01'
                
                # 尝试转换月份
                month_num = self.MONTH_MAP.get(month_raw, 1)
                pub_month = month_num
                pub_date_str = f"{pub_year}-{month_num:0>2}-{day_str:0>2}"
        
        # DOI
        doi = 'N/A'
        for article_id in article_elem.findall('.//ArticleId'):
            if article_id.get('IdType') == 'doi':
                doi = article_id.text if article_id.text else 'N/A'
                break
        
        # 摘要
        abstract_elem = article_elem.find('.//Abstract/AbstractText')
        abstract = abstract_elem.text if abstract_elem is not None else 'N/A'
        
        # 关键词
        keywords = []
        for keyword_elem in article_elem.findall('.//Keyword'):
            if keyword_elem.text:
                keywords.append(keyword_elem.text)
        
        # PDF URL
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmid}/pdf/" if pmid else 'N/A'
        
        return {
            'pmid': pmid,
            'title': title,
            'authors': authors,
            'journal': journal,
            'pub_date': pub_date_str,
            'pub_year': pub_year,
            'pub_month': pub_month,
            'doi': doi,
            'abstract': abstract,
            'keywords': keywords,
            'pdf_url': pdf_url,
            'pdf_status': 'unknown',
            'pubmed_url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            'doi_url': f"https://doi.org/{doi}" if doi != 'N/A' else 'N/A'
        }


class PDFDownloader:
    """PDF 下载器"""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.session = requests.Session()
    
    def download_pdf(self, paper: Dict, output_dir: str) -> bool:
        """
        下载单篇论文的 PDF
        
        Args:
            paper: 论文信息字典
            output_dir: 输出目录
        
        Returns:
            是否下载成功
        """
        pmid = paper['pmid']
        pdf_url = paper['pdf_url']
        
        if pdf_url == 'N/A':
            logger.warning(f"PMID {pmid}: 无 PDF 链接")
            return False
        
        output_path = os.path.join(output_dir, f"{pmid}.pdf")
        
        try:
            response = self.session.get(pdf_url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"PMID {pmid}: 下载成功 -> {output_path}")
            paper['pdf_local_path'] = output_path
            paper['pdf_status'] = 'downloaded'
            return True
            
        except Exception as e:
            logger.warning(f"PMID {pmid}: 下载失败 - {e}")
            paper['pdf_status'] = 'failed'
            return False


class ResultExporter:
    """结果导出器"""
    
    @staticmethod
    def to_json(papers: List[Dict], output_path: str, query_metadata: Dict = None):
        """导出为 JSON"""
        result = {
            'query_metadata': query_metadata or {},
            'papers': papers
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已导出 JSON: {output_path}")
    
    @staticmethod
    def to_csv(papers: List[Dict], output_path: str):
        """导出为 CSV"""
        if not papers:
            logger.warning("没有数据可导出")
            return
        
        fieldnames = [
            'PMID', '标题', '作者', '期刊', '发表日期', 'DOI',
            'PDF状态', 'PDF链接', 'PubMed链接'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for paper in papers:
                writer.writerow({
                    'PMID': paper['pmid'],
                    '标题': paper['title'],
                    '作者': '; '.join(paper['authors']),
                    '期刊': paper['journal'],
                    '发表日期': paper['pub_date'],
                    'DOI': paper['doi'],
                    'PDF状态': paper['pdf_status'],
                    'PDF链接': paper['pdf_url'],
                    'PubMed链接': paper['pubmed_url']
                })
        
        logger.info(f"已导出 CSV: {output_path}")
    
    @staticmethod
    def to_markdown(papers: List[Dict], output_path: str, query_metadata: Dict = None):
        """导出为 Markdown"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 专家文献检索报告\n\n")
            
            if query_metadata:
                f.write("## 查询信息\n\n")
                f.write(f"- **查询对象**: {query_metadata.get('author', 'N/A')}\n")
                if query_metadata.get('affiliation'):
                    f.write(f"- **机构**: {query_metadata['affiliation']}\n")
                f.write(f"- **查询时间**: {query_metadata.get('timestamp', 'N/A')}\n")
                f.write(f"- **查询范围**: 最近 {query_metadata.get('months', 6)} 个月\n")
                f.write(f"- **总计**: {len(papers)} 篇论文\n\n")
            
            f.write("## 文献列表\n\n")
            
            for idx, paper in enumerate(papers, 1):
                f.write(f"### {idx}. {paper['title']}\n\n")
                f.write(f"- **PMID**: {paper['pmid']}\n")
                f.write(f"- **作者**: {'; '.join(paper['authors'])}\n")
                f.write(f"- **期刊**: {paper['journal']}\n")
                f.write(f"- **发表日期**: {paper['pub_date']}\n")
                f.write(f"- **DOI**: {paper['doi']}\n")
                
                if paper['abstract'] != 'N/A':
                    f.write(f"- **摘要**: {paper['abstract'][:200]}...\n")
                
                f.write(f"- **链接**: ")
                links = []
                if paper['pdf_url'] != 'N/A':
                    links.append(f"[PDF]({paper['pdf_url']})")
                links.append(f"[PubMed]({paper['pubmed_url']})")
                if paper['doi_url'] != 'N/A':
                    links.append(f"[DOI]({paper['doi_url']})")
                f.write(" | ".join(links) + "\n\n")
        
        logger.info(f"已导出 Markdown: {output_path}")


def cmd_search(args):
    """执行搜索命令"""
    searcher = PubMedSearcher(api_key=args.api_key)
    
    # 单个查询
    if args.author:
        logger.info(f"查询专家: {args.author}")
        pmids = searcher.search(
            author=args.author,
            affiliation=args.affiliation,
            months=args.months,
            max_results=args.max_results
        )
        
        if not pmids:
            logger.warning("未找到相关论文")
            return
        
        papers = searcher.fetch_details(pmids)
        
        # 保存结果
        query_metadata = {
            'timestamp': datetime.now().isoformat(),
            'author': args.author,
            'affiliation': args.affiliation or 'N/A',
            'months': args.months,
            'total_results': len(papers)
        }
        
        output_path = args.output or 'results.json'
        ResultExporter.to_json(papers, output_path, query_metadata)
        
        logger.info(f"✓ 查询完成，共 {len(papers)} 篇论文")
    
    # 批量查询
    elif args.batch:
        logger.info(f"批量查询: {args.batch}")
        all_papers = []
        
        with open(args.batch, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                author = row.get('author', '').strip()
                affiliation = row.get('affiliation', '').strip()
                
                if not author:
                    continue
                
                logger.info(f"查询: {author} ({affiliation})")
                pmids = searcher.search(
                    author=author,
                    affiliation=affiliation or None,
                    months=args.months,
                    max_results=args.max_results
                )
                
                papers = searcher.fetch_details(pmids)
                all_papers.extend(papers)
                time.sleep(1)  # 批量查询间隔
        
        output_path = args.output or 'batch_results.json'
        ResultExporter.to_json(all_papers, output_path, {
            'timestamp': datetime.now().isoformat(),
            'batch_file': args.batch,
            'months': args.months,
            'total_results': len(all_papers)
        })
        
        logger.info(f"✓ 批量查询完成，共 {len(all_papers)} 篇论文")


def cmd_fetch_pdf(args):
    """执行 PDF 下载命令"""
    # 加载结果
    if not os.path.exists(args.input):
        logger.error(f"输入文件不存在: {args.input}")
        return
    
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    papers = data.get('papers', [])
    logger.info(f"准备下载 {len(papers)} 篇论文的 PDF")
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    
    # 下载 PDF
    downloader = PDFDownloader(max_workers=args.max_workers)
    success_count = 0
    
    for paper in papers:
        if downloader.download_pdf(paper, args.output):
            success_count += 1
        time.sleep(0.5)  # 下载间隔
    
    # 保存更新后的结果
    ResultExporter.to_json(papers, args.input, data.get('query_metadata'))
    
    logger.info(f"✓ PDF 下载完成: {success_count}/{len(papers)} 成功")


def cmd_export(args):
    """执行导出命令"""
    if not os.path.exists(args.input):
        logger.error(f"输入文件不存在: {args.input}")
        return
    
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    papers = data.get('papers', [])
    query_metadata = data.get('query_metadata', {})
    
    if args.format == 'csv':
        ResultExporter.to_csv(papers, args.output)
    elif args.format == 'markdown':
        ResultExporter.to_markdown(papers, args.output, query_metadata)
    elif args.format == 'json':
        ResultExporter.to_json(papers, args.output, query_metadata)
    
    logger.info(f"✓ 导出完成: {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description='专家文献检索工具 - 查询专家最近发表的论文'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='查询专家文献')
    search_parser.add_argument('--author', help='作者名')
    search_parser.add_argument('--affiliation', help='机构名')
    search_parser.add_argument('--batch', help='批量查询 CSV 文件')
    search_parser.add_argument('--months', type=int, default=6, help='查询范围（月数）')
    search_parser.add_argument('--max-results', type=int, default=100, help='最大结果数')
    search_parser.add_argument('--output', default='results.json', help='输出文件')
    search_parser.add_argument('--api-key', help='NCBI API Key')
    search_parser.set_defaults(func=cmd_search)
    
    # fetch-pdf 命令
    pdf_parser = subparsers.add_parser('fetch-pdf', help='下载 PDF')
    pdf_parser.add_argument('--input', required=True, help='输入 JSON 文件')
    pdf_parser.add_argument('--output', default='./pdfs', help='输出目录')
    pdf_parser.add_argument('--max-workers', type=int, default=5, help='并发数')
    pdf_parser.set_defaults(func=cmd_fetch_pdf)
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出结果')
    export_parser.add_argument('--input', required=True, help='输入 JSON 文件')
    export_parser.add_argument('--format', choices=['csv', 'markdown', 'json'], 
                              default='csv', help='输出格式')
    export_parser.add_argument('--output', required=True, help='输出文件')
    export_parser.set_defaults(func=cmd_export)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == '__main__':
    main()
