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
g_i.Project.Title = "Tunnel Excavation Analysis"
g_i.Project.UnitForce = "kN"
g_i.Project.UnitLength = "m"
g_i.Project.UnitTime = "day"

# 模型范围 | Model boundaries
g_i.SoilContour.initializerectangular(0, -30, 40, 0)
print("✅ 项目建立完成 | Project created")

# ============================================================
# 3. 定义土层 | Define Soil Layers
# ============================================================
g_i.borehole(0)
g_i.soillayer(0)
g_i.Soillayer_1.Zones[0].Top = 0
g_i.Soillayer_1.Zones[0].Bottom = -30
g_i.Borehole_1.Head = -5  # 水位 y=-5m | GWL at y=-5m
print("✅ 土层定义完成 | Soil layers defined")

# ============================================================
# 4. 定义材料 | Define Materials
# ============================================================
soil_mat = g_i.soilmat()
soil_mat.setproperties("SoilModel", 2)  # Mohr-Coulomb
soil_mat.setproperties(
    "Identification",        "Soil",
    "DrainageType",          0,          # Drained | 排水
    "gammaUnsat",            18.0,
    "gammaSat",              20.0,
    "Eref",                  20000.0,
    "nu",                    0.3,
    "cRef",                  5.0,
    "phi",                   28.0,
    "psi",                   0.0,
    "PermHorizontalPrimary", 1.0,
    "PermVertical",          1.0,
)
g_i.Soillayer_1.Soil.Material = soil_mat
print("✅ 材料定义完成 | Materials defined")

# ============================================================
# 5. 定义结构 | Define Structure
# ============================================================
g_i.gotostructures()

# 圆形隧道衬砌（板单元）| Circular tunnel lining (plate)
# 圆心 (0, -15)，半径 R=3m，取右半圆
# 用多段折线近似圆形 | Approximate circle with segments
import math
R = 3.0
cx, cy = 0.0, -15.0
n_segments = 16  # 分16段近似半圆

points = []
for i in range(n_segments + 1):
    angle = math.pi / 2 - i * math.pi / n_segments  # 从顶部到底部
    x = cx + R * math.cos(angle)
    y = cy + R * math.sin(angle)
    points.append((x, y))

# 创建隧道衬砌线段 | Create tunnel lining segments
tunnel_lines = []
for i in range(len(points) - 1):
    line = g_i.plate(points[i], points[i+1])
    tunnel_lines.append(line)

# 衬砌材料 | Lining material
lining_mat = g_i.platemat()
lining_mat.setproperties(
    "Identification",  "Lining",
    "MaterialType",    1,          # Elastic
    "EA1",             9.0e6,      # 轴向刚度 | Axial stiffness (kN/m)
    "EI",              67500.0,    # 抗弯刚度 | Bending stiffness (kN·m²/m)
    "w",               7.2,        # 自重 | Weight (kN/m/m)
    "StructNu",        0.2,        # 泊松比 | Poisson's ratio
    "PreventPunching", False,
)
g_i.setmaterial(g_i.Plates, lining_mat)

# 隧道内部土体多边形（用于开挖）| Tunnel soil polygon for excavation
# 用圆形多边形近似 | Approximate with polygon
tunnel_points = []
for i in range(n_segments + 1):
    angle = math.pi / 2 - i * math.pi / n_segments
    x = cx + R * math.cos(angle)
    y = cy + R * math.sin(angle)
    tunnel_points.append((x, y))
# 闭合多边形（加入圆心处的边界）
tunnel_points.append((0, cy))  # 底部中心
tunnel_points.append((0, cy + R))  # 顶部中心

tunnel_poly = g_i.polygon(*tunnel_points)
tunnel_poly = tunnel_poly[0]

print("✅ 结构定义完成 | Structure defined")

# ============================================================
# 6. 网格划分 | Mesh Generation
# ============================================================
g_i.gotomesh()
g_i.mesh(0.06)
print("✅ 网格划分完成 | Mesh generated")

# ============================================================
# 7. 计算阶段 | Calculation Phases
# ============================================================
g_i.gotostructures()
g_i.setmaterial(g_i.Plates, lining_mat)
g_i.gotostages()

phase0 = g_i.InitialPhase
phase0.Identification = "Initial Stress"

# 阶段1：激活衬砌 + 开挖 | Phase 1: Activate lining + excavate
phase1 = g_i.phase(phase0)
phase1.Identification = "Excavation with Lining"
phase1.DeformCalcType = "plastic"
phase1.Deform.LoadingType = "stagedconstruction"
g_i.setcurrentphase(phase1)

# ✅ 同时停用土体 + 激活衬砌
g_i.deactivate(tunnel_poly, phase1)
for p in g_i.Plates:
    p.Active.set(phase1, True)

# 阶段2：完全收缩 | Phase 2: Full contraction
phase2 = g_i.phase(phase1)
phase2.Identification = "Full Contraction"
phase2.DeformCalcType = "plastic"
phase2.Deform.LoadingType = "stagedconstruction"
phase2.Deform.Loading.Mstage = 1.0

print("✅ 计算阶段设置完成 | Phases set")

# ============================================================
# 8. 运行计算 | Run Calculation
# ============================================================
print("⏳ 开始计算... | Calculating...")
for ph in g_i.Phases:
    ph.ShouldCalculate = True
g_i.calculate()
print("✅ 计算完成 | Calculation complete")

# ============================================================
# 9. 保存 & 结果 | Save & Results
# ============================================================
g_i.save(save_path)
print("✅ 项目已保存 | Saved")

# 连接 Output | Connect Output
s_o, g_o = new_server('localhost', 10001, password=passwd,
                       timeout=3600, request_timeout=3600)
s_o.open(save_path)

print("\n" + "="*50)
print("隧道开挖结果 | Tunnel Excavation Results")
print("="*50)

# 最终阶段结果
phase_o = g_o.Phases[-1]
print("阶段:", phase_o.Identification.value)

# 地面沉降 | Surface settlement
uy = g_o.getresults(phase_o, g_o.ResultTypes.Soil.Uy, "node")
uy_vals = list(uy)
print(f"🔍 最大地面沉降 = {abs(min(uy_vals))*1000:.2f} mm")

# 水平位移 | Horizontal displacement
ux = g_o.getresults(phase_o, g_o.ResultTypes.Soil.Ux, "node")
ux_vals = list(ux)
print(f"🔍 最大水平位移 = {max(ux_vals)*1000:.2f} mm")

# 衬砌弯矩 | Lining bending moment
try:
    m2d = g_o.getresults(phase_o, g_o.ResultTypes.Plate.M2D, "node")
    m_vals = list(m2d)
    print(f"🔍 衬砌最大弯矩 = {max(m_vals):.2f} kNm/m")
    print(f"🔍 衬砌最小弯矩 = {min(m_vals):.2f} kNm/m")
except:
    print("⚠️ 衬砌弯矩获取失败")

# 衬砌轴力 | Lining axial force
try:
    nx2d = g_o.getresults(phase_o, g_o.ResultTypes.Plate.Nx2D, "node")
    nx_vals = list(nx2d)
    print(f"🔍 衬砌最大轴力 = {max(nx_vals):.2f} kN/m")
    print(f"🔍 衬砌最小轴力 = {min(nx_vals):.2f} kN/m")
except:
    print("⚠️ 衬砌轴力获取失败")

print("="*50)
print("\n🎉 隧道开挖分析完成 | Tunnel Excavation Analysis Complete!")