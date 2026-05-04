"""熔断器：防止 API 雪崩导致所有小说同时进入 ERROR"""
import time
import logging
from enum import Enum
from threading import Lock

logger = logging.getLogger(__name__)


class BreakerState(Enum):
    """定义 `BreakerState`，作为应用层中的业务对象。

    职责: 承载本模块的状态、规则或协作入口。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """定义 `CircuitBreaker`，作为应用层中的业务对象。

    职责: 承载本模块的状态、规则或协作入口。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    def __init__(
        self,
        failure_threshold: int = 5,    # 连续失败 5 次后断开
        reset_timeout: int = 120,       # 断开后 120 秒尝试恢复
        half_open_max_calls: int = 1,  # 试探阶段最多放行 1 次
    ):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - failure_threshold: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        - reset_timeout: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        - half_open_max_calls: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = BreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._lock = Lock()

    def is_open(self) -> bool:
        """同步判断 `open` 条件是否成立。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `is_open` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 布尔值，表示判断、校验或执行条件是否成立。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        with self._lock:
            if self._state == BreakerState.OPEN:
                if time.time() - self._last_failure_time > self.reset_timeout:
                    logger.info("[CircuitBreaker] → HALF_OPEN，开始试探")
                    self._state = BreakerState.HALF_OPEN
                    self._success_count = 0
                    return False  # 放行试探
                return True  # 仍在断开期
            return False

    def wait_seconds(self) -> float:
        """还需等待多少秒"""
        elapsed = time.time() - self._last_failure_time
        return max(0.0, self.reset_timeout - elapsed)

    def record_success(self):
        """同步执行 `record_success` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `record_success` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        with self._lock:
            if self._state == BreakerState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    logger.info("[CircuitBreaker] → CLOSED，恢复正常")
                    self._state = BreakerState.CLOSED
                    self._failure_count = 0
            elif self._state == BreakerState.CLOSED:
                self._failure_count = 0  # 成功重置计数

    def record_failure(self):
        """同步执行 `record_failure` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `record_failure` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state == BreakerState.HALF_OPEN:
                logger.warning("[CircuitBreaker] 试探失败 → OPEN")
                self._state = BreakerState.OPEN
            elif self._failure_count >= self.failure_threshold:
                logger.warning(
                    f"[CircuitBreaker] 连续失败 {self._failure_count} 次 → OPEN，"
                    f"暂停 {self.reset_timeout}s"
                )
                self._state = BreakerState.OPEN

    @property
    def state(self) -> str:
        """读取或计算 `state` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `state` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return self._state.value
