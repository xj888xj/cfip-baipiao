import os
import requests
import pandas as pd
from tqdm import tqdm
import time

def get_ip_from_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            ips = [line.strip() for line in f if line.strip()]
        return ips
    except FileNotFoundError:
        print(f"文件未找到: {filename}")
        return []
    except IOError as e:
        print(f"读取文件 {filename} 时出错: {e}")
        return []

def ipinfoapi(ips: list, session):
    url = 'http://ip-api.com/batch'
    ips_dict = [{'query': ip, "fields": "city,country,countryCode,isp,org,as,query"} for ip in ips]
    
    try:
        with session.post(url, json=ips_dict) as resp:
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                print('请求过于频繁，正在等待...')
                time.sleep(10)  # 等待10秒后重试
                return ipinfoapi(ips, session)  # 递归重试
            else:
                print(f'获取ip信息失败: {resp.status_code}, {resp.reason}')
                return None
    except Exception as e:
        print(f'requests error: {e}')
        return None

def get_ip_info(ips):
    session = requests.Session()
    ipinfo = []
    
    for i in tqdm(range(0, len(ips), 10)):  # 每10个IP为一组请求
        batch_ips = ips[i:i + 10]
        result = ipinfoapi(batch_ips, session)
        if result:
            ipinfo.extend(result)
        time.sleep(2)  # 每批请求之间的延迟
    return ipinfo

def gatherip(port):
    filename = f"iplist_{port}.txt"
    return get_ip_from_file(filename)

def process_ipinfo(ipinfo, port):
    # 检查返回的数据是否包含所需的字段
    if not ipinfo or 'countryCode' not in ipinfo[0]:
        print("返回的数据不包含'countryCode'字段，无法处理。")
        return

    save_dir = f"./ip{port}/"

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    grouped = pd.DataFrame(ipinfo).groupby('countryCode')
    for countryCode, group in grouped:
        only_ip = group['query'].drop_duplicates()
        only_ip.to_csv(save_dir + countryCode + '.txt', header=None, index=False)

def main(port):
    ips = gatherip(port)
    print(f'Total ips: {len(ips)}')
    ipinfo = get_ip_info(ips)
    process_ipinfo(ipinfo, port)

if __name__ == "__main__":
    main(8443)
