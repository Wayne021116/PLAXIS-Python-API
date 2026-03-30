# 纯 Python 计算 Terzaghi 公式
import math
# ============================================================
# Terzaghi 地基承载力计算
# Strip Footing Bearing Capacity (Terzaghi Formula)
# ============================================================

# 输入参数 | Input parameters
B = 3.0      # 基础宽度 | Foundation width (m)
D = 1.5      # 埋置深度 | Embedment depth (m)
gamma = 18.0 # 土重度 | Unit weight (kN/m³)
phi = 30.0   # 内摩擦角 | Friction angle (°)
c = 0.0      # 黏聚力 | Cohesion (kPa)
Fs = 3.0     # 安全系数 | Factor of safety

phi_r = math.radians(phi)
Nq = (math.e ** (math.pi * math.tan(phi_r))) * \
     (math.tan(math.radians(45 + phi/2))) ** 2
Nc = (Nq - 1) / math.tan(phi_r) if phi > 0 else 5.14
Ngamma = 2 * (Nq + 1) * math.tan(phi_r)

print("=" * 50)
print("Terzaghi 承载力系数 | Bearing Capacity Factors")
print("=" * 50)
print(f"Nc = {Nc:.3f}")
print(f"Nq = {Nq:.3f}")
print(f"Nγ = {Ngamma:.3f}")

q = gamma * D
qult = c * Nc + q * Nq + 0.5 * gamma * B * Ngamma

print("\n" + "=" * 50)
print("计算结果 | Results")
print("=" * 50)
print(f"覆土压力 q = γ×D = {q:.1f} kPa")
print(f"极限承载力 qult = {qult:.2f} kPa")
print(f"容许承载力 qall = qult/Fs = {qult/Fs:.2f} kPa")
print("=" * 50)

# ============================================================
# PLAXIS 相关
from plxscripting.easy import *

passwd = "your password"
save_path = r"D:\BaiduNetdiskDownload\PLAXIS 2D 2024(64bit)\file\dynamic.p2dx"
s_i, g_i = new_server("localhost", 10000, password=passwd,
                       timeout=3600, request_timeout=3600)

# ============================================================
# 1. 新建项目 | Create New Project
# ============================================================
s_i.new()
g_i.Project.Title = "Strip Footing Bearing Capacity"
g_i.Project.UnitForce = "kN"
g_i.Project.UnitLength = "m"
g_i.Project.UnitTime = "day"

# 模型范围 | Model boundaries
# 取对称一半，x=0~15m，y=-10~0m
g_i.SoilContour.initializerectangular(0, -10, 15, 0)
print("✅ 项目建立完成 | Project created")

# ============================================================
# 2. 定义土层 | Define Soil Layers
# ============================================================
g_i.borehole(0)
g_i.soillayer(0)
g_i.Soillayer_1.Zones[0].Top = 0
g_i.Soillayer_1.Zones[0].Bottom = -10
g_i.Borehole_1.Head = -10  # 水位在模型以下 | GWL below model
print("✅ 土层定义完成 | Soil layers defined")

# ============================================================
# 3. 定义材料 | Define Materials
# ============================================================

# 地基土材料（Mohr-Coulomb）| Soil material
soil_mat = g_i.soilmat()
soil_mat.setproperties("SoilModel", 2)
soil_mat.setproperties(
    "Identification",        "Sand",
    "DrainageType",          0,
    "gammaUnsat",            18.0,
    "gammaSat",              20.0,
    "Eref",                  30000.0,
    "nu",                    0.3,
    "cRef",                  0.0,
    "phi",                   30.0,
    "psi",                   0.0,
    "PermHorizontalPrimary", 1.0,
    "PermVertical",          1.0,
)
soil_mat.InterfaceStrengthDetermination = "manual"
soil_mat.Rinter = 1.0  # 界面强度 = 土体强度 | Interface = soil strength

# 混凝土基础材料 | Concrete foundation material
concrete_mat = g_i.soilmat()
concrete_mat.setproperties("SoilModel", 2)
concrete_mat.setproperties(
    "Identification",        "Concrete",
    "DrainageType",          0,
    "gammaUnsat",            24.0,     # 混凝土重度 | Concrete unit weight
    "gammaSat",              24.0,
    "Eref",                  3.0e7,    # 混凝土弹性模量 | Concrete E (kPa)
    "nu",                    0.2,      # 泊松比 | Poisson's ratio
    "cRef",                  1000.0,   # 高黏聚力（刚性）| High cohesion (rigid)
    "phi",                   0.0,
    "psi",                   0.0,
    "PermHorizontalPrimary", 0.0,
    "PermVertical",          0.0,
)

print("✅ 材料定义完成 | Materials defined")

# ============================================================
# 4. 定义结构 | Define Structure
# ============================================================
g_i.gotostructures()

# 基础用土体多边形 | Foundation as soil polygon (per official tutorial)
# 取对称一半：宽 B/2=1.5m，厚 0.5m，埋深 D=1.5m
# 基础顶面 y=-1.0，底面 y=-1.5
foundation = g_i.polygon(
    (0,   -1.0),   # 左上
    (1.5, -1.0),   # 右上
    (1.5, -1.5),   # 右下
    (0,   -1.5),   # 左下
)[0]

# 荷载加在基础顶面 y=-1.0 | Load on top of foundation
g_i.lineload((0, -1.0), (1.5, -1.0))
load = 1000
g_i.LineLoad_1.qy_start = -load  # kN/m/m

print("✅ 结构定义完成 | Structure defined")

# ============================================================
# 5. 网格划分 | Mesh Generation
# ============================================================
g_i.gotomesh()
g_i.mesh(0.1)  # 较细网格 | Fine mesh for accuracy
print("✅ 网格划分完成 | Mesh generated")

# ============================================================
# 6. 计算阶段 | Calculation Phases
# ============================================================
g_i.gotostages()

# 初始阶段：纯土体自重平衡
phase0 = g_i.InitialPhase
phase0.Identification = "Initial Stress"
for s in g_i.Soils:
    g_i.set(s.Material, phase0, soil_mat)

# 阶段1：激活基础和界面 | Phase 1: Activate foundation and interface
phase1 = g_i.phase(phase0)
phase1.Identification = "Soil Equilibrium"
phase1.DeformCalcType = "plastic"

# 阶段2：施加荷载直到破坏 | Phase 2: Apply load to failure
phase2 = g_i.phase(phase1)
phase2.Identification = "Simultaneous Loading"
phase2.DeformCalcType = "plastic"
phase2.Deform.UseDefaultIterationParams = False
phase2.Deform.MaxSteps = 1000
phase2.Deform.ResetDisplacementsToZero = True
g_i.setcurrentphase(phase2)

foundation_soil = [s for s in g_i.Soils if "Polygon_1" in s.Parent.Name.value][0]
g_i.set(foundation_soil.Material, phase2, concrete_mat)
g_i.activate(foundation, phase2)
g_i.activate(g_i.Interfaces, phase2)
g_i.activate(g_i.LineLoads, phase2)

print("✅ 计算阶段设置完成 | Phases set")

# ============================================================
# 7. 运行计算 | Run Calculation
# ============================================================
print("⏳ 开始计算... | Calculating...")
g_i.calculate(phase0, phase1, phase2)
print("✅ 计算完成 | Complete")

# ============================================================
# 8. 保存 & 结果 | Save & Results
# ============================================================
g_i.save(save_path)
print("✅ 项目已保存 | Saved")

s_o, g_o = new_server('localhost', 10001, password=passwd,
                       timeout=3600, request_timeout=3600)
s_o.open(save_path)

phase_o = g_o.Phases[-1]
print(f"ΣMstage = {phase_o.Reached.SumMstage.value:.3f}")

# 土体位移 | Soil displacement
uy = g_o.getresults(phase_o, g_o.ResultTypes.Soil.Uy, "node")
uy_vals = list(uy)
print(f"🔍 最大沉降 = {min(uy_vals)*1000:.2f} mm")

# 极限承载力 | Ultimate bearing capacity
# ΣMstage < 1 说明土体破坏，极限承载力 = 荷载 × ΣMstage
msf = phase_o.Reached.SumMstage.value
plaxis_qult = load * msf
print(f"\n{'='*50}")
print(f"🔍 ΣMstage = {msf:.3f}")
print(f"🔍 PLAXIS 极限承载力 = {plaxis_qult:.2f} kPa")
print(f"🔍 Terzaghi 极限承载力 = {qult:.2f} kPa")
if msf < 0.99:
    print(f"🔍 误差 = {abs(plaxis_qult-qult)/qult*100:.1f}%")
else:
    print("⚠️ 土体未破坏，需加大荷载！")
print(f"{'='*50}")
print("\n🎉 地基承载力分析完成 | Bearing Capacity Analysis Complete!")