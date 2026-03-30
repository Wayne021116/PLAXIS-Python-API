from plxscripting.easy import *
import math

passwd = "your password"
save_path = r"D:\BaiduNetdiskDownload\PLAXIS 2D 2024(64bit)\file\dynamic.p2dx"

# ============================================================
# 1. 连接服务器 | Connect to Server
# ============================================================
s_i, g_i = new_server("localhost", 10000, password=passwd,
           timeout=3600, request_timeout=3600)

# ============================================================
# 2. 新建项目 | Create New Project
# ============================================================
s_i.new()
g_i.Project.Title = "Seismic Dynamic Response Analysis"
g_i.Project.UnitForce = "kN"
g_i.Project.UnitLength = "m"
g_i.Project.UnitTime = "s"

g_i.SoilContour.initializerectangular(0, -20, 30, 0)
print("✅ 项目建立完成 | Project created")

# ============================================================
# 3. 定义土层 | Define Soil Layers
# ============================================================
g_i.borehole(0)
g_i.soillayer(0)
g_i.Soillayer_1.Zones[0].Top  = 0
g_i.Soillayer_1.Zones[0].Bottom = -20
g_i.Borehole_1.Head = -5    # 水位 y = -5 m
print("✅ 土层定义完成 | Soil layers defined")

# ============================================================
# 4. 定义材料 | Define Materials
# ============================================================
soil_mat = g_i.soilmat()
soil_mat.setproperties("SoilModel", 2)  # Mohr-Coulomb
soil_mat.setproperties(
  "Identification",     "Sand",
  "DrainageType",      0,     # Drained
  "gammaUnsat",       18.0,
  "gammaSat",        20.0,
  "Eref",         50000.0,
  "nu",           0.3,
  "cRef",          5.0,
  "phi",          30.0,
  "psi",          0.0,
  "PermHorizontalPrimary", 1.0,
  "PermVertical",      1.0,
)

print("✅ 材料定义完成 | Materials defined")

# ============================================================
# 5. 定义结构 & 地震波 | Define Structure & Seismic Input
# ============================================================
g_i.gotostructures()

# 底部施加 X 方向线位移（水平地震输入）
# Apply horizontal line displacement at model base as seismic input
line_displ = g_i.linedispl((0, -20), (30, -20))[0]
g_i.linedispl((0, -20), (0, 0))      # 左侧
g_i.linedispl((30, -20), (30, 0))    # 右侧

# a = 0.1g，简谐位移振幅 u = a / (2πf)² 
a_input  = 0.1 * 9.81           # m/s² = 0.981 m/s²
freq = 2.0                  # 2 Hz
omega = 2 * math.pi * 2.0        # rad/s
u_amp = a_input / (omega ** 2)     # 位移幅值 ≈ 0.0062 m
print(f"  地震位移振幅 u = {u_amp*1000:.4f} mm")
print(f"  对应的加速度幅值 a = {a_input:.3f} m/s²")

# 关键：创建简谐荷载乘子并关联到线位移 x 分量
# Key fix: create harmonic multiplier and link it to ux of the line displacement
disp_mult = g_i.displmultiplier()
disp_mult.Signal = "Harmonic"
disp_mult.Amplitude = 1.0
disp_mult.Frequency = freq   # Hz
disp_mult.Phase   = 0.0   # °

# 将位移振幅写入线位移，并关联乘子
line_displ.ux_start = u_amp     # 基准位移幅值 (m)
line_displ.Multiplier_ux = disp_mult   # ✅ 关联乘子 — 这是原脚本缺失的关键行

print("✅ 地震波设置完成 | Seismic wave defined")

# ============================================================
# 6. 网格划分 | Mesh Generation
# ============================================================
g_i.gotosoil()
for vol in g_i.Soils:
  vol.Material = soil_mat

g_i.gotomesh()
g_i.mesh(0.06)
print("✅ 网格划分完成 | Mesh generated")

# ============================================================
# 7. 计算阶段 | Calculation Phases
# ============================================================
g_i.gotostages()

# 初始阶段 | Initial phase — K0 procedure
phase0 = g_i.InitialPhase
phase0.Identification = "Initial Stress"
for s in g_i.Soils:
  g_i.set(s.Material, phase0, soil_mat)
g_i.set(g_i.LineDisplacement_1_1.Displacement_x, phase0, "Prescribed")
g_i.set(g_i.LineDisplacement_1_1.Displacement_y, phase0, "Fixed")
g_i.set(g_i.LineDisplacement_2_1.Displacement_x, phase0, "Free")
g_i.set(g_i.LineDisplacement_2_1.Displacement_y, phase0, "Fixed")
g_i.set(g_i.LineDisplacement_3_1.Displacement_x, phase0, "Free")
g_i.set(g_i.LineDisplacement_3_1.Displacement_y, phase0, "Fixed")
# 阶段1：静力重力 | Phase 1: Static gravity
phase1 = g_i.phase(phase0)
phase1.Identification = "Static Gravity"
phase1.DeformCalcType = "plastic"
for s in g_i.Soils:
  g_i.set(s.Material, phase1, soil_mat)

# 阶段2：动力地震 | Phase 2: Dynamic seismic
phase2 = g_i.phase(phase1)
phase2.Identification = "Seismic Dynamic"
phase2.DeformCalcType = "dynamics"
phase2.Deform.ResetDisplacementsToZero = True
phase2.Deform.TimeInterval = 0.01
phase2.Deform.TimeIntervalSeconds = 1    
phase2.MaxStepsStored = 100
phase2.Deform.UseDefaultIterationParams = False
phase2.Deform.MaxSteps = 2000
phase2.Deform.AutomaticTimeStepping = False 
phase2.Deform.MaxThreads = 8
phase2.ReboundOption = False
# 动力参数 | Dynamic parameters
phase2.Deform.NewmarkAlpha = 0.3025
phase2.Deform.NewmarkBeta = 0.6
# 设置阻尼参数 | Damping parameters
phase2.Deform.RayleighAlpha = 0.1
phase2.Deform.RayleighBeta = 0.001
# 激活底部线位移 | Activate bottom line displacement
target_line = g_i.Lines[-1]
g_i.activate(target_line, phase2)
g_i.activate(line_displ, phase2)
g_i.set(g_i.LineDisplacement_1_1.ux_start, phase2, u_amp)

print(f"✅ 动力阶段设置完成 | Dynamic phase configured")
print(f"  持续时间: {phase2.Deform.TimeIntervalSeconds.value} s")
print(f"  最大步数: {phase2.Deform.MaxSteps.value}")

g_i.setcurrentphase(phase2)

print("✅ 计算阶段设置完成 | Phases set")
g_i.set(g_i.DynLineDisplacement_1_1.Multiplierx, phase2, disp_mult)
print("✅ 乘子关联成功")
g_i.activate(g_i.DynLineDisplacement_1_1, phase2)
print("✅ 动力线位移激活成功")

# ============================================================
# 8. 运行计算 | Run Calculation
# ============================================================
print("⏳ 开始计算... | Calculating...")
# print(f"  计算阶段: {phase0.Identification.value} -> {phase1.Identification.value} -> {phase2.Identification.value}")
g_i.calculate(phase0, phase1, phase2)
print("✅ 计算完成 | Calculation complete")

# ============================================================
# 9. 保存 & 结果 | Save & Results
# ============================================================
g_i.save(save_path)
print("✅ 项目已保存 | Saved")

# 连接输出服务器
s_o, g_o = new_server('localhost', 10001, password=passwd,
           timeout=3600, request_timeout=3600)
s_o.open(save_path)

phase_o = g_o.Phases[-1]

ax_all = list(g_o.getresults(phase_o, g_o.ResultTypes.Soil.Ax, "node"))
ux_all = list(g_o.getresults(phase_o, g_o.ResultTypes.Soil.Ux, "node"))
y_all = list(g_o.getresults(phase_o, g_o.ResultTypes.Soil.Y, "node"))

print(f"ax 范围: {min(ax_all):.4f} ~ {max(ax_all):.4f} m/s²")
print(f"ux 范围: {min(ux_all)*1000:.4f} ~ {max(ux_all)*1000:.4f} mm")

max_y = max(y_all)
surface_idx = [i for i, y in enumerate(y_all) if abs(y - max_y) < 0.1]
surface_ax = [ax_all[i] for i in surface_idx]
surface_ux = [ux_all[i] for i in surface_idx]

ax_max = max(abs(v) for v in surface_ax)
ux_max = max(abs(v) for v in surface_ux)

print(f"\n地表动力响应 | Surface Dynamic Response:")
print(f"🔍 最大水平加速度 = {ax_max:.4f} m/s²")
print(f"🔍 最大水平位移  = {ux_max*1000:.4f} mm")
print(f"🔍 加速度放大系数 = {ax_max/(0.1*9.81):.3f}")
print("\n🎉 地震动力响应分析完成 | Seismic Dynamic Analysis Complete!")