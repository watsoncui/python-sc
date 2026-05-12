/**
 * 18-Week Python Scientific Computing course data.
 * Mirrors meta_course/schedule-18weeks.md + literature.md + notebook-design.md.
 */

export type LessonLevel = 'B' | 'H' | 'C'

export interface Lesson {
  id: string
  title: string
  level: LessonLevel
  hasAI: boolean
  /** 45-min session breakdown (from schedule-18weeks.md "每节 45 分钟建议") */
  sessionGuide?: string
  /** AI session prompt template (for lessons with hasAI:true) */
  aiPromptTemplate?: string
  /** In-class exercise description */
  exercise?: string
}

export interface Literature {
  shortName: string
  title: string
  url: string
  year: string
  courseLink: string  // 与本课的关联说明
}

export interface WeekData {
  week: number
  title: string
  module: string
  lessons: [Lesson, Lesson, Lesson]
  contextTags: string[]
  demoCode: string
  literature: Literature[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Literature database (from meta_course/literature.md)
// ─────────────────────────────────────────────────────────────────────────────
const LIT = {
  SCIPY_SPATIAL: {
    shortName: 'SciPy spatial.transform',
    title: 'SciPy spatial.transform 可微扩展（JAX/PyTorch/CuPy）',
    url: 'https://arxiv.org/abs/2511.18157',
    year: '2025',
    courseLink: '体现「科学计算栈」现代演进，适合介绍可复现环境与工具链',
  },
  RAMANSPY: {
    shortName: 'RamanSPy',
    title: 'RamanSPy: 拉曼光谱分析 Python 库',
    url: 'https://openreview.net/forum?id=RamanSPy',
    year: '2024',
    courseLink: '基于 NumPy/SciPy 标准化流程并衔接 ML，「从数据到可复现分析」案例',
  },
  ZERNIPAX: {
    shortName: 'ZERNIPAX',
    title: 'ZERNIPAX: Zernike 多项式计算（NumPy/JAX）',
    url: 'https://www.sciencedirect.com/science/article/pii/S0096300325002607',
    year: '2025',
    courseLink: '光学 Zernike 多项式，涉及多项式与线性代数运算（NumPy/JAX）',
  },
  PYDMD: {
    shortName: 'PyDMD',
    title: 'PyDMD: 动态模态分解（特征值/SVD）',
    url: 'https://arxiv.org/abs/2402.07463',
    year: '2024',
    courseLink: '用 NumPy/SciPy 做特征值/SVD、提取时空模态，应用于流体、神经、等离子体',
  },
  SPARTA: {
    shortName: 'SPARTA',
    title: 'SPARTA: CERN 共振分析工具（NumPy/SciPy/信号）',
    url: 'https://cds.cern.ch/',
    year: '2024',
    courseLink: '用 NumPy/SciPy/scikit-rf 做共振分析，替代人工、强调可复现流程',
  },
  TRIPS_PY: {
    shortName: 'TRIPs-Py',
    title: 'TRIPs-Py: Python 反问题正则化工具包',
    url: 'https://arxiv.org/abs/2402.17603',
    year: '2024',
    courseLink: 'Tikhonov/TSVD/Krylov/ℓp-ℓq 正则化；含去模糊、CT 算例，与课程「岭回归/正则化」一致',
  },
  EV_PINN: {
    shortName: 'EV-PINN',
    title: 'EV-PINN: 电动汽车动力学物理信息神经网络',
    url: 'https://arxiv.org/abs/2411.14691',
    year: '2024',
    courseLink: '从数据学习电机效率与阻力参数，与「可微 + 优化 + PINN」对应',
  },
  JAX_ODE: {
    shortName: 'JAX ODE 校准',
    title: 'JAX 可微 ODE 参数估计（两阶段优化流程）',
    url: 'https://arxiv.org/abs/2509.07283',
    year: '2025',
    courseLink: '全局探索 + 梯度细化校准 ODE 参数，用于电池/燃烧/生物机理模型',
  },
  UQPy: {
    shortName: 'UQpy v4',
    title: 'UQpy v4.1/v4.2: 通用不确定性量化工具箱',
    url: 'https://uqpyproject.readthedocs.io',
    year: '2023',
    courseLink: '模块化 UQ 工作流，与 NumPy/SciPy 兼容，讲完 Monte Carlo 后介绍',
  },
  CHAOSPY: {
    shortName: 'Chaospy',
    title: 'Chaospy v4.3: 多项式混沌与高级抽样',
    url: 'https://chaospy.readthedocs.io',
    year: '2024',
    courseLink: 'PCE 与高级蒙特卡洛，与课程「Chaospy 初识」对应',
  },
  PINN_HEAT: {
    shortName: 'PINN 热-力学',
    title: 'PINN 激光金属沉积热传导与热应力仿真',
    url: 'https://arxiv.org/abs/2412.18786',
    year: '2024',
    courseLink: 'PDE 残差 + 数据驱动，可与「PDE 有限差分」对比',
  },
  HEAT_CAVITY: {
    shortName: '热腔 PINN',
    title: 'PINN 自然对流热腔流动（2D/3D 验证）',
    url: 'https://www.nature.com/articles/s41598-024-00000-0',
    year: '2024',
    courseLink: '2D/3D 正向模拟与已有数值解对比，体现「PDE + 数值验证」',
  },
  DEEPF_NET: {
    shortName: 'DeepF-fNet',
    title: 'DeepF-fNet: PINN + DeepONet 振动隔离优化',
    url: 'https://arxiv.org/abs/2412.21132',
    year: '2024',
    courseLink: '振动隔离优化，可与传统优化（遗传算法）对比，体现「科学 ML + 优化」',
  },
  HEAT_2D: {
    shortName: '2D 热方程',
    title: '二维热方程有限差分 Python 实现与稳定性分析',
    url: 'https://www.ijsr.net',
    year: '2024',
    courseLink: '有限差分、显式/隐式格式、NumPy/SciPy/Matplotlib，与课程「一维热方程→二维泊松」一致',
  },
  PYLOPS: {
    shortName: 'PyLops',
    title: 'PyLops: 线性算子与 TV 正则化',
    url: 'https://pylops.readthedocs.io',
    year: '2024',
    courseLink: '总变分等正则化、Split Bregman，可与 TRIPs-Py 互补介绍',
  },
} satisfies Record<string, Literature>

// ─────────────────────────────────────────────────────────────────────────────
// 18 Weeks
// ─────────────────────────────────────────────────────────────────────────────
const WEEKS: WeekData[] = [
  {
    week: 1,
    title: '环境与 Python 最小子集',
    module: '工具与基础',
    lessons: [
      {
        id: '1.1', title: '课程导论与工具链：uv/conda + Jupyter', level: 'B', hasAI: false,
        sessionGuide: '课程目标与规矩 8min → uv/conda 安装演示 10min → Jupyter 启动/快捷键 8min → 可复现环境（environment.yml 或 pyproject.toml）8min → Git 管理代码 5min → 学生跟做排错 6min',
        exercise: '下次课前能打开 Jupyter 并跑通一个 cell；能用 `uv sync` 或 `conda env create` 复现环境。',
      },
      {
        id: '1.2', title: 'Python 最小子集（一）：变量、列表与索引', level: 'B', hasAI: false,
        sessionGuide: '变量与类型（int/float/str）8min → 列表创建、len、索引与切片 12min → 列表与「将来数组」的对比 5min → 随堂练习：取前5/后3/每隔一个 15min → 常见错误（越界、类型混用）5min',
        exercise: '给定列表 [1.2, 2.3, 1.8, 3.1, 0.9]，写出取前 3 个、后 2 个、每隔一个的切片。',
      },
      {
        id: '1.3', title: 'Python 最小子集（二）：循环、函数与文件读写', level: 'B', hasAI: true,
        sessionGuide: 'for 循环与 range 8min → if/else 5min → def/return 10min → 读 CSV（open/readline/split）7min → AI 环节 10min → 小结与作业说明 5min',
        aiPromptTemplate: '任务：用 Python 读取 CSV 文件（列名 x, y），计算 y 列的均值，不使用 pandas。\n\n建议提示词：\n"用 Python 3，不使用 pandas，读取 CSV 文件（第一行是列头 x,y），计算 y 列的算术均值，打印结果，保留 4 位小数"\n\n验证步骤：\n1. 修改文件路径和列索引，确认能跑通\n2. 手算一个小样本验证输出是否正确\n3. 能否把求均值改为求方差？',
        exercise: '用 AI 生成「读 CSV 并求均值」的代码，然后：① 改为求标准差；② 逐行解释代码含义；③ 改路径和列索引。',
      },
    ],
    contextTags: ['week1', 'python-basics', 'environment', 'jupyter'],
    literature: [LIT.SCIPY_SPATIAL, LIT.RAMANSPY],
    demoCode: `# 第 1 周 · Python 最小子集
# 1.2 列表与切片

data = [1.2, 2.3, 1.8, 3.1, 0.9, 2.7, 1.5]

print("全部数据:", data)
print("前 3 个:", data[:3])
print("后 2 个:", data[-2:])
print("每隔一个:", data[::2])
print("最大值:", max(data))

# 1.3 函数与循环
def compute_stats(values: list[float]) -> dict:
    """计算均值和标准差（不使用 NumPy）。"""
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = variance ** 0.5
    return {"mean": mean, "std": std, "n": n}

stats = compute_stats(data)
for key, val in stats.items():
    print(f"  {key}: {val:.4f}")

# AI 辅助环节：让 AI 生成「读 CSV 并求均值」的代码
# 提示词：用 Python 3，不使用 pandas，读取 CSV（列头 x,y），
#         计算 y 列均值并打印，保留 4 位小数
`,
  },

  {
    week: 2,
    title: 'NumPy 与数组计算',
    module: 'NumPy',
    lessons: [
      {
        id: '2.1', title: 'ndarray 创建、形状与 dtype', level: 'B', hasAI: false,
        sessionGuide: '为何用 NumPy（与列表对比）5min → np.array/zeros/arange/linspace 12min → shape/ndim/dtype/reshape 10min → 标量/列表/矩阵对应关系 8min → 随堂练习 10min',
        exercise: '构造一个 shape 为 (3, 4) 的零矩阵；将 np.arange(12) reshape 成 (3,4) 和 (4,3)；演示 reshape(-1,1) 与 (1,-1) 的区别。',
      },
      {
        id: '2.2', title: '索引、切片与广播规则', level: 'B', hasAI: false,
        sessionGuide: '一维索引与切片 5min → 二维索引 [i,j]、行/列切片 12min → 布尔索引（掩码）10min → 广播规则 10min → 随堂练习 8min',
        exercise: '从 3×4 矩阵中取第2行、取前3列、取大于6的元素；用广播计算列向量加行向量。',
      },
      {
        id: '2.3', title: '线性代数运算与范数', level: 'B', hasAI: true,
        sessionGuide: '矩阵乘法 @ 与 * 的区别 8min → 转置/内积/矩阵-向量乘 7min → 范数：L1/L2/Frobenius 10min → AI 环节：查 norm 的 ord 参数 10min → 随堂练习 10min',
        aiPromptTemplate: '任务：查询 np.linalg.norm 的 ord 参数含义并验证。\n\n建议提示词：\n"np.linalg.norm 的 ord 参数有哪些取值？分别对应什么数学范数？请给出每种取值的一行 Python 示例"\n\n验证步骤：\n1. 对向量 [3, 4]，手算 L1=7，L2=5，inf=4\n2. 对矩阵，手算 Frobenius（各元素平方和开根号）\n3. 在文档里找到对应段落确认',
        exercise: '对矩阵 A=[[2,1],[1,3]] 和向量 v=[1,-1]：计算 A@v；计算 ‖v‖₁、‖v‖₂、‖A‖_F；用 AI 查 ord=\'nuc\'（核范数）并验证。',
      },
    ],
    contextTags: ['week2', 'numpy', 'broadcasting', 'linear-algebra', 'norms'],
    literature: [LIT.ZERNIPAX, LIT.PYDMD, LIT.SPARTA],
    demoCode: `# 第 2 周 · NumPy 与数组计算
import numpy as np

# 2.1 ndarray 创建
x = np.array([1.0, 2.0, 3.0, 4.0])
A = np.arange(12).reshape(3, 4)
B = np.linspace(0, 1, 5)
print("向量 x:", x, "shape:", x.shape)
print("矩阵 A:\\n", A)

# 2.2 索引与广播
print("\\n第 1 行:", A[0])
print("第 2 列:", A[:, 1])
print("大于 6 的元素:", A[A > 6])

col = np.array([[1], [2], [3]])   # shape (3,1)
row = np.array([10, 20, 30, 40])  # shape (4,)
print("\\n广播结果:\\n", col + row)

# 2.3 矩阵运算与范数
M = np.array([[2., 1.], [1., 3.]])
v = np.array([1., -1.])
print("\\nM @ v =", M @ v)
print("‖v‖₂ =", np.linalg.norm(v))
print("‖v‖₁ =", np.linalg.norm(v, ord=1))
print("‖M‖_F =", np.linalg.norm(M, ord='fro'))
# AI 辅助：查 ord='nuc'（核范数）并验证
print("‖M‖_nuc =", np.linalg.norm(M, ord='nuc'))
`,
  },

  {
    week: 3,
    title: 'NumPy 进阶与误差基础',
    module: '误差与线性代数',
    lessons: [
      {
        id: '3.1', title: '矩阵分解：LU、QR、SVD 初识', level: 'B', hasAI: false,
        sessionGuide: '为何需要分解 5min → LU：lu/L/U/两步求解 10min → QR：正交性/最小二乘预告 8min → SVD 初识：奇异值/主方向直观 10min → 随堂：对同一矩阵做 lu/qr/svd 12min',
        exercise: '对矩阵 A=[[4,3],[6,3]]：做 LU 分解并验证 P@L@U==A；做 SVD 并打印奇异值；解释 QR 与最小二乘的关系。',
      },
      {
        id: '3.2', title: '误差、稳定性与条件数', level: 'B', hasAI: false,
        sessionGuide: '浮点与机器精度 8min → 相对误差与有效数字 5min → 条件数 cond(A) 7min → 病态方程组：小扰动→大误差 10min → 随堂：病态矩阵实验 15min',
        exercise: '构造 Hilbert 矩阵 H（3×3），打印 cond(H)；用 solve 解 Hx=b，改 b 的第一个元素 ±1e-6，观察解的变化幅度。',
      },
      {
        id: '3.3', title: '线性方程组（一）：直接法', level: 'B', hasAI: false,
        sessionGuide: 'Ax=b 唯一解条件 3min → 高斯消元手算 2×2 7min → LU 分解即两步求解 8min → scipy.linalg.solve 用法 10min → 随堂：3×3 自编题 17min',
        exercise: '用 scipy.linalg.solve 解 3×3 方程组，代入验证 A@x≈b；尝试奇异矩阵看报错含义。',
      },
    ],
    contextTags: ['week3', 'numpy', 'matrix-decomposition', 'numerical-stability', 'condition-number'],
    literature: [LIT.ZERNIPAX, LIT.PYDMD],
    demoCode: `# 第 3 周 · 矩阵分解与误差基础
import numpy as np
from scipy import linalg

A = np.array([[4., 3.], [6., 3.]])

# 3.1 LU 分解
P, L, U = linalg.lu(A)
print("A =\\n", A)
print("P @ L @ U == A?", np.allclose(P @ L @ U, A))
Q, R = linalg.qr(A)
print("‖Q^T Q - I‖ =", np.linalg.norm(Q.T @ Q - np.eye(2)))
U_, s, Vt = linalg.svd(A)
print("奇异值:", s)

# 3.2 条件数与病态
H = np.array([[1, 1/2, 1/3], [1/2, 1/3, 1/4], [1/3, 1/4, 1/5]])
print("\\ncond(Hilbert 3×3) =", np.linalg.cond(H))

b = np.array([1., 0., 0.])
x = linalg.solve(H, b)
print("残差 ‖Hx-b‖ =", np.linalg.norm(H @ x - b))

# 3.3 直接法
A2 = np.array([[2., 1., -1.], [-3., -1., 2.], [-2., 1., 2.]])
b2 = np.array([8., -11., -3.])
x2 = linalg.solve(A2, b2)
print("\\n解:", x2, "  验证:", np.allclose(A2 @ x2, b2))
`,
  },

  {
    week: 4,
    title: '线性代数数值解',
    module: '线性代数',
    lessons: [
      {
        id: '4.1', title: '迭代法：Jacobi / Gauss-Seidel 格式与收敛性', level: 'B', hasAI: false,
        sessionGuide: '直接法大规模成本/迭代动机 5min → Jacobi 格式 10min → G-S 与 Jacobi 对比 5min → 收敛性（对角占优/谱半径）5min → 实现 Jacobi/画残差 15min → scipy.sparse 简单示例 5min',
        exercise: '对对角占优 3×3 矩阵运行 Jacobi 迭代至残差 <1e-8；对一个不收敛的矩阵验证发散；画残差随迭代次数的下降曲线。',
      },
      {
        id: '4.2', title: '特征值与特征向量：幂法、eig', level: 'B', hasAI: false,
        sessionGuide: '特征值定义与几何直观 5min → 2×2 手算一例 10min → 幂法思想 7min → scipy.linalg.eig/eigvals 8min → 应用预告（主成分/稳定性）5min → 随堂验证 Av=λv 10min',
        exercise: '对 [[2,1],[1,3]] 求特征值并验证 Av=λv；演示复数特征值的实矩阵；用 `A^k @ v` 观察幂法收敛方向。',
      },
      {
        id: '4.3', title: '最小二乘与正规方程', level: 'B', hasAI: true,
        sessionGuide: '超定方程组「无解」与最小二乘意义 8min → 法方程推导与解 7min → scipy.linalg.lstsq 调用 8min → 直线拟合 10min → AI 环节 7min → 随堂换数据 5min',
        aiPromptTemplate: '任务：让 AI 写「用 lstsq 拟合直线」并检验。\n\n建议提示词：\n"用 scipy.linalg.lstsq 对给定的 x=[0,1,2,3,4], y=[1.1,1.9,3.0,3.8,5.2] 做最小二乘直线拟合，返回斜率和截距，并画出数据点和拟合直线（matplotlib），标注残差"\n\n验证步骤：\n1. 手算正规方程 (A\'A)x = A\'b 验证参数\n2. 将 y 改为二次多项式数据，修改代码做二次拟合\n3. 检查 AI 是否理解残差的含义',
        exercise: '对 5 组数据用 lstsq 拟合 y=ax+b；画数据点+拟合线+残差棒图；改为二次多项式拟合并对比残差。',
      },
    ],
    contextTags: ['week4', 'iterative-methods', 'eigenvalues', 'least-squares'],
    literature: [LIT.PYDMD, LIT.TRIPS_PY],
    demoCode: `# 第 4 周 · 线性代数数值解
import numpy as np
from scipy import linalg

# 4.1 Jacobi 迭代法
def jacobi(A, b, max_iter=200, tol=1e-10):
    D = np.diag(np.diag(A))
    R = A - D
    x = np.zeros_like(b, dtype=float)
    residuals = []
    for _ in range(max_iter):
        x_new = (b - R @ x) / np.diag(A)
        res = np.linalg.norm(x_new - x)
        residuals.append(res)
        if res < tol:
            break
        x = x_new
    return x, residuals

A = np.array([[4., -1., 0.], [-1., 4., -1.], [0., -1., 4.]])
b = np.array([15., 10., 10.])
x, resid = jacobi(A, b)
print("Jacobi 解:", x, "  迭代次数:", len(resid))

# 4.2 特征值
M = np.array([[2., 1.], [1., 3.]])
vals, vecs = linalg.eig(M)
for i, (lam, v) in enumerate(zip(vals.real, vecs.T)):
    print(f"λ{i+1}={lam:.4f}  Av={M@v.real}  λv={lam*v.real}")

# 4.3 最小二乘（直线拟合）
rng = np.random.default_rng(42)
t = np.linspace(0, 1, 20)
y = 2.5 * t + 0.3 + rng.normal(0, 0.1, 20)
A_ls = np.column_stack([t, np.ones_like(t)])
sol, res, rank, sv = linalg.lstsq(A_ls, y)
print(f"\\n斜率 {sol[0]:.3f}（真值 2.5）, 截距 {sol[1]:.3f}（真值 0.3）")
`,
  },

  {
    week: 5,
    title: '线性代数收尾与插值入门',
    module: '插值',
    lessons: [
      {
        id: '5.1', title: '最小二乘进阶：正则化与病态', level: 'B', hasAI: false,
        sessionGuide: '病态设计矩阵导致解爆炸 5min → 岭回归 (A\'A+λI)x=A\'b 8min → λ 的作用 7min → 解岭回归/画 λ-解范数曲线 10min → 随堂对比不同 λ 的拟合 15min',
        exercise: '构造 12 次多项式设计矩阵（病态），对比 λ=0/1e-4/1e-2 时的系数范数和拟合曲线；简短介绍 Lasso 与稀疏解的直观。',
      },
      {
        id: '5.2', title: '插值（一）：多项式插值与 Runge 现象', level: 'B', hasAI: false,
        sessionGuide: '插值问题定义 5min → 拉格朗日/牛顿差商思想 8min → scipy.interpolate.interp1d 10min → Runge 现象 12min → 随堂：等距节点画多种插值对比 10min',
        exercise: '对 f(x)=1/(1+x²) 在 [-5,5] 等距 11 节点上做：线性/三次/11次多项式插值；画三条曲线和精确值；测量最大误差。',
      },
      {
        id: '5.3', title: '插值（二）：样条插值', level: 'B', hasAI: false,
        sessionGuide: '样条动机（分段低次/光滑拼接）5min → 三次样条条件 8min → CubicSpline 用法 10min → 与多项式插值对比 10min → 随堂换数据改边界 12min',
        exercise: '用 CubicSpline 重做 5.2 的插值实验，比较与高次多项式的最大误差；探讨 not-a-knot 与 clamped 边界条件的差异。',
      },
    ],
    contextTags: ['week5', 'regularization', 'ridge-regression', 'interpolation', 'spline', 'runge-phenomenon'],
    literature: [LIT.TRIPS_PY, LIT.PYLOPS],
    demoCode: `# 第 5 周 · 正则化与插值
import numpy as np
from scipy import linalg, interpolate

# 5.1 岭回归
def ridge(A, b, lam):
    return linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ b)

t = np.linspace(-1, 1, 15)
y = np.sin(np.pi * t) + np.random.default_rng(0).normal(0, 0.05, len(t))
deg = 12
A = np.vander(t, deg + 1, increasing=True)
for lam in [0., 1e-4, 1e-2]:
    c = ridge(A, y, lam)
    print(f"λ={lam:.0e}  ‖c‖₂={np.linalg.norm(c):.2f}")

# 5.2 Runge 现象
x_nodes = np.linspace(-5, 5, 11)
y_nodes = 1 / (1 + x_nodes ** 2)
x_fine = np.linspace(-5, 5, 200)
cs = interpolate.CubicSpline(x_nodes, y_nodes)
y_exact = 1 / (1 + x_fine ** 2)
y_spline = cs(x_fine)
poly_coeff = np.polyfit(x_nodes, y_nodes, len(x_nodes) - 1)
y_poly = np.polyval(poly_coeff, x_fine)
print(f"\\n样条最大误差:    {np.max(np.abs(y_spline - y_exact)):.4f}")
print(f"多项式最大误差:  {np.max(np.abs(y_poly   - y_exact)):.4f}  (Runge!)")
`,
  },

  {
    week: 6,
    title: '拟合与数值微积分',
    module: '数值微积分',
    lessons: [
      {
        id: '6.1', title: '拟合：非线性拟合与 curve_fit', level: 'B', hasAI: false,
        sessionGuide: '拟合与插值区别 5min → 非线性模型 y=f(x;θ) 8min → curve_fit：函数形式/初值/协方差 12min → 残差图与 RMSE 7min → 随堂：指数/对数拟合 13min',
        exercise: '对指数衰减数据 y=2.5e^{-0.8t}+噪声，用 curve_fit 拟合参数；画数据+拟合曲线+残差；探讨初值对收敛的影响（坏初值不收敛）。',
      },
      {
        id: '6.2', title: '数值积分（一）：Newton-Cotes 与 quad', level: 'B', hasAI: false,
        sessionGuide: '积分动机 3min → 梯形/Simpson 公式 8min → 手算 ∫₀¹x²dx 7min → scipy.integrate.quad 用法 10min → 随堂 2-3 个已知积分 12min → 注意事项（奇点/无穷区间）5min',
        exercise: '用 quad 计算 ∫₀^∞ e^{-x²} dx、∫₀^π sin(x) dx；自写梯形法（n=100）与 quad 对比误差；处理 1/√x 的奇点（`limit=` 参数）。',
      },
      {
        id: '6.3', title: '数值积分（二）：Gauss 求积、数值微分与性能调优', level: 'B', hasAI: false,
        sessionGuide: 'Gauss 求积思想 7min → fixed_quad 调用 6min → 与 quad 对比 4min → 差商/步长权衡 8min → **性能调优入门** 8min（先写对再写快；向量化避 for 循环；第15周讲 profiling）→ 随堂 h-误差 12min',
        exercise: '对 sin(x) 在 π/4 处：用中心差商（不同 h）近似导数，画 h vs 误差曲线；思考 h 太小误差反增的原因（舍入误差）。',
      },
    ],
    contextTags: ['week6', 'curve-fitting', 'numerical-integration', 'numerical-differentiation', 'performance'],
    literature: [LIT.EV_PINN],
    demoCode: `# 第 6 周 · 拟合与数值微积分
import numpy as np
from scipy import optimize, integrate

# 6.1 非线性拟合：指数模型
def exp_model(t, a, b): return a * np.exp(-b * t)

rng = np.random.default_rng(7)
t_data = np.linspace(0, 3, 20)
y_data = 2.5 * np.exp(-0.8 * t_data) + rng.normal(0, 0.05, 20)
popt, _ = optimize.curve_fit(exp_model, t_data, y_data, p0=[2., 1.])
print(f"拟合: a={popt[0]:.4f}（真值 2.5）, b={popt[1]:.4f}（真值 0.8）")

# 6.2 数值积分
f = lambda x: np.exp(-x**2)
val, _ = integrate.quad(f, 0, 1)
print(f"\\n∫₀¹ e^(-x²) dx = {val:.8f}")

# 6.3 数值微分：差商 vs 精确
def f2(x): return np.sin(x)
x0 = np.pi / 4
print("\\nh        差商              误差")
for h in [1e-1, 1e-4, 1e-7, 1e-12]:
    deriv = (f2(x0 + h) - f2(x0 - h)) / (2 * h)
    err = abs(deriv - np.cos(x0))
    print(f"1e{int(np.log10(h)):+d}  {deriv:.10f}  {err:.2e}")
`,
  },

  {
    week: 7,
    title: '常微分方程初值问题',
    module: 'ODE',
    lessons: [
      {
        id: '7.1', title: 'ODE 初值问题：Euler 与改进 Euler', level: 'B', hasAI: false,
        sessionGuide: 'dy/dt=f(t,y), y(t₀)=y₀ 表述 3min → 一阶线性 ODE 手算 5min → Euler 法：几何直观/公式 10min → 改进 Euler（Heun）7min → 自写循环实现 10min → 改 h 观察误差 10min',
        exercise: '用 Euler 法解 y\'=-y，h=0.1/0.01/0.001，与解析解 e^{-t} 对比末端误差；画不同 h 下的误差曲线。',
      },
      {
        id: '7.2', title: 'Runge-Kutta 与 scipy.integrate.solve_ivp', level: 'B', hasAI: false,
        sessionGuide: 'RK 思想：多步 f 值提高精度 5min → 二阶/四阶 RK 公式 8min → solve_ivp 调用：fun/t_span/y0/t_eval 10min → 与 Euler 对比 7min → 随堂改参数 15min',
        exercise: '用 solve_ivp(method=\'RK45\') 解 y\'=-y，比较 rtol=1e-3/1e-6/1e-10 时的末端误差和函数调用次数。',
      },
      {
        id: '7.3', title: '刚性方程与稳定性简介', level: 'B', hasAI: true,
        sessionGuide: '刚性直观：有的方程 h 需极小才稳定 5min → 隐式思想/BDF 8min → method=\'Radau\'或\'BDF\' 5min → AI 环节：洛伦兹方程 15min → 何时显式/隐式小结 2min',
        aiPromptTemplate: '任务：让 AI 生成洛伦兹方程的 solve_ivp 代码并验证。\n\n建议提示词：\n"用 Python + scipy.integrate.solve_ivp，解洛伦兹方程：dx/dt=σ(y-x), dy/dt=x(ρ-z)-y, dz/dt=xy-βz，参数 σ=10, ρ=28, β=8/3，初值 [1,0,0]，t 从 0 到 40，画 x(t)/y(t)/z(t) 三条曲线和 3D 吸引子图"\n\n验证步骤：\n1. 确认方程右端的 3 个分量是否正确\n2. 改初值为 [1+1e-8, 0, 0]，观察对初值的敏感性\n3. 能否把 ρ 改为 20（非混沌区域）观察区别？',
        exercise: '解洛伦兹方程，画 3D 吸引子；改初值 [1+ε, 0, 0]（ε=1e-8）观察混沌对初值的敏感性；尝试 method=\'Radau\' 与 \'RK45\' 的速度对比。',
      },
    ],
    contextTags: ['week7', 'ode', 'euler-method', 'runge-kutta', 'solve_ivp', 'stiff-ode', 'lorenz'],
    literature: [LIT.JAX_ODE, LIT.EV_PINN],
    demoCode: `# 第 7 周 · 常微分方程初值问题
import numpy as np
from scipy.integrate import solve_ivp

# 7.1 Euler 法：dy/dt = -y
def euler(f, t0, y0, T, h):
    t = np.arange(t0, T + h, h)
    y = np.empty(len(t))
    y[0] = y0
    for i in range(len(t) - 1):
        y[i+1] = y[i] + h * f(t[i], y[i])
    return t, y

f_decay = lambda t, y: -y
t_e, y_e = euler(f_decay, 0, 1, 3, h=0.2)
print(f"Euler (h=0.2)  末端误差: {abs(y_e[-1] - np.exp(-3)):.4e}")

# 7.2 solve_ivp（RK45）
sol = solve_ivp(f_decay, [0, 3], [1.0], t_eval=np.linspace(0, 3, 100),
                method='RK45', rtol=1e-8)
print(f"RK45           末端误差: {abs(sol.y[0, -1] - np.exp(-3)):.4e}")

# 7.3 洛伦兹方程（AI 辅助环节）
sigma, rho, beta = 10., 28., 8/3
def lorenz(t, s): return [sigma*(s[1]-s[0]), s[0]*(rho-s[2])-s[1], s[0]*s[1]-beta*s[2]]

sol_l = solve_ivp(lorenz, [0, 40], [1., 0., 0.],
                  t_eval=np.linspace(0, 40, 8000), method='RK45', rtol=1e-8)
print(f"\\n洛伦兹末态: x={sol_l.y[0,-1]:.3f} y={sol_l.y[1,-1]:.3f} z={sol_l.y[2,-1]:.3f}")
`,
  },

  {
    week: 8,
    title: 'ODE 应用与方程求根',
    module: 'ODE + 优化',
    lessons: [
      {
        id: '8.1', title: 'ODE 小综合：单摆、振子与相图', level: 'B', hasAI: false,
        sessionGuide: '单摆/振子化为一阶系统 8min → fun/初值/solve_ivp/画曲线 12min → 相图：以 y1 为横轴画轨迹 10min → 随堂：改 ω/初值/阻尼项 15min',
        exercise: '解单摆 [θ\'=ω, ω\'=-g/L·sin(θ)]；画相图（闭合曲线=周期，开放=不稳定）；对比小角（sin≈θ）与大角（sin不可近似）的差异。',
      },
      {
        id: '8.2', title: '非线性方程求根：二分、Newton、scipy.optimize', level: 'B', hasAI: false,
        sessionGuide: 'f(x)=0 表述 3min → 二分法：思想/收敛/实现 10min → Newton：迭代式/几何直观/初值敏感 8min → fsolve/brentq 用法 7min → 随堂求根/多根 12min → 存在性 5min',
        exercise: '对 f(x)=x³-2x-5 用：①自写 Newton 法（≤20步）；②scipy brentq；③fsolve；比较收敛速度；画 f(x) 确认唯一实根。',
      },
      {
        id: '8.3', title: '无约束优化（一）：梯度、Newton 方向', level: 'B', hasAI: false,
        sessionGuide: '无约束优化/局部极小/梯度为0 5min → 梯度下降 8min → 牛顿法求极小 7min → scipy.optimize.minimize(method=\'BFGS\') 10min → 随堂：2D Rosenbrock 15min',
        exercise: '用 minimize(method=\'BFGS\') 找 Rosenbrock 函数极小；画等高线 + 优化轨迹（callback）；从不同初值出发，观察是否都收敛到 (1,1)。',
      },
    ],
    contextTags: ['week8', 'ode', 'phase-portrait', 'root-finding', 'bfgs', 'optimization'],
    literature: [LIT.EV_PINN, LIT.JAX_ODE],
    demoCode: `# 第 8 周 · ODE 应用与方程求根
import numpy as np
from scipy.integrate import solve_ivp
from scipy import optimize

# 8.1 单摆相图
def pendulum(t, y, omega=1.5):
    return [y[1], -omega**2 * np.sin(y[0])]

for y0 in [0.5, 1.5, 2.8]:
    sol = solve_ivp(pendulum, [0, 20], [y0, 0.], t_eval=np.linspace(0, 20, 500))
    print(f"θ₀={y0:.1f}  末端 θ={sol.y[0, -1]:.3f}")

# 8.2 Newton 法求根 f(x) = x³-2x-5
def f(x): return x**3 - 2*x - 5
def df(x): return 3*x**2 - 2

x = 2.0
for _ in range(20):
    x -= f(x) / df(x)
    if abs(f(x)) < 1e-12: break
print(f"\\nNewton 根: {x:.10f}  f(x)={f(x):.2e}")
print(f"brentq 根: {optimize.brentq(f, 2, 3):.10f}")

# 8.3 BFGS 优化 Rosenbrock
points = []
def rosenbrock(x):
    points.append(x.copy())
    return (1 - x[0])**2 + 100*(x[1] - x[0]**2)**2

res = optimize.minimize(rosenbrock, [-1., 1.], method='BFGS')
print(f"\\nRosenbrock 极小: {res.x.round(6)}, 迭代 {len(points)} 步")
`,
  },

  {
    week: 9,
    title: '优化与科学可视化',
    module: '优化 + 可视化',
    lessons: [
      {
        id: '9.1', title: '无约束优化（二）：BFGS、实践与调参', level: 'B', hasAI: false,
        sessionGuide: 'BFGS 直观（近似 Hessian 逆）5min → gtol/xtol/maxiter 5min → 完整示例/打印迭代数 10min → 初值敏感性 8min → 随堂调 tol 12min → 失败案例 5min',
        exercise: '对 Rosenbrock 从 5 个不同初值出发，记录各自迭代次数；用 callback 画迭代轨迹；尝试 method=\'Nelder-Mead\'，对比收敛速度。',
      },
      {
        id: '9.2', title: '约束优化入门与 SciPy', level: 'B', hasAI: false,
        sessionGuide: '约束优化 min f(x) s.t. g≤0,h=0 表述 5min → 等式约束直线上极小 8min → scipy constraints 参数 10min → 不等式约束圆盘内极小 7min → 随堂 2D 问题 15min',
        exercise: '在单位圆 x²+y²≤1 内最大化 x+2y（用 SLSQP）；画可行域和最优点；尝试加 bounds 参数（变量上下界）。',
      },
      {
        id: '9.3', title: '科学可视化：Matplotlib 2D/3D 与子图', level: 'B', hasAI: false,
        sessionGuide: 'fig,ax=plt.subplots 基本流程 8min → 多子图 subplots(2,2) 8min → 标注：xlabel/ylabel/legend/grid 7min → savefig/dpi/格式 3min → 3D：Axes3D/plot_surface 8min → 随堂重绘前面图表 11min',
        exercise: '把 7.3 洛伦兹方程的结果用 2×2 子图展示：① x(t)；② y(t)；③ z(t)；④ 3D 吸引子；统一风格（字体/颜色/图例），保存为 PNG。',
      },
    ],
    contextTags: ['week9', 'optimization', 'bfgs', 'constrained-optimization', 'matplotlib', '3d-visualization'],
    literature: [LIT.EV_PINN, LIT.DEEPF_NET],
    demoCode: `# 第 9 周 · 优化与科学可视化
import numpy as np
from scipy import optimize

# 9.1 BFGS 轨迹
points = []
def rosenbrock(x):
    points.append(x.copy())
    return (1 - x[0])**2 + 100*(x[1] - x[0]**2)**2

res = optimize.minimize(rosenbrock, [-1.5, 0.5], method='BFGS',
                        options={'gtol': 1e-8})
print(f"BFGS: 极小={res.x.round(6)}, 迭代={len(points)} 步")

# 9.2 约束优化：单位圆内最大化 x+y
obj = lambda x: -(x[0] + x[1])
cons = {'type': 'ineq', 'fun': lambda x: 1 - x[0]**2 - x[1]**2}
res2 = optimize.minimize(obj, [0., 0.], method='SLSQP', constraints=cons)
print(f"约束极值（最大 x+y）: {-res2.fun:.4f}  点: {res2.x.round(4)}")

# 9.3 可视化示例（等高线）
import matplotlib.pyplot as plt
x1 = np.linspace(-2, 2, 200)
y1 = np.linspace(-0.5, 3, 200)
X, Y = np.meshgrid(x1, y1)
Z = (1 - X)**2 + 100*(Y - X**2)**2
fig, ax = plt.subplots(figsize=(6, 4))
ax.contourf(X, Y, np.log1p(Z), levels=30, cmap='viridis')
pts = np.array(points[:50])
ax.plot(pts[:, 0], pts[:, 1], 'w-o', ms=2, alpha=0.5, label='BFGS 轨迹')
ax.set(title='Rosenbrock 等高线 + 优化轨迹', xlabel='x', ylabel='y')
ax.legend(fontsize=8)
plt.tight_layout()
print("图已生成（在 Jupyter 中会自动显示）")
`,
  },

  {
    week: 10,
    title: '可视化收尾与 AI 辅助科学计算',
    module: 'AI 辅助',
    lessons: [
      {
        id: '10.1', title: '可视化进阶：标注、动画与可复现出图', level: 'B', hasAI: true,
        sessionGuide: '科学出图规范（坐标轴/单位/图例/字体）8min → 可复现（代码放 Notebook/固定随机种子）5min → FuncAnimation 动画 12min → AI 环节 15min → 小结 5min',
        aiPromptTemplate: '任务：让 AI 生成带误差棒的散点图并拟合直线。\n\n建议提示词：\n"用 Python + matplotlib，给定 x=[1,2,3,4,5]，y=[2.1,3.8,6.2,7.9,10.1]，y_err=[0.3,0.4,0.5,0.4,0.3]，画带误差棒的散点图，叠加最小二乘直线拟合，标注坐标轴（xlabel=\'x\', ylabel=\'y\'），图例区分数据点和拟合线，设置 figsize=(6,4)"\n\n验证步骤：\n1. 修改 y_err 的值，确认误差棒随之变化\n2. 把拟合改为二次多项式\n3. 检查图的 xlabel/ylabel 是否正确显示',
        exercise: '给实验数据（自选）画带误差棒的散点图 + 最小二乘拟合线；保存为 300 dpi PDF（论文级）；用 FuncAnimation 做简单动图（如 ODE 解随时间演化）。',
      },
      {
        id: '10.2', title: 'AI 辅助（一）：提示与任务描述', level: 'B', hasAI: false,
        sessionGuide: '好提示要素（数学表述/输入输出/编程环境）8min → 反面例子：简略 vs 详细提示 12min → 迭代：先跑通再细化 10min → 随堂：每人写两版提示对比 AI 输出 15min',
        exercise: '选一个本课已学算法（如 lstsq/solve_ivp/minimize），写简略提示和详细提示，比较 AI 输出质量；整理出「好提示清单」。',
      },
      {
        id: '10.3', title: 'AI 辅助（二）：验证、调试与批判性使用', level: 'H', hasAI: false,
        sessionGuide: '为何必须验证（AI 会编公式/过时 API/数值错误）5min → **调试入门**：读 Traceback/print/断点/%debug/二分定位/把报错给 AI 8min → 案例 1：错误公式 10min → 案例 2：过时 API 6min → 案例 3：数值不稳定 6min → 随堂找错 10min',
        exercise: '以下代码有 bug：`def norm(v): return sum(v)**2`；用调试步骤（print → %debug → 文档对照）找出并修正；解释每一步在干什么。',
      },
    ],
    contextTags: ['week10', 'visualization', 'ai-assisted', 'debugging', 'prompt-engineering'],
    literature: [LIT.SCIPY_SPATIAL],
    demoCode: `# 第 10 周 · AI 辅助科学计算
import numpy as np
from scipy.integrate import solve_ivp

# 10.2 好提示 vs 差提示
# ─── 差提示（太模糊）：「写个 RK4 求解 ODE」
# ─── 好提示（详细）：────────────────────────────────
# "用 Python 3 + scipy，对 dy/dt = -y，初值 y(0)=1，
#  在 t∈[0,3] 内用 solve_ivp(method='RK45', rtol=1e-8)，
#  返回 t 数组和 y 数组，并打印 t=1,2,3 时的相对误差"
# ─────────────────────────────────────────────────────

sol = solve_ivp(lambda t, y: -y, [0, 3], [1.],
                t_eval=[1., 2., 3.], method='RK45', rtol=1e-8)
print("好提示生成的代码结果：")
for ti, yi in zip(sol.t, sol.y[0]):
    err = abs(yi - np.exp(-ti)) / np.exp(-ti)
    print(f"  t={ti:.0f}  y={yi:.8f}  相对误差={err:.2e}")

# 10.3 调试演示：识别并修正 bug
def broken_norm(v):
    """AI 生成的 bug 代码：意图计算 L2 范数"""
    return sum(v)**2           # BUG！应为 sum(x**2 for x in v)**0.5

# 调试步骤：
# 1. 读报错：没有报错，但结果 49 ≠ 5
# 2. print 验证：print(sum([3,4])**2)  → 49  ← 这里出错了
# 3. 对照文档：L2 范数 = sqrt(sum(x²))
v = [3.0, 4.0]
print(f"\\nbug 版本:  {broken_norm(v):.1f}  （期望 5.0）")
print(f"numpy 验证: {np.linalg.norm(v):.1f}")

def fixed_norm(v):
    return sum(x**2 for x in v) ** 0.5
print(f"修复版本:  {fixed_norm(v):.1f}")
`,
  },

  {
    week: 11,
    title: 'AI 辅助收尾与偏微分方程入门',
    module: 'PDE',
    lessons: [
      {
        id: '11.1', title: 'AI 辅助（三）：读文档与可复现性；布置期末项目', level: 'B', hasAI: false,
        sessionGuide: 'AI 查文档再官方确认 8min → 可复现性：注明 AI 使用与验证 7min → 随堂：选函数用 AI 查再文档定位 10min → **期末项目布置 15min**（handout：题目类型/提交第18周/AI与可复现要求/补考说明）',
        exercise: '用 AI 查 scipy.integrate.quad 的 limit 参数含义，然后在官方文档中定位对应段落；在 Notebook 里注明「本段 AI 辅助完成，已通过……验证」。',
      },
      {
        id: '11.2', title: 'PDE 入门（一）：一维热方程与有限差分', level: 'H', hasAI: false,
        sessionGuide: '一维热方程 u_t=u_xx 5min → 空间差分→ODE 系统 10min → 时间离散（显式 Euler）/稳定性条件（r≤0.5）10min → 自写或 scipy.sparse 12min → 随堂改 Δx/Δt 看不稳定 8min',
        exercise: '实现一维热方程显式差分（Δx=1/50, Δt 满足稳定性）；初值 sin(πx)，与解析解 e^{-π²t}sin(πx) 比较各时刻误差；尝试违反稳定性条件观察震荡。',
      },
      {
        id: '11.3', title: 'PDE 入门（二）：二维泊松与库的使用', level: 'H', hasAI: false,
        sessionGuide: '二维泊松 -Δu=f 5min → 五点差分/未知量排成向量 8min → FEniCS 或 SciPy Poisson 示例 15min → 画热力图 7min → 随堂改 f 或边界 10min',
        exercise: '用 scipy.sparse + spsolve 解二维泊松方程（5×5 节点）；画解的热力图；改右端 f 重跑并对比。',
      },
    ],
    contextTags: ['week11', 'pde', 'heat-equation', 'finite-difference', 'poisson', 'final-project'],
    literature: [LIT.HEAT_2D, LIT.PINN_HEAT],
    demoCode: `# 第 11 周 · 一维热方程有限差分
import numpy as np

# 11.2 一维热方程：u_t = u_xx
# 初值 u(x,0)=sin(πx)，边界 u(0,t)=u(1,t)=0
# 解析解：u(x,t) = exp(-π²t) sin(πx)

L, T = 1.0, 0.2
Nx, Nt = 50, 2000
dx, dt = L / Nx, T / Nt
r = dt / dx**2
print(f"dx={dx:.4f}, dt={dt:.6f}, r={r:.4f} ({'✓ 稳定' if r <= 0.5 else '✗ 不稳定！'})")

x = np.linspace(0, L, Nx + 1)
u = np.sin(np.pi * x)
u[0] = u[-1] = 0.0

snapshots = [(0.0, u.copy())]
for n in range(Nt):
    u_new = u.copy()
    u_new[1:-1] = u[1:-1] + r * (u[2:] - 2*u[1:-1] + u[:-1])
    u_new[0] = u_new[-1] = 0.0
    u = u_new
    if (n + 1) in [Nt//4, Nt//2, Nt]:
        snapshots.append(((n+1)*dt, u.copy()))

print("\\n时刻        最大误差")
for t_snap, u_snap in snapshots:
    u_exact = np.exp(-np.pi**2 * t_snap) * np.sin(np.pi * x)
    print(f"t={t_snap:.3f}    {np.max(np.abs(u_snap - u_exact)):.2e}")
`,
  },

  {
    week: 12,
    title: '偏微分方程与反问题 / UQ',
    module: '反问题 + UQ',
    lessons: [
      {
        id: '12.1', title: 'PDE 入门（三）：扩散方程与简单应用', level: 'H', hasAI: false,
        sessionGuide: '扩散方程带源项 5min → 离散右端加源项 8min → CFL/精度选取 7min → 一维热传导（端点加热）15min → 随堂改参数看演化 10min',
        exercise: '在热方程中加源项 g(x,t)=sin(πx)cos(t)；实现显式差分；画解随时间演化的动画（可选）。',
      },
      {
        id: '12.2', title: '反问题与正则化入门', level: 'H', hasAI: false,
        sessionGuide: '正问题 vs 反问题（已知系数求解 vs 已知部分解反推）8min → 不适定/正则化必要性 7min → Tikhonov（(A\'A+λI)x=A\'b，与岭回归一致）5min → 一维反热传导简化例 15min → 随堂改 λ 10min',
        exercise: '已知离散积分方程 Ax=b（由高斯核构成），加噪声后用 Tikhonov 反演 x；画不同 λ 下的解范数（L-曲线法选最优 λ）。',
      },
      {
        id: '12.3', title: '不确定性量化（一）：蒙特卡洛与抽样', level: 'H', hasAI: true,
        sessionGuide: '随机输入→随机输出 5min → 蒙特卡洛：抽样 N 次/均值/方差/分位数 12min → 简单 ODE 例 10min → AI 环节 13min → 小结 5min',
        aiPromptTemplate: '任务：让 AI 写 Monte Carlo UQ 脚本并验证。\n\n建议提示词：\n"对 ODE dy/dt = -k*y, y(0)=1，参数 k 服从 Uniform(0.5, 1.5)，做 1000 次采样，每次用 Euler 法（h=0.01）计算 y(1) 的值，画 y(1) 的直方图（50个 bin），打印均值和标准差"\n\n验证步骤：\n1. 将样本量从 1000 改为 100 和 10000，观察直方图收敛\n2. 手算解析期望 E[e^{-k}] = (e^{-0.5}-e^{-1.5})/1，与 MC 均值比较\n3. 能否改为正态分布 k~N(1.0, 0.3²)？',
        exercise: 'ODE y\'=-ky（k~Uniform(0.5,1.5)），做 5000 次 MC 采样；比较 MC 均值与解析期望 (e^{-0.5}-e^{-1.5})；画 95% 置信区间随时间的带状图。',
      },
    ],
    contextTags: ['week12', 'pde', 'inverse-problems', 'tikhonov', 'regularization', 'monte-carlo', 'uq'],
    literature: [LIT.TRIPS_PY, LIT.PYLOPS, LIT.UQPy, LIT.HEAT_2D],
    demoCode: `# 第 12 周 · 反问题与蒙特卡洛 UQ
import numpy as np
from scipy import linalg

rng = np.random.default_rng(0)

# 12.2 Tikhonov 正则化（离散积分方程）
n = 30
h = 1.0 / n
# 正问题矩阵（高斯核）
A = np.array([[h * np.exp(-((i-j)*h)**2 / 0.05) for j in range(n)] for i in range(n)])
x_true = np.where((np.arange(n)/n > 0.3) & (np.arange(n)/n < 0.7), 1.0, 0.0)
b_noisy = A @ x_true + rng.normal(0, 0.01, n)

print("Tikhonov 正则化（不同 λ 的相对误差）:")
for lam in [0., 1e-3, 1e-1]:
    x_reg = linalg.solve(A.T @ A + lam * np.eye(n), A.T @ b_noisy)
    err = np.linalg.norm(x_reg - x_true) / np.linalg.norm(x_true)
    print(f"  λ={lam:.0e}  误差={err:.4f}")

# 12.3 蒙特卡洛 UQ
N = 5000
k_samples = rng.uniform(0.5, 1.5, N)
y_at_1 = np.exp(-k_samples)  # 解析解

print(f"\\n蒙特卡洛（N={N}）y(1) 统计:")
print(f"  均值:       {y_at_1.mean():.5f}")
print(f"  解析期望:   {(np.exp(-0.5)-np.exp(-1.5))/1:.5f}")
print(f"  标准差:     {y_at_1.std():.5f}")
print(f"  95% CI:     [{np.percentile(y_at_1,2.5):.4f}, {np.percentile(y_at_1,97.5):.4f}]")
`,
  },

  {
    week: 13,
    title: '不确定性量化与可微编程',
    module: '可微编程',
    lessons: [
      {
        id: '13.1', title: '不确定性量化（二）：Chaospy / UQpy 初识', level: 'H', hasAI: false,
        sessionGuide: 'PCE 动机：正交多项式逼近随机解 10min → Chaospy/UQpy 最小示例 12min → 与 Monte Carlo 对比（同一问题）10min → 随堂换分布或换 ODE 13min',
        exercise: '用 Chaospy 对 k~Uniform(0.5,1.5) 做 PCE 估计 E[y(1)] 和 Var[y(1)]；与 N=1000/5000 Monte Carlo 对比精度和计算量。',
      },
      {
        id: '13.2', title: '可微编程（一）：自动微分与 JAX 入门', level: 'H', hasAI: false,
        sessionGuide: '为何要导数（优化/灵敏度/梯度下降）5min → 数值/符号/自动微分对比 5min → JAX：grad(f)(x)/jacfwd 12min → 对标量/向量函数求导 8min → 随堂验证 15min',
        exercise: '用 JAX grad 对 f(x)=x\'Ax、sin(x)、Rosenbrock 函数求导，与数值差商对比误差；测量计算速度差异。',
      },
      {
        id: '13.3', title: '可微编程（二）：ODE 参数辨识', level: 'H', hasAI: false,
        sessionGuide: '从观测反推 ODE 参数 θ 8min → 损失=观测-模型差/需 ∂损失/∂θ 7min → JAX+diffrax/odeint+grad 15min → 带噪数据拟合 θ 10min → 随堂改真值或噪声 5min',
        exercise: '对 y\'=-θy，从 5 个带噪观测（真值 θ=0.7）用 JAX grad 做梯度下降拟合 θ；与 scipy curve_fit 结果对比；改噪声水平观察估计精度变化。',
      },
    ],
    contextTags: ['week13', 'uq', 'polynomial-chaos', 'automatic-differentiation', 'jax', 'ode-calibration'],
    literature: [LIT.CHAOSPY, LIT.UQPy, LIT.JAX_ODE],
    demoCode: `# 第 13 周 · 自动微分与 ODE 参数辨识
import numpy as np

# 数值微分（无需 JAX）
def f(x): return x**3 - 2*x + 1.0
def numerical_grad(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)

x0 = 1.5
exact_grad = 3 * x0**2 - 2
num_grad   = numerical_grad(f, x0)
print(f"数值微分:  {num_grad:.8f}")
print(f"解析导数:  {exact_grad:.8f}")
print(f"误差:      {abs(num_grad - exact_grad):.2e}")

try:
    import jax
    import jax.numpy as jnp
    grad_f = jax.grad(f)
    print(f"JAX grad:  {float(grad_f(x0)):.8f}")
    print(f"JAX 误差:  {abs(float(grad_f(x0)) - exact_grad):.2e}")

    # ODE 参数辨识：y'=-θy，拟合 θ=0.7
    theta_true = 0.7
    t_obs = np.array([0., 0.5, 1.0, 1.5, 2.0])
    y_obs = jnp.array(np.exp(-theta_true * t_obs)
                      + np.random.default_rng(3).normal(0, 0.02, len(t_obs)))
    def loss(theta):
        return jnp.sum((jnp.exp(-theta * jnp.array(t_obs)) - y_obs)**2)
    theta = jnp.array(1.0)
    for step in range(300):
        g = jax.grad(loss)(theta)
        theta = theta - 0.3 * g
    print(f"\\n辨识 θ = {float(theta):.4f}（真值 {theta_true}）")
except ImportError:
    print("\\n（JAX 未安装，可 pip install jax 后运行 JAX 示例）")
`,
  },

  {
    week: 14,
    title: '科学机器学习（整周）',
    module: '科学 ML',
    lessons: [
      {
        id: '14.1', title: '科学 ML（一）：PINN 与物理信息神经网络', level: 'H', hasAI: false,
        sessionGuide: 'PINN 动机：u_θ(x) 近似 PDE 解 8min → 损失=残差+边界写法 10min → JAX/PyTorch 写网络/损失/优化循环 15min → 一维热/泊松小例：训练+画近似解 7min → 小结 5min',
        exercise: '对 u\'\'(x)+u(x)=0（精确解 sin(x)），写出 PINN 损失函数；若安装 JAX，训练 200 步并与解析解比较；讨论「配点」的选取策略。',
      },
      {
        id: '14.2', title: '科学 ML（二）：PINN 实践、验证与调参', level: 'C', hasAI: false,
        sessionGuide: 'PINN 可能不收敛/陷入局部极小 5min → 有解析解问题：PINN vs 解析解/画误差 12min → 与有限差分解对比/调参（宽度/深度/学习率/配点数）12min → 随堂调参 11min → 适用场景与局限 5min',
        exercise: '对比 PINN 与有限差分解同一 ODE 的精度与计算时间；调网络宽度（8/32/128）观察精度变化；总结 PINN「何时有优势、何时有局限」。',
      },
      {
        id: '14.3', title: '科学 ML（三）：延伸与文献', level: 'H', hasAI: false,
        sessionGuide: 'Neural ODE 简短回顾 8min → Fourier 神经算子一句话动机 7min → literature.md 选 1-2 篇 SciML 文献导读 15min → 科学 ML 在课程中的位置小结 10min → 选读任务 5min',
        exercise: '从 literature.md 选一篇 PINN 文献，整理「问题→课内知识→代码/库」对应表（半页）；讨论该文献的验证方式。',
      },
    ],
    contextTags: ['week14', 'pinn', 'scientific-ml', 'neural-ode', 'physics-informed'],
    literature: [LIT.EV_PINN, LIT.PINN_HEAT, LIT.HEAT_CAVITY, LIT.DEEPF_NET],
    demoCode: `# 第 14 周 · 物理信息神经网络（PINN）
# 求解 ODE：u'' + u = 0，u(0)=0, u(π)=0（精确解 u=sin(x)）
import numpy as np

def pinn_loss_demo():
    """
    PINN 损失函数构成演示（NumPy 版，仅展示原理）
      L_total = L_pde + λ * L_bc
      L_pde = mean(|u'' + u|²) 在配点上
      L_bc  = |u(0)|² + |u(π)|²
    使用精确解代入，验证损失应为 0
    """
    x = np.linspace(0.01, np.pi - 0.01, 20)  # 配点
    # 精确解：u=sin(x), u''=-sin(x)
    u = np.sin(x)
    u_xx = -np.sin(x)
    residual = u_xx + u            # ODE 残差
    L_pde = np.mean(residual**2)
    L_bc  = np.sin(0)**2 + np.sin(np.pi)**2
    print(f"PDE 残差损失（应≈0）: {L_pde:.2e}")
    print(f"边界损失（应≈0）:     {L_bc:.2e}")

pinn_loss_demo()

# 配点策略比较
for n_pts in [10, 50, 200]:
    x_coll = np.linspace(0.01, np.pi-0.01, n_pts)
    res = np.mean((-np.sin(x_coll) + np.sin(x_coll))**2)
    print(f"配点数 {n_pts:4d}:  L_pde={res:.2e}（近似=0 说明配点选取合理）")

print("\\n↑ 实际训练需要 JAX/PyTorch 支持自动微分，安装后可实现完整训练循环")
`,
  },

  {
    week: 15,
    title: 'Python 与 C 及其他语言的交互',
    module: '高性能',
    lessons: [
      {
        id: '15.1', title: '性能分析、Cython/Numba/ctypes', level: 'H', hasAI: false,
        sessionGuide: '何时需要 C/C++ 5min → Profiling（cProfile/line_profiler）10min → Cython .pyx 编译 10min → Numba @jit 8min → ctypes 加载 .so 7min → 随堂：对本课循环做 profiling 5min',
        exercise: '对第 15 周 demoCode 中的 loop_pairwise 用 cProfile 找热点；用 Numba @jit 加速，测量加速比；讨论进一步的 C 扩展场景。',
      },
      {
        id: '15.2', title: 'C/C++ 扩展实战', level: 'H', hasAI: false,
        sessionGuide: 'ctypes/cffi 加载 .so/argtypes/restype/ndarray.ctypes 10min → 实战：C/C++ 向量求和→编译→Python 调用→验证 25min → Cython 包装最小示例 5min → 小结 5min',
        exercise: '（有 C++ 环境者）写 C++ 函数计算两向量点积，编译为 .so，用 ctypes 调用并与 np.dot 结果验证；（无 C++ 者）完成 Numba @jit 加速实验。',
      },
      {
        id: '15.3', title: '其他语言与 GPU：Fortran/Julia/CUDA/CuPy', level: 'H', hasAI: false,
        sessionGuide: 'f2py/PyJulia/subprocess 一句话场景 8min → CuPy 与 NumPy 对应/CPU vs GPU 时间对比 15min → Numba CUDA kernel（向量加）12min → 小结 5min → 随堂 5min',
        exercise: '（有 GPU）用 CuPy 与 NumPy 做相同的矩阵乘法，对比 1000×1000 和 10000×10000 的时间；（无 GPU）读 CuPy 文档，画 CPU vs GPU 理论性能比较图。',
      },
    ],
    contextTags: ['week15', 'performance', 'numba', 'cython', 'ctypes', 'cuda', 'cupy', 'profiling'],
    literature: [LIT.SCIPY_SPATIAL],
    demoCode: `# 第 15 周 · 性能分析与加速
import numpy as np
import time

# 15.1 三种实现逐对距离，测量速度
def loop_pairwise(X):
    n = X.shape[0]
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            diff = X[i] - X[j]
            D[i, j] = np.sqrt(np.dot(diff, diff))
    return D

def vectorized_pairwise(X):
    diff = X[:, None, :] - X[None, :, :]   # (n, n, d)
    return np.sqrt((diff**2).sum(axis=-1))

from scipy.spatial.distance import cdist

n = 100
rng = np.random.default_rng(42)
X = rng.standard_normal((n, 3))

print(f"{'方法':<15} {'时间 (ms)':>12} {'加速比':>8}")
print("-" * 36)
t0 = time.perf_counter(); D1 = loop_pairwise(X);       t1 = time.perf_counter()
t2 = time.perf_counter(); D2 = vectorized_pairwise(X); t3 = time.perf_counter()
t4 = time.perf_counter(); D3 = cdist(X, X);            t5 = time.perf_counter()

base = (t1-t0)*1000
print(f"{'Python 循环':<15} {base:>12.2f} {'1.0×':>8}")
print(f"{'NumPy 向量化':<15} {(t3-t2)*1000:>12.2f} {base/(t3-t2)*1000:>7.0f}×")
print(f"{'scipy.cdist':<15} {(t5-t4)*1000:>12.2f} {base/(t5-t4)*1000:>7.0f}×")
print(f"结果一致: {np.allclose(D1, D2) and np.allclose(D1, D3)}")
# 注：实际 Numba/Cython 加速可在 Jupyter 中用 %timeit 和 @jit 测试
`,
  },

  {
    week: 16,
    title: '科学研究延伸阅读',
    module: '文献导读',
    lessons: [
      {
        id: '16.1', title: '按模块选读：反问题、ODE、PDE、SciML', level: 'H', hasAI: false,
        sessionGuide: 'literature.md 结构说明 5min → 三条线索导读（反问题 TRIPs-Py、ODE JAX/EV-PINN、PDE/PINN）各 8min → 学生自选模块阅读 1-2 篇做笔记 16min → 小结 8min',
        exercise: '选读 literature.md 中一篇文献，整理：① 研究问题；② 用到了哪几讲的知识；③ 核心代码/库；④ 验证方式。',
      },
      {
        id: '16.2', title: '文献与课内对应：报告或讨论', level: 'C', hasAI: false,
        sessionGuide: '2-3 组就所选文献做 5-8 分钟报告 20min → 教师点评（如何读论文/如何对应到代码）10min → 其余组交半页对应 10min → 小结 5min',
        exercise: '准备 5-8 分钟报告：①研究问题；②与课内对应；③用到了哪些库；④验证方式；⑤自己能否复现核心实验？',
      },
      {
        id: '16.3', title: '延伸阅读清单与考核说明', level: 'B', hasAI: false,
        sessionGuide: '发延伸阅读清单 8min → **考核说明**：成绩仅平时+项目（无笔试/上机）；AI 须注明并验证；项目不及格补考（重做或按校历）12min → 学生答疑 25min',
        exercise: '答疑时间：提出期末项目选题或实现方案；确认 Notebook 环境与提交格式。',
      },
    ],
    contextTags: ['week16', 'research-literature', 'inverse-problems', 'scientific-ml', 'review'],
    literature: [LIT.TRIPS_PY, LIT.JAX_ODE, LIT.PINN_HEAT, LIT.EV_PINN],
    demoCode: `# 第 16 周 · 科学研究文献回顾
# 综合课程核心模块，对应 literature.md 的三条线索

import numpy as np
from scipy import linalg, integrate, optimize, interpolate

print("=" * 55)
print("文献线索一：反问题 → TRIPs-Py (arXiv:2402.17603)")
print("=" * 55)
n = 20
A = np.eye(n) * 2 + np.eye(n, k=1) * (-1) + np.eye(n, k=-1) * (-1)
b = np.ones(n)
for lam in [0., 0.01, 0.1]:
    x = linalg.solve(A + lam * np.eye(n), b)
    print(f"  Tikhonov λ={lam:.2f}  ‖x‖={np.linalg.norm(x):.3f}")

print("\\n" + "=" * 55)
print("文献线索二：ODE 参数辨识 → JAX ODE (arXiv:2509.07283)")
print("=" * 55)
from scipy.optimize import minimize
theta_true = 0.7
t_obs = np.array([0., 0.5, 1.0, 1.5, 2.0])
y_obs = np.exp(-theta_true * t_obs) + np.random.default_rng(5).normal(0, 0.03, 5)
loss = lambda p: np.sum((np.exp(-p[0] * t_obs) - y_obs)**2)
res = minimize(loss, [1.0])
print(f"  拟合 θ = {res.x[0]:.4f}（真值 {theta_true}）")

print("\\n" + "=" * 55)
print("文献线索三：PDE/PINN → 热方程 (arXiv:2412.18786)")
print("=" * 55)
Nx, dt, T = 30, 0.001, 0.1
dx = 1.0 / Nx; r = dt / dx**2
u = np.sin(np.pi * np.linspace(0, 1, Nx+1))
for _ in range(int(T/dt)):
    u[1:-1] += r * (u[2:] - 2*u[1:-1] + u[:-1])
u_exact = np.exp(-np.pi**2 * T) * np.sin(np.pi * np.linspace(0,1,Nx+1))
print(f"  热方程有限差分误差: {np.max(np.abs(u - u_exact)):.2e}")
`,
  },

  {
    week: 17,
    title: '大规模与并行计算',
    module: '并行 + 工程化',
    lessons: [
      {
        id: '17.1', title: '多进程与并行思想', level: 'H', hasAI: false,
        sessionGuide: '并行动机（多核/蒙特卡洛/参数扫描）5min → multiprocessing.Pool/map/imap 10min → ProcessPoolExecutor 示例 10min → 随堂：对前面 Monte Carlo 做多进程加速 15min → 多进程 vs 多线程（GIL）5min',
        exercise: '对 12.3 的 Monte Carlo UQ（1000 次采样），分别用串行和 ProcessPoolExecutor（4进程）实现，测量加速比；讨论数据传递成本。',
      },
      {
        id: '17.2', title: 'Dask 与「比内存大」的计算', level: 'H', hasAI: false,
        sessionGuide: 'Dask 动机（数组大于内存/懒求值）5min → dask.array 与 NumPy API 对应 12min → 任务图与 .visualize() 5min → 随堂：大矩阵运算或逐块处理 18min → 小结 5min',
        exercise: '用 dask.array 做一次矩阵乘法和逐块均值计算；调用 .visualize() 查看任务图；与 NumPy 结果验证一致性。',
      },
      {
        id: '17.3', title: '科学计算工程化与设计模式', level: 'H', hasAI: false,
        sessionGuide: '工程化动机 5min → 模块化（函数/类/包）8min → 配置与数据分离 6min → **设计模式**（流水线+策略）15min → 单元测试入门（assert/pytest）5min → 随堂：把脚本拆成函数+配置+测试 8min',
        exercise: '把 4.1 的 Jacobi 迭代器重构为类（`class LinearSolver`，支持 method=\'jacobi\'|\'direct\'|\'lstsq\'）；为每种 method 写 pytest 单元测试。',
      },
    ],
    contextTags: ['week17', 'parallel', 'multiprocessing', 'dask', 'software-engineering', 'design-patterns'],
    literature: [LIT.SCIPY_SPATIAL],
    demoCode: `# 第 17 周 · 并行计算与科学计算工程化
import numpy as np
import time
from concurrent.futures import ProcessPoolExecutor

# 17.1 多进程并行：ODE 参数扫描
def run_ode(k: float) -> float:
    """Euler 法解 y'=-ky，返回 y(1)"""
    dt, t, y = 0.001, 0.0, 1.0
    while t < 1.0:
        y += dt * (-k * y)
        t += dt
    return y

k_values = np.linspace(0.5, 2.0, 20).tolist()

t0 = time.perf_counter()
serial = [run_ode(k) for k in k_values]
t1 = time.perf_counter()

t2 = time.perf_counter()
with ProcessPoolExecutor(max_workers=4) as pool:
    parallel = list(pool.map(run_ode, k_values))
t3 = time.perf_counter()

print(f"串行:   {(t1-t0)*1000:.1f} ms")
print(f"并行:   {(t3-t2)*1000:.1f} ms  (4 进程)")
print(f"结果一致: {np.allclose(serial, parallel)}")

# 17.3 策略模式：可替换的线性求解器
class LinearSolver:
    """策略模式：根据 method 选择求解算法"""
    def __init__(self, method: str = "direct"):
        self.method = method

    def solve(self, A: np.ndarray, b: np.ndarray) -> np.ndarray:
        from scipy import linalg
        if self.method == "direct":
            return linalg.solve(A, b)
        elif self.method == "lstsq":
            return linalg.lstsq(A, b)[0]
        elif self.method == "jacobi":
            D = np.diag(np.diag(A)); R = A - D; x = np.zeros_like(b, dtype=float)
            for _ in range(1000):
                x_new = (b - R @ x) / np.diag(A)
                if np.linalg.norm(x_new - x) < 1e-10: break
                x = x_new
            return x
        raise ValueError(f"未知 method: {self.method}")

A = np.array([[4., -1.], [-1., 3.]])
b = np.array([1., 2.])
for method in ["direct", "lstsq", "jacobi"]:
    sol = LinearSolver(method).solve(A, b)
    print(f"{method:8s} 解: {sol.round(5)}  残差: {np.linalg.norm(A@sol-b):.2e}")
`,
  },

  {
    week: 18,
    title: '项目提交与展示 / 轻松话题',
    module: '项目',
    lessons: [
      {
        id: '18.1', title: '项目提交与展示（一）', level: 'C', hasAI: false,
        sessionGuide: '提交方式/截止时间/格式确认 5min → 学生展示若干组（3-5 min/组：问题/方法/结果/验证/AI 使用）25min → 教师点评与共性问题 10min → 未展示组下节展示 5min',
        exercise: '准备展示：① 研究问题（1句话）；② 方法（用到哪几周知识）；③ 关键结果图；④ 验证方式；⑤ AI 使用说明；限 3-5 分钟。',
      },
      {
        id: '18.2', title: '项目展示（二）或轻松话题（一）', level: 'C', hasAI: false,
        sessionGuide: '若继续展示：同 18.1 → 若轻松话题：延伸阅读分享（学生/教师推荐 1-2 篇）15min → 科学计算前沿/工具生态小讲座（JAX/SciML/可复现实践）20min → 课程知识串讲 10min',
        exercise: '（轻松话题选项）选一个课程中感兴趣的主题（PINN/JAX/并行/UQ），准备 3 分钟介绍「我在这个方向想继续探索什么」。',
      },
      {
        id: '18.3', title: '轻松话题（二）或总结', level: 'B', hasAI: false,
        sessionGuide: '课程总结：各模块回顾与后续学习路径（数值分析/PDE 库/SciML/高性能）15min → literature.md 选读建议与可复现性再强调 10min → 自由答疑 20min',
        exercise: '课程结束！推荐延伸资源：① 数值分析课（Trefethen《Numerical Linear Algebra》）；② FEniCS/FEniCSx；③ JAX 生态（Diffrax/Optax）；④ literature.md 全文。',
      },
    ],
    contextTags: ['week18', 'project', 'presentation', 'review', 'final'],
    literature: [LIT.JAX_ODE, LIT.TRIPS_PY, LIT.EV_PINN],
    demoCode: `# 第 18 周 · 期末项目综合演示
# 融合课程全程关键工具的「一页纸 Python 科学计算清单」
import numpy as np
from scipy import linalg, integrate, optimize
import time

print("=" * 60)
print("Python 科学计算课程 · 第 18 周综合演示")
print("=" * 60)

rng = np.random.default_rng(2026)

# 1. 数值线性代数（第 3-5 周）
n = 100
A = rng.standard_normal((n, n))
A = A @ A.T + n * np.eye(n)
b = rng.standard_normal(n)
x = linalg.solve(A, b)
print(f"1. 线性系统    残差: {np.linalg.norm(A@x-b):.2e}   cond: {np.linalg.cond(A):.1f}")

# 2. 最小二乘 + 正则化（第 4-5 周）
A_ls = rng.standard_normal((50, 20))
b_ls = rng.standard_normal(50)
x_ls, _, _, _ = linalg.lstsq(A_ls, b_ls)
x_reg = linalg.solve(A_ls.T @ A_ls + 0.1 * np.eye(20), A_ls.T @ b_ls)
print(f"2. 最小二乘   ‖x‖={np.linalg.norm(x_ls):.2f}  正则化‖x‖={np.linalg.norm(x_reg):.2f}")

# 3. ODE + SIR 传染病模型（第 7-8 周）
def sir(t, y, beta=0.5, gamma=0.1):
    S, I, R = y; N = S+I+R
    return [-beta*S*I/N, beta*S*I/N-gamma*I, gamma*I]
sol = integrate.solve_ivp(sir, [0, 160], [990., 10., 0.],
                          t_eval=np.linspace(0, 160, 500))
print(f"3. SIR 模型    峰值感染: {sol.y[1].max():.0f}人")

# 4. 非线性拟合（第 6 周）
from scipy.optimize import curve_fit
t_data = np.linspace(0, 3, 20)
y_data = 2.5 * np.exp(-0.8*t_data) + rng.normal(0, 0.05, 20)
p, _ = curve_fit(lambda t,a,b: a*np.exp(-b*t), t_data, y_data, p0=[2,1])
print(f"4. 曲线拟合    a={p[0]:.3f}（真2.5） b={p[1]:.3f}（真0.8）")

# 5. 蒙特卡洛 UQ（第 12 周）
k_mc = rng.uniform(0.5, 1.5, 10000)
print(f"5. Monte Carlo E[e^(-k)]: {np.exp(-k_mc).mean():.5f}（解析: {(np.exp(-0.5)-np.exp(-1.5)):.5f}）")

print("\\n课程圆满结束！感谢同学们的参与与努力。")
`,
  },
]

export default WEEKS

export function getWeek(n: number): WeekData | undefined {
  return WEEKS.find((w) => w.week === n)
}
