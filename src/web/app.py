import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import uuid
import platform

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io

sys.path.insert(0, str(Path(__file__).parent.parent))

from web.parser import parse_export_command, validate_time_range

DEF_TZ = "Asia/Shanghai"

TEMP_EXPORT_DIR = Path(tempfile.gettempdir()) / "data_export_temp"
TEMP_EXPORT_DIR.mkdir(exist_ok=True)

file_cache = {}

app = FastAPI(title="数据导出工具", description="电商客服数据导出Web工具")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExportRequest(BaseModel):
    text: str


def get_pigeon_binary() -> Path:
    """根据操作系统选择对应的pigeon可执行文件"""
    tools_dir = Path(__file__).parent.parent / "tools"
    
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "darwin":
        if "arm" in machine or "aarch64" in machine:
            binary_name = "pigeon_conversation-mac-arm"
        else:
            binary_name = "pigeon_conversation-mac-x64"
    elif system == "linux":
        if "arm" in machine or "aarch64" in machine:
            binary_name = "pigeon_conversation-linux-arm"
        else:
            binary_name = "pigeon_conversation-linux-x64"
    else:
        binary_name = "pigeon_conversation-linux-x64"
    
    binary_path = tools_dir / binary_name
    
    if not binary_path.exists():
        fallback_names = [
            "pigeon_conversation-linux-x64",
            "pigeon_conversation-linux-arm",
            "pigeon_conversation-mac-arm",
            "pigeon_conversation-mac-x64"
        ]
        for name in fallback_names:
            fallback_path = tools_dir / name
            if fallback_path.exists():
                binary_path = fallback_path
                break
    
    return binary_path


def to_timestamp_ms(dt_str: str) -> int:
    """将时间字符串转换为毫秒时间戳"""
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    if ZoneInfo is not None:
        dt = dt.replace(tzinfo=ZoneInfo(DEF_TZ))
    else:
        dt = dt.replace(tzinfo=timezone.utc).astimezone()
    return int(dt.timestamp() * 1000)


def format_chinese_range(start_str: str, end_str: str) -> str:
    """格式化时间范围为中文格式"""
    sdt = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
    edt = datetime.strptime(end_str, "%Y-%m-%d %H:%M")
    s_label = f"{sdt.month}月{sdt.day}日{sdt.hour}点"
    e_label = f"{edt.month}月{edt.day}日{edt.hour}点"
    return f"{s_label}-{e_label}"


def call_data_download(shop_id: str, start_ms: int, end_ms: int) -> str:
    """调用数据下载脚本获取tos_key"""
    script_path = Path(__file__).parent.parent / "tools" / "dataDownload.py"
    cmd = [
        sys.executable,
        str(script_path),
        "--shop_id", shop_id,
        "--start_time", str(start_ms),
        "--end_time", str(end_ms),
    ]
    
    try:
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"数据下载失败: {e.output}")
    
    tos_key = output.splitlines()[0].strip()
    if not tos_key:
        raise RuntimeError("未获取到有效的tos_key")
    
    return tos_key


def run_pigeon_download(tos_key: str, output_dir: Path) -> Path:
    """执行pigeon可执行文件下载数据"""
    pigeon_path = get_pigeon_binary()
    
    if not pigeon_path.exists():
        raise RuntimeError(f"可执行文件不存在: {pigeon_path}")
    
    if not os.access(pigeon_path, os.X_OK):
        try:
            pigeon_path.chmod(0o755)
        except Exception as e:
            raise RuntimeError(f"设置可执行权限失败: {e}")
    
    before_files = set(output_dir.glob("*"))
    
    cmd = [str(pigeon_path), tos_key]
    
    print(f"[DEBUG] 执行pigeon: {cmd}")
    print(f"[DEBUG] 工作目录: {output_dir}")
    print(f"[DEBUG] tos_key: {tos_key}")
    
    try:
        result = subprocess.run(
            cmd, 
            cwd=str(output_dir), 
            capture_output=True, 
            text=True,
            timeout=300
        )
        
        print(f"[DEBUG] pigeon退出码: {result.returncode}")
        print(f"[DEBUG] pigeon stdout: {result.stdout}")
        print(f"[DEBUG] pigeon stderr: {result.stderr}")
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "未知错误"
            raise RuntimeError(f"pigeon执行失败 (exit code {result.returncode}): {error_msg}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("pigeon执行超时（超过300秒）")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"执行pigeon下载失败: {e}")
    
    after_files = set(output_dir.glob("*"))
    new_files = after_files - before_files
    
    print(f"[DEBUG] 执行前文件数: {len(before_files)}")
    print(f"[DEBUG] 执行后文件数: {len(after_files)}")
    print(f"[DEBUG] 新增文件: {[f.name for f in new_files]}")
    
    if not new_files:
        all_files = list(output_dir.glob("*"))
        print(f"[DEBUG] 目录中所有文件: {[f.name for f in all_files]}")
        raise RuntimeError("未找到新生成的文件，请检查pigeon可执行文件是否正常工作")
    
    latest_file = max(new_files, key=lambda p: p.stat().st_mtime)
    return latest_file


@app.get("/", response_class=HTMLResponse)
async def root():
    """返回主页HTML"""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>数据导出工具</h1><p>请访问 /docs 查看API文档</p>")


@app.post("/api/export")
async def export_data(request: ExportRequest):
    """
    解析自然语言命令并导出数据
    
    示例请求：
    {
        "text": "请帮我导出修丽可官方旗舰店店铺ID为8226405从2026年2月9日10点到2026年2月9日17点的数据"
    }
    """
    try:
        parsed = parse_export_command(request.text)
        if not parsed:
            raise HTTPException(
                status_code=400,
                detail="无法解析命令格式。请使用格式：请帮我导出[店铺名称]店铺ID为[数字]从[年份]年[月份]月[日期]日[小时]点到[年份]年[月份]月[日期]日[小时]点的数据"
            )
        
        is_valid, message = validate_time_range(parsed["start_time"], parsed["end_time"])
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        start_ms = to_timestamp_ms(parsed["start_time"])
        end_ms = to_timestamp_ms(parsed["end_time"])
        
        try:
            tos_key = call_data_download(parsed["shop_id"], start_ms, end_ms)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取数据下载密钥失败: {str(e)}")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                downloaded_file = run_pigeon_download(tos_key, temp_path)
                
                time_range_label = format_chinese_range(parsed["start_time"], parsed["end_time"])
                final_filename = f"{parsed['shop_name']}{time_range_label}标注数据.xlsx"
                
                file_id = str(uuid.uuid4())
                temp_file_path = TEMP_EXPORT_DIR / f"{file_id}.xlsx"
                
                shutil.copy2(downloaded_file, temp_file_path)
                
                file_cache[file_id] = {
                    "path": temp_file_path,
                    "filename": final_filename,
                    "created_at": datetime.now()
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")
        
        return {
            "success": True,
            "message": "数据导出成功",
            "data": {
                "shop_name": parsed["shop_name"],
                "shop_id": parsed["shop_id"],
                "start_time": parsed["start_time"],
                "end_time": parsed["end_time"],
                "filename": final_filename,
                "download_url": f"/api/download/{file_id}"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@app.get("/api/download/{file_id}")
async def download_file(file_id: str):
    """下载导出的数据文件，下载后自动删除"""
    if file_id not in file_cache:
        raise HTTPException(status_code=404, detail="文件不存在或已过期")
    
    file_info = file_cache[file_id]
    file_path = file_info["path"]
    filename = file_info["filename"]
    
    if not file_path.exists():
        del file_cache[file_id]
        raise HTTPException(status_code=404, detail="文件已被删除")
    
    def iterfile():
        try:
            with open(file_path, "rb") as f:
                yield from f
        finally:
            try:
                if file_path.exists():
                    file_path.unlink()
                if file_id in file_cache:
                    del file_cache[file_id]
            except Exception:
                pass
    
    return StreamingResponse(
        iterfile(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/files")
async def list_files():
    """列出所有已导出的文件"""
    files = []
    for file_id, file_info in file_cache.items():
        file_path = file_info["path"]
        if file_path.exists():
            stat = file_path.stat()
            files.append({
                "filename": file_info["filename"],
                "size": stat.st_size,
                "created_at": file_info["created_at"].isoformat(),
                "download_url": f"/api/download/{file_id}"
            })
    
    return {"files": sorted(files, key=lambda x: x["created_at"], reverse=True)}


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "platform": platform.system(),
        "machine": platform.machine(),
        "pigeon_binary": str(get_pigeon_binary())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
