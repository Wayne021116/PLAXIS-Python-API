from plxscripting.easy import *

passwd="your password"
save_path = r"D:\BaiduNetdiskDownload\PLAXIS 2D 2024(64bit)\file\dynamic.p2dx"
# ============================================================
# 1. 连接 PLAXIS 服务器 | Connect to PLAXIS Server
# ============================================================
s_i, g_i = new_server("localhost", 10000, password=passwd)

# ============================================================
# 2. 新建项目 | Create New Project
# ============================================================
s_i.new()       # 新建项目 | Create new project
     
# s_i.open(r"D:\project\slope analysis.p2dx")   # 打开已有项目 | Open existing project

g_i.Project.Title = "Slope Stability Analysis"  # 边坡稳定分析
g_i.Project.Comments = "Mohr-Coulomb Model with Groundwater"  # Mohr-Coulomb 模型，含地下水位

# 设置单位 | Set units (kN, m, day)
g_i.Project.UnitForce = "kN"
g_i.Project.UnitLength = "m"
g_i.Project.UnitTime = "day"

print("✅ 项目建立完成 | Project created")

# 进入建模模式 | Enter modeling mode
g_i.gotostructures()

# 定义土体多边形 | Define soil polygon
# 坐标点：左下→右下→右上→坡顶→坡脚→左上
# Coordinates: bottom-left → bottom-right → top-right → slope-top → slope-toe → top-left
# 坡脚 slope toe at x=10, 坡顶 slope top at x=10+5*1.5=17.5
soil = g_i.polygon(
    (0,  0),    # 左下 | bottom-left
    (30, 0),    # 右下 | bottom-right
    (30, 15),   # 右上 | top-right
    (17.5, 15), # 坡顶 | slope top
    (10, 10),   # 坡脚 | slope toe
    (0, 10)     # 左上 | top-left
)
soil = soil[0]
print("✅ 几何建立完成 | Geometry created")

# ============================================================
# 3. 定义材料 | Define Material (Mohr-Coulomb)
# ============================================================
soil_mat = g_i.soilmat()

soil_mat.setproperties(
    "Identification",  "Clay_MC",
    "SoilModel",       2,         # 2 = Mohr-Coulomb
    "DrainageType",    0,         # 0 = Drained | 排水
    "gammaUnsat",      18.0,      # 非饱和重度 | Unsaturated unit weight (kN/m³)
    "gammaSat",        20.0,      # 饱和重度 | Saturated unit weight (kN/m³)
    "Eref",            20000.0,   # 弹性模量 | Young's modulus (kPa)
    "nu",              0.3,       # 泊松比 | Poisson's ratio
    "cref",            10.0,      # 黏聚力 | Cohesion (kPa)
    "phi",             25.0,      # 内摩擦角 | Friction angle (°)
    "psi",             0.0,       # 剪胀角 | Dilatancy angle (°)
)

# 赋材料给土体 | Assign material to soil
g_i.gotosoil()
for vol in g_i.Soils:
    vol.Material = soil_mat

print("✅ 材料定义完成 | Material defined")

# ============================================================
# 4. 设置地下水位 | Set Groundwater Level
# ============================================================
g_i.gotowater()
g_i.waterlevel(
    (0,  8),   # 左侧水位 | Left water level
    (30, 8)    # 右侧水位 | Right water level
)
print("✅ 地下水位设置完成 | Groundwater level set")

# ============================================================
# 5. 网格划分 | Mesh Generation
# ============================================================
g_i.gotomesh()
g_i.mesh(0.06)  # 0.06 = 中等精细度 | Medium mesh coarseness
print("✅ 网格划分完成 | Mesh generated")

# ============================================================
# 6. 计算阶段设置 | Calculation Phase Setup
# ============================================================
g_i.gotostages()

# 阶段1：初始地应力 | Phase 1: Initial Stress (K0 procedure)
phase0 = g_i.InitialPhase
phase0.Identification = "Initial Stress"  # 初始地应力
g_i.activate(soil, phase0)

# 阶段2：安全系数计算 | Phase 2: Safety Analysis (Phi-c Reduction)
phase1 = g_i.phase(phase0)
phase1.Identification = "Safety Analysis"  # 边坡安全系数
phase1.DeformCalcType = 7               # 计算类型 | Calculation Type
                                        # 4 = Plastic          | 塑性计算
                                        # 5 = Consolidation    | 固结计算
                                        # 6 = Fully Coupled    | 完全耦合流固变形
                                        # 7 = Safety           | 安全系数（强度折减）✅
                                        # 8 = Dynamics with Consolidation | 动力+固结
phase1.Deform.LoadingType = "incrementalmultipliers"  # 增量模式 | Incremental multipliers
phase1.Deform.UseDefaultIterationParams = False
phase1.Deform.MaxSteps = 100

# 设置强度折减 | Apply strength reduction
g_i.set(g_i.Soils[0].ApplyStrengthReduction, phase1, True)
print("✅ 计算阶段设置完成 | Calculation phases set")

# ============================================================
# 7. 运行计算 | Run Calculation
# ============================================================
print("⏳ 开始计算，请稍候... | Calculating, please wait...")
g_i.calculate(phase0, phase1)
print("✅ 计算完成 | Calculation complete")

# ============================================================
# 8. 提取结果 | Extract Results
# ============================================================
# 保存项目 | Save project
g_i.save(save_path)
print("✅ 项目已保存 | Project saved")

# 从 Input 服务器获取安全系数 | Get FOS from Input server
phase_result = g_i.Phases[-1]
print("计算结果状态 | Calculation status:", phase_result.CalculationResult.value)
print(f"🔍 安全系数 | Factor of Safety (SumMsf) = {phase_result.Reached.SumMsf.value:.3f}")

# 连接 Output 服务器 | Connect to Output server
s_o, g_o = new_server('localhost', 10001, password=passwd, timeout=3600, request_timeout=3600)
print("✅ Output 连接成功 | Output server connected")

# 从 Output 服务器获取阶段 | Get phase from Output server
phase_o = g_o.Phases[-1]
print("阶段 | Phase:", phase_o.Identification.value)
print(f"🔍 安全系数 | Factor of Safety (SumMsf) = {phase_o.Reached.SumMsf.value:.3f}")

# ============================================================
# 注意：位移结果说明 | Note: Displacement Results Explanation
# ============================================================
# 在增量模式的 Safety 分析中，PLAXIS 会持续折减土体强度直到边坡完全破坏。
# 破坏发生时，位移会发散到极大的数值（如数千米），这是正常现象。
#
# In Safety analysis with Incremental Multipliers mode,
# PLAXIS continuously reduces soil strength until the slope fails.
# When failure occurs, displacements diverge to extremely large values.
# This is expected behavior and does NOT represent real physical displacements.
#
# ✅ 真正有意义的结果是安全系数 SumMsf
# ✅ The meaningful result is the Factor of Safety (SumMsf)
# ============================================================

# 获取位移结果 | Get displacement results
uy_results = g_o.getresults(phase_o, g_o.ResultTypes.Soil.Uy, "node")
uy_values = list(uy_results)
print(f"🔍 最大竖向位移 | Max vertical displacement Uy_max = {max(uy_values):.4f} m")
print(f"🔍 最小竖向位移 | Min vertical displacement Uy_min = {min(uy_values):.4f} m")

ux_results = g_o.getresults(phase_o, g_o.ResultTypes.Soil.Ux, "node")
ux_values = list(ux_results)
print(f"🔍 最大水平位移 | Max horizontal displacement Ux_max = {max(ux_values):.4f} m")

utot_results = g_o.getresults(phase_o, g_o.ResultTypes.Soil.Utot, "node")
utot_values = list(utot_results)
print(f"🔍 最大总位移 | Max total displacement Utot_max = {max(utot_values):.4f} m")

print("\n🎉 边坡稳定分析完成 | Slope Stability Analysis Complete!")