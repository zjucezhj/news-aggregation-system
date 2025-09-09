import pandas as pd
import json
import pickle
from bs4 import BeautifulSoup
import os

def save_data(data, path, data_type=None, mode='w', **kwargs):
    """
    通用数据保存函数，根据数据类型自动选择保存方式
    
    参数:
    data: 要保存的数据
    path: 项目名称/文件名(不含扩展名)
    data_type: 数据类型('html', 'excel', 'json', 'pkl')，如果为None则自动推断
    mode: 文件模式('w'写入, 'a'追加等)
    **kwargs: 其他参数，如:
        - 对于HTML: level, head, sheet_name等
        - 对于Excel: sheet_name, engine等
    """
    # 如果没有指定数据类型，则尝试自动推断
    if data_type is None:
        if isinstance(data, BeautifulSoup):
            data_type = 'html'
        elif isinstance(data, pd.DataFrame):
            data_type = 'xlsx'
        elif isinstance(data, (list, dict)):
            data_type = 'json'
        else:
            data_type = 'pkl'  # 默认为pickle
    
    # 构建完整文件路径
    file_path = f"{path}.{data_type}"
    
    # 确保文件所在目录存在
    directory = os.path.dirname(file_path)
    if directory:  # 如果路径包含目录部分
        os.makedirs(directory, exist_ok=True)
    
    # 定义处理函数字典
    handlers = {
        'html': lambda: _save_html(data, path, mode, **kwargs),
        'xlsx': lambda: _save_excel(data, path, mode, **kwargs),
        'json': lambda: _save_json(data, path, mode, **kwargs),
        'pkl': lambda: _save_pkl(data, path, mode, **kwargs)
    }
    
    # 获取处理函数并执行，如果类型不存在则使用默认处理
    handler = handlers.get(data_type, lambda: print(f"未知数据类型: {data_type}"))
    handler()

def _save_html(data, path, mode, **kwargs):
    """保存HTML数据"""
    level = kwargs.get('level', 2)
    head = kwargs.get('head', 'Content')

    with open(f"{path}.html", mode, encoding="utf-8") as f:
        content_buffer = [
            "<div class='container'>",
            f"  <h{level}>{head}</h{level}>",
            f"  {str(data)}",
            "</div>"
        ]
        f.write('\n'.join(content_buffer))
    print(f"HTML数据已保存到 {path}.html")

def _save_excel(data, path, mode, **kwargs):
    """保存Excel数据"""
    sheet_name = kwargs.get('sheet_name', 'Sheet1')
    engine = kwargs.get('engine', 'openpyxl')
    
    # Excel有不同的处理方式
    if mode == 'a' or os.path.exists(f"{path}.xlsx"):
        # 追加模式，文件已存在
        with pd.ExcelWriter(f"{path}.xlsx", engine=engine, mode='a', if_sheet_exists='replace') as writer:
            data.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        # 写入模式或文件不存在
        with pd.ExcelWriter(f"{path}.xlsx", engine=engine, mode='w') as writer:
            data.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"Excel数据已保存到 {path}.xlsx")

def _save_json(data, path, mode, **kwargs):
    """保存JSON数据"""
    with open(f"{path}.json", mode, encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"JSON数据已保存到 {path}.json")

def _save_pkl(data, path, mode, **kwargs):
    """保存Pickle数据"""
    mode = 'wb' if mode == 'w' else 'ab'  # 处理二进制模式
    with open(f"{path}.pkl", mode) as f:
        pickle.dump(data, f)
    print(f"Pickle数据已保存到 {path}.pkl")


def load_data(path, data_type=None, **kwargs):
    """
    通用数据读取函数，根据文件后缀自动判断文件类型
    
    参数:
    path: 文件路径(可以包含扩展名，也可以不包含)
    data_type: 数据类型('html', 'excel', 'json', 'pkl')，如果为None则自动推断
    **kwargs: 其他参数，如:
        - 对于Excel: sheet_name, engine等
        - 对于HTML: parser等
    
    返回:
    读取的数据对象
    """
    # 如果没有指定数据类型，则从文件扩展名推断
    if data_type is None:
        # 获取文件扩展名
        _, ext = os.path.splitext(path)
        if ext:
            data_type = ext[1:]  # 去掉点号
        else:
            # 如果没有扩展名，尝试常见扩展名
            for ext in ['xlsx', 'json', 'pkl', 'html']:
                if os.path.exists(f"{path}.{ext}"):
                    data_type = ext
                    path = f"{path}.{ext}"
                    break
            else:
                raise ValueError(f"无法推断文件类型，请提供明确的文件路径或数据类型: {path}")
    
    # 确保文件存在
    if not path.endswith(f".{data_type}"):
        file_path = f"{path}.{data_type}"
    else:
        file_path = path
        
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 定义处理函数字典
    handlers = {
        'html': lambda: _load_html(file_path, **kwargs),
        'xlsx': lambda: _load_excel(file_path, **kwargs),
        'json': lambda: _load_json(file_path, **kwargs),
        'pkl': lambda: _load_pkl(file_path, **kwargs)
    }
    
    # 获取处理函数并执行，如果类型不存在则抛出异常
    if data_type not in handlers:
        raise ValueError(f"不支持的数据类型: {data_type}")
    
    return handlers[data_type]()

def _load_html(path, **kwargs):
    """读取HTML数据"""
    parser = kwargs.get('parser', 'html.parser')
    with open(path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), parser)
    print(f"HTML数据已从 {path} 读取")
    return soup

def _load_excel(path, **kwargs):
    """读取Excel数据"""
    sheet_name = kwargs.get('sheet_name', 0)  # 默认为第一个sheet
    engine = kwargs.get('engine', None)
    df = pd.read_excel(path, sheet_name=sheet_name, engine=engine)
    print(f"Excel数据已从 {path} 读取")
    return df

def _load_json(path, **kwargs):
    """读取JSON数据"""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"JSON数据已从 {path} 读取")
    return data

def _load_pkl(path, **kwargs):
    """读取Pickle数据"""
    with open(path, 'rb') as f:
        data = pickle.load(f)
    print(f"Pickle数据已从 {path} 读取")
    return data