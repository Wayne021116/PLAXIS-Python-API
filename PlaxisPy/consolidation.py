from plxscripting.easy import *

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
g_i.Project.Title = "Consolidation Settlement Analysis"
g_i.Project.UnitForce = "kN"
g_i.Project.UnitLength = "m"
g_i.Project.UnitTime = "day"

g_i.SoilContour.initializerectangular(0, -20, 30, 0)
print("✅ 项目建立完成 | Project created")

# ============================================================
# 3. 定义土层 | Define Soil Layers
# ============================================================
g_i.borehole(0)

# 上层：软土 y=0~-10 | Upper layer: Soft soil
g_i.soillayer(0)
g_i.Soillayer_1.Zones[0].Top = 0
g_i.Soillayer_1.Zones[0].Bottom = -10

# 下层：砂土 y=-10~-20 | Lower layer: Sand
g_i.soillayer(0)
g_i.Soillayer_2.Zones[0].Bottom = -20

# 水位在地面 | GWL at ground surface
g_i.Borehole_1.Head = 0
print("✅ 土层定义完成 | Soil layers defined")

# ============================================================
# 4. 定义材料 | Define Materials
# ============================================================

# 软土材料（Soft Soil）| Soft soil material
material1 = g_i.soilmat()
material1.setproperties("SoilModel", 5)  # 5 = Soft Soil
material1.setproperties(
    "Identification",        "SoftClay",
    "DrainageType",          1,          # 不排水A | Undrained A
    "gammaUnsat",            15.0,       # 非饱和重度 | Unsaturated unit weight (kN/m³)
    "gammaSat",              16.0,       # 饱和重度 | Saturated unit weight (kN/m³)
    "eInit",                 1.5,        # 初始孔隙比 | Initial void ratio
    "lambdaModified",        0.15,       # 修正压缩指数 | Modified compression index
    "kappaModified",         0.03,       # 修正膨胀指数 | Modified swelling index
    "cRef",                  2.0,        # 黏聚力 | Cohesion (kPa)
    "phi",                   22.0,       # 摩擦角 | Friction angle (°)
    "nuUR",                  0.15,       # 泊松比 | Poisson's ratio
    "PermHorizontalPrimary", 0.001,      # 水平渗透系数 | Horizontal permeability (m/day)
    "PermVertical",          0.001,      # 竖直渗透系数 | Vertical permeability (m/day)
    "POP",                   10.0,       # 预加载比 | Pre-overburden pressure
)

# 砂土材料（Mohr-Coulomb）| Sand material
material2 = g_i.soilmat()
material2.setproperties("SoilModel", 2)  # 2 = Mohr-Coulomb
material2.setproperties(
    "Identification",        "Sand",
    "DrainageType",          0,          # 排水 | Drained
    "gammaUnsat",            18.0,
    "gammaSat",              20.0,
    "Eref",                  30000.0,
    "nu",                    0.3,
    "cRef",                  0.0,
    "phi",                   32.0,
    "psi",                   0.0,
    "PermHorizontalPrimary", 1.0,        # 高渗透性 | High permeability (m/day)
    "PermVertical",          1.0,
)

# 赋材料 | Assign materials
g_i.Soillayer_1.Soil.Material = material1
g_i.Soillayer_2.Soil.Material = material2
print("✅ 材料定义完成 | Materials defined")

# ============================================================
# 5. 定义荷载 | Define Load
# ============================================================
g_i.gotostructures()

# 地表均布荷载 x=0~15m | Surface load
g_i.lineload((0, 0), (15, 0))
g_i.LineLoad_1.qy_start = -15.0  # -15 kPa
print("✅ 荷载定义完成 | Load defined")

# ============================================================
# 6. 网格划分 | Mesh Generation
# ============================================================
g_i.gotomesh()
g_i.mesh(0.06)
print("✅ 网格划分完成 | Mesh generated")

# ============================================================
# 7. 计算阶段 | Calculation Phases
# ============================================================
g_i.gotostages()

# 初始阶段 | Initial phase
phase0 = g_i.InitialPhase
phase0.Identification = "Initial Stress"

# 阶段1：施加堆载（塑性）| Phase 1: Apply load (plastic)
phase1 = g_i.phase(phase0)
phase1.Identification = "Apply Load"
phase1.DeformCalcType = "plastic"
g_i.setcurrentphase(phase1)
g_i.set(g_i.LineLoad_1_1.Active, phase1, True)

# 阶段2：固结30天 | Phase 2: Consolidation 30 days
phase2 = g_i.phase(phase1)
phase2.Identification = "Consolidation 30 days"
phase2.DeformCalcType = "consolidation"  # 固结计算
phase2.TimeInterval = 30  # 30天

# 阶段3：固结100天 | Phase 3: Consolidation 100 days
phase3 = g_i.phase(phase2)
phase3.Identification = "Consolidation 100 days"
phase3.DeformCalcType = "consolidation"
phase3.TimeInterval = 70  # 再加70天

# 阶段4：固结365天 | Phase 4: Consolidation 365 days
phase4 = g_i.phase(phase3)
phase4.Identification = "Consolidation 365 days"
phase4.DeformCalcType = "consolidation"
phase4.TimeInterval = 265  # 再加265天

print("✅ 计算阶段设置完成 | Phases set")

# ============================================================
# 8. 运行计算 | Run Calculation
# ============================================================
for ph in g_i.Phases:
    ph.ShouldCalculate = True

print("⏳ 开始计算... | Calculating...")
g_i.calculate()
print("✅ 计算完成 | Calculation complete")

# ============================================================
# 9. 保存 & 结果 | Save & Results
# ============================================================
g_i.save(save_path)
print("✅ 项目已保存 | Project saved")

# 连接 Output | Connect Output
s_o, g_o = new_server('localhost', 10001, password=passwd,
                       timeout=3600, request_timeout=3600)

s_o.open(save_path)

print("\n" + "="*50)
print("固结沉降结果 | Consolidation Settlement Results")
print("="*50)

times = [0, 30, 100, 365]
for i, (ph, t) in enumerate(zip([phase1, phase2, phase3, phase4], times)):
    ph_o = g_o.Phases[i + 1]
    uy = g_o.getresults(ph_o, g_o.ResultTypes.Soil.Uy, "node")
    uy_vals = list(uy)
    settlement = abs(min(uy_vals))
    print(f"时间 t={t:4d} 天 | 最大沉降 = {settlement*1000:.2f} mm")

# 超孔压 | Excess pore pressure
ph_o1 = g_o.Phases[1]  # 施加荷载后
pex = g_o.getresults(ph_o1, g_o.ResultTypes.Soil.PExcess, "node")
pex_vals = list(pex)
print(f"\n施加荷载后最大超孔压 = {max(pex_vals):.2f} kPa")

ph_o4 = g_o.Phases[4]  # 固结365天后
pex4 = g_o.getresults(ph_o4, g_o.ResultTypes.Soil.PExcess, "node")
pex4_vals = list(pex4)
print(f"固结365天后最大超孔压 = {max(pex4_vals):.2f} kPa")

print("="*50)
print("\n🎉 固结沉降分析完成 | Consolidation Analysis Complete!")