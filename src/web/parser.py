import re
from datetime import datetime
from typing import Optional, Tuple


def parse_export_command(text: str) -> Optional[dict]:
    """
    解析自然语言导出命令，提取店铺名称、店铺ID和时间范围
    
    示例输入：
    "请帮我导出修丽可官方旗舰店店铺ID为8226405从2026年2月9日10点到2026年2月9日17点的数据"
    
    返回格式：
    {
        "shop_name": "修丽可官方旗舰店",
        "shop_id": "8226405",
        "start_time": "2026-02-09 10:00",
        "end_time": "2026-02-09 17:00"
    }
    """
    pattern = r"请帮我导出(.+?)店铺ID为(\d+)从(\d{4})年(\d{1,2})月(\d{1,2})日(\d{1,2})点到(\d{4})年(\d{1,2})月(\d{1,2})日(\d{1,2})点的数据"
    
    match = re.search(pattern, text)
    if not match:
        return None
    
    shop_name = match.group(1).strip()
    shop_id = match.group(2)
    
    start_year = match.group(3)
    start_month = match.group(4).zfill(2)
    start_day = match.group(5).zfill(2)
    start_hour = match.group(6).zfill(2)
    
    end_year = match.group(7)
    end_month = match.group(8).zfill(2)
    end_day = match.group(9).zfill(2)
    end_hour = match.group(10).zfill(2)
    
    start_time = f"{start_year}-{start_month}-{start_day} {start_hour}:00"
    end_time = f"{end_year}-{end_month}-{end_day} {end_hour}:00"
    
    return {
        "shop_name": shop_name,
        "shop_id": shop_id,
        "start_time": start_time,
        "end_time": end_time
    }


def validate_time_range(start_time: str, end_time: str) -> Tuple[bool, str]:
    """
    验证时间范围是否合理
    """
    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M")
        
        if end_dt <= start_dt:
            return False, "结束时间必须大于开始时间"
        
        if end_dt > datetime.now():
            return False, "结束时间不能晚于当前时间"
        
        time_diff = (end_dt - start_dt).total_seconds() / 3600
        if time_diff > 168:
            return False, "时间范围不能超过7天（168小时）"
        
        return True, "时间范围有效"
    except Exception as e:
        return False, f"时间格式错误: {str(e)}"
