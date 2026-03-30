from plxscripting.easy import *
import math

# ============================================================
# 配置参数 | Configuration
# ============================================================
PASSWD     = "your password"
SAVE_PATH  = r"D:\BaiduNetdiskDownload\PLAXIS 2D 2024(64bit)\file\dam flow.p2dx"
K_H        = 0.001   # 水平渗透系数 | Horizontal permeability (m/day)
DAM_HEIGHT = 8.0     # 堤高 | Dam height (m)


def set_global_waterlevel(si, wl_names, phase_obj=None, phase_name=None):
    """
    尝试多种命令格式设置全局水位（兼容不同 PLAXIS 版本）
    Try multiple _setglobalwaterlevel signatures for PLAXIS version compatibility
    """
    phase_candidates = []
    if phase_name:
        phase_candidates.append(str(phase_name))
    if phase_obj is not None:
        try:
            phase_candidates.append(str(phase_obj.Name.value))
        except Exception:
            pass
    phase_candidates.append("InitialPhase")

    # 去重并保留顺序 | Deduplicate while preserving order
    seen = set()
    phase_candidates = [p for p in phase_candidates if not (p in seen or seen.add(p))]

    if isinstance(wl_names, str):
        wl_candidates = [wl_names]
    else:
        wl_candidates = [str(x) for x in wl_names if str(x).strip()]
    seen_wl = set()
    wl_candidates = [w for w in wl_candidates if not (w in seen_wl or seen_wl.add(w))]

    commands = []
    for wl in wl_candidates:
        for p in phase_candidates:
            # 正序尝试：水位线 阶段 | Original order: waterlevel phase
            commands.append(f"_setglobalwaterlevel {wl} {p}")
            commands.append(f'_setglobalwaterlevel "{wl}" {p}')
            commands.append(f'_setglobalwaterlevel {wl} "{p}"')
            commands.append(f'_setglobalwaterlevel "{wl}" "{p}"')
            # 逆序尝试：阶段 水位线 | Swapped order: phase waterlevel
            commands.append(f"_setglobalwaterlevel {p} {wl}")
            commands.append(f'_setglobalwaterlevel "{p}" {wl}')
            commands.append(f'_setglobalwaterlevel {p} "{wl}"')
            commands.append(f'_setglobalwaterlevel "{p}" "{wl}"')

    tried = []
    for cmd in commands:
        tried.append(cmd)
        result   = si.connection.request_commands(cmd)
        feedback = result.get("commands", [{}])[0].get("feedback", {})
        success  = bool(feedback.get("success", False))
        if success:
            print(f"✅ 全局水位设置成功 | GWL set: {cmd}")
            return

    raise RuntimeError("设置全局水位失败 | Failed to set GWL. Tried:\n" + "\n".join(tried))


def pick_waterlevel_candidates(gi, created_wl_obj):
    """
    收集所有可用水位线名称，优先返回用户自定义水位
    Collect all water level names, preferring user-defined over borehole levels
    """
    names = []
    try:
        names.append(str(created_wl_obj.Name.value))
    except Exception:
        pass
    try:
        for w in gi.WaterLevels:
            names.append(str(w.Name.value))
    except Exception:
        pass

    # 优先用户水位，排除钻孔水位 | Prefer user levels over BoreholeWaterLevels
    preferred = [n for n in names if "boreholewaterlevels" not in n.lower()]
    ordered   = preferred + names

    seen    = set()
    ordered = [n for n in ordered if n and not (n in seen or seen.add(n))]
    if not ordered:
        raise RuntimeError("未找到可用水位线名称 | No water level name found")
    return ordered


def finite_values(values, name):
    """
    过滤非有限值，确保结果有效 | Filter out non-finite values
    """
    cleaned = [v for v in values if isinstance(v, (int, float)) and math.isfinite(v)]
    if not cleaned:
        raise RuntimeError(f"{name} 结果为空或无有效数值 | No valid results")
    return cleaned


def try_get_result(phase, result_obj, candidate_names):
    """
    兼容不同版本 ResultTypes 字段名，返回第一个可用结果
    Try multiple field names for PLAXIS version compatibility
    """
    last_error = None
    locations  = ["node", "stresspoint"]
    for attr in candidate_names:
        if not hasattr(result_obj, attr):
            continue
        result_type = getattr(result_obj, attr)
        for loc in locations:
            try:
                vals = list(g_o.getresults(phase, result_type, loc))
                vals = finite_values(vals, f"{attr}@{loc}")
                return f"{attr}@{loc}", vals
            except Exception as exc:
                last_error = exc
                continue
    raise RuntimeError(f"未找到可用结果字段 | No valid field in: {candidate_names}; "
                       f"last_error={last_error}")


# ============================================================
# 1. 连接服务器 | Connect to Server
# ============================================================
s_i, g_i = new_server(
    "localhost", 10000,
    password=PASSWD,
    timeout=3600,
    request_timeout=3600,
)

s_i.new()
g_i.Project.Title      = "Seepage Analysis - Earth Dam"
g_i.Project.UnitForce  = "kN"
g_i.Project.UnitLength = "m"
g_i.Project.UnitTime   = "day"
g_i.SoilContour.initializerectangular(0, 0, 60, 10)
print("✅ 项目建立完成 | Project created")

# ============================================================
# 2. 定义土层 | Define Soil Layers
# ============================================================
g_i.borehole(0)
g_i.soillayer(0)
g_i.Soillayer_1.Zones[0].Top    = 10
g_i.Soillayer_1.Zones[0].Bottom = 0
g_i.Borehole_1.Head = 6          # 初始地下水位 | Initial groundwater level (m)
print("✅ 土层定义完成 | Soil layers defined")

# ============================================================
# 3. 定义材料 | Define Materials
# ============================================================
soil_mat = g_i.soilmat()
soil_mat.setproperties("SoilModel", 2)   # Mohr-Coulomb
soil_mat.setproperties(
    "Identification",        "Dam_Soil",
    "DrainageType",          0,           # 排水 | Drained
    "gammaUnsat",            18.0,        # 非饱和重度 | Unsaturated unit weight (kN/m³)
    "gammaSat",              20.0,        # 饱和重度 | Saturated unit weight (kN/m³)
    "Eref",                  20000.0,     # 弹性模量 | Young's modulus (kPa)
    "nu",                    0.3,         # 泊松比 | Poisson's ratio
    "cRef",                  5.0,         # 黏聚力 | Cohesion (kPa)
    "phi",                   28.0,        # 摩擦角 | Friction angle (°)
    "psi",                   0.0,         # 剪胀角 | Dilatancy angle (°)
    "PermHorizontalPrimary", K_H,         # 水平渗透系数 | Horizontal permeability (m/day)
    "PermVertical",          0.001,       # 竖向渗透系数 | Vertical permeability (m/day)
)
g_i.Soillayer_1.Soil.Material = soil_mat
print("✅ 材料定义完成 | Materials defined")

# ============================================================
# 4. 定义堤坝几何 | Define Dam Geometry
# 堤高8m，坡比1:2，堤顶宽4m
# Dam height 8m, slope ratio 1:2, crest width 4m
# 上游坡脚x=20，堤顶左x=36，堤顶右x=40，下游坡脚x=56
# Upstream toe x=20, crest left x=36, crest right x=40, downstream toe x=56
# ============================================================
g_i.gotostructures()
g_i.polygon(
    (20, 0),   # 上游坡脚 | Upstream toe
    (56, 0),   # 下游坡脚 | Downstream toe
    (40, 8),   # 堤顶右   | Crest right
    (36, 8),   # 堤顶左   | Crest left
)
print("✅ 几何定义完成 | Geometry defined")

# ============================================================
# 5. 定义浸润线 | Define Seepage Line
# 上游水位7m经坝体衰减至下游出逸点1m
# Upstream h=7m attenuates through dam body to downstream exit h=1m
# 需在 gotoflow 模式下创建 | Must be created in gotoflow mode
# ============================================================
g_i.gotoflow()
created_wl = g_i.waterlevel(
    (0,  7),    # 上游水面起点  | Upstream water surface start
    (34, 7),    # 上游坡面      | Upstream slope
    (37, 5.5),  # 浸润线控制点1 | Seepage line control point 1
    (40, 3.5),  # 浸润线控制点2 | Seepage line control point 2
    (43, 2.0),  # 浸润线控制点3 | Seepage line control point 3
    (54, 1),    # 下游出逸点    | Downstream exit point
    (60, 1),    # 下游水面      | Downstream water surface
)
wl_names = pick_waterlevel_candidates(g_i, created_wl)
print(f"✅ 水位线定义完成 | Seepage line defined, candidates: {wl_names}")

# ============================================================
# 6. 赋材料 | Assign Materials
# ============================================================
g_i.gotosoil()
for s in g_i.Soils:
    s.Material = soil_mat

# ============================================================
# 7. 网格划分 | Mesh Generation
# ============================================================
g_i.gotomesh()
g_i.mesh(0.06)
print("✅ 网格完成 | Mesh generated")

# ============================================================
# 8. 计算阶段 | Calculation Phases
# ============================================================
g_i.gotostages()

# 初始阶段：K0 自重应力 | Initial phase: K0 stress state
phase0 = g_i.InitialPhase
phase0.Identification = "Initial Stress"
# 设置初始阶段全局水位 | Set global water level for initial phase
set_global_waterlevel(s_i, wl_names, phase_obj=phase0, phase_name="InitialPhase")

# 阶段1：稳态渗流 | Phase 1: Steady state seepage
phase1 = g_i.phase(phase0)
phase1.Identification   = "Steady State Seepage"
phase1.DeformCalcType   = "plastic"
phase1.PorePresCalcType = "steady state groundwater flow"   # 稳态地下水渗流计算
# 设置渗流阶段全局水位 | Set global water level for seepage phase
set_global_waterlevel(s_i, wl_names, phase_obj=phase1, phase_name=phase1.Name.value)
print("✅ 计算阶段完成 | Phases set")

# ============================================================
# 9. 运行计算 | Run Calculation
# ============================================================
g_i.setcurrentphase(phase1)
print("⏳ 开始计算... | Calculating...")
g_i.calculate()
print("✅ 计算完成 | Calculation complete")

g_i.save(SAVE_PATH)
print("✅ 已保存 | Saved")

# ============================================================
# 10. 结果提取 | Results
# ============================================================
s_o, g_o = new_server(
    "localhost", 10001,
    password=PASSWD,
    timeout=3600,
    request_timeout=3600,
)
s_o.open(SAVE_PATH)

phase_o = g_o.Phases[-1]
print(f"\n阶段 | Phase: {phase_o.Identification.value}")

# 水头分布 | Hydraulic head distribution
head_vals = finite_values(
    list(g_o.getresults(phase_o, g_o.ResultTypes.Soil.GWHead, "node")), "GWHead"
)
print(f"🔍 最大水头 | Max head           = {max(head_vals):.2f} m")
print(f"🔍 最小水头 | Min head           = {min(head_vals):.2f} m")

# 渗透坡降 | Hydraulic gradient
grad_vals = finite_values(
    list(g_o.getresults(phase_o, g_o.ResultTypes.Soil.HydraulicGradientTot, "node")),
    "HydraulicGradientTot",
)
print(f"🔍 最大渗透坡降 | Max gradient   = {max(grad_vals):.4f}")

# 渗流速度 | Seepage velocity
# 渗流量 | Seepage discharge
qx_vals = finite_values(
    list(g_o.getresults(phase_o, g_o.ResultTypes.Soil.Qx, "node")), "Qx"
)
qy_vals = finite_values(
    list(g_o.getresults(phase_o, g_o.ResultTypes.Soil.Qy, "node")), "Qy"
)
# 合成总渗流量 Q = √(Qx² + Qy²) | Total discharge magnitude
qtot_vals = [(qx**2 + qy**2)**0.5 for qx, qy in zip(qx_vals, qy_vals)]
print(f"🔍 最大水平渗流量 | Max Qx         = {max(abs(v) for v in qx_vals):.6f} m³/day/m")
print(f"🔍 最大竖向渗流量 | Max Qy         = {max(abs(v) for v in qy_vals):.6f} m³/day/m")
print(f"🔍 最大总渗流量   | Max Q total    = {max(qtot_vals):.6f} m³/day/m")

print("\n🎉 堤坝渗流分析完成 | Dam Seepage Analysis Complete!")