# Python 科学计算在科学研究中的应用 · 文献与课程对应

本表列出**近年文献**（以 2023–2025 为主），其研究步骤中明确用到本课所授内容（NumPy/SciPy、线性代数、ODE、优化、PDE、反问题、UQ、可微编程、PINN 等），便于在相应章节「顺带涉及」或在**第 16–18 周**集中做「科学研究应用」导读。

---

## 一、按课程模块对应的文献

### 环境与工具链、可复现性（第 1 周）

| 文献 | 与本课关联 | 简要说明 |
|------|------------|----------|
| **SciPy spatial.transform 可微扩展** (arXiv:2511.18157, 2025) | Jupyter/NumPy/SciPy 生态、可复现 | SciPy 的 3D 刚体变换支持 JAX/PyTorch/CuPy 的可微与 GPU，体现「科学计算栈」的现代演进。 |
| **RamanSPy** (OpenReview 2024) | Python 科学计算栈、数据与 AI | 拉曼光谱分析库，基于 NumPy/SciPy 标准化流程并衔接 ML，可作「从数据到可复现分析」的案例。 |

### NumPy、线性代数、矩阵分解（第 2–4 周）

| 文献 | 与本课关联 | 简要说明 |
|------|------------|----------|
| **ZERNIPAX** (ScienceDirect 2025, S0096300325002607) | NumPy/JAX、线性代数、多项式与矩阵运算 | 光学 Zernike 多项式计算，基于 NumPy/JAX，涉及多项式与线性代数运算，用于光学/天体/等离子体仿真。 |
| **PyDMD** (arXiv:2402.07463, 2024; SoftwareX/JOSS 类) | 特征值、SVD、线性代数、动力系统 | 动态模态分解 (DMD)，用 NumPy/SciPy 做特征值/SVD、提取时空模态，应用于流体、流行病、神经、等离子体等。 |
| **SPARTA** (CERN/粒子加速器, 2024) | NumPy、SciPy、线性代数与信号 | 用 NumPy/SciPy/scikit-rf 做共振分析与品质因子估计，替代人工、强调可复现流程。 |

### 最小二乘、拟合、优化（第 4–6、8–9 周）

| 文献 | 与本课关联 | 简要说明 |
|------|------------|----------|
| **curve_fit / 参数估计** | scipy.optimize.curve_fit、最小二乘、初值 | 药理剂量-反应 (Hill)、LED 光谱 (Gaussian)、势能曲线拟合等，均为「模型 + curve_fit + 误差」的典型科研用法。 |
| **EV-PINN** (arXiv:2411.14691, 2024) | 优化、物理参数辨识 | 电动汽车动力学 PINN，从数据学习电机效率、阻力等参数，与「可微 + 优化」对应。 |

### 常微分方程、solve_ivp、动力系统（第 7–8 周）

| 文献 | 与本课关联 | 简要说明 |
|------|------------|----------|
| **Prelude to chaos / solve_ivp** (Medium 等, 2024) | scipy.integrate.solve_ivp、非线性 ODE、混沌 | 用 solve_ivp 解非线性 ODE、观察混沌，与课程「洛伦兹 + 相图」直接对应。 |
| **JAX 可微 ODE 参数估计** (arXiv:2509.07283, 2025) | solve_ivp 思想、可微、优化 | 将问题转为 JAX 可微 ODE 校准流程：全局探索 + 梯度细化，用于电池、燃烧、生物等机理模型。 |
| **Diffrax / Neural ODE** (JAX 生态) | ODE 初值问题、自动微分 | 可微 ODE 求解器，与「ODE 参数辨识」和「科学 ML」衔接。 |

### 偏微分方程、热方程、扩散（第 11–12 周）

| 文献 | 与本课关联 | 简要说明 |
|------|------------|----------|
| **2D 热方程数值解** (IJSR 等, 2024) | 有限差分、显式/隐式、NumPy/SciPy/Matplotlib | 二维热方程实现与稳定性分析，与课程「一维热方程 → 二维泊松」一致。 |
| **PINN 热-力学** (arXiv:2412.18786, 2024) | 热传导、应力、PDE + 神经网络 | 激光金属沉积中的温度与热应力 PINN，PDE 残差 + 数据，可与「PDE 离散」对比。 |
| **热腔流动 PINN** (Nature Scientific Reports 2024) | 自然对流、2D/3D、PDE 验证 | 2D/3D 自然对流正向模拟，与已有解对比，体现「PDE + 数值验证」。 |

### 反问题、正则化（第 12 周）

| 文献 | 与本课关联 | 简要说明 |
|------|------------|----------|
| **TRIPs-Py** (arXiv:2402.17603; Numer. Algor. 2024) | Tikhonov、TSVD、迭代正则化、图像/CT | Python 反问题正则化包：Tikhonov、截断 SVD、Krylov、ℓp-ℓq；含去模糊、CT、动态 CT 等算例，与课程「岭回归/正则化」一致。 |
| **PyLops** (TV 正则化等) | 线性算子、TV、反问题 | 总变分等正则化、Split Bregman，可与 TRIPs-Py 互补介绍。 |

### 不确定性量化（第 12–13 周）

| 文献 | 与本课关联 | 简要说明 |
|------|------------|----------|
| **UQpy v4.1/v4.2** (SoftwareX 2023; 文档 2024) | 蒙特卡洛、抽样、UQ 工作流 | 通用 UQ 工具箱，模块化、与 NumPy/SciPy 兼容，适合讲完 Monte Carlo 后介绍。 |
| **Chaospy** (v4.3, 2024) | 多项式混沌、抽样、quadrature | PCE 与高级蒙特卡洛，与课程「Chaospy 初识」对应。 |

### 可微编程、JAX、科学机器学习（第 13–14 周）

| 文献 | 与本课关联 | 简要说明 |
|------|------------|----------|
| **JAX ODE 校准** (arXiv:2509.07283, 2025) | JAX、可微 ODE、参数估计、优化 | 从问题描述到可微 ODE 校准流水线，两阶段优化，对应「可微编程 + ODE 参数辨识」。 |
| **EV-PINN** (arXiv:2411.14691) | PINN、ODE/物理参数、优化 | 电动汽车动力学的 PINN，仅用速度-时间数据估计物理参数。 |
| **DeepF-fNet** (arXiv:2412.21132, 2024) | PINN、振动、结构优化 | 振动隔离优化中的 PINN+DeepONet，可与传统优化（如遗传算法）对比。 |
| **PINN 空气动力学** (arXiv:2403.17470 等) | PDE、代理模型、数据同化 | 参数化代理、多物理耦合、湍流推断，体现「PDE + 数据」的科研用法。 |

---

## 二、按周次「可涉及」建议（与 schedule-18weeks 对应）

- **第 1 周**：可提 SciPy 可微扩展、RamanSPy，说明「科学计算栈」与可复现性。
- **第 2–3 周**：ZERNIPAX（NumPy/数组）、PyDMD（特征值/SVD）、SPARTA（线性代数与信号）。
- **第 4–5 周**：最小二乘/拟合 → TRIPs-Py 的 Tikhonov、curve_fit 在药理/物理中的应用。
- **第 6 周**：数值积分/拟合 → 强调 curve_fit 在实验数据建模中的普遍性。
- **第 7–8 周**：ODE/动力系统 → solve_ivp 与混沌、JAX ODE 校准、EV-PINN 参数辨识。
- **第 9 周**：优化 → EV-PINN、DeepF-fNet 中的优化目标。
- **第 11–12 周**：PDE → 2D 热方程文献、PINN 热-力学/热腔流动；反问题 → TRIPs-Py、PyLops。
- **第 12–13 周**：UQ → UQpy、Chaospy 论文与文档。
- **第 13–14 周**：可微与科学 ML → JAX ODE 校准、PINN 多篇（EV、热、振动、气动）。
- **第 16–18 周**：见下节「科学研究应用」集中使用方式。

---

## 三、第 16–18 周「科学研究应用」集中使用方式

- **第 16 周**  
  - **16.1**：在「挑战项目展示」前或后，用 **20–25 分钟**做「科学研究中的 Python 科学计算」导读：从 `literature.md` 中选 2–3 条线（例如：① 反问题 TRIPs-Py + 课程正则化；② ODE 参数估计 JAX/EV-PINN + solve_ivp/可微；③ PDE/PINN 热方程 + 课程 PDE 与科学 ML），每条用 1 篇文献说明「问题 → 用的课内知识 → 代码/库」；可发 `literature.md` 或精简版阅读清单。  
  - **16.2–16.3**：考核说明与复习时，可提醒「延伸阅读见 literature.md」，或布置「选读 1 篇并写半页与课程内容的对应」。  
- **第 17–18 周**  
  - 考核周不占正课；可将「延伸阅读清单」（上表 + 链接）作为课后材料发给学生，供有兴趣者按模块选读。

---

## 四、文献链接与引用格式（便于复制）

| 简称 | 链接或标识 | 引用概要 |
|------|------------|----------|
| SciPy spatial.transform | https://arxiv.org/abs/2511.18157 | arXiv:2511.18157 (2025) |
| RamanSPy | OpenReview 2024 (RamanSPy) | 拉曼光谱 + Python/NumPy/AI |
| ZERNIPAX | ScienceDirect S0096300325002607 (2025) | Zernike 多项式 NumPy/JAX |
| PyDMD | https://arxiv.org/abs/2402.07463 | arXiv:2402.07463 (2024) |
| TRIPs-Py | https://arxiv.org/abs/2402.17603 | Pasha et al., Numer. Algor. (2024); arXiv:2402.17603 |
| UQpy | SoftwareX (2023); https://uqpyproject.readthedocs.io | Tsapetis et al., UQpy v4.1 |
| JAX ODE 校准 | https://arxiv.org/abs/2509.07283 | arXiv:2509.07283 (2025) |
| EV-PINN | https://arxiv.org/abs/2411.14691 | arXiv:2411.14691 (2024) |
| PINN 热-力学 | https://arxiv.org/abs/2412.18786 | arXiv:2412.18786 (2024) |
| DeepF-fNet | https://arxiv.org/abs/2412.21132 | arXiv:2412.21132 (2024) |
| 2D 热方程 | IJSR 等 (2024), 2D heat equation Python | 有限差分、稳定性 |
| 热腔 PINN | Nature Sci. Rep. 2024, thermal cavity PINN | 自然对流 2D/3D |

以上链接与刊名以授课时再次核对为准；可要求学生引用时使用正式出版信息。
