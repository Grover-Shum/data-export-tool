import argparse
import json
import sys

import requests

URL = "https://serviceagent.bytehiservice.com/pigeonproxy/log/v2/conversation/export"


def parse_args():
    parser = argparse.ArgumentParser(description="Call export API and return tos_key")
    parser.add_argument("--shop_id", required=True)
    parser.add_argument("--start_time", required=True, help="start timestamp in ms")
    parser.add_argument("--end_time", required=True, help="end timestamp in ms")
    parser.add_argument("--min_message_count", type=int, default=1)
    parser.add_argument("--max_message_count", type=int, default=999)
    parser.add_argument("--page_size", type=int, default=5000)
    parser.add_argument("--page_num", type=int, default=1)
    parser.add_argument("--tenant_id", default="")
    parser.add_argument("--user_name", default="")
    parser.add_argument("--user_id", default="")
    return parser.parse_args()


def main():
    args = parse_args()

    payload = {
        "shop_id": args.shop_id,
        "create_time_range": {
            "start_time": str(args.start_time),
            "end_time": str(args.end_time),
        },
        "min_message_count": args.min_message_count,
        "max_message_count": args.max_message_count,
        "page_size": args.page_size,
        "page_num": args.page_num,
        "tenant_id": args.tenant_id,
        "user_name": args.user_name,
        "user_id": args.user_id,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "User-Agent": "PostmanRuntime-ApipostRuntime/1.1.0",
        "x-tt-env": "ppe_wp_pigeonproxy",
        "x-use-ppe": "1",
    }

    try:
        resp = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f"[data_download] request failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        data = resp.json()
    except Exception:
        print(f"[data_download] response is not valid JSON. Status: {resp.status_code}", file=sys.stderr)
        sys.exit(1)

    # 根据实际返回结构调整
    tos_key = None
    try:
        # 尝试从 deep path 获取: data -> base_resp -> extra -> tos_key
        if isinstance(data, dict) and "data" in data:
            d = data["data"]
            if isinstance(d, dict):
                base_resp = d.get("base_resp", {})
                extra = base_resp.get("extra", {})
                tos_key = extra.get("tos_key")
        
        # 如果上面没找到，尝试旧逻辑
        if not tos_key and isinstance(data, dict):
            inner = data.get("data") if isinstance(data.get("data"), dict) else data
            tos_key = inner.get("tos_key") if isinstance(inner, dict) else None
    except Exception:
        pass

    if not tos_key:
        print(f"[data_download] tos_key not found in response: {data}", file=sys.stderr)
        sys.exit(1)

    # 只打印 tos_key，方便上游脚本读取
    print(tos_key)


if __name__ == "__main__":
    main()
