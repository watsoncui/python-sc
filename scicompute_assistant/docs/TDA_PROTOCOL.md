# TDA 集成方案：后端 → 前端的数据协议

> 任务 3：让后端 giotto-tda 持久图对象高效地在前端 Plotly 窗口中渲染。

## 1. 设计目标

| 目标 | 实现策略 |
|---|---|
| Plotly **零后处理** | 数组扁平为 `list[list[float]]`，与 Plotly `scatter.x/y` 直接对齐 |
| 维度可区分 | 每个点显式带 `dimension` 字段，前端映射到颜色/形状 |
| 与 giotto-tda 解耦 | 全部转换集中在 `common/compute/tda.py`，替换为 ripser/persim 不影响 API |
| 单次请求即够画 | 同时返回 *持久图*、*Betti 曲线*、*点云预览* 与 *坐标轴范围* |
| 大点云不爆 payload | `downsample_preview` 参数限制点云预览大小 |

## 2. 协议（Pydantic 定义见 `common/protocols/tda_payload.py`）

### 2.1 请求

```jsonc
POST /tda/pipeline
{
  "data": [[x1, y1], [x2, y2], ...] | null,
  "code": "X = make_circles(...)" | null,   // 二选一，code 走 sandbox
  "pipeline": "vietoris_rips",              // vietoris_rips | alpha | cubical | mapper
  "max_dimension": 2,
  "max_edge_length": 1.0,
  "n_bins": 100,
  "downsample_preview": 500
}
```

### 2.2 响应

```jsonc
{
  "diagram": {
    "points": [
      {"birth": 0.0, "death": 0.42, "dimension": 0, "persistence": 0.42},
      {"birth": 0.18, "death": 1.05, "dimension": 1, "persistence": 0.87}
    ],
    "max_filtration": 1.05,
    "axis_limits": [0.0, 1.05],
    "betti_curves": [
      {"dimension": 0, "filtration": [0, 0.02, ...], "values": [60, 59, ...]},
      {"dimension": 1, "filtration": [0, 0.02, ...], "values": [0, 0, ...]}
    ],
    "point_cloud_preview": [[x, y], ...] | null,
    "scale": "linear"
  },
  "elapsed_ms": 87.3,
  "backend": "giotto-tda",
  "warnings": []
}
```

### 2.3 关键字段语义

* `points[i].persistence` 是后端预算好的 `death - birth`，前端用于过滤短噪声特征
  （e.g. slider 拖动）无需重新计算。
* `axis_limits` 已统一了 H0/H1/H2 的最大 filtration，前端可一次性设置 Plotly
  `xaxis.range`/`yaxis.range`，避免动画过程中跳变。
* `betti_curves` 与 `points` 共享 filtration 上限，便于联动高亮。
* `point_cloud_preview` 用等距下采样（`np.linspace`）保证形状感不变。

## 3. 后端转换流程

```mermaid
flowchart LR
    A[TDARequest.data\nList[List[float]]] --> B[np.asarray(dtype=float64)]
    B --> C{giotto-tda 可用?}
    C -- yes --> D[VietorisRipsPersistence /\nWeakAlphaPersistence.fit_transform]
    C -- no --> E[NumPy fallback:\nMST 边长 → H0]
    D --> F[diagrams ndarray]
    E --> F
    F --> G[_to_payload\n构造 PersistenceDiagramPayload]
    G --> H[axis_limits = (0, max(death))]
    G --> I[betti_curves: 在 grid 上区间计数]
    G --> J[point_cloud_preview = 等距下采样]
    H & I & J --> K[TDAResponse(JSON)]
```

## 4. 前端 Plotly 渲染范例（最小可运行片段）

```javascript
// 假设 resp = await fetch('/tda/pipeline', ...).then(r => r.json())
const dims = [...new Set(resp.diagram.points.map(p => p.dimension))].sort();
const palette = {0: '#1f77b4', 1: '#d62728', 2: '#2ca02c'};

const traces = dims.map(d => {
  const pts = resp.diagram.points.filter(p => p.dimension === d);
  return {
    x: pts.map(p => p.birth),
    y: pts.map(p => p.death),
    mode: 'markers',
    name: `H${d}`,
    type: 'scattergl',
    marker: { color: palette[d] ?? '#999', size: 8, opacity: 0.85 },
    hovertemplate: 'birth=%{x:.3f}<br>death=%{y:.3f}<br>persistence=%{customdata:.3f}',
    customdata: pts.map(p => p.persistence),
  };
});

const [lo, hi] = resp.diagram.axis_limits;
traces.push({                     // 对角线（参考）
  x: [lo, hi], y: [lo, hi],
  mode: 'lines', line: { dash: 'dot', color: '#aaa' },
  showlegend: false,
});

Plotly.newPlot('diagram', traces, {
  xaxis: { title: 'Birth', range: [lo, hi] },
  yaxis: { title: 'Death', range: [lo, hi], scaleanchor: 'x' },
  margin: { t: 24, r: 12, l: 48, b: 48 },
});
```

注意：使用 `scattergl` 让数千个特征点保持流畅。

## 5. 大数据 / 流式扩展（可选）

| 情景 | 协议增强 | 实施 |
|---|---|---|
| `len(data) > 5e4` | 增加 `subsample: int` 字段，由后端先做 SciPy KDTree 子采样再做持久同调 | giotto-tda 中调用 `Subsampler` |
| 多张图（Mapper） | `pipeline = "mapper"` 时，返回额外的 `mapper_graph: { nodes, edges }` 字段 | 节点 `{id, members[], centroid[]}` |
| WebSocket 流 | 上游慢，启用 `/tda/stream` —— 服务器按 (H0, H1, H2) 顺序逐步 push `PersistenceDiagramPayload`（增量合并） | Server-Sent Events，相同协议碎片 |

## 6. 失败语义

* giotto-tda 未安装：`backend = "numpy-fallback"`，`warnings` 含说明，UI 给出黄色横幅。
* `data` 为空或 ndim 不是 2：`HTTP 400`，`detail` 说明形状要求。
* 用户传 `code` 而非 `data`：路由层拒绝（必须先经 `/compute/run` 拿到结果再回传），
  防止 TDA 路由间接成为通用代码执行入口。
