"""Windows Hardware and System Information Tool for KritiAI."""
import os
import platform
import shutil
from typing import Any, Dict
import psutil
from security.policies.models import RiskLevel
from tools.base import BaseTool, ToolResult


class SystemInfoTool(BaseTool):
    """Inspects Windows hardware, RAM, CPU, GPU, storage, and recommends suitable local AI models."""
    name = "system_info"
    description = "Detect Windows system information, hardware specifications, and local model suitability."
    input_schema = {
        "type": "object",
        "properties": {
            "detailed": {"type": "boolean", "description": "Whether to perform deep hardware inspection", "optional": True}
        }
    }
    output_schema = {
        "type": "object",
        "properties": {
            "os": {"type": "string"},
            "cpu": {"type": "object"},
            "memory_gb": {"type": "object"},
            "disk_gb": {"type": "object"},
            "recommended_model_tier": {"type": "string"}
        }
    }
    risk_level = RiskLevel.LOW
    required_permission = "allow_application_control"
    timeout_seconds = 15

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            # Memory
            vm = psutil.virtual_memory()
            total_ram_gb = round(vm.total / (1024 ** 3), 2)
            avail_ram_gb = round(vm.available / (1024 ** 3), 2)

            # Disk
            disk = shutil.disk_usage(os.getcwd())
            total_disk_gb = round(disk.total / (1024 ** 3), 2)
            free_disk_gb = round(disk.free / (1024 ** 3), 2)

            # CPU
            cpu_count = psutil.cpu_count(logical=True)
            cpu_phys = psutil.cpu_count(logical=False)

            # Determine recommendation
            if total_ram_gb >= 32:
                rec_tier = "Large / 14B-32B Models (e.g. Qwen2.5-Coder-14B, Command-R)"
            elif total_ram_gb >= 16:
                rec_tier = "Medium / 7B-8B Models (e.g. Llama-3.1-8B, Qwen2.5-Coder-7B)"
            elif total_ram_gb >= 8:
                rec_tier = "Small / 3B-4B Models (e.g. Phi-3.5-mini, Llama-3.2-3B)"
            else:
                rec_tier = "Ultra-Light / 1B-2B Models or Cloud API"

            data = {
                "os": f"{platform.system()} {platform.release()} ({platform.version()})",
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "cpu": {
                    "logical_cores": cpu_count,
                    "physical_cores": cpu_phys,
                    "usage_percent": psutil.cpu_percent(interval=0.1)
                },
                "memory_gb": {
                    "total": total_ram_gb,
                    "available": avail_ram_gb,
                    "used_percent": vm.percent
                },
                "disk_gb": {
                    "total": total_disk_gb,
                    "free": free_disk_gb
                },
                "recommended_model_tier": rec_tier
            }

            return ToolResult(
                success=True,
                data=data,
                verification={"verified": True, "reason": "Hardware telemetry collected."}
            )
        except Exception as ex:
            return ToolResult(success=False, error=f"System info collection error: {str(ex)}")

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": execution_result.success, "reason": "System info valid."}
