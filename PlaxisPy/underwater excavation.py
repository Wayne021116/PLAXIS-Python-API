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
g_i.Project.Title = "Underwater Excavation"
g_i.Project.UnitForce = "kN"
g_i.Project.UnitLength = "m"
g_i.Project.UnitTime = "day"

# 设置模型范围 | Set model boundaries
g_i.SoilContour.initializerectangular(0, -30, 65, 20)
print("✅ 项目建立完成 | Project created")

# ============================================================
# 3. 定义土层 | Define Soil Layers (Borehole)
# ============================================================
g_i.borehole(0)

# 上层：黏土层 y=0~20 | Upper layer: Clay y=0~20
g_i.soillayer(0)
g_i.Soillayer_1.Zones[0].Top = 20

# 下层：砂土层 y=-30~0 | Lower layer: Sand y=-30~0
g_i.soillayer(0)
g_i.Soillayer_2.Zones[0].Bottom = -30

# 水位 y=18m | Groundwater level
g_i.Borehole_1.Head = 18
print("✅ 土层定义完成 | Soil layers defined")

# ============================================================
# 4. 定义材料 | Define Materials
# ============================================================

# 黏土材料（软土模型）| Clay material (Soft Soil model)
material1 = g_i.soilmat()
material1.setproperties("SoilModel", 5)         # 5 = Soft Soil | 软土模型
material1.setproperties(
    "Identification",       "Clay",
    "DrainageType",         1,          # 1 = Undrained A | 不排水(A)
    "gammaUnsat",           16.0,       # 非饱和重度 | Unsaturated unit weight
    "gammaSat",             18.0,       # 饱和重度 | Saturated unit weight
    "eInit",                1.0,        # 初始孔隙比 | Initial void ratio
    "lambdaModified",       0.03,       # 修正压缩指数 | Modified compression index
    "kappaModified",        0.0085,     # 修正膨胀指数 | Modified swelling index
    "cRef",                 1.0,        # 黏聚力 | Cohesion (kPa)
    "phi",                  25.0,       # 摩擦角 | Friction angle (°)
    "psi",                  0.0,        # 剪胀角 | Dilatancy angle (°)
    "nuUR",                 0.15,       # 泊松比 | Poisson's ratio
    "PermHorizontalPrimary",0.001,      # 水平渗透系数 | Horizontal permeability
    "PermVertical",         0.001,      # 竖直渗透系数 | Vertical permeability
    "POP",                  5.0,        # 预加载比 | Pre-overburden pressure
)

material1.InterfaceStrengthDetermination = "Manual"
material1.Rinter = 0.5       # 界面强度折减 | Interface strength reduction

# 砂土材料（土体硬化模型）| Sand material (Hardening Soil model)
material2 = g_i.soilmat()
material2.setproperties("SoilModel", 3) # 3 = Hardening Soil | 土体硬化模型
material2.setproperties(
    "Identification",       "Sand",
    "DrainageType",         0,          # 0 = Drained | 排水
    "gammaUnsat",           17.0,       # 非饱和重度 | Unsaturated unit weight
    "gammaSat",             20.0,       # 饱和重度 | Saturated unit weight
    "E50Ref",               40000.0,    # 标准三轴刚度 | Secant stiffness
    "EOedRef",              40000.0,    # 侧限压缩刚度 | Oedometer stiffness
    "EURRef",               120000.0,   # 卸载/重加载刚度 | Unloading stiffness
    "PowerM",               0.5,        # 刚度应力水平指数 | Power for stress-level dependency
    "cRef",                 0.5,        # 黏聚力 | Cohesion (kPa)
    "phi",                  32.0,       # 摩擦角 | Friction angle (°)
    "psi",                  2.0,        # 剪胀角 | Dilatancy angle (°)
    "PermHorizontalPrimary",1.0,        # 水平渗透系数 | Horizontal permeability
    "PermVertical",         1.0,        # 竖直渗透系数 | Vertical permeability
)
material2.InterfaceStrengthDetermination = "manual"
material2.Rinter = 0.67       # 界面强度折减 | Interface strength reduction

# 赋材料给土层 | Assign materials to soil layers
g_i.Soillayer_1.Soil.Material = material1  # 黏土层 | Clay layer
g_i.Soillayer_2.Soil.Material = material2  # 砂土层 | Sand layer
print("✅ 材料定义完成 | Materials defined")

# ============================================================
# 5. 定义结构单元 | Define Structural Elements
# ============================================================
g_i.gotostructures()

# 地下连续墙（板单元）| Diaphragm wall (Plate element)
plate = g_i.plate((50, 20), (50, -10))

# ✅ 添加水平分隔线划分开挖区域
g_i.line((50, 18), (65, 18))  # y=18 第1步开挖底部
g_i.line((50, 10), (65, 10))  # y=10 第2步开挖底部

platematerial = g_i.platemat()
platematerial.setproperties(
    "Identification",   "Wall",
    "MaterialType",     1,
    "EA1",              7.5e6,      # 轴向刚度 | Axial stiffness (kN/m)
    "EI",               1.0e6,      # 抗弯刚度 | Bending stiffness (kN·m²/m)
    "w",                10.0,       # 单位重度 | Weight (kN/m/m)
    "StructNu",         0.0,        # 泊松比 | Poisson's ratio
    "PreventPunching",  False,
)

# 对 Line 对象赋材料
plate[0].Material = platematerial

# 定义界面 | Define interfaces
g_i.posinterface(g_i.Line_1)   # 正界面 | Positive interface
g_i.neginterface(g_i.Line_1)   # 负界面 | Negative interface

# 内支撑（固定端锚杆）| Strut (Fixed end anchor)
g_i.fixedendanchor((50, 19))

anchormaterial = g_i.anchormat()
anchormaterial.setproperties(
    "Identification",   "Strut",
    "MaterialType",     1,          # 1 = Elastic | 弹性
    "EA",               2.0e5,      # 轴向刚度 | Axial stiffness (kN)
    "Lspacing",         5.0,        # 平面外间距 | Out-of-plane spacing (m)
)

g_i.FixedEndAnchors[0].Material = anchormaterial
g_i.FixedEndAnchors[0].EquivalentLength = 15

# 地表荷载 | Surface load
g_i.lineload((43, 20), (48, 20))
g_i.LineLoad_1.qy_start = -5.0     # 荷载大小 | Load magnitude (kN/m/m)

print("✅ 结构单元定义完成 | Structural elements defined")

# ============================================================
# 6. 网格划分 | Mesh Generation
# ============================================================
g_i.gotomesh()
g_i.mesh(0.06)
print("✅ 网格划分完成 | Mesh generated")

# ============================================================
# 7. 计算阶段设置 | Calculation Phase Setup
# ============================================================
# 切回结构模式赋材料
g_i.gotostructures()
g_i.setmaterial(g_i.Plates, platematerial)
g_i.gotostages()

# 初始阶段 | Initial phase (K0 procedure)
phase0 = g_i.InitialPhase
phase0.Identification = "Initial Phase"

# 第1阶段：外部荷载 | Phase 1: External load
phase1 = g_i.phase(phase0)
phase1.Identification = "External Load"
g_i.Model.CurrentPhase = phase1
g_i.activate(g_i.Plates, phase1)        # 激活板单元 | Activate plates
g_i.activate(g_i.Interfaces, phase1)    # 激活界面 | Activate interfaces
g_i.activate(g_i.LineLoads, phase1)     # 激活荷载 | Activate line loads

# 第2阶段：第1步开挖 | Phase 2: First excavation (y=18~20m)
phase2 = g_i.phase(phase1)
phase2.Identification = "First Excavation"
g_i.Model.CurrentPhase = phase2
g_i.deactivate(g_i.Soil_1_1, phase2)  # 停用第1层开挖土 | Deactivate first excavation soil

# 第3阶段：安装内支撑 | Phase 3: Strut installation
phase3 = g_i.phase(phase2)
phase3.Identification = "Strut Installation"
g_i.Model.CurrentPhase = phase3
g_i.activate(g_i.FixedEndAnchors, phase3)  # 激活锚杆 | Activate anchors

# 第4阶段：第2步开挖（水下）| Phase 4: Second excavation (underwater)
phase4 = g_i.phase(phase3)
phase4.Identification = "Second Excavation"
g_i.Model.CurrentPhase = phase4
g_i.deactivate(g_i.Soil_1_2, phase4)  # 停用第2层土 | Deactivate second excavation soil

# 第5阶段：第3步开挖 | Phase 5: Third excavation
phase5 = g_i.phase(phase4)
phase5.Identification = "Third Excavation"
g_i.Model.CurrentPhase = phase5
g_i.deactivate(g_i.Soil_1_4, phase5)  # 停用第3层土 | Deactivate third excavation soil

print("✅ 计算阶段设置完成 | Calculation phases set")

# ============================================================
# 8. 运行计算 | Run Calculation
# ============================================================
print("⏳ 开始计算，请稍候... | Calculating, please wait...")
g_i.Phases[0].ShouldCalculate = True
g_i.Phases[1].ShouldCalculate = True
g_i.Phases[2].ShouldCalculate = True
g_i.Phases[3].ShouldCalculate = True
g_i.Phases[4].ShouldCalculate = True
g_i.Phases[5].ShouldCalculate = True

g_i.calculate()
print("✅ 计算完成 | Calculation complete")

# ============================================================
# 9. 保存项目 | Save Project
# ============================================================
g_i.save(save_path)
print("✅ 项目已保存 | Project saved")

# ============================================================
# 10. 提取结果 | Extract Results
# ============================================================
# 连接 Output 服务器 | Connect to Output server
s_o, g_o = new_server('localhost', 10001, password=passwd)
print("✅ Output 连接成功 | Output server connected")

# 各阶段结果 | Results for each phase
for ph in g_o.Phases:
    print(f"\n阶段 | Phase: {ph.Identification.value}")
    print(f"  ΣMstage = {ph.Reached.SumMstage.value:.3f}")

    # 土体位移 | Soil displacement
    uy = g_o.getresults(ph, g_o.ResultTypes.Soil.Uy, "node")
    ux = g_o.getresults(ph, g_o.ResultTypes.Soil.Ux, "node")
    utot = g_o.getresults(ph, g_o.ResultTypes.Soil.Utot, "node")
    uy_vals = list(uy)
    ux_vals = list(ux)
    utot_vals = list(utot)
    print(f"  最大竖向位移 | Max Uy = {max(uy_vals):.4f} m")
    print(f"  最小竖向位移 | Min Uy = {min(uy_vals):.4f} m")
    print(f"  最大水平位移 | Max Ux = {max(ux_vals):.4f} m")
    print(f"  最大总位移   | Max Utot = {max(utot_vals):.4f} m")
   
print("\n🎉 水下基坑开挖分析完成 | Underwater Excavation Analysis Complete!")
