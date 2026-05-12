tags: week:3, numpy, vectorization

# 第 3 周 · NumPy 向量化基础

> 教学目标：把基于 Python `for` 循环的初级实现重构为 ndarray 整体运算。

## 1. 三条核心法则

1. **广播（Broadcasting）**：形状不同的数组只要末轴尺寸兼容，就可以在不显式扩展的情况下逐元素运算。
2. **ufunc**：`np.add`、`np.exp` 等通用函数在 C 层迭代，比 Python 解释器快 1-2 个数量级。
3. **轴归约**：`arr.sum(axis=...)`、`np.einsum`、`np.add.reduceat` 能消除一次 Python 层循环。

## 2. 常见反例

```python
# 学生写法：O(n) Python 迭代
def sum_squares(arr):
    s = 0
    for x in arr:
        s += x * x
    return s
```

应改写为：

```python
def sum_squares(arr):
    arr = np.asarray(arr, dtype=np.float64)
    return float(np.sum(arr ** 2))
```

## 3. 数值稳定提示

* 计算 `log(sum(exp(x)))` 时使用 `scipy.special.logsumexp`。
* 求解线性最小二乘时优先用 `np.linalg.lstsq`，而非显式构造正规方程。
