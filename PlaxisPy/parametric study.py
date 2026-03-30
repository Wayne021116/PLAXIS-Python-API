import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Microsoft YaHei'  # 支持中文

from plxscripting.easy import *

passwd = "your password"
save_path = r"D:\BaiduNetdiskDownload\PLAXIS 2D 2024(64bit)\file\parametric_study.png"
s_i, g_i = new_server("localhost", 10000, password=passwd,
                       timeout=3600, request_timeout=3600)

# ============================================================
# 参数化研究设置 | Parametric Study Setup
# ============================================================

# 研究1：改变摩擦角 φ | Study 1: Vary friction angle
phi_values = [20, 25, 30, 35, 40]
fos_phi = []

# 研究2：改变黏聚力 c | Study 2: Vary cohesion
c_values = [5, 10, 15, 20, 25]
fos_c = []

# 研究3：改变坡比 | Study 3: Vary slope ratio
slope_ratios = [1.0, 1.5, 2.0, 2.5, 3.0]
fos_slope = []

def run_slope_analysis(phi, c, slope_ratio):
    """运行一次边坡稳定分析 | Run one slope stability analysis"""

    s_i.new()
    g_i.Project.Title = f"Slope phi={phi} c={c} ratio={slope_ratio}"
    g_i.Project.UnitForce = "kN"
    g_i.Project.UnitLength = "m"
    g_i.Project.UnitTime = "day"
    g_i.SoilContour.initializerectangular(0, 0, 30, 15)

    # 土层
    g_i.borehole(0)
    g_i.soillayer(0)
    g_i.Soillayer_1.Zones[0].Top = 15
    g_i.Soillayer_1.Zones[0].Bottom = 0
    g_i.Borehole_1.Head = 8

    # 材料
    soil_mat = g_i.soilmat()
    soil_mat.setproperties("SoilModel", 2)
    soil_mat.setproperties(
        "Identification",        "Slope_Soil",
        "DrainageType",          0,
        "gammaUnsat",            18.0,
        "gammaSat",              20.0,
        "Eref",                  20000.0,
        "nu",                    0.3,
        "cRef",                  float(c),
        "phi",                   float(phi),
        "psi",                   0.0,
        "PermHorizontalPrimary", 1.0,
        "PermVertical",          1.0,
    )

    # 几何
    g_i.gotostructures()
    slope_top_x = 10 + 5 * slope_ratio
    soil = g_i.polygon(
        (0,           0),
        (30,          0),
        (30,          15),
        (slope_top_x, 15),
        (10,          10),
        (0,           10),
    )[0]

    # 赋材料
    g_i.gotosoil()
    for vol in g_i.Soils:
        vol.Material = soil_mat

    # 水位
    g_i.gotowater()
    g_i.waterlevel((0, 8), (30, 8))

    # 网格
    g_i.gotomesh()
    g_i.mesh(0.06)

    # 计算阶段
    g_i.gotostages()
    phase0 = g_i.InitialPhase
    phase0.Identification = "Initial Stress"
    g_i.activate(soil, phase0)

    phase1 = g_i.phase(phase0)
    phase1.Identification = "Safety"
    phase1.DeformCalcType = 7
    phase1.Deform.LoadingType = "incrementalmultipliers"
    phase1.Deform.UseDefaultIterationParams = False
    phase1.Deform.MaxSteps = 100
    g_i.set(g_i.Soils[0].ApplyStrengthReduction, phase1, True)

    # 计算
    g_i.calculate(phase0, phase1)

    # 结果
    fos = g_i.Phases[-1].Reached.SumMsf.value
    return fos

# ============================================================
# 研究1：改变摩擦角 | Study 1: Vary phi
# ============================================================
print("="*50)
print("研究1：改变摩擦角 φ | Study 1: Vary phi")
print("="*50)
for phi in phi_values:
    print(f"计算 φ={phi}°...")
    fos = run_slope_analysis(phi=phi, c=10, slope_ratio=1.5)
    fos_phi.append(fos)
    print(f"φ={phi}° → FOS={fos:.3f}")

# ============================================================
# 研究2：改变黏聚力 | Study 2: Vary cohesion
# ============================================================
print("\n" + "="*50)
print("研究2：改变黏聚力 c | Study 2: Vary cohesion")
print("="*50)
for c in c_values:
    print(f"计算 c={c} kPa...")
    fos = run_slope_analysis(phi=25, c=c, slope_ratio=1.5)
    fos_c.append(fos)
    print(f"c={c} kPa → FOS={fos:.3f}")

# ============================================================
# 研究3：改变坡比 | Study 3: Vary slope ratio
# ============================================================
print("\n" + "="*50)
print("研究3：改变坡比 | Study 3: Vary slope ratio")
print("="*50)
for ratio in slope_ratios:
    print(f"计算坡比 1:{ratio}...")
    fos = run_slope_analysis(phi=25, c=10, slope_ratio=ratio)
    fos_slope.append(fos)
    print(f"坡比 1:{ratio} → FOS={fos:.3f}")

# ============================================================
# 绘图 | Plot Results
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('边坡稳定参数化研究 | Slope Stability Parametric Study',
             fontsize=14, fontweight='bold')

# 图1：FOS vs φ
axes[0].plot(phi_values, fos_phi, 'bo-', linewidth=2, markersize=8)
axes[0].axhline(y=1.0, color='r', linestyle='--', label='FOS=1.0')
axes[0].axhline(y=1.5, color='g', linestyle='--', label='FOS=1.5')
axes[0].set_xlabel('内摩擦角 φ (°)')
axes[0].set_ylabel('安全系数 FOS')
axes[0].set_title('FOS vs 摩擦角 φ')
axes[0].legend()
axes[0].grid(True)

# 图2：FOS vs c
axes[1].plot(c_values, fos_c, 'rs-', linewidth=2, markersize=8)
axes[1].axhline(y=1.0, color='r', linestyle='--', label='FOS=1.0')
axes[1].axhline(y=1.5, color='g', linestyle='--', label='FOS=1.5')
axes[1].set_xlabel('黏聚力 c (kPa)')
axes[1].set_ylabel('安全系数 FOS')
axes[1].set_title('FOS vs 黏聚力 c')
axes[1].legend()
axes[1].grid(True)

# 图3：FOS vs 坡比
axes[2].plot(slope_ratios, fos_slope, 'g^-', linewidth=2, markersize=8)
axes[2].axhline(y=1.0, color='r', linestyle='--', label='FOS=1.0')
axes[2].axhline(y=1.5, color='g', linestyle='--', label='FOS=1.5')
axes[2].set_xlabel('坡比 (水平:垂直)')
axes[2].set_ylabel('安全系数 FOS')
axes[2].set_title('FOS vs 坡比')
axes[2].legend()
axes[2].grid(True)

plt.tight_layout()
plt.savefig(save_path, dpi=150, bbox_inches='tight')
plt.show()
print("\n✅ 图表已保存 | Figure saved")
print("\n🎉 参数化研究完成 | Parametric Study Complete!")