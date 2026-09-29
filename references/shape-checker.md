# 可选形状检查工具

`scripts/check_shapes.py` 使用 Python 3.10+ 标准库，不执行模型，不联网，不修改输入文件。

```bash
python scripts/check_shapes.py assets/shape-example.json --strict
```

## 格式

```json
{
  "schema_version": 1,
  "tensors": {
    "A": ["B", 12, 32],
    "W": [32, 64],
    "Y": ["B", 12, 64]
  },
  "operations": [
    {"id": "project", "op": "matmul", "inputs": ["A", "W"], "output": "Y"}
  ]
}
```

`tensors` 的值是形状列表。正整数表示已知维度，字符串表示符号，空列表 `[]` 表示标量。符号应统一命名；工具不会求解代数式。

| op | 要求 |
|---|---|
| `add`, `hadamard` | 两个输入；需要广播时显式 `"broadcast": true` |
| `matmul` | 两个输入、各至少二维；支持前导批次轴广播 |
| `scale` | 第一个输入是张量，第二个是 `[]` 标量 |
| `concat` | 至少两个输入；必须提供整数 `axis` |
| `reduce` | 一个输入；提供 `axis`（整数或列表）、可选 `keepdims` |
| `transpose` | 一个输入；`axes` 为完整非负轴排列 |
| `reshape` | 一个输入；根据声明输出检查元素数 |

`reduce` 只检查形状变化，不判断 Sum/Mean/Std 的具体统计意义。

## 结果解释

- **ERROR**：已知维度、轴、rank、ID 或格式存在矛盾，退出码 1。
- **REVIEW**：符号等价、广播或算子无法确定；默认仍返回 0，`--strict` 返回 2。
- 0 错误、0 待确认：仅表示这些声明在支持范围内相容，不证明模型、数值、图例或实际渲染正确。

例如 `[B,32]` 与 `[N,32]` 的 `B=N` 未建立时标 REVIEW；不能擅自假设两个符号相等。`[B,4,32] → [B,128]` 可检查乘积相同；包含 `F+4` 的复杂等价式可能需要人工确认。

工具不检查全图输出路线、循环、共享权重、任务标签、语义命名和图形遮挡。继续使用方法契约和实际渲染检查。`assets/shape-example.json` 只是合成的符号示例，不代表任何用户模型。
