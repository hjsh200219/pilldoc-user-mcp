"""메트릭 수집 유틸리티"""
import time
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
from functools import wraps
import json
import logging

logger = logging.getLogger(__name__)


class Metrics:
    """메트릭 수집 및 관리 클래스"""

    def __init__(self):
        self.tool_metrics = defaultdict(lambda: {
            "call_count": 0,
            "success_count": 0,
            "error_count": 0,
            "total_duration": 0,
            "min_duration": float('inf'),
            "max_duration": 0,
            "errors": []
        })
        self.start_time = datetime.now()

    def record_tool_call(self, tool_name: str, duration: float, success: bool, error: Optional[str] = None):
        """도구 호출 메트릭 기록"""
        metrics = self.tool_metrics[tool_name]
        metrics["call_count"] += 1
        metrics["total_duration"] += duration

        if success:
            metrics["success_count"] += 1
        else:
            metrics["error_count"] += 1
            if error:
                metrics["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error
                })
                # 최근 10개 에러만 유지
                metrics["errors"] = metrics["errors"][-10:]

        # 최소/최대 지연시간 업데이트
        metrics["min_duration"] = min(metrics["min_duration"], duration)
        metrics["max_duration"] = max(metrics["max_duration"], duration)

    def get_metrics(self) -> Dict[str, Any]:
        """전체 메트릭 조회"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        # 도구별 통계 계산
        tool_stats = {}
        for tool_name, metrics in self.tool_metrics.items():
            avg_duration = (
                metrics["total_duration"] / metrics["call_count"]
                if metrics["call_count"] > 0
                else 0
            )

            success_rate = (
                metrics["success_count"] / metrics["call_count"] * 100
                if metrics["call_count"] > 0
                else 0
            )

            tool_stats[tool_name] = {
                "call_count": metrics["call_count"],
                "success_rate": f"{success_rate:.1f}%",
                "avg_duration": f"{avg_duration:.3f}s",
                "min_duration": f"{metrics['min_duration']:.3f}s" if metrics['min_duration'] != float('inf') else "N/A",
                "max_duration": f"{metrics['max_duration']:.3f}s",
                "error_count": metrics["error_count"],
                "recent_errors": metrics["errors"][-5:]  # 최근 5개 에러
            }

        # 전체 통계
        total_calls = sum(m["call_count"] for m in self.tool_metrics.values())
        total_success = sum(m["success_count"] for m in self.tool_metrics.values())
        total_errors = sum(m["error_count"] for m in self.tool_metrics.values())

        overall_success_rate = (
            total_success / total_calls * 100
            if total_calls > 0
            else 0
        )

        return {
            "uptime_seconds": uptime,
            "uptime_formatted": self._format_duration(uptime),
            "start_time": self.start_time.isoformat(),
            "overall": {
                "total_calls": total_calls,
                "total_success": total_success,
                "total_errors": total_errors,
                "success_rate": f"{overall_success_rate:.1f}%"
            },
            "tools": tool_stats
        }

    def reset(self):
        """메트릭 초기화"""
        self.tool_metrics.clear()
        self.start_time = datetime.now()
        logger.info("Metrics have been reset")

    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """메트릭 내보내기"""
        metrics = self.get_metrics()
        metrics_json = json.dumps(metrics, indent=2, ensure_ascii=False)

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(metrics_json)
            logger.info(f"Metrics exported to {filepath}")

        return metrics_json

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """시간 포맷팅"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


# 전역 메트릭 인스턴스
_metrics = Metrics()


def track_execution(tool_name: str):
    """도구 실행 추적 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error_msg = None

            try:
                result = func(*args, **kwargs)
                success = True
                return result

            except Exception as e:
                error_msg = str(e)
                raise

            finally:
                duration = time.time() - start_time
                _metrics.record_tool_call(tool_name, duration, success, error_msg)

        return wrapper
    return decorator


def get_global_metrics() -> Dict[str, Any]:
    """전역 메트릭 조회"""
    return _metrics.get_metrics()


def reset_global_metrics():
    """전역 메트릭 초기화"""
    _metrics.reset()