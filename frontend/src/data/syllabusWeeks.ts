/**
 * 18-Week Python Scientific Computing course syllabus data.
 * Mirrors meta_course/schedule-18weeks.md.
 * Each week contains:
 *   - title, module, level
 *   - 3 lessons
 *   - A runnable Python code example for the Monaco editor
 *   - context_tags for the AI audit endpoint
 */

export type LessonLevel = 'B' | 'H' | 'C'

export interface Lesson {
  id: string       // e.g. "1.1"
  title: string
  level: LessonLevel
  hasAI: boolean
}

export interface WeekData {
  week: number
  title: string
  module: string
  lessons: [Lesson, Lesson, Lesson]
  contextTags: string[]
  demoCode: string
}

const WEEKS: WeekData[] = [
  // ──────────────────────────────────────────────────────────
  // 第 1 周
  // ──────────────────────────────────────────────────────────
  {
    week: 1,
    title: '环境与 Python 最小子集',
    module: '工具与基础',
    lessons: [
      { id: '1.1', title: '课程导论与工具链：uv/conda + Jupyter', level: 'B', hasAI: false },
      { id: '1.2', title: 'Python 最小子集（一）：变量、列表与索引', level: 'B', hasAI: false },
      { id: '1.3', title: 'Python 最小子集（二）：循环、函数与文件读写', level: 'B', hasAI: true },
    ],
    contextTags: ['week1', 'python-basics', 'environment'],
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

# AI 辅助环节：
# 任务：用 AI 生成「读 CSV 并求均值」的代码，然后在此验证
# 提示词示例：
#   "用 Python 读取 data/week01_sample.csv（列名 x, y），
#    计算 y 列的均值，不使用 pandas"
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 2 周
  // ──────────────────────────────────────────────────────────
  {
    week: 2,
    title: 'NumPy 与数组计算',
    module: 'NumPy',
    lessons: [
      { id: '2.1', title: 'ndarray 创建、形状与 dtype', level: 'B', hasAI: false },
      { id: '2.2', title: '索引、切片与广播规则', level: 'B', hasAI: false },
      { id: '2.3', title: '线性代数运算与范数', level: 'B', hasAI: true },
    ],
    contextTags: ['week2', 'numpy', 'broadcasting', 'linear-algebra'],
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

# 广播：列向量与行向量相加
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

# AI 辅助：查询 np.linalg.norm 的 ord 参数含义并验证
# 例如：ord='nuc' 是核范数（奇异值之和）
print("‖M‖_nuc =", np.linalg.norm(M, ord='nuc'))
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 3 周
  // ──────────────────────────────────────────────────────────
  {
    week: 3,
    title: 'NumPy 进阶与误差基础',
    module: '误差与线性代数',
    lessons: [
      { id: '3.1', title: '矩阵分解：LU、QR、SVD 初识', level: 'B', hasAI: false },
      { id: '3.2', title: '误差、稳定性与条件数', level: 'B', hasAI: false },
      { id: '3.3', title: '线性方程组（一）：直接法', level: 'B', hasAI: false },
    ],
    contextTags: ['week3', 'numpy', 'matrix-decomposition', 'numerical-stability', 'linear-systems'],
    demoCode: `# 第 3 周 · 矩阵分解与误差基础
import numpy as np
from scipy import linalg

A = np.array([[4., 3.], [6., 3.]])

# 3.1 LU 分解
P, L, U = linalg.lu(A)
print("A =\\n", A)
print("L =\\n", L, "\\nU =\\n", U)
print("P @ L @ U == A?", np.allclose(P @ L @ U, A))

# QR 分解
Q, R = linalg.qr(A)
print("\\n‖Q^T Q - I‖ =", np.linalg.norm(Q.T @ Q - np.eye(2)))

# SVD
U_, s, Vt = linalg.svd(A)
print("奇异值:", s)

# 3.2 条件数与病态
H = np.array([[1, 1/2, 1/3],
              [1/2, 1/3, 1/4],
              [1/3, 1/4, 1/5]])  # Hilbert 矩阵（病态）
print("\\ncond(Hilbert 3×3) =", np.linalg.cond(H))

b = np.array([1., 0., 0.])
x = linalg.solve(H, b)
print("solve 解:", x)
print("残差 ‖Hx - b‖ =", np.linalg.norm(H @ x - b))

# 3.3 直接法
A2 = np.array([[2., 1., -1.],
               [-3., -1., 2.],
               [-2., 1., 2.]])
b2 = np.array([8., -11., -3.])
x2 = linalg.solve(A2, b2)
print("\\n解:", x2)
print("验证 A @ x ≈ b:", np.allclose(A2 @ x2, b2))
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 4 周
  // ──────────────────────────────────────────────────────────
  {
    week: 4,
    title: '线性代数数值解',
    module: '线性代数',
    lessons: [
      { id: '4.1', title: '线性方程组（二）：迭代法 Jacobi/G-S', level: 'B', hasAI: false },
      { id: '4.2', title: '特征值与特征向量：幂法、scipy.linalg.eig', level: 'B', hasAI: false },
      { id: '4.3', title: '最小二乘与正规方程', level: 'B', hasAI: true },
    ],
    contextTags: ['week4', 'linear-systems', 'eigenvalues', 'least-squares', 'numpy'],
    demoCode: `# 第 4 周 · 线性代数数值解
import numpy as np
from scipy import linalg
import matplotlib.pyplot as plt

# 4.1 Jacobi 迭代法
def jacobi(A, b, max_iter=100, tol=1e-8):
    D = np.diag(np.diag(A))
    R = A - D
    x = np.zeros_like(b, dtype=float)
    residuals = []
    for _ in range(max_iter):
        x_new = (b - R @ x) / np.diag(A)
        residuals.append(np.linalg.norm(x_new - x))
        if residuals[-1] < tol:
            break
        x = x_new
    return x, residuals

# 对角占优矩阵（收敛）
A = np.array([[4., -1., 0.],
              [-1., 4., -1.],
              [0., -1., 4.]])
b = np.array([15., 10., 10.])
x, resid = jacobi(A, b)
print("Jacobi 解:", x, "  迭代次数:", len(resid))
print("scipy 解:", linalg.solve(A, b))

# 4.2 特征值
M = np.array([[2., 1.], [1., 3.]])
vals, vecs = linalg.eig(M)
print("\\n特征值:", vals.real)
for i, (lam, v) in enumerate(zip(vals.real, vecs.T)):
    print(f"  λ{i+1}={lam:.4f}, M@v = {M @ v.real}, λv = {lam * v.real}")

# 4.3 最小二乘（直线拟合）
rng = np.random.default_rng(42)
t = np.linspace(0, 1, 20)
y = 2.5 * t + 0.3 + rng.normal(0, 0.1, 20)
A_ls = np.column_stack([t, np.ones_like(t)])
sol, res, rank, sv = linalg.lstsq(A_ls, y)
print(f"\\n最小二乘：斜率 {sol[0]:.3f}, 截距 {sol[1]:.3f}")
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 5 周
  // ──────────────────────────────────────────────────────────
  {
    week: 5,
    title: '线性代数收尾与插值入门',
    module: '插值',
    lessons: [
      { id: '5.1', title: '最小二乘进阶：正则化与病态', level: 'B', hasAI: false },
      { id: '5.2', title: '插值（一）：多项式插值与 Runge 现象', level: 'B', hasAI: false },
      { id: '5.3', title: '插值（二）：样条插值', level: 'B', hasAI: false },
    ],
    contextTags: ['week5', 'regularization', 'interpolation', 'spline', 'runge-phenomenon'],
    demoCode: `# 第 5 周 · 正则化与插值
import numpy as np
from scipy import linalg, interpolate
import matplotlib.pyplot as plt

# 5.1 岭回归：(A'A + λI)x = A'b
def ridge_regression(A, b, lam):
    AtA = A.T @ A
    Atb = A.T @ b
    return linalg.solve(AtA + lam * np.eye(AtA.shape[0]), Atb)

# 高次多项式设计矩阵（病态）
t = np.linspace(-1, 1, 15)
y = np.sin(np.pi * t) + np.random.default_rng(0).normal(0, 0.05, len(t))
deg = 12
A = np.vander(t, deg + 1, increasing=True)

for lam in [0.0, 1e-4, 1e-2]:
    c = ridge_regression(A, y, lam)
    print(f"λ={lam:.0e}  ‖c‖₂={np.linalg.norm(c):.2f}")

# 5.2 Runge 现象
x_nodes = np.linspace(-5, 5, 11)
y_nodes = 1 / (1 + x_nodes ** 2)
x_fine = np.linspace(-5, 5, 200)
# 样条插值（稳定）
cs = interpolate.CubicSpline(x_nodes, y_nodes)
y_spline = cs(x_fine)
# 多项式插值（Runge 现象）
poly_coeff = np.polyfit(x_nodes, y_nodes, len(x_nodes) - 1)
y_poly = np.polyval(poly_coeff, x_fine)
y_exact = 1 / (1 + x_fine ** 2)

print(f"\\n样条最大误差:    {np.max(np.abs(y_spline - y_exact)):.4f}")
print(f"多项式最大误差:  {np.max(np.abs(y_poly   - y_exact)):.4f}  (Runge!)")
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 6 周
  // ──────────────────────────────────────────────────────────
  {
    week: 6,
    title: '拟合与数值微积分',
    module: '数值微积分',
    lessons: [
      { id: '6.1', title: '拟合：最小二乘多项式与非线性拟合', level: 'B', hasAI: false },
      { id: '6.2', title: '数值积分（一）：Newton-Cotes 与 quad', level: 'B', hasAI: false },
      { id: '6.3', title: '数值积分（二）：Gauss 求积、数值微分与性能调优', level: 'B', hasAI: false },
    ],
    contextTags: ['week6', 'curve-fitting', 'numerical-integration', 'numerical-differentiation'],
    demoCode: `# 第 6 周 · 拟合与数值微积分
import numpy as np
from scipy import optimize, integrate

# 6.1 非线性拟合：指数模型
def exp_model(t, a, b):
    return a * np.exp(-b * t)

rng = np.random.default_rng(7)
t_data = np.linspace(0, 3, 20)
y_data = 2.5 * np.exp(-0.8 * t_data) + rng.normal(0, 0.05, 20)
popt, pcov = optimize.curve_fit(exp_model, t_data, y_data, p0=[2., 1.])
print(f"拟合参数：a={popt[0]:.4f}（真值 2.5）, b={popt[1]:.4f}（真值 0.8）")

# 6.2 数值积分
# 梯形公式（手写）
def trapz_rule(f, a, b, n=1000):
    h = (b - a) / n
    x = np.linspace(a, b, n + 1)
    return h * (f(x[0]) / 2 + f(x[-1]) / 2 + np.sum(f(x[1:-1])))

f = lambda x: np.exp(-x**2)
val_trap, _ = integrate.quad(f, 0, 1)
val_our   = trapz_rule(f, 0, 1, n=100)
print(f"\\nquad 结果:       {val_trap:.10f}")
print(f"梯形 n=100:      {val_our:.10f}")

# 6.3 数值微分：差商 vs 精确值
def f2(x): return np.sin(x)
def df_exact(x): return np.cos(x)

x0 = np.pi / 4
for h in [1e-1, 1e-4, 1e-7, 1e-12]:
    deriv = (f2(x0 + h) - f2(x0 - h)) / (2 * h)
    err = abs(deriv - df_exact(x0))
    print(f"h={h:.0e}  差商={deriv:.8f}  误差={err:.2e}")
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 7 周
  // ──────────────────────────────────────────────────────────
  {
    week: 7,
    title: '常微分方程初值问题',
    module: 'ODE',
    lessons: [
      { id: '7.1', title: 'ODE 初值问题：Euler 与改进 Euler', level: 'B', hasAI: false },
      { id: '7.2', title: 'Runge-Kutta 与 scipy.integrate.solve_ivp', level: 'B', hasAI: false },
      { id: '7.3', title: '刚性方程与稳定性简介', level: 'B', hasAI: true },
    ],
    contextTags: ['week7', 'ode', 'euler-method', 'runge-kutta', 'solve_ivp', 'stiff-ode'],
    demoCode: `# 第 7 周 · 常微分方程初值问题
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# 7.1 Euler 法：dy/dt = -y, y(0) = 1
def euler(f, t0, y0, T, h):
    t = np.arange(t0, T + h, h)
    y = np.empty(len(t))
    y[0] = y0
    for i in range(len(t) - 1):
        y[i+1] = y[i] + h * f(t[i], y[i])
    return t, y

f_decay = lambda t, y: -y
t_euler, y_euler = euler(f_decay, 0, 1, 3, h=0.2)
t_fine = np.linspace(0, 3, 300)
print("Euler (h=0.2) 末端误差:", abs(y_euler[-1] - np.exp(-3)))

# 7.2 solve_ivp（RK45）
sol = solve_ivp(f_decay, [0, 3], [1.0], t_eval=np.linspace(0, 3, 100),
                method='RK45', rtol=1e-6)
print("RK45 末端误差:         ", abs(sol.y[0, -1] - np.exp(-3)))

# 7.3 AI 辅助环节：洛伦兹方程
# 任务：描述「洛伦兹方程 + 初值 + 画三条分量曲线」让 AI 生成代码
sigma, rho, beta = 10., 28., 8/3
def lorenz(t, state):
    x, y, z = state
    return [sigma*(y - x), x*(rho - z) - y, x*y - beta*z]

sol_l = solve_ivp(lorenz, [0, 40], [1., 0., 0.],
                  t_eval=np.linspace(0, 40, 8000), method='RK45', rtol=1e-8)
print("\\n洛伦兹轨迹末态:", sol_l.y[:, -1].round(3))
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 8 周
  // ──────────────────────────────────────────────────────────
  {
    week: 8,
    title: 'ODE 应用与方程求根',
    module: 'ODE + 优化',
    lessons: [
      { id: '8.1', title: 'ODE 小综合：单摆、振子与相图', level: 'B', hasAI: false },
      { id: '8.2', title: '非线性方程求根：二分、Newton、scipy.optimize', level: 'B', hasAI: false },
      { id: '8.3', title: '无约束优化（一）：梯度、Newton 方向', level: 'B', hasAI: false },
    ],
    contextTags: ['week8', 'ode', 'phase-portrait', 'root-finding', 'optimization'],
    demoCode: `# 第 8 周 · ODE 应用与方程求根
import numpy as np
from scipy.integrate import solve_ivp
from scipy import optimize

# 8.1 单摆相图：y' = [y2, -ω²sin(y1)]
omega = 1.5

def pendulum(t, y, omega):
    return [y[1], -omega**2 * np.sin(y[0])]

for y0_angle in [0.5, 1.5, 2.8]:
    sol = solve_ivp(pendulum, [0, 20], [y0_angle, 0.],
                    args=(omega,), t_eval=np.linspace(0, 20, 500))
    print(f"θ₀={y0_angle:.1f}  末端 θ={sol.y[0, -1]:.3f}")

# 8.2 Newton 法求根
def f(x): return x**3 - 2*x - 5
def df(x): return 3*x**2 - 2

# 手写 Newton
x = 2.0
for _ in range(20):
    x = x - f(x) / df(x)
    if abs(f(x)) < 1e-12:
        break
print(f"\\nNewton 根: {x:.10f}  f(x)={f(x):.2e}")

# scipy
root = optimize.brentq(f, 2, 3)
print(f"brentq 根: {root:.10f}")

# 8.3 BFGS 最小化 Rosenbrock
def rosenbrock(x): return (1 - x[0])**2 + 100*(x[1] - x[0]**2)**2
def grad_rosenbrock(x):
    return np.array([
        -2*(1 - x[0]) - 400*x[0]*(x[1] - x[0]**2),
        200*(x[1] - x[0]**2)
    ])

res = optimize.minimize(rosenbrock, [-1., 1.], jac=grad_rosenbrock, method='BFGS')
print(f"\\nRosenbrock 极小: {res.x.round(6)}, f={res.fun:.2e}")
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 9 周
  // ──────────────────────────────────────────────────────────
  {
    week: 9,
    title: '优化与科学可视化',
    module: '优化 + 可视化',
    lessons: [
      { id: '9.1', title: '无约束优化（二）：BFGS、实践与调参', level: 'B', hasAI: false },
      { id: '9.2', title: '约束优化入门与 SciPy 使用', level: 'B', hasAI: false },
      { id: '9.3', title: '科学可视化：Matplotlib 2D/3D 与子图', level: 'B', hasAI: false },
    ],
    contextTags: ['week9', 'optimization', 'bfgs', 'constrained-optimization', 'matplotlib'],
    demoCode: `# 第 9 周 · 优化与科学可视化
import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt

# 9.1 BFGS 调参（回调记录轨迹）
points = []
def rosenbrock(x):
    points.append(x.copy())
    return (1 - x[0])**2 + 100*(x[1] - x[0]**2)**2

res = optimize.minimize(rosenbrock, [-1.5, 0.5], method='BFGS',
                        options={'gtol': 1e-8, 'maxiter': 500})
print(f"BFGS: 极小={res.x.round(6)}, 迭代={len(points)} 步")

# 9.2 约束优化：在圆 x²+y² ≤ 1 内最大化 x+y
obj = lambda x: -(x[0] + x[1])
constraints = {'type': 'ineq', 'fun': lambda x: 1 - x[0]**2 - x[1]**2}
res2 = optimize.minimize(obj, [0., 0.], method='SLSQP',
                         constraints=constraints)
print(f"约束极值（最大 x+y）: {-res2.fun:.4f}  点: {res2.x.round(4)}")

# 9.3 多子图可视化
fig, axes = plt.subplots(1, 2, figsize=(10, 4))

# 左：等高线 + BFGS 轨迹
x1 = np.linspace(-2, 2, 200)
y1 = np.linspace(-0.5, 3, 200)
X, Y = np.meshgrid(x1, y1)
Z = (1 - X)**2 + 100*(Y - X**2)**2
axes[0].contourf(X, Y, np.log1p(Z), levels=30, cmap='viridis')
pts = np.array(points[:100])
axes[0].plot(pts[:, 0], pts[:, 1], 'w-o', ms=2, alpha=0.6, label='BFGS 轨迹')
axes[0].set(title='Rosenbrock 等高线 + 优化轨迹', xlabel='x', ylabel='y')
axes[0].legend(fontsize=8)

# 右：约束域与解
theta = np.linspace(0, 2*np.pi, 200)
axes[1].fill(np.cos(theta), np.sin(theta), alpha=0.2, label='可行域')
axes[1].plot(*res2.x, 'r*', ms=12, label=f'极值点 ({res2.x[0]:.2f},{res2.x[1]:.2f})')
axes[1].set(title='约束优化：最大化 x+y', xlabel='x', ylabel='y', aspect='equal')
axes[1].legend(fontsize=8)

plt.tight_layout()
plt.savefig('/tmp/week09_optimization.png', dpi=120)
print("图已保存")
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 10 周
  // ──────────────────────────────────────────────────────────
  {
    week: 10,
    title: '可视化收尾与 AI 辅助科学计算',
    module: 'AI 辅助',
    lessons: [
      { id: '10.1', title: '可视化进阶：标注、动画与可复现出图', level: 'B', hasAI: true },
      { id: '10.2', title: 'AI 辅助（一）：提示与任务描述', level: 'B', hasAI: false },
      { id: '10.3', title: 'AI 辅助（二）：验证、调试与批判性使用', level: 'H', hasAI: false },
    ],
    contextTags: ['week10', 'visualization', 'ai-assisted', 'debugging', 'prompt-engineering'],
    demoCode: `# 第 10 周 · AI 辅助科学计算
import numpy as np
from scipy.integrate import solve_ivp

# 10.2 好提示 vs 差提示示例
# ─── 差提示：「写个 RK4 求解 ODE」（太模糊）
# ─── 好提示：────────────────────────────────
# "用 Python 3 + scipy，对 dy/dt = -y，初值 y(0)=1，
#  在 t∈[0,3] 内用 solve_ivp(method='RK45', rtol=1e-8)，
#  返回 t 数组和 y 数组，并打印 t=1,2,3 时的相对误差"
# ────────────────────────────────────────────

sol = solve_ivp(lambda t, y: -y, [0, 3], [1.],
                t_eval=[1., 2., 3.], method='RK45', rtol=1e-8)
for ti, yi in zip(sol.t, sol.y[0]):
    err = abs(yi - np.exp(-ti)) / np.exp(-ti)
    print(f"t={ti:.0f}  y={yi:.8f}  相对误差={err:.2e}")

# 10.3 调试示例：识别 AI 给出的错误代码
# 下面这段代码有 bug，请找出并修正：
def broken_norm(v):
    """尝试计算 L2 范数，但有错误"""
    return sum(v)**2  # BUG: 应该是 sum(x**2 for x in v) ** 0.5

v = [3.0, 4.0]
print("\\n错误结果:", broken_norm(v))        # 49，不对
print("正确结果:", np.linalg.norm(v))       # 5.0

def fixed_norm(v):
    return sum(x**2 for x in v) ** 0.5

print("修复结果:", fixed_norm(v))

# 10.3 调试策略：读 Traceback → print 定位 → 对照文档
# 验证：用已知结果（如 ‖[3,4]‖=5）检验修复是否正确
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 11 周
  // ──────────────────────────────────────────────────────────
  {
    week: 11,
    title: 'AI 辅助收尾与偏微分方程入门',
    module: 'PDE',
    lessons: [
      { id: '11.1', title: 'AI 辅助（三）：读文档与可复现性；期末项目布置', level: 'B', hasAI: false },
      { id: '11.2', title: 'PDE 入门（一）：一维热方程与有限差分', level: 'H', hasAI: false },
      { id: '11.3', title: 'PDE 入门（二）：二维泊松与库的使用', level: 'H', hasAI: false },
    ],
    contextTags: ['week11', 'pde', 'heat-equation', 'finite-difference', 'poisson'],
    demoCode: `# 第 11 周 · 一维热方程有限差分
import numpy as np
import matplotlib.pyplot as plt

# 11.2 一维热方程：u_t = u_xx，显式差分
# 边界：u(0,t)=0, u(1,t)=0；初值：u(x,0)=sin(πx)

L = 1.0
T = 0.2
Nx = 50          # 空间节点数
Nt = 2000        # 时间步数
dx = L / Nx
dt = T / Nt
r = dt / dx**2   # 稳定性条件：r ≤ 0.5

print(f"dx={dx:.4f}, dt={dt:.6f}, r={r:.4f} ({'稳定' if r <= 0.5 else '不稳定！'})")

x = np.linspace(0, L, Nx + 1)
u = np.sin(np.pi * x)  # 初始条件
u[0] = u[-1] = 0.0     # 边界

snapshots = [(0.0, u.copy())]
for n in range(Nt):
    u_new = u.copy()
    u_new[1:-1] = u[1:-1] + r * (u[2:] - 2*u[1:-1] + u[:-1])
    u_new[0] = u_new[-1] = 0.0
    u = u_new
    if (n + 1) in [Nt // 4, Nt // 2, Nt]:
        snapshots.append(((n + 1) * dt, u.copy()))

# 解析解：u(x,t) = exp(-π²t) sin(πx)
for t_snap, u_snap in snapshots:
    u_exact = np.exp(-np.pi**2 * t_snap) * np.sin(np.pi * x)
    err = np.max(np.abs(u_snap - u_exact))
    print(f"t={t_snap:.3f}  最大误差={err:.2e}")
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 12 周
  // ──────────────────────────────────────────────────────────
  {
    week: 12,
    title: '偏微分方程与反问题 / UQ',
    module: '反问题 + UQ',
    lessons: [
      { id: '12.1', title: 'PDE 入门（三）：扩散方程与简单应用', level: 'H', hasAI: false },
      { id: '12.2', title: '反问题与正则化入门', level: 'H', hasAI: false },
      { id: '12.3', title: '不确定性量化（一）：蒙特卡洛与抽样', level: 'H', hasAI: true },
    ],
    contextTags: ['week12', 'pde', 'inverse-problems', 'tikhonov', 'monte-carlo', 'uq'],
    demoCode: `# 第 12 周 · 反问题与蒙特卡洛 UQ
import numpy as np
from scipy import linalg

rng = np.random.default_rng(0)

# 12.2 Tikhonov 正则化（一维反卷积）
# 正问题：Ax = b（A 来自离散卷积）
n = 30
h = 1.0 / n
A = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        A[i, j] = h * np.exp(-((i - j) * h) ** 2 / 0.05)

x_true = np.where((np.arange(n) / n > 0.3) & (np.arange(n) / n < 0.7), 1.0, 0.0)
b_noisy = A @ x_true + rng.normal(0, 0.01, n)

print("Tikhonov 正则化（不同 λ）:")
for lam in [0., 1e-3, 1e-1]:
    x_reg = linalg.solve(A.T @ A + lam * np.eye(n), A.T @ b_noisy)
    err = np.linalg.norm(x_reg - x_true) / np.linalg.norm(x_true)
    print(f"  λ={lam:.0e}  相对误差={err:.4f}")

# 12.3 蒙特卡洛 UQ
# ODE: dy/dt = -k*y, k ~ Uniform(0.5, 1.5), y(0)=1
# 估计 y(1) 的均值与方差

N = 5000
k_samples = rng.uniform(0.5, 1.5, N)
y_at_1 = np.exp(-k_samples * 1.0)

print(f"\\n蒙特卡洛（N={N}）y(1) 统计:")
print(f"  均值:   {y_at_1.mean():.5f}")
print(f"  标准差: {y_at_1.std():.5f}")
# 解析：E[e^{-k}] = (e^{-0.5} - e^{-1.5}) / 1
analytic_mean = (np.exp(-0.5) - np.exp(-1.5)) / 1.0
print(f"  解析均值: {analytic_mean:.5f}")
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 13 周
  // ──────────────────────────────────────────────────────────
  {
    week: 13,
    title: '不确定性量化与可微编程',
    module: '可微编程',
    lessons: [
      { id: '13.1', title: '不确定性量化（二）：Chaospy / UQpy 初识', level: 'H', hasAI: false },
      { id: '13.2', title: '可微编程（一）：自动微分与 JAX 入门', level: 'H', hasAI: false },
      { id: '13.3', title: '可微编程（二）：ODE 参数辨识', level: 'H', hasAI: false },
    ],
    contextTags: ['week13', 'uq', 'automatic-differentiation', 'jax', 'ode-parameter-identification'],
    demoCode: `# 第 13 周 · 自动微分与 ODE 参数辨识
# 注意：需要安装 jax。若未安装，可先安装：pip install jax

try:
    import jax
    import jax.numpy as jnp
    HAS_JAX = True
except ImportError:
    HAS_JAX = False
    print("JAX 未安装，跳过 JAX 演示")

import numpy as np

# 数值微分对比（无需 JAX）
def f(x): return x**3 - 2*x + 1.0

def numerical_grad(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)

x0 = 1.5
exact_grad = 3 * x0**2 - 2  # 解析导数
num_grad   = numerical_grad(f, x0)
print(f"数值微分:  {num_grad:.8f}")
print(f"解析导数:  {exact_grad:.8f}")
print(f"误差:      {abs(num_grad - exact_grad):.2e}")

if HAS_JAX:
    # JAX 自动微分
    grad_f = jax.grad(f)
    jax_grad = float(grad_f(x0))
    print(f"JAX grad:  {jax_grad:.8f}")
    print(f"JAX 误差:  {abs(jax_grad - exact_grad):.2e}")

    # 13.3 ODE 参数辨识：y'=-θy, 拟合 θ
    # 生成带噪观测
    theta_true = 0.7
    t_obs = np.array([0., 0.5, 1.0, 1.5, 2.0])
    rng = np.random.default_rng(3)
    y_obs = jnp.array(np.exp(-theta_true * t_obs)
                       + rng.normal(0, 0.02, len(t_obs)))

    def loss(theta):
        y_pred = jnp.exp(-theta * jnp.array(t_obs))
        return jnp.sum((y_pred - y_obs)**2)

    theta = jnp.array(1.0)
    grad_loss = jax.grad(loss)
    lr = 0.5
    for step in range(200):
        g = grad_loss(theta)
        theta = theta - lr * g
    print(f"\\n辨识 θ = {float(theta):.4f}（真值 {theta_true}）")
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 14 周
  // ──────────────────────────────────────────────────────────
  {
    week: 14,
    title: '科学机器学习（整周）',
    module: '科学 ML',
    lessons: [
      { id: '14.1', title: '科学 ML（一）：PINN 与物理信息神经网络', level: 'H', hasAI: false },
      { id: '14.2', title: '科学 ML（二）：PINN 实践、验证与调参', level: 'C', hasAI: false },
      { id: '14.3', title: '科学 ML（三）：延伸与文献', level: 'H', hasAI: false },
    ],
    contextTags: ['week14', 'pinn', 'scientific-ml', 'neural-ode', 'fourier-neural-operator'],
    demoCode: `# 第 14 周 · 物理信息神经网络（PINN）
# 求解一维 ODE：u'' + u = 0，u(0)=0, u(π)=0（精确解 u=sin(x)）

import numpy as np

# 使用纯 NumPy 模拟简单的 PINN（不依赖深度学习框架）
# 真实 PINN 需要 JAX 或 PyTorch 支持自动微分

def pinn_demo_numpy():
    """
    演示 PINN 损失函数的构成：
      L_total = L_pde + L_bc
    其中 L_pde = |u'' + u|² 在配点上的均值
          L_bc  = |u(0)|² + |u(π)|²
    """
    # 解析解 u(x) = sin(x)
    x_colloc = np.linspace(0.01, np.pi - 0.01, 20)  # PDE 配点
    u_exact   = np.sin(x_colloc)
    u_xx_exact = -np.sin(x_colloc)  # u'' = -sin(x)

    # PDE 残差（使用精确解应为 0）
    residual = u_xx_exact + u_exact
    L_pde = np.mean(residual**2)
    L_bc  = np.sin(0)**2 + np.sin(np.pi)**2
    print(f"PDE 残差损失:  {L_pde:.2e}")
    print(f"边界损失:      {L_bc:.2e}")
    print(f"总损失:        {L_pde + L_bc:.2e}")
    print("（使用精确解时损失应接近 0）")

pinn_demo_numpy()

# 提示：如已安装 JAX，可用 jax.grad 实现全自动微分的 PINN
# 核心思路：
#   1. 定义神经网络 u_theta(x) 作为 PDE 解的近似
#   2. 计算 PDE 残差 R(x) = u_theta''(x) + u_theta(x)
#   3. 最小化 loss = mean(R^2) + lambda * (边界条件项)
print("\\n若安装了 JAX/PyTorch，可在此实现完整 PINN 训练循环。")
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 15 周
  // ──────────────────────────────────────────────────────────
  {
    week: 15,
    title: 'Python 与 C 及其他语言的交互',
    module: '高性能',
    lessons: [
      { id: '15.1', title: '性能分析、Cython/Numba/ctypes', level: 'H', hasAI: false },
      { id: '15.2', title: 'C/C++ 扩展实战', level: 'H', hasAI: false },
      { id: '15.3', title: '其他语言与 GPU：Fortran/Julia/CUDA/CuPy', level: 'H', hasAI: false },
    ],
    contextTags: ['week15', 'performance', 'numba', 'cython', 'ctypes', 'cuda', 'cupy'],
    demoCode: `# 第 15 周 · 性能分析与加速
import numpy as np
import time

# 15.1 比较：循环 vs 向量化 vs Numba
def loop_pairwise(X):
    """朴素循环实现逐对距离（慢）"""
    n = X.shape[0]
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            diff = X[i] - X[j]
            D[i, j] = np.sqrt(np.dot(diff, diff))
    return D

def vectorized_pairwise(X):
    """向量化实现（利用广播）"""
    diff = X[:, None, :] - X[None, :, :]   # (n, n, d)
    return np.sqrt((diff**2).sum(axis=-1))

# SciPy 最快
from scipy.spatial.distance import cdist

n = 100
rng = np.random.default_rng(42)
X = rng.standard_normal((n, 3))

t0 = time.perf_counter(); D1 = loop_pairwise(X);       t1 = time.perf_counter()
t2 = time.perf_counter(); D2 = vectorized_pairwise(X); t3 = time.perf_counter()
t4 = time.perf_counter(); D3 = cdist(X, X);            t5 = time.perf_counter()

print(f"循环:        {(t1-t0)*1000:7.2f} ms")
print(f"向量化:      {(t3-t2)*1000:7.2f} ms  ({(t1-t0)/(t3-t2):.0f}× 加速)")
print(f"scipy:       {(t5-t4)*1000:7.2f} ms  ({(t1-t0)/(t5-t4):.0f}× 加速)")
print("结果一致:", np.allclose(D1, D2) and np.allclose(D1, D3))

# 15.1 性能分析提示（需在 Jupyter 中使用）
# %timeit loop_pairwise(X)
# %timeit vectorized_pairwise(X)
# 或用 cProfile：
# import cProfile; cProfile.run('loop_pairwise(X)')
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 16 周
  // ──────────────────────────────────────────────────────────
  {
    week: 16,
    title: '科学研究延伸阅读',
    module: '文献导读',
    lessons: [
      { id: '16.1', title: '按模块选读：反问题、ODE、PDE、SciML', level: 'H', hasAI: false },
      { id: '16.2', title: '文献与课内对应：报告或讨论', level: 'C', hasAI: false },
      { id: '16.3', title: '延伸阅读清单与考核说明', level: 'B', hasAI: false },
    ],
    contextTags: ['week16', 'research-literature', 'inverse-problems', 'scientific-ml', 'review'],
    demoCode: `# 第 16 周 · 文献回顾：课内知识与科研的对应
# 以下代码综合了课程中各关键模块的核心操作

import numpy as np
from scipy import linalg, integrate, optimize, interpolate

print("=" * 55)
print("课程核心模块回顾")
print("=" * 55)

# 1. 线性代数 + Tikhonov 正则化（第 5/12 周）
n = 20
A = np.random.default_rng(1).standard_normal((n, n))
A = A.T @ A + np.eye(n)  # 正定
b = np.ones(n)
for lam in [0., 0.1, 1.0]:
    x = linalg.solve(A + lam * np.eye(n), b)
    print(f"正则化 λ={lam:.1f}  ‖x‖={np.linalg.norm(x):.3f}")

# 2. ODE 求解（第 7/8 周）
sol = integrate.solve_ivp(lambda t, y: [-y[0] + np.sin(t)], [0, 10], [0.],
                           t_eval=np.linspace(0, 10, 5), rtol=1e-8)
print("\\nODE 末态:", sol.y[0, -1:.4f])" if False else
      f"\\nODE 末态: {sol.y[0, -1]:.4f}")

# 3. 优化（第 8/9 周）
res = optimize.minimize(lambda x: x[0]**4 + (x[1]-2)**2, [0., 0.], method='BFGS')
print(f"优化极值: {res.x.round(4)},  f={res.fun:.4f}")

# 4. 插值（第 5 周）
x = np.array([0., 1., 2., 3., 4.])
y = np.sin(x)
cs = interpolate.CubicSpline(x, y)
err = abs(cs(2.5) - np.sin(2.5))
print(f"样条插值误差 at x=2.5: {err:.2e}")

# 5. 蒙特卡洛（第 12 周）
k = np.random.default_rng(42).uniform(0.5, 1.5, 10000)
print(f"MC E[e^(-k)]: {np.exp(-k).mean():.5f}")
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 17 周
  // ──────────────────────────────────────────────────────────
  {
    week: 17,
    title: '大规模与并行计算',
    module: '并行 + 工程化',
    lessons: [
      { id: '17.1', title: '多进程与并行思想', level: 'H', hasAI: false },
      { id: '17.2', title: 'Dask 与「比内存大」的计算', level: 'H', hasAI: false },
      { id: '17.3', title: '科学计算工程化与设计模式', level: 'H', hasAI: false },
    ],
    contextTags: ['week17', 'parallel', 'multiprocessing', 'dask', 'software-engineering'],
    demoCode: `# 第 17 周 · 并行计算与工程化
import numpy as np
import time
from concurrent.futures import ProcessPoolExecutor

# 17.1 多进程并行：参数扫描
def run_ode_for_k(k: float) -> float:
    """对参数 k 求解 y'=-ky 在 t=1 的值"""
    # 使用 Euler 法（避免在子进程中导入 scipy）
    dt, t, y = 0.001, 0.0, 1.0
    while t < 1.0:
        y += dt * (-k * y)
        t += dt
    return y

k_values = np.linspace(0.5, 2.0, 20).tolist()

# 串行
t0 = time.perf_counter()
serial_results = [run_ode_for_k(k) for k in k_values]
t1 = time.perf_counter()

# 并行
t2 = time.perf_counter()
with ProcessPoolExecutor(max_workers=4) as pool:
    parallel_results = list(pool.map(run_ode_for_k, k_values))
t3 = time.perf_counter()

print(f"串行:   {(t1-t0)*1000:.1f} ms")
print(f"并行:   {(t3-t2)*1000:.1f} ms  (4 进程)")
print(f"结果一致: {np.allclose(serial_results, parallel_results)}")

# 17.3 工程化：流水线设计模式
class LinearSolver:
    """策略模式：可互换的线性求解器"""
    def __init__(self, method: str = "direct"):
        self.method = method

    def solve(self, A: np.ndarray, b: np.ndarray) -> np.ndarray:
        from scipy import linalg
        if self.method == "direct":
            return linalg.solve(A, b)
        elif self.method == "lstsq":
            return linalg.lstsq(A, b)[0]
        raise ValueError(f"未知方法: {self.method}")

A = np.array([[2., 1.], [1., 3.]])
b = np.array([5., 10.])
for method in ["direct", "lstsq"]:
    sol = LinearSolver(method).solve(A, b)
    print(f"{method:8s} 解: {sol.round(4)}")
`,
  },

  // ──────────────────────────────────────────────────────────
  // 第 18 周
  // ──────────────────────────────────────────────────────────
  {
    week: 18,
    title: '项目提交与展示 / 轻松话题',
    module: '项目',
    lessons: [
      { id: '18.1', title: '项目提交与展示（一）', level: 'C', hasAI: false },
      { id: '18.2', title: '项目展示（二）或轻松话题（一）', level: 'C', hasAI: false },
      { id: '18.3', title: '轻松话题（二）或总结', level: 'B', hasAI: false },
    ],
    contextTags: ['week18', 'project', 'presentation', 'review'],
    demoCode: `# 第 18 周 · 期末项目综合示例
# 本示例综合了课程全程学到的工具与方法

import numpy as np
from scipy import linalg, integrate, optimize
import time

print("=" * 55)
print("Python 科学计算课程 · 综合演示")
print("=" * 55)

# 1. 数值线性代数
n = 100
rng = np.random.default_rng(2026)
A = rng.standard_normal((n, n))
A = A @ A.T + n * np.eye(n)   # 正定矩阵
b = rng.standard_normal(n)
x = linalg.solve(A, b)
print(f"1. 线性系统残差: {np.linalg.norm(A @ x - b):.2e}")

# 2. 非线性 ODE + 参数扫描
def sir_model(t, y, beta, gamma):
    S, I, R = y
    N = S + I + R
    dS = -beta * S * I / N
    dI =  beta * S * I / N - gamma * I
    dR =  gamma * I
    return [dS, dI, dR]

peak_infected = []
for beta in [0.3, 0.5, 0.8]:
    sol = integrate.solve_ivp(
        sir_model, [0, 160], [990, 10, 0],
        args=(beta, 0.1), t_eval=np.linspace(0, 160, 500)
    )
    peak_infected.append(sol.y[1].max())
    print(f"2. β={beta}  峰值感染: {peak_infected[-1]:.0f}")

# 3. 优化问题
res = optimize.minimize(
    lambda p: np.sum((p[0]*np.exp(-p[1]*np.linspace(0,2,20))
                      - np.exp(-0.6*np.linspace(0,2,20)))**2),
    [1.0, 1.0], method='BFGS'
)
print(f"3. 拟合参数: a={res.x[0]:.4f} (真值1.0), b={res.x[1]:.4f} (真值0.6)")

print("\\n课程结束！感谢同学们的参与。")
`,
  },
]

export default WEEKS

export function getWeek(n: number): WeekData | undefined {
  return WEEKS.find((w) => w.week === n)
}
