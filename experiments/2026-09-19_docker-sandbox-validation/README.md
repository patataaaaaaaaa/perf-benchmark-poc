# Docker 基础沙箱验证

## 实验问题

框架执行 workload、测试、benchmark 和候选代码时，能否落实第一版安全边界？

## 验证项目

| 检查项 | 结果 |
|---|:---:|
| 容器内使用非 root 用户 | 通过 |
| DeepSeek API 密钥不可见 | 通过 |
| 仓库以只读方式挂载 | 通过 |
| 无默认网络路由且外连失败 | 通过 |
| 超时进程被终止 | 通过 |
| 超过内存限制的进程失败 | 通过 |

超时样例以退出码 `124` 结束；超内存样例以退出码 `137` 结束，符合本次负向验证预期。

## 相关实现

- `docker/sandbox.Dockerfile`
- `src/framework/sandbox.py`
- `scripts/validate_sandbox.py`
- `subjects/sandbox_checks/`
- `tests/test_sandbox.py`
- `results/summary.json`：脱敏后的机器可读负向验证结果。

## 结论与边界

基础沙箱已经满足科研原型的最小隔离要求，可以用于当前受控实验。但 Docker 共享宿主机
内核，它不是面向恶意攻击者的强隔离系统，不能据此宣称达到生产级不可信代码执行安全。

完整原始日志保存在本机忽略提交的
`artifacts/sandbox_validation/20260919_145020_727781/`。
